"""
Handshake 握手协议单元测试
"""

import unittest
import sys
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from protocol.handshake import Handshake, PROTOCOL_STR, HANDSHAKE_SIZE


class TestHandshakeSerialization(unittest.TestCase):
    """测试握手消息序列化"""
    
    def setUp(self):
        """设置测试数据"""
        self.info_hash = b'\x00' * 20  # 20字节
        self.peer_id = b'-BN0100-123456789012'  # 20字节
    
    def test_handshake_serialize(self):
        """测试握手消息序列化"""
        handshake = Handshake(info_hash=self.info_hash, peer_id=self.peer_id)
        data = handshake.serialize()
        
        # 检查总长度
        self.assertEqual(len(data), HANDSHAKE_SIZE)
        
        # 检查协议字符串长度（1字节）
        self.assertEqual(data[0], len(PROTOCOL_STR))
        
        # 检查协议字符串
        self.assertEqual(data[1:20], PROTOCOL_STR)
        
        # 检查保留位（8字节）
        self.assertEqual(data[20:28], b'\x00' * 8)
        
        # 检查 info_hash（20字节）
        self.assertEqual(data[28:48], self.info_hash)
        
        # 检查 peer_id（20字节）
        self.assertEqual(data[48:68], self.peer_id)
    
    def test_handshake_with_custom_reserved(self):
        """测试带自定义保留位的握手"""
        reserved = b'\x00\x00\x00\x00\x00\x10\x00\x00'  # 启用DHT扩展
        handshake = Handshake(
            info_hash=self.info_hash,
            peer_id=self.peer_id,
            reserved=reserved
        )
        data = handshake.serialize()
        self.assertEqual(data[20:28], reserved)
    
    def test_invalid_info_hash_length(self):
        """测试无效的 info_hash 长度"""
        with self.assertRaises(ValueError):
            Handshake(info_hash=b'short', peer_id=self.peer_id)
    
    def test_invalid_peer_id_length(self):
        """测试无效的 peer_id 长度"""
        with self.assertRaises(ValueError):
            Handshake(info_hash=self.info_hash, peer_id=b'short')
    
    def test_invalid_reserved_length(self):
        """测试无效的 reserved 长度"""
        with self.assertRaises(ValueError):
            Handshake(
                info_hash=self.info_hash,
                peer_id=self.peer_id,
                reserved=b'short'
            )


class TestHandshakeDeserialization(unittest.TestCase):
    """测试握手消息反序列化"""
    
    def setUp(self):
        """设置测试数据"""
        self.info_hash = b'\x01' * 20
        self.peer_id = b'-BN0100-ABCDEFGHIJKL'
        self.handshake = Handshake(
            info_hash=self.info_hash,
            peer_id=self.peer_id
        )
    
    def test_handshake_deserialize(self):
        """测试握手消息反序列化"""
        data = self.handshake.serialize()
        restored, consumed = Handshake.deserialize(data)
        
        self.assertEqual(consumed, HANDSHAKE_SIZE)
        self.assertEqual(restored.info_hash, self.info_hash)
        self.assertEqual(restored.peer_id, self.peer_id)
        self.assertEqual(restored.reserved, b'\x00' * 8)
    
    def test_incomplete_handshake(self):
        """测试不完整的握手消息"""
        data = b'\x13BitTorrent protocol'  # 只有头部
        with self.assertRaises(ValueError):
            Handshake.deserialize(data)
    
    def test_invalid_protocol_string(self):
        """测试无效的协议字符串"""
        # 修改协议字符串
        data = bytearray(self.handshake.serialize())
        data[1:5] = b'XXXX'
        
        with self.assertRaises(ValueError):
            Handshake.deserialize(bytes(data))
    
    def test_empty_data(self):
        """测试空数据"""
        with self.assertRaises(ValueError):
            Handshake.deserialize(b'')


class TestHandshakeExtensions(unittest.TestCase):
    """测试握手扩展功能"""
    
    def setUp(self):
        """设置测试数据"""
        self.info_hash = b'\x00' * 20
        self.peer_id = b'-BN0100-123456789012'
    
    def test_supports_dht_false(self):
        """测试 DHT 支持检测（默认不支持）"""
        handshake = Handshake(
            info_hash=self.info_hash,
            peer_id=self.peer_id,
            reserved=b'\x00' * 8
        )
        self.assertFalse(handshake.supports_dht())
    
    def test_supports_dht_true(self):
        """测试 DHT 支持检测（支持）"""
        # 第5字节的第0位设置为1
        reserved = bytearray(8)
        reserved[5] = 0x01
        handshake = Handshake(
            info_hash=self.info_hash,
            peer_id=self.peer_id,
            reserved=bytes(reserved)
        )
        self.assertTrue(handshake.supports_dht())
    
    def test_supports_extension(self):
        """测试通用扩展位检测"""
        # 设置第0位
        reserved = bytearray(8)
        reserved[0] = 0x01
        handshake = Handshake(
            info_hash=self.info_hash,
            peer_id=self.peer_id,
            reserved=bytes(reserved)
        )
        self.assertTrue(handshake.supports_extension(0))
        self.assertFalse(handshake.supports_extension(1))
    
    def test_supports_extension_invalid_bit(self):
        """测试无效扩展位"""
        handshake = Handshake(
            info_hash=self.info_hash,
            peer_id=self.peer_id
        )
        self.assertFalse(handshake.supports_extension(-1))
        self.assertFalse(handshake.supports_extension(64))


class TestHandshakeConstants(unittest.TestCase):
    """测试握手常量"""
    
    def test_protocol_str(self):
        """测试协议字符串"""
        self.assertEqual(PROTOCOL_STR, b'BitTorrent protocol')
        self.assertEqual(len(PROTOCOL_STR), 19)
    
    def test_handshake_size(self):
        """测试握手消息大小"""
        # 1 (pstrlen) + 19 (pstr) + 8 (reserved) + 20 (info_hash) + 20 (peer_id)
        expected_size = 1 + 19 + 8 + 20 + 20
        self.assertEqual(HANDSHAKE_SIZE, expected_size)


class TestHandshakeRoundTrip(unittest.TestCase):
    """测试握手往返"""
    
    def test_full_roundtrip(self):
        """测试完整的序列化-反序列化往返"""
        info_hash = b'\xAB' * 20
        peer_id = b'-TEST01-XYZ123456789'
        reserved = b'\x00\x00\x00\x00\x00\x10\x00\x01'
        
        original = Handshake(
            info_hash=info_hash,
            peer_id=peer_id,
            reserved=reserved
        )
        
        data = original.serialize()
        restored, _ = Handshake.deserialize(data)
        
        self.assertEqual(restored.info_hash, info_hash)
        self.assertEqual(restored.peer_id, peer_id)
        self.assertEqual(restored.reserved, reserved)
    
    def test_default_reserved_roundtrip(self):
        """测试默认保留位往返"""
        original = Handshake(
            info_hash=b'\x00' * 20,
            peer_id=b'-BN0100-123456789012'
        )
        
        data = original.serialize()
        restored, _ = Handshake.deserialize(data)
        
        self.assertEqual(restored.reserved, b'\x00' * 8)


if __name__ == '__main__':
    unittest.main()
