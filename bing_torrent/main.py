"""
BingTorrent - 命令行入口

使用方法:
    python main.py <path_to_torrent_file>
"""

import sys
import asyncio
import argparse
from pathlib import Path

from core.torrent import Torrent
from utils.logger import get_logger
from utils.config import set_config

logger = get_logger("main")


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description='BingTorrent - A high-performance BitTorrent client',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python -m bing_torrent main example.torrent
  python -m bing_torrent main /path/to/file.torrent --download-dir ./downloads
        """
    )
    
    parser.add_argument(
        'torrent',
        help='Path to .torrent file'
    )
    
    parser.add_argument(
        '--download-dir',
        default=None,
        help='Download directory (default: ./downloads)'
    )
    
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Logging level (default: INFO)'
    )
    
    parser.add_argument(
        '--max-peers',
        type=int,
        default=50,
        help='Maximum number of peer connections (default: 50)'
    )
    
    return parser.parse_args()


async def main_async(torrent_path: str):
    """
    异步主函数
    
    Args:
        torrent_path: .torrent 文件路径
    """
    # 检查文件是否存在
    if not Path(torrent_path).exists():
        logger.error(f"Torrent file not found: {torrent_path}")
        sys.exit(1)
    
    try:
        # 创建 Torrent 任务
        torrent = Torrent(torrent_path)
        
        # 注册信号处理（Ctrl+C）
        loop = asyncio.get_event_loop()
        for sig in ('SIGINT', 'SIGTERM'):
            try:
                loop.add_signal_handler(
                    getattr(__import__('signal'), sig),
                    lambda: asyncio.create_task(shutdown(torrent))
                )
            except NotImplementedError:
                # Windows 不支持 add_signal_handler
                pass
        
        # 启动下载
        await torrent.start()
        
        # 等待下载完成
        while not torrent.get_status().is_complete:
            await asyncio.sleep(1)
            
            # 打印进度
            status = torrent.get_status()
            print(f"\r{status}", end='', flush=True)
        
        print("\n\nDownload completed successfully!")
    
    except KeyboardInterrupt:
        logger.info("\nInterrupted by user")
    
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        sys.exit(1)
    
    finally:
        # 清理资源
        if 'torrent' in locals():
            await torrent.stop()


async def shutdown(torrent: Torrent):
    """优雅关闭"""
    logger.info("\nShutting down...")
    await torrent.stop()


def main():
    """主入口函数"""
    args = parse_arguments()
    
    # 更新配置
    if args.download_dir:
        set_config(download_dir=args.download_dir)
    
    set_config(log_level=args.log_level)
    set_config(max_peers=args.max_peers)
    
    # 打印欢迎信息
    print("=" * 60)
    print("  BingTorrent v0.1.0 - High-Performance BitTorrent Client")
    print("=" * 60)
    print()
    
    # 运行异步主函数
    try:
        asyncio.run(main_async(args.torrent))
    except KeyboardInterrupt:
        print("\nGoodbye!")


if __name__ == '__main__':
    main()
