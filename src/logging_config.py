# -*- coding: utf-8 -*-
"""日志配置（参考股票项目简化版）"""
import logging, sys

def setup_logging(log_prefix="learn", console_level=logging.INFO):
    fmt = logging.Formatter(
        f"%(asctime)s [{log_prefix}] %(levelname)s %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(fmt)
    handler.setLevel(console_level)

    root = logging.getLogger()
    root.setLevel(console_level)
    root.handlers.clear()
    root.addHandler(handler)