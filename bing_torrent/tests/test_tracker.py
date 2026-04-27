"""
Tracker 客户端单元测试
"""

import unittest
import sys
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from network.tracker import Peer, TrackerResponse


class TestPeer(unittest.TestCase):
    """测试 Peer 类"""
    
    def test_peer_creation(self):
        """测试 Peer 创建"""
        peer = Peer(ip="192.168.1.1", port=6881)
        self.assertEqual(peer.ip, "192.168.1.1")
        self.assertEqual(peer.port, 6881)
    
    def test_peer_with_peer_id(self):
        """测试带 Peer ID 的创建"""
        peer_id = b'-BN0100-123456789012'
        peer = Peer(ip="10.0.0.1", port=7000, peer_id=peer_id)
        self.assertEqual(peer.peer_id, peer_id)
    
    def test_peer_string_representation(self):
        """测试 Peer 字符串表示"""
        peer = Peer(ip="192.168.1.1", port=6881)
        self.assertEqual(str(peer), "192.168.1.1:6881")
    
    def test_peer_equality(self):
        """测试 Peer 相等性"""
        peer1 = Peer(ip="192.168.1.1", port=6881)
        peer2 = Peer(ip="192.168.1.1", port=6881)
        peer3 = Peer(ip="192.168.1.2", port=6881)
        
        self.assertEqual(peer1, peer2)
        self.assertNotEqual(peer1, peer3)
    
    def test_peer_hash(self):
        """测试 Peer 哈希（用于集合）"""
        peer1 = Peer(ip="192.168.1.1", port=6881)
        peer2 = Peer(ip="192.168.1.1", port=6881)
        
        # 相同的 Peer 应该有相同的哈希
        self.assertEqual(hash(peer1), hash(peer2))
        
        # 可以放入集合
        peer_set = {peer1, peer2}
        self.assertEqual(len(peer_set), 1)


class TestTrackerResponse(unittest.TestCase):
    """测试 Tracker 响应"""
    
    def test_tracker_response_defaults(self):
        """测试 Tracker 响应默认值"""
        response = TrackerResponse(interval=1800)
        self.assertEqual(response.interval, 1800)
        self.assertIsNone(response.min_interval)
        self.assertEqual(response.complete, 0)
        self.assertEqual(response.incomplete, 0)
        self.assertEqual(response.peers, [])
    
    def test_tracker_response_with_peers(self):
        """测试带 Peer 列表的响应"""
        peers = [
            Peer(ip="192.168.1.1", port=6881),
            Peer(ip="192.168.1.2", port=6882)
        ]
        response = TrackerResponse(
            interval=1800,
            complete=10,
            incomplete=5,
            peers=peers
        )
        
        self.assertEqual(len(response.peers), 2)
        self.assertEqual(response.complete, 10)
        self.assertEqual(response.incomplete, 5)


class TestCompactPeerParsing(unittest.TestCase):
    """测试 Compact Peer 列表解析"""
    
    def test_parse_single_peer(self):
        """测试解析单个 Peer"""
        import struct
        
        # IP: 192.168.1.1, Port: 6881
        peer_data = bytes([192, 168, 1, 1]) + struct.pack('!H', 6881)
        
        from network.tracker import TrackerClient
        client = TrackerClient("http://tracker.example.com/announce")
        peers = client._parse_peers(peer_data)
        
        self.assertEqual(len(peers), 1)
        self.assertEqual(peers[0].ip, "192.168.1.1")
        self.assertEqual(peers[0].port, 6881)
    
    def test_parse_multiple_peers(self):
        """测试解析多个 Peer"""
        import struct
        
        # 两个 Peer
        peer1 = bytes([192, 168, 1, 1]) + struct.pack('!H', 6881)
        peer2 = bytes([10, 0, 0, 1]) + struct.pack('!H', 7000)
        peer_data = peer1 + peer2
        
        from network.tracker import TrackerClient
        client = TrackerClient("http://tracker.example.com/announce")
        peers = client._parse_peers(peer_data)
        
        self.assertEqual(len(peers), 2)
        self.assertEqual(peers[0].ip, "192.168.1.1")
        self.assertEqual(peers[1].ip, "10.0.0.1")
    
    def test_parse_empty_peer_list(self):
        """测试解析空 Peer 列表"""
        from network.tracker import TrackerClient
        client = TrackerClient("http://tracker.example.com/announce")
        peers = client._parse_peers(b'')
        self.assertEqual(peers, [])
    
    def test_parse_invalid_length(self):
        """测试解析无效长度的 Peer 数据"""
        from network.tracker import TrackerClient
        client = TrackerClient("http://tracker.example.com/announce")
        # 5字节（不是6的倍数）
        peers = client._parse_peers(b'\x00\x01\x02\x03\x04')
        self.assertEqual(peers, [])


class TestNonCompactPeerParsing(unittest.TestCase):
    """测试非 Compact Peer 列表解析"""
    
    def test_parse_dict_list(self):
        """测试解析字典列表"""
        peers_data = [
            {b'ip': b'192.168.1.1', b'port': 6881},
            {b'ip': b'10.0.0.1', b'port': 7000}
        ]
        
        from network.tracker import TrackerClient
        client = TrackerClient("http://tracker.example.com/announce")
        peers = client._parse_peers(peers_data)
        
        self.assertEqual(len(peers), 2)
        self.assertEqual(peers[0].ip, "192.168.1.1")
        self.assertEqual(peers[1].port, 7000)
    
    def test_parse_with_peer_id(self):
        """测试解析带 Peer ID 的字典"""
        peers_data = [
            {
                b'ip': b'192.168.1.1',
                b'port': 6881,
                b'peer id': b'-BN0100-123456789012'
            }
        ]
        
        from network.tracker import TrackerClient
        client = TrackerClient("http://tracker.example.com/announce")
        peers = client._parse_peers(peers_data)
        
        self.assertEqual(len(peers), 1)
        self.assertIsNotNone(peers[0].peer_id)
    
    def test_parse_empty_dict_list(self):
        """测试解析空列表"""
        from network.tracker import TrackerClient
        client = TrackerClient("http://tracker.example.com/announce")
        peers = client._parse_peers([])
        self.assertEqual(peers, [])


class TestQueryStringEncoding(unittest.TestCase):
    """测试查询字符串编码"""
    
    def test_encode_info_hash(self):
        """测试 info_hash 编码"""
        from network.tracker import TrackerClient
        client = TrackerClient("http://tracker.example.com/announce")
        
        info_hash = b'\x00\x01\x02\x03' * 5  # 20字节
        params = {'info_hash': info_hash, 'peer_id': b'test'}
        
        query_string = client._build_query_string(params)
        
        # info_hash 应该被 URL 编码
        self.assertIn('info_hash=', query_string)
        self.assertIn('%00%01%02%03', query_string)
    
    def test_encode_regular_params(self):
        """测试普通参数编码"""
        from network.tracker import TrackerClient
        client = TrackerClient("http://tracker.example.com/announce")
        
        params = {'port': 6881, 'uploaded': 0, 'downloaded': 100}
        query_string = client._build_query_string(params)
        
        self.assertIn('port=6881', query_string)
        self.assertIn('uploaded=0', query_string)
        self.assertIn('downloaded=100', query_string)


if __name__ == '__main__':
    unittest.main()
