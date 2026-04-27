"""
Peer 消息定义与解析

BitTorrent Peer Wire Protocol 消息格式：
- 长度字段：4字节大端整数（不包括自身）
- ID字段：1字节（消息类型）
- 负载：可变长度

消息类型：
0: choke
1: unchoke
2: interested
3: not interested
4: have (index)
5: bitfield
6: request (index, begin, length)
7: piece (index, begin, block)
8: cancel (index, begin, length)
9: port (listen-port)
"""

import struct
from enum import IntEnum
from dataclasses import dataclass
from typing import Optional


class MessageID(IntEnum):
    """消息类型枚举"""
    CHOKE = 0
    UNCHOKE = 1
    INTERESTED = 2
    NOT_INTERESTED = 3
    HAVE = 4
    BITFIELD = 5
    REQUEST = 6
    PIECE = 7
    CANCEL = 8
    PORT = 9
    KEEP_ALIVE = -1  # 特殊消息：长度为0


@dataclass
class Message:
    """Peer 消息基类"""
    msg_id: MessageID
    
    def serialize(self) -> bytes:
        """序列化消息为字节流"""
        if self.msg_id == MessageID.KEEP_ALIVE:
            return struct.pack('>I', 0)
        
        payload = self._serialize_payload()
        length = len(payload) + 1  # +1 for msg_id
        return struct.pack('>IB', length, self.msg_id) + payload
    
    def _serialize_payload(self) -> bytes:
        """序列化消息负载（子类实现）"""
        return b''
    
    @classmethod
    def deserialize(cls, data: bytes) -> tuple['Message', int]:
        """
        从字节流反序列化消息
        
        Returns:
            (Message对象, 消耗的字节数)
        """
        if len(data) < 4:
            raise ValueError("Incomplete message length")
        
        length = struct.unpack('>I', data[:4])[0]
        
        # Keep-alive 消息
        if length == 0:
            return KeepAlive(), 4
        
        if len(data) < 5:
            raise ValueError("Incomplete message id")
        
        msg_id = struct.unpack('>B', data[4:5])[0]
        
        if len(data) < 5 + length - 1:
            raise ValueError("Incomplete message payload")
        
        payload = data[5:5 + length - 1]
        
        message_class = MESSAGE_TYPES.get(msg_id)
        if message_class is None:
            raise ValueError(f"Unknown message type: {msg_id}")
        
        return message_class.deserialize_payload(payload), 5 + length - 1
    
    @classmethod
    def deserialize_payload(cls, payload: bytes) -> 'Message':
        """从负载反序列化消息（子类实现）"""
        raise NotImplementedError


@dataclass
class KeepAlive(Message):
    """保活消息（空消息）"""
    msg_id: MessageID = MessageID.KEEP_ALIVE


@dataclass
class Choke(Message):
    """阻塞消息"""
    msg_id: MessageID = MessageID.CHOKE


@dataclass
class Unchoke(Message):
    """非阻塞消息"""
    msg_id: MessageID = MessageID.UNCHOKE


@dataclass
class Interested(Message):
    """感兴趣消息"""
    msg_id: MessageID = MessageID.INTERESTED


@dataclass
class NotInterested(Message):
    """不感兴趣消息"""
    msg_id: MessageID = MessageID.NOT_INTERESTED


@dataclass
class Have(Message):
    """拥有分片消息"""
    msg_id: MessageID = MessageID.HAVE
    piece_index: int = 0
    
    def _serialize_payload(self) -> bytes:
        return struct.pack('>I', self.piece_index)
    
    @classmethod
    def deserialize_payload(cls, payload: bytes) -> 'Have':
        piece_index = struct.unpack('>I', payload)[0]
        return cls(piece_index=piece_index)


@dataclass
class Bitfield(Message):
    """位域消息（告知对方自己拥有哪些分片）"""
    msg_id: MessageID = MessageID.BITFIELD
    bitfield: bytes = b''
    
    def _serialize_payload(self) -> bytes:
        return self.bitfield
    
    @classmethod
    def deserialize_payload(cls, payload: bytes) -> 'Bitfield':
        return cls(bitfield=payload)


@dataclass
class Request(Message):
    """请求数据块消息"""
    msg_id: MessageID = MessageID.REQUEST
    piece_index: int = 0
    begin: int = 0
    length: int = 0
    
    def _serialize_payload(self) -> bytes:
        return struct.pack('>III', self.piece_index, self.begin, self.length)
    
    @classmethod
    def deserialize_payload(cls, payload: bytes) -> 'Request':
        piece_index, begin, length = struct.unpack('>III', payload)
        return cls(piece_index=piece_index, begin=begin, length=length)


@dataclass
class Piece(Message):
    """数据块消息"""
    msg_id: MessageID = MessageID.PIECE
    piece_index: int = 0
    begin: int = 0
    block: bytes = b''
    
    def _serialize_payload(self) -> bytes:
        return struct.pack('>II', self.piece_index, self.begin) + self.block
    
    @classmethod
    def deserialize_payload(cls, payload: bytes) -> 'Piece':
        piece_index, begin = struct.unpack('>II', payload[:8])
        block = payload[8:]
        return cls(piece_index=piece_index, begin=begin, block=block)


@dataclass
class Cancel(Message):
    """取消请求消息"""
    msg_id: MessageID = MessageID.CANCEL
    piece_index: int = 0
    begin: int = 0
    length: int = 0
    
    def _serialize_payload(self) -> bytes:
        return struct.pack('>III', self.piece_index, self.begin, self.length)
    
    @classmethod
    def deserialize_payload(cls, payload: bytes) -> 'Cancel':
        piece_index, begin, length = struct.unpack('>III', payload)
        return cls(piece_index=piece_index, begin=begin, length=length)


@dataclass
class Port(Message):
    """DHT 端口消息"""
    msg_id: MessageID = MessageID.PORT
    listen_port: int = 0
    
    def _serialize_payload(self) -> bytes:
        return struct.pack('>H', self.listen_port)
    
    @classmethod
    def deserialize_payload(cls, payload: bytes) -> 'Port':
        listen_port = struct.unpack('>H', payload)[0]
        return cls(listen_port=listen_port)


# 消息类型映射表
MESSAGE_TYPES = {
    MessageID.CHOKE: Choke,
    MessageID.UNCHOKE: Unchoke,
    MessageID.INTERESTED: Interested,
    MessageID.NOT_INTERESTED: NotInterested,
    MessageID.HAVE: Have,
    MessageID.BITFIELD: Bitfield,
    MessageID.REQUEST: Request,
    MessageID.PIECE: Piece,
    MessageID.CANCEL: Cancel,
    MessageID.PORT: Port,
}
