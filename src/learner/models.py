# -*- coding: utf-8 -*-
"""学习规划数据模型"""
from dataclasses import dataclass, field, asdict
from typing import Optional

@dataclass
class DailyTask:
    day: int
    title: str
    description: str = ""
    est_hours: float = 1.0
    resource_title: str = ""
    resource_url: str = ""
    completed: bool = False

@dataclass
class Milestone:
    week_start: int
    week_end: int
    phase: str
    description: str = ""
    objectives: list[str] = field(default_factory=list)
    task_count: int = 0
    difficulty: int = 2  # 1=easy, 2=medium, 3=hard

@dataclass
class PrerequisiteCheck:
    status: str = "passed"  # passed / warning / failed
    details: list[dict] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

@dataclass
class PlanEvaluation:
    score: int = 0        # 1-10
    issues: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)

@dataclass
class StudyPlan:
    plan_id: str = ""
    goal: str = ""
    user_id: str = ""
    total_weeks: int = 0
    created_at: str = ""
    milestones: list[Milestone] = field(default_factory=list)
    daily_tasks: list[DailyTask] = field(default_factory=list)
    prerequisite_check: PrerequisiteCheck = field(default_factory=PrerequisiteCheck)
    evaluation: Optional[PlanEvaluation] = None

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(data: dict) -> "StudyPlan":
        # 简化的反序列化，实际项目可用 marshmallow/pydantic
        plan = StudyPlan(
            plan_id=data.get("plan_id", ""),
            goal=data.get("goal", ""),
            user_id=data.get("user_id", ""),
            total_weeks=data.get("total_weeks", 0),
            created_at=data.get("created_at", ""),
        )
        for m in data.get("milestones", []):
            plan.milestones.append(Milestone(**m))
        for t in data.get("daily_tasks", []):
            plan.daily_tasks.append(DailyTask(**t))
        pc = data.get("prerequisite_check", {})
        plan.prerequisite_check = PrerequisiteCheck(**pc)
        ev = data.get("evaluation")
        if ev:
            plan.evaluation = PlanEvaluation(**ev)
        return plan