# -*- coding: utf-8 -*-
"""RuyiLearningPlanner - FastAPI 后端服务入口"""
import logging, os

from api.app import app
from src.config import setup_env, get_config
from src.logging_config import setup_logging

setup_env()
config = get_config()
setup_logging(log_prefix="learning_server")

if __name__ == "__main__":
    import uvicorn
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    uvicorn.run("server:app", host=host, port=port, reload=True)