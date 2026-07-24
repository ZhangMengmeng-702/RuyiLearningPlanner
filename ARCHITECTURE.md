# Ruyi Learning Planner - 架构整合文档

## 概述

Ruyi Learning Planner 是一个基于 FastAPI + Hermes Agent 的智能学习规划助手，为用户提供个性化学习路径规划、进度追踪和自适应调整能力。系统采用前后端分离架构：

- **后端**：FastAPI 传输层 + Hermes Agent 核心推理引擎，负责业务逻辑、数据存储、认证鉴权和计划生成
- **前端**：React + TypeScript 单页应用，提供对话交互、计划看板、今日任务等用户界面

系统已实现完整的用户认证体系、安全防护机制和自适应调整引擎。

## 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| 框架 | FastAPI 0.104+ | 高性能异步 API 框架 |
| 数据库 | SQLite | 轻量级嵌入式数据库（会话、进度） |
| 存储 | JSON 文件 | 用户画像、学习计划、用户数据持久化 |
| Agent | Hermes Agent | 核心 Agent 引擎（HTTP 连接） |
| LLM | DeepSeek (硅基流动) | 学习计划生成与评估（fallback） |
| RAG | Dify | 知识库向量检索 |
| 认证 | JWT + Cookie | 基于 HttpOnly Cookie 的会话管理 |
| 前端 | React + TypeScript + Vite | 单页应用框架 |
| 样式 | Tailwind CSS | 原子化 CSS 框架 |
| 文档 | OpenAPI 3.0 | 自动生成 API 文档 |

## 项目结构

```
RuyiLearningPlanner/
├── api/                    # REST API 层
│   ├── app.py              # FastAPI 主应用（路由注册、中间件）
│   ├── deps.py             # 依赖注入（获取当前用户）
│   ├── middlewares/        # 中间件
│   │   └── auth.py         # 认证中间件（权限校验、豁免路径）
│   └── v1/endpoints/       # API 端点
│       ├── auth.py         # 用户认证（登录/注册/登出/状态）
│       ├── learn_chat.py   # 学习对话（SSE）、计划管理、会话管理
│       ├── profile.py      # 用户画像 CRUD
│       ├── progress.py     # 进度追踪（打卡、统计、自适应调整）
│       └── knowledge.py    # 知识库文档（列表、详情、搜索）
├── src/                    # 核心业务逻辑
│   ├── agent/              # Agent 核心模块
│   │   ├── orchestrator.py # 流程调度器（混合 ReAct）
│   │   ├── tool_registry.py # 工具注册表（@tool 装饰器）
│   │   └── session_db.py   # 会话持久化（SQLite）
│   ├── llm/                # LLM 客户端
│   │   └── hermes_client.py # Hermes Agent HTTP 客户端
│   ├── learner/            # 学习规划引擎
│   │   ├── models.py       # 数据模型
│   │   ├── plan_engine.py  # 计划生成引擎
│   │   ├── plan_adjuster.py # 计划自适应调整器
│   │   └── prompts/        # 提示词模板
│   ├── knowledge_base_manager.py # 本地知识库管理（资源匹配）
│   ├── dify_client.py      # Dify 知识库客户端
│   ├── profile_manager.py  # 用户画像管理器
│   ├── prerequisite_checker.py # 前置依赖检查器
│   ├── auth.py             # 用户认证核心（注册、登录、密码哈希、会话管理）
│   ├── config.py           # 配置管理
│   └── utils/
│       └── path_security.py # 路径安全工具（防路径遍历攻击）
├── tools/                  # 工具定义（@tool 装饰器）
│   ├── call_llm.py         # LLM 调用工具
│   ├── manage_profile.py   # 画像管理工具
│   ├── retrieve_knowledge.py # 知识库检索
│   ├── evaluate_plan.py    # 计划评估工具
│   └── generate_schedule.py # 日程生成工具（ICS）
├── skills/                 # Hermes Agent 技能定义
│   └── autonomous-ai-agents/learning-planner/
├── data/                   # 数据存储目录（运行时生成）
│   ├── profiles/           # 用户画像 JSON
│   ├── plans/              # 学习计划 JSON + ICS 文件
│   ├── sessions.db         # 会话数据库（SQLite）
│   ├── progress.db         # 进度数据库（SQLite）
│   ├── users.json          # 用户数据（用户名、密码哈希）
│   └── sessions.json       # 会话数据（token、user_id、过期时间）
├── kb_docs/                # 知识库文档源
│   ├── python_learning_path/ # Python 学习路径（13章）
│   └── exercises/          # 练习题（13套）
├── apps/learning-web/      # 前端（React + TypeScript）
├── main.py                 # 命令行入口
├── server.py               # 服务启动入口
└── Dify_KB_ID.txt          # Dify 知识库 ID
```

## API 端点

### 基础路径

所有 API 端点前缀：`/api/v1/`

### 认证中间件

**AuthMiddleware** 对所有 `/api/v1/` 路径进行权限校验：

| 功能 | 说明 |
|------|------|
| 拦截路径 | 所有 `/api/v1/` 开头的请求 |
| 豁免路径 | `/api/v1/auth/login`、`/api/v1/auth/register`、`/api/v1/auth/status`、`/api/v1/knowledge/*` |
| 认证方式 | 读取 HttpOnly Cookie 中的会话令牌，验证有效性 |
| 用户注入 | 验证通过后将 `user_id` 和 `username` 注入 `request.state.user` |
| 失败响应 | 返回 401 `{"error": "unauthorized", "message": "Login required"}` |

**权限校验机制**：
- 所有非豁免 API 接口自动验证当前用户身份
- 用户只能访问自己的数据（user_id 匹配校验）
- 打卡、计划调整等接口额外验证 plan_id 归属（`_plan_belongs_to_user()`）

### 1. 用户认证（Auth）

| 端点 | 方法 | 说明 |
|------|------|------|
| `/auth/login` | POST | 用户登录（返回 Cookie） |
| `/auth/register` | POST | 用户注册 |
| `/auth/logout` | POST | 用户登出（清除 Cookie） |
| `/auth/status` | GET | 获取登录状态 |

#### 请求体（POST `/auth/login`）：
```json
{
  "username": "string (≥3字符)",
  "password": "string (≥6字符)"
}
```

#### 响应体：
```json
{
  "status": "ok",
  "message": "登录成功",
  "user": {
    "user_id": "user_xxx",
    "username": "xxx"
  }
}
```

### 2. 学习对话（Learn Chat）

| 端点 | 方法 | 说明 |
|------|------|------|
| `/learn/chat` | POST | SSE 流式聊天（AgentOrchestrator 编排） |
| `/learn/plan/{plan_id}` | GET | 获取学习计划详情 |
| `/learn/plan/{plan_id}/ics` | GET | 获取计划日历文件（ICS）— 需权限校验 |
| `/learn/plan/{plan_id}/adjust` | POST | SSE 流式调整计划 |
| `/learn/session/list` | GET | 获取用户会话列表 |
| `/learn/session/{session_id}` | GET | 获取会话信息 |
| `/learn/session/{session_id}/messages` | GET | 获取会话消息历史 |
| `/learn/session/{session_id}` | DELETE | 删除会话 |
| `/learn/cleanup` | POST | 清理过期会话 |

#### `/learn/chat` - 流式聊天

**请求体**：
```json
{
  "user_id": "string (必填)",
  "message": "string (必填)",
  "session_id": "string (可选，为空时自动创建)"
}
```

**SSE 事件类型**：
| 事件 | 说明 | 数据结构 |
|------|------|---------|
| `session_created` | 新会话创建 | `{"session_id": "xxx"}` |
| `token` | 进度提示 | `{"message": "正在检查用户画像..."}` |
| `profile` | 用户画像信息 | `{"success": bool, "profile": {...}}` |
| `knowledge` | 知识库检索结果 | `{"success": bool, "results": [...], "count": int}` |
| `prerequisite` | 前置依赖检查 | `{"status": "passed/warning/failed", "details": [...], "warnings": [...]}` |
| `evaluation` | 计划评估 | `{"score": int, "issues": [...], "suggestions": [...]}` |
| `schedule` | 日历生成 | `{"success": bool, "output_path": "xxx"}` |
| `plan` | 最终计划 | 完整学习计划 JSON |
| `done` | 完成 | `{"plan_id": "xxx", "ics_path": "xxx"}` |
| `error` | 错误 | `{"message": "xxx"}` |

### 3. 用户画像（Profile）

| 端点 | 方法 | 说明 |
|------|------|------|
| `/profile/{user_id}` | GET | 获取用户画像（需权限校验） |
| `/profile/{user_id}` | POST | 更新用户画像（需权限校验） |
| `/profile/{user_id}/init` | POST | 初始化用户画像（需权限校验） |

### 4. 进度追踪（Progress）

| 端点 | 方法 | 说明 |
|------|------|------|
| `/progress/checkin` | POST | 每日打卡（需权限校验，含 plan_id 归属校验） |
| `/progress/stats/{user_id}` | GET | 获取学习统计（需权限校验） |
| `/progress/checkin/today/{user_id}` | GET | 获取今日打卡状态（需权限校验） |

#### 请求体（POST `/progress/checkin`）：
```json
{
  "user_id": "string (必填)",
  "plan_id": "string (必填)",
  "day": "integer (必填，计划天数)",
  "tasks_completed": ["string"],
  "difficulty_rating": "integer (1-5)",
  "completion_pct": "integer (0-100)",
  "time_spent_hours": "float",
  "feedback_text": "string"
}
```

### 5. 知识库（Knowledge）

| 端点 | 方法 | 说明 |
|------|------|------|
| `/knowledge/list` | GET | 获取文档列表（公开） |
| `/knowledge/search` | GET | 搜索文档（公开） |
| `/knowledge/doc/{doc_id:path}` | GET | 获取文档详情（公开，含路径安全校验） |

## 数据模型

### User（用户）

| 字段 | 类型 | 说明 |
|------|------|------|
| user_id | str | 用户唯一标识 |
| username | str | 用户名 |
| password_hash | str | PBKDF2-HMAC-SHA256 哈希值 |
| salt | str | 随机盐值（16字节） |
| created_at | float | 创建时间戳 |
| last_login | float | 最后登录时间戳 |

### Session（会话）

| 字段 | 类型 | 说明 |
|------|------|------|
| token | str | 会话令牌（256位随机数） |
| user_id | str | 用户 ID |
| username | str | 用户名 |
| created_at | float | 创建时间戳 |
| expires_at | float | 过期时间戳（30天） |

### Profile（用户画像）

| 字段 | 类型 | 说明 |
|------|------|------|
| user_id | str | 用户唯一标识 |
| goal | str | 学习目标 |
| current_level | str | 当前水平（beginner/intermediate/advanced） |
| hours_per_week | int | 每周可用学习小时 |
| preference | str | 学习偏好（video/reading/hands-on） |
| known_topics | list[str] | 已掌握知识点 |
| is_complete | bool | 画像是否完整 |

### StudyPlan（学习计划）

| 字段 | 类型 | 说明 |
|------|------|------|
| plan_id | str | 计划唯一标识 |
| goal | str | 学习目标 |
| user_id | str | 用户 ID（用于权限校验） |
| total_weeks | int | 总周数 |
| created_at | str | 创建时间 |
| milestones | list[Milestone] | 里程碑列表 |
| daily_tasks | list[DailyTask] | 每日任务列表 |
| prerequisite_check | PrerequisiteCheck | 前置依赖检查结果 |
| evaluation | PlanEvaluation | 计划评估结果 |
| ics_path | str | 日历文件路径 |
| adjusted | bool | 是否已调整 |
| adjust_reason | str | 调整原因 |

### DailyTask（每日任务）

| 字段 | 类型 | 说明 |
|------|------|------|
| day | int | 第几天 |
| title | str | 任务标题 |
| description | str | 任务描述 |
| est_hours | float | 预计时长（小时） |
| resources | list[TaskResource] | 学习资源（视频、文档、练习） |
| exercises | list[TaskExercise] | 练习题 |
| completed | bool | 是否已完成 |

### TaskResource（学习资源）

| 字段 | 类型 | 说明 |
|------|------|------|
| title | str | 资源标题 |
| url | str | 资源链接 |
| type | str | 资源类型（video/article/exercise/book/course/other） |
| description | str | 资源描述 |

## 安全机制

### 1. 认证系统

| 机制 | 实现细节 |
|------|---------|
| **密码存储** | PBKDF2-HMAC-SHA256，10万次迭代，每个用户独立随机盐值（16字节） |
| **会话令牌** | 256位随机会话令牌（`secrets.token_hex(32)`） |
| **Cookie 配置** | HttpOnly、SameSite=Lax、30天有效期 |
| **会话存储** | JSON 文件（`data/sessions.json`），包含 token、user_id、username、expires_at |
| **会话清理** | 自动清理过期会话，登录时清理其他设备会话 |
| **认证状态** | `/api/v1/auth/status` 接口支持 Mock 模式（AUTH_ENABLED=false） |

### 2. 权限校验

| 机制 | 实现细节 |
|------|---------|
| **中间件校验** | AuthMiddleware 拦截所有 `/api/v1/` 请求，验证 Cookie 有效性 |
| **用户注入** | 验证通过后将 `{"user_id", "username"}` 注入 `request.state.user` |
| **用户隔离** | 所有 API 接口校验当前用户只能访问自己的数据（user_id 匹配） |
| **计划归属校验** | 打卡、计划调整接口通过 `_plan_belongs_to_user()` 验证 plan_id 归属 |
| **依赖注入** | `get_current_user()` 和 `get_current_user_id()` 提供当前用户信息 |

### 3. 路径安全

| 机制 | 实现细节 |
|------|---------|
| **白名单验证** | plan_id、user_id、session_id、doc_id 均有正则白名单校验 |
| **路径规范化** | 使用 `os.path.basename()` 去除路径分隔符 |
| **目录限制** | 使用 `safe_join()` 确保最终路径在指定目录内 |
| **安全函数** | `safe_filename()`、`safe_plan_id()`、`safe_doc_id()` 封装安全校验 |
| **异常处理** | 非法路径返回 `PathSecurityError`，API 返回 400/403 错误 |

### 4. 消息持久化安全

| 机制 | 实现细节 |
|------|---------|
| **实时保存** | 消息生成过程中每 0.5s 或 50 token 自动保存到 SQLite |
| **空消息防护** | 收到第一个 token 时才创建 assistant 消息，防止空消息残留 |
| **中断处理** | 生成中断时不保存空消息，确保数据完整性 |

### 5. 前端安全

| 机制 | 实现细节 |
|------|---------|
| **路由守卫** | `ProtectedRoute` 组件，未登录自动跳转登录页 |
| **用户数据隔离** | localStorage key 按用户区分，不同用户数据独立存储 |
| **SSE 认证** | `credentials: 'include'` 确保 SSE 请求携带 Cookie |
| **清除对话** | 前端调用后端 DELETE API 删除会话，前后端同步删除 |

## 工具系统

### 已注册工具

| 工具名称 | 说明 | 参数 |
|----------|------|------|
| `call_llm` | 调用 LLM 生成文本 | system_prompt, user_message, response_schema, model, temperature, stream |
| `manage_profile` | 管理用户画像 | action(create/get/update/delete), user_id, **kwargs |
| `retrieve_knowledge` | 知识库检索 | query, top_k |
| `evaluate_plan` | 评估计划质量 | plan_json |
| `generate_schedule` | 生成日历文件 | plan_json, output_path, start_date |

## Agent 架构

### 混合模式设计

| 流程 | 模式 | 说明 |
|------|------|------|
| `generate_plan()` | 结构化流程 | 固定顺序：检查画像 → 检索 → 生成 → 检查 → 评估 → 导出 |
| `adjust_plan()` | ReAct 循环 | LLM 自主决定调用哪些工具，最多 5 步迭代 |

## 会话管理

### SessionDB 特性

| 功能 | 说明 |
|------|------|
| 持久化 | SQLite 存储，重启不丢失 |
| 实时保存 | 消息生成过程中定时保存（每 0.5s 或 50 个 token） |
| 清理 | 24 小时未活动自动清理 |

## 配置说明

### 环境变量

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `HERMES_ENABLED` | false | 是否启用 Hermes Agent |
| `HERMES_API_KEY` | hermes | Hermes Agent API Key |
| `HERMES_BASE_URL` | http://127.0.0.1:8642/v1 | Hermes Agent HTTP 地址 |
| `LLM_API_KEY` | 空 | 硅基流动 API Key |
| `LLM_BASE_URL` | https://api.siliconflow.cn/v1 | LLM API 地址 |
| `LLM_MODEL` | deepseek-ai/DeepSeek-V4-Flash | LLM 模型 |
| `DIFY_BASE_URL` | http://localhost/v1 | Dify API 地址 |
| `DIFY_KB_ID` | 空 | Dify 知识库 ID |
| `AUTH_ENABLED` | true | 是否启用认证系统 |
| `API_HOST` | 0.0.0.0 | 服务绑定地址 |
| `API_PORT` | 8000 | 服务端口 |

## 启动方式

### 命令行

```bash
# 启动服务
uv run uvicorn api.app:app --host 0.0.0.0 --port 8000 --reload

# 命令行工具
python main.py plan --user-id test_user --goal "学习Python"
python main.py serve --host 0.0.0.0 --port 8000
```

### API 文档

- Swagger UI：http://localhost:8000/docs
- ReDoc：http://localhost:8000/redoc

---

**最后更新**：2026-07-23