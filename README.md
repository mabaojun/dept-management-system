# 部门数字化管理终端

部门工作任务、工作日志与 AI 绩效分析一体化管理系统（内部系统）。

## 功能模块

| 模块 | 说明 |
|---|---|
| 数据看板 | 任务状态分布、近 14 天完成趋势、成员任务负载、最近未完成任务 |
| 任务管理 | 建任务 / 指派 / 进度跟进 / 状态流转（待开始、进行中、已完成、受阻），全量字段改动审计 |
| 工作日志 | 成员提交日志，AI 自动解析任务关联与工时 |
| AI 绩效分析 | 月度绩效参考意见（OpenAI 兼容协议，默认 DeepSeek；未配 Key 时降级 Mock 演示） |
| 阶段总结 | 每周二 / 周五 17:00 自动生成，支持手动触发 |
| 成员管理 | 账号增删、密码重置、角色分配 |
| 系统设置 | LLM 接入配置（仅管理员，DB 配置优先于 .env） |

## 技术栈

- 后端：Python FastAPI + SQLAlchemy 2.0，本地 SQLite（`backend/dev.db`），生产 PostgreSQL（`DATABASE_URL` 切换）
- 前端：Vue3 + TypeScript + Element Plus + ECharts
- AI：OpenAI 兼容协议（DeepSeek / Qwen / GLM 均可）
- 部署：Docker Compose（后端 + Nginx 前端）

## 端口说明（重要）

宿主机 8000 / 5173 已被其他服务占用，本项目统一使用以下端口：

| 服务 | 端口 | 说明 |
|---|---|---|
| 后端 API | **9000** | 本地开发 `http://localhost:9000/api`；Docker 部署同样发布到宿主机 9000 |
| 前端开发服务器 | **5174** | `npm run dev`，代理 `/api` 到本地 9000 |
| 前端（Docker/Nginx） | **8080** | `docker compose up` 后访问 `http://localhost:8080`，Nginx 反代 `/api` 到容器内后端 9000 |

## 快速开始（本地开发）

```bash
# 后端（默认 SQLite，首次启动自动建表并创建初始管理员）
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp ../.env.example .env   # 按需修改，务必更换 SECRET_KEY
uvicorn app.main:app --port 9000

# 前端（另开终端）
cd frontend
npm install
npm run dev   # http://localhost:5174
```

初始管理员账号：`admin`（密码由 `ADMIN_PASSWORD` 配置，默认 `admin123`，上线务必修改）。
初始成员账号用户名为姓名全拼（如 qiujinbao、chenzhuo），初始密码由管理员掌握并可在成员管理页重置。

## Docker 部署

```bash
cp .env.example .env   # 配置 DATABASE_URL（生产建议 PostgreSQL）、SECRET_KEY、LLM_API_KEY
docker compose up -d --build
```

- 访问入口：`http://localhost:8080`（前端），API 直连：`http://localhost:9000/api`
- 数据持久化：Docker 卷 `backend-data`（SQLite 时为 `/data/dev.db`）

## 角色权限

- `admin`（系统管理员）/ `manager`（部门管理者）：管理成员、任务、看板、绩效分析
- `staff`（部门成员）：仅能查看和操作自己的任务与日志
- 看板中的「成员任务负载」仅管理侧（admin/manager）可见

## 目录结构

```
├── backend/            # FastAPI 后端（app/api 接口层、app/services 业务层、app/models 数据模型）
├── frontend/           # Vue3 前端（src/views 页面、src/api 接口封装）
├── docker-compose.yml  # 编排：backend(9000) + frontend/nginx(8080)
├── .env.example        # 环境变量样例
└── docs/API.md         # API 速查
```

## 更多文档

- [API 速查](docs/API.md)
