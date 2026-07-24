# Ruyi Learning Planner — 如意学习规划助手

> Hermes Agent 驱动的个性化智能学习规划系统

## 功能特性

| 模块 | 功能 | 状态 |
|------|------|:----:|
| 🤖 **智能对话规划** | 多轮对话引导、用户画像采集、个性化学习路径生成、SSE 流式响应 | ✅ |
| 📅 **计划看板** | 周计划卡片展示、每日任务展开、学习资源链接（视频/文档/练习） | ✅ |
| ✅ **进度追踪** | 每日打卡、难度评分（1-5星）、完成度统计、连续打卡天数、自适应调整触发 | ✅ |
| 🎯 **自适应调整** | 根据完成情况自动顺延任务、调整任务量、难度自适应（偏难降难度/偏易升难度） | ✅ |
| 🔐 **用户认证** | 用户名密码登录/注册、会话管理（HttpOnly Cookie）、权限校验、用户数据隔离 | ✅ |
| 📥 **日历导出** | 学习计划导出为 .ics 文件，支持导入 Apple Calendar、Google Calendar、Outlook 等 | ✅ |
| 🗑️ **对话管理** | 历史对话持久化（SQLite）、清除对话、暂停生成（AbortController） | ✅ |
| 📚 **知识库集成** | Dify RAG 检索 + 本地知识库资源匹配（三级评分机制：关键词匹配、映射匹配、标题词匹配） | ✅ |

## 快速启动

### 环境要求

- Python 3.12+
- Node.js 18+
- Dify v1.15+（可选，用于 RAG 检索）

### 后端

```bash
cd D:/ai/RuyiLearningPlanner

# 1. 复制环境变量
cp .env.example .env
# 编辑 .env 填入 DIFY_BASE_URL、DIFY_KB_ID、LLM_API_KEY

# 2. 安装依赖（使用 uv）
uv sync

# 3. 启动服务
uv run uvicorn api.app:app --host 0.0.0.0 --port 8000 --reload
```

### 前端

```bash
cd D:/ai/RuyiLearningPlanner/apps/learning-web
npm install
npm run dev
```

访问地址：http://localhost:5173

### 首次使用

1. 打开前端页面，会自动跳转到登录页
2. 注册一个新账号（用户名 ≥3 字符，密码 ≥6 字符）
3. 在「对话规划」页面输入学习目标，例如："我想在3个月内学会Python数据分析"
4. AI 会引导你完成画像采集，然后生成个性化学习计划

## 项目结构

```
RuyiLearningPlanner/
├── api/                           # FastAPI REST API 层
│   ├── app.py                     # FastAPI 主应用（路由注册、中间件）
│   ├── deps.py                    # 依赖注入（获取当前用户）
│   ├── middlewares/               # 中间件
│   │   └── auth.py                # 认证中间件（权限校验）
│   └── v1/endpoints/              # API 端点
│       ├── auth.py                # 用户认证（登录/注册/登出）
│       ├── learn_chat.py          # 学习对话（SSE 流式）
│       ├── profile.py             # 用户画像 CRUD
│       ├── progress.py            # 进度打卡
│       └── knowledge.py           # 知识库文档
├── src/                           # 核心业务逻辑
│   ├── agent/                     # Agent 核心模块
│   │   ├── orchestrator.py        # 流程调度器（混合 ReAct）
│   │   ├── tool_registry.py       # 工具注册表（@tool 装饰器）
│   │   └── session_db.py          # 会话持久化（SQLite）
│   ├── learner/                   # 学习规划引擎
│   │   ├── models.py              # 数据模型
│   │   ├── plan_engine.py         # 计划生成引擎
│   │   ├── plan_adjuster.py       # 计划自适应调整器
│   │   └── prompts/               # LLM Prompt 模板
│   ├── knowledge_base_manager.py  # 本地知识库管理
│   ├── dify_client.py             # Dify KB 检索客户端
│   ├── profile_manager.py         # 用户画像管理器
│   ├── prerequisite_checker.py    # 前置依赖检查器
│   ├── auth.py                    # 用户认证核心（注册、登录、密码哈希）
│   └── utils/
│       └── path_security.py       # 路径安全工具（防路径遍历）
├── apps/learning-web/             # React 前端
│   ├── src/
│   │   ├── pages/                 # 页面组件
│   │   │   ├── LoginPage.tsx      # 登录/注册页面
│   │   │   ├── LearnChatPage.tsx  # 对话规划首页
│   │   │   ├── PlanViewPage.tsx   # 计划看板
│   │   │   └── TodayPage.tsx      # 今日任务+打卡
│   │   ├── components/            # UI 组件
│   │   │   ├── learn/             # 学习相关组件
│   │   │   └── layout/            # 布局组件
│   │   ├── hooks/                 # 自定义 Hooks
│   │   │   ├── useAuth.ts         # 认证状态管理
│   │   │   └── useLearningChat.ts # 对话状态管理
│   │   ├── services/              # API 服务
│   │   └── store/                 # 状态管理
│   └── ...
├── kb_docs/                       # 本地知识库文档
│   ├── python_learning_path/      # Python 学习路径（13章）
│   └── exercises/                 # 练习题（13套）
├── data/                          # 运行时数据（自动生成）
│   ├── profiles/                  # 用户画像 JSON
│   ├── plans/                     # 学习计划 JSON + ICS
│   ├── sessions.db                # 会话数据库（SQLite）
│   ├── progress.db                # 进度数据库（SQLite）
│   ├── users.json                 # 用户数据
│   └── sessions.json              # 会话数据
├── skills/                        # Hermes Agent Skill
├── tests/                         # 测试用例
└── README.md                      # 项目说明
```

## API 文档

启动服务后访问：
- Swagger UI：http://localhost:8000/docs
- ReDoc：http://localhost:8000/redoc

## 安全特性

- 🔐 **密码安全**：PBKDF2-HMAC-SHA256 哈希，10万次迭代，每个用户独立随机盐值（16字节）
- 🍪 **会话管理**：256位随机会话令牌，HttpOnly Cookie，30天有效期，自动清理过期会话
- 🚫 **权限校验**：所有 API 验证用户只能访问自己的数据，打卡接口验证 plan_id 归属
- 🛡️ **路径安全**：plan_id/user_id/session_id/doc_id 均有正则白名单校验，os.path.basename() 规范化，safe_join() 限制目录范围
- 📝 **消息持久化**：对话消息实时存储到 SQLite，每 0.5s 或 50 token 自动保存，刷新不丢失
- 🗑️ **空消息防护**：收到第一个 token 时才创建消息，防止生成中断导致空消息残留
- 🔒 **认证中间件**：AuthMiddleware 拦截所有 /api/v1/ 请求，豁免登录/注册/状态查询接口

## 知识库资源

项目内置了丰富的学习资源，每个任务都会自动匹配：
- 🎥 **视频教程**：B站（黑马程序员、尚硅谷、莫烦Python）
- 📄 **文档教程**：菜鸟教程、廖雪峰Python、官方文档
- 💻 **在线练习**：菜鸟在线练习、NumPy 100题、Pandas 100题
- 📝 **本地题库**：13章配套练习题文档

## 三人分工

| 角色 | 负责 |
|:----:|------|
| A | 后端+Agent 集成、认证系统、权限校验、安全修复、SSE 流式通信、自适应调整引擎 |
| B | 前端页面、认证状态管理、UI/UX、日历导出、会话管理、用户数据隔离 |
| C | 项目整合（前后端联调）、测试用例设计与执行、问题发现与定位、Bug修复与回归验证、知识库文档、文档编写、演示准备、安全审计 |

## 使用流程

### 首次使用
1. 打开前端页面，自动跳转到登录页
2. 注册新账号（用户名 ≥3 字符，密码 ≥6 字符）
3. 在「对话规划」页面输入学习目标，例如："我想在3个月内学会Python数据分析"
4. AI 引导完成画像采集（编程基础、每日学习时间、学习偏好）
5. 生成个性化学习计划，可查看计划看板和今日任务

### 日常使用
1. 登录后进入「对话规划」查看历史对话
2. 点击「计划看板」查看完整学习计划和学习资源链接
3. 在「今日任务」页面完成打卡，反馈难度和完成情况
4. 系统根据打卡情况自动调整后续计划

### 会话管理
- ⏸ **暂停生成**：计划生成过程中可点击暂停按钮中断
- 🗑 **清除对话**：点击清除按钮删除当前会话及其消息（前后端同步删除）
- 📥 **导出日历**：在计划看板页面下载 .ics 文件导入日历应用

## 配置说明

### 环境变量

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| DIFY_BASE_URL | http://localhost/v1 | Dify API 地址 |
| DIFY_KB_ID | 空 | Dify 知识库 ID |
| LLM_API_KEY | 空 | 硅基流动 API Key |
| LLM_BASE_URL | https://api.siliconflow.cn/v1 | LLM API 地址 |
| LLM_MODEL | deepseek-ai/DeepSeek-V4-Flash | LLM 模型 |
| AUTH_ENABLED | true | 是否启用认证系统 |

### 文件说明

- `.env`：环境变量配置
- `Dify_KB_ID.txt`：Dify 知识库 ID（单行文本）
- `data/`：运行时数据存储目录（自动创建）