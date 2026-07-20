# -*- coding: utf-8 -*-
"""学习规划引擎 — 编排画像采集 → KB检索 → LLM生成 → 评估 → 导出"""
import json, os, time, uuid
from dataclasses import asdict
from src.dify_client import DifyClient
from src.profile_manager import ProfileManager
from src.learner.models import StudyPlan

PROMPTS_DIR = os.path.join(os.path.dirname(__file__), "prompts")
PLANS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "plans")


class PlanEngine:
    def __init__(self, dify_client: DifyClient = None, profile_mgr: ProfileManager = None):
        self.dify = dify_client or DifyClient()
        self.profile_mgr = profile_mgr or ProfileManager()
        os.makedirs(PLANS_DIR, exist_ok=True)

    def _load_prompt(self, name: str) -> str:
        path = os.path.join(PROMPTS_DIR, name)
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                return f.read()
        return ""

    def _call_llm(self, system_prompt: str, user_message: str) -> dict:
        """调用 LLM（可通过 Hermes Agent 或直接 HTTP）"""
        import urllib.request

        api_key = os.getenv("LLM_API_KEY", "")
        base_url = os.getenv("LLM_BASE_URL", "https://api.siliconflow.cn/v1")
        model = os.getenv("LLM_MODEL", "deepseek-ai/DeepSeek-V4-Flash")

        if not api_key:
            # 无 API Key → 返回 mock 数据
            return self._mock_plan()

        payload = json.dumps({
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            "response_format": {"type": "json_object"},
        }).encode("utf-8")

        req = urllib.request.Request(
            f"{base_url}/chat/completions", data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            }
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                result = json.loads(resp.read().decode("utf-8"))
            content = result["choices"][0]["message"]["content"]
            return json.loads(content)
        except Exception as e:
            print(f"[PlanEngine] LLM 调用失败，降级为 mock: {e}")
            return self._mock_plan()

    def _mock_plan(self) -> dict:
        return {
            "plan_id": f"plan_{int(time.time())}",
            "goal": "学习Python数据分析",
            "user_id": "demo",
            "total_weeks": 12,
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "milestones": [
                {"week_start": 1, "week_end": 2, "phase": "Python基础语法",
                 "description": "变量、数据类型、条件判断、循环结构",
                 "objectives": ["掌握基础语法", "能写简单脚本"], "task_count": 10, "difficulty": 1},
                {"week_start": 3, "week_end": 4, "phase": "函数与模块",
                 "description": "函数定义、参数传递、模块导入",
                 "objectives": ["理解函数作用域", "能组织多文件项目"], "task_count": 8, "difficulty": 2},
                {"week_start": 5, "week_end": 6, "phase": "NumPy与Pandas入门",
                 "description": "数组操作、DataFrame基础、CSV处理",
                 "objectives": ["能处理结构化数据", "能做基础统计分析"], "task_count": 8, "difficulty": 2},
                {"week_start": 7, "week_end": 8, "phase": "数据可视化",
                 "description": "Matplotlib、Seaborn基础图表",
                 "objectives": ["能绘制折线图/柱状图/散点图"], "task_count": 6, "difficulty": 2},
                {"week_start": 9, "week_end": 10, "phase": "综合实战项目",
                 "description": "选择一个真实数据集完成完整分析",
                 "objectives": ["能独立完成数据分析项目"], "task_count": 4, "difficulty": 3},
                {"week_start": 11, "week_end": 12, "phase": "复习与总结",
                 "description": "回顾所有知识点、查漏补缺",
                 "objectives": ["形成完整的知识体系"], "task_count": 4, "difficulty": 1},
            ],
            "daily_tasks": [
                {"day": 1, "title": "安装Python环境 + Hello World", "est_hours": 1.0},
                {"day": 2, "title": "变量与数据类型练习", "est_hours": 1.5},
                {"day": 3, "title": "条件判断（if/elif/else）练习", "est_hours": 1.0},
            ],
            "prerequisite_check": {"status": "passed", "details": [], "warnings": []},
            "evaluation": {"score": 8, "issues": [], "suggestions": []},
        }

    def generate(self, user_id: str, goal: str) -> StudyPlan:
        profile = self.profile_mgr.get(user_id)
        if not profile or not profile.is_complete():
            raise ValueError("画像不完整，请先完成画像采集")

        # 检索知识库
        kb_query = f"{goal} {' '.join(profile.known_topics or [])}"
        kb_results = self.dify.retrieve_formatted(kb_query)

        # 构造 LLM 输入
        system_prompt = self._load_prompt("plan_generation.txt")
        user_message = json.dumps({
            "goal": goal,
            "profile": {
                "current_level": profile.current_level,
                "hours_per_week": profile.hours_per_week,
                "preference": profile.preference,
                "known_topics": profile.known_topics or [],
            },
            "knowledge_base_results": kb_results,
        }, ensure_ascii=False)

        # 调用 LLM
        plan_dict = self._call_llm(system_prompt, user_message)
        plan = StudyPlan.from_dict(plan_dict)
        plan.user_id = user_id

        # 保存
        plan_path = os.path.join(PLANS_DIR, f"{plan.plan_id}.json")
        with open(plan_path, "w", encoding="utf-8") as f:
            json.dump(plan.to_dict(), f, ensure_ascii=False, indent=2)

        return plan

    def adjust(self, plan_id: str, feedback: dict) -> StudyPlan:
        plan_path = os.path.join(PLANS_DIR, f"{plan_id}.json")
        if not os.path.exists(plan_path):
            raise FileNotFoundError(f"计划 {plan_id} 不存在")

        with open(plan_path, encoding="utf-8") as f:
            original = json.load(f)

        # 调整 prompt + LLM 调用（当前返回 mock 修改结果）
        original["adjusted"] = True
        original["adjust_reason"] = feedback.get("feedback_text", "")
        plan = StudyPlan.from_dict(original)

        plan_path = os.path.join(PLANS_DIR, f"{plan_id}.json")
        with open(plan_path, "w", encoding="utf-8") as f:
            json.dump(original, f, ensure_ascii=False, indent=2)
        return plan