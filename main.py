# -*- coding: utf-8 -*-
"""
Ruyi Learning Planner — 智能学习规划助手入口

使用方式：
  python main.py plan --user-id <用户ID> --goal <学习目标>
  python main.py serve
  python main.py tools list
"""

import argparse
import json
import logging
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.config import setup_env, get_config
from src.logging_config import setup_logging


def setup():
    setup_env()
    config = get_config()
    setup_logging(log_prefix="learning_planner")


def cmd_plan(args):
    """生成学习计划"""
    from src.agent.orchestrator import AgentOrchestrator

    orchestrator = AgentOrchestrator()
    print(f"🎯 开始为用户 {args.user_id} 生成学习计划...")
    print(f"📚 学习目标: {args.goal}")
    print("-" * 60)

    plan_data = None
    for event in orchestrator.generate_plan(args.user_id, args.goal):
        event_json = json.loads(event)
        event_type = event_json["event"]
        data = event_json["data"]

        if event_type == "token":
            print(f"   {data}")
        elif event_type == "profile":
            if data.get("success"):
                if data.get("exists") and data.get("profile"):
                    profile = data["profile"]
                    print(f"👤 用户画像: {profile.get('goal', '')} | {profile.get('current_level', '')} | {profile.get('hours_per_week', '')}h/周")
                    if not profile.get("is_complete"):
                        print("   ⚠️ 画像不完整，请先补充信息")
                else:
                    print("   ⚠️ 用户画像不存在，请先创建")
        elif event_type == "prompt":
            print(f"\n📝 需要补充信息: {data.get('message', '')}")
            print("   使用以下命令创建/更新画像:")
            print("   python main.py profile create --user-id <用户ID>")
            print("   python main.py profile update --user-id <用户ID> --goal <目标> --level <水平> --hours <小时> --preference <偏好>")
        elif event_type == "knowledge":
            if data.get("success"):
                print(f"📖 检索到 {data.get('count', 0)} 条知识库内容")
        elif event_type == "evaluation":
            print(f"📊 计划评分: {data.get('score', 0)}/10")
            if data.get("issues"):
                for i, issue in enumerate(data["issues"], 1):
                    print(f"   问题{i}: {issue}")
            if data.get("suggestions"):
                for i, suggestion in enumerate(data["suggestions"], 1):
                    print(f"   建议{i}: {suggestion}")
        elif event_type == "schedule":
            if data.get("success"):
                print(f"📅 日历文件已生成: {data.get('output_path', '')}")
        elif event_type == "plan":
            plan_data = data
            print(f"\n✅ 计划生成成功!")
            print(f"   计划ID: {data.get('plan_id', '')}")
            print(f"   总周数: {data.get('total_weeks', 0)} 周")
            print(f"   里程碑: {len(data.get('milestones', []))} 个")
            print(f"   每日任务: {len(data.get('daily_tasks', []))} 个")
        elif event_type == "done":
            print(f"\n🎉 完成! 计划ID: {data.get('plan_id', '')}")
        elif event_type == "error":
            print(f"\n❌ 错误: {data.get('message', '')}")
            return 1

    if plan_data:
        plan_path = os.path.join("data", "plans", f"{plan_data.get('plan_id', '')}.json")
        print(f"\n📁 计划文件已保存到: {plan_path}")

    return 0


def cmd_serve(args):
    """启动 FastAPI 服务"""
    import uvicorn
    from api.app import app

    host = args.host or os.getenv("API_HOST", "0.0.0.0")
    port = args.port or int(os.getenv("API_PORT", "8000"))

    print(f"🚀 启动学习规划助手服务...")
    print(f"📍 地址: http://{host}:{port}")
    print(f"📖 API文档: http://{host}:{port}/docs")
    print("按 Ctrl+C 停止服务")

    uvicorn.run("main:app", host=host, port=port, reload=True)


def cmd_tools(args):
    """工具管理"""
    from src.agent.tool_registry import registry

    registry.discover_and_load()

    if args.action == "list":
        print("📦 已注册工具列表:")
        print("-" * 60)
        definitions = registry.get_definitions()
        for tool in definitions:
            emoji = tool.get("emoji", "")
            name = tool.get("name", "")
            desc = tool.get("description", "")[:50] + "..." if len(tool.get("description", "")) > 50 else tool.get("description", "")
            print(f"  {emoji} {name}")
            print(f"     {desc}")
            params = tool.get("parameters", {}).get("properties", {})
            if params:
                print(f"     参数: {', '.join(params.keys())}")
            print()

    elif args.action == "call":
        if not args.name:
            print("❌ 请指定工具名称")
            return 1

        args_dict = {}
        for arg in args.args:
            if "=" in arg:
                key, value = arg.split("=", 1)
                try:
                    args_dict[key] = json.loads(value)
                except json.JSONDecodeError:
                    args_dict[key] = value
            else:
                args_dict[arg] = True

        print(f"🔧 调用工具: {args.name}")
        print(f"   参数: {args_dict}")
        print("-" * 60)

        result = registry.call_tool(args.name, args_dict)
        try:
            result_data = json.loads(result)
            if result_data.get("success"):
                print(f"✅ 成功!")
                print(json.dumps(result_data, ensure_ascii=False, indent=2))
            else:
                print(f"❌ 失败: {result_data.get('error', '')}")
        except json.JSONDecodeError:
            print(result)

    return 0


def cmd_profile(args):
    """用户画像管理"""
    from src.agent.tool_registry import registry
    registry.discover_and_load()

    if args.action == "get":
        result = registry.call_tool("manage_profile", {"action": "get", "user_id": args.user_id})
    elif args.action == "create":
        result = registry.call_tool("manage_profile", {"action": "create", "user_id": args.user_id})
    elif args.action == "update":
        update_data = {}
        if args.goal:
            update_data["goal"] = args.goal
        if args.level:
            update_data["current_level"] = args.level
        if args.hours:
            update_data["hours_per_week"] = args.hours
        if args.preference:
            update_data["preference"] = args.preference
        result = registry.call_tool("manage_profile", {"action": "update", "user_id": args.user_id, **update_data})
    else:
        print(f"❌ 不支持的操作: {args.action}")
        return 1

    try:
        result_data = json.loads(result)
        print(json.dumps(result_data, ensure_ascii=False, indent=2))
    except json.JSONDecodeError:
        print(result)

    return 0


def main():
    setup()

    parser = argparse.ArgumentParser(description="Ruyi Learning Planner — 智能学习规划助手")
    subparsers = parser.add_subparsers(dest="command", required=True)

    plan_parser = subparsers.add_parser("plan", help="生成学习计划")
    plan_parser.add_argument("--user-id", required=True, help="用户ID")
    plan_parser.add_argument("--goal", required=True, help="学习目标")

    serve_parser = subparsers.add_parser("serve", help="启动服务")
    serve_parser.add_argument("--host", help="主机地址")
    serve_parser.add_argument("--port", type=int, help="端口号")

    tools_parser = subparsers.add_parser("tools", help="工具管理")
    tools_sub = tools_parser.add_subparsers(dest="action", required=True)
    tools_sub.add_parser("list", help="列出所有工具")
    call_parser = tools_sub.add_parser("call", help="调用工具")
    call_parser.add_argument("name", help="工具名称")
    call_parser.add_argument("args", nargs="*", help="参数 key=value")

    profile_parser = subparsers.add_parser("profile", help="用户画像管理")
    profile_sub = profile_parser.add_subparsers(dest="action", required=True)
    profile_sub.add_parser("get", help="获取画像").add_argument("--user-id", required=True)
    profile_sub.add_parser("create", help="创建画像").add_argument("--user-id", required=True)
    update_parser = profile_sub.add_parser("update", help="更新画像")
    update_parser.add_argument("--user-id", required=True)
    update_parser.add_argument("--goal", help="学习目标")
    update_parser.add_argument("--level", help="当前水平")
    update_parser.add_argument("--hours", type=int, help="每周学习小时")
    update_parser.add_argument("--preference", help="学习偏好")

    args = parser.parse_args()

    if args.command == "plan":
        sys.exit(cmd_plan(args))
    elif args.command == "serve":
        cmd_serve(args)
    elif args.command == "tools":
        sys.exit(cmd_tools(args))
    elif args.command == "profile":
        sys.exit(cmd_profile(args))


if __name__ == "__main__":
    main()
