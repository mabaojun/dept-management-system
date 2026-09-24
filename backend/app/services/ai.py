"""AI 服务层：LLM 客户端 + 提示词 + Mock 降级。

遵循《Agent 设计方法论》：
- System Prompt 采用「角色-能力-约束-输出格式」四层结构
- 显式边界声明 + 结构化 JSON 输出
- 未配置 LLM_API_KEY 时自动降级为 Mock 模式，保证系统可运行
"""
import json
import re

from openai import OpenAI

from app.db.base import SessionLocal
from app.services.sysconfig import get_llm_config

# ── 日志解析 Agent（信息判断型）──
PARSE_LOG_PROMPT = """# 角色定义
你是「部门工作日志解析员」，负责将成员上报的原始工作日志解析为结构化数据。
专业背景：熟悉通信行业部门日常工作（如签约流程、装机、维护、客户拜访、内部事务）。

# 能力声明
从日志文本中抽取：任务列表、每项任务的类别、预估耗时（小时）、产出物；并生成一句话摘要。

# 约束规则
- 只依据日志原文抽取，不得编造日志中不存在的信息（防幻觉）
- 无法判断的字段填 null，不要猜测
- 不对工作质量做任何评价，你只负责解析

# 输出格式（严格输出 JSON，不要输出其他内容）
{"tasks": [{"title": "...", "category": "...", "duration_hours": 0, "output": "..."}], "summary": "..."}"""

# ── 绩效分析 Agent（多源整合型，仅输出参考意见）──
MONTHLY_REVIEW_PROMPT = """# 角色定义
你是「部门绩效分析顾问」，基于客观数据为管理者生成本月绩效参考意见。
专业背景：熟悉通信行业部门工作模式与绩效评估方法。

# 能力声明
基于输入的任务统计、日志统计与日志样例，输出：总评、参考得分（0-100）、亮点、风险、改进建议。

# 约束规则
- 你输出的是「参考意见」，不是最终考核结论；最终评分权在部门管理者
- 严格基于输入数据，不得编造数据（防幻觉）；数据不足时明确说明
- 语言简明、具体、可执行，避免空话
- 注意：若日志中提到不熟悉的业务流程（如某类签约流程），在 suggestions 中提示管理者补充该流程的工作量说明（步骤、文件、紧迫性），以便后续完善评分机制

# 输出格式（严格输出 JSON，不要输出其他内容）
{"summary": "...", "score_reference": 0, "strengths": ["..."], "risks": ["..."], "suggestions": ["..."]}"""


# ── 阶段进展总结 Agent（定时任务 + 手动触发共用）──
PERIOD_REPORT_PROMPT = """# 角色定义
你是「部门任务进展总结员」，基于任务快照与改动记录生成阶段工作总结。
专业背景：熟悉通信行业部门工作模式。

# 能力声明
基于输入的任务清单（状态/进展叙述/负责人）与周期内改动记录，输出：总体进展概述、亮点、风险。

# 约束规则
- 严格基于输入数据，不得编造数据（防幻觉）；改动记录为空时如实说明
- 语言简明扼要、突出重点，概述控制在 150 字以内
- 优先关注：受阻任务、临近截止日期的任务、长期无进展的任务

# 输出格式（严格输出 JSON，不要输出其他内容）
{"summary": "...", "highlights": ["..."], "risks": ["..."]}"""


def is_mock_mode() -> bool:
    with SessionLocal() as db:
        return not get_llm_config(db)["api_key"]


def _chat(system: str, user: str) -> str:
    with SessionLocal() as db:
        cfg = get_llm_config(db)
    client = OpenAI(api_key=cfg["api_key"], base_url=cfg["base_url"])
    resp = client.chat.completions.create(
        model=cfg["model"],
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0.2,
    )
    return resp.choices[0].message.content or ""


def test_connection() -> str:
    """连通性测试：发送一条极小请求，失败时抛出异常。"""
    return _chat("你是连通性测试助手", "请只回复两个字：正常")


def _extract_json(text: str) -> dict:
    """从模型输出中提取 JSON（容忍代码块包裹）。"""
    match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        raise ValueError("LLM 输出中未找到 JSON")
    return json.loads(match.group(0))


def parse_worklog(content: str) -> dict:
    """解析工作日志为结构化数据。Mock 模式返回演示数据。"""
    if is_mock_mode():
        return _mock_parse(content)
    raw = _chat(PARSE_LOG_PROMPT, f"工作日志原文：\n{content}")
    return _extract_json(raw)


def monthly_review(payload: dict) -> dict:
    """生成本月绩效参考意见。Mock 模式返回演示数据。"""
    if is_mock_mode():
        return _mock_review(payload)
    raw = _chat(MONTHLY_REVIEW_PROMPT, json.dumps(payload, ensure_ascii=False))
    return _extract_json(raw)


def period_report(payload: dict) -> dict:
    """生成阶段工作总结。Mock 模式返回规则拼接的演示数据。"""
    if is_mock_mode():
        return _mock_period_report(payload)
    raw = _chat(PERIOD_REPORT_PROMPT, json.dumps(payload, ensure_ascii=False))
    return _extract_json(raw)


# ── Mock 降级（未配置 LLM Key 时保证全链路可运行）──
def _mock_parse(content: str) -> dict:
    lines = [ln.strip() for ln in content.splitlines() if ln.strip()]
    tasks = [
        {
            "title": ln[:40],
            "category": "日常事务",
            "duration_hours": 2,
            "output": None,
        }
        for ln in lines[:5]
    ] or [{"title": "未识别到具体任务", "category": "其他", "duration_hours": None, "output": None}]
    return {
        "tasks": tasks,
        "summary": f"（演示数据）日志共 {len(lines)} 行，已按行拆分为 {len(tasks)} 项任务。配置 LLM_API_KEY 后可获得真实解析。",
    }


def _mock_review(payload: dict) -> dict:
    stats = payload.get("task_stats", {})
    done = stats.get("done", 0)
    total = stats.get("total", 0)
    rate = round(done / total * 100) if total else 0
    return {
        "summary": f"（演示数据）本月共 {total} 项任务，完成 {done} 项，完成率约 {rate}%。配置 LLM_API_KEY 后可获得基于日志内容的真实分析。",
        "score_reference": min(60 + rate // 5, 95),
        "strengths": ["任务按计划推进，日志上报及时"],
        "risks": ["部分任务接近截止日期尚未完成"],
        "suggestions": [
            "对临近截止日期的任务设置提醒并优先跟进",
            "为不熟悉的业务流程（如签约流程）补充工作量说明：步骤、所需文件、紧迫性",
        ],
    }


def _mock_period_report(payload: dict) -> dict:
    tasks = payload.get("tasks", [])
    changes = payload.get("changes", [])
    by_status = {"done": 0, "in_progress": 0, "blocked": 0, "todo": 0}
    for t in tasks:
        by_status[t.get("status", "todo")] = by_status.get(t.get("status", "todo"), 0) + 1
    summary = (
        f"（演示数据）本周期共跟踪 {len(tasks)} 项任务："
        f"已完成 {by_status['done']}、进行中 {by_status['in_progress']}、"
        f"受阻 {by_status['blocked']}、待开始 {by_status['todo']}；"
        f"期间累计 {len(changes)} 条任务改动记录。配置 LLM_API_KEY 后可获得 AI 生成的深度总结。"
    )
    highlights = []
    if changes:
        highlights.append(f"周期内产生 {len(changes)} 次任务更新，团队推进保持活跃")
    if by_status["done"]:
        highlights.append(f"完成 {by_status['done']} 项任务")
    risks = []
    if by_status["blocked"]:
        risks.append(f"{by_status['blocked']} 项任务受阻，需优先协调资源")
    if not changes:
        risks.append("周期内无任务改动记录，请关注任务实际推进情况")
    return {"summary": summary, "highlights": highlights, "risks": risks}
