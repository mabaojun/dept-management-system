# API 速查

Base URL：`http://localhost:9000/api`（本地开发与 Docker 部署一致；经 Nginx 前端访问时为 `http://localhost:8080/api`）。

## 认证

1. `POST /auth/login`，body `{ "username": "admin", "password": "..." }`，响应含 `access_token`
2. 后续请求带 header `Authorization: Bearer <access_token>`

## 常用端点

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
| 阶段总结 | `GET /reports`；手动生成 `POST /reports/generate` body `{"kind": "weekly"\|"midweek"}`（周二/周五 17:00 自动生成） | 列表全员；生成仅管理者 |
| 绩效分析 | `POST /analysis/monthly-review`，body `{month: "YYYY-MM", user_id?}` | 管理者 |
| 看板 | `GET /dashboard/summary`（`member_load` 仅 admin/manager 返回） | 管理者 |

## 约束

- 任务字段枚举：`status ∈ todo/in_progress/done/blocked`；`priority ∈ low/mid/high/urgent`
- `staff` 角色只能看 / 改自己的任务和日志，越权返回 403
- LLM 未配置 `LLM_API_KEY` 时，AI 相关功能自动降级为 Mock 演示数据
