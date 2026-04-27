"""
FileManager 文件管理器单元测试
"""

import unittest
import sys
import os
import tempfile
import hashlib
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from storage.file_manager import FileManager, FileInfo


class TestFileManagerInitialization(unittest.TestCase):
    """测试 FileManager 初始化"""
    
    def setUp(self):
        """创建临时目录"""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """清理临时目录"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_single_file_initialization(self):
        """测试单文件初始化"""
        files = [FileInfo(path="test.txt", length=1024)]
        fm = FileManager(files, download_dir=self.temp_dir)
        
        self.assertEqual(fm.total_size, 1024)
        self.assertEqual(len(fm.files), 1)
    
    def test_multiple_files_initialization(self):
        """测试多文件初始化"""
        files = [
            FileInfo(path="file1.txt", length=500),
            FileInfo(path="file2.txt", length=1500)
        ]
        fm = FileManager(files, download_dir=self.temp_dir)
        
        self.assertEqual(fm.total_size, 2000)
        self.assertEqual(len(fm.files), 2)
    
    def test_initialize_files_creates_directories(self):
        """测试初始化文件时创建目录"""
        files = [FileInfo(path="subdir/test.txt", length=100)]
        fm = FileManager(files, download_dir=self.temp_dir)
        fm.initialize_files()
        
        file_path = os.path.join(self.temp_dir, "subdir", "test.txt")
        self.assertTrue(os.path.exists(file_path))
    
    def test_initialize_files_creates_empty_file(self):
        """测试初始化创建空文件"""
        files = [FileInfo(path="empty.txt", length=1024)]
        fm = FileManager(files, download_dir=self.temp_dir)
        fm.initialize_files()
        
        file_path = os.path.join(self.temp_dir, "empty.txt")
        self.assertTrue(os.path.exists(file_path))
        self.assertEqual(os.path.getsize(file_path), 1024)


class TestFileManagerWriteRead(unittest.TestCase):
    """测试 FileManager 读写操作"""
    
    def setUp(self):
        """创建临时目录和文件管理器"""
        self.temp_dir = tempfile.mkdtemp()
        files = [FileInfo(path="test.bin", length=4096)]
        self.fm = FileManager(files, download_dir=self.temp_dir)
        self.fm.initialize_files()
    
    def tearDown(self):
        """清理"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_write_and_read_block(self):
        """测试写入和读取数据块"""
        data = b'\x00\x01\x02\x03' * 100  # 400字节
        self.fm.write_block(0, data)
        
        read_data = self.fm.read_block(0, len(data))
        self.assertEqual(read_data, data)
    
    def test_write_at_offset(self):
        """测试在偏移位置写入"""
        data = b'Hello World'
        self.fm.write_block(100, data)
        
        read_data = self.fm.read_block(100, len(data))
        self.assertEqual(read_data, data)
    
    def test_write_across_boundary(self):
        """测试跨边界写入（如果有多文件）"""
        # 单文件情况下，测试在文件内不同位置写入
        data1 = b'First'
        data2 = b'Second'
        
        self.fm.write_block(0, data1)
        self.fm.write_block(100, data2)
        
        self.assertEqual(self.fm.read_block(0, 5), data1)
        self.assertEqual(self.fm.read_block(100, 6), data2)
    
    def test_invalid_offset_write(self):
        """测试无效偏移量写入"""
        with self.assertRaises(ValueError):
            self.fm.write_block(-1, b'data')
        
        with self.assertRaises(ValueError):
            self.fm.write_block(5000, b'data')  # 超出文件大小
    
    def test_invalid_offset_read(self):
        """测试无效偏移量读取"""
        with self.assertRaises(ValueError):
            self.fm.read_block(-1, 10)
        
        with self.assertRaises(ValueError):
            self.fm.read_block(5000, 10)


class TestFileManagerMultiFile(unittest.TestCase):
    """测试多文件场景"""
    
    def setUp(self):
        """创建多文件管理器"""
        self.temp_dir = tempfile.mkdtemp()
        files = [
            FileInfo(path="file1.bin", length=1000),
            FileInfo(path="file2.bin", length=2000)
        ]
        self.fm = FileManager(files, download_dir=self.temp_dir)
        self.fm.initialize_files()
    
    def tearDown(self):
        """清理"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_total_size_calculation(self):
        """测试总大小计算"""
        self.assertEqual(self.fm.total_size, 3000)
    
    def test_write_to_second_file(self):
        """测试写入第二个文件"""
        # 第一个文件占 0-999，第二个文件从 1000 开始
        data = b'Second file data'
        self.fm.write_block(1000, data)
        
        read_data = self.fm.read_block(1000, len(data))
        self.assertEqual(read_data, data)
    
    def test_write_across_files(self):
        """测试跨文件写入"""
        # 在第一个文件末尾和第二个文件开头写入
        data = b'A' * 100 + b'B' * 100  # 200字节
        self.fm.write_block(950, data)  # 跨越两个文件
        
        # 验证数据
        read_data = self.fm.read_block(950, 200)
        self.assertEqual(read_data, data)


class TestFileManagerHashVerification(unittest.TestCase):
    """测试哈希校验功能"""
    
    def setUp(self):
        """创建临时目录"""
        self.temp_dir = tempfile.mkdtemp()
        files = [FileInfo(path="test.bin", length=1024)]
        self.fm = FileManager(files, download_dir=self.temp_dir)
        self.fm.initialize_files()
    
    def tearDown(self):
        """清理"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_verify_piece_success(self):
        """测试成功的哈希校验"""
        data = b'Test data for hashing' * 10
        expected_hash = hashlib.sha1(data).digest()
        
        result = self.fm.verify_piece(0, data, expected_hash)
        self.assertTrue(result)
    
    def test_verify_piece_failure(self):
        """测试失败的哈希校验"""
        data = b'Test data'
        wrong_hash = hashlib.sha1(b'Wrong data').digest()
        
        result = self.fm.verify_piece(0, data, wrong_hash)
        self.assertFalse(result)
    
    def test_verify_empty_piece(self):
        """测试空分片校验"""
        data = b''
        expected_hash = hashlib.sha1(data).digest()
        
        result = self.fm.verify_piece(0, data, expected_hash)
        self.assertTrue(result)


class TestFileManagerProgress(unittest.TestCase):
    """测试进度保存和加载"""
    
    def setUp(self):
        """创建临时目录"""
        self.temp_dir = tempfile.mkdtemp()
        files = [FileInfo(path="test.bin", length=1024)]
        self.fm = FileManager(files, download_dir=self.temp_dir)
    
    def tearDown(self):
        """清理"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_save_and_load_progress(self):
        """测试保存和加载进度"""
        downloaded_pieces = {0, 2, 5, 10}
        
        # 保存进度
        self.fm.save_progress("test.bt", downloaded_pieces)
        
        # 加载进度
        loaded = self.fm.load_progress("test.bt")
        self.assertEqual(loaded, downloaded_pieces)
    
    def test_load_nonexistent_progress(self):
        """测试加载不存在的进度文件"""
        loaded = self.fm.load_progress("nonexistent.bt")
        self.assertEqual(loaded, set())
    
    def test_save_progress_creates_file(self):
        """测试保存进度创建文件"""
        self.fm.save_progress("progress.bt", {0, 1})
        
        progress_file = os.path.join(self.temp_dir, "progress.bt")
        self.assertTrue(os.path.exists(progress_file))


class TestFileManagerFormatSize(unittest.TestCase):
    """测试文件大小格式化"""
    
    def test_format_bytes(self):
        """测试字节格式化"""
        self.assertEqual(FileManager._format_size(500), "500.00 B")
    
    def test_format_kilobytes(self):
        """测试KB格式化"""
        result = FileManager._format_size(1024)
        self.assertIn("KB", result)
    
    def test_format_megabytes(self):
        """测试MB格式化"""
        result = FileManager._format_size(1024 * 1024)
        self.assertIn("MB", result)
    
    def test_format_gigabytes(self):
        """测试GB格式化"""
        result = FileManager._format_size(1024 * 1024 * 1024)
        self.assertIn("GB", result)


if __name__ == '__main__':
    unittest.main()
