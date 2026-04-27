"""
Bencode 编解码器单元测试
"""

import unittest
import sys
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from protocol.bencode import encode, decode, BencodeError


class TestBencodeDecode(unittest.TestCase):
    """测试 Bencode 解码功能"""
    
    def test_decode_integer(self):
        """测试整数解码"""
        self.assertEqual(decode(b'i3e'), 3)
        self.assertEqual(decode(b'i-3e'), -3)
        self.assertEqual(decode(b'i0e'), 0)
    
    def test_decode_byte_string(self):
        """测试字节串解码"""
        self.assertEqual(decode(b'4:spam'), b'spam')
        self.assertEqual(decode(b'0:'), b'')
    
    def test_decode_list(self):
        """测试列表解码"""
        result = decode(b'l4:spami3ee')
        self.assertEqual(result, [b'spam', 3])
        
        empty_list = decode(b'le')
        self.assertEqual(empty_list, [])
    
    def test_decode_dict(self):
        """测试字典解码"""
        result = decode(b'd3:cow3:moo4:spam4:eggse')
        self.assertEqual(result, {b'cow': b'moo', b'spam': b'eggs'})
        
        empty_dict = decode(b'de')
        self.assertEqual(empty_dict, {})
    
    def test_decode_nested_structure(self):
        """测试嵌套结构解码"""
        data = b'd4:spaml4:spami3eee'
        result = decode(data)
        self.assertEqual(result, {b'spam': [b'spam', 3]})
    
    def test_decode_invalid_data(self):
        """测试无效数据解码"""
        with self.assertRaises(BencodeError):
            decode(b'')
        
        with self.assertRaises(BencodeError):
            decode(b'invalid')


class TestBencodeEncode(unittest.TestCase):
    """测试 Bencode 编码功能"""
    
    def test_encode_integer(self):
        """测试整数编码"""
        self.assertEqual(encode(3), b'i3e')
        self.assertEqual(encode(-3), b'i-3e')
        self.assertEqual(encode(0), b'i0e')
    
    def test_encode_byte_string(self):
        """测试字节串编码"""
        self.assertEqual(encode(b'spam'), b'4:spam')
        self.assertEqual(encode(b''), b'0:')
    
    def test_encode_list(self):
        """测试列表编码"""
        result = encode([b'spam', 3])
        self.assertEqual(result, b'l4:spami3ee')
        
        empty_list = encode([])
        self.assertEqual(empty_list, b'le')
    
    def test_encode_dict(self):
        """测试字典编码（键应该排序）"""
        result = encode({b'cow': b'moo', b'spam': b'eggs'})
        # 字典键必须按字典序排序
        self.assertEqual(result, b'd3:cow3:moo4:spam4:eggse')
        
        empty_dict = encode({})
        self.assertEqual(empty_dict, b'de')
    
    def test_encode_nested_structure(self):
        """测试嵌套结构编码"""
        data = {b'spam': [b'spam', 3]}
        result = encode(data)
        self.assertEqual(result, b'd4:spaml4:spami3eee')
    
    def test_encode_unsupported_type(self):
        """测试不支持的类型"""
        with self.assertRaises(BencodeError):
            encode("string")  # str 不支持，必须是 bytes
        
        with self.assertRaises(BencodeError):
            encode(3.14)  # float 不支持


class TestBencodeRoundTrip(unittest.TestCase):
    """测试编码-解码往返"""
    
    def test_integer_roundtrip(self):
        """测试整数往返"""
        for value in [0, 1, -1, 12345, -12345]:
            self.assertEqual(decode(encode(value)), value)
    
    def test_byte_string_roundtrip(self):
        """测试字节串往返"""
        for value in [b'', b'a', b'spam', b'\x00\x01\x02']:
            self.assertEqual(decode(encode(value)), value)
    
    def test_list_roundtrip(self):
        """测试列表往返"""
        values = [
            [],
            [1, 2, 3],
            [b'a', b'b', b'c'],
            [1, b'spam', [2, 3]],
        ]
        for value in values:
            self.assertEqual(decode(encode(value)), value)
    
    def test_dict_roundtrip(self):
        """测试字典往返"""
        values = [
            {},
            {b'a': 1, b'b': 2},
            {b'key': b'value'},
            {b'nested': {b'inner': b'data'}},
        ]
        for value in values:
            self.assertEqual(decode(encode(value)), value)


if __name__ == '__main__':
    unittest.main()
