"""
Peer 管理器 - 连接池管理

职责：
1. 维护 Peer 连接池
2. 管理连接的建立和断开
3. 协调多个 Peer 的下载任务
4. 实现 Tit-for-Tat 算法（未来扩展）
"""

import asyncio
from typing import Dict, List, Set, Optional
from dataclasses import dataclass, field

from .peer_connection import PeerConnection
from .piece_manager import PieceManager
from protocol.message import Message, Request, Piece
from network.tracker import Peer as TrackerPeer
from storage.file_manager import FileManager
from utils.logger import get_logger
from utils.config import get_config

logger = get_logger("core.peer_manager")


@dataclass
class DownloadStats:
    """下载统计信息"""
    downloaded_bytes: int = 0
    uploaded_bytes: int = 0
    total_pieces_completed: int = 0
    active_connections: int = 0
    
    def __str__(self):
        return (
            f"Downloaded: {self.downloaded_bytes / (1024*1024):.2f} MB, "
            f"Pieces: {self.total_pieces_completed}, "
            f"Connections: {self.active_connections}"
        )


class PeerManager:
    """Peer 连接池管理器"""
    
    def __init__(
        self,
        info_hash: bytes,
        peer_id: bytes,
        piece_manager: PieceManager,
        file_manager: FileManager
    ):
        """
        初始化 Peer 管理器
        
        Args:
            info_hash: 种子信息哈希
            peer_id: 本地 Peer ID
            piece_manager: 分片管理器
            file_manager: 文件管理器
        """
        self.info_hash = info_hash
        self.peer_id = peer_id
        self.piece_manager = piece_manager
        self.file_manager = file_manager
        
        self.config = get_config()
        
        # 连接池
        self.connections: Dict[str, PeerConnection] = {}  # {peer_key: PeerConnection}
        self.connecting_peers: Set[str] = set()  # 正在连接的 Peer
        
        # 统计信息
        self.stats = DownloadStats()
        
        # 控制标志
        self._running = False
        self._download_tasks: List[asyncio.Task] = []
        
        logger.info("PeerManager initialized")
    
    async def add_peers(self, peers: List[TrackerPeer]) -> None:
        """
        添加 Peer 列表并尝试连接
        
        Args:
            peers: Tracker 返回的 Peer 列表
        """
        logger.info(f"Adding {len(peers)} peers to connection pool")
        
        for peer in peers:
            peer_key = f"{peer.ip}:{peer.port}"
            
            # 跳过已存在的连接
            if peer_key in self.connections or peer_key in self.connecting_peers:
                continue
            
            # 限制最大连接数
            if len(self.connections) >= self.config.max_peers:
                logger.debug(f"Max connections reached ({self.config.max_peers})")
                break
            
            # 异步连接 Peer
            self.connecting_peers.add(peer_key)
            task = asyncio.create_task(self._connect_peer(peer))
            self._download_tasks.append(task)
    
    async def _connect_peer(self, tracker_peer: TrackerPeer) -> None:
        """
        连接到单个 Peer
        
        Args:
            tracker_peer: Tracker Peer 信息
        """
        peer_key = f"{tracker_peer.ip}:{tracker_peer.port}"
        
        try:
            # 创建连接对象
            connection = PeerConnection(
                ip=tracker_peer.ip,
                port=tracker_peer.port,
                info_hash=self.info_hash,
                peer_id=self.peer_id,
                on_message=self._on_message,
                on_piece_data=self._on_piece_data
            )
            
            # 执行连接和握手
            success = await connection.connect()
            
            if success and connection.is_connected():
                self.connections[peer_key] = connection
                self.stats.active_connections = len(self.connections)
                logger.info(f"Successfully connected to {peer_key}")
                
                # 启动下载循环
                download_task = asyncio.create_task(self._download_loop(connection))
                self._download_tasks.append(download_task)
            else:
                logger.debug(f"Failed to connect to {peer_key}")
        
        except Exception as e:
            logger.error(f"Error connecting to {peer_key}: {e}")
        
        finally:
            self.connecting_peers.discard(peer_key)
    
    async def _download_loop(self, connection: PeerConnection) -> None:
        """
        下载循环：持续从 Peer 请求数据
        
        Args:
            connection: Peer 连接
        """
        peer_key = f"{connection.ip}:{connection.port}"
        
        try:
            while connection.is_connected() and self._running:
                # 等待对方 unchoke
                if not connection.can_download():
                    await asyncio.sleep(0.1)
                    continue
                
                # 选择一个分片
                piece_index = self.piece_manager.select_piece(peer_key)
                
                if piece_index is None:
                    # 没有可用分片，等待
                    await asyncio.sleep(0.5)
                    continue
                
                # 计算分片的块数量
                if piece_index == self.piece_manager.total_pieces - 1:
                    piece_length = self.piece_manager.last_piece_length
                else:
                    piece_length = self.piece_manager.piece_length
                
                num_blocks = (piece_length + self.config.request_size - 1) // self.config.request_size
                
                # 发送所有块的请求
                for block_index in range(num_blocks):
                    request = self.piece_manager.create_request(
                        peer_key, piece_index, block_index
                    )
                    
                    if request:
                        await connection.request_block(
                            request.piece_index,
                            request.begin,
                            request.length
                        )
                        
                        # 限制并发请求数
                        pending = len(self.piece_manager.pending_requests.get(peer_key, set()))
                        if pending >= self.config.max_pending_requests:
                            break
                
                # 等待一段时间再请求更多
                await asyncio.sleep(0.1)
        
        except asyncio.CancelledError:
            logger.debug(f"Download loop cancelled for {peer_key}")
        
        except Exception as e:
            logger.error(f"Download loop error for {peer_key}: {e}")
        
        finally:
            # 清理
            await self._remove_connection(peer_key)
    
    async def _on_message(self, message: Message) -> None:
        """
        收到消息时的回调
        
        Args:
            message: 收到的消息
        """
        # 这里可以处理通用消息逻辑
        pass
    
    async def _on_piece_data(self, piece_index: int, begin: int, data: bytes) -> None:
        """
        收到数据块时的回调
        
        Args:
            piece_index: 分片索引
            begin: 起始位置
            data: 数据块
        """
        try:
            # 计算全局偏移量
            offset = piece_index * self.piece_manager.piece_length + begin
            
            # 写入文件
            self.file_manager.write_block(offset, data)
            
            # 更新统计
            self.stats.downloaded_bytes += len(data)
            
            logger.debug(f"Received block: piece={piece_index}, begin={begin}, size={len(data)}")
            
            # TODO: 检查分片是否完整，如果完整则进行哈希校验
        
        except Exception as e:
            logger.error(f"Error processing piece data: {e}")
    
    async def _remove_connection(self, peer_key: str) -> None:
        """
        移除连接
        
        Args:
            peer_key: Peer 标识
        """
        if peer_key in self.connections:
            connection = self.connections.pop(peer_key)
            await connection.close()
            
            # 清理 PieceManager 中的信息
            self.piece_manager.remove_peer(peer_key)
            
            self.stats.active_connections = len(self.connections)
            logger.info(f"Removed connection: {peer_key}")
    
    async def stop(self) -> None:
        """停止所有连接和下载任务"""
        logger.info("Stopping PeerManager...")
        
        self._running = False
        
        # 取消所有任务
        for task in self._download_tasks:
            if not task.done():
                task.cancel()
        
        # 等待任务完成
        if self._download_tasks:
            await asyncio.gather(*self._download_tasks, return_exceptions=True)
        
        # 关闭所有连接
        for peer_key in list(self.connections.keys()):
            await self._remove_connection(peer_key)
        
        logger.info("PeerManager stopped")
    
    def get_stats(self) -> DownloadStats:
        """获取下载统计信息"""
        self.stats.active_connections = len(self.connections)
        return self.stats
    
    def is_running(self) -> bool:
        """检查是否正在运行"""
        return self._running
    
    def start(self) -> None:
        """启动管理器"""
        self._running = True
        logger.info("PeerManager started")
