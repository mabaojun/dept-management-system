---
name: dept-system-ops
description: 部门数字化管理终端（联通部门管理系统）的架构说明与 API 操作指南。当需要通过 API 操作系统（增删成员、指派任务、查询看板）、排查系统问题或修改系统代码时使用。
---

# 部门数字化管理终端 — 系统操作指南

## 描述

本系统是部门数字化管理终端，用于管理整个部门的工作任务、工作日志、AI 绩效分析。本技能为智能体提供系统架构认知和完整的 API 操作说明，使智能体能直接代替人工操作系统。

## 使用场景

- 需要「帮我在系统里建个任务」「把某人加入系统」「删掉某成员」等操作请求时
- 需要查询任务进度、成员负载、看板统计并汇总汇报时
- 需要排查系统故障、修改前后端代码时

## 系统架构

- 后端：Python FastAPI + SQLAlchemy 2.0，本地 SQLite（`backend/dev.db`），生产 PostgreSQL（`DATABASE_URL` 环境变量切换）
- 前端：Vue3 + TypeScript + Element Plus + ECharts
- AI：OpenAI 兼容协议（DeepSeek），未配置 `LLM_API_KEY` 时为 Mock 演示模式；配置入口「系统设置」页（仅管理员），DB 配置优先于 .env
- 部署：Docker Compose（后端发布在 9000，前端发布在 8080）；本地开发 `backend: uvicorn app.main:app --port 9000`，`frontend: npm run dev`（5174）
- 角色权限：admin（系统管理员）/ manager（部门管理者）/ staff（部门成员）

## API 操作指令

所有请求 Base URL `http://localhost:9000/api`，需先登录取 JWT：

1. `POST /auth/login`，body `{ "username": "admin", "password": "..." }`，响应含 `access_token`
2. 后续请求带 header `Authorization: Bearer <access_token>`

常用端点：

| 操作 | 方法与路径 | 权限 |
|---|---|---|
| 列成员 | `GET /users` | admin/manager |
| 建成员 | `POST /users`，body `{username, password, name, role}` | admin/manager |
| 删成员 | `DELETE /users/{id}`（名下有任务/日志/绩效时会被拒绝，需先处理） | admin |
| 重置密码 | `PUT /users/{id}/password`，body `{new_password}` | admin |
| 列任务 | `GET /tasks?status=&assignee_id=` | 登录用户 |
| 建任务 | `POST /tasks`，body `{title, description, assignee_id, priority, due_date}` | admin/manager |
| 改任务 | `PATCH /tasks/{id}`（管理者可改任意字段；负责人可改 status/description/progress，改动逐字段写入审计日志） | 管理者或负责人 |
| 任务改动记录 | `GET /tasks/{id}/changes`（逐字段 old→new 时间线） | 登录用户 |
| 删任务 | `DELETE /tasks/{id}` | admin/manager |
| 工作日志 | `GET/POST /worklogs`，AI 解析 `POST /worklogs/{id}/parse` | 登录用户 |
| 阶段总结 | `GET /reports`；手动生成 `POST /reports/generate` body `{"kind": "weekly"|"midweek"}`（周二/周五 17:00 自动生成） | 列表全员；生成仅管理者 |
| 绩效分析 | `POST /analysis/monthly-review`，body `{month: "YYYY-MM", user_id?}` | 管理者 |
| 看板 | `GET /dashboard/summary` | 管理者 |

## 约束

- 任务字段枚举：status ∈ `todo/in_progress/done/blocked`；priority ∈ `low/mid/high/urgent`
- staff 角色只能看/改自己的任务和日志，越权返回 403
- 系统所有界面文案、注释、提交信息一律使用中文
- 初始成员账号用户名为姓名全拼（如 qiujinbao、chenzhuo、mabaojun、yangmeiyuanxiao、bisixin），初始密码由管理员掌握并可在成员管理页重置

## 示例

输入：「把陈卓的等保测评任务改成已完成」
做法：`GET /tasks` 找到标题含「等保测评」的任务 id → `PATCH /tasks/{id}` body `{"status": "done"}`。
