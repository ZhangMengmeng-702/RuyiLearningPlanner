---
name: learning-planner
description: "智能学习规划助手 — 采集用户画像、检索知识库、生成个性化学习计划、动态调整"
version: 1.0.0
author: Ruyi Team
tags: [learning, education, planning, hermes-agent]
tools:
  - retrieve_knowledge
  - manage_profile
  - call_llm
  - evaluate_plan
  - generate_schedule
---

# Learning Planner Skill

## 触发条件

当用户说以下内容时激活本 skill：

- "我想学..."
- "帮我规划..."
- "请制定学习计划..."
- "如何系统学习..."
- Any message from the FastAPI `/learn/chat` endpoint

## 工作流程

### 完整规划流程

```
用户输入学习目标
  ↓ Step 1: 检查画像
    调用 manage_profile(action="get", user_id)
    → 如果画像不完整：
      调用 call_llm 生成追问 → 返回给用户等待回答
    → 如果完整：继续 Step 2

  ↓ Step 2: 检索知识库
    调用 retrieve_knowledge(query=用户目标 + 画像信息)
    → 返回相关课程章节、前置知识、练习题

  ↓ Step 3: 生成计划
    调用 call_llm(system_prompt=plan_generation.txt, user_message={画像+检索结果})
    → 返回结构化 JSON（StudyPlan）

  ↓ Step 4: 质量评估
    调用 evaluate_plan(plan)
    → 如果 score < 6：重新生成
    → 如果 score >= 6：继续

  ↓ Step 5: 导出日程
    调用 generate_schedule(plan)
    → 生成 .ics 日历文件

  ↓ Step 6: 返回结果
    → 返回 Plan JSON + .ics 文件路径
```

### 调整流程

```
用户反馈（难度评分 + 完成度 + 文字）
  ↓ Step 1: 读取原计划
  ↓ Step 2: 调用 call_llm(adjust_prompt, {原计划+反馈})
  ↓ Step 3: 评估调整后的计划
  ↓ Step 4: 返回调整结果
```

## 工具清单

### retrieve_knowledge

- **职责**: 调用 Dify KB API 检索学习内容
- **输入**: query (str), top_k (int, default=5), kb_id (str, optional)
- **输出**: RetrievalResult 列表
- **实现**: `tools/retrieve_knowledge.py`

### manage_profile

- **职责**: 创建/读取/更新用户画像
- **输入**: action ("get"|"create"|"update"), user_id, data (dict, optional)
- **输出**: Profile JSON
- **实现**: `tools/manage_profile.py`

### call_llm

- **职责**: 调用硅基流动 LLM（DeepSeek）生成文本或结构化数据
- **输入**: system_prompt, user_message, response_schema (optional)
- **输出**: 文本或 JSON
- **实现**: `tools/call_llm.py`

### evaluate_plan

- **职责**: 评估学习计划质量，返回评分和改进建议
- **输入**: plan (StudyPlan JSON)
- **输出**: { score, issues[], suggestions[] }
- **实现**: `tools/evaluate_plan.py`

### generate_schedule

- **职责**: 将计划中的 daily_tasks 导出为 .ics 日历文件
- **输入**: plan (StudyPlan JSON), output_path (optional)
- **输出**: { file_path, task_count }
- **实现**: `tools/generate_schedule.py`