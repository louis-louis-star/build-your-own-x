"""
Config 配置管理单元测试
"""

import unittest
import sys
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.config import Config, get_config, set_config


class TestConfigDefaults(unittest.TestCase):
    """测试配置默认值"""
    
    def test_default_peer_id_prefix(self):
        """测试默认 Peer ID 前缀"""
        config = Config()
        self.assertEqual(config.peer_id_prefix, "-BN0100-")
    
    def test_default_port(self):
        """测试默认端口"""
        config = Config()
        self.assertEqual(config.port, 6881)
    
    def test_default_max_peers(self):
        """测试默认最大 Peer 数"""
        config = Config()
        self.assertEqual(config.max_peers, 50)
    
    def test_default_timeouts(self):
        """测试默认超时设置"""
        config = Config()
        self.assertEqual(config.connect_timeout, 10)
        self.assertEqual(config.read_timeout, 30)
        self.assertEqual(config.tracker_timeout, 30)
    
    def test_default_piece_size(self):
        """测试默认分片大小"""
        config = Config()
        self.assertEqual(config.piece_size, 16 * 1024)  # 16KB
    
    def test_default_log_level(self):
        """测试默认日志级别"""
        config = Config()
        self.assertEqual(config.log_level, "INFO")


class TestConfigPeerIdGeneration(unittest.TestCase):
    """测试 Peer ID 生成"""
    
    def test_peer_id_is_generated(self):
        """测试 Peer ID 自动生成"""
        config = Config()
        self.assertTrue(hasattr(config, 'peer_id'))
        self.assertIsNotNone(config.peer_id)
    
    def test_peer_id_length(self):
        """测试 Peer ID 长度（20字节）"""
        config = Config()
        peer_id = config.peer_id.encode('utf-8')
        self.assertEqual(len(peer_id), 20)
    
    def test_peer_id_prefix_preserved(self):
        """测试 Peer ID 保留前缀"""
        config = Config()
        self.assertTrue(config.peer_id.startswith(config.peer_id_prefix))
    
    def test_peer_id_uniqueness(self):
        """测试 Peer ID 唯一性"""
        config1 = Config()
        config2 = Config()
        self.assertNotEqual(config1.peer_id, config2.peer_id)


class TestConfigDownloadDir(unittest.TestCase):
    """测试下载目录配置"""
    
    def test_default_download_dir(self):
        """测试默认下载目录"""
        config = Config()
        self.assertIn("downloads", config.download_dir)
    
    def test_custom_download_dir(self):
        """测试自定义下载目录"""
        import tempfile
        temp_dir = tempfile.mkdtemp()
        config = Config(download_dir=temp_dir)
        self.assertEqual(config.download_dir, temp_dir)
        
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)


class TestGlobalConfig(unittest.TestCase):
    """测试全局配置"""
    
    def tearDown(self):
        """清理：重置配置"""
        from utils import config
        config.default_config = Config()
    
    def test_get_config_returns_instance(self):
        """测试获取配置实例"""
        config = get_config()
        self.assertIsInstance(config, Config)
    
    def test_set_config_updates_values(self):
        """测试设置配置"""
        set_config(max_peers=30)
        config = get_config()
        self.assertEqual(config.max_peers, 30)
    
    def test_set_config_invalid_option(self):
        """测试设置无效配置项"""
        with self.assertRaises(AttributeError):
            set_config(invalid_option=123)
    
    def test_set_config_multiple_values(self):
        """测试同时设置多个配置"""
        set_config(max_peers=25, log_level="DEBUG", port=7000)
        config = get_config()
        self.assertEqual(config.max_peers, 25)
        self.assertEqual(config.log_level, "DEBUG")
        self.assertEqual(config.port, 7000)


class TestConfigValidation(unittest.TestCase):
    """测试配置验证"""
    
    def test_positive_port(self):
        """测试端口为正数"""
        config = Config(port=8080)
        self.assertGreater(config.port, 0)
    
    def test_positive_max_peers(self):
        """测试最大 Peer 数为正数"""
        config = Config(max_peers=100)
        self.assertGreater(config.max_peers, 0)
    
    def test_positive_timeout(self):
        """测试超时为正数"""
        config = Config(connect_timeout=15)
        self.assertGreater(config.connect_timeout, 0)


if __name__ == '__main__':
    unittest.main()
