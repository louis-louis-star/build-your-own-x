"""
配置管理模块

管理 BingTorrent 的全局配置参数
"""

import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Config:
    """BingTorrent 配置类"""
    
    # 网络配置
    peer_id_prefix: str = "-BN0100-"  # Peer ID 前缀（8字节）
    port: int = 6881  # 监听端口
    max_peers: int = 50  # 最大连接 Peer 数
    connect_timeout: int = 10  # 连接超时时间（秒）
    read_timeout: int = 30  # 读取超时时间（秒）
    
    # Tracker 配置
    tracker_timeout: int = 30  # Tracker 请求超时
    announce_interval: int = 1800  # 宣告间隔（秒）
    
    # 下载配置
    piece_size: int = 16 * 1024  # 默认分片大小（16KB）
    max_pending_requests: int = 5  # 每个 Peer 最大未决请求数
    request_size: int = 16 * 1024  # 请求块大小（16KB）
    
    # 存储配置
    download_dir: str = field(default_factory=lambda: os.path.join(os.getcwd(), "downloads"))
    cache_size: int = 1024 * 1024  # 缓存大小（1MB）
    
    # 日志配置
    log_level: str = "INFO"
    log_file: Optional[str] = None
    
    def __post_init__(self):
        """初始化后处理"""
        # 确保下载目录存在
        os.makedirs(self.download_dir, exist_ok=True)
        
        # 生成唯一的 Peer ID
        import random
        import string
        random_suffix = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
        self.peer_id = self.peer_id_prefix + random_suffix


# 全局配置实例
default_config = Config()


def get_config() -> Config:
    """获取全局配置"""
    return default_config


def set_config(**kwargs) -> None:
    """更新配置"""
    for key, value in kwargs.items():
        if hasattr(default_config, key):
            setattr(default_config, key, value)
        else:
            raise AttributeError(f"Unknown config option: {key}")
