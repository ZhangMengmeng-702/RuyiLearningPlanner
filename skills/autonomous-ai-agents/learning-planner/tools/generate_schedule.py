# -*- coding: utf-8 -*-
"""
Generate Schedule Tool — 日程导出工具

功能：将学习计划导出为 ICS 格式（日历文件），支持导入到 Google Calendar、Outlook 等
依赖：无外部依赖，纯 Python 实现 ICS 生成
"""

import json
import logging
import os
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


def check_generate_schedule_requirements() -> bool:
    return True


GENERATE_SCHEDULE_SCHEMA = {
    "name": "generate_schedule",
    "description": "将学习计划导出为 ICS 日历文件。支持导入到 Google Calendar、Outlook 等日历应用。",
    "parameters": {
        "type": "object",
        "properties": {
            "plan_json": {"type": "string", "description": "学习计划 JSON 字符串"},
            "start_date": {"type": "string", "description": "开始日期（YYYY-MM-DD，默认今天）"},
            "output_path": {"type": "string", "description": "输出文件路径（可选，不填则返回 ICS 内容）"},
        },
        "required": ["plan_json"]
    }
}


def _create_ics_event(summary: str, description: str, start_time: datetime,
                      duration_hours: float = 1.0, location: str = "学习") -> str:
    end_time = start_time + timedelta(hours=duration_hours)
    uid = f"{uuid.uuid4()}@learning-planner.local"
    dtstamp = datetime.now().strftime("%Y%m%dT%H%M%SZ")

    def _format_dt(dt: datetime) -> str:
        return dt.strftime("%Y%m%dT%H%M%S")

    event = f"""BEGIN:VEVENT
UID:{uid}
DTSTAMP:{dtstamp}
DTSTART:{_format_dt(start_time)}
DTEND:{_format_dt(end_time)}
SUMMARY:{summary}
DESCRIPTION:{description}
LOCATION:{location}
STATUS:CONFIRMED
BEGIN:VALARM
TRIGGER:-PT15M
DESCRIPTION:学习提醒
ACTION:DISPLAY
END:VALARM
END:VEVENT
"""
    return event


def _generate_ics_content(plan_data: Dict[str, Any], start_date: datetime) -> str:
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Learning Planner//Hermes Agent//ZH",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
    ]

    current_date = start_date
    daily_idx = 0

    if "daily_tasks" in plan_data:
        for task in plan_data["daily_tasks"]:
            title = task.get("title", "")
            est_hours = task.get("est_hours", 1.0)
            description = task.get("description", "") or task.get("title", "")

            if title:
                event = _create_ics_event(
                    summary=title,
                    description=description,
                    start_time=datetime(current_date.year, current_date.month, current_date.day, 9, 0),
                    duration_hours=est_hours,
                )
                lines.append(event)
                daily_idx += 1

            current_date += timedelta(days=1)

    if "milestones" in plan_data:
        for milestone in plan_data["milestones"]:
            phase = milestone.get("phase", "")
            description = milestone.get("description", "")
            week_start = milestone.get("week_start", 1)

            if phase:
                milestone_date = start_date + timedelta(weeks=week_start - 1)
                event = _create_ics_event(
                    summary=f"🎯 阶段目标: {phase}",
                    description=f"{description}\n\n里程碑开始日期",
                    start_time=datetime(milestone_date.year, milestone_date.month, milestone_date.day, 9, 0),
                    duration_hours=0.5,
                )
                lines.append(event)

    lines.append("END:VCALENDAR")
    return "\n".join(lines)


def _handle_generate_schedule(args: Dict[str, Any]) -> str:
    plan_json = args.get("plan_json", "")
    start_date_str = args.get("start_date", "")
    output_path = args.get("output_path", "")

    if not plan_json:
        return json.dumps({"success": False, "error": "plan_json 参数不能为空"}, ensure_ascii=False)

    try:
        plan_data = json.loads(plan_json)
    except json.JSONDecodeError:
        return json.dumps({"success": False, "error": "plan_json 不是有效的 JSON"}, ensure_ascii=False)

    try:
        if start_date_str:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
        else:
            start_date = datetime.now().date()
    except ValueError:
        return json.dumps({"success": False, "error": "start_date 格式错误，应为 YYYY-MM-DD"}, ensure_ascii=False)

    ics_content = _generate_ics_content(plan_data, start_date)

    if output_path:
        try:
            os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(ics_content)
            return json.dumps({
                "success": True,
                "output_path": output_path,
                "event_count": ics_content.count("BEGIN:VEVENT"),
                "start_date": start_date_str or str(start_date),
            }, ensure_ascii=False, indent=2)
        except Exception as e:
            return json.dumps({
                "success": False,
                "error": f"写入文件失败: {str(e)}",
                "output_path": output_path,
            }, ensure_ascii=False)
    else:
        return json.dumps({
            "success": True,
            "ics_content": ics_content,
            "event_count": ics_content.count("BEGIN:VEVENT"),
            "start_date": start_date_str or str(start_date),
        }, ensure_ascii=False, indent=2)


try:
    from src.agent.tool_registry import registry
    registry.register(
        name="generate_schedule",
        toolset="learning",
        schema=GENERATE_SCHEDULE_SCHEMA,
        handler=_handle_generate_schedule,
        check_fn=check_generate_schedule_requirements,
        emoji="📅",
    )
except ImportError:
    pass
