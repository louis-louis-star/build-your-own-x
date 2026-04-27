"""
日志封装模块

提供统一的日志记录接口
"""

import logging
import sys
from typing import Optional
import sys
from pathlib import Path

# 添加根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.config import get_config


def setup_logger(name: str = "BingTorrent", log_file: Optional[str] = None) -> logging.Logger:
    """
    设置并返回日志记录器
    
    Args:
        name: 日志记录器名称
        log_file: 日志文件路径（可选）
        
    Returns:
        配置好的 Logger 实例
    """
    config = get_config()
    
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, config.log_level.upper()))
    
    # 避免重复添加 handler
    if logger.handlers:
        return logger
    
    # 创建格式化器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 控制台 Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 文件 Handler（如果指定了日志文件）
    if log_file or config.log_file:
        file_path = log_file or config.log_file
        file_handler = logging.FileHandler(file_path, encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


# 默认日志记录器
logger = setup_logger()


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    获取日志记录器
    
    Args:
        name: 子模块名称
        
    Returns:
        Logger 实例
    """
    if name:
        return setup_logger(f"BingTorrent.{name}")
    return logger
