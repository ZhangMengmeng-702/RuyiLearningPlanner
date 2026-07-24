# -*- coding: utf-8 -*-
"""
Retrieve Knowledge Tool — 从 Dify 知识库检索学习内容

功能：调用 Dify KB API 检索与用户目标相关的学习内容
依赖：src/dify_client.py 中的 DifyClient
"""

import json
import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

try:
    from src.dify_client import DifyClient
    _dify_client = None

    def _get_dify_client() -> DifyClient:
        global _dify_client
        if _dify_client is None:
            _dify_client = DifyClient()
        return _dify_client
except ImportError:
    logger.warning("DifyClient 导入失败，将使用 mock 模式")

    class MockDifyClient:
        def retrieve(self, query: str, top_k: int = 5, score_threshold: float = 0.5) -> List[Dict[str, Any]]:
            return [
                {"title": "Python 基础语法", "content": "变量、数据类型、条件判断、循环结构", "score": 0.92, "metadata": {}},
                {"title": "函数与模块", "content": "函数定义、参数传递、模块导入", "score": 0.85, "metadata": {}},
                {"title": "NumPy 入门", "content": "数组创建、索引、基本运算", "score": 0.78, "metadata": {}},
            ]

        def retrieve_formatted(self, query: str, top_k: int = 5) -> str:
            results = self.retrieve(query, top_k=top_k)
            lines = []
            for i, r in enumerate(results, 1):
                lines.append(f"[{i}] {r.get('title','')} (score:{r.get('score',0):.2f})\n{r.get('content','')}")
            return "\n\n".join(lines)

    def _get_dify_client() -> MockDifyClient:
        return MockDifyClient()


def check_retrieve_knowledge_requirements() -> bool:
    return True


RETRIEVE_KNOWLEDGE_SCHEMA = {
    "name": "retrieve_knowledge",
    "description": "从 Dify 知识库检索学习内容。用于获取与用户学习目标相关的课程章节、前置知识、练习题等。",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "检索关键词（如：Python数据分析 学习路径）"},
            "top_k": {"type": "integer", "description": "返回结果数量（默认5）", "default": 5, "minimum": 1, "maximum": 20},
            "kb_id": {"type": "string", "description": "知识库ID（可选，不填则使用默认知识库）"},
        },
        "required": ["query"]
    }
}


def _handle_retrieve_knowledge(args: Dict[str, Any]) -> str:
    query = args.get("query", "")
    top_k = args.get("top_k", 5)
    kb_id = args.get("kb_id", "")

    if not query:
        return json.dumps({"success": False, "error": "query 参数不能为空"}, ensure_ascii=False)

    try:
        client = _get_dify_client()
        if kb_id:
            client.kb_id = kb_id
        results = client.retrieve(query, top_k=top_k)

        formatted_results = []
        for i, r in enumerate(results, 1):
            formatted_results.append({
                "rank": i,
                "title": r.get("title", ""),
                "content": r.get("content", ""),
                "score": r.get("score", 0.0),
                "metadata": r.get("metadata", {}),
            })

        return json.dumps({
            "success": True,
            "query": query,
            "count": len(formatted_results),
            "results": formatted_results,
        }, ensure_ascii=False, indent=2)

    except Exception as e:
        logger.error(f"retrieve_knowledge 调用失败: {e}", exc_info=True)
        return json.dumps({
            "success": False,
            "error": str(e),
            "query": query,
        }, ensure_ascii=False)


try:
    from src.agent.tool_registry import registry
    registry.register(
        name="retrieve_knowledge",
        toolset="learning",
        schema=RETRIEVE_KNOWLEDGE_SCHEMA,
        handler=_handle_retrieve_knowledge,
        check_fn=check_retrieve_knowledge_requirements,
        emoji="📚",
    )
except ImportError:
    pass
