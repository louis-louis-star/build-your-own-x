"""
文件 IO、断点续传、磁盘缓存管理

负责：
1. 创建和管理下载文件
2. 分片数据的写入和读取
3. 哈希校验
4. 断点续传支持
"""

import os
import hashlib
from pathlib import Path
from typing import List, Optional, Dict
from dataclasses import dataclass, field

from utils.logger import get_logger
from utils.config import get_config

logger = get_logger("storage.file_manager")


@dataclass
class FileInfo:
    """文件信息"""
    path: str
    length: int


class FileManager:
    """文件管理器"""
    
    def __init__(self, files: List[FileInfo], download_dir: Optional[str] = None):
        """
        初始化文件管理器
        
        Args:
            files: 文件列表
            download_dir: 下载目录（可选，默认使用配置）
        """
        self.config = get_config()
        self.download_dir = download_dir or self.config.download_dir
        self.files = files
        self.total_size = sum(f.length for f in files)
        
        # 文件句柄缓存
        self._file_handles: Dict[int, object] = {}
        
        # 创建下载目录
        os.makedirs(self.download_dir, exist_ok=True)
        
        logger.info(f"FileManager initialized: {len(files)} files, total size: {self._format_size(self.total_size)}")
    
    def initialize_files(self) -> None:
        """
        初始化文件（创建空文件，分配空间）
        """
        for i, file_info in enumerate(self.files):
            file_path = self._get_full_path(file_info.path)
            
            # 创建父目录
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # 如果文件不存在，创建空文件
            if not os.path.exists(file_path):
                try:
                    with open(file_path, 'wb') as f:
                        # 预分配空间（可选，某些文件系统支持）
                        f.seek(file_info.length - 1)
                        f.write(b'\x00')
                    logger.debug(f"Created file: {file_info.path}")
                except Exception as e:
                    logger.error(f"Failed to create file {file_info.path}: {e}")
                    raise
    
    def write_block(self, offset: int, data: bytes) -> None:
        """
        写入数据块到指定偏移位置
        
        Args:
            offset: 全局偏移量（相对于所有文件的起始位置）
            data: 要写入的数据
        """
        if offset < 0 or offset + len(data) > self.total_size:
            raise ValueError(f"Invalid offset: {offset}, data length: {len(data)}")
        
        # 找到对应的文件
        file_index, file_offset = self._find_file(offset)
        remaining_data = data
        
        while remaining_data and file_index < len(self.files):
            file_info = self.files[file_index]
            available_space = file_info.length - file_offset
            
            if len(remaining_data) <= available_space:
                # 数据可以完全写入当前文件
                self._write_to_file(file_index, file_offset, remaining_data)
                break
            else:
                # 数据跨越多个文件
                chunk = remaining_data[:available_space]
                self._write_to_file(file_index, file_offset, chunk)
                remaining_data = remaining_data[available_space:]
                file_index += 1
                file_offset = 0
    
    def read_block(self, offset: int, length: int) -> bytes:
        """
        从指定偏移位置读取数据块
        
        Args:
            offset: 全局偏移量
            length: 读取长度
            
        Returns:
            读取的数据
        """
        if offset < 0 or offset + length > self.total_size:
            raise ValueError(f"Invalid offset: {offset}, length: {length}")
        
        result = bytearray()
        remaining_length = length
        current_offset = offset
        
        while remaining_length > 0:
            file_index, file_offset = self._find_file(current_offset)
            file_info = self.files[file_index]
            
            available = file_info.length - file_offset
            read_length = min(remaining_length, available)
            
            data = self._read_from_file(file_index, file_offset, read_length)
            result.extend(data)
            
            remaining_length -= read_length
            current_offset += read_length
        
        return bytes(result)
    
    def verify_piece(self, piece_index: int, piece_data: bytes, expected_hash: bytes) -> bool:
        """
        验证分片数据的哈希值
        
        Args:
            piece_index: 分片索引
            piece_data: 分片数据
            expected_hash: 期望的 SHA1 哈希值
            
        Returns:
            是否验证通过
        """
        actual_hash = hashlib.sha1(piece_data).digest()
        is_valid = actual_hash == expected_hash
        
        if is_valid:
            logger.debug(f"Piece {piece_index} verified successfully")
        else:
            logger.warning(f"Piece {piece_index} verification failed")
            logger.debug(f"Expected: {expected_hash.hex()}, Got: {actual_hash.hex()}")
        
        return is_valid
    
    def save_progress(self, progress_file: str, downloaded_pieces: set) -> None:
        """
        保存下载进度（用于断点续传）
        
        Args:
            progress_file: 进度文件路径
            downloaded_pieces: 已下载的分片索引集合
        """
        try:
            progress_path = os.path.join(self.download_dir, progress_file)
            with open(progress_path, 'w') as f:
                # 保存已下载的分片索引（每行一个）
                for index in sorted(downloaded_pieces):
                    f.write(f"{index}\n")
            logger.debug(f"Progress saved: {len(downloaded_pieces)} pieces")
        except Exception as e:
            logger.error(f"Failed to save progress: {e}")
    
    def load_progress(self, progress_file: str) -> set:
        """
        加载下载进度
        
        Args:
            progress_file: 进度文件路径
            
        Returns:
            已下载的分片索引集合
        """
        downloaded_pieces = set()
        progress_path = os.path.join(self.download_dir, progress_file)
        
        if not os.path.exists(progress_path):
            return downloaded_pieces
        
        try:
            with open(progress_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        downloaded_pieces.add(int(line))
            logger.info(f"Progress loaded: {len(downloaded_pieces)} pieces")
        except Exception as e:
            logger.error(f"Failed to load progress: {e}")
        
        return downloaded_pieces
    
    def close(self) -> None:
        """关闭所有文件句柄"""
        for file_index, handle in self._file_handles.items():
            try:
                handle.close()
            except Exception as e:
                logger.error(f"Error closing file {file_index}: {e}")
        self._file_handles.clear()
    
    def _get_full_path(self, file_path: str) -> str:
        """获取文件的完整路径"""
        return os.path.join(self.download_dir, file_path)
    
    def _find_file(self, offset: int) -> tuple[int, int]:
        """
        根据全局偏移量找到对应的文件和文件内偏移
        
        Returns:
            (文件索引, 文件内偏移)
        """
        current_offset = offset
        for i, file_info in enumerate(self.files):
            if current_offset < file_info.length:
                return i, current_offset
            current_offset -= file_info.length
        
        raise ValueError(f"Offset {offset} is beyond total size {self.total_size}")
    
    def _write_to_file(self, file_index: int, offset: int, data: bytes) -> None:
        """写入数据到指定文件"""
        file_handle = self._get_file_handle(file_index)
        file_handle.seek(offset)
        file_handle.write(data)
        file_handle.flush()
    
    def _read_from_file(self, file_index: int, offset: int, length: int) -> bytes:
        """从指定文件读取数据"""
        file_handle = self._get_file_handle(file_index)
        file_handle.seek(offset)
        return file_handle.read(length)
    
    def _get_file_handle(self, file_index: int):
        """获取或创建文件句柄（带缓存）"""
        if file_index not in self._file_handles:
            file_path = self._get_full_path(self.files[file_index].path)
            self._file_handles[file_index] = open(file_path, 'r+b')
        return self._file_handles[file_index]
    
    @staticmethod
    def _format_size(size_bytes: int) -> str:
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.2f} TB"
    
    def __del__(self):
        """析构时关闭文件"""
        try:
            self.close()
        except:
            pass
