# -*- coding: utf-8 -*-
"""
Call LLM Tool — LLM 调用工具

功能：调用 LLM 生成文本或结构化数据
优先使用 Hermes Agent（HTTP），fallback 到硅基流动 LLM
支持流式输出模式
依赖：环境变量 HERMES_ENABLED, HERMES_API_KEY, HERMES_BASE_URL, HERMES_MODEL
      或 LLM_API_KEY, LLM_BASE_URL, LLM_MODEL
"""

import json
import logging
import os
import urllib.request
import time
from typing import Any, Dict, Generator, List, Optional

from src.agent.tool_registry import tool

logger = logging.getLogger(__name__)

_hermes_client = None
_hermes_available = None
_hermes_last_check = 0
_HERMES_CHECK_CACHE = 30  # 30秒内不重复检查


def _get_hermes_client():
    """获取 Hermes 客户端（单例）"""
    global _hermes_client
    if _hermes_client is None:
        try:
            from src.llm.hermes_client import HermesClient
            _hermes_client = HermesClient(
                api_key=os.getenv("HERMES_API_KEY", "hermes"),
                base_url=os.getenv("HERMES_BASE_URL", "http://127.0.0.1:8642/v1"),
                model=os.getenv("HERMES_MODEL", "hermes-agent"),
                timeout=10.0,  # 缩短超时到10秒
            )
        except ImportError:
            logger.warning("HermesClient 导入失败，将使用 fallback 模式")
            return None
    return _hermes_client


def _is_hermes_enabled():
    """检查是否启用 Hermes"""
    return os.getenv("HERMES_ENABLED", "false").lower() == "true"


def _is_hermes_available() -> bool:
    """快速检测 Hermes 是否可用（带缓存）"""
    global _hermes_available, _hermes_last_check
    now = time.time()
    
    if now - _hermes_last_check < _HERMES_CHECK_CACHE and _hermes_available is not None:
        return _hermes_available
    
    client = _get_hermes_client()
    if not client:
        _hermes_available = False
        _hermes_last_check = now
        return False
    
    try:
        import urllib.request
        base_url = os.getenv("HERMES_BASE_URL", "http://127.0.0.1:8642/v1")
        req = urllib.request.Request(f"{base_url}/models")
        urllib.request.urlopen(req, timeout=2)
        _hermes_available = True
    except Exception:
        logger.warning("Hermes Agent 不可用，将使用 fallback 模式")
        _hermes_available = False
    
    _hermes_last_check = now
    return _hermes_available


@tool(
    name="call_llm",
    description="调用 LLM 生成文本或结构化数据。用于生成学习计划、评估计划质量、生成追问问题等。",
    toolset="learning",
    emoji="🤖",
)
def call_llm(system_prompt: str, user_message: str, response_schema: Optional[Dict] = None,
             model: str = "", temperature: float = 0.7, stream: bool = False) -> str:
    if _is_hermes_enabled() and _is_hermes_available():
        client = _get_hermes_client()
        if client:
            try:
                return _call_hermes(client, system_prompt, user_message, response_schema,
                                    model, temperature, stream)
            except Exception as e:
                logger.error(f"Hermes 调用失败，fallback 到硅基流动: {e}")

    return _call_siliconflow(system_prompt, user_message, response_schema, model, temperature, stream)


def _call_hermes(client, system_prompt: str, user_message: str, response_schema: Optional[Dict] = None,
                 model: str = "", temperature: float = 0.7, stream: bool = False) -> str:
    """调用 Hermes Agent"""
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
    ]

    model_name = model or os.getenv("HERMES_MODEL", "hermes-agent")

    if stream:
        return json.dumps({
            "success": True,
            "content": "",
            "is_streaming": True,
            "model": model_name,
            "provider": "hermes",
        }, ensure_ascii=False)

    response = client.chat_completion(
        messages=messages,
        model=model_name,
        temperature=temperature,
        tools=_build_tools_from_schema(response_schema) if response_schema else None,
    )

    content = response.choices[0].message.content or ""
    usage = {
        "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
        "completion_tokens": response.usage.completion_tokens if response.usage else 0,
    }

    try:
        parsed_content = json.loads(content)
        return json.dumps({
            "success": True,
            "content": parsed_content,
            "is_json": True,
            "usage": usage,
            "model": model_name,
            "provider": "hermes",
        }, ensure_ascii=False)
    except json.JSONDecodeError:
        return json.dumps({
            "success": True,
            "content": content,
            "is_json": False,
            "usage": usage,
            "model": model_name,
            "provider": "hermes",
        }, ensure_ascii=False)


def _call_siliconflow(system_prompt: str, user_message: str, response_schema: Optional[Dict] = None,
                      model: str = "", temperature: float = 0.7, stream: bool = False) -> str:
    """调用硅基流动 LLM（fallback）"""
    api_key = os.getenv("LLM_API_KEY", "")
    base_url = os.getenv("LLM_BASE_URL", "https://api.siliconflow.cn/v1")
    model_name = model or os.getenv("LLM_MODEL", "deepseek-ai/DeepSeek-V4-Flash")

    if not api_key:
        logger.warning("LLM_API_KEY 未设置，返回 mock 数据")
        return json.dumps(_mock_response(user_message), ensure_ascii=False)

    if stream:
        return json.dumps({
            "success": True,
            "content": "",
            "is_streaming": True,
            "model": model_name,
            "provider": "siliconflow",
        }, ensure_ascii=False)

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
        payload_stream = payload.copy()
        payload_stream["stream"] = True
        req = urllib.request.Request(
            f"{base_url}/chat/completions",
            data=json.dumps(payload_stream).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
                "Accept": "text/event-stream",
            },
        )
        content_parts = []
        usage = {}
        with urllib.request.urlopen(req, timeout=300) as resp:
            for line in resp:
                line = line.decode("utf-8").strip()
                if line.startswith("data: "):
                    data = line[6:]
                    if data == "[DONE]":
                        break
                    try:
                        parsed = json.loads(data)
                        delta = parsed["choices"][0]["delta"].get("content", "")
                        if delta:
                            content_parts.append(delta)
                        if parsed.get("usage"):
                            usage = parsed["usage"]
                    except (json.JSONDecodeError, KeyError, IndexError):
                        continue

        content = "".join(content_parts)

        try:
            parsed_content = json.loads(content)
            return json.dumps({
                "success": True,
                "content": parsed_content,
                "is_json": True,
                "usage": usage,
                "model": model_name,
                "provider": "siliconflow",
            }, ensure_ascii=False)
        except json.JSONDecodeError:
            return json.dumps({
                "success": True,
                "content": content,
                "is_json": False,
                "usage": usage,
                "model": model_name,
                "provider": "siliconflow",
            }, ensure_ascii=False)

    except Exception as e:
        logger.error(f"LLM API 调用失败，fallback 到 mock 数据: {e}")
        mock = _mock_response(user_message)
        mock["fallback_reason"] = str(e)
        return json.dumps(mock, ensure_ascii=False)


def _build_tools_from_schema(schema: Optional[Dict]) -> Optional[List[Dict]]:
    """从 response_schema 构建 tools 列表"""
    if not schema:
        return None
    return [{
        "type": "function",
        "function": {
            "name": "generate_structured_response",
            "description": "生成结构化响应",
            "parameters": schema,
        },
    }]


def call_llm_stream(system_prompt: str, user_message: str, response_schema: Optional[Dict] = None,
                    model: str = "", temperature: float = 0.7) -> Generator[str, None, None]:
    if _is_hermes_enabled() and _is_hermes_available():
        client = _get_hermes_client()
        if client:
            try:
                yield from _call_hermes_stream(client, system_prompt, user_message, response_schema,
                                               model, temperature)
                return
            except Exception as e:
                logger.error(f"Hermes 流式调用失败，fallback 到硅基流动: {e}")

    yield from _call_siliconflow_stream(system_prompt, user_message, response_schema, model, temperature)


def _call_hermes_stream(client, system_prompt: str, user_message: str,
                        response_schema: Optional[Dict] = None, model: str = "",
                        temperature: float = 0.7) -> Generator[str, None, None]:
    """Hermes 流式调用"""
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
    ]

    model_name = model or os.getenv("HERMES_MODEL", "hermes-agent")

    try:
        stream = client.chat_completion(
            messages=messages,
            model=model_name,
            temperature=temperature,
            stream=True,
            tools=_build_tools_from_schema(response_schema) if response_schema else None,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta
            if delta.content:
                yield delta.content
    except Exception as e:
        logger.error(f"Hermes 流式调用失败: {e}", exc_info=True)
        yield json.dumps({
            "success": False,
            "error": str(e),
            "content": "",
            "model": model_name,
            "provider": "hermes",
        }, ensure_ascii=False)


def _call_siliconflow_stream(system_prompt: str, user_message: str,
                             response_schema: Optional[Dict] = None, model: str = "",
                             temperature: float = 0.7) -> Generator[str, None, None]:
    """硅基流动流式调用（fallback）"""
    api_key = os.getenv("LLM_API_KEY", "")
    base_url = os.getenv("LLM_BASE_URL", "https://api.siliconflow.cn/v1")
    model_name = model or os.getenv("LLM_MODEL", "deepseek-ai/DeepSeek-V4-Flash")

    if not api_key:
        yield json.dumps(_mock_response(user_message), ensure_ascii=False)
        return

    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        "temperature": temperature,
        "stream": True,
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
                "Accept": "text/event-stream",
            },
        )

        with urllib.request.urlopen(req, timeout=120) as resp:
            for line in resp:
                line = line.decode("utf-8").strip()
                if line.startswith("data: "):
                    data = line[6:]
                    if data == "[DONE]":
                        break
                    try:
                        parsed = json.loads(data)
                        delta = parsed["choices"][0]["delta"].get("content", "")
                        if delta:
                            yield delta
                    except json.JSONDecodeError:
                        continue

    except Exception as e:
        logger.error(f"LLM 流式调用失败，fallback 到 mock 数据: {e}")
        mock = _mock_response(user_message)
        mock["fallback_reason"] = str(e)
        yield json.dumps(mock, ensure_ascii=False)


def _mock_response(user_message: str) -> Dict[str, Any]:
    keywords = ["学习计划", "规划", "学习", "课程", "教程", "Python", "plan", "goal", "profile"]
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
                    {"id": "t1_1", "day": 1, "title": "安装Python环境 + Hello World", "est_hours": 1.0,
                     "description": "安装Python并编写第一个程序",
                     "resources": [
                         {"title": "Python官方教程-入门", "url": "https://docs.python.org/zh-cn/3/tutorial/", "type": "course"},
                         {"title": "廖雪峰Python教程", "url": "https://www.liaoxuefeng.com/wiki/1016959663602400", "type": "article"},
                         {"title": "黑马程序员Python入门视频", "url": "https://www.bilibili.com/video/BV1qW4y1a7fU?p=10", "type": "video"},
                     ],
                     "exercises": [
                        {"title": "基础语法练习题", "url": "/learn/kb/python_learning_path/01-基础语法", "description": "变量、数据类型、输入输出练习"},
                     ]},
                    {"id": "t1_2", "day": 1, "title": "认识变量与数据类型", "est_hours": 1.5,
                     "description": "学习整数、浮点数、字符串、布尔值",
                     "resources": [
                         {"title": "菜鸟教程-Python变量", "url": "https://www.runoob.com/python3/python3-basic-syntax.html", "type": "article"},
                         {"title": "数据类型详解", "url": "/learn/kb/python_learning_path/01-基础语法", "type": "article"},
                     ],
                     "exercises": [
                        {"title": "变量与数据类型练习", "url": "/learn/kb/exercises/01-变量练习", "description": "包含20道基础练习题"},
                     ]},
                    {"id": "t1_3", "day": 1, "title": "基本输入输出", "est_hours": 0.5,
                     "description": "print() 和 input() 的使用",
                     "resources": [
                         {"title": "Python输入输出教程", "url": "https://www.runoob.com/python3/python3-inputoutput.html", "type": "article"},
                         {"title": "廖雪峰-输入输出", "url": "https://www.liaoxuefeng.com/wiki/1016959663602400/1017063413908976", "type": "article"},
                         {"title": "黑马程序员-输入输出视频", "url": "https://www.bilibili.com/video/BV1qW4y1a7fU?p=17", "type": "video"},
                     ],
                     "exercises": [
                        {"title": "输入输出练习", "url": "/learn/kb/exercises/01-变量练习", "description": "print和input函数练习"},
                        {"title": "菜鸟在线练习", "url": "https://www.runoob.com/python3/python3-tutorial.html", "description": "在线交互式练习"},
                     ]},
                    {"id": "t2_1", "day": 2, "title": "条件判断（if/elif/else）", "est_hours": 1.0,
                     "description": "学习条件判断语句",
                     "resources": [
                         {"title": "廖雪峰-条件判断", "url": "https://www.liaoxuefeng.com/wiki/1016959663602400/1017063413908976", "type": "article"},
                         {"title": "流程控制详解", "url": "/learn/kb/python_learning_path/02-流程控制", "type": "article"},
                     ],
                     "exercises": [
                        {"title": "条件判断练习", "url": "/learn/kb/exercises/02-流程控制练习", "description": "if-else 条件判断练习"},
                     ]},
                    {"id": "t2_2", "day": 2, "title": "for 循环", "est_hours": 1.0,
                     "description": "学习 for 循环和 range()",
                     "resources": [
                         {"title": "菜鸟教程-for循环", "url": "https://www.runoob.com/python3/python3-loop.html", "type": "article"},
                         {"title": "廖雪峰-for循环", "url": "https://www.liaoxuefeng.com/wiki/1016959663602400/1017070470158080", "type": "article"},
                         {"title": "尚硅谷-循环视频", "url": "https://www.bilibili.com/video/BV1wD4y1o7AS?p=25", "type": "video"},
                     ],
                     "exercises": [
                        {"title": "循环练习", "url": "/learn/kb/exercises/02-流程控制练习", "description": "for和while循环练习"},
                        {"title": "循环专题练习", "url": "https://www.runoob.com/python3/python3-examples.html", "description": "菜鸟教程实例练习"},
                     ]},
                    {"id": "t2_3", "day": 2, "title": "while 循环", "est_hours": 0.5,
                     "description": "学习 while 循环",
                     "resources": [
                         {"title": "Python while循环", "url": "https://www.liaoxuefeng.com/wiki/1016959663602400/1017063826246112", "type": "article"},
                         {"title": "菜鸟教程-while循环", "url": "https://www.runoob.com/python3/python3-while-loop.html", "type": "article"},
                         {"title": "黑马程序员-while循环视频", "url": "https://www.bilibili.com/video/BV1qW4y1a7fU?p=25", "type": "video"},
                     ],
                     "exercises": [
                        {"title": "while循环练习", "url": "/learn/kb/exercises/02-流程控制练习", "description": "while循环专项练习"},
                     ]},
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