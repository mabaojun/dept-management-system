---
name: period-report-fetch
description: 阶段工作总结抓取推送。从联通部门管理系统（青青草原牛马管理系统）抓取每周二/周五 17:00 自动生成的阶段任务进展简报，并整理推送给用户。当用户要求「抓取阶段总结」「推送最新周报」「看看本周任务进展报告」或由定时任务在每周二、周五 17 点后触发时使用。
---

# 阶段工作总结抓取推送

## 描述

系统后端内置定时器，每周二 17:00 生成「期中简报」（midweek，覆盖上周六至今）、每周五 17:00 生成「本周周报」（weekly，覆盖本周一至今）。报告结合周期内全部任务快照与逐字段改动日志，由 AI 生成总结、亮点与风险。本技能负责从系统 API 抓取报告并推送给用户。

## 抓取步骤

1. 登录获取 token（Base URL `http://localhost:9000/api`）：

   ```
   POST /auth/login  body {"username": "...", "password": "..."}
   ```

   响应中的 `access_token` 用于后续请求 header `Authorization: Bearer <token>`。

2. 拉取报告列表（全员可访问，按生成时间倒序）：

   ```
   GET /reports
   ```

3. 取列表第一份（最新）报告，按以下格式推送给用户：

   - **标题**：`📋 阶段任务进展（{kind 为 weekly 时"本周周报"，midweek 时"期中简报"}）{period_start} ~ {period_end}`
   - **总结**：`content.summary`
   - **亮点**：`content.highlights` 逐条列出
   - **风险与关注**：`content.risks` 逐条列出
   - **规模**：`content.task_count` 项任务、`content.change_count` 条改动
   - 可选附上 `content.tasks` 中的任务进展明细表（标题 / 负责人 / 状态 / 进展）

4. 判断是否为本次周期的新报告：对比报告 `created_at` 是否晚于上次推送时间；若最新报告仍是上一周期（即本周期报告尚未生成），告知用户「本期报告尚未生成（生成时间：周二/周五 17:00），当前最新为 {period_start} ~ {period_end} 的报告」。

## 注意事项

- 报告由后端定时器自动生成，也可由管理者在「工作日志 → 阶段总结」页手动触发
- 未配置 LLM Key 时报告为规则拼接的演示数据，summary 会带「（演示数据）」前缀，推送时如实说明
- 不要重复推送同一份报告：记住已推送报告的 `created_at`（可记录在会话或让用户确认）
- 系统未启动时先提示用户启动后端：`cd backend && uvicorn app.main:app --port 9000`

## 示例

用户：「推送一下最新的阶段总结」
做法：登录 → `GET /reports` → 取第一份 → 按「标题/总结/亮点/风险/规模」格式输出给用户。
