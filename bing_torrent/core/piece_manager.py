"""
分片管理器 - Piece Manager

职责：
1. 跟踪哪些分片已下载、哪些缺失
2. 实现分片选择算法（Rarest First）
3. 分配下载任务给 Peer
4. 管理未决请求

核心算法：
- Rarest First: 优先下载全网拥有者最少的分片
- Endgame Mode: 残局模式，最后几个分片向所有 Peer 请求
"""

import random
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict

from utils.logger import get_logger
from utils.config import get_config

logger = get_logger("core.piece_manager")


@dataclass
class BlockRequest:
    """数据块请求"""
    piece_index: int
    begin: int
    length: int
    peer_id: str  # 请求的 Peer ID
    
    def __hash__(self):
        return hash((self.piece_index, self.begin, self.length))


class PieceManager:
    """分片管理器"""
    
    def __init__(self, total_pieces: int, piece_length: int, last_piece_length: int):
        """
        初始化分片管理器
        
        Args:
            total_pieces: 总分片数
            piece_length: 每个分片的长度（最后一个分片可能不同）
            last_piece_length: 最后一个分片的长度
        """
        self.total_pieces = total_pieces
        self.piece_length = piece_length
        self.last_piece_length = last_piece_length
        
        # 分片状态
        self.downloaded_pieces: Set[int] = set()  # 已下载的分片
        self.requested_pieces: Dict[int, Set[str]] = defaultdict(set)  # 正在请求的分片 {piece_index: {peer_ids}}
        
        # 未决请求（已发送但未收到响应）
        self.pending_requests: Dict[str, Set[BlockRequest]] = defaultdict(set)  # {peer_id: {requests}}
        
        # Peer 拥有的分片信息 {peer_id: bitfield}
        self.peer_bitfields: Dict[str, bytearray] = {}
        
        # 分片稀有度计数 {piece_index: count}
        self.piece_rarity: Dict[int, int] = defaultdict(int)
        
        # 配置
        self.config = get_config()
        self.block_size = self.config.request_size
        
        logger.info(f"PieceManager initialized: {total_pieces} pieces, length={piece_length}")
    
    def init_bitfield(self, peer_id: str, bitfield: bytearray) -> None:
        """
        初始化或更新 Peer 的位域信息
        
        Args:
            peer_id: Peer ID
            bitfield: 位域数据
        """
        self.peer_bitfields[peer_id] = bitfield
        
        # 更新稀有度计数
        for piece_index in range(self.total_pieces):
            if self._has_piece(bitfield, piece_index):
                self.piece_rarity[piece_index] += 1
    
    def remove_peer(self, peer_id: str) -> None:
        """
        移除 Peer 及其相关信息
        
        Args:
            peer_id: Peer ID
        """
        if peer_id in self.peer_bitfields:
            bitfield = self.peer_bitfields.pop(peer_id)
            # 减少稀有度计数
            for piece_index in range(self.total_pieces):
                if self._has_piece(bitfield, piece_index):
                    self.piece_rarity[piece_index] -= 1
        
        # 清理该 Peer 的请求
        if peer_id in self.requested_pieces:
            del self.requested_pieces[peer_id]
        if peer_id in self.pending_requests:
            del self.pending_requests[peer_id]
        
        logger.debug(f"Removed peer {peer_id[:8]} from PieceManager")
    
    def select_piece(self, peer_id: str) -> Optional[int]:
        """
        为指定 Peer 选择一个分片进行下载
        
        使用 Rarest First 算法：
        1. 过滤出该 Peer 拥有且我们未下载的分片
        2. 从中选择稀有度最低的分片
        3. 如果有多个相同稀有度，随机选择
        
        Args:
            peer_id: Peer ID
            
        Returns:
            选中的分片索引，如果没有可用分片则返回 None
        """
        if peer_id not in self.peer_bitfields:
            return None
        
        bitfield = self.peer_bitfields[peer_id]
        
        # 收集候选分片：Peer 有且我们没下载且未在请求中
        candidates = []
        for piece_index in range(self.total_pieces):
            if (self._has_piece(bitfield, piece_index) and
                piece_index not in self.downloaded_pieces and
                piece_index not in self.requested_pieces):
                rarity = self.piece_rarity.get(piece_index, 0)
                candidates.append((rarity, piece_index))
        
        if not candidates:
            return None
        
        # 按稀有度排序，选择最稀有的
        candidates.sort(key=lambda x: x[0])
        min_rarity = candidates[0][0]
        
        # 从最稀有的分片中随机选择一个
        rarest_pieces = [idx for rarity, idx in candidates if rarity == min_rarity]
        selected = random.choice(rarest_pieces)
        
        # 标记为正在请求
        self.requested_pieces[selected].add(peer_id)
        
        logger.debug(f"Selected piece {selected} for peer {peer_id[:8]} (rarity: {min_rarity})")
        
        return selected
    
    def create_request(self, peer_id: str, piece_index: int, block_index: int) -> Optional[BlockRequest]:
        """
        创建数据块请求
        
        Args:
            peer_id: Peer ID
            piece_index: 分片索引
            block_index: 块索引（分片内的第几个块）
            
        Returns:
            BlockRequest 对象，如果无效则返回 None
        """
        # 计算分片长度
        if piece_index == self.total_pieces - 1:
            piece_len = self.last_piece_length
        else:
            piece_len = self.piece_length
        
        # 计算块的起始位置和长度
        begin = block_index * self.block_size
        length = min(self.block_size, piece_len - begin)
        
        if length <= 0:
            return None
        
        request = BlockRequest(
            piece_index=piece_index,
            begin=begin,
            length=length,
            peer_id=peer_id
        )
        
        self.pending_requests[peer_id].add(request)
        
        return request
    
    def complete_request(self, peer_id: str, request: BlockRequest) -> None:
        """
        完成一个请求（收到数据后调用）
        
        Args:
            peer_id: Peer ID
            request: 完成的请求
        """
        if peer_id in self.pending_requests:
            self.pending_requests[peer_id].discard(request)
    
    def cancel_requests_for_peer(self, peer_id: str) -> List[BlockRequest]:
        """
        取消某个 Peer 的所有未决请求
        
        Args:
            peer_id: Peer ID
            
        Returns:
            被取消的请求列表
        """
        cancelled = list(self.pending_requests.get(peer_id, set()))
        self.pending_requests[peer_id].clear()
        return cancelled
    
    def mark_piece_complete(self, piece_index: int) -> None:
        """
        标记分片下载完成
        
        Args:
            piece_index: 分片索引
        """
        self.downloaded_pieces.add(piece_index)
        
        # 清理请求记录
        if piece_index in self.requested_pieces:
            del self.requested_pieces[piece_index]
        
        logger.info(f"Piece {piece_index} completed ({len(self.downloaded_pieces)}/{self.total_pieces})")
    
    def is_piece_downloaded(self, piece_index: int) -> bool:
        """检查分片是否已下载"""
        return piece_index in self.downloaded_pieces
    
    def is_download_complete(self) -> bool:
        """检查是否所有分片都已下载"""
        return len(self.downloaded_pieces) == self.total_pieces
    
    def get_download_progress(self) -> float:
        """获取下载进度（0.0 - 1.0）"""
        if self.total_pieces == 0:
            return 0.0
        return len(self.downloaded_pieces) / self.total_pieces
    
    def get_remaining_blocks_count(self, piece_index: int) -> int:
        """获取分片剩余的块数量"""
        if piece_index == self.total_pieces - 1:
            piece_len = self.last_piece_length
        else:
            piece_len = self.piece_length
        
        total_blocks = (piece_len + self.block_size - 1) // self.block_size
        
        # 计算已完成的块数（简化：假设请求的都是连续的）
        requested_count = sum(
            1 for reqs in self.pending_requests.values()
            for req in reqs
            if req.piece_index == piece_index
        )
        
        return total_blocks - requested_count
    
    @staticmethod
    def _has_piece(bitfield: bytearray, piece_index: int) -> bool:
        """检查位域中是否包含指定分片"""
        byte_index = piece_index // 8
        bit_index = 7 - (piece_index % 8)
        
        if byte_index >= len(bitfield):
            return False
        
        return (bitfield[byte_index] >> bit_index) & 1 == 1
    
    def get_status(self) -> dict:
        """获取管理器状态（用于调试和监控）"""
        return {
            'total_pieces': self.total_pieces,
            'downloaded_pieces': len(self.downloaded_pieces),
            'pending_requests': sum(len(reqs) for reqs in self.pending_requests.values()),
            'connected_peers': len(self.peer_bitfields),
            'progress': f"{self.get_download_progress() * 100:.2f}%"
        }
