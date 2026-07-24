# -*- coding: utf-8 -*-
"""
Call LLM Tool — LLM 调用工具

功能：调用硅基流动 LLM（DeepSeek）生成文本或结构化数据
依赖：环境变量 LLM_API_KEY, LLM_BASE_URL, LLM_MODEL
"""

import json
import logging
import os
import urllib.request
import time
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


def check_call_llm_requirements() -> bool:
    return True


CALL_LLM_SCHEMA = {
    "name": "call_llm",
    "description": "调用 LLM 生成文本或结构化数据。用于生成学习计划、评估计划质量、生成追问问题等。",
    "parameters": {
        "type": "object",
        "properties": {
            "system_prompt": {"type": "string", "description": "系统提示词（角色定义、任务描述）"},
            "user_message": {"type": "string", "description": "用户消息（输入数据、具体请求）"},
            "response_schema": {"type": "object", "description": "响应 JSON Schema（可选，用于强制结构化输出）"},
            "model": {"type": "string", "description": "模型名称（可选，默认使用配置中的模型）"},
            "temperature": {"type": "number", "description": "温度参数（0-2，默认0.7）", "default": 0.7, "minimum": 0, "maximum": 2},
        },
        "required": ["system_prompt", "user_message"]
    }
}


def _call_llm_api(system_prompt: str, user_message: str, model: str = "",
                  temperature: float = 0.7, response_schema: Optional[Dict] = None) -> Dict[str, Any]:
    api_key = os.getenv("LLM_API_KEY", "")
    base_url = os.getenv("LLM_BASE_URL", "https://api.siliconflow.cn/v1")
    model_name = model or os.getenv("LLM_MODEL", "deepseek-ai/DeepSeek-V4-Flash")

    if not api_key:
        logger.warning("LLM_API_KEY 未设置，返回 mock 数据")
        return _mock_response(user_message)

    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        "temperature": temperature,
    }

    if response_schema:
        payload["response_format"] = {"type": "json_object"}

    try:
        req = urllib.request.Request(
            f"{base_url}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read().decode("utf-8"))

        content = result["choices"][0]["message"]["content"]
        usage = result.get("usage", {})

        try:
            parsed_content = json.loads(content)
            return {
                "success": True,
                "content": parsed_content,
                "is_json": True,
                "usage": usage,
                "model": model_name,
            }
        except json.JSONDecodeError:
            return {
                "success": True,
                "content": content,
                "is_json": False,
                "usage": usage,
                "model": model_name,
            }

    except Exception as e:
        logger.error(f"LLM API 调用失败: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "content": "",
            "is_json": False,
            "model": model_name,
        }


def _mock_response(user_message: str) -> Dict[str, Any]:
    keywords = ["学习计划", "规划", "学习", "课程", "教程"]
    if any(keyword in user_message for keyword in keywords):
        return {
            "success": True,
            "content": {
                "plan_id": f"plan_{int(time.time())}",
                "goal": "学习Python数据分析",
                "total_weeks": 12,
                "created_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
                "milestones": [
                    {"week_start": 1, "week_end": 2, "phase": "Python基础语法",
                     "description": "变量、数据类型、条件判断、循环",
                     "objectives": ["掌握基础语法", "能写简单脚本"], "task_count": 10, "difficulty": 1},
                    {"week_start": 3, "week_end": 4, "phase": "函数与模块",
                     "description": "函数定义、参数传递、模块导入",
                     "objectives": ["理解函数作用域", "能组织多文件项目"], "task_count": 8, "difficulty": 2},
                ],
                "daily_tasks": [
                    {"day": 1, "title": "安装Python环境 + Hello World", "est_hours": 1.0},
                    {"day": 2, "title": "变量与数据类型练习", "est_hours": 1.5},
                ],
                "prerequisite_check": {"status": "passed", "details": [], "warnings": []},
                "evaluation": {"score": 8, "issues": [], "suggestions": []},
            },
            "is_json": True,
            "usage": {"prompt_tokens": 100, "completion_tokens": 200},
            "model": "deepseek-ai/DeepSeek-V4-Flash",
        }

    return {
        "success": True,
        "content": "这是 LLM 的模拟回复。请配置 LLM_API_KEY 环境变量以使用真实 LLM。",
        "is_json": False,
        "usage": {"prompt_tokens": 50, "completion_tokens": 30},
        "model": "mock",
    }


def _handle_call_llm(args: Dict[str, Any]) -> str:
    system_prompt = args.get("system_prompt", "")
    user_message = args.get("user_message", "")
    model = args.get("model", "")
    temperature = args.get("temperature", 0.7)
    response_schema = args.get("response_schema")

    if not system_prompt or not user_message:
        return json.dumps({"success": False, "error": "system_prompt 和 user_message 参数不能为空"}, ensure_ascii=False)

    result = _call_llm_api(system_prompt, user_message, model, temperature, response_schema)
    return json.dumps(result, ensure_ascii=False, indent=2)


try:
    from src.agent.tool_registry import registry
    registry.register(
        name="call_llm",
        toolset="learning",
        schema=CALL_LLM_SCHEMA,
        handler=_handle_call_llm,
        check_fn=check_call_llm_requirements,
        emoji="🤖",
    )
except ImportError:
    pass
