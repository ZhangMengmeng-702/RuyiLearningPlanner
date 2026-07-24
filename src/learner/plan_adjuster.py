# -*- coding: utf-8 -*-
"""
学习计划自适应调整器
根据每日打卡数据自动调整后续计划：
1. 任务顺延 - 未完成的任务往后推
2. 任务量调整 - 根据完成率增减任务量
3. 难度自适应 - 根据难度反馈调整后续难度
"""
import json
import os
import time
from typing import Dict, List, Any, Tuple
from datetime import datetime

PLANS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "plans")


class PlanAdjuster:
    """计划自适应调整器"""

    def __init__(self, plan_data: Dict[str, Any]):
        self.plan = plan_data
        self.daily_tasks = plan_data.get("daily_tasks", [])

    def auto_adjust(self, checkin_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        根据打卡数据自动调整计划
        返回调整后的计划数据
        """
        day = checkin_data.get("day", 1)
        tasks_completed = checkin_data.get("tasks_completed", [])
        difficulty_rating = checkin_data.get("difficulty_rating", 2)  # 1-5
        completion_pct = checkin_data.get("completion_pct", 100)
        time_spent_hours = checkin_data.get("time_spent_hours", 0)
        feedback_text = checkin_data.get("feedback_text", "")

        adjustment_reasons = []

        # 1. 任务顺延：找出当天未完成的任务，往后推
        unfinished_tasks = self._get_unfinished_tasks(day, tasks_completed)
        if unfinished_tasks:
            adjustment_reasons.append(f"今日有 {len(unfinished_tasks)} 个任务未完成，已顺延至后续天数")
            self._carry_over_tasks(day, unfinished_tasks)

        # 2. 获取最近几天的打卡数据（用于趋势判断）
        recent_checkins = self._get_recent_checkins(checkin_data.get("user_id", ""),
                                                     checkin_data.get("plan_id", ""),
                                                     day, days=3)

        # 3. 任务量调整：根据完成率趋势调整后续任务量
        workload_adjustment = self._calculate_workload_adjustment(recent_checkins, completion_pct)
        if workload_adjustment != 0:
            direction = "增加" if workload_adjustment > 0 else "减少"
            adjustment_reasons.append(f"近期完成率{'较高' if workload_adjustment > 0 else '较低'}，已{direction}后续任务量")
            self._adjust_workload(day, workload_adjustment)

        # 4. 难度自适应：根据难度反馈调整后续难度
        difficulty_adjustment = self._calculate_difficulty_adjustment(recent_checkins, difficulty_rating)
        if difficulty_adjustment != 0:
            direction = "提高" if difficulty_adjustment > 0 else "降低"
            adjustment_reasons.append(f"近期难度反馈{'偏易' if difficulty_adjustment > 0 else '偏难'}，已{direction}后续难度")
            self._adjust_difficulty(day, difficulty_adjustment)

        # 更新计划元数据
        self.plan["adjusted"] = True
        self.plan["adjust_reason"] = "；".join(adjustment_reasons) if adjustment_reasons else "自适应微调"
        self.plan["adjusted_at"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        self.plan["auto_adjusted"] = True
        self.plan["daily_tasks"] = self.daily_tasks

        return self.plan

    def _get_unfinished_tasks(self, day: int, tasks_completed: List[str]) -> List[Dict[str, Any]]:
        """获取当天未完成的任务"""
        today_tasks = [t for t in self.daily_tasks if t.get("day") == day]
        completed_set = set(tasks_completed)
        return [t for t in today_tasks if t.get("id") not in completed_set]

    def _carry_over_tasks(self, from_day: int, tasks: List[Dict[str, Any]]):
        """
        将未完成的任务顺延到后续天数
        策略：均匀分配到后续 3 天，避免某一天任务过多
        """
        if not tasks:
            return

        # 找出后续的天
        future_days = sorted(set(t.get("day") for t in self.daily_tasks if t.get("day", 0) > from_day))
        if not future_days:
            # 如果没有后续天了，添加新的天
            new_day = from_day + 1
            for i, task in enumerate(tasks):
                new_task = task.copy()
                new_task["day"] = new_day
                new_task["carried_over"] = True
                new_task["original_day"] = from_day
                self.daily_tasks.append(new_task)
            return

        # 分配到后续 3 天（或所有后续天，如果不足 3 天）
        distribute_days = future_days[:min(3, len(future_days))]
        tasks_per_day = (len(tasks) + len(distribute_days) - 1) // len(distribute_days)

        for i, task in enumerate(tasks):
            target_day_idx = min(i // tasks_per_day, len(distribute_days) - 1)
            target_day = distribute_days[target_day_idx]
            new_task = task.copy()
            new_task["day"] = target_day
            new_task["carried_over"] = True
            new_task["original_day"] = from_day
            new_task["completed"] = False
            self.daily_tasks.append(new_task)

        # 重新排序
        self.daily_tasks.sort(key=lambda t: (t.get("day", 0), t.get("id", "")))

    def _get_recent_checkins(self, user_id: str, plan_id: str, current_day: int, days: int = 3) -> List[Dict[str, Any]]:
        """获取最近几天的打卡记录（用于趋势判断）"""
        import os
        import sqlite3
        import json

        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "progress.db")
        if not os.path.exists(db_path):
            return []

        try:
            conn = sqlite3.connect(db_path)
            rows = conn.execute(
                "SELECT day, difficulty_rating, completion_pct, time_spent_hours, tasks_completed "
                "FROM checkins WHERE user_id=? AND plan_id=? AND day < ? ORDER BY day DESC LIMIT ?",
                (user_id, plan_id, current_day, days)
            ).fetchall()
            conn.close()

            result = []
            for row in rows:
                result.append({
                    "day": row[0],
                    "difficulty_rating": row[1],
                    "completion_pct": row[2],
                    "time_spent_hours": row[3],
                    "tasks_completed": json.loads(row[4]) if row[4] else [],
                })
            return result
        except Exception:
            return []

    def _calculate_workload_adjustment(self, recent_checkins: List[Dict], current_completion: int) -> int:
        """
        计算任务量调整幅度
        返回：-1 减少，0 不变，1 增加
        """
        # 收集所有完成率（包括当前）
        all_completions = [current_completion] + [c.get("completion_pct", 100) for c in recent_checkins]
        
        if not all_completions:
            return 0
        
        avg_completion = sum(all_completions) / len(all_completions)
        
        # 连续几天完成率都很高，增加任务量
        if avg_completion >= 90 and len(all_completions) >= 2:
            return 1
        elif current_completion >= 95 and len(all_completions) == 1:
            # 只有一天但完成率极高，也适当增加
            return 1
        
        # 连续几天完成率都很低，减少任务量
        if avg_completion < 50 and len(all_completions) >= 2:
            return -1
        elif current_completion < 40:
            # 当天完成率很低，立即减少
            return -1
        
        return 0

    def _adjust_workload(self, from_day: int, adjustment: int):
        """
        调整后续任务量
        adjustment: -1 减少（每天减少 1 个任务），1 增加（每天增加 1 个任务）
        """
        future_tasks = [t for t in self.daily_tasks if t.get("day", 0) > from_day]
        if not future_tasks:
            return

        future_days = sorted(set(t.get("day") for t in future_tasks))
        if not future_days:
            return

        if adjustment > 0:
            # 增加任务量：把后面的任务往前挪一些
            # 简单策略：从第 7 天后的任务每天往前挪 1 个
            for day in future_days[:7]:
                day_tasks = [t for t in future_tasks if t.get("day") == day]
                if len(day_tasks) > 1:
                    # 把最后一个任务往前挪一天
                    last_task = day_tasks[-1]
                    prev_day = day - 1
                    if prev_day > from_day:
                        last_task["day"] = prev_day

        elif adjustment < 0:
            # 减少任务量：把一些任务往后推
            # 简单策略：从第 2 天开始，每天最后 1 个任务往后推一天
            for day in reversed(future_days[:7]):
                day_tasks = [t for t in future_tasks if t.get("day") == day]
                if len(day_tasks) > 1:
                    last_task = day_tasks[-1]
                    next_day = day + 1
                    last_task["day"] = next_day

        # 重新排序
        self.daily_tasks.sort(key=lambda t: (t.get("day", 0), t.get("id", "")))

    def _calculate_difficulty_adjustment(self, recent_checkins: List[Dict], current_difficulty: int) -> int:
        """
        计算难度调整幅度
        返回：-1 降低难度，0 不变，1 提高难度
        难度评分：1-5 分，3 分为适中
        """
        # 收集所有难度反馈（包括当前）
        all_difficulties = [current_difficulty] + [c.get("difficulty_rating", 3) for c in recent_checkins if c.get("difficulty_rating", 0) > 0]
        
        if not all_difficulties:
            return 0
        
        avg_difficulty = sum(all_difficulties) / len(all_difficulties)
        
        # 连续几天都觉得太简单，提高难度
        if avg_difficulty <= 1.5 and len(all_difficulties) >= 2:
            return 1
        elif current_difficulty <= 1 and len(all_difficulties) == 1:
            return 1
        
        # 连续几天都觉得太难，降低难度
        if avg_difficulty >= 3.5 and len(all_difficulties) >= 2:
            return -1
        elif current_difficulty >= 4:
            return -1
        
        return 0

    def _adjust_difficulty(self, from_day: int, adjustment: int):
        """
        调整后续任务难度
        通过调整任务描述和标记难度级别实现
        """
        future_tasks = [t for t in self.daily_tasks if t.get("day", 0) > from_day]
        if not future_tasks:
            return

        for task in future_tasks:
            current_diff = task.get("difficulty", 2)
            if adjustment > 0:
                task["difficulty"] = min(current_diff + 1, 3)
                if "难度调整" not in task.get("description", ""):
                    task["description"] = (task.get("description", "") +
                                           f"\n\n[系统自动调整] 提高难度：增加拓展练习")
            elif adjustment < 0:
                task["difficulty"] = max(current_diff - 1, 1)
                if "难度调整" not in task.get("description", ""):
                    task["description"] = (task.get("description", "") +
                                           f"\n\n[系统自动调整] 降低难度：重点掌握基础概念")

    def save_plan(self) -> str:
        """保存调整后的计划"""
        plan_id = self.plan.get("plan_id", "")
        if not plan_id:
            return ""

        plan_path = os.path.join(PLANS_DIR, f"{plan_id}.json")
        os.makedirs(os.path.dirname(plan_path), exist_ok=True)
        with open(plan_path, "w", encoding="utf-8") as f:
            json.dump(self.plan, f, ensure_ascii=False, indent=2)

        return plan_id


def load_plan(plan_id: str) -> Dict[str, Any]:
    """加载计划数据"""
    plan_path = os.path.join(PLANS_DIR, f"{plan_id}.json")
    if not os.path.exists(plan_path):
        return {}
    with open(plan_path, encoding="utf-8") as f:
        return json.load(f)


def auto_adjust_plan_after_checkin(plan_id: str, checkin_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    打卡后自动调整计划的便捷函数
    返回调整后的计划数据
    """
    plan_data = load_plan(plan_id)
    if not plan_data:
        return {}

    adjuster = PlanAdjuster(plan_data)
    adjusted_plan = adjuster.auto_adjust(checkin_data)
    adjuster.save_plan()

    return adjusted_plan
