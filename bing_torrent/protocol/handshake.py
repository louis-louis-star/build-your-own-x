"""
握手协议实现

BitTorrent 握手格式：
- pstrlen: 1字节（协议标识符长度，固定为19）
- pstr: 19字节（"BitTorrent protocol"）
- reserved: 8字节（保留位，用于扩展协议）
- info_hash: 20字节（种子信息的 SHA1 哈希）
- peer_id: 20字节（Peer ID）

握手后，双方可以开始交换消息。
"""

import struct
from dataclasses import dataclass
from typing import Optional

from utils.logger import get_logger

logger = get_logger("protocol.handshake")


PROTOCOL_STR = b'BitTorrent protocol'
PROTOCOL_LEN = len(PROTOCOL_STR)
HANDSHAKE_SIZE = 49 + len(PROTOCOL_STR)  # 1 + 19 + 8 + 20 + 20


@dataclass
class Handshake:
    """握手消息"""
    info_hash: bytes
    peer_id: bytes
    reserved: bytes = b'\x00' * 8  # 默认无扩展
    
    def __post_init__(self):
        if len(self.info_hash) != 20:
            raise ValueError(f"info_hash must be 20 bytes, got {len(self.info_hash)}")
        if len(self.peer_id) != 20:
            raise ValueError(f"peer_id must be 20 bytes, got {len(self.peer_id)}")
        if len(self.reserved) != 8:
            raise ValueError(f"reserved must be 8 bytes, got {len(self.reserved)}")
    
    def serialize(self) -> bytes:
        """序列化握手消息"""
        return (
            struct.pack('B', PROTOCOL_LEN) +
            PROTOCOL_STR +
            self.reserved +
            self.info_hash +
            self.peer_id
        )
    
    @classmethod
    def deserialize(cls, data: bytes) -> tuple['Handshake', int]:
        """
        从字节流反序列化握手消息
        
        Returns:
            (Handshake对象, 消耗的字节数)
        """
        if len(data) < 1:
            raise ValueError("Incomplete handshake length")
        
        pstrlen = struct.unpack('B', data[0:1])[0]
        
        if pstrlen != PROTOCOL_LEN:
            raise ValueError(f"Invalid protocol string length: {pstrlen}")
        
        expected_size = 1 + pstrlen + 8 + 20 + 20
        if len(data) < expected_size:
            raise ValueError(f"Incomplete handshake: need {expected_size}, got {len(data)}")
        
        offset = 1
        pstr = data[offset:offset + pstrlen]
        offset += pstrlen
        
        if pstr != PROTOCOL_STR:
            raise ValueError(f"Invalid protocol string: {pstr}")
        
        reserved = data[offset:offset + 8]
        offset += 8
        
        info_hash = data[offset:offset + 20]
        offset += 20
        
        peer_id = data[offset:offset + 20]
        offset += 20
        
        return cls(info_hash=info_hash, peer_id=peer_id, reserved=reserved), offset
    
    def supports_dht(self) -> bool:
        """检查是否支持 DHT 扩展（第5位）"""
        return (self.reserved[5] & 0x01) != 0
    
    def supports_extension(self, extension_bit: int) -> bool:
        """检查是否支持指定扩展位"""
        if extension_bit < 0 or extension_bit > 63:
            return False
        byte_index = extension_bit // 8
        bit_index = extension_bit % 8
        if byte_index >= len(self.reserved):
            return False
        return (self.reserved[byte_index] >> bit_index) & 1 == 1


async def perform_handshake(
    reader, 
    writer, 
    info_hash: bytes, 
    peer_id: bytes
) -> Handshake:
    """
    执行握手流程
    
    Args:
        reader: asyncio StreamReader
        writer: asyncio StreamWriter
        info_hash: 种子信息哈希
        peer_id: 本地 Peer ID
        
    Returns:
        对方的握手消息
    """
    # 发送握手
    local_handshake = Handshake(info_hash=info_hash, peer_id=peer_id)
    writer.write(local_handshake.serialize())
    await writer.drain()
    
    logger.debug(f"Sent handshake to peer")
    
    # 接收握手
    data = b''
    while len(data) < HANDSHAKE_SIZE:
        chunk = await reader.read(HANDSHAKE_SIZE - len(data))
        if not chunk:
            raise ConnectionError("Connection closed during handshake")
        data += chunk
    
    remote_handshake, _ = Handshake.deserialize(data)
    
    # 验证 info_hash
    if remote_handshake.info_hash != info_hash:
        raise ValueError("Remote peer has different info_hash")
    
    logger.debug(f"Handshake completed with peer {remote_handshake.peer_id[:8]}")
    
    return remote_handshake
