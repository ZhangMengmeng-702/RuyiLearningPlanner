# Hermes Learning Assistant — API 接口文档

> **版本**: v1.0.0  
> **基础路径**: `/api/v1`  
> **通信协议**: HTTP/HTTPS + JSON（学习对话使用 SSE 流式）  
> **前端对接**: React + TypeScript + Vite（B 负责）
> **后端实现**: FastAPI（A 负责）
> **文档维护**: C（项目整合+质量保障）

---

## 1. 总览

Hermes 学习规划助手后端采用 FastAPI 实现，前端通过 `services/api.ts` 统一调用。

### 1.1 接口清单

| 模块 | 端点 | 方法 | 说明 | 状态 |
|------|------|------|------|------|
| 健康检查 | `/health` | GET | 服务健康检查 | 🟢 已实现 |
| 学习对话 | `/learn/chat` | POST | SSE 流式聊天（AgentOrchestrator 编排） | 🟢 已实现 |
| 学习对话 | `/learn/chat/stream` | POST | 直接流式 LLM 对话（token 级推送） | 🔴 待实现 |
| 学习对话 | `/learn/chat/hermes` | POST | 直接调用 Hermes Agent（HTTP 连接） | 🔴 待实现 |
| 计划管理 | `/learn/plan/{plan_id}` | GET | 获取学习计划详情 | 🟢 已实现 |
| 计划管理 | `/learn/plan/{plan_id}/ics` | GET | 获取计划日历文件（ICS） | 🔴 待实现 |
| 计划管理 | `/learn/plan/{plan_id}/adjust` | POST | SSE 流式调整计划 | 🟢 已实现 |
| 会话管理 | `/learn/session/{session_id}` | GET | 获取会话信息 | 🔴 待实现 |
| 会话管理 | `/learn/session/{session_id}/messages` | GET | 获取会话消息历史 | 🔴 待实现 |
| 会话管理 | `/learn/session/{session_id}` | DELETE | 删除会话 | 🔴 待实现 |
| 会话管理 | `/learn/cleanup` | POST | 清理过期会话 | 🔴 待实现 |
| 用户画像 | `/profile/{user_id}` | GET | 获取用户画像 | 🟢 已实现 |
| 用户画像 | `/profile/{user_id}` | POST | 更新用户画像 | 🟢 已实现 |
| 用户画像 | `/profile/{user_id}/init` | POST | 初始化新用户画像 | 🟢 已实现 |
| 学习进度 | `/progress/checkin` | POST | 提交打卡 | 🟢 已实现 |
| 学习进度 | `/progress/stats/{user_id}` | GET | 获取进度统计 | 🟢 已实现 |

**总计**：16 个端点（含健康检查），其中 9 个已实现，7 个待实现

### 1.2 路由前缀

```
/api/v1/learn      → learn_chat.py
/api/v1/profile    → profile.py
/api/v1/progress   → progress.py
```

---

## 2. 通用约定

### 2.1 响应格式

大多数接口直接返回 JSON 对象，无统一包装。具体格式见各接口定义。

### 2.2 错误处理

- 前端通过 `resp.ok` 判断请求是否成功
- 网络错误时前端显示"连接失败：请确保后端服务已启动"
- 后端应返回合适的 HTTP 状态码（4xx/5xx）

---

## 3. 健康检查

### 3.1 GET `/health`

服务健康检查端点。

**响应**:
```json
{
  "status": "ok",
  "service": "learning-planner"
}
```

---

## 4. 用户画像接口

### 4.1 GET `/api/v1/profile/{user_id}`

获取用户画像信息。

**路径参数**:
| 参数 | 类型 | 说明 |
|------|------|------|
| user_id | string | 用户唯一标识 |

**响应（用户不存在）**:
```json
{
  "user_id": "user_001",
  "exists": false
}
```

**响应（用户存在）**:
```json
{
  "user_id": "user_001",
  "exists": true,
  "profile": {
    "goal": "转行做数据分析",
    "current_level": "beginner",
    "hours_per_week": 10,
    "preference": "hands-on",
    "known_topics": ["Excel基础", "SQL入门"],
    "is_complete": true
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| goal | string | 学习目标 |
| current_level | string | 当前水平：`beginner` / `intermediate` / `advanced` |
| hours_per_week | int | 每周可学习小时数 |
| preference | string | 学习偏好：`video` / `reading` / `hands-on` |
| known_topics | string[] | 已掌握的知识点列表 |
| is_complete | boolean | 画像是否完整（goal + level + hours + preference 都有值） |

---

### 4.2 POST `/api/v1/profile/{user_id}`

更新用户画像（不存在则自动创建）。

**路径参数**:
| 参数 | 类型 | 说明 |
|------|------|------|
| user_id | string | 用户唯一标识 |

**请求体**:
```json
{
  "goal": "转行做数据分析",
  "current_level": "beginner",
  "hours_per_week": 10,
  "preference": "hands-on",
  "known_topics": ["Excel基础", "SQL入门"]
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| goal | string | 否 | 学习目标 |
| current_level | string | 否 | 当前水平 |
| hours_per_week | int | 否 | 每周学习小时数 |
| preference | string | 否 | 学习偏好 |
| known_topics | string[] | 否 | 已掌握知识点 |

**响应**:
```json
{
  "user_id": "user_001",
  "status": "updated",
  "is_complete": true
}
```

---

### 4.3 POST `/api/v1/profile/{user_id}/init`

初始化新用户画像（创建空画像）。

**路径参数**:
| 参数 | 类型 | 说明 |
|------|------|------|
| user_id | string | 用户唯一标识 |

**响应**:
```json
{
  "user_id": "user_001",
  "status": "created"
}
```

---

## 5. 学习对话接口

### 5.1 POST `/api/v1/learn/chat` 🟢

向学习助手发送消息，获取 SSE 流式响应（AgentOrchestrator 编排）。

**请求头**:
```
Content-Type: application/json
Accept: text/event-stream
```

**请求体**:
```json
{
  "user_id": "user_001",
  "session_id": "session_abc123",
  "message": "我想学Python数据分析"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| user_id | string | 是 | 用户唯一标识 |
| message | string | 是 | 用户输入的消息 |
| session_id | string | 否 | 会话 ID，不传则新建会话 |

---

### 5.2 SSE 流式响应格式

**Content-Type**: `text/event-stream`

每行格式：
```
data: {"event": "token", "data": "正在分析..."}
data: {"event": "plan", "data": { ... StudyPlan ... }}
```

**注意**：后端输出不带 `event:` 行，`event` 字段在 JSON data 内部。前端按 `data.event` 区分事件类型。

**事件类型（共 10 种）**:

| event | 说明 | data 类型 | data 结构 |
|-------|------|-----------|-----------|
| `session_created` | 新会话创建 | object | `{"session_id": "xxx"}` |
| `token` | 进度提示/文本片段 | object | `{"message": "正在检查用户画像..."}` |
| `profile` | 用户画像信息 | object | `{"success": bool, "profile": {...}}` |
| `knowledge` | 知识库检索结果 | object | `{"success": bool, "results": [...], "count": int}` |
| `prerequisite` | 前置依赖检查 | object | `{"status": "passed/warning/failed", "details": [...], "warnings": [...]}` |
| `evaluation` | 计划评估 | object | `{"score": int, "issues": [...], "suggestions": [...]}` |
| `schedule` | 日历生成 | object | `{"success": bool, "output_path": "xxx"}` |
| `plan` | 最终计划 | object | 完整学习计划 JSON（StudyPlan） |
| `done` | 完成 | object | `{"plan_id": "xxx", "ics_path": "xxx"}` |
| `error` | 错误 | object | `{"message": "xxx"}` |

**响应示例**:
```
data: {"event":"session_created","data":{"session_id":"sess_abc123"}}

data: {"event":"token","data":{"message":"正在分析你的学习目标..."}}

data: {"event":"profile","data":{"success":true,"profile":{"goal":"学习Python数据分析",...}}}

data: {"event":"knowledge","data":{"success":true,"results":[...],"count":5}}

data: {"event":"prerequisite","data":{"status":"passed","details":[...],"warnings":[]}}

data: {"event":"evaluation","data":{"score":8,"issues":[],"suggestions":["建议增加实践项目"]}}

data: {"event":"schedule","data":{"success":true,"output_path":"data/plans/plan_xxx.ics"}}

data: {"event":"plan","data":{"plan_id":"plan_xxx","goal":"学习Python数据分析",...}}

data: {"event":"done","data":{"plan_id":"plan_xxx","ics_path":"/api/v1/learn/plan/plan_xxx/ics"}}
```

---

### 5.3 POST `/api/v1/learn/chat/stream` 🔴

直接流式 LLM 对话（token 级推送），绕过 Agent 编排，直接调用 LLM。

> **状态**: 待实现

**请求体**: 同 `/learn/chat`

**SSE 事件类型**:
| 事件 | 说明 | data 结构 |
|------|------|-----------|
| `typing` | 输入状态 | `{"status": "started/finished"}` |
| `stream_chunk` | token 内容块 | `{"content": "xxx"}` |
| `done` | 完成 | `{}` |
| `error` | 错误 | `{"message": "xxx"}` |

---

### 5.4 POST `/api/v1/learn/chat/hermes` 🔴

直接调用 Hermes Agent（HTTP 连接），绕过本地工具，使用 Hermes 的完整能力。

> **状态**: 待实现

**请求体**: 同 `/learn/chat`

**SSE 事件类型**:
| 事件 | 说明 | data 结构 |
|------|------|-----------|
| `typing` | 输入状态 | `{"status": "started/finished"}` |
| `stream_chunk` | token 内容块 | `{"content": "xxx"}` |
| `done` | 完成 | `{"provider": "hermes"}` |
| `error` | 错误 | `{"message": "xxx", "provider": "hermes"}` |

---

### 5.5 GET `/api/v1/learn/plan/{plan_id}` 🟢

获取已生成的学习计划详情。

**路径参数**:
| 参数 | 类型 | 说明 |
|------|------|------|
| plan_id | string | 计划 ID |

**响应**: `StudyPlan` 对象（见第 7 章数据模型）

---

### 5.6 GET `/api/v1/learn/plan/{plan_id}/ics` 🔴

获取计划日历文件（ICS 格式），可导入到日历应用。

> **状态**: 待实现

**路径参数**:
| 参数 | 类型 | 说明 |
|------|------|------|
| plan_id | string | 计划 ID |

**响应**: ICS 文件（`text/calendar`）

---

### 5.7 POST `/api/v1/learn/plan/{plan_id}/adjust` 🟢

根据用户反馈调整学习计划（SSE 流式），使用 ReAct 循环模式。

**路径参数**:
| 参数 | 类型 | 说明 |
|------|------|------|
| plan_id | string | 计划 ID |

**请求体**:
```json
{
  "feedback": "第2周太难了，能不能简单点？",
  "session_id": "session_abc123"
}
```

**SSE 事件**: 同 `/learn/chat` 的 10 种事件类型

---

### 5.8 GET `/api/v1/learn/session/{session_id}` 🔴

获取会话信息。

> **状态**: 待实现

**路径参数**:
| 参数 | 类型 | 说明 |
|------|------|------|
| session_id | string | 会话 ID |

**响应**:
```json
{
  "session_id": "sess_abc123",
  "user_id": "user_001",
  "created_at": "2026-07-21T10:00:00Z",
  "last_active": "2026-07-21T12:00:00Z",
  "message_count": 15,
  "compressed": false,
  "plan_id": "plan_xxx"
}
```

---

### 5.9 GET `/api/v1/learn/session/{session_id}/messages` 🔴

获取会话消息历史。

> **状态**: 待实现

**路径参数**:
| 参数 | 类型 | 说明 |
|------|------|------|
| session_id | string | 会话 ID |

**查询参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| limit | int | 否 | 返回消息数量，默认 50 |
| offset | int | 否 | 偏移量，默认 0 |

**响应**:
```json
{
  "session_id": "sess_abc123",
  "messages": [
    {
      "role": "user",
      "content": "我想学Python",
      "timestamp": "2026-07-21T10:00:00Z"
    },
    {
      "role": "assistant",
      "content": "好的，我来帮你制定学习计划...",
      "timestamp": "2026-07-21T10:00:05Z"
    }
  ],
  "total": 15
}
```

---

### 5.10 DELETE `/api/v1/learn/session/{session_id}` 🔴

删除会话及其消息历史。

> **状态**: 待实现

**路径参数**:
| 参数 | 类型 | 说明 |
|------|------|------|
| session_id | string | 会话 ID |

**响应**:
```json
{
  "status": "deleted",
  "session_id": "sess_abc123"
}
```

---

### 5.11 POST `/api/v1/learn/cleanup` 🔴

清理过期会话（24 小时未活动的会话）。

> **状态**: 待实现

**响应**:
```json
{
  "status": "ok",
  "cleaned_count": 5
}
```

---

## 6. 学习进度接口

### 6.1 POST `/api/v1/progress/checkin`

提交每日学习打卡。

**请求体**:
```json
{
  "user_id": "user_001",
  "plan_id": "plan_abc123",
  "day": 3,
  "tasks_completed": ["task_001", "task_002"],
  "difficulty_rating": 3,
  "completion_pct": 85,
  "time_spent_hours": 2.5,
  "feedback_text": "今天的内容有点难，但还是完成了"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| user_id | string | 是 | 用户 ID |
| plan_id | string | 是 | 计划 ID |
| day | int | 是 | 第几天（1-based） |
| tasks_completed | string[] | 否 | 已完成的任务 ID 列表 |
| difficulty_rating | int | 否 | 难度评分 1-5 |
| completion_pct | int | 否 | 完成度 0-100 |
| time_spent_hours | float | 否 | 学习时长（小时） |
| feedback_text | string | 否 | 文字反馈 |

**响应**:
```json
{
  "status": "ok",
  "day": 3,
  "checkin_date": "2026-07-21"
}
```

---

### 6.2 GET `/api/v1/progress/stats/{user_id}`

获取学习进度统计。

**路径参数**:
| 参数 | 类型 | 说明 |
|------|------|------|
| user_id | string | 用户 ID |

**查询参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| plan_id | string | 否 | 计划 ID，不传则返回所有计划的统计 |

**响应**:
```json
{
  "user_id": "user_001",
  "total_days": 7,
  "completed_days": 5,
  "streak": 3,
  "avg_completion_pct": 82.5,
  "avg_difficulty": 2.8,
  "total_hours": 12.5,
  "checkins": [
    {
      "day": 1,
      "date": "2026-07-15",
      "difficulty": 2,
      "completion": 100,
      "hours": 1.5,
      "feedback": "很简单"
    }
  ]
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| total_days | int | 总打卡天数 |
| completed_days | int | 高质量完成天数（完成度 ≥ 80%） |
| streak | int | 连续打卡天数 |
| avg_completion_pct | float | 平均完成率 |
| avg_difficulty | float | 平均难度评分 |
| total_hours | float | 总学习时长（小时） |
| checkins | array | 打卡记录列表（按 day 升序） |

---

## 7. 数据模型

### 7.1 StudyPlan（学习计划）

```typescript
interface StudyPlan {
  plan_id: string;
  goal: string;
  user_id: string;
  total_weeks: number;
  created_at: string;
  milestones: Milestone[];
  daily_tasks: DailyTask[];
  prerequisite_check: PrerequisiteCheck;
  evaluation?: PlanEvaluation;
  adjusted?: boolean;
  adjust_reason?: string;
}
```

### 7.2 Milestone（里程碑 / 阶段）

```typescript
interface Milestone {
  week_start: number;      // 起始周（1-based）
  week_end: number;        // 结束周
  phase: string;           // 阶段名称
  description: string;     // 阶段描述
  objectives: string[];    // 学习目标列表
  task_count: number;      // 任务数量
  difficulty: 1 | 2 | 3;   // 难度等级
}
```

### 7.3 DailyTask（每日任务）

```typescript
interface DailyTask {
  day: number;             // 第几天（1-based）
  week: number;            // 第几周
  tasks: TaskItem[];       // 该天的任务列表
}

interface TaskItem {
  id: string;              // 任务唯一 ID
  title: string;           // 任务标题
  description?: string;    // 任务描述
  est_hours: number;       // 预计耗时（小时）
  resource_url?: string;   // 学习资源链接
  resource_title?: string; // 资源标题
  completed?: boolean;     // 是否已完成（前端维护）
}
```

### 7.4 PrerequisiteCheck（前置依赖检查）

```typescript
interface PrerequisiteCheck {
  status: 'passed' | 'warning' | 'failed';
  details: {
    chapter: string;
    prerequisites: string[];
    status: string;        // 'covered' | 'missing'
  }[];
  warnings: string[];
}
```

### 7.5 PlanEvaluation（计划质量评估）

```typescript
interface PlanEvaluation {
  score: number;           // 评分 1-10
  issues: string[];        // 存在的问题
  suggestions: string[];   // 改进建议
}
```

### 7.6 ProfileData（用户画像）

```typescript
interface ProfileData {
  user_id: string;
  exists: boolean;
  profile?: {
    goal: string;
    current_level: string;  // 'beginner' | 'intermediate' | 'advanced'
    hours_per_week: number;
    preference: string;     // 'video' | 'reading' | 'hands-on'
    known_topics: string[];
    is_complete: boolean;
  };
}
```

### 7.7 ProgressStats（进度统计）

```typescript
interface ProgressStats {
  user_id: string;
  total_days: number;
  completed_days: number;
  streak: number;
  avg_completion_pct: number;
  avg_difficulty: number;
  total_hours: number;
  checkins: {
    day: number;
    date: string;
    difficulty: number;
    completion: number;
    hours: number;
    feedback: string;
  }[];
}
```

### 7.8 CheckinPayload（打卡请求）

```typescript
interface CheckinPayload {
  user_id: string;
  plan_id: string;
  day: number;
  tasks_completed: string[];
  difficulty_rating: number;   // 1-5
  completion_pct: number;      // 0-100
  time_spent_hours: number;
  feedback_text: string;
}
```

---

## 8. 前端对接要点

### 8.1 API 封装

前端在 `src/services/api.ts` 中统一封装：
- `apiGet(url)` — GET 请求
- `apiPost(url, body)` — POST 请求
- `apiPostSSE(url, body, onEvent)` — SSE 流式请求

开发环境通过 Vite 代理转发：`/api → http://127.0.0.1:8000`

### 8.2 核心 Hooks

| Hook | 说明 |
|------|------|
| `useLearningChat(userId)` | 对话逻辑 + SSE 流式处理 |
| `usePlan(planId)` | 计划数据获取 |
| `useProgress(userId, planId)` | 进度统计 + 打卡 |

### 8.3 Mock 模式

前端内置 Mock 模式（对话页复选框切换），后端不可用时前端可独立开发。

---

## 9. 存储说明

| 数据 | 存储方式 | 路径 |
|------|----------|------|
| 用户画像 | JSON 文件 | `data/profiles/{user_id}.json` |
| 学习计划 | JSON 文件 | `data/plans/{plan_id}.json` |
| 打卡记录 | SQLite | `data/progress.db` |

---

## 10. 工具系统

### 10.1 已注册工具（共 5 个）

| 工具名称 | 说明 | 参数 |
|----------|------|------|
| `call_llm` | 调用 LLM 生成文本 | system_prompt, user_message, response_schema, model, temperature, stream |
| `manage_profile` | 管理用户画像 | action(create/get/update/delete), user_id, **kwargs |
| `retrieve_knowledge` | 知识库检索 | query, top_k |
| `evaluate_plan` | 评估计划质量 | plan_json |
| `generate_schedule` | 生成日历文件 | plan_json, output_path, start_date |

### 10.2 工具调用方式

```python
from src.agent.tool_registry import registry

# 调用工具
result = registry.call_tool("call_llm", {
    "system_prompt": "你是学习规划专家",
    "user_message": "帮我生成一个Python学习计划"
})

# 获取工具列表（OpenAI format）
tools = registry.to_openai_tools(toolsets=["learning"])
```

### 10.3 @tool 装饰器

```python
from src.agent.tool_registry import tool

@tool(
    name="my_tool",
    description="工具描述",
    toolset="learning",
    emoji="🔧"
)
def my_tool(param1: str, param2: int) -> str:
    return json.dumps({"success": True, "result": ...})
```

---

## 11. Agent 架构

### 11.1 混合模式设计

| 流程 | 模式 | 说明 |
|------|------|------|
| `generate_plan()` | 结构化流程 | 固定顺序：检查画像 → 检索 → 生成 → 检查 → 评估 → 导出 |
| `adjust_plan()` | ReAct 循环 | LLM 自主决定调用哪些工具，最多 5 步迭代 |

### 11.2 结构化流程（generate_plan）

生成学习计划时使用固定的结构化流程，确保计划质量：

```
1. 检查用户画像 → 2. 知识库检索 → 3. 生成计划初稿 
    → 4. 前置依赖检查 → 5. 计划质量评估 → 6. 生成日历文件 → 7. 返回最终计划
```

### 11.3 ReAct 循环流程（adjust_plan）

调整计划时使用 ReAct 模式，LLM 自主选择工具：

```
用户反馈 → LLM 分析 → 工具选择 → 工具执行 → 结果追加 → 继续/结束
```

1. **LLM 分析**：根据当前对话历史和反馈，决定下一步行动
2. **工具选择**：输出 `{"tool_calls": [{"name": "...", "arguments": {...}}]}`
3. **工具执行**：调用对应工具，获取结果
4. **结果追加**：将工具结果追加到消息历史
5. **继续/结束**：如果 LLM 直接返回结果，结束循环（最多 5 步）

---

## 12. 会话管理

### 12.1 SessionDB 特性

| 功能 | 说明 |
|------|------|
| 持久化 | SQLite 存储，重启不丢失 |
| 压缩 | 超过 20 条消息自动生成摘要 |
| 清理 | 24 小时未活动自动清理 |
| 缓存 | 系统提示独立缓存 |

### 12.2 会话生命周期

```
创建 → 活跃 → 压缩（>20条消息） → 过期（24小时） → 清理
```

### 12.3 会话数据存储

- 数据库文件：`data/sessions.db`
- 系统提示缓存：内存缓存
- 消息压缩阈值：20 条
- 过期时间：24 小时未活动

---

## 13. 配置说明

### 13.1 环境变量（共 12 个）

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `HERMES_ENABLED` | false | 是否启用 Hermes Agent（true/false） |
| `HERMES_API_KEY` | hermes | Hermes Agent API Key |
| `HERMES_BASE_URL` | http://127.0.0.1:8642/v1 | Hermes Agent HTTP 地址 |
| `HERMES_MODEL` | hermes-agent | Hermes Agent 模型名称 |
| `LLM_API_KEY` | 空 | 硅基流动 API Key（fallback） |
| `LLM_BASE_URL` | https://api.siliconflow.cn/v1 | LLM API 地址（fallback） |
| `LLM_MODEL` | deepseek-ai/DeepSeek-V4-Flash | LLM 模型（fallback） |
| `DIFY_BASE_URL` | http://localhost/v1 | Dify API 地址 |
| `DIFY_KB_ID` | 空 | Dify 知识库 ID（从 Dify_KB_ID.txt 读取） |
| `API_HOST` | 0.0.0.0 | 服务绑定地址 |
| `API_PORT` | 8000 | 服务端口 |
| `LOG_LEVEL` | INFO | 日志级别 |

### 13.2 配置文件

- `.env`：环境变量配置文件
- `Dify_KB_ID.txt`：Dify 知识库 ID（单行文本）

### 13.3 Hermes Agent 集成说明

**架构**：
```
前端 → FastAPI (/learn/chat/hermes) → HermesClient → HTTP → Hermes Agent (127.0.0.1:8642)
```

**启用方式**：
1. 安装并启动 Hermes Agent：`hermes serve --port 8642`
2. 设置环境变量：`HERMES_ENABLED=true`
3. 配置其他 Hermes 相关变量（可选，使用默认值即可）

**回退机制**：
- 当 `HERMES_ENABLED=false` 或 Hermes Agent 不可用时，自动回退到硅基流动 LLM
- 所有 LLM 调用工具（call_llm）均支持自动回退

---

## 14. 启动方式

### 14.1 命令行

```bash
# 生成学习计划
python main.py plan --user-id test_user --goal "学习Python"

# 启动服务
python main.py serve --host 0.0.0.0 --port 8000

# 工具管理
python main.py tools list
python main.py tools call call_llm system_prompt="你好" user_message="测试"

# 用户画像管理
python main.py profile create --user-id test_user
python main.py profile update --user-id test_user --goal "学习Python" --level beginner --hours 10 --preference video
```

### 14.2 API 文档地址

启动服务后访问：
- **Swagger UI**：http://localhost:8000/docs
- **ReDoc**：http://localhost:8000/redoc

---

## 15. 相关文档

- 前端架构与接口文档：[前端架构与接口文档.md](file:///D:/ai/RuyiLearningPlanner/docs/前端架构与接口文档.md)
- 部署文档：[deployment.md](file:///D:/ai/RuyiLearningPlanner/docs/deployment.md)
- 演示用例：[demo_scripts.md](file:///D:/ai/RuyiLearningPlanner/docs/demo_scripts.md)
- 架构文档：[architecture.md](file:///D:/ai/RuyiLearningPlanner/docs/architecture.md)

---

*文档版本：v1.0.0 | 最后更新：2026-07-21 | 维护者：C*
