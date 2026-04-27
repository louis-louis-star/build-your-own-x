"""
Bencode 编解码器实现

Bencode 是 BitTorrent 使用的编码格式，支持四种数据类型：
- bytes: 4:spam -> b'spam'
- int: i3e -> 3
- list: l4:spami3ee -> [b'spam', 3]
- dict: d3:cow3:moo4:spam4:eggse -> {b'cow': b'moo', b'spam': b'eggs'}
"""

from typing import Union, List, Dict

Bencodable = Union[bytes, int, List['Bencodable'], Dict[bytes, 'Bencodable']]


class BencodeError(Exception):
    """Bencode 编解码异常"""
    pass


def decode(data: bytes) -> Bencodable:
    """
    解码 Bencode 数据
    
    Args:
        data: Bencode 编码的字节数据
        
    Returns:
        解码后的 Python 对象
        
    Raises:
        BencodeError: 解码失败时抛出
    """
    if not data:
        raise BencodeError("Empty data")
    
    obj, _ = _decode_item(data, 0)
    return obj


def _decode_item(data: bytes, index: int) -> tuple[Bencodable, int]:
    """
    递归解码单个 Bencode 项
    
    Returns:
        (解码后的对象, 下一个位置的索引)
    """
    if index >= len(data):
        raise BencodeError("Unexpected end of data")
    
    byte = data[index:index+1]
    
    if byte == b'i':
        return _decode_int(data, index + 1)
    elif byte == b'l':
        return _decode_list(data, index + 1)
    elif byte == b'd':
        return _decode_dict(data, index + 1)
    elif byte.isdigit():
        return _decode_bytes(data, index)
    else:
        raise BencodeError(f"Invalid byte: {byte}")


def _decode_int(data: bytes, index: int) -> tuple[int, int]:
    """解码整数: i<integer>e"""
    try:
        end = data.index(b'e', index)
    except ValueError:
        raise BencodeError("Unterminated integer")
    
    try:
        number = int(data[index:end])
    except ValueError:
        raise BencodeError(f"Invalid integer: {data[index:end]}")
    
    return number, end + 1


def _decode_bytes(data: bytes, index: int) -> tuple[bytes, int]:
    """解码字节串: <length>:<data>"""
    colon = data.index(b':', index)
    try:
        length = int(data[index:colon])
    except ValueError:
        raise BencodeError(f"Invalid length: {data[index:colon]}")
    
    start = colon + 1
    end = start + length
    
    if end > len(data):
        raise BencodeError("Data too short for byte string")
    
    return data[start:end], end


def _decode_list(data: bytes, index: int) -> tuple[list, int]:
    """解码列表: l<bencoded values>e"""
    result = []
    
    while index < len(data):
        if data[index:index+1] == b'e':
            return result, index + 1
        
        item, index = _decode_item(data, index)
        result.append(item)
    
    raise BencodeError("Unterminated list")


def _decode_dict(data: bytes, index: int) -> tuple[dict, int]:
    """解码字典: d<bencoded key><bencoded value>e"""
    result = {}
    
    while index < len(data):
        if data[index:index+1] == b'e':
            return result, index + 1
        
        # 字典的键必须是字节串
        key, index = _decode_item(data, index)
        if not isinstance(key, bytes):
            raise BencodeError("Dictionary keys must be byte strings")
        
        value, index = _decode_item(data, index)
        result[key] = value
    
    raise BencodeError("Unterminated dictionary")


def encode(obj: Bencodable) -> bytes:
    """
    编码 Python 对象为 Bencode 格式
    
    Args:
        obj: 要编码的对象（bytes, int, list, dict）
        
    Returns:
        Bencode 编码的字节数据
        
    Raises:
        BencodeError: 编码失败时抛出
    """
    if isinstance(obj, bytes):
        return _encode_bytes(obj)
    elif isinstance(obj, int):
        return _encode_int(obj)
    elif isinstance(obj, list):
        return _encode_list(obj)
    elif isinstance(obj, dict):
        return _encode_dict(obj)
    else:
        raise BencodeError(f"Unsupported type: {type(obj)}")


def _encode_bytes(data: bytes) -> bytes:
    """编码字节串"""
    return f"{len(data)}:".encode() + data


def _encode_int(number: int) -> bytes:
    """编码整数"""
    return f"i{number}e".encode()


def _encode_list(items: list) -> bytes:
    """编码列表"""
    return b'l' + b''.join(encode(item) for item in items) + b'e'


def _encode_dict(mapping: dict) -> bytes:
    """编码字典（键必须按字典序排序）"""
    # BitTorrent 规范要求字典键必须排序
    sorted_items = sorted(mapping.items(), key=lambda x: x[0])
    return b'd' + b''.join(
        encode(key) + encode(value) 
        for key, value in sorted_items
    ) + b'e'
