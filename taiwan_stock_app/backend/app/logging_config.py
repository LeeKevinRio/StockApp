"""
統一日誌配置 — 所有模組使用 logging.getLogger(__name__)
"""
import logging
import sys


def setup_logging(level: str = "INFO") -> None:
    """初始化全域日誌格式"""
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )

    root = logging.getLogger()
    root.setLevel(numeric_level)
    # 避免重複 handler
    if not root.handlers:
        root.addHandler(handler)
