"""
Torrent 类 - 下载任务的核心控制器

职责：
1. 解析 .torrent 文件
2. 计算 info_hash
3. 协调 PeerManager、PieceManager、FileManager
4. 管理下载生命周期（启动、暂停、停止）
"""

import hashlib
import asyncio
from pathlib import Path
from typing import Optional, List
from dataclasses import dataclass, field

from protocol.bencode import decode, encode, Bencodable
from core.piece_manager import PieceManager
from core.peer_manager import PeerManager
from network.tracker import TrackerClient, Peer as TrackerPeer
from storage.file_manager import FileManager, FileInfo
from utils.logger import get_logger
from utils.config import get_config

logger = get_logger("core.torrent")


@dataclass
class MetaInfo:
    """种子元数据"""
    announce: str  # Tracker URL
    info: dict  # info 字典
    name: str  # 文件或目录名
    piece_length: int  # 分片长度
    pieces: bytes  # 分片哈希列表（每20字节一个哈希）
    files: Optional[List[dict]] = None  # 文件列表（多文件模式）
    length: Optional[int] = None  # 文件大小（单文件模式）


@dataclass
class TorrentStatus:
    """下载状态"""
    is_running: bool = False
    is_complete: bool = False
    progress: float = 0.0  # 0.0 - 1.0
    downloaded_bytes: int = 0
    uploaded_bytes: int = 0
    num_peers: int = 0
    num_pieces_completed: int = 0
    total_pieces: int = 0
    
    def __str__(self):
        return (
            f"Progress: {self.progress * 100:.2f}%, "
            f"Peers: {self.num_peers}, "
            f"Pieces: {self.num_pieces_completed}/{self.total_pieces}"
        )


class Torrent:
    """Torrent 下载任务"""
    
    def __init__(self, torrent_path: str):
        """
        初始化 Torrent 任务
        
        Args:
            torrent_path: .torrent 文件路径
        """
        self.torrent_path = torrent_path
        self.config = get_config()
        
        # 加载和解析种子文件
        with open(torrent_path, 'rb') as f:
            self.raw_data = f.read()
        
        self.metadata = decode(self.raw_data)
        self.meta_info = self._parse_meta_info()
        self.info_hash = self._calc_info_hash()
        
        logger.info(f"Loaded torrent: {self.meta_info.name}")
        logger.info(f"Info hash: {self.info_hash.hex()}")
        logger.info(f"Tracker: {self.meta_info.announce}")
        
        # 初始化组件
        self.file_manager: Optional[FileManager] = None
        self.piece_manager: Optional[PieceManager] = None
        self.peer_manager: Optional[PeerManager] = None
        self.tracker_client: Optional[TrackerClient] = None
        
        # 状态
        self.status = TorrentStatus(total_pieces=self._get_total_pieces())
        self._monitor_task: Optional[asyncio.Task] = None
    
    def _parse_meta_info(self) -> MetaInfo:
        """解析种子元数据"""
        metadata = self.metadata
        
        announce = metadata[b'announce'].decode('utf-8')
        info = metadata[b'info']
        
        name = info[b'name'].decode('utf-8', errors='ignore')
        piece_length = info[b'piece length']
        pieces = info[b'pieces']
        
        # 判断是单文件还是多文件
        files = info.get(b'files')
        length = info.get(b'length')
        
        return MetaInfo(
            announce=announce,
            info=info,
            name=name,
            piece_length=piece_length,
            pieces=pieces,
            files=files,
            length=length
        )
    
    def _calc_info_hash(self) -> bytes:
        """计算 info_hash（SHA1 哈希）"""
        info_bytes = encode(self.meta_info.info)
        return hashlib.sha1(info_bytes).digest()
    
    def _get_total_pieces(self) -> int:
        """计算总分片数"""
        pieces_bytes = len(self.meta_info.pieces)
        return pieces_bytes // 20
    
    def _get_last_piece_length(self) -> int:
        """计算最后一个分片的长度"""
        total_size = self._get_total_size()
        piece_length = self.meta_info.piece_length
        total_pieces = self._get_total_pieces()
        
        last_piece_length = total_size % piece_length
        if last_piece_length == 0:
            last_piece_length = piece_length
        
        return last_piece_length
    
    def _get_total_size(self) -> int:
        """计算总文件大小"""
        if self.meta_info.files:
            # 多文件模式
            return sum(f[b'length'] for f in self.meta_info.files)
        else:
            # 单文件模式
            return self.meta_info.length or 0
    
    def _initialize_components(self) -> None:
        """初始化所有组件"""
        # 1. 初始化文件管理器
        files = self._build_file_list()
        self.file_manager = FileManager(files)
        self.file_manager.initialize_files()
        
        # 2. 初始化分片管理器
        total_pieces = self._get_total_pieces()
        piece_length = self.meta_info.piece_length
        last_piece_length = self._get_last_piece_length()
        
        self.piece_manager = PieceManager(total_pieces, piece_length, last_piece_length)
        
        # 3. 初始化 Tracker 客户端
        self.tracker_client = TrackerClient(self.meta_info.announce)
        
        # 4. 初始化 Peer 管理器
        self.peer_manager = PeerManager(
            info_hash=self.info_hash,
            peer_id=self.config.peer_id.encode('utf-8')[:20],
            piece_manager=self.piece_manager,
            file_manager=self.file_manager
        )
    
    def _build_file_list(self) -> List[FileInfo]:
        """构建文件列表"""
        files = []
        
        if self.meta_info.files:
            # 多文件模式
            for file_dict in self.meta_info.files:
                path_parts = [p.decode('utf-8', errors='ignore') for p in file_dict[b'path']]
                file_path = str(Path(self.meta_info.name).joinpath(*path_parts))
                file_length = file_dict[b'length']
                files.append(FileInfo(path=file_path, length=file_length))
        else:
            # 单文件模式
            file_path = self.meta_info.name
            file_length = self.meta_info.length or 0
            files.append(FileInfo(path=file_path, length=file_length))
        
        return files
    
    async def start(self) -> None:
        """启动下载任务"""
        if self.status.is_running:
            logger.warning("Torrent is already running")
            return
        
        logger.info("Starting torrent download...")
        
        try:
            # 1. 初始化组件
            self._initialize_components()
            
            # 2. 启动 Peer 管理器
            self.peer_manager.start()
            
            # 3. 从 Tracker 获取 Peer 列表
            await self._announce_to_tracker()
            
            # 4. 启动监控任务
            self.status.is_running = True
            self._monitor_task = asyncio.create_task(self._monitor_loop())
            
            logger.info("Torrent started successfully")
        
        except Exception as e:
            logger.error(f"Failed to start torrent: {e}")
            await self.stop()
            raise
    
    async def stop(self) -> None:
        """停止下载任务"""
        logger.info("Stopping torrent...")
        
        self.status.is_running = False
        
        # 停止监控任务
        if self._monitor_task and not self._monitor_task.done():
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        
        # 停止 Peer 管理器
        if self.peer_manager:
            await self.peer_manager.stop()
        
        # 关闭文件管理器
        if self.file_manager:
            self.file_manager.close()
        
        logger.info("Torrent stopped")
    
    async def _announce_to_tracker(self) -> None:
        """向 Tracker 宣告并获取 Peer 列表"""
        if not self.tracker_client or not self.peer_manager:
            return
        
        try:
            total_size = self._get_total_size()
            
            response = await self.tracker_client.announce(
                info_hash=self.info_hash,
                peer_id=self.config.peer_id.encode('utf-8')[:20],
                port=self.config.port,
                uploaded=self.status.uploaded_bytes,
                downloaded=self.status.downloaded_bytes,
                left=total_size - self.status.downloaded_bytes,
                event='started'
            )
            
            logger.info(f"Got {len(response.peers)} peers from tracker")
            
            # 添加 Peers
            await self.peer_manager.add_peers(response.peers)
        
        except Exception as e:
            logger.error(f"Tracker announcement failed: {e}")
    
    async def _monitor_loop(self) -> None:
        """监控循环：定期检查下载状态"""
        try:
            while self.status.is_running:
                # 更新状态
                if self.piece_manager:
                    self.status.progress = self.piece_manager.get_download_progress()
                    self.status.num_pieces_completed = len(self.piece_manager.downloaded_pieces)
                
                if self.peer_manager:
                    stats = self.peer_manager.get_stats()
                    self.status.downloaded_bytes = stats.downloaded_bytes
                    self.status.uploaded_bytes = stats.uploaded_bytes
                    self.status.num_peers = stats.active_connections
                
                # 检查是否完成
                if self.piece_manager and self.piece_manager.is_download_complete():
                    self.status.is_complete = True
                    logger.info("Download completed!")
                    break
                
                # 打印状态
                logger.info(f"Status: {self.status}")
                
                # 定期重新宣告（获取新的 Peer）
                if self.tracker_client and self.peer_manager:
                    await self._announce_to_tracker()
                
                await asyncio.sleep(30)  # 每30秒检查一次
        
        except asyncio.CancelledError:
            logger.debug("Monitor loop cancelled")
        
        except Exception as e:
            logger.error(f"Monitor loop error: {e}")
    
    def get_status(self) -> TorrentStatus:
        """获取当前状态"""
        return self.status
    
    def __repr__(self):
        return f"Torrent({self.meta_info.name}, {self.status.progress * 100:.1f}%)"
