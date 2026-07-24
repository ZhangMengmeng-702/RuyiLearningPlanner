# Hermes Agent 智能学习规划助手 — 完整设计方案（修订版）

> **生成日期**：2026-07-19 | **版本**：v2.0（修订版）
> **项目定位**：大模型-Agent 方向毕业设计/项目选题
> **技术栈**：Hermes Agent, 多工具调用, 自主规划, 智慧教育

---

## 目录

- [一、产品形态选择](#一产品形态选择)
- [二、系统架构设计](#二系统架构设计)
- [三、核心工作流](#三核心工作流)
- [四、各层具体实现方案](#四各层具体实现方案)
- [五、与现有项目的复用清单](#五与现有项目的复用清单)
- [六、难度评估与风险](#六难度评估与风险)
- [七、详细实现路径（Day-by-Day）](#七详细实现路径day-by-day)
- [八、三人跨电脑协作方案](#八三人跨电脑协作方案)
- [附录：v1 → v2 修订说明](#附录v1--v2-修订说明)

---

## 一、产品形态选择

基于现有技术栈（RuyiDailyStockAnalysis 的 FastAPI + React + Vite + Tailwind + Dify 知识库），最合适的形态是：

| 形态 | 分析 | 结论 |
|------|------|:----:|
| **网页（Web App）** | 股票项目已有完整 FastAPI+React+Vite 架构、Dify 有 Next.js 前端、Hermes 有 dashboard。复用现有技术栈零成本启动 | **✅ 最佳选择** |
| 小程序 | 需微信生态开发能力，与现有 Python/FastAPI 栈无交集，需从零搭建 | ❌ |
| 桌面软件 | 股票项目有 Electron 桌面端，但学习规划场景没必要桌面化，维护成本高 | ❌ |
| 插件 | Hermes 插件或 Dify 插件均可，但受限于宿主平台 UI，展示效果和交互灵活性不如独立 Web | ⚠️ 二期可选 |

> **结论：Web App。** 但注意——**Hermes Agent 是核心编排引擎，不是可选项**。

**实际实现状态**：✅ Web App 已完整实现，包含用户认证、智能对话规划、计划看板、今日任务、自适应调整、日历导出等全部核心功能。

---

## 二、系统架构设计

### 2.1 核心设计原则（修订重点）

1. **Hermes Agent 是大脑，不是装饰** — 所有学习规划的核心推理都在 Hermes Agent 中完成，FastAPI 只是传输层
2. **诚实面对"前置知识"问题** — 不承诺全自动知识图谱推理，采用「人工标注 + LLM 校验」的务实路径
3. **MVP 优先** — 3 个核心页面起步，不堆砌功能
4. **可验证的计划质量** — 每次生成计划附带评估标准，而非黑盒输出

### 2.2 整体架构

```
┌────────────────────────────────────────────────────────────┐
│                   用户浏览器（Web UI）                        │
│  React + TypeScript + Tailwind                              │
│  ┌────────────┐  ┌──────────────┐  ┌──────────────────┐    │
│  │ 对话交互界面 │  │ 计划看板      │  │ 今日任务+进度    │    │
│  └──────┬─────┘  └──────┬───────┘  └───────┬──────────┘    │
└─────────┼───────────────┼──────────────────┼───────────────┘
          │               │                  │
          │      HTTP/JSON + SSE 流式        │
          │                                   │
┌─────────▼───────────────────────────────────▼──────────────┐
│              FastAPI 传输层（薄层）                          │
│  职责：仅做 HTTP 路由、鉴权、请求格式校验、转发              │
│  不做任何 LLM 调用/KB 检索/规划推理                         │
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
│  │    - query_llm(prompt, schema)  → LLM 调用             │   │
│  │                                                         │   │
│  │  自主行为流程:                                           │   │
│  │  用户输入目标 → Agent:                                   │   │
│  │    1. 检查画像是否完整                                   │   │
│  │    2. 不完整 → 主动提问补充                               │   │
│  │    3. 调用 retrieve_knowledge 检索知识库                   │   │
│  │    4. 调用 query_llm 生成计划（含前置依赖分析）             │   │
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
                         │  HTTP
                         │
            ┌────────────┴────────────┐
            │                         │
    ┌───────▼───────┐        ┌───────▼───────┐
    │ Dify KB API    │        │ LLM API       │
    │ (localhost:80) │        │ (硅基流动)     │
    │ 知识库检索     │        │ 文本生成       │
    └───────────────┘        └───────────────┘
```

### 2.3 架构关键变化对比（v1 → v2）

| 维度 | v1（旧设计） | v2（修订版） |
|------|:-----------:|:------------:|
| Hermes Agent 角色 | 第二阶段可选增强 | **核心引擎，贯穿全程** |
| FastAPI 角色 | 编排 + 推理 | **纯传输层**，不参与推理 |
| 前置知识处理 | "自动检测依赖"（过于乐观） | **人工标注 + LLM 校验**（务实） |
| 计划质量 | 黑盒输出，无评估 | **evaluate_plan 自评 + 多选机制** |
| Web UI 页面数 | 6 个 | **3 个核心页面** |

### 2.4 模块职责

| 模块 | 职责 | 技术选型 | 备注 |
|------|------|---------|------|
| **Web UI** | 对话交互、计划展示、任务打卡 | React + TypeScript + Vite + Tailwind | 复用 stock 项目前端栈 |
| **FastAPI 传输层** | HTTP 路由、鉴权、请求转发到 Hermes Agent | FastAPI + uvicorn | **薄层，不做推理** |
| **Hermes Agent** | 画像采集、KB 检索、LLM 规划、质量评估、日程导出 | Hermes Agent + skill: learning-planner | **核心智能所在** |
| **Dify KB** | 学习内容存储与向量检索 | Dify v1.15.0 Docker | 复用现有部署 |
| **LLM** | 规划文本生成 + 结构化 JSON 输出 | DeepSeek V4 / 硅基流动 | 复用现有配置 |

### 2.5 数据存储方案

| 数据类型 | 存储方式 | 说明 | 实际实现 |
|---------|---------|------|:-------:|
| 用户数据 | JSON 文件（`data/users.json`） | 用户名、密码哈希、盐值 | ✅ |
| 用户会话 | JSON 文件（`data/sessions.json`） | 会话令牌、用户 ID、过期时间 | ✅ |
| 用户画像 | JSON 文件（`data/profiles/{user_id}.json`） | 每个用户独立文件 | ✅ |
| 学习计划 | JSON 文件（`data/plans/{plan_id}.json`） | 生成即存储，支持版本回退 | ✅ |
| 学习计划（ICS） | ICS 文件（`data/plans/{plan_id}.ics`） | 日历导出文件 | ✅ |
| 每日进度 | SQLite（`data/progress.db`） | 打卡记录 + 完成度统计 | ✅ |
| 对话历史 | SQLite（`data/sessions.db`） | Agent 多轮上下文，实时存储 | ✅ |

### 2.6 安全机制（实际实现）

| 安全机制 | 实现细节 |
|---------|---------|
| **认证系统** | PBKDF2-HMAC-SHA256 密码哈希（10万次迭代）、256位随机会话令牌、HttpOnly Cookie |
| **权限校验** | AuthMiddleware 拦截所有 API 请求，验证用户只能访问自己的数据 |
| **路径安全** | plan_id/user_id/session_id/doc_id 白名单验证 + os.path.basename() 规范化 |
| **消息持久化** | 对话消息实时存储到 SQLite（每 0.5s 或 50 token），空消息防护 |
| **前端安全** | ProtectedRoute 路由守卫、用户数据隔离、SSE 请求带 credentials |

---

## 三、核心工作流

### 3.1 首次使用

```
用户打开 Web UI → 输入: "我想学Python数据分析"
       │
       ▼
FastAPI 转发请求到 Hermes Agent
       │
       ▼
Hermes Agent (skill: learning-planner) 启动:
  Step 1: 检查画像
     → 无画像 → 主动提问:
       "你目前的编程基础是？（零基础 / 有编程经验 / 已入门Python）"
       "每天能投入多少时间？（1小时 / 2小时 / 更多）"
       "你更喜欢哪种学习方式？（视频教程 / 文档阅读 / 边做边学）"

  Step 2: 收集完整画像后 → 调用 retrieve_knowledge
     → Dify KB 检索: "Python数据分析 学习路径 零基础" TOP_K=5
     → 返回: 课程大纲章节、前置知识列表、推荐教材

  Step 3: 调用 query_llm 生成计划
     → 输入: 画像 + 知识库结果 + Plan Generation Prompt
     → 输出结构化 JSON（含前置依赖分析 + 周计划 + 日任务）

  Step 4: 调用 evaluate_plan 自评
     → 检查: 前置依赖是否覆盖、时间分配是否合理、难度梯度是否平滑
     → 返回自评分数 + 改进建议（可选重新生成）

  Step 5: 调用 generate_schedule 导出日程
     → 生成 .ics 日历文件

  Step 6: 返回 Plan JSON → FastAPI → Web UI 渲染
```

### 3.2 每日使用

```
用户打开 Web UI → 看到今日任务清单
  ├─ 勾选完成任务 → POST 进度到 Agent
  ├─ 查看学习资源 → Agent 从知识库推荐当前阶段资料
  ├─ 提问 → Agent 基于当前学习阶段 + 知识库答疑
  └─ 反馈难度 → 结构化反馈（难度评分1-5 + 完成百分比 + 可选文字）
```

### 3.3 动态调整

```
用户完成第 2 周，反馈:
  "难度评分: 4/5（偏难）"
  "完成度: 70%"
  "文字反馈: Pandas的DataFrame操作比较多，消化需要更多时间"

→ FastAPI 转发到 Hermes Agent
→ Agent 评估反馈:
   难度 4/5 + 完成度 70% = 确实偏难
→ Agent 重新规划:
   ├─ 将第 3 周原定「Pandas 进阶」推迟到第 4 周
   ├─ 第 3 周改为「Pandas 基础巩固 + 更多练习」
   ├─ 检索知识库「Pandas 入门练习」获取更多习题资源
   └─ 后续周次顺延
→ 返回更新后的 Plan JSON
```

### 3.4 反馈处理的量化策略

| 反馈维度 | 采集方式 | 处理逻辑 |
|---------|---------|---------|
| **难度评分** | 1-5 星选择 | 1-2→减速，3→保持，4-5→加速 |
| **完成度** | 百分比滑块（0-100%） | <50%→减量，50-80%→保持，>80%→可加速 |
| **时间消耗** | 实际花费小时数 | 与预计时间对比，调整后续任务估时 |
| **文字反馈** | 可选文本框 | LLM 分析语义，提取关键调整需求 |

---

## 四、各层具体实现方案

### 4.1 知识库层（Dify）

**现状**：Dify Docker 已部署运行（Nginx 端口 80，`/v1` 路由至 API:5001）
**已有知识库**：「零基础AI编程」（ID: `d45422c6-a5da-48da-9a4c-b886a82ce053`）

#### 知识库文档设计指南（重要）

为了让 RAG 检索产生高质量结果，**知识库文档必须结构化**，不能只是长篇的 Markdown 文本。

**推荐文档结构**：

```markdown
# 章节名：Python 变量与数据类型

## 元数据
- 前置知识: 无（这是第一章）
- 后续章节: Python 运算符与表达式
- 预计学习时间: 2 小时
- 难度: ⭐
- 关键词: 变量, 赋值, int, float, str, bool, type()

## 学习目标
完成本章后，你应该能：
1. 理解变量的概念和作用
2. 掌握 Python 的四种基本数据类型
3. 能用 type() 查看变量类型

## 核心内容
（正文...）

## 练习题
1. 创建一个变量存储你的名字并打印
2. ...

## 常见问题
Q: 变量名可以以数字开头吗？
A: 不可以
```

**为什么这样设计**：
| 原因 | 说明 |
|------|------|
| 元数据字段 | Dify 支持元数据过滤，可按难度/前置关系精准检索 |
| 短章节 | 避免长文档被切分后上下文碎片化 |
| 练习题独立 | 可单独检索"Python 练习题"而不混入正文 |
| 常见问题 | 直接命中用户答疑场景的检索需求 |

#### 需新建的知识库

| 知识库 | 内容 | 文件量 | 优先级 |
|--------|------|:------:|:------:|
| **Python 系统学习路径** | 从零→就业的全链路，每章按上述模板，含前置知识标注 | 10-15 个 .md 文件 | P0 |
| **编程练习题集** | 按章节分类的练习题，每题含题目+提示+参考解答 | 20-30 个 .md 文件 | P1 |
| **计算机基础补充** | 数据结构/算法/网络/操作系统简明教程 | 8-12 个 .md 文件 | P2 |

**检索方式**：纯 Python stdlib（urllib），复用 dify-knowledge-base-api 技能中已验证的调用模式：

```python
# Dify KB 检索示例（纯标准库）
import urllib.request, json

def retrieve_knowledge(query: str, top_k: int = 5) -> list[dict]:
    url = f"http://localhost/v1/datasets/{KB_ID}/retrieve"
    payload = json.dumps({
        "query": query,
        "retrieval_setting": {
            "top_k": top_k,
            "score_threshold": 0.5,
            "score_threshold_enabled": True
        }
    }).encode()
    req = urllib.request.Request(url, data=payload,
        headers={"Content-Type": "application/json",
                 "Authorization": f"Bearer {API_KEY}"})
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read()).get("records", [])
```

### 4.2 Hermes Agent（核心引擎）

#### Skill: learning-planner 设计

```yaml
# skill: learning-planner
name: learning-planner
description: "智能学习规划助手 — 采集用户画像、检索知识库、生成个性化学习计划"
tools:
  - name: retrieve_knowledge
    description: "从 Dify 知识库检索学习内容"
    params: { query: str, top_k: int, kb_filter: str | null }
  - name: manage_profile
    description: "管理用户画像（创建/读取/更新）"
    params: { action: "get"|"create"|"update", user_id: str, data: dict | null }
  - name: generate_schedule
    description: "将学习计划导出为 .ics 日历文件"
    params: { plan: dict, output_path: str }
  - name: evaluate_plan
    description: "评估学习计划质量，返回评分和改进建议"
    params: { plan: dict, profile: dict }  # returns { score, issues, suggestions }
  - name: call_llm
    description: "调用 LLM 生成文本或结构化数据"
    params: { system_prompt: str, user_prompt: str, response_schema: dict | null }

behavior:
  on_user_message:
    - 检查用户画像是否完整
    - 不完整 → 使用 call_llm 生成追问问题
    - 完整 → 执行规划流程:
        1. retrieve_knowledge(用户目标)
        2. call_llm(生成结构化计划)
        3. evaluate_plan(自评)
        4. generate_schedule(导出日程)
    - 返回 Plan JSON 给用户
```

#### Hermes Agent 的启动方式

```bash
# 方式一：直接启动一个 Hermes 会话专注于学习规划
hermes chat --skill learning-planner \
            --profile learning-assistant \
            -q "启动学习规划助手服务"

# 方式二：后台常驻模式（推荐）
# Hermes Agent 作为后台守护进程运行
# FastAPI 通过 subprocess 或 WebSocket 与 Agent 通信
# 每个用户连接对应 Agent 中的一个子会话
```

#### 前置知识依赖的处理（务实方案）

| 方案 | 说明 | 精确度 | 实现成本 |
|------|------|:------:|:--------:|
| **✅ 方案A：人工标注**（推荐） | 在每个知识库文档的元数据中写明 `前置知识` 和 `后续章节` 字段，LLM 规划时直接读取 | **高**（人工保证） | 低（写文档时顺带标注） |
| ⚠️ 方案B：LLM 自动推断 | LLM 根据章节内容自行判断前置依赖，无需标注 | 中低（可能漏判/误判） | 零 |
| ❌ 方案C：知识图谱 | 构建完整的知识依赖图 + 图遍历算法 | 高 | 极高（几周开发） |

**推荐方案 A**。知识库文档中标注前置关系是举手之劳，但能从根本上保证计划的合理性。

```json
// LLM 输出的计划中，前置依赖检查部分：
{
  "prerequisite_check": {
    "status": "passed",
    "details": [
      {"chapter": "NumPy入门", "prerequisites": ["Python基础语法"], "status": "covered"},
      {"chapter": "Pandas入门", "prerequisites": ["Python基础语法", "NumPy入门"], "status": "covered"},
      {"chapter": "数据可视化", "prerequisites": ["Pandas入门"], "status": "covered"}
    ],
    "warnings": []  // 如果有缺失的前置知识，列在这里
  }
}
```

### 4.3 Web UI 层（复用 React 栈）

**复用**：`apps/dsa-web/` 的 Vite + React + TypeScript + Tailwind + 通用组件

#### 核心页面（精简为 3 个）

| 页面 | 路由 | 功能说明 | 复杂度 |
|------|------|---------|:------:|
| **对话首页** | `/learn` | 对话交互主界面，支持流式输出，嵌入画像采集表单卡片 | ⭐⭐ |
| **计划看板** | `/learn/plan/{id}` | 周计划概览（卡片式而非甘特图）+ 每日任务展开 | ⭐⭐ |
| **今日任务+进度** | `/learn/today` | 今日任务清单 + 勾选打卡 + 进度统计（环形图） | ⭐ |

> **⚠️ 甘特图已移除**：甘特图组件开发成本高，对 MVP 价值低。改为卡片式周计划展示，每张卡片是一个里程碑，点击展开每日任务。视觉上更简洁，开发周期缩短 1 天。

#### 关键前端组件

| 组件 | 说明 | 复用来源 |
|------|------|---------|
| `LearningChat.tsx` | 对话交互（输入框 + 消息列表 + Markdown 渲染 + SSE 流式） | 新建（参考 ChatGPT UI） |
| `PlanOverview.tsx` | 周计划卡片列表 + 每日任务展开（替代甘特图） | 新建 |
| `TaskList.tsx` | 今日任务清单 + 打卡勾选 + 难度反馈表单 | 新建 |
| `ProgressChart.tsx` | 完成率环形图 + 连续打卡天数 | 新建（可用简单 SVG 自绘） |
| `FeedbackForm.tsx` | 结构化反馈组件（难度星星 + 完成度滑块 + 文字框） | 新建 |
| `Input.tsx` | 通用输入框 | ✅ 复用 dsa-web |
| `Select.tsx` | 通用下拉 | ✅ 复用 dsa-web |

### 4.4 FastAPI 传输层

```python
api/v1/endpoints/
├── learn_chat.py       # POST /chat → 转发到 Hermes Agent，SSE 流式返回
├── profile.py          # GET/PUT /profile/{uid} → 直接读写画像文件
└── progress.py         # POST /checkin, GET /progress/{uid} → 直接读写 SQLite
```

注意：FastAPI 仅做**薄传输层**，不调用 LLM、不检索知识库、不做规划推理。所有"智能"都在 Hermes Agent 中完成。

---

## 五、与现有项目的复用清单

### 5.1 直接复用（零修改）

| 现有资产 | 路径 | 复用方式 |
|---------|------|---------|
| FastAPI + uvicorn 服务 | `server.py` | 直接作为 Web 服务器 |
| CORS 中间件 | `api/middlewares/` | 直接复用 |
| 通用前端组件 | `apps/dsa-web/src/components/common/` | Input/Select/Checkbox/Button |
| Vite + Tailwind 配置 | `apps/dsa-web/vite.config.ts`, `tailwind.config.js` | 直接复制 |
| 前端构建脚本 | `apps/dsa-web/package.json` | 直接 `npm run dev` |
| Dify 知识库检索脚本 | dify-knowledge-base-api 技能 | 复用 stdlib 调用模式 |
| LLM 配置（硅基流动/DeepSeek） | `key.txt`, 环境变量 | 直接复用 |
| `src/config.py` | 配置解析 | 复用配置读取逻辑 |

### 5.2 需新增的资产（按 MVP 优先级）

| P0（必须） | 预估工时 | 说明 |
|-----------|:--------:|------|
| 知识库文档（Python 学习路径，10-15 个 .md） | 3-4 小时 | 每个章节按模板编写，含前置知识标注 |
| Hermes skill: learning-planner | 2-3 小时 | YAML 技能定义 + 工具注册 |
| 画像管理 JSON 存储 | 1 小时 | `src/profile_manager.py` |
| FastAPI 传输层聊天端点 | 2 小时 | `api/v1/endpoints/learn_chat.py`（SSE 转发） |
| 对话前端组件 | 4-5 小时 | `LearningChat.tsx`（流式消息 + Markdown） |

| P1（重要） | 预估工时 | 说明 |
|-----------|:--------:|------|
| 计划看板前端 | 3-4 小时 | `PlanOverview.tsx`（卡片式周计划） |
| 今日任务 + 进度前端 | 2-3 小时 | `TaskList.tsx` + `ProgressChart.tsx` |
| 进度追踪 SQLite | 1-2 小时 | `src/progress_tracker.py` |
| 结构化反馈组件 | 1 小时 | `FeedbackForm.tsx` |

| P2（增强） | 预估工时 | 说明 |
|-----------|:--------:|------|
| 计划质量自评（evaluate_plan） | 2 小时 | Hermes 工具 + LLM Prompt |
| .ics 日程导出 | 1 小时 | `src/schedule_exporter.py` |
| 练习题知识库上传 | 1-2 小时 | 整理并上传到 Dify |

---

## 六、难度评估与风险

### 6.1 技术难度拆解

| 模块 | 难度 | 理由 | 风险等级 |
|------|:----:|------|:--------:|
| **知识库搭建** | ⭐ 低 | Dify 上传文档即用，检索 API 已打通 | 🟢 低 |
| **FastAPI 传输层** | ⭐ 低 | 仅转发请求，不做推理，比 v1 设计更简单 | 🟢 低 |
| **用户画像管理** | ⭐ 低 | JSON CRUD，常规操作 | 🟢 低 |
| **进度追踪** | ⭐ 低 | SQLite 打卡记录，常规操作 | 🟢 低 |
| **前端对话组件** | ⭐⭐ 中 | 流式渲染 + Markdown 解析有一定复杂度 | 🟡 中 |
| **前端计划展示** | ⭐⭐ 中 | 卡片式周计划比甘特图简单，但仍需良好交互设计 | 🟡 中 |
| **LLM 规划 Prompt** | ⭐⭐⭐ 中高 | 核心难点——要让 LLM 输出结构化的、教学法合理的计划 | 🔴 **关键风险** |
| **Hermes Agent 集成** | ⭐⭐ 中 | skill 定义 + 工具注册 + FastAPI <-> Agent 通信 | 🟡 中 |
| **前置知识处理** | ⭐⭐ 中 | 方案 A（人工标注）大幅降低了难度 | 🟢 低（已降级） |
| **动态调整机制** | ⭐⭐⭐ 中高 | 量化反馈处理逻辑需要反复迭代调优 | 🔴 **关键风险** |

### 6.2 整体评估

| 维度 | 评级 |
|------|------|
| **综合实现难度** | ⭐⭐ **中等偏低**（较 v1 更务实） |
| **技术可行性** | ✅ **可行** |
| **MVP 工期** | **5-7 天**（三人团队） |
| **完整产品工期** | **2 周**（三人团队） |
| **答辩演示可用性** | ✅ Day 5 即可展示完整交互闭环 |

### 6.3 关键风险与应对

| 风险 | 影响 | 概率 | 应对措施 |
|------|:----:|:----:|---------|
| **LLM 生成的计划教学法不靠谱**（如跳过基础直接讲高级话题） | 🔴 | 中 | ① 人工标注前置知识做约束 ② evaluate_plan 自评机制 ③ 人工审核后放行 |
| **结构化 JSON 输出不稳定**（字段缺失、格式错误） | 🟡 | 高 | ① 用 JSON Schema + retry 机制 ② 后端做校验和默认值填充 ③ 前端容错渲染 |
| **Hermes Agent 与 Web UI 通信复杂** | 🟡 | 中 | MVP 阶段用 subprocess 调 Hermes CLI 简化，后期再优化为长连接 |
| **知识库内容准备耗时超预期** | 🟡 | 中 | MVP 只上传 5 个核心章节，后续增量补充 |
| **三人协作代码冲突** | 🟡 | 中 | 按模块分文件（极少冲突），每日合并一次 |

### 6.4 v1 中已识别并修正的风险

| v1 中的问题 | v2 修正 |
|------------|--------|
| Hermes Agent 是可选增强 | → Hermes Agent 是核心引擎 |
| 6 个前端页面，含甘特图 | → 3 个核心页面，卡片式计划替代甘特图 |
| 前置知识"自动检测"过于乐观 | → 人工标注 + LLM 校验 |
| 无计划质量评估 | → evaluate_plan 自评机制 |
| 反馈"太难了"模糊处理 | → 结构化量化反馈（难度评分 + 完成度 + 文字） |
| FastAPI 做 LLM 调用 | → FastAPI 仅做传输层，LLM 调用统一由 Hermes 管理 |

---

## 七、详细实现路径（Day-by-Day）

### 阶段一：基础设施（Day 1）

| 时间 | 角色 | 任务 | 产出 |
|:----:|:----:|------|------|
| 上午 | **C（知识库）** | 编写 5 个核心章节 Markdown（含前置知识标注），上传 Dify，验证检索 | Python 学习路径 KB ready |
| 上午 | **A（后端）** | 创建项目骨架、FastAPI 传输层、uvicorn 启动 | `server.py` + `api/app.py` 可启动 |
| 下午 | **A** | 画像管理 JSON 存储、进度追踪 SQLite | `src/profile_manager.py`, `progress_tracker.py` |
| 下午 | **B（前端）** | 初始化 React 项目、配置路由、Layout 框架 | `npm run dev` 可看到空白页面框架 |
| 下午 | **C** | 编写 Hermes skill: learning-planner 定义文件 | `skills/learning-planner/SKILL.md` |

**验收标准**：FastAPI 可启动，Dify 检索可返回正确结果，前端空白项目可运行。

### 阶段二：Hermes Agent 集成（Day 2）

| 时间 | 角色 | 任务 | 产出 |
|:----:|:----:|------|------|
| 上午 | **A + C** | skill 工具函数开发（retrieve_knowledge, manage_profile, call_llm） | 3 个 Python 工具函数 |
| 上午 | **B** | 对话组件基础框架（消息列表 + 输入框 + Markdown渲染） | `LearningChat.tsx`（静态版本） |
| 下午 | **A** | FastAPI SSE 端点，接收前端消息 → 转发 Hermes CLI → 流式返回 | `/api/v1/learn/chat` SSE 可通 |
| 下午 | **A + C** | Hermes Agent 会话管理（每用户一个子会话，持久化上下文） | Agent 可保持多用户状态 |
| 下午 | **B** | 前端 SSE 接入，对话组件对接实时流式输出 | 对话界面可接收流式消息 |

**验收标准**：前端输入消息 → FastAPI → Hermes Agent（模拟回复）→ 流式渲染到前端。

### 阶段三：核心 Prompt + 规划引擎（Day 3-4）

| 时间 | 角色 | 任务 | 产出 |
|:----:|:----:|------|------|
| Day 3 上午 | **A + C** | Plan Generation Prompt v1 编写 + 测试 | `prompts/plan_generation.txt` |
| Day 3 下午 | **A + C** | 画像采集 Prompt + 多轮对话引导 Prompt | `prompts/profile_collection.txt` |
| Day 3 下午 | **A** | 前置知识校验逻辑（读取文档元数据中的依赖标注） | `src/prerequisite_checker.py` |
| Day 4 上午 | **A + C** | evaluate_plan 自评 Prompt + 工具函数 | 计划可自评质量分数 |
| Day 4 下午 | **A + C** | 端到端测试：画像→检索→规划→评估 全链路 | 可在终端中跑通完整流程 |

**验收标准**：在 Hermes 终端中输入"我想学 Python 数据分析"，返回完整的结构化学习计划。

### 阶段四：前端（Day 4-5）

| 时间 | 角色 | 任务 | 产出 |
|:----:|:----:|------|------|
| Day 4 下午 | **B** | 画像采集表单卡片（嵌入对话流中） | 对话中可展示选择卡片 |
| Day 5 上午 | **B** | 计划看板页面（卡片式周计划 + 展开每日任务） | `PlanOverview.tsx` |
| Day 5 下午 | **B** | 今日任务 + 打卡 + 进度统计页面 | `TaskList.tsx` + `ProgressChart.tsx` |
| Day 5 下午 | **B** | 结构化反馈组件（难度星星 + 完成度滑块） | `FeedbackForm.tsx` |

**验收标准**：三个页面完整可用，数据从 FastAPI 获取并正确渲染。

### 阶段五：联调 + 动态调整（Day 6）

| 时间 | 角色 | 任务 | 产出 |
|:----:|:----:|------|------|
| 上午 | **A + B + C** | 全链路联调：Web UI → FastAPI → Hermes Agent → Dify KB → LLM → 返回渲染 | 完整闭环 |
| 下午 | **A + C** | 动态调整 Prompt + 量化反馈处理逻辑 | 用户反馈后可生成调整计划 |
| 下午 | **B** | 调整后的计划对比展示（原计划 vs 新计划 diff） | 用户可见计划变化 |

**验收标准**：完成一个完整的学习规划闭环（目标→画像→计划→反馈→调整）。

### 阶段六：打磨 + 文档（Day 7）

| 时间 | 角色 | 任务 | 产出 |
|:----:|:----:|------|------|
| 上午 | **C** | 文档编写（架构文档 + API 文档 + 部署说明） | `docs/` 目录 |
| 上午 | **B** | UI 润色、响应式适配、加载状态处理 | 前端体验完善 |
| 下午 | **A + B + C** | 3 条演示用例脚本编写 + 预演 | 可稳定演示的完整流程 |
| 下午 | **C** | 补充练习题知识库（可选） | 知识库内容扩充 |

---

## 八、三人跨电脑协作方案

### 8.1 分工

| 角色 | 人 | 负责模块 | 核心技能 |
|:----:|:--:|---------|---------|
| **A — 后端/Agent** | 1 人 | Hermes Agent 集成、skill 工具开发、Frontmatter、FastAPI 传输层、LLM Prompt | Python、LLM Prompt Engineering、Hermes Agent |
| **B — 前端** | 1 人 | React 页面、对话组件、计划卡片、任务清单、进度图表 | React、TypeScript、Tailwind、SSE 流式 |
| **C — 项目整合/质量保障** | 1 人 | 项目整合（前后端联调）、测试用例设计与执行、问题发现与定位、Bug修复与回归验证、知识库文档编写与上传、文档撰写、演示脚本 | Markdown、Dify、测试、文档写作、问题排查、前后端联调 |

### 8.2 协作架构

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
                    │  (部署在 C 的电脑上，    │
                    │   或一台云服务器)        │
                    │  http://192.168.x.x:80 │
                    │                        │
                    │  公共 LLM API           │
                    │  (硅基流动，各人各自    │
                    │   本地配置 key.txt)     │
                    └────────────────────────┘
```

### 8.3 协作流程

```
Day 1-3: 各自独立开发
  A: 本地跑 Dify + 开发 Agent skill
  B: 本地跑 Dify + 开发前端（mock 数据）
  C: 编写知识库文档（本地编辑，不上传到 Dify 先）

Day 4: 知识库上架
  C 将文档上传到公共 Dify 实例
  A/B 将 API 地址切换到公共 Dify

Day 5-7: 联调集成
  所有人指向同一套后端 + Dify + LLM
  A 负责代码合并和解决冲突
  B 和 C 做端到端测试和 Bug 修复
```

### 8.4 Git 策略

```bash
# 分支策略
main         ─── 稳定版本（可演示）
  └─ dev     ─── 日常开发集成分支
     ├─ feat/backend-agent   ← A
     ├─ feat/frontend-ui     ← B
     └─ feat/kb-content      ← C

# 每日惯例
git checkout dev && git pull origin dev    # 早上拉最新
git checkout feat/xxx                       # 切到特性分支开发
git add . && git commit -m "feat: xxx"     # 晚上提交
git push origin feat/xxx
# A 负责：将 feat/* 合并到 dev，解决冲突
```

### 8.5 接口约定（实际实现）

**前后端接口**（A 与 B 的契约）：

```
POST /api/v1/learn/chat
  Request:  { user_id, message, session_id? }
  Response: SSE stream, 每个 event 格式:
            event: session_created → data: {"session_id": "xxx"}
            event: token           → data: {"message": "进度提示文本"}
            event: profile         → data: {"success": bool, "profile": {...}}
            event: knowledge       → data: {"success": bool, "results": [...]}
            event: prerequisite    → data: {"status": "passed/warning/failed", ...}
            event: evaluation      → data: {"score": int, "issues": [...]}
            event: schedule        → data: {"success": bool, "output_path": "xxx"}
            event: plan            → data: { 完整学习计划 JSON }
            event: done            → data: {"plan_id": "xxx", "ics_path": "xxx"}
            event: error           → data: {"message": "xxx"}

GET /api/v1/learn/plan/{plan_id}
  Response: { plan JSON }

GET /api/v1/learn/plan/{plan_id}/ics
  Response: text/calendar 格式的 .ics 文件

POST /api/v1/learn/plan/{plan_id}/adjust
  Response: SSE stream（同 learn/chat）

GET /api/v1/learn/session/list
  Response: { sessions: [...] }

GET /api/v1/learn/session/{session_id}/messages
  Response: { messages: [...] }

DELETE /api/v1/learn/session/{session_id}
  Response: { status: "ok" }

POST /api/v1/progress/checkin
  Request:  { user_id, plan_id, day, tasks_completed[], difficulty_rating,
              completion_pct, time_spent_hours, feedback_text? }

GET /api/v1/progress/stats/{user_id}
  Response: { checkins[], stats: { total_days, completed_days, streak, avg_completion } }

GET /api/v1/progress/checkin/today/{user_id}
  Response: { checked_in: bool, ... }

POST /api/v1/auth/login
  Request:  { username, password }
  Response: { status: "ok", user: { user_id, username } } + Set-Cookie

POST /api/v1/auth/register
  Request:  { username, password }
  Response: { status: "ok", user: { user_id, username } } + Set-Cookie

POST /api/v1/auth/logout
  Response: { status: "ok" } + Clear-Cookie

GET /api/v1/auth/status
  Response: { auth_enabled: bool, logged_in: bool, user: { user_id, username } | null }
```

**后端-Hermes 接口**（A 内部实现）：

```
形式: subprocess 调用 hermes CLI
  command: hermes chat -s learning-planner -q "<JSON 格式的请求>"
  输出: stdout 流式输出，逐行 JSON

或者更稳定的方式（推荐）:
  Python 直接 import hermes-agent 的 agent 模块
  在 Python 进程中直接创建 Agent 实例
  通过 Agent.run() 方法交互
```

### 8.6 风险与应对

| 风险 | 概率 | 应对 |
|------|:----:|------|
| subprocess 调 Hermes CLI 不稳定 | 中 | MVP 先用，后期改为直接 import agent 模块 |
| 知识库内容不一致 | 中 | C 负责统一上传，其他人不直接操作 Dify |
| Git 冲突 | 低 | 按模块分文件，A（api/）, B（apps/）, C（kb_docs/）基本不重叠 |
| LLM API Key 泄露 | 🔴 | `key.txt` 加入 `.gitignore`，每人本地配，不经过 Git |
| 网络不通（公共 Dify） | 中 | 备选：每人本地 Dify，C 微信共享知识库文件 |

---

## 附录：v1 → v2 修订说明

| 问题 | v1 原设计 | v2 修订 | 修订原因 |
|------|:---------:|:-------:|---------|
| **Hermes Agent 角色** | 第二阶段可选增强 | 核心引擎，贯穿全程 | 项目名叫"Hermes Agent"，Agent 必须是核心，不是锦上添花 |
| **FastAPI 角色** | 编排 + 推理 | 纯传输层 | 避免 FastAPI 和 Hermes Agent 功能重叠、职责不清 |
| **前端页面数** | 6 个（含甘特图） | 3 个核心页面 | 甘特图开发成本高，MVP 不需要；卡片式展示更务实 |
| **前置知识处理** | "自动检测" | 人工标注 + LLM 校验 | 全自动知识图谱推理超出 MVP 范围，且不可靠 |
| **反馈机制** | "太难了"模糊处理 | 量化反馈（1-5 + 完成度%） | 模糊语义 LLM 理解偏差大，量化数据更可控 |
| **计划质量** | 无评估 | evaluate_plan 自评 | 防止 LLM 输出看似合理但教学法有问题的计划 |
| **知识库文档** | 任意 Markdown | 结构化模板（含元数据标签） | RAG 检索质量高度依赖文档结构，随意写效果差 |
| **工作量估计** | 偏乐观 | 增加了修正后的工时估算 | v1 低估了 LLM Prompt 迭代的工时 |
| **Hermes 集成路径** | 未明确 | subprocess CLI → 直接 import 模块的渐进路线 | Hermes CLI 调用有延迟问题，需考虑更稳定的集成方式 |