# BingTorrent 快速开始指南

## 📦 安装

### 1. 安装依赖
```bash
cd bing_torrent
pip install -r requirements.txt
```

### 2. 验证安装（运行测试）
```bash
python -m pytest tests/test_bencode.py -v
python -m pytest tests/test_piece_manager.py -v
```

## 🚀 使用方法

### 基本用法
```bash
python main.py example.torrent
```

### 高级选项
```bash
# 指定下载目录
python main.py example.torrent --download-dir ./my_downloads

# 调整日志级别
python main.py example.torrent --log-level DEBUG

# 限制最大连接数
python main.py example.torrent --max-peers 30
```

## 🏗️ 项目架构

```
bing_torrent/
├── bing_torrent/              # 核心源码
│   ├── __init__.py
│   ├── main.py                # CLI 入口
│   │
│   ├── core/                  # 业务逻辑层
│   │   ├── torrent.py         # Torrent 主控制器
│   │   ├── piece_manager.py   # 分片管理器（Rarest First 算法）
│   │   └── peer_manager.py    # Peer 连接池管理
│   │
│   ├── protocol/              # 协议实现层
│   │   ├── bencode.py         # Bencode 编解码
│   │   ├── message.py         # Peer 消息定义
│   │   └── handshake.py       # 握手协议
│   │
│   ├── network/               # 网络通信层
│   │   ├── tracker.py         # Tracker HTTP 通信
│   │   └── peer_connection.py # Peer TCP 连接（异步）
│   │
│   ├── storage/               # 存储层
│   │   └── file_manager.py    # 文件 IO、断点续传
│   │
│   └── utils/                 # 工具类
│       ├── config.py          # 配置管理
│       └── logger.py          # 日志封装
│
├── tests/                     # 单元测试
│   ├── test_bencode.py
│   └── test_piece_manager.py
│
├── requirements.txt
└── setup.py
```

## 🔧 开发路线图

### ✅ Phase 1: MVP（已完成）
- [x] Bencode 编解码器
- [x] Tracker 通信
- [x] Peer 握手和连接
- [x] 单文件下载
- [x] 基础分片管理

### 🚧 Phase 2: 并发优化（进行中）
- [ ] 完善多 Peer 并发下载
- [ ] 实现完整的 Piece 校验流程
- [ ] 添加进度条 UI
- [ ] 支持多文件种子

### ⏳ Phase 3: 扩展功能
- [ ] DHT 网络支持（BEP-0005）
- [ ] 磁力链接支持（BEP-0009）
- [ ] PEX Peer 交换（BEP-0011）
- [ ] 断点续传完善

### ⏳ Phase 4: 性能优化
- [ ] Tit-for-Tat 上传算法
- [ ] uTP 协议支持
- [ ] 磁盘缓存优化
- [ ] WebUI 界面

## 📝 核心模块说明

### 1. Bencode 编解码器 (`protocol/bencode.py`)
```python
from bing_torrent.protocol.bencode import encode, decode

# 编码
data = encode({b'key': b'value', b'num': 42})

# 解码
obj = decode(data)
```

### 2. Torrent 主控制器 (`core/torrent.py`)
```python
from bing_torrent.core.torrent import Torrent

# 创建任务
torrent = Torrent("example.torrent")

# 启动下载
await torrent.start()

# 获取状态
status = torrent.get_status()
print(f"Progress: {status.progress * 100:.2f}%")
```

### 3. PieceManager 分片选择 (`core/piece_manager.py`)
- **Rarest First**: 优先下载全网拥有者最少的分片
- **Endgame Mode**: 残局模式（待实现）

## 🧪 运行测试

```bash
# 运行所有测试
python -m pytest tests/ -v

# 运行特定测试
python -m pytest tests/test_bencode.py::TestBencodeDecode -v
```

## ❓ 常见问题

### Q: 如何获取测试用的 .torrent 文件？
A: 可以从以下网站下载合法的开源种子文件：
- Ubuntu 官方镜像：https://releases.ubuntu.com/
- Linux 发行版 torrents

### Q: 下载速度慢怎么办？
A: 当前版本是 MVP，后续会优化：
- 增加 Peer 连接数（`--max-peers`）
- 实现更智能的分片选择算法
- 添加 DHT 网络支持

### Q: 支持哪些操作系统？
A: 理论上支持所有 Python 3.8+ 的系统：
- Windows ✅
- Linux ✅
- macOS ✅

## 🤝 贡献代码

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License
