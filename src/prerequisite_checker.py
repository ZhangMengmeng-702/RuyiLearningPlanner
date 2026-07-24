# -*- coding: utf-8 -*-
"""前置依赖检查器 — 从知识库文档元数据中提取依赖关系，校验计划是否覆盖"""
import json
import logging
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)

PREREQUISITE_RULES = {
    "Python基础语法": [],
    "变量与数据类型": ["Python基础语法"],
    "运算符与表达式": ["变量与数据类型"],
    "条件判断": ["运算符与表达式"],
    "循环结构": ["条件判断"],
    "函数": ["循环结构"],
    "列表与元组": ["函数"],
    "字典与集合": ["列表与元组"],
    "文件操作": ["函数"],
    "异常处理": ["函数"],
    "模块与包": ["函数"],
    "面向对象入门": ["模块与包", "函数"],
    "面向对象进阶": ["面向对象入门"],
    "NumPy入门": ["Python基础语法", "列表与元组"],
    "Pandas入门": ["NumPy入门", "文件操作"],
    "Matplotlib入门": ["NumPy入门", "Pandas入门"],
    "数据清洗": ["Pandas入门"],
    "数据分析": ["数据清洗"],
    "数据可视化": ["Matplotlib入门", "数据分析"],
}


class PrerequisiteChecker:
    def __init__(self, rules: Dict[str, List[str]] = None):
        self.rules = rules or PREREQUISITE_RULES

    def check_plan(self, plan_data: Dict) -> Dict:
        details = []
        warnings = []
        covered_topics = set()

        if "milestones" in plan_data:
            for milestone in plan_data["milestones"]:
                phase = milestone.get("phase", "")
                description = milestone.get("description", "")

                covered_topics.add(phase)

                prerequisites = self.rules.get(phase, [])
                if prerequisites:
                    missing = [p for p in prerequisites if p not in covered_topics]
                    if missing:
                        status = "missing"
                        warnings.append(f"阶段 '{phase}' 的前置知识 {missing} 未在计划中覆盖")
                    else:
                        status = "covered"
                    details.append({
                        "chapter": phase,
                        "prerequisites": prerequisites,
                        "status": status,
                    })
                else:
                    details.append({
                        "chapter": phase,
                        "prerequisites": [],
                        "status": "covered",
                    })

        if "daily_tasks" in plan_data:
            for task in plan_data["daily_tasks"]:
                title = task.get("title", "")
                for topic, prereqs in self.rules.items():
                    if topic in title:
                        covered_topics.add(topic)
                        missing = [p for p in prereqs if p not in covered_topics]
                        if missing and topic not in [d["chapter"] for d in details]:
                            warnings.append(f"任务 '{title}' 的前置知识 {missing} 未覆盖")

        if warnings:
            status = "warning"
        elif not details:
            status = "passed"
        else:
            status = "passed"

        return {
            "status": status,
            "details": details,
            "warnings": warnings,
            "covered_topics": list(covered_topics),
        }

    def validate_sequence(self, phases: List[str]) -> List[Tuple[str, str, List[str]]]:
        issues = []
        covered = set()
        for i, phase in enumerate(phases):
            prerequisites = self.rules.get(phase, [])
            missing = [p for p in prerequisites if p not in covered]
            if missing:
                issues.append((phase, "missing_prerequisite", missing))
            covered.add(phase)
        return issues

    def suggest_prerequisites(self, target_topic: str) -> List[str]:
        result = []
        queue = [target_topic]
        visited = set()

        while queue:
            topic = queue.pop(0)
            if topic in visited:
                continue
            visited.add(topic)

            prereqs = self.rules.get(topic, [])
            for prereq in prereqs:
                if prereq not in visited and prereq not in result:
                    result.append(prereq)
                    queue.append(prereq)

        return list(reversed(result))
