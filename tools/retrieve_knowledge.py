# -*- coding: utf-8 -*-
"""
Retrieve Knowledge Tool — 知识库检索工具

功能：从 Dify 知识库检索相关学习资料
依赖：dify_client 模块，Dify_KB_ID.txt
"""

import json
import logging

from src.agent.tool_registry import tool
from src.dify_client import DifyClient

logger = logging.getLogger(__name__)


@tool(
    name="retrieve_knowledge",
    description="从知识库检索与学习目标相关的资料。用于为学习计划生成提供内容支撑。",
    toolset="learning",
    emoji="📚",
)
def retrieve_knowledge(query: str, top_k: int = 5) -> str:
    client = DifyClient()
    results = client.retrieve(query, top_k=top_k)

    if not results:
        return json.dumps({
            "success": True,
            "results": [],
            "message": "知识库未检索到相关内容",
        }, ensure_ascii=False)

    formatted_results = []
    for r in results:
        formatted_results.append({
            "title": r.title,
            "content": r.content,
            "score": r.score,
            "metadata": r.metadata,
        })

    return json.dumps({
        "success": True,
        "results": formatted_results,
        "count": len(formatted_results),
    }, ensure_ascii=False)