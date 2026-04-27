# BingTorrent 架构设计文档

## 📐 整体架构

BingTorrent 采用**分层架构**和**事件驱动**设计，基于 Python asyncio 实现高并发下载。

```
┌─────────────────────────────────────────────────┐
│              CLI Interface (main.py)             │
│         命令行接口 / 用户交互层                    │
└────────────────────┬────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────┐
│          Core Business Logic Layer               │
│  ┌──────────┐  ┌──────────────┐  ┌───────────┐ │
│  │ Torrent  │──│ PeerManager  │──│ PieceMgr  │ │
│  │Controller│  │ Connection   │  │ Rarest    │ │
│  │          │  │ Pool Mgmt    │  │ First     │ │
│  └──────────┘  └──────────────┘  └───────────┘ │
└────────────────────┬────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────┐
│         Protocol Implementation Layer            │
│  ┌──────────┐  ┌──────────┐  ┌──────────────┐  │
│  │ Bencode  │  │ Message  │  │ Handshake    │  │
│  │ Encode/  │  │ Types &  │  │ Protocol &   │  │
│  │ Decode   │  │ Parsing  │  │ State Mgmt   │  │
│  └──────────┘  └──────────┘  └──────────────┘  │
└────────────────────┬────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────┐
│          Network Communication Layer             │
│  ┌──────────────┐  ┌──────────────────────────┐ │
│  │ Tracker      │  │ PeerConnection           │ │
│  │ HTTP/HTTPS   │  │ Async TCP Socket         │ │
│  │ Announce     │  │ Read/Write Loop          │ │
│  └──────────────┘  └──────────────────────────┘ │
└────────────────────┬────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────┐
│              Storage Layer                       │
│  ┌──────────────────────────────────────────┐   │
│  │ FileManager                              │   │
│  │ - File I/O Operations                    │   │
│  │ - Multi-file Support                     │   │
│  │ - Hash Verification                      │   │
│  │ - Resume Download                        │   │
│  └──────────────────────────────────────────┘   │
└─────────────────────────────────────────────────┘
```

## 🔑 核心组件详解

### 1. Torrent 控制器 (`core/torrent.py`)

**职责**: 整个下载任务的中枢控制器

**主要功能**:
- 解析 .torrent 文件（Bencode 解码）
- 计算 info_hash（SHA1）
- 初始化所有子组件（FileManager, PieceManager, PeerManager, TrackerClient）
- 协调下载生命周期（start/stop）
- 监控下载进度

**关键方法**:
```python
class Torrent:
    async def start() -> None       # 启动下载
    async def stop() -> None        # 停止下载
    async def _announce_to_tracker() # 向 Tracker 宣告
    async def _monitor_loop()       # 监控循环
```

**数据流**:
```
.torrent 文件 
    → Bencode 解码 
    → MetaInfo 
    → 初始化组件 
    → 启动 PeerManager 
    → 开始下载
```

---

### 2. PieceManager (`core/piece_manager.py`)

**职责**: 智能分片管理，决定下载哪些分片

**核心算法**: **Rarest First**（最稀有优先）

**数据结构**:
```python
downloaded_pieces: Set[int]           # 已下载分片
requested_pieces: Dict[int, Set[str]] # 请求中的分片 {piece_idx: {peer_ids}}
pending_requests: Dict[str, Set]      # 未决请求 {peer_id: {requests}}
peer_bitfields: Dict[str, bytearray]  # Peer 拥有的分片
piece_rarity: Dict[int, int]          # 分片稀有度计数
```

**分片选择流程**:
```
1. 过滤候选分片:
   - Peer 拥有该分片
   - 我们未下载
   - 未在请求中

2. 计算稀有度:
   rarity = 拥有该分片的 Peer 数量

3. 选择策略:
   - 按稀有度升序排序
   - 从最稀有的分片中随机选择一个
```

**示例**:
```python
# Peer1 拥有分片: [0, 1, 2]
# Peer2 拥有分片: [0, 1]
# 稀有度: piece_0=2, piece_1=2, piece_2=1
# 选择: piece_2（最稀有）
```

---

### 3. PeerManager (`core/peer_manager.py`)

**职责**: 管理 Peer 连接池，协调多 Peer 并发下载

**连接管理**:
```python
connections: Dict[str, PeerConnection]  # 活跃连接
connecting_peers: Set[str]              # 正在连接的 Peer
```

**工作流程**:
```
1. 从 Tracker 获取 Peer 列表
2. 异步连接到多个 Peer（限制最大连接数）
3. 为每个成功连接的 Peer 启动下载循环
4. 监控连接状态，自动重连
```

**下载循环** (`_download_loop`):
```python
while connected and running:
    if can_download():  # 对方 unchoke 且我们 interested
        piece_index = piece_manager.select_piece(peer_id)
        if piece_index:
            # 计算块数量
            # 发送 Request 消息
            # 等待 Piece 消息响应
```

---

### 4. PeerConnection (`network/peer_connection.py`)

**职责**: 封装单个 Peer 的 TCP 连接和状态机

**Peer 状态机** (4个关键状态):
```python
am_choking: bool        # 我们是否阻塞对方
am_interested: bool     # 我们是否对对方感兴趣
peer_choking: bool      # 对方是否阻塞我们
peer_interested: bool   # 对方是否对我们感兴趣
```

**连接状态**:
```python
DISCONNECTED → CONNECTING → HANDSHAKING → CONNECTED → CLOSING
```

**握手流程**:
```
1. 发送握手: pstrlen + "BitTorrent protocol" + reserved + info_hash + peer_id
2. 接收握手: 验证对方的 info_hash 是否匹配
3. 发送 Interested 消息
4. 等待 Unchoke 消息
5. 开始交换数据
```

**消息循环** (`_read_loop`):
```python
buffer = b''
while connected:
    chunk = await reader.read(4096)
    buffer += chunk
    
    while buffer:
        message, consumed = Message.deserialize(buffer)
        buffer = buffer[consumed:]
        await _handle_message(message)
```

---

### 5. Tracker Client (`network/tracker.py`)

**职责**: 与 Tracker 服务器通信，获取 Peer 列表

**HTTP 请求参数**:
```python
{
    'info_hash': <20字节原始哈希>,
    'peer_id': <20字节 Peer ID>,
    'port': 6881,
    'uploaded': 0,
    'downloaded': 0,
    'left': <文件大小>,
    'compact': 1,  # 使用紧凑格式
    'event': 'started'  # started/stopped/completed
}
```

**Compact Peer 列表解析**:
```
每 6 字节一个 Peer:
- 前 4 字节: IP 地址（大端序）
- 后 2 字节: 端口号（大端序）

示例: b'\xC0\xA8\x01\x01\x1A\xE9'
      → IP: 192.168.1.1, Port: 6889
```

---

### 6. FileManager (`storage/file_manager.py`)

**职责**: 文件 IO、分片写入、哈希校验

**多文件支持**:
```python
# 单文件模式
FileInfo(path="ubuntu.iso", length=2147483648)

# 多文件模式
[
    FileInfo(path="movie/cd1.avi", length=700000000),
    FileInfo(path="movie/cd2.avi", length=700000000),
]
```

**全局偏移量映射**:
```
文件1: [0, file1_length)
文件2: [file1_length, file1_length + file2_length)
...

write_block(global_offset, data):
    1. 找到对应的文件和文件内偏移
    2. 如果数据跨越多个文件，分段写入
```

**哈希校验**:
```python
def verify_piece(piece_index, piece_data, expected_hash):
    actual_hash = sha1(piece_data)
    return actual_hash == expected_hash
```

---

### 7. Bencode 编解码器 (`protocol/bencode.py`)

**支持的类型**:
```python
# 整数
i3e → 3
i-3e → -3

# 字节串
4:spam → b'spam'

# 列表
l4:spami3ee → [b'spam', 3]

# 字典（键必须排序）
d3:cow3:moo4:spam4:eggse → {b'cow': b'moo', b'spam': b'eggs'}
```

**递归下降解析**:
```
decode(data):
    ↓
_decode_item(data, index):
    ├─ 'i' → _decode_int()
    ├─ 'l' → _decode_list() → 递归调用 _decode_item()
    ├─ 'd' → _decode_dict() → 递归调用 _decode_item()
    └─ digit → _decode_bytes()
```

---

## 🔄 数据流图

### 完整下载流程

```
用户输入 .torrent 文件路径
         ↓
┌─────────────────────┐
│  Torrent.start()    │
│  - 解析种子文件      │
│  - 计算 info_hash   │
│  - 初始化组件        │
└─────────┬───────────┘
          ↓
┌─────────────────────┐
│ Tracker.announce()  │
│  - HTTP GET 请求    │
│  - 获取 Peer 列表   │
└─────────┬───────────┘
          ↓
┌─────────────────────┐
│ PeerManager         │
│  - 连接到多个 Peer  │
│  - 执行握手         │
└─────────┬───────────┘
          ↓
┌─────────────────────┐
│ 下载循环（并发）     │
│ For each Peer:      │
│  1. PieceManager    │
│     选择分片         │
│  2. 发送 Request    │
│  3. 接收 Piece      │
│  4. FileManager     │
│     写入磁盘         │
│  5. 哈希校验        │
└─────────┬───────────┘
          ↓
┌─────────────────────┐
│ 下载完成            │
│  - 验证所有分片     │
│  - 关闭连接         │
└─────────────────────┘
```

---

## 🎯 关键设计决策

### 1. 为什么使用 asyncio？

**优势**:
- 高并发：可以同时连接数十个 Peer
- 非阻塞 IO：网络等待时不占用 CPU
- 简洁的代码：避免回调地狱

**对比多线程**:
```python
# 多线程（复杂）
threading.Thread(target=download_from_peer).start()

# asyncio（简洁）
asyncio.create_task(download_from_peer())
```

### 2. 为什么选择 Rarest First 算法？

**原因**:
- 提高系统整体可用性
- 防止热门分片过度集中
- 加速后期下载速度

**对比其他算法**:
- Sequential: 顺序下载，简单但不利于 swarm
- Random: 随机选择，均衡但不够智能
- Rarest First: 最优选择，BitTorrent 标准算法

### 3. 为什么要实现状态机？

**Peer 状态机的必要性**:
```
只有当 peer_choking=False 且 am_interested=True 时，
才能从对方下载数据。

状态转换:
收到 Choke 消息 → peer_choking = True  → 停止请求
收到 Unchoke 消息 → peer_choking = False → 可以请求
```

### 4. 为什么使用 Compact Peer 列表？

**优势**:
- 节省带宽：6 字节 vs ~70 字节（非 compact）
- 解析快速：固定长度，直接切片
- Tracker 负载低

---

## 🚀 性能优化建议

### 1. 连接池优化
```python
# 当前：固定最大连接数
max_peers = 50

# 优化：动态调整
if download_speed < threshold:
    increase_max_peers()
else:
    decrease_max_peers()  # 减少 overhead
```

### 2. 请求管道化
```python
# 当前：等待一个块完成再请求下一个
await request_block()
await receive_piece()

# 优化：批量请求
for i in range(5):  # 同时请求 5 个块
    await request_block()
```

### 3. 磁盘缓存
```python
# 当前：每个块直接写入磁盘
file_manager.write_block(offset, data)

# 优化：内存缓存 + 批量写入
cache[piece_index] = data
if cache_full():
    flush_to_disk()
```

---

## 📊 扩展性设计

### 预留扩展点

1. **DHT 网络** (`network/dht.py`)
   ```python
   class DHTNode:
       async def find_peers(info_hash)
       async def bootstrap(nodes)
   ```

2. **磁力链接** (`core/magnet.py`)
   ```python
   class MagnetLink:
       def parse(uri)
       async def fetch_metadata(dht)
   ```

3. **PEX** (`network/pex.py`)
   ```python
   class PeerExchange:
       def send_pex(peer)
       def receive_pex(peer)
   ```

4. **WebUI** (`webui/server.py`)
   ```python
   class WebServer:
       async def handle_request()
       async def send_progress()
   ```

---

## 🧪 测试策略

### 单元测试
```python
# 测试 Bencode 编解码
test_encode_decode_integer()
test_encode_decode_nested_dict()

# 测试 PieceManager
test_rarest_first_algorithm()
test_piece_selection()
```

### 集成测试
```python
# 模拟 Tracker 响应
mock_tracker_response()

# 模拟 Peer 连接
mock_peer_handshake()
```

### 端到端测试
```python
# 使用真实种子文件
test_download_small_file()
test_download_multi_file()
```

---

## 📝 总结

BingTorrent 的架构设计遵循以下原则：

1. **高内聚低耦合**: 每个模块职责明确
2. **异步优先**: 充分利用 asyncio 并发能力
3. **可扩展性**: 预留 DHT、磁力链接等扩展点
4. **可测试性**: 清晰的接口，便于单元测试
5. **可读性**: 详细的注释和文档

这个架构不仅适合学习 BitTorrent 协议，也为构建生产级应用打下了坚实基础。
