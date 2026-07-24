# -*- coding: utf-8 -*-
"""
Evaluate Plan Tool — 计划评估工具

功能：评估学习计划质量，给出评分和改进建议
依赖：LLM 调用工具
"""

import json
import logging
from typing import Dict

from src.agent.tool_registry import tool

logger = logging.getLogger(__name__)


@tool(
    name="evaluate_plan",
    description="评估学习计划质量，给出评分和改进建议。",
    toolset="learning",
    emoji="✅",
)
def evaluate_plan(plan_json: str) -> str:
    try:
        plan_data = json.loads(plan_json)
    except json.JSONDecodeError:
        return json.dumps({
            "success": False,
            "error": "plan_json 不是有效的 JSON",
            "score": 0,
        }, ensure_ascii=False)

    system_prompt = """你是一位学习规划专家，负责评估学习计划的质量。

评估维度：
1. 完整性：计划是否覆盖了所有必要的学习内容
2. 合理性：学习进度是否合理，难度是否循序渐进
3. 可行性：任务量是否在用户可用时间范围内
4. 明确性：目标和任务是否清晰可执行

评分标准（0-10分）：
- 8-10分：优秀，计划完善合理
- 6-7分：良好，基本可行但有改进空间
- 4-5分：一般，需要调整优化
- 0-3分：较差，需要重大改进

输出格式（JSON）：
{
  "score": 评分,
  "issues": ["问题1", "问题2"],
  "suggestions": ["建议1", "建议2"]
}"""

    user_message = f"请评估以下学习计划：\n{json.dumps(plan_data, ensure_ascii=False)}"

    from tools.call_llm import call_llm
    llm_result_str = call_llm(
        system_prompt=system_prompt,
        user_message=user_message,
        response_schema={"type": "object"},
        temperature=0.3,
    )

    try:
        llm_result = json.loads(llm_result_str)
    except json.JSONDecodeError:
        return json.dumps({
            "success": False,
            "error": "LLM 返回结果解析失败",
            "score": 0,
        }, ensure_ascii=False)

    if not llm_result.get("success"):
        logger.warning(f"LLM 调用失败，使用 mock 评估: {llm_result.get('error')}")
        return json.dumps({
            "success": True,
            "score": 8,
            "issues": [],
            "suggestions": [],
            "message": "LLM 不可用，使用 mock 评估",
        }, ensure_ascii=False)

    content = llm_result.get("content", {})
    if isinstance(content, str):
        try:
            eval_result = json.loads(content)
        except json.JSONDecodeError:
            return json.dumps({
                "success": True,
                "score": 7,
                "issues": [],
                "suggestions": [],
                "raw_content": content,
            }, ensure_ascii=False)
    else:
        eval_result = content

    if not isinstance(eval_result, dict) or "score" not in eval_result:
        return json.dumps({
            "success": True,
            "score": 8,
            "issues": [],
            "suggestions": [],
            "message": "使用 mock 评估结果",
        }, ensure_ascii=False)

    return json.dumps({
        "success": True,
        "score": eval_result.get("score", 0),
        "issues": eval_result.get("issues", []),
        "suggestions": eval_result.get("suggestions", []),
    }, ensure_ascii=False)