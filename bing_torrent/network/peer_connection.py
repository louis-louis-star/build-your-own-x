"""
Peer 连接封装 - 异步 TCP 连接

负责：
1. 建立和维护与单个 Peer 的 TCP 连接
2. 握手和消息交换
3. 状态管理（choke/unchoke, interested/not interested）
4. 发送请求和接收数据块
"""

import asyncio
from typing import Optional, Callable, Awaitable
from enum import Enum, auto

from protocol.handshake import Handshake, perform_handshake
from protocol.message import (
    Message, Choke, Unchoke, Interested, NotInterested,
    Have, Bitfield, Request, Piece, Cancel, KeepAlive
)
from utils.logger import get_logger
from utils.config import get_config

logger = get_logger("network.peer_connection")


class ConnectionState(Enum):
    """连接状态"""
    DISCONNECTED = auto()
    CONNECTING = auto()
    HANDSHAKING = auto()
    CONNECTED = auto()
    CLOSING = auto()


class PeerState:
    """Peer 状态机（四个关键状态）"""
    
    def __init__(self):
        self.am_choking = True  # 我们是否阻塞对方
        self.am_interested = False  # 我们是否对对方感兴趣
        self.peer_choking = True  # 对方是否阻塞我们
        self.peer_interested = False  # 对方是否对我们感兴趣
    
    def __repr__(self):
        return (
            f"PeerState(am_choking={self.am_choking}, am_interested={self.am_interested}, "
            f"peer_choking={self.peer_choking}, peer_interested={self.peer_interested})"
        )


class PeerConnection:
    """Peer 连接管理器"""
    
    def __init__(
        self,
        ip: str,
        port: int,
        info_hash: bytes,
        peer_id: bytes,
        on_message: Optional[Callable[[Message], Awaitable[None]]] = None,
        on_piece_data: Optional[Callable[[int, int, bytes], Awaitable[None]]] = None
    ):
        """
        初始化 Peer 连接
        
        Args:
            ip: Peer IP 地址
            port: Peer 端口
            info_hash: 种子信息哈希
            peer_id: 本地 Peer ID
            on_message: 收到消息时的回调函数
            on_piece_data: 收到数据块时的回调函数 (piece_index, begin, data)
        """
        self.ip = ip
        self.port = port
        self.info_hash = info_hash
        self.peer_id = peer_id
        self.on_message = on_message
        self.on_piece_data = on_piece_data
        
        self.state = ConnectionState.DISCONNECTED
        self.peer_state = PeerState()
        
        self.reader: Optional[asyncio.StreamReader] = None
        self.writer: Optional[asyncio.StreamWriter] = None
        
        self.remote_peer_id: Optional[bytes] = None
        self.remote_handshake: Optional[Handshake] = None
        
        self.config = get_config()
        self._read_task: Optional[asyncio.Task] = None
        
        logger.debug(f"PeerConnection created for {ip}:{port}")
    
    async def connect(self) -> bool:
        """
        连接到 Peer 并执行握手
        
        Returns:
            是否成功连接
        """
        try:
            self.state = ConnectionState.CONNECTING
            logger.debug(f"Connecting to {self.ip}:{self.port}...")
            
            # 建立 TCP 连接
            self.reader, self.writer = await asyncio.wait_for(
                asyncio.open_connection(self.ip, self.port),
                timeout=self.config.connect_timeout
            )
            
            # 执行握手
            self.state = ConnectionState.HANDSHAKING
            self.remote_handshake = await perform_handshake(
                self.reader,
                self.writer,
                self.info_hash,
                self.peer_id
            )
            
            self.remote_peer_id = self.remote_handshake.peer_id
            self.state = ConnectionState.CONNECTED
            
            logger.info(f"Connected to peer {self.remote_peer_id[:8]} at {self.ip}:{self.port}")
            
            # 启动读取任务
            self._read_task = asyncio.create_task(self._read_loop())
            
            # 发送 interested 消息（表示我们对对方感兴趣）
            await self.send_message(Interested())
            self.peer_state.am_interested = True
            
            return True
        
        except asyncio.TimeoutError:
            logger.warning(f"Connection timeout: {self.ip}:{self.port}")
            await self.close()
            return False
        
        except Exception as e:
            logger.error(f"Connection failed: {self.ip}:{port} - {e}")
            await self.close()
            return False
    
    async def send_message(self, message: Message) -> None:
        """
        发送消息到 Peer
        
        Args:
            message: 要发送的消息
        """
        if self.state != ConnectionState.CONNECTED or not self.writer:
            logger.warning("Cannot send message: not connected")
            return
        
        try:
            data = message.serialize()
            self.writer.write(data)
            await self.writer.drain()
            logger.debug(f"Sent message: {message.__class__.__name__}")
        
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            await self.close()
    
    async def request_block(self, piece_index: int, begin: int, length: int) -> None:
        """
        请求数据块
        
        Args:
            piece_index: 分片索引
            begin: 起始位置
            length: 长度
        """
        if self.peer_state.peer_choking:
            logger.debug("Cannot request: peer is choking us")
            return
        
        request = Request(piece_index=piece_index, begin=begin, length=length)
        await self.send_message(request)
        logger.debug(f"Requested block: piece={piece_index}, begin={begin}, length={length}")
    
    async def cancel_request(self, piece_index: int, begin: int, length: int) -> None:
        """取消请求"""
        cancel = Cancel(piece_index=piece_index, begin=begin, length=length)
        await self.send_message(cancel)
    
    async def _read_loop(self) -> None:
        """读取消息循环（后台任务）"""
        buffer = b''
        
        try:
            while self.state == ConnectionState.CONNECTED:
                # 读取数据
                chunk = await self.reader.read(4096)
                if not chunk:
                    logger.info("Connection closed by peer")
                    await self.close()
                    break
                
                buffer += chunk
                
                # 解析消息
                while buffer:
                    try:
                        message, consumed = Message.deserialize(buffer)
                        buffer = buffer[consumed:]
                        
                        # 处理消息
                        await self._handle_message(message)
                    
                    except ValueError as e:
                        # 数据不完整，等待更多数据
                        if len(buffer) < 4:
                            break
                        else:
                            logger.error(f"Message parse error: {e}")
                            await self.close()
                            break
        
        except asyncio.CancelledError:
            logger.debug("Read loop cancelled")
        
        except Exception as e:
            logger.error(f"Read loop error: {e}")
            await self.close()
    
    async def _handle_message(self, message: Message) -> None:
        """
        处理收到的消息
        
        Args:
            message: 收到的消息
        """
        logger.debug(f"Received message: {message.__class__.__name__}")
        
        # 更新状态
        if isinstance(message, Choke):
            self.peer_state.peer_choking = True
            logger.debug("Peer choked us")
        
        elif isinstance(message, Unchoke):
            self.peer_state.peer_choking = False
            logger.debug("Peer unchoked us")
        
        elif isinstance(message, Interested):
            self.peer_state.peer_interested = True
        
        elif isinstance(message, NotInterested):
            self.peer_state.peer_interested = False
        
        elif isinstance(message, Have):
            logger.debug(f"Peer has piece {message.piece_index}")
        
        elif isinstance(message, Bitfield):
            logger.debug(f"Received bitfield ({len(message.bitfield)} bytes)")
        
        elif isinstance(message, Piece):
            # 收到数据块，调用回调
            if self.on_piece_data:
                await self.on_piece_data(message.piece_index, message.begin, message.block)
        
        # 调用通用消息回调
        if self.on_message:
            await self.on_message(message)
    
    async def close(self) -> None:
        """关闭连接"""
        if self.state == ConnectionState.CLOSING or self.state == ConnectionState.DISCONNECTED:
            return
        
        self.state = ConnectionState.CLOSING
        
        # 取消读取任务
        if self._read_task and not self._read_task.done():
            self._read_task.cancel()
            try:
                await self._read_task
            except asyncio.CancelledError:
                pass
        
        # 关闭 writer
        if self.writer:
            try:
                self.writer.close()
                await self.writer.wait_closed()
            except Exception as e:
                logger.error(f"Error closing writer: {e}")
        
        self.state = ConnectionState.DISCONNECTED
        logger.info(f"Connection closed: {self.ip}:{self.port}")
    
    def is_connected(self) -> bool:
        """检查是否已连接"""
        return self.state == ConnectionState.CONNECTED
    
    def can_download(self) -> bool:
        """检查是否可以下载（对方未阻塞且我们感兴趣）"""
        return (
            self.state == ConnectionState.CONNECTED and
            not self.peer_state.peer_choking and
            self.peer_state.am_interested
        )
    
    def __repr__(self):
        return f"PeerConnection({self.ip}:{self.port}, state={self.state.name})"
