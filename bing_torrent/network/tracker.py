"""
Tracker HTTP/HTTPS 通信模块

负责向 Tracker 服务器宣告并获取 Peer 列表。
支持 compact 模式（二进制 Peer 列表）。
"""

import struct
import asyncio
from dataclasses import dataclass, field
from typing import List, Optional
from urllib.parse import urlparse, urlencode

import aiohttp

from protocol.bencode import decode, BencodeError
from utils.logger import get_logger
from utils.config import get_config

logger = get_logger("network.tracker")


@dataclass
class Peer:
    """Peer 信息"""
    ip: str
    port: int
    peer_id: Optional[bytes] = None
    
    def __str__(self):
        return f"{self.ip}:{self.port}"
    
    def __repr__(self):
        return f"Peer({self.ip}, {self.port})"
    
    def __hash__(self):
        return hash((self.ip, self.port))
    
    def __eq__(self, other):
        if not isinstance(other, Peer):
            return False
        return self.ip == other.ip and self.port == other.port


@dataclass
class TrackerResponse:
    """Tracker 响应数据"""
    interval: int  # 下次宣告间隔（秒）
    min_interval: Optional[int] = None  # 最小宣告间隔
    complete: int = 0  # 做种者数量
    incomplete: int = 0  # 下载者数量
    peers: List[Peer] = field(default_factory=list)  # Peer 列表


class TrackerClient:
    """Tracker 客户端"""
    
    def __init__(self, announce_url: str):
        """
        初始化 Tracker 客户端
        
        Args:
            announce_url: Tracker 宣告 URL
        """
        self.announce_url = announce_url
        self.config = get_config()
    
    async def announce(
        self,
        info_hash: bytes,
        peer_id: bytes,
        port: int,
        uploaded: int = 0,
        downloaded: int = 0,
        left: int = 0,
        event: Optional[str] = None
    ) -> TrackerResponse:
        """
        向 Tracker 宣告
        
        Args:
            info_hash: 种子信息哈希（20字节）
            peer_id: Peer ID（20字节）
            port: 监听端口
            uploaded: 已上传字节数
            downloaded: 已下载字节数
            left: 剩余字节数
            event: 事件类型（started, stopped, completed）
            
        Returns:
            Tracker 响应
            
        Raises:
            Exception: 请求失败时抛出
        """
        params = {
            'info_hash': info_hash,
            'peer_id': peer_id,
            'port': port,
            'uploaded': uploaded,
            'downloaded': downloaded,
            'left': left,
            'compact': 1,  # 使用 compact 模式
            'no_peer_id': 1,
        }
        
        if event:
            params['event'] = event
        
        # 构建查询字符串（注意：info_hash 和 peer_id 需要原始字节）
        query_string = self._build_query_string(params)
        url = f"{self.announce_url}?{query_string}"
        
        logger.info(f"Announcing to tracker: {self.announce_url}")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    timeout=aiohttp.ClientTimeout(total=self.config.tracker_timeout)
                ) as response:
                    if response.status != 200:
                        raise Exception(f"Tracker returned status {response.status}")
                    
                    data = await response.read()
                    return self._parse_response(data)
        
        except asyncio.TimeoutError:
            raise Exception("Tracker request timed out")
        except Exception as e:
            logger.error(f"Tracker announcement failed: {e}")
            raise
    
    def _build_query_string(self, params: dict) -> str:
        """
        构建查询字符串（正确处理 info_hash 和 peer_id）
        
        BitTorrent 协议要求 info_hash 和 peer_id 以 URL 编码的原始字节发送
        """
        parts = []
        for key, value in params.items():
            if key in ('info_hash', 'peer_id') and isinstance(value, bytes):
                # URL 编码原始字节
                encoded = ''.join(f'%{byte:02X}' for byte in value)
                parts.append(f"{key}={encoded}")
            else:
                parts.append(f"{key}={value}")
        
        return '&'.join(parts)
    
    def _parse_response(self, data: bytes) -> TrackerResponse:
        """
        解析 Tracker 响应
        
        Args:
            data: Bencode 编码的响应数据
            
        Returns:
            TrackerResponse 对象
        """
        try:
            response_dict = decode(data)
        except BencodeError as e:
            raise Exception(f"Failed to decode tracker response: {e}")
        
        if not isinstance(response_dict, dict):
            raise Exception("Invalid tracker response format")
        
        # 检查错误
        if b'failure reason' in response_dict:
            reason = response_dict[b'failure reason'].decode('utf-8', errors='ignore')
            raise Exception(f"Tracker error: {reason}")
        
        # 解析字段
        interval = response_dict.get(b'interval', 1800)
        min_interval = response_dict.get(b'min interval')
        complete = response_dict.get(b'complete', 0)
        incomplete = response_dict.get(b'incomplete', 0)
        
        # 解析 Peer 列表
        peers = self._parse_peers(response_dict.get(b'peers', b''))
        
        logger.info(f"Tracker response: {len(peers)} peers, interval={interval}s")
        
        return TrackerResponse(
            interval=interval,
            min_interval=min_interval,
            complete=complete,
            incomplete=incomplete,
            peers=peers
        )
    
    def _parse_peers(self, peers_data) -> List[Peer]:
        """
        解析 Peer 列表（支持 compact 和非 compact 格式）
        
        Compact 格式：每 6 字节一个 Peer（4字节IP + 2字节端口）
        非 compact 格式：字典列表，包含 ip 和 port 字段
        """
        peers = []
        
        if isinstance(peers_data, bytes):
            # Compact 格式
            if len(peers_data) % 6 != 0:
                logger.warning(f"Invalid compact peer list length: {len(peers_data)}")
                return peers
            
            for i in range(0, len(peers_data), 6):
                chunk = peers_data[i:i+6]
                ip_bytes = chunk[:4]
                port = struct.unpack('!H', chunk[4:6])[0]
                ip = '.'.join(str(b) for b in ip_bytes)
                peers.append(Peer(ip=ip, port=port))
        
        elif isinstance(peers_data, list):
            # 非 compact 格式（字典列表）
            for peer_dict in peers_data:
                if isinstance(peer_dict, dict):
                    ip = peer_dict.get(b'ip', b'').decode('utf-8', errors='ignore')
                    port = peer_dict.get(b'port', 0)
                    peer_id = peer_dict.get(b'peer id')
                    if ip and port:
                        peers.append(Peer(ip=ip, port=port, peer_id=peer_id))
        
        else:
            logger.warning(f"Unknown peers format: {type(peers_data)}")
        
        return peers
