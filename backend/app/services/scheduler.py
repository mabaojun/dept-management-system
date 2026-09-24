"""定时调度：每周二、每周五 17:00 自动生成阶段工作总结。

轻量实现（不引入 APScheduler）：asyncio 循环计算距下个触发点的秒数后休眠。
服务重启后自动重新对齐到下一个触发点。
"""
import asyncio
import logging
from datetime import datetime, time, timedelta

from app.db.base import SessionLocal
from app.services.report import generate_period_report

logger = logging.getLogger("scheduler")

# weekday(): 周一=0 … 周五=4
REPORT_TIMES: dict[int, tuple[str, time]] = {
    1: ("midweek", time(17, 0)),  # 周二 17:00 中期简报
    4: ("weekly", time(17, 0)),  # 周五 17:00 周报
}


def _next_run(now: datetime) -> tuple[datetime, str]:
    """距 now 最近的下个触发点。"""
    for offset in range(8):
        day = (now + timedelta(days=offset)).date()
        if day.weekday() in REPORT_TIMES:
            kind, at = REPORT_TIMES[day.weekday()]
            run_at = datetime.combine(day, at)
            if run_at > now:
                return run_at, kind
    raise RuntimeError("unreachable")  # 8 天内必含周二/周五


async def scheduler_loop() -> None:
    while True:
        now = datetime.now()
        run_at, kind = _next_run(now)
        wait = (run_at - now).total_seconds() + 1
        logger.info("下次阶段总结生成：%s (%s)", run_at, kind)
        try:
            await asyncio.sleep(wait)
        except asyncio.CancelledError:
            return
        try:
            # 生成过程涉及同步 DB/LLM 调用，放入线程避免阻塞事件循环
            await asyncio.to_thread(_generate, kind)
        except Exception:  # noqa: BLE001 单次失败不影响服务，下个周期重试
            logger.exception("阶段总结生成失败 kind=%s", kind)


def _generate(kind: str) -> None:
    with SessionLocal() as db:
        report = generate_period_report(db, kind)
    logger.info("阶段总结已生成 #%s kind=%s", report.id, kind)
