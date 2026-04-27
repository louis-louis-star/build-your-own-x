from setuptools import setup, find_packages

setup(
    name="bing-torrent",
    version="0.1.0",
    author="Your Name",
    description="A high-performance BitTorrent client built from scratch",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "aiohttp>=3.8.0",
        "async-timeout>=4.0.0",
    ],
)
