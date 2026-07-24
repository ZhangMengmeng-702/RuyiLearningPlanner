# -*- coding: utf-8 -*-
"""
Generate Schedule Tool — 日程生成工具

功能：将学习计划导出为 ICS 日历文件
依赖：学习计划 JSON 数据
"""

import json
import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict

from src.agent.tool_registry import tool

logger = logging.getLogger(__name__)


@tool(
    name="generate_schedule",
    description="将学习计划导出为 ICS 日历文件。",
    toolset="learning",
    emoji="📅",
)
def generate_schedule(plan_json: str, output_path: str = "", start_date: str = "") -> str:
    try:
        plan_data = json.loads(plan_json)
    except json.JSONDecodeError:
        return json.dumps({
            "success": False,
            "error": "plan_json 不是有效的 JSON",
        }, ensure_ascii=False)

    if not start_date:
        start_date = datetime.now().strftime("%Y-%m-%d")

    if not output_path:
        output_path = f"plan_{plan_data.get('plan_id', 'default')}.ics"

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    start_dt = datetime.strptime(start_date, "%Y-%m-%d")

    ics_content = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//RuyiLearningPlanner//Learning Plan//ZH",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
    ]

    uid_counter = 1

    milestones = plan_data.get("milestones", [])
    for idx, milestone in enumerate(milestones, 1):
        week_start = milestone.get("week_start", idx)
        event_date = start_dt + timedelta(weeks=week_start - 1)

        title = f"阶段{idx}: {milestone.get('phase', '')}"
        description = milestone.get("description", "")
        objectives = milestone.get("objectives", [])
        if objectives:
            description += "\n目标：" + ", ".join(objectives)

        ics_content.extend([
            "BEGIN:VEVENT",
            f"UID:{uid_counter}@{output_path}",
            f"DTSTART;VALUE=DATE:{event_date.strftime('%Y%m%d')}",
            f"DTEND;VALUE=DATE:{(event_date + timedelta(days=1)).strftime('%Y%m%d')}",
            f"SUMMARY:{title}",
            f"DESCRIPTION:{description}",
            "STATUS:CONFIRMED",
            "TRANSP:OPAQUE",
            "BEGIN:VALARM",
            "TRIGGER:-P1D",
            "ACTION:DISPLAY",
            f"DESCRIPTION:学习里程碑提醒: {title}",
            "END:VALARM",
            "END:VEVENT",
        ])
        uid_counter += 1

    daily_tasks = plan_data.get("daily_tasks", [])
    for task in daily_tasks:
        day_num = task.get("day", 1)
        event_date = start_dt + timedelta(days=day_num - 1)

        title = task.get("title", "")
        est_hours = task.get("est_hours", 1)

        ics_content.extend([
            "BEGIN:VEVENT",
            f"UID:{uid_counter}@{output_path}",
            f"DTSTART;VALUE=DATE:{event_date.strftime('%Y%m%d')}",
            f"DTEND;VALUE=DATE:{(event_date + timedelta(days=1)).strftime('%Y%m%d')}",
            f"SUMMARY:学习任务: {title}",
            f"DESCRIPTION:预计时长: {est_hours}小时",
            "STATUS:CONFIRMED",
            "TRANSP:OPAQUE",
            "END:VEVENT",
        ])
        uid_counter += 1

    ics_content.append("END:VCALENDAR")

    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(ics_content))

        return json.dumps({
            "success": True,
            "output_path": output_path,
            "event_count": uid_counter - 1,
        }, ensure_ascii=False)

    except Exception as e:
        logger.error(f"生成日历文件失败: {e}", exc_info=True)
        return json.dumps({
            "success": False,
            "error": str(e),
        }, ensure_ascii=False)