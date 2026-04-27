"""
PieceManager 单元测试
"""

import unittest
import sys
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.piece_manager import PieceManager


class TestPieceManager(unittest.TestCase):
    """测试分片管理器"""
    
    def setUp(self):
        """初始化测试环境"""
        self.total_pieces = 10
        self.piece_length = 16 * 1024  # 16KB
        self.last_piece_length = 8 * 1024  # 8KB
        
        self.manager = PieceManager(
            total_pieces=self.total_pieces,
            piece_length=self.piece_length,
            last_piece_length=self.last_piece_length
        )
    
    def test_initial_state(self):
        """测试初始状态"""
        self.assertEqual(self.manager.total_pieces, self.total_pieces)
        self.assertEqual(len(self.manager.downloaded_pieces), 0)
        self.assertFalse(self.manager.is_download_complete())
        self.assertEqual(self.manager.get_download_progress(), 0.0)
    
    def test_init_bitfield(self):
        """测试位域初始化"""
        peer_id = "peer1"
        bitfield = bytearray([0xFF, 0xC0])  # 前10位为1
        
        self.manager.init_bitfield(peer_id, bitfield)
        
        # 检查稀有度计数
        for i in range(10):
            self.assertGreater(self.manager.piece_rarity.get(i, 0), 0)
    
    def test_select_piece(self):
        """测试分片选择"""
        peer_id = "peer1"
        bitfield = bytearray([0xFF, 0xC0])
        
        self.manager.init_bitfield(peer_id, bitfield)
        
        # 应该能选择一个分片
        selected = self.manager.select_piece(peer_id)
        self.assertIsNotNone(selected)
        self.assertIn(selected, range(10))
    
    def test_mark_piece_complete(self):
        """测试标记分片完成"""
        self.manager.mark_piece_complete(0)
        
        self.assertIn(0, self.manager.downloaded_pieces)
        self.assertTrue(self.manager.is_piece_downloaded(0))
    
    def test_download_complete(self):
        """测试下载完成检测"""
        # 标记所有分片为完成
        for i in range(self.total_pieces):
            self.manager.mark_piece_complete(i)
        
        self.assertTrue(self.manager.is_download_complete())
        self.assertEqual(self.manager.get_download_progress(), 1.0)
    
    def test_remove_peer(self):
        """测试移除 Peer"""
        peer_id = "peer1"
        bitfield = bytearray([0xFF])
        
        self.manager.init_bitfield(peer_id, bitfield)
        self.manager.remove_peer(peer_id)
        
        self.assertNotIn(peer_id, self.manager.peer_bitfields)
    
    def test_get_status(self):
        """测试获取状态"""
        status = self.manager.get_status()
        
        self.assertIn('total_pieces', status)
        self.assertIn('downloaded_pieces', status)
        self.assertIn('progress', status)


class TestPieceSelectionAlgorithm(unittest.TestCase):
    """测试分片选择算法（Rarest First）"""
    
    def setUp(self):
        self.manager = PieceManager(
            total_pieces=5,
            piece_length=16384,
            last_piece_length=16384
        )
    
    def test_rarest_first(self):
        """测试最稀有优先算法"""
        # Peer1 拥有分片 0, 1, 2
        peer1_bitfield = bytearray([0xE0])  # 11100000
        self.manager.init_bitfield("peer1", peer1_bitfield)
        
        # Peer2 拥有分片 0, 1
        peer2_bitfield = bytearray([0xC0])  # 11000000
        self.manager.init_bitfield("peer2", peer2_bitfield)
        
        # 从 Peer1 选择时，应该优先选择分片 2（只有 Peer1 有）
        selected = self.manager.select_piece("peer1")
        self.assertIsNotNone(selected)
        
        # 分片 2 的稀有度应该是 1（最低）
        self.assertEqual(self.manager.piece_rarity[2], 1)


if __name__ == '__main__':
    unittest.main()
