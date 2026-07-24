# Ruyi Learning Planner — 部署文档

> **版本**：v1.0 | **更新日期**：2026-07-21

---

## 目录

- [1. 项目整体架构概览](#1-项目整体架构概览)
- [2. 环境要求](#2-环境要求)
- [3. 本地开发环境部署步骤](#3-本地开发环境部署步骤)
- [4. 配置文件说明](#4-配置文件说明)
- [5. Hermes Agent 集成](#5-hermes-agent-集成)
- [6. 工具系统](#6-工具系统)
- [7. 会话管理](#7-会话管理)
- [8. 局域网多机协作部署方案](#8-局域网多机协作部署方案)
- [9. 常见问题排查](#9-常见问题排查)

---

## 1. 项目整体架构概览

Ruyi Learning Planner 是一个基于 LLM + RAG 的智能学习规划系统，采用前后端分离架构，由三大部分组成：

```
┌─────────────────────────────────────────────────────────────┐
│                    用户浏览器 (前端)                                  │
│  React + TypeScript + Vite + Tailwind CSS               │
│  端口：5173 (dev) / 静态文件 (prod)                    │
│  页面：对话页 / 计划看板 / 今日任务                      │
└────────────────────────────┬────────────────────────────────┘
                         │ HTTP + SSE 流式通信
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI 后端服务                            │
│  Python 3.10+ / FastAPI / Uvicorn                      │
│  端口：8000                                             │
│  核心模块：                                               │
│    ├─ 学习规划引擎 (Plan Engine)                          │
│    ├─ 用户画像管理 (Profile Manager)                       │
│    ├─ 进度追踪 (Progress Tracker)                        │
│    └─ Dify 知识库客户端 (Dify Client)                     │
└────────────────────────────┬────────────────────────────────┘
                             │ HTTP API 检索
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                    Dify 知识库服务 (RAG)                       │
│  Docker 部署 / 端口：80                                   │
│  知识库：Python 学习路径 13 章 + 练习题集               │
│  向量检索 + 语义匹配                                        │
└─────────────────────────────────────────────────────────────┘
                             │
                             ▼
                    ┌───────────────┐
                    │  LLM API    │
                    │ (硅基流动)   │
                    │ DeepSeek   │
                    └─────────────┘
```

### 技术栈汇总

| 层级 | 技术 | 版本/版本要求 | 说明 |
|------|------|------------|------|
| 前端框架 | React | 18.3+ | UI 框架 |
| 前端构建 | Vite | 5.1+ | 构建工具 |
| 样式 | Tailwind CSS | 3.4+ | CSS 框架 |
| 语言 | TypeScript | 5.3+ | 类型系统 |
| 后端框架 | FastAPI | 0.110+ | API 框架 |
| 后端运行时 | Python | >= 3.10 | 运行环境 |
| 后端服务器 | Uvicorn | 0.27+ | ASGI 服务器 |
| 包管理 | uv | 最新 | Python 依赖管理 |
| 数据库 | SQLite | 内置 | 进度/会话存储 |
| 数据存储 | JSON 文件 | - | 用户画像/计划 |
| RAG 引擎 | Dify | 最新 | 知识库检索 |
| 容器 | Docker | 20.10+ | Dify 部署用 |
| LLM | DeepSeek-V4-Flash | - | 硅基流动 API |

---

## 2. 环境要求

### 2.1 硬件要求

| 组件 | 最低配置 | 推荐配置 |
|------|--------|---------|
| CPU | 双核 2GHz+ | 四核 3GHz+ |
| 内存 | 4GB | 8GB+ |
| 磁盘 | 10GB 可用空间 | 20GB+ 可用空间 |
| 网络 | 可访问外网（调用 LLM API） | 稳定网络连接 |

### 2.2 软件要求

| 软件 | 版本要求 | 用途 |
|------|---------|------|
| Python | >= 3.10 | 后端运行环境 |
| Node.js | >= 18.0 | 前端构建工具 |
| npm | >= 9.0 | 前端包管理 |
| uv | 最新版 | Python 包管理（推荐） |
| Docker | >= 20.10 | Dify 部署（可选，如使用 Docker 方式） |
| Docker Compose | >= 2.0 | Dify 编排（可选） |
| Git | 最新版 | 版本控制 |
| Hermes Agent | 最新版 | 本地 Agent 推理引擎（可选，需另行安装） |

### 2.3 第三方服务

| 服务 | 说明 | 获取方式 |
|------|------|---------|
| 硅基流动 API Key | 用于调用 LLM（fallback） | https://siliconflow.cn/ | 注册账号获取 |
| Dify 知识库 | 用于 RAG 检索 | 本地 Docker 部署或使用云服务 |
| Hermes Agent | 本地 Agent 推理引擎（可选） | 参考 Hermes 官方文档安装 |

### 2.4 Hermes Agent 安装（可选）

Hermes Agent 是可选的本地推理引擎，启用后可提升响应速度并保护数据隐私。

**安装方式**：

1. 参考 Hermes 官方文档完成安装
2. 安装完成后启动 Hermes 服务，默认端口为 8642
3. 验证服务是否正常：

```bash
curl http://127.0.0.1:8642/v1/models
```

4. 在 `.env` 中设置 `HERMES_ENABLED=true` 即可启用

> **注意**：Hermes 不可用时系统会自动回退到硅基流动 LLM，不影响核心功能使用。

---

## 3. 本地开发环境部署步骤

### 3.1 第一部分：Dify 知识库部署

Dify 用于知识库服务，提供 RAG 检索能力。

#### 方式一：Docker 部署（推荐）

**步骤 1：克隆 Dify 官方仓库

```bash
cd D:/ai
git clone https://github.com/langgenius/dify.git
cd dify/docker
```

**步骤 2：复制环境变量配置

```bash
cp .env.example .env
```

**步骤 3：启动 Dify 服务

```bash
docker compose up -d
```

**步骤 4：验证服务

打开浏览器访问：http://localhost，初始化管理员账号。

**步骤 5：创建知识库

1. 登录 Dify 后台
2. 进入「知识库」→「创建知识库」
3. 知识库名称：`Python学习路径`
4. 上传 `kb_docs/python_learning_path/` 目录下的所有 `.md` 文件
5. 选择「下一步 → 选择索引方式：**高质量**（使用 embedding 模型）
6. 等待索引完成

**步骤 6：获取知识库 ID创建完成后，在知识库设置页面找到 `知识库 ID`，记录下来（类似 `472aa70a-3edc-46ef-8175-da3f2e817e83`）。

**步骤 7：创建 API Key

1. 进入 Dify 后台「开发者」→「API 密钥」
2. 创建新的 API 密钥
3. 记录 API Key（形如 `app-xxxxxxxxxxxxxxxxxxxxxxxx`

#### 方式二：使用 Dify 云服务

如果本地 Docker 资源有限，可直接使用 Dify 云服务：

1. 注册 https://dify.ai/
2. 创建知识库，上传文档
3. 获取知识库 ID 和 API Key

---

### 3.2 第二部分：后端服务部署

#### 步骤 1：克隆项目

```bash
cd D:/ai
git clone <your-repo-url.git RuyiLearningPlanner
cd RuyiLearningPlanner
```

#### 步骤 2：安装 Python 依赖（使用 uv）

```bash
# 安装 uv（如果未安装）
pip install uv

# 同步依赖
uv sync
```

> 如果不用 uv，也可以用 pip：

```bash
pip install fastapi uvicorn pydantic
```

#### 步骤 3：配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env
```

编辑 `.env` 文件，填入以下配置：

```env
# === Dify 知识库配置
DIFY_BASE_URL=http://localhost/v1
DIFY_KB_ID=你的知识库ID

# === LLM 配置（硅基流动）
LLM_BASE_URL=https://api.siliconflow.cn/v1
LLM_MODEL=deepseek-ai/DeepSeek-V4-Flash
```

#### 步骤 4：配置 API Key

在项目根目录创建 `key.txt` 文件，写入 Dify API Key：

```
app-xxxxxxxxxxxxxxxxxxxxxxxx
```

> **注意**：`key.txt` 已在 `.gitignore` 中，不会提交到 Git。

#### 步骤 5：启动后端服务

```bash
uv run uvicorn server:app --reload --host 0.0.0.0 --port 8000
```

或直接运行：

```bash
python server.py
```

#### 步骤 6：验证服务

打开浏览器访问：
- 健康检查：http://localhost:8000/health
- API 文档：http://localhost:8000/docs
- ReDoc：http://localhost:8000/redoc

预期返回：
```json
{"status": "ok", "service": "learning-planner"}
```

---

### 3.3 第三部分：前端部署

#### 步骤 1：进入前端目录

```bash
cd D:/ai/RuyiLearningPlanner/apps/learning-web
```

#### 步骤 2：安装依赖

```bash
npm install
```

> 如果安装缓慢，可使用国内镜像：

```bash
npm install --registry=https://registry.npmmirror.com
```

#### 步骤 3：配置 API 地址

编辑 `vite.config.ts` 中的代理配置（如需要修改后端地址）：

```typescript
server: {
  host: '0.0.0.0',
  port: 5173,
  proxy: {
    '/api': {
      target: 'http://127.0.0.1:8000',  // 后端地址
      changeOrigin: true,
    },
  },
},
```

#### 步骤 4：启动开发服务器

```bash
npm run dev
```

#### 步骤 5：验证前端

打开浏览器访问：http://localhost:5173

---

## 4. 配置文件说明

### 4.1 .env 环境变量配置

项目根目录的 `.env` 文件包含所有环境配置项：

| 变量名 | 默认值 | 必填 | 说明 |
|--------|--------|:----:|------|
| `HERMES_ENABLED` | `false` | 否 | 是否启用 Hermes Agent |
| `HERMES_API_KEY` | `hermes` | 否 | Hermes Agent API Key |
| `HERMES_BASE_URL` | `http://127.0.0.1:8642/v1` | 否 | Hermes Agent HTTP 地址 |
| `HERMES_MODEL` | `hermes-agent` | 否 | Hermes Agent 模型名称 |
| `LLM_API_KEY` | 空 | 否* | 硅基流动 API Key（fallback） |
| `LLM_BASE_URL` | `https://api.siliconflow.cn/v1` | 否 | LLM API 地址 |
| `LLM_MODEL` | `deepseek-ai/DeepSeek-V4-Flash` | 否 | LLM 模型 |
| `DIFY_BASE_URL` | `http://localhost/v1` | 否 | Dify API 地址 |
| `DIFY_KB_ID` | 空 | 否 | Dify 知识库 ID |
| `API_HOST` | `0.0.0.0` | 否 | 服务绑定地址 |
| `API_PORT` | `8000` | 否 | 服务端口 |
| `LOG_LEVEL` | `INFO` | 否 | 日志级别 |

> *`LLM_API_KEY` 也可以放在 `key.txt` 中。使用 Hermes 时 LLM 配置为 fallback，可留空。

### 4.2 key.txt API 密钥文件

项目根目录的 `key.txt` 存放敏感密钥，格式：

```
app-xxxxxxxxxxxxxxxxxxxxxxxx
```

支持的密钥按以下顺序查找：
1. `DIFY_KEY_PATH` 环境变量指定的路径
2. 当前目录的 `key.txt`
3. 项目根目录的 `key.txt`
4. 环境变量中的密钥

### 4.3 Dify_KB_ID.txt 知识库 ID 文件

（可选）可在项目根目录创建 `Dify_KB_ID.txt` 存放知识库 ID：

```
472aa70a-3edc-46ef-8175-da3f2e817e83
```

### 4.4 数据存储目录

运行时会自动生成以下数据目录：

```
data/
├── profiles/          # 用户画像 JSON 文件
├── plans/             # 学习计划 JSON + ICS 日历文件
├── sessions.db       # 会话数据库（SQLite）
└── progress.db   # 进度数据库（SQLite）
```

---

## 5. Hermes Agent 集成

### 5.1 架构概览

Hermes Agent 是本地推理引擎，集成后可大幅提升响应速度并保护数据隐私。整体调用链路如下：

```
┌─────────────┐    HTTP + SSE    ┌──────────────┐    HTTP    ┌───────────────┐
│   前端界面   │ ───────────────► │  FastAPI 后端 │ ────────► │ Hermes Agent  │
│  (React)    │ ◄─────────────── │   (Python)   │ ◄──────── │  (本地推理)    │
└─────────────┘                  └──────────────┘            └───────────────┘
                                      │
                                      │  fallback（不可用时自动降级）
                                      ▼
                                 ┌──────────┐
                                 │ 硅基流动  │
                                 │   LLM    │
                                 └──────────┘
```

**调用链路说明**：
- 前端 → FastAPI：HTTP + SSE 流式通信
- FastAPI → HermesClient：Python 客户端封装
- HermesClient → Hermes Agent：HTTP 调用本地 Agent 服务
- Hermes 不可用时：自动回退到硅基流动 LLM

### 5.2 启用方式

1. 确保 Hermes Agent 已安装并启动（默认端口 8642）
2. 在 `.env` 中配置：

```env
HERMES_ENABLED=true
HERMES_API_KEY=hermes
HERMES_BASE_URL=http://127.0.0.1:8642/v1
HERMES_MODEL=hermes-agent
```

3. 重启后端服务即可生效

### 5.3 回退机制

系统内置智能回退策略，确保服务高可用：

| 场景 | 触发条件 | 回退行为 |
|------|---------|---------|
| Hermes 未启动 | 连接失败 / 超时 | 自动使用硅基流动 LLM |
| Hermes 报错 | 服务端返回错误 | 降级到 LLM，记录日志 |
| Hermes 禁用 | `HERMES_ENABLED=false` | 直接使用 LLM |
| LLM 也不可用 | 两者均失败 | 返回友好错误提示 |

> 回退过程对用户透明，前端无感知。可通过后端日志查看当前使用的推理引擎。

---

## 6. 工具系统

### 6.1 概述

系统内置工具调用（Tool Calling）能力，Agent 可以根据用户需求动态调用工具完成复杂任务。工具通过 `@tool` 装饰器注册，支持自动参数解析和结果返回。

### 6.2 核心工具列表

| 工具名称 | 功能说明 |
|---------|---------|
| `search_knowledge_base` | 检索 Dify 知识库，获取相关学习资料 |
| `analyze_user_profile` | 分析用户画像，提取学习目标、基础、时间等信息 |
| `check_prerequisites` | 检查学习路径的前置依赖，确保计划合理性 |
| `evaluate_plan_quality` | 自评估生成的学习计划质量，打分并给出改进建议 |
| `generate_learning_schedule` | 根据用户时间安排生成具体的每日学习日程 |

### 6.3 @tool 装饰器

工具通过 `@tool` 装饰器定义，示例：

```python
@tool
def search_knowledge_base(query: str, top_k: int = 3) -> list:
    """
    从知识库中检索相关内容
    
    Args:
        query: 检索查询词
        top_k: 返回结果数量
    Returns:
        相关文档列表
    """
    # 工具实现逻辑
    ...
```

装饰器会自动：
- 解析函数签名和 docstring 生成工具描述
- 校验调用参数类型
- 处理异常并返回结构化结果
- 记录调用日志

---

## 7. 会话管理

### 7.1 SQLite 会话存储

所有对话会话持久化存储在 SQLite 数据库中（`data/sessions.db`），支持：

- 多用户会话隔离
- 历史消息回溯
- 会话状态恢复
- 断点续传

### 7.2 自动压缩机制

为避免会话过长导致 token 消耗过高，系统实现了智能压缩策略：

- **触发条件**：会话消息超过 N 轮或 token 超过阈值
- **压缩方式**：使用 LLM 对历史对话进行摘要压缩
- **保留内容**：保留关键信息（用户画像、学习目标、已确认的计划等）
- **对用户透明**：压缩过程不中断对话流程

### 7.3 自动清理策略

系统会定期清理过期会话，避免数据库膨胀：

| 清理规则 | 说明 |
|---------|------|
| 过期时间 | 超过 30 天未活跃的会话 |
| 清理时机 | 服务启动时 + 每日定时任务 |
| 数据备份 | 清理前可选备份为 JSON 文件 |
| 用户数据 | 用户画像和学习计划不受影响 |

---

## 8. 局域网多机协作部署方案

### 8.1 部署拓扑

三人分工场景：三台机器在同一局域网内协作开发

```
┌─────────────────────────────────────────────────────────────┐
│  C 的机器 (知识库)  192.168.1.103                     │
│  ┌──────────────────────────────────────────┐          │
│  │  Dify Docker (:80)                         │          │
│  │  - Python 学习路径知识库                  │          │
│  │  - 练习题知识库                        │          │
│  └──────────────────────────────────────────┘          │
└───────────────────────┬──────────────────────────────┘
                        │
         ┌──────────────┴───────────────┐
         │                                 │
         ▼                                 ▼
┌──────────────────────────┐    ┌──────────────────────────┐
│ A 的机器 (后端)         │    │ B 的机器 (前端)        │
│ 192.168.1.101          │    │ 192.168.1.102          │
│ ┌────────────────────┐    │    │ ┌────────────────────┐ │
│ │ FastAPI (:8000)  │    │    │ │ Vite dev (:5173) │ │
│ │ Hermes Agent    │◄───┼────┼─►│ → A 的 FastAPI   │ │
│ │ → C 的 Dify     │    │    │ └────────────────────┘ │
│ └────────────────────┘    │    └──────────────────────────┘
└──────────────────────────┘
```

### 8.2 机器角色分配

| 机器 | 角色 | IP | 部署服务 | 端口 |
|------|------|-----|---------|------|
| A 机器 | 后端 + Agent | 192.168.1.101 | FastAPI 后端服务 | 8000 |
| B 机器 | 前端 | 192.168.1.102 | Vite 开发服务器 | 5173 |
| C 机器 | 知识库 +  | 192.168.1.103 | Dify Docker | 80 |

### 8.3 部署步骤

#### 步骤 1：C 机器部署 Dify（知识库）

```bash
# C 机器上操作
cd ~/dify/docker
docker compose up -d
```

验证：
```bash
curl http://localhost/health
```

**获取 C 机器局域网 IP：
```bash
# Windows
ipconfig

# Linux/Mac
ifconfig
```

假设 C 机器 IP 为 `192.168.1.103`。

#### 步骤 2：A 机器部署后端

**修改 A 机器 `.env` 配置**：

```env
DIFY_BASE_URL=http://192.168.1.103/v1
DIFY_KB_ID=472aa70a-3edc-46ef-8175-da3f2e817e83
```

**启动后端**：

```bash
cd D:/ai/RuyiLearningPlanner
uv run uvicorn server:app --reload --host 0.0.0.0 --port 8000
```

验证 A 机器 IP 为 `192.168.1.101`。

#### 步骤 3：B 机器部署前端

**修改 B 机器 `vite.config.ts` 代理配置**：

```typescript
server: {
  host: '0.0.0.0',
  port: 5173,
  proxy: {
    '/api': {
      target: 'http://192.168.1.101:8000',  // 指向 A 机器后端
      changeOrigin: true,
    },
  },
},
```

**启动前端**：

```bash
cd D:/ai/RuyiLearningPlanner/apps/learning-web
npm run dev
```

#### 步骤 4：验证连通性

**B 机器 → A 机器：
```bash
curl http://192.168.1.101:8000/health
```

**A 机器 → C 机器：
```bash
curl http://192.168.1.103/health
```

**浏览器访问前端**：
http://192.168.1.102:5173

### 8.4 防火墙设置

确保三台机器的防火墙都需开放对应端口：

**Windows 防火墙开放端口：

```powershell
# 开放 8000 端口（后端）
netsh advfirewall firewall add rule name="FastAPI" dir=in action=allow protocol=TCP localport=8000

# 开放 5173 端口（前端）
netsh advfirewall firewall add rule name="Vite" dir=in action=allow protocol=TCP localport=5173

# 开放 80 端口（Dify）
netsh advfirewall firewall add rule name="Dify" dir=in action=allow protocol=TCP localport=80
```

**Linux 防火墙开放端口：

```bash
# Ubuntu/Debian
sudo ufw allow 8000/tcp
sudo ufw allow 5173/tcp
sudo ufw allow 80/tcp

# CentOS/RHEL
sudo firewall-cmd --add-port=8000/tcp --permanent
sudo firewall-cmd --add-port=5173/tcp --permanent
sudo firewall-cmd --add-port=80/tcp --permanent
sudo firewall-cmd --reload
```

---

## 9. 常见问题排查

### 9.1 端口占用问题

**症状**：启动服务时报错「Address already in use」

**排查步骤**：

1. 查找占用端口的进程：

```bash
# Windows
netstat -ano | findstr :8000

# Linux/Mac
lsof -i :8000
```

2. 杀掉占用进程：

```bash
# Windows (PID 是查找到的进程 ID
taskkill /PID <PID> /F

# Linux/Mac
kill -9 <PID>
```

3. 或修改服务端口：

后端修改 `.env`：
```env
API_PORT=8001
```

前端修改 `vite.config.ts`：
```typescript
server: {
  port: 5174,
  // ...
}
```

### 9.2 CORS 跨域问题

**症状**：前端请求后端时浏览器控制台报 CORS 错误。

**原因**：浏览器同源策略限制。

**解决方案**：

后端已配置 CORS 中间件（`api/app.py`），默认允许所有源：

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

如仍有问题：
1. 确认前端请求的 URL 和后端地址正确
2. 检查是否有反向代理修改了请求头
3. 开发环境下使用 Vite 代理避免 CORS 问题

### 9.3 连接超时问题

**症状**：请求后端或 Dify 超时。

**排查步骤**：

1. 检查服务是否正常运行：
```bash
# 检查后端
curl http://localhost:8000/health

# 检查 Dify
curl http://localhost/health
```

2. 检查防火墙设置
3. 检查 IP 地址是否正确
4. 增加超时时间（如需要）

### 9.4 Dify 知识库检索返回空

**症状**：`retrieve()` 返回空列表。

**排查步骤**：

1. 确认知识库 ID 正确
2. 确认 API Key 有效
3. 检查 Dify 后台知识库是否已索引完成
4. 降低 `score_threshold` 阈值
5. 检查 Dify 日志：
```bash
cd dify/docker
docker compose logs api
```

### 9.5 LLM API 调用失败

**症状**：LLM 返回错误或超时。

**排查步骤**：

1. 检查 API Key 是否正确
2. 检查余额是否充足
3. 检查网络是否可访问 API
4. 查看具体错误信息
5. 尝试更换模型

### 9.6 SSE 流式中断

**症状**：对话过程中断开连接。

**排查步骤**：

1. 检查后端日志
2. 检查网络稳定性
3. 确认 Nginx/反向代理的 SSE 超时配置
4. 增加心跳机制

### 9.7 前端页面白屏

**症状**：打开页面一片空白。

**排查步骤**：

1. 打开浏览器开发者工具查看控制台错误
2. 检查 `npm install` 是否成功
3. 清除浏览器缓存
4. 检查 Vite 服务器是否正常运行
5. 查看 Vite 控制台输出

### 9.8 数据库文件损坏

**症状**：SQLite 数据库报错。

**解决方案**：

删除损坏的数据库文件，重启服务会自动重建：

```bash
rm data/sessions.db
rm data/progress.db
```

> 注意：删除会丢失历史数据，请谨慎操作。

### 9.9 Hermes Agent 连接失败

**症状**：后端日志显示 Hermes 连接超时或连接被拒绝。

**排查步骤**：

1. 确认 Hermes Agent 是否已启动：
```bash
# 检查 Hermes 服务
curl http://127.0.0.1:8642/v1/models
```

2. 检查 Hermes 配置是否正确：
```env
HERMES_ENABLED=true
HERMES_BASE_URL=http://127.0.0.1:8642/v1
HERMES_API_KEY=hermes
```

3. 确认端口号是否正确（默认 8642）
4. 检查防火墙是否阻止了本地连接
5. 查看 Hermes 服务日志确认是否正常运行

> **提示**：Hermes 不可用时系统会自动回退到硅基流动 LLM，不会影响核心功能使用。

### 9.10 Hermes CLI 不可用

**症状**：命令行输入 hermes 提示「命令未找到」。

**排查步骤**：

1. 确认 Hermes 是否已正确安装
2. 检查环境变量 PATH 是否已包含 Hermes 安装目录
3. 重启终端或刷新环境变量
4. 使用完整路径执行 Hermes 命令
5. Windows 用户检查是否添加到了系统 PATH

> 如无法解决，可暂时设置 `HERMES_ENABLED=false`，使用硅基流动 LLM 继续使用系统。

---

**最后更新：2026-07-21
