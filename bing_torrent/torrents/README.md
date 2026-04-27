# 测试用种子文件目录

将你的 `.torrent` 文件放在这个目录下进行测试。

## 推荐的测试种子

### 1. 小型测试文件（推荐首先测试）
- Ubuntu 桌面版 ISO（约 2-3GB）
- Linux Mint ISO
- 其他开源软件的安装包

### 2. 获取测试种子的途径

**合法的开源种子：**
- Ubuntu: https://releases.ubuntu.com/
- Linux Mint: https://www.linuxmint.com/edition.php
- Debian: https://cdimage.debian.org/
- Fedora: https://getfedora.org/

**测试小技巧：**
1. 先使用小文件测试（< 100MB）
2. 确保 Tracker 服务器可用
3. 观察日志输出，检查连接是否正常

## 使用方法

```bash
# 从 torrents 目录运行
python main.py torrents/ubuntu.torrent

# 或者指定完整路径
python main.py ./torrents/myfile.torrent
```

## 注意事项

⚠️ **重要提示：**
- 只下载合法、开源的内容
- 尊重版权法
- 本项目仅用于学习 BitTorrent 协议
- 当前版本是 MVP，可能不够稳定

## 调试技巧

如果下载遇到问题：

```bash
# 使用 DEBUG 级别日志
python main.py torrents/test.torrent --log-level DEBUG

# 限制 Peer 数量（便于调试）
python main.py torrents/test.torrent --max-peers 5
```
