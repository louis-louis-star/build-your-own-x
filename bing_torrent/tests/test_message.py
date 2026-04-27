"""
Message 协议单元测试
"""

import unittest
import sys
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from protocol.message import (
    Message, KeepAlive, Choke, Unchoke, Interested, NotInterested,
    Have, Bitfield, Request, Piece, Cancel, Port, MessageID
)


class TestMessageSerialization(unittest.TestCase):
    """测试消息序列化"""
    
    def test_keep_alive_serialize(self):
        """测试 KeepAlive 消息序列化"""
        msg = KeepAlive()
        data = msg.serialize()
        self.assertEqual(data, b'\x00\x00\x00\x00')  # 长度为0
    
    def test_choke_serialize(self):
        """测试 Choke 消息序列化"""
        msg = Choke()
        data = msg.serialize()
        self.assertEqual(len(data), 5)  # 4字节长度 + 1字节ID
        self.assertEqual(data[4], MessageID.CHOKE)
    
    def test_unchoke_serialize(self):
        """测试 Unchoke 消息序列化"""
        msg = Unchoke()
        data = msg.serialize()
        self.assertEqual(data[4], MessageID.UNCHOKE)
    
    def test_interested_serialize(self):
        """测试 Interested 消息序列化"""
        msg = Interested()
        data = msg.serialize()
        self.assertEqual(data[4], MessageID.INTERESTED)
    
    def test_have_serialize(self):
        """测试 Have 消息序列化"""
        msg = Have(piece_index=42)
        data = msg.serialize()
        self.assertEqual(data[4], MessageID.HAVE)
        # 负载应该是 4字节的 piece_index
        self.assertEqual(len(data), 9)  # 4 + 1 + 4
    
    def test_request_serialize(self):
        """测试 Request 消息序列化"""
        msg = Request(piece_index=0, begin=1024, length=16384)
        data = msg.serialize()
        self.assertEqual(data[4], MessageID.REQUEST)
        self.assertEqual(len(data), 17)  # 4 + 1 + 12 (3个int)
    
    def test_piece_serialize(self):
        """测试 Piece 消息序列化"""
        block_data = b'\x00' * 100
        msg = Piece(piece_index=0, begin=0, block=block_data)
        data = msg.serialize()
        self.assertEqual(data[4], MessageID.PIECE)
        expected_length = 4 + 1 + 8 + 100  # length + id + index + begin + block
        self.assertEqual(len(data), expected_length)
    
    def test_cancel_serialize(self):
        """测试 Cancel 消息序列化"""
        msg = Cancel(piece_index=1, begin=0, length=16384)
        data = msg.serialize()
        self.assertEqual(data[4], MessageID.CANCEL)
    
    def test_bitfield_serialize(self):
        """测试 Bitfield 消息序列化"""
        bitfield = bytearray([0xFF, 0xC0])
        msg = Bitfield(bitfield=bitfield)
        data = msg.serialize()
        self.assertEqual(data[4], MessageID.BITFIELD)


class TestMessageDeserialization(unittest.TestCase):
    """测试消息反序列化"""
    
    def test_keep_alive_deserialize(self):
        """测试 KeepAlive 反序列化"""
        data = b'\x00\x00\x00\x00'
        msg, consumed = Message.deserialize(data)
        self.assertIsInstance(msg, KeepAlive)
        self.assertEqual(consumed, 4)
    
    def test_choke_deserialize(self):
        """测试 Choke 反序列化"""
        data = b'\x00\x00\x00\x01\x00'
        msg, consumed = Message.deserialize(data)
        self.assertIsInstance(msg, Choke)
        self.assertEqual(consumed, 5)
    
    def test_have_deserialize(self):
        """测试 Have 反序列化"""
        # 长度=5, ID=4, piece_index=42
        data = b'\x00\x00\x00\x05\x04\x00\x00\x00\x2a'
        msg, consumed = Message.deserialize(data)
        self.assertIsInstance(msg, Have)
        self.assertEqual(msg.piece_index, 42)
        self.assertEqual(consumed, 9)
    
    def test_request_deserialize(self):
        """测试 Request 反序列化"""
        import struct
        payload = struct.pack('>III', 0, 1024, 16384)
        data = b'\x00\x00\x00\r\x06' + payload  # 长度=13
        msg, consumed = Message.deserialize(data)
        self.assertIsInstance(msg, Request)
        self.assertEqual(msg.piece_index, 0)
        self.assertEqual(msg.begin, 1024)
        self.assertEqual(msg.length, 16384)
    
    def test_piece_deserialize(self):
        """测试 Piece 反序列化"""
        import struct
        block = b'\x00' * 100
        header = struct.pack('>II', 0, 0)  # piece_index, begin
        payload = header + block
        length = len(payload) + 1
        data = struct.pack('>IB', length, MessageID.PIECE) + payload
        
        msg, consumed = Message.deserialize(data)
        self.assertIsInstance(msg, Piece)
        self.assertEqual(msg.piece_index, 0)
        self.assertEqual(msg.begin, 0)
        self.assertEqual(len(msg.block), 100)
    
    def test_bitfield_deserialize(self):
        """测试 Bitfield 反序列化"""
        bitfield = bytearray([0xFF, 0xC0])
        length = len(bitfield) + 1
        data = bytes([0, 0, 0, length, MessageID.BITFIELD]) + bytes(bitfield)
        
        msg, consumed = Message.deserialize(data)
        self.assertIsInstance(msg, Bitfield)
        self.assertEqual(msg.bitfield, bytes(bitfield))
    
    def test_incomplete_message(self):
        """测试不完整消息的处理"""
        with self.assertRaises(ValueError):
            Message.deserialize(b'\x00\x00')  # 长度字段不完整
    
    def test_invalid_message_type(self):
        """测试无效消息类型"""
        # 长度=2, ID=99（无效）
        data = b'\x00\x00\x00\x02\x63\x00\x00'
        with self.assertRaises(ValueError):
            Message.deserialize(data)


class TestMessageRoundTrip(unittest.TestCase):
    """测试消息往返（序列化->反序列化）"""
    
    def test_choke_roundtrip(self):
        """测试 Choke 往返"""
        msg = Choke()
        data = msg.serialize()
        restored, _ = Message.deserialize(data)
        self.assertIsInstance(restored, Choke)
    
    def test_have_roundtrip(self):
        """测试 Have 往返"""
        msg = Have(piece_index=123)
        data = msg.serialize()
        restored, _ = Message.deserialize(data)
        self.assertIsInstance(restored, Have)
        self.assertEqual(restored.piece_index, 123)
    
    def test_request_roundtrip(self):
        """测试 Request 往返"""
        msg = Request(piece_index=5, begin=2048, length=16384)
        data = msg.serialize()
        restored, _ = Message.deserialize(data)
        self.assertIsInstance(restored, Request)
        self.assertEqual(restored.piece_index, 5)
        self.assertEqual(restored.begin, 2048)
        self.assertEqual(restored.length, 16384)
    
    def test_piece_roundtrip(self):
        """测试 Piece 往返"""
        block = b'\x01\x02\x03\x04' * 25
        msg = Piece(piece_index=10, begin=4096, block=block)
        data = msg.serialize()
        restored, _ = Message.deserialize(data)
        self.assertIsInstance(restored, Piece)
        self.assertEqual(restored.piece_index, 10)
        self.assertEqual(restored.begin, 4096)
        self.assertEqual(restored.block, block)


class TestMessageID(unittest.TestCase):
    """测试消息ID枚举"""
    
    def test_message_id_values(self):
        """测试消息ID值是否正确"""
        self.assertEqual(MessageID.CHOKE, 0)
        self.assertEqual(MessageID.UNCHOKE, 1)
        self.assertEqual(MessageID.INTERESTED, 2)
        self.assertEqual(MessageID.NOT_INTERESTED, 3)
        self.assertEqual(MessageID.HAVE, 4)
        self.assertEqual(MessageID.BITFIELD, 5)
        self.assertEqual(MessageID.REQUEST, 6)
        self.assertEqual(MessageID.PIECE, 7)
        self.assertEqual(MessageID.CANCEL, 8)
        self.assertEqual(MessageID.PORT, 9)
        self.assertEqual(MessageID.KEEP_ALIVE, -1)


if __name__ == '__main__':
    unittest.main()
