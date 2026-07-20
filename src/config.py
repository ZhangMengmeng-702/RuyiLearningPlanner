# -*- coding: utf-8 -*-
"""环境变量与配置加载（轻量版，参考股票项目 src/config.py 简化）"""
import os

ENV_PREFIX = "LEARN_"

def setup_env():
    if os.path.exists(".env"):
        with open(".env", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, val = line.split("=", 1)
                os.environ.setdefault(key.strip(), val.strip())

def get_config():
    return {
        "dify_base_url": os.getenv("DIFY_BASE_URL", "http://localhost/v1"),
        "dify_kb_id": os.getenv("DIFY_KB_ID", ""),
        "llm_api_key": os.getenv("LLM_API_KEY", ""),
        "llm_base_url": os.getenv("LLM_BASE_URL", "https://api.siliconflow.cn/v1"),
        "llm_model": os.getenv("LLM_MODEL", "deepseek-ai/DeepSeek-V4-Flash"),
        "log_level": os.getenv("LOG_LEVEL", "INFO"),
        "api_host": os.getenv("API_HOST", "0.0.0.0"),
        "api_port": int(os.getenv("API_PORT", "8000")),
    }