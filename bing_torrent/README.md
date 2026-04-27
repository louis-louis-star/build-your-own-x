# BingTorrent - 高性能 BitTorrent 客户端

## 项目简介
BingTorrent 是一个从零实现的 BitTorrent 客户端，采用异步编程架构，支持高并发下载。

## 特性
- ✅ Bencode 编解码
- ✅ Tracker HTTP/HTTPS 通信
- ✅ Peer 连接管理（异步）
- ✅ Rarest First 分片选择算法
- ✅ 多文件支持
- ✅ 断点续传
- 🚧 DHT 网络（开发中）
- 🚧 磁力链接（开发中）

## 安装依赖
```bash
pip install -r requirements.txt
```

## 使用方法
```bash
python main.py <path_to_torrent_file>
```

## 项目结构
```
bing_torrent/
├── bing_torrent/          # 核心源码
│   ├── core/              # 业务逻辑层
│   ├── protocol/          # 协议实现层
│   ├── network/           # 网络通信层
│   ├── storage/           # 存储层
│   └── utils/             # 工具类
├── tests/                 # 单元测试
└── examples/              # 示例种子文件
```

## 开发路线图
- Phase 1: MVP（单文件下载）✅
- Phase 2: 并发与策略优化 🚧
- Phase 3: DHT 和磁力链接 ⏳
- Phase 4: 性能优化和完善 ⏳
