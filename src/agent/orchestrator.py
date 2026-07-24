# -*- coding: utf-8 -*-
"""
Agent Orchestrator — 学习规划流程调度器

混合模式：
- generate_plan: 结构化流程（检查画像→检索→生成→检查→评估→导出）
- adjust_plan: ReAct 循环（LLM 驱动工具选择）

参考 HermesAgent 的 ConversationLoop 和 RuyiDailyStockAnalysis 的 AgentExecutor
"""

import json
import logging
import os
import time
from typing import Any, Dict, Generator, List, Optional

from src.agent.tool_registry import registry, ToolDefinition
from src.learner.models import StudyPlan
from src.prerequisite_checker import PrerequisiteChecker

logger = logging.getLogger(__name__)

PLANS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "plans")


class AgentOrchestrator:
    def __init__(self):
        self._load_tools()
        self._prerequisite_checker = PrerequisiteChecker()

    def _load_tools(self):
        import tools.retrieve_knowledge
        import tools.manage_profile
        import tools.call_llm
        import tools.evaluate_plan
        import tools.generate_schedule

    def _emit(self, event_type: str, data: Any) -> str:
        return json.dumps({"event": event_type, "data": data}, ensure_ascii=False)

    def generate_plan(self, user_id: str, goal: str) -> Generator[str, None, None]:
        os.makedirs(PLANS_DIR, exist_ok=True)

        yield self._emit("token", "正在检查用户画像...")

        profile_result = self._check_profile(user_id)
        yield self._emit("profile", profile_result)

        if not profile_result.get("success"):
            yield self._emit("error", {"message": profile_result.get("error", "画像检查失败")})
            return

        if not profile_result.get("profile", {}).get("is_complete"):
            yield self._emit("prompt", {"message": "请补充以下信息：目标、当前水平、每周学习时间、学习偏好"})
            return

        yield self._emit("token", "正在检索知识库...")

        kb_results = self._retrieve_knowledge(goal, profile_result["profile"])
        yield self._emit("knowledge", kb_results)

        yield self._emit("token", "正在生成学习计划...")

        plan_result = self._generate_plan(goal, profile_result["profile"], kb_results)
        if not plan_result.get("success"):
            yield self._emit("error", {"message": plan_result.get("error", "计划生成失败")})
            return

        content = plan_result.get("content", {})
        if isinstance(content, str):
            try:
                plan_data = json.loads(content)
            except json.JSONDecodeError:
                yield self._emit("error", {"message": "计划生成结果不是有效的JSON"})
                return
        else:
            plan_data = content

        if not isinstance(plan_data, dict):
            yield self._emit("error", {"message": "计划数据格式错误"})
            return

        plan_data["user_id"] = user_id

        yield self._emit("token", "正在检查前置依赖...")

        prerequisite_result = self._check_prerequisites(plan_data)
        yield self._emit("prerequisite", prerequisite_result)
        plan_data["prerequisite_check"] = prerequisite_result

        yield self._emit("token", "正在评估计划质量...")

        eval_result = self._evaluate_plan(plan_data)
        yield self._emit("evaluation", eval_result)

        score = eval_result.get("score", 0)
        plan_data["evaluation"] = {
            "score": score,
            "issues": eval_result.get("issues", []),
            "suggestions": eval_result.get("suggestions", []),
        }

        yield self._emit("token", "正在生成日历文件...")

        schedule_result = self._generate_schedule(plan_data)
        yield self._emit("schedule", schedule_result)

        plan_data["ics_path"] = schedule_result.get("output_path", "")

        plan_path = os.path.join(PLANS_DIR, f"{plan_data.get('plan_id', '')}.json")
        with open(plan_path, "w", encoding="utf-8") as f:
            json.dump(plan_data, f, ensure_ascii=False, indent=2)

        yield self._emit("plan", plan_data)
        yield self._emit("done", {"plan_id": plan_data.get("plan_id"), "ics_path": plan_data.get("ics_path")})

    def adjust_plan(self, plan_id: str, feedback: Dict[str, Any]) -> Generator[str, None, None]:
        plan_path = os.path.join(PLANS_DIR, f"{plan_id}.json")
        if not os.path.exists(plan_path):
            yield self._emit("error", {"message": f"计划 {plan_id} 不存在"})
            return

        with open(plan_path, encoding="utf-8") as f:
            original_plan = json.load(f)

        yield self._emit("token", "正在根据反馈调整计划...")

        user_id = original_plan.get("user_id", "")
        goal = original_plan.get("goal", "")

        for event in self._react_adjust_plan(original_plan, feedback, user_id, goal):
            yield event

    def _react_adjust_plan(self, original_plan: Dict, feedback: Dict, user_id: str, goal: str) -> Generator[str, None, None]:
        messages = [
            {"role": "system", "content": self._get_react_system_prompt()},
            {"role": "user", "content": json.dumps({
                "task": "根据用户反馈调整学习计划",
                "original_plan": original_plan,
                "feedback": feedback,
                "user_id": user_id,
                "goal": goal,
            }, ensure_ascii=False)},
        ]

        tools = registry.to_openai_tools(toolsets=["learning"])

        max_steps = 5
        plan_data = original_plan.copy()

        for step in range(max_steps):
            yield self._emit("token", f"ReAct 循环步骤 {step + 1}/{max_steps}...")

            llm_result = self._call_llm_with_tools(messages, tools)
            if not llm_result.get("success"):
                yield self._emit("error", {"message": llm_result.get("error", "LLM 调用失败")})
                break

            content = llm_result.get("content", "")

            tool_calls = self._parse_tool_calls(content)

            if not tool_calls:
                try:
                    plan_data = json.loads(content)
                except json.JSONDecodeError:
                    plan_data = {"content": content}

                yield self._emit("token", "LLM 直接返回调整结果，结束循环")
                break

            for tool_call in tool_calls:
                tool_name = tool_call.get("name")
                tool_args = tool_call.get("arguments", {})

                yield self._emit("token", f"正在调用工具: {tool_name}")

                result = registry.call_tool(tool_name, tool_args)

                try:
                    tool_result = json.loads(result)
                except json.JSONDecodeError:
                    tool_result = {"content": result}

                if tool_name == "retrieve_knowledge":
                    yield self._emit("knowledge", tool_result)
                elif tool_name == "evaluate_plan":
                    yield self._emit("evaluation", tool_result)
                    score = tool_result.get("score", 0)
                    if score >= 6:
                        yield self._emit("token", f"计划评分 {score}/10，调整完成")
                elif tool_name == "generate_schedule":
                    yield self._emit("schedule", tool_result)

                messages.append({
                    "role": "tool",
                    "content": json.dumps({
                        "tool_name": tool_name,
                        "tool_result": tool_result,
                    }, ensure_ascii=False),
                })

                if tool_name == "call_llm" and tool_result.get("content"):
                    try:
                        plan_data = tool_result.get("content")
                        if isinstance(plan_data, str):
                            plan_data = json.loads(plan_data)
                    except json.JSONDecodeError:
                        pass

        prerequisite_result = self._check_prerequisites(plan_data)
        plan_data["prerequisite_check"] = prerequisite_result

        plan_data["plan_id"] = original_plan.get("plan_id")
        plan_data["user_id"] = user_id
        plan_data["adjusted"] = True
        plan_data["adjust_reason"] = feedback.get("feedback_text", "")
        plan_data["adjusted_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")

        schedule_result = self._generate_schedule(plan_data)
        plan_data["ics_path"] = schedule_result.get("output_path", "")

        plan_path = os.path.join(PLANS_DIR, f"{plan_data.get('plan_id', '')}.json")
        with open(plan_path, "w", encoding="utf-8") as f:
            json.dump(plan_data, f, ensure_ascii=False, indent=2)

        yield self._emit("plan", plan_data)
        yield self._emit("done", {"plan_id": plan_data.get("plan_id"), "message": "计划已调整"})

    def _get_react_system_prompt(self) -> str:
        prompt = """你是一个学习规划助手，可以调用工具来完成任务。

可用工具：
1. retrieve_knowledge - 从知识库检索相关学习资料
2. evaluate_plan - 评估学习计划质量
3. generate_schedule - 生成日历文件
4. call_llm - 调用 LLM 生成文本（可用于重新生成计划）
5. manage_profile - 管理用户画像

调整计划流程：
1. 根据用户反馈决定是否需要重新检索知识库
2. 如果需要重大调整，调用 call_llm 重新生成计划
3. 评估调整后的计划质量
4. 生成新的日历文件
5. 返回最终调整后的计划

输出格式：
- 如果需要调用工具，输出 JSON 格式：
  {"tool_calls": [{"name": "工具名称", "arguments": {"参数": "值"}}]}
- 如果直接回答，输出计划的 JSON 格式数据
"""
        return prompt

    def _call_llm_with_tools(self, messages: List[Dict], tools: List[Dict]) -> Dict[str, Any]:
        system_prompt = ""
        for m in messages:
            if m.get("role") == "system":
                system_prompt = m.get("content", "")

        user_message = ""
        for m in messages:
            if m.get("role") == "user":
                user_message = m.get("content", "")

        result = registry.call_tool("call_llm", {
            "system_prompt": system_prompt,
            "user_message": user_message,
            "temperature": 0.5,
        })

        return json.loads(result)

    def _parse_tool_calls(self, content: str) -> List[Dict]:
        if not content:
            return []

        try:
            parsed = json.loads(content)
            if isinstance(parsed, dict) and "tool_calls" in parsed:
                return parsed["tool_calls"]
        except json.JSONDecodeError:
            pass

        return []

    def _check_profile(self, user_id: str) -> Dict[str, Any]:
        result = registry.call_tool("manage_profile", {"action": "get", "user_id": user_id})
        return json.loads(result)

    def _retrieve_knowledge(self, goal: str, profile: Dict[str, Any]) -> Dict[str, Any]:
        query = f"{goal} {' '.join(profile.get('known_topics', []))}"
        # 增加 top_k 获取更多文档，以便提取更丰富的学习资源
        result = registry.call_tool("retrieve_knowledge", {"query": query, "top_k": 30})
        return json.loads(result)

    def _check_prerequisites(self, plan_data: Dict[str, Any]) -> Dict[str, Any]:
        return self._prerequisite_checker.check_plan(plan_data)

    def _format_knowledge_for_prompt(self, kb_results: Dict[str, Any], goal: str = "") -> str:
        """将知识库检索结果格式化为便于LLM使用的格式"""
        from src.knowledge_base_manager import kb_manager
        from src.resource_extractor import extract_resources_from_content, extract_exercises_from_content, resource_to_dict

        lines = []

        # 从本地知识库检索相关文档
        local_docs = kb_manager.search(goal, top_k=15) if goal else []

        # 收集所有资源链接
        all_resources = []
        all_exercises = []
        resource_id = 1
        exercise_id = 1

        for doc in local_docs:
            # 文档本身的资源
            for res in doc.resources:
                all_resources.append({
                    "id": f"R{resource_id}",
                    "title": res.title,
                    "url": res.url,
                    "type": res.type,
                    "description": res.description,
                    "source_doc": doc.title,
                })
                resource_id += 1

            # 文档对应的练习题
            if doc.category == "exercises":
                all_exercises.append({
                    "id": f"E{exercise_id}",
                    "title": doc.title,
                    "url": f"/learn/kb/{doc.doc_id}",
                    "description": f"练习题文档，共{doc.estimated_hours}小时，难度{doc.difficulty}/3",
                    "source_doc": doc.title,
                    "doc_id": doc.doc_id,
                })
                exercise_id += 1
            elif doc.category == "python_learning_path":
                # 从学习资料中提取在线练习资源
                for res in doc.resources:
                    if res.type == "exercise":
                        all_exercises.append({
                            "id": f"E{exercise_id}",
                            "title": res.title,
                            "url": res.url,
                            "description": res.description,
                            "source_doc": doc.title,
                        })
                        exercise_id += 1

        # 从 Dify 检索结果中提取学习资源
        dify_results = kb_results.get("results", []) if kb_results.get("success") else []
        dify_docs_info = []

        for i, r in enumerate(dify_results):
            title = r.get("title", "")
            content = r.get("content", "")
            doc_id = r.get("document_id", r.get("id", r.get("metadata", {}).get("document_id", f"dify_{i}")))
            score = r.get("score", 0)
            metadata = r.get("metadata", {})

            dify_docs_info.append({
                "title": title,
                "doc_id": doc_id,
                "score": score,
                "content": content[:200],
            })

            # 从文档内容中提取资源
            extracted_resources = extract_resources_from_content(content, source_doc=title, doc_id=doc_id)
            for res in extracted_resources:
                res_dict = resource_to_dict(res)
                res_dict["id"] = f"DR{resource_id}"
                all_resources.append(res_dict)
                resource_id += 1

            # 从文档内容中提取练习题
            extracted_exercises = extract_exercises_from_content(content, source_doc=title, doc_id=doc_id)
            for ex in extracted_exercises:
                ex_dict = resource_to_dict(ex)
                ex_dict["id"] = f"DE{exercise_id}"
                all_exercises.append(ex_dict)
                exercise_id += 1

        # 去重
        seen_res = set()
        unique_resources = []
        for r in all_resources:
            key = r.get("url", "") or r.get("title", "")
            if key and key not in seen_res:
                seen_res.add(key)
                unique_resources.append(r)

        seen_ex = set()
        unique_exercises = []
        for e in all_exercises:
            key = e.get("url", "") or e.get("title", "")
            if key and key not in seen_ex:
                seen_ex.add(key)
                unique_exercises.append(e)

        if unique_resources:
            lines.append("## 学习资源（可作为任务的 resources，点击链接可直接打开，务必为每个任务选择2-5个最匹配的）")
            lines.append("")
            for r in unique_resources[:30]:
                type_label = {"video": "视频", "article": "文档", "course": "课程", "exercise": "在线练习", "other": "其他"}.get(r.get("type", "other"), r.get("type", "其他"))
                lines.append(f"[{r.get('id', 'R')}] [{type_label}] {r.get('title', '')}")
                lines.append(f"    URL: {r.get('url', '')}")
                if r.get("description"):
                    lines.append(f"    简介: {r['description'][:100]}")
                if r.get("source_doc"):
                    lines.append(f"    来源: {r['source_doc']}")
                lines.append("")

        if unique_exercises:
            lines.append("## 练习题（可作为任务的 exercises，务必为每个任务选择1-3个匹配的）")
            lines.append("")
            for e in unique_exercises[:20]:
                lines.append(f"[{e.get('id', 'E')}] {e.get('title', '')}")
                if e.get("url"):
                    lines.append(f"    URL: {e['url']}")
                if e.get("description"):
                    lines.append(f"    简介: {e['description'][:100]}")
                if e.get("source_doc"):
                    lines.append(f"    来源: {e['source_doc']}")
                lines.append("")

        # Dify 知识库文档摘要（补充上下文）
        if dify_docs_info:
            lines.append("## 相关知识库文档摘要（帮助理解知识点上下文）")
            lines.append("")
            for i, doc in enumerate(dify_docs_info[:10], 1):
                lines.append(f"[D{i}] {doc['title']} (相关度: {doc['score']:.2f})")
                lines.append(f"    摘要: {doc['content'][:150]}")
                lines.append("")

        if not lines:
            return "(知识库未检索到相关内容)"

        lines.append("## 使用说明")
        lines.append("1. 【重要】生成每个每日任务时，必须从上述「学习资源」中选择最相关的 2-5 个作为任务的 resources 数组")
        lines.append("2. 【重要】从上述「练习题」中选择 1-3 个最匹配的作为任务的 exercises 数组")
        lines.append("3. resources 数组中每个对象必须包含: title（资源标题）、type（video/article/course/exercise/other）、url（资源链接，必须原样完整复制上面给出的URL）")
        lines.append("4. exercises 数组中每个对象必须包含: title（练习题标题）、url（链接，有则完整复制，没有则为空字符串）、description（简介）")
        lines.append("5. 【重要】URL 必须原样完整复制上面给出的链接，确保用户点击可以直接打开，绝对不能省略或修改URL")
        lines.append("6. 资源和练习题必须与任务内容高度相关，不要乱配")
        lines.append("7. 尽量多选相关的资源，让学习内容更全面（建议每个任务至少3个资源，2个练习题）")
        lines.append("8. 优先选择来源可靠、质量高的资源（如官方文档、知名教程）")

        return "\n".join(lines)

    def _generate_plan(self, goal: str, profile: Dict[str, Any], kb_results: Dict[str, Any]) -> Dict[str, Any]:
        kb_text = self._format_knowledge_for_prompt(kb_results, goal)

        user_message = json.dumps({
            "goal": goal,
            "profile": profile,
            "knowledge_base_results": kb_text,
        }, ensure_ascii=False)

        system_prompt = ""
        prompt_path = os.path.join(os.path.dirname(__file__), "..", "learner", "prompts", "plan_generation.txt")
        if os.path.exists(prompt_path):
            with open(prompt_path, "r", encoding="utf-8") as f:
                system_prompt = f.read()

        result = registry.call_tool("call_llm", {
            "system_prompt": system_prompt,
            "user_message": user_message,
            "temperature": 0.7,
        })

        plan_data = json.loads(result)

        # 后处理：为资源不足的任务自动补充知识库资源
        if plan_data.get("success") and plan_data.get("content", {}).get("daily_tasks"):
            plan_data["content"] = self._enrich_tasks_with_resources(
                plan_data["content"], kb_results, goal
            )

        return plan_data

    def _enrich_tasks_with_resources(self, plan: Dict[str, Any], kb_results: Dict[str, Any], goal: str) -> Dict[str, Any]:
        """为资源不足的任务自动补充知识库资源"""
        from src.knowledge_base_manager import kb_manager
        from src.resource_extractor import extract_resources_from_content, extract_exercises_from_content

        daily_tasks = plan.get("daily_tasks", [])
        if not daily_tasks:
            return plan

        # 获取所有本地知识库文档（python_learning_path类）
        all_docs = []
        kb_manager.load_all()
        for doc in kb_manager.get_all_docs().values():
            if doc.category == "python_learning_path":
                all_docs.append(doc)

        if not all_docs:
            return plan

        # 按文件名排序（01-, 02-, ...）
        all_docs.sort(key=lambda d: d.doc_id)

        # 预定义的关键词映射表（任务关键词 -> 文档关键词）
        keyword_map = {
            "变量": ["变量", "数据类型", "int", "float", "str", "print", "input", "基础语法"],
            "字符串": ["字符串", "str", "切片", "格式化"],
            "数字": ["数字", "运算", "int", "float", "类型转换"],
            "运算": ["运算符", "数字", "算术"],
            "条件": ["条件", "if", "elif", "else", "流程控制"],
            "判断": ["条件", "if", "elif", "else", "流程控制"],
            "if": ["条件", "if", "elif", "else", "流程控制"],
            "循环": ["循环", "for", "while", "流程控制"],
            "for": ["循环", "for", "while", "流程控制"],
            "while": ["循环", "for", "while", "流程控制"],
            "函数": ["函数", "def", "参数", "返回值"],
            "def": ["函数", "def", "参数", "返回值"],
            "列表": ["列表", "list", "元组", "数据结构"],
            "list": ["列表", "list", "元组", "数据结构"],
            "元组": ["列表", "list", "元组", "数据结构"],
            "tuple": ["列表", "list", "元组", "数据结构"],
            "字典": ["字典", "dict", "集合", "set", "数据结构"],
            "dict": ["字典", "dict", "集合", "set", "数据结构"],
            "集合": ["字典", "dict", "集合", "set", "数据结构"],
            "set": ["字典", "dict", "集合", "set", "数据结构"],
            "模块": ["模块", "包", "import", "module"],
            "import": ["模块", "包", "import", "module"],
            "包": ["模块", "包", "import", "module"],
            "文件": ["文件", "异常", "io", "open"],
            "异常": ["文件", "异常", "io", "open"],
            "open": ["文件", "异常", "io", "open"],
            "面向对象": ["面向对象", "类", "class", "对象"],
            "class": ["面向对象", "类", "class", "对象"],
            "类": ["面向对象", "类", "class", "对象"],
            "继承": ["面向对象", "类", "class", "继承", "多态"],
            "标准库": ["标准库", "os", "sys", "datetime", "常用库"],
            "numpy": ["NumPy", "数组", "数值计算", "numpy"],
            "数组": ["NumPy", "数组", "数值计算", "numpy"],
            "pandas": ["Pandas", "数据可视化", "数据分析", "pandas"],
            "数据处理": ["Pandas", "数据可视化", "数据分析", "pandas"],
            "可视化": ["Pandas", "数据可视化", "数据分析", "pandas"],
            "matplotlib": ["Pandas", "数据可视化", "数据分析", "pandas"],
            "实战": ["综合实战", "项目", "数据分析"],
            "项目": ["综合实战", "项目", "数据分析"],
        }

        def find_best_doc(task_title: str, task_desc: str):
            """找到最匹配的知识库文档"""
            text = f"{task_title} {task_desc}".lower()
            
            best_doc = None
            best_score = 0.0
            
            for doc in all_docs:
                score = 0.0
                doc_title = doc.title.lower()
                doc_keywords = [k.lower() for k in doc.keywords]
                
                # 标题关键词匹配
                for kw in doc_keywords:
                    if kw in text:
                        score += 3.0
                
                # 标题中包含的关键词映射
                for task_kw, doc_kws in keyword_map.items():
                    if task_kw.lower() in text:
                        for dk in doc_kws:
                            if dk.lower() in doc_title or dk.lower() in [k.lower() for k in doc.keywords]:
                                score += 2.0
                                break
                
                # 标题词直接匹配
                for word in text.split():
                    if len(word) > 1 and word in doc_title:
                        score += 1.5
                
                if score > best_score:
                    best_score = score
                    best_doc = doc
            
            return best_doc, best_score

        # 也收集所有练习题文档
        exercise_docs = []
        for doc in kb_manager.get_all_docs().values():
            if doc.category == "exercises":
                exercise_docs.append(doc)
        exercise_docs.sort(key=lambda d: d.doc_id)

        def find_best_exercise(task_title: str, task_desc: str):
            """找到最匹配的练习题"""
            text = f"{task_title} {task_desc}".lower()
            best = None
            best_score = 0.0
            for ex_doc in exercise_docs:
                score = 0.0
                ex_title = ex_doc.title.lower()
                ex_kws = [k.lower() for k in ex_doc.keywords]
                for kw in ex_kws:
                    if kw in text:
                        score += 3.0
                for word in text.split():
                    if len(word) > 1 and word in ex_title:
                        score += 1.5
                if score > best_score:
                    best_score = score
                    best = ex_doc
            return best

        # 为每个任务补充资源
        for task in daily_tasks:
            task_title = task.get("title", "")
            task_desc = task.get("description", "")
            resources = task.get("resources", [])
            exercises = task.get("exercises", [])

            # 找到最匹配的知识库文档
            best_doc, score = find_best_doc(task_title, task_desc)
            
            if best_doc and best_doc.resources:
                # 使用该文档的所有资源（按类型分类）
                existing_urls = {r.get("url", "") for r in resources if r.get("url")}
                
                for res in best_doc.resources:
                    if res.url and res.url not in existing_urls:
                        resources.append({
                            "title": res.title,
                            "url": res.url,
                            "type": res.type,
                            "description": res.description,
                        })
                        existing_urls.add(res.url)
                
                task["resources"] = resources

            # 找到最匹配的练习题
            if len(exercises) < 3:
                best_ex = find_best_exercise(task_title, task_desc)
                if best_ex:
                    ex_url = f"/learn/kb/{best_ex.doc_id}"
                    existing_ex_urls = {e.get("url", "") for e in exercises}
                    if ex_url not in existing_ex_urls:
                        exercises.append({
                            "title": best_ex.title,
                            "url": ex_url,
                            "description": f"难度 {best_ex.difficulty}/3，预计 {best_ex.estimated_hours} 小时",
                        })
                
                # 也把文档里的在线练习加进去
                if best_doc and best_doc.resources:
                    for res in best_doc.resources:
                        if res.type == "exercise" and res.url:
                            existing_ex_urls = {e.get("url", "") for e in exercises}
                            if res.url not in existing_ex_urls:
                                exercises.append({
                                    "title": res.title,
                                    "url": res.url,
                                    "description": res.description,
                                })
                
                task["exercises"] = exercises

        plan["daily_tasks"] = daily_tasks
        return plan

    def _adjust_plan(self, original_plan: Dict[str, Any], feedback: Dict[str, Any]) -> Dict[str, Any]:
        user_message = json.dumps({
            "original_plan": original_plan,
            "feedback": feedback,
        }, ensure_ascii=False)

        system_prompt = ""
        prompt_path = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                                   "skills", "autonomous-ai-agents", "learning-planner",
                                   "prompts", "plan_adjustment.txt")
        if os.path.exists(prompt_path):
            with open(prompt_path, "r", encoding="utf-8") as f:
                system_prompt = f.read()

        result = registry.call_tool("call_llm", {
            "system_prompt": system_prompt,
            "user_message": user_message,
            "temperature": 0.5,
        })

        return json.loads(result)

    def _regenerate_plan(self, goal: str, profile: Dict[str, Any], kb_results: Dict[str, Any],
                        eval_result: Dict[str, Any]) -> Dict[str, Any]:
        kb_text = ""
        if kb_results.get("success"):
            for r in kb_results.get("results", []):
                kb_text += f"[{r.get('title','')}]\n{r.get('content','')}\n\n"

        suggestions = eval_result.get("suggestions", [])
        issues = eval_result.get("issues", [])

        user_message = json.dumps({
            "goal": goal,
            "profile": profile,
            "knowledge_base_results": kb_text,
            "previous_evaluation": {
                "score": eval_result.get("score", 0),
                "issues": issues,
                "suggestions": suggestions,
            },
            "improvement_request": f"请根据以下问题改进计划：{', '.join(issues)}。改进建议：{', '.join(suggestions)}",
        }, ensure_ascii=False)

        try:
            with open(os.path.join(os.path.dirname(__file__), "..", "learner", "prompts", "plan_generation.txt"), "r", encoding="utf-8") as f:
                system_prompt = f.read()
        except Exception:
            system_prompt = ""

        system_prompt += "\n\n请根据以下评估结果和改进建议重新生成更优的学习计划：\n" + \
                         f"问题：{', '.join(issues)}\n建议：{', '.join(suggestions)}"

        result = registry.call_tool("call_llm", {
            "system_prompt": system_prompt,
            "user_message": user_message,
            "temperature": 0.5,
        })

        result_data = json.loads(result)
        if result_data.get("success"):
            return result_data.get("content", {})
        return {}

    def _evaluate_plan(self, plan_data: Dict[str, Any]) -> Dict[str, Any]:
        plan_json = json.dumps(plan_data, ensure_ascii=False)
        result = registry.call_tool("evaluate_plan", {"plan_json": plan_json})
        return json.loads(result)

    def _generate_schedule(self, plan_data: Dict[str, Any]) -> Dict[str, Any]:
        plan_json = json.dumps(plan_data, ensure_ascii=False)
        output_path = os.path.join(PLANS_DIR, f"{plan_data.get('plan_id', '')}.ics")
        result = registry.call_tool("generate_schedule", {
            "plan_json": plan_json,
            "output_path": output_path,
            "start_date": time.strftime("%Y-%m-%d"),
        })
        return json.loads(result)