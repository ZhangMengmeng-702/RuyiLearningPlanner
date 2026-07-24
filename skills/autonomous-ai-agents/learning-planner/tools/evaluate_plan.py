# -*- coding: utf-8 -*-
"""
Evaluate Plan Tool — 计划质量评估工具

功能：评估学习计划的合理性、完整性、难度适配度、前置知识覆盖度
依赖：调用 call_llm 工具进行智能评估
"""

import json
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

try:
    from tools.call_llm import _call_llm_api
except ImportError:
    logger.warning("call_llm 导入失败，将使用本地规则评估")


def check_evaluate_plan_requirements() -> bool:
    return True


EVALUATE_PLAN_SCHEMA = {
    "name": "evaluate_plan",
    "description": "评估学习计划的合理性、完整性、难度适配度、前置知识覆盖度。返回评分和改进建议。",
    "parameters": {
        "type": "object",
        "properties": {
            "plan_json": {"type": "string", "description": "学习计划 JSON 字符串"},
            "user_profile": {"type": "string", "description": "用户画像 JSON 字符串（可选）"},
        },
        "required": ["plan_json"]
    }
}


def _evaluate_plan_rules(plan_data: Dict[str, Any], user_profile: Optional[Dict] = None) -> Dict[str, Any]:
    score = 0
    issues = []
    suggestions = []

    if "milestones" in plan_data:
        milestones = plan_data["milestones"]
        if len(milestones) >= 3:
            score += 2
        else:
            score += 1
            issues.append("里程碑数量不足，建议至少设置3个阶段")
            suggestions.append("增加更多阶段以细化学习路径")

        for m in milestones:
            if "phase" in m and "description" in m:
                score += 0.5
            else:
                issues.append(f"里程碑缺少必要字段: {m}")

    if "daily_tasks" in plan_data:
        tasks = plan_data["daily_tasks"]
        if len(tasks) >= 5:
            score += 2
        else:
            score += 1
            issues.append("每日任务数量较少")

        total_hours = sum(t.get("est_hours", 0) for t in tasks)
        if total_hours > 0 and total_hours <= 8:
            score += 1
        elif total_hours > 8:
            issues.append("每日预估学习时长超过8小时，可能过于紧张")
            suggestions.append("适当减少每日学习量，保证学习效果")

    if "prerequisite_check" in plan_data:
        prereq = plan_data["prerequisite_check"]
        if prereq.get("status") == "passed":
            score += 1
        elif prereq.get("warnings"):
            score += 0.5
            issues.extend(prereq.get("warnings", []))

    if "goal" in plan_data:
        score += 1
        if len(plan_data["goal"]) > 5:
            score += 1
        else:
            issues.append("学习目标描述过于简略")

    score = min(10, score)

    if score >= 8:
        status = "excellent"
        status_text = "优秀"
    elif score >= 6:
        status = "good"
        status_text = "良好"
    elif score >= 4:
        status = "average"
        status_text = "一般"
    else:
        status = "poor"
        status_text = "较差"

    return {
        "success": True,
        "score": round(score, 1),
        "status": status,
        "status_text": status_text,
        "issues": issues,
        "suggestions": suggestions,
        "method": "rule_based",
    }


def _evaluate_plan_llm(plan_data: Dict[str, Any], user_profile: Optional[Dict] = None) -> Dict[str, Any]:
    try:
        system_prompt = """你是一个学习计划评估专家。请根据以下标准评估学习计划：
1. 合理性：学习路径是否符合循序渐进的原则
2. 完整性：是否覆盖了必要的知识点和技能
3. 难度适配度：是否适合用户当前水平
4. 前置知识覆盖度：是否考虑了用户的已知知识
5. 可执行性：时间安排是否合理

返回格式：
{
    "score": 0-10的评分,
    "status": "excellent/good/average/poor",
    "status_text": "优秀/良好/一般/较差",
    "issues": ["问题1", "问题2"],
    "suggestions": ["建议1", "建议2"],
    "aspects": {
        "reasonableness": {"score": 0-10, "comment": "评价"},
        "completeness": {"score": 0-10, "comment": "评价"},
        "difficulty_fit": {"score": 0-10, "comment": "评价"},
        "prerequisite_coverage": {"score": 0-10, "comment": "评价"},
        "executability": {"score": 0-10, "comment": "评价"}
    }
}
"""
        user_message = f"""请评估以下学习计划：
计划数据：
{json.dumps(plan_data, ensure_ascii=False, indent=2)}

用户画像：
{json.dumps(user_profile or {}, ensure_ascii=False, indent=2)}
"""
        result = _call_llm_api(system_prompt, user_message, temperature=0.3)
        if result.get("success"):
            content = result.get("content", {})
            if isinstance(content, str):
                try:
                    content = json.loads(content)
                except json.JSONDecodeError:
                    return _evaluate_plan_rules(plan_data, user_profile)
            if isinstance(content, dict) and "score" in content:
                content["method"] = "llm_based"
                return content
    except Exception as e:
        logger.warning(f"LLM 评估失败，回退到规则评估: {e}")

    return _evaluate_plan_rules(plan_data, user_profile)


def _handle_evaluate_plan(args: Dict[str, Any]) -> str:
    plan_json = args.get("plan_json", "")
    user_profile_json = args.get("user_profile", "")

    if not plan_json:
        return json.dumps({"success": False, "error": "plan_json 参数不能为空"}, ensure_ascii=False)

    try:
        plan_data = json.loads(plan_json)
    except json.JSONDecodeError:
        return json.dumps({"success": False, "error": "plan_json 不是有效的 JSON"}, ensure_ascii=False)

    user_profile = None
    if user_profile_json:
        try:
            user_profile = json.loads(user_profile_json)
        except json.JSONDecodeError:
            logger.warning("user_profile_json 不是有效的 JSON，忽略")

    result = _evaluate_plan_llm(plan_data, user_profile)
    return json.dumps(result, ensure_ascii=False, indent=2)


try:
    from src.agent.tool_registry import registry
    registry.register(
        name="evaluate_plan",
        toolset="learning",
        schema=EVALUATE_PLAN_SCHEMA,
        handler=_handle_evaluate_plan,
        check_fn=check_evaluate_plan_requirements,
        emoji="📊",
    )
except ImportError:
    pass
