# Hermes Agent 智能学习规划助手 — 架构文档

> **版本**：v1.0 | **日期**：2026-07-21
> **状态**：初稿（持续完善中）

---

## 目录

- [一、整体架构概览](#一整体架构概览)
- [二、各层职责说明](#二各层职责说明)
- [三、技术选型说明](#三技术选型说明)
- [四、数据流详解](#四数据流详解)
- [五、模块划分与文件结构](#五模块划分与文件结构)
- [六、关键接口约定](#六关键接口约定)
- [七、数据存储方案](#七数据存储方案)
- [八、三人协作架构](#八三人协作架构)

---

## 一、整体架构概览

### 1.1 架构分层图

```
┌────────────────────────────────────────────────────────────┐
│                     用户浏览器（Web UI）                      │
│  React + TypeScript + Tailwind CSS + Vite                   │
│  ┌────────────┐  ┌──────────────┐  ┌──────────────────┐    │
│  │ 对话交互界面 │  │ 计划看板      │  │ 今日任务+进度    │    │
│  └──────┬─────┘  └──────┬───────┘  └───────┬──────────┘    │
└─────────┼───────────────┼──────────────────┼───────────────┘
          │               │                  │
          │      HTTP/JSON + SSE 流式        │
          │                                   │
┌─────────▼───────────────────────────────────▼──────────────┐
│              FastAPI 传输层（薄层）                          │
│  职责：HTTP 路由、CORS、请求格式校验、转发                    │
│  不做任何 LLM 调用/KB 检索/规划推理                          │
│  ┌────────────────────┐  ┌──────────────────────────────┐  │
│  │ /api/v1/learn/*    │  │ Agent 交互代理                │  │
│  │ → 把请求转为 JSON  │  │ → 调用 Hermes Agent CLI      │  │
│  │ → 转发给 Hermes    │  │ → 流式返回结果               │  │
│  └────────────────────┘  └──────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │  subprocess / WebSocket
                         │
┌────────────────────────▼────────────────────────────────────┐
│              Hermes Agent（核心推理引擎）                     │
│                                                              │
│  启动时加载 skill: learning-planner                          │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  skill: learning-planner                              │   │
│  │  工具:                                                 │   │
│  │    - retrieve_knowledge(query)  → Dify KB API         │   │
│  │    - manage_profile(action, data) → 画像 CRUD          │   │
│  │    - generate_schedule(plan)    → .ics 导出            │   │
│  │    - evaluate_plan(plan)        → 计划质量自评          │   │
│  │    - call_llm(prompt, schema)  → LLM 调用             │   │
│  │                                                         │   │
│  │  自主行为流程:                                           │   │
│  │  用户输入目标 → Agent:                                   │   │
│  │    1. 检查画像是否完整                                   │   │
│  │    2. 不完整 → 主动提问补充                               │   │
│  │    3. 调用 retrieve_knowledge 检索知识库                   │   │
│  │    4. 调用 call_llm 生成计划（含前置依赖分析）             │   │
│  │    5. 调用 evaluate_plan 自评质量                          │   │
│  │    6. 调用 generate_schedule 导出日程                      │   │
│  │    7. 返回结果                                           │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  持久的 Agent 会话:                                          │
│    每个用户对应一个 Hermes 会话（或子会话）                    │
│    会话保持用户画像 + 当前计划 + 学习进度上下文               │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │  HTTP API
                         │
            ┌────────────┴────────────┐
            │                         │
    ┌───────▼───────┐        ┌───────▼───────┐
    │ Dify KB API    │        │ LLM API       │
    │ (知识库检索)   │        │ (文本生成)     │
    └───────────────┘        └───────────────┘
```

### 1.2 核心设计原则

| 原则 | 说明 |
|------|------|
| **Hermes Agent 是大脑** | 所有学习规划的核心推理都在 Hermes Agent 中完成，FastAPI 只是传输层 |
| **薄传输层** | FastAPI 仅做 HTTP 协议转换和转发，不参与推理 |
| **人工标注 + LLM 校验** | 前置知识依赖采用人工标注（KB 文档元数据）+ LLM 校验的务实路径 |
| **可验证的计划质量** | 每次生成计划附带 evaluate_plan 自评，而非黑盒输出 |
| **MVP 优先** | 3 个核心页面起步，功能按需迭代 |

---

## 二、各层职责说明

### 2.1 Web UI 层（B 负责）

**职责**：用户交互、数据展示、状态管理

**核心页面**：
| 页面 | 路由 | 功能 |
|------|------|------|
| 对话首页 | `/learn` | 对话交互主界面，支持流式输出，嵌入画像采集表单 |
| 计划看板 | `/learn/plan/{id}` | 周计划概览（卡片式）+ 每日任务展开 |
| 今日任务 | `/learn/today` | 今日任务清单 + 打卡 + 进度统计 |

**核心组件**：
- `LearningChat.tsx` — 对话组件（消息列表 + 输入框 + Markdown 渲染 + SSE 流式）
- `PlanOverview.tsx` — 计划看板（里程碑卡片 + 任务展开）
- `TaskList.tsx` — 任务清单 + 打卡 + 反馈表单
- `ProgressChart.tsx` — 进度可视化（环形图）
- `FeedbackForm.tsx` — 结构化反馈组件

### 2.2 FastAPI 传输层（A 负责）

**职责**：
- HTTP 路由注册
- CORS 跨域处理
- 请求参数校验
- 将前端请求转发给 Hermes Agent
- 将 Hermes 的输出以 SSE 流式返回前端
- 直接读写画像/进度数据（不经过 Agent）

**端点列表**：
| 端点 | 方法 | 说明 |
|------|:----:|------|
| `/api/v1/learn/chat` | POST | 对话接口，SSE 流式返回 |
| `/api/v1/learn/plan/{plan_id}` | GET | 获取学习计划详情 |
| `/api/v1/learn/plan/{plan_id}/adjust` | POST | 调整学习计划 |
| `/api/v1/profile/{user_id}` | GET | 获取用户画像 |
| `/api/v1/profile/{user_id}` | PUT | 更新用户画像 |
| `/api/v1/progress/checkin` | POST | 打卡 |
| `/api/v1/progress/{user_id}` | GET | 获取进度统计 |

### 2.3 Hermes Agent 层（A 负责）

**职责**：核心智能推理

**核心 Skill**：`learning-planner`

**工具列表**：
| 工具 | 功能 |
|------|------|
| `retrieve_knowledge` | 从 Dify 知识库检索学习内容 |
| `manage_profile` | 管理用户画像（创建/读取/更新） |
| `call_llm` | 调用 LLM 生成文本或结构化数据 |
| `evaluate_plan` | 评估学习计划质量 |
| `generate_schedule` | 导出 .ics 日历文件 |

**核心 Prompt 文件**：
- `plan_generation.txt` — 计划生成 Prompt
- `profile_collection.txt` — 画像采集 Prompt
- `plan_adjustment.txt` — 计划调整 Prompt

### 2.4 知识库层（C 负责）

**职责**：学习内容存储与向量检索

**知识库列表**：
| 知识库 | 内容 | 文件量 | 优先级 |
|--------|------|:------:|:------:|
| Python 系统学习路径 | 从零到就业的全链路，每章含前置知识标注 | 13 个 .md | P0 |
| 编程练习题集 | 按章节分类的练习题 + 解答 | 10 个 .md | P1 |
| 计算机基础补充 | 数据结构/算法/网络/操作系统简明教程 | 8-12 个 | P2 |

**文档结构**：每个 Markdown 文件包含 frontmatter 元数据（前置知识、后续章节、难度、关键词等）

---

## 三、技术选型说明

### 3.1 前端技术栈

| 技术 | 选型 | 说明 |
|------|------|------|
| 框架 | React 18 | 复用现有项目经验 |
| 语言 | TypeScript | 类型安全，减少 Bug |
| 构建工具 | Vite | 热更新快，开发体验好 |
| 样式 | Tailwind CSS | 原子化 CSS，开发效率高 |
| 状态管理 | React Hooks (useState/useContext) | MVP 阶段够用 |
| Markdown 渲染 | react-markdown | 支持代码高亮 |
| 流式通信 | EventSource / fetch SSE | 接收后端流式消息 |

### 3.2 后端技术栈

| 技术 | 选型 | 说明 |
|------|------|------|
| Web 框架 | FastAPI | 异步、高性能、自动生成文档 |
| 服务器 | Uvicorn | ASGI 服务器 |
| Agent 框架 | Hermes Agent | 核心推理引擎 |
| HTTP 客户端 | urllib (stdlib) | 纯标准库，减少依赖 |
| 数据存储 | JSON + SQLite | 轻量级，MVP 阶段足够 |

### 3.3 基础设施

| 组件 | 选型 | 说明 |
|------|------|------|
| 知识库 | Dify v1.15.0 | 向量检索 + RAG |
| LLM | 硅基流动 / DeepSeek V4 | 复用现有配置 |
| 版本控制 | Git | 三人协作 |
| 代码托管 | GitHub / Gitee | 远程仓库 |

---

## 四、数据流详解

### 4.1 首次使用流程

```
用户打开 Web UI
    │
    ▼
输入: "我想学Python数据分析"
    │
    ▼
FastAPI 接收请求 → 转发到 Hermes Agent
    │
    ▼
Hermes Agent (skill: learning-planner):
    │
    ├─ Step 1: 检查画像
    │     → 无画像 → 主动提问（多轮采集）
    │     → 调用 manage_profile 创建画像
    │
    ├─ Step 2: 检索知识库
    │     → 调用 retrieve_knowledge("Python数据分析 学习路径 零基础")
    │     → Dify KB 返回 TOP_K=5 相关章节
    │
    ├─ Step 3: 生成计划
    │     → 调用 call_llm(画像 + 知识库结果 + Plan Generation Prompt)
    │     → LLM 返回结构化 Plan JSON
    │
    ├─ Step 4: 质量自评
    │     → 调用 evaluate_plan(plan, profile)
    │     → 检查：前置依赖完整性、时间分配合理性、难度梯度平滑度
    │     → 返回评分 + 改进建议
    │
    ├─ Step 5: 导出日程（可选）
    │     → 调用 generate_schedule(plan)
    │     → 生成 .ics 日历文件
    │
    └─ Step 6: 返回 Plan JSON
            │
            ▼
    FastAPI → SSE 流式 → 前端渲染
```

### 4.2 每日使用流程

```
用户打开 Web UI → 看到今日任务清单
    │
    ├─ 勾选完成任务 → POST /api/v1/progress/checkin → SQLite 更新
    │
    ├─ 点击学习资源 → Agent 从 KB 推荐当前阶段资料
    │
    ├─ 提问 → Agent 基于当前学习阶段 + 知识库答疑
    │
    └─ 反馈难度 → 结构化反馈（难度1-5 + 完成度% + 文字）
              │
              ▼
         Hermes Agent 评估 → 重新规划后续计划
              │
              ▼
         返回调整后的 Plan JSON
```

### 4.3 动态调整流程

```
用户反馈:
  - 难度评分: 4/5（偏难）
  - 完成度: 70%
  - 文字反馈: Pandas的DataFrame操作比较多
    │
    ▼
FastAPI → Hermes Agent
    │
    ▼
Agent 处理:
  1. 评估反馈（量化 + 语义分析）
  2. 确定调整策略（减速 + 增加练习）
  3. 调用 retrieve_knowledge 获取更多习题资源
  4. 调用 call_llm 重新规划后续周次
  5. evaluate_plan 自评新计划
  6. 返回调整后的 Plan JSON
```

---

## 五、模块划分与文件结构

### 5.1 完整目录结构

```
D:\ai\RuyiLearningPlanner\
├── server.py                        # uvicorn 启动入口
├── pyproject.toml                   # Python 项目配置
├── README.md                        # 项目说明
├── .gitignore                       # Git 忽略规则
│
├── api/                             # FastAPI 传输层
│   ├── app.py                       # FastAPI 应用 + CORS + 路由注册
│   ├── deps.py                      # 依赖注入
│   └── v1/
│       └── endpoints/
│           ├── __init__.py
│           ├── learn_chat.py        # SSE 流式聊天端点
│           ├── profile.py           # 画像 CRUD
│           └── progress.py          # 进度 CRUD
│
├── src/                             # 后端核心模块
│   ├── config.py                    # 配置解析
│   ├── dify_client.py               # Dify KB 检索客户端
│   ├── profile_manager.py           # 画像管理（JSON）
│   ├── progress_tracker.py          # 进度追踪（SQLite）
│   ├── prerequisite_checker.py      # 前置依赖检查器
│   └── schedule_exporter.py         # .ics 日程导出
│
├── skills/                          # Hermes Agent Skills
│   └── learning-planner/
│       ├── SKILL.md                 # skill 定义
│       ├── tools/
│       │   ├── retrieve_knowledge.py
│       │   ├── manage_profile.py
│       │   ├── call_llm.py
│       │   ├── evaluate_plan.py
│       │   └── generate_schedule.py
│       └── prompts/
│           ├── plan_generation.txt
│           ├── plan_adjustment.txt
│           └── profile_collection.txt
│
├── kb_docs/                         # 知识库源文件（版本管理）
│   ├── python_learning_path/        # Python 学习路径（13章）
│   ├── exercises/                   # 练习题集
│   └── computer_basics/             # 计算机基础补充
│
├── tests/                           # 测试套件
│   ├── test_dify_client.py
│   ├── test_kb_retrieval.py
│   ├── test_profile_manager.py
│   ├── test_api_learn.py
│   └── test_full_flow.py
│
├── docs/                            # 项目文档
│   ├── architecture.md              # 架构文档（本文档）
│   ├── api_spec.md                  # API 接口文档
│   ├── deployment.md                # 部署说明
│   └── demo_scripts.md              # 演示用例脚本
│
├── data/                            # 运行时数据
│   ├── profiles/                    # 用户画像 JSON
│   ├── plans/                       # 学习计划 JSON
│   └── progress.db                  # 进度 SQLite
│
└── apps/
    └── learning-web/                # 前端 React 应用
        ├── index.html
        ├── package.json
        ├── vite.config.ts
        ├── tailwind.config.js
        ├── tsconfig.json
        └── src/
            ├── main.tsx
            ├── App.tsx
            ├── pages/
            ├── components/
            ├── hooks/
            ├── services/
            └── types/
```

### 5.2 所有权划分

| 模块 | 负责人 | 说明 |
|------|:------:|------|
| `api/` + `src/` + `skills/` | A | 后端 + Agent |
| `apps/learning-web/` | B | 前端 |
| `kb_docs/` + `tests/` + `docs/` + `README.md` + `.gitignore` | C | 内容 + 质量 + 文档 |

---

## 六、关键接口约定

### 6.1 SSE 消息格式

```
服务端 → 客户端 (text/event-stream):

事件类型:
  event: token
  data: "这是LLM生成的文本片段..."
  
  event: plan
  data: { "plan_id": "xxx", "total_weeks": 12, "milestones": [...], ... }
  
  event: done  
  data: { "session_id": "session_xxx" }
  
  event: error
  data: { "code": "LLM_TIMEOUT", "message": "模型响应超时，请重试" }
```

### 6.2 Plan JSON Schema

完整定义见 [api_spec.md](./api_spec.md)

核心结构：
```typescript
interface StudyPlan {
  plan_id: string;
  goal: string;
  created_at: string;
  total_weeks: number;
  milestones: Milestone[];
  daily_tasks: DailyTask[];
  prerequisite_check: { status, details, warnings };
  evaluation?: { score, issues, suggestions };
}
```

---

## 七、数据存储方案

| 数据类型 | 存储方式 | 路径 | 说明 |
|---------|---------|------|------|
| 用户画像 | JSON 文件 | `data/profiles/{user_id}.json` | 每个用户独立文件 |
| 学习计划 | JSON 文件 | `data/plans/{plan_id}.json` | 生成即存储，支持版本回退 |
| 每日进度 | SQLite | `data/progress.db` | 打卡记录 + 完成度统计 |
| 对话历史 | Hermes 会话 | Agent 内部管理 | 多轮上下文 |
| 知识库内容 | Dify | Dify 内部存储 | 向量检索 |

---

## 八、三人协作架构

### 8.1 跨电脑拓扑

```
                             Git 远程仓库
                           (GitHub / Gitee)
                         ┌──────┼──────┐
                         │      │      │
                     A 的电脑  B 的电脑  C 的电脑
                    (后端+Agent) (前端)   (知识库+文档)
                         │             │
                         └──────┬──────┘
                                │
                    ┌───────────▼───────────┐
                    │  公共 Dify 实例         │
                    │  (部署在 C 的电脑上)     │
                    │  http://192.168.x.x:80 │
                    │                        │
                    │  公共 LLM API           │
                    │  (硅基流动，各自本地    │
                    │   配置 key.txt)         │
                    └────────────────────────┘
```

### 8.2 Git 分支策略

```
main (保护分支)
  └─ dev (日常集成分支)
        ├─ feat/backend-agent    ← A
        ├─ feat/frontend-ui      ← B
        └─ feat/kb-content       ← C
```

### 8.3 关键交接点

| 交接 | 内容 | 时间 |
|------|------|:----:|
| C → A | Dify KB ID、API Key、Base URL | Day 1 下午 |
| A → B | SSE 消息格式 + Plan JSON Schema | Day 2 下午 |
| C → A+B | Bug List + 测试反馈 | 每天持续 |

---

> **本文档状态**：初稿，后续根据开发进度持续更新
