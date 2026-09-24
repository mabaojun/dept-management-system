"""导入《工作任务跟踪表 v12》作为初始数据。

用法（在 backend 目录下执行）:
    python -m scripts.import_tracking

幂等：成员按用户名查重、任务按标题查重，重复执行不会产生重复数据。
"""

from datetime import date, datetime

from app.core.security import hash_password
from app.db.base import SessionLocal
from app.models import Task, User

# 初始密码（至少 6 位），导入后可在「成员管理」中重置
INITIAL_PASSWORD = "unicom123"

# ── 成员（全部为部门成员角色）──
MEMBERS = [
    # (用户名, 姓名, 角色)
    ("qiujinbao", "邱金宝", "staff"),
    ("chenzhuo", "陈卓", "staff"),
    ("mabaojun", "马保俊", "staff"),
    ("yangmeiyuanxiao", "杨美园晓", "staff"),
    ("bisixin", "毕泗欣", "staff"),
]

# ── 任务（来源：工作任务跟踪表 v12，2026-09-21）──
# (序号, 任务板块, 工作内容, 负责人名, 协助说明, 状态, 优先级, 截止日期, 备注)
TASKS: list[tuple[int, str, str, str, str, str, str, date | None, str]] = [
    (1, "大寨山项目投标", "对接超图，跟进软件技术标编制", "陈卓", "", "done", "low", None,
     "已结束（9/16 因不满三家废标）"),
    (2, "大寨山项目投标", "整理工程公司技术标、硬件选型技术标文件", "马保俊", "共同负责人：陈卓", "done", "low", None,
     "已结束（9/16 因不满三家废标）"),
    (3, "大寨山项目投标", "整理商务标资料，搭建标书整体框架", "杨美园晓", "", "done", "low", None,
     "已结束（9/16 因不满三家废标）"),
    (4, "大寨山项目投标", "各板块对接协调、统筹跟进", "陈卓", "", "done", "low", None,
     "已结束（9/16 因不满三家废标）"),
    (5, "澳海DCMM三级认定", "对接工程公司、威海工业院，签订支出合同，落实3.5万元项目支出（当月开票、当月付款）",
     "邱金宝", "", "in_progress", "high", date(2026, 9, 30),
     "本月必完成；正在支出，需工程公司挂发票，确保当月开票、当月付款"),
    (6, "澳海DCMM三级认定", "推进项目评测进度", "邱金宝", "", "in_progress", "mid", None, ""),
    (7, "法院展厅建设", "现场勘察（已完成），跟进供应商方案制作", "邱金宝", "", "blocked", "high", None,
     "阻塞原因：院长外出无法对接；跟进要点：保持与院方沟通，院长外出结束后尽快恢复方案对接"),
    (8, "商企280万项目", "内部签约流程办理，跟踪前台签约目标分配", "马保俊", "", "todo", "mid", None,
     "待前台明确目标后推进"),
    (9, "等保测评", "等保测评相关工作", "陈卓", "", "in_progress", "mid", None, ""),
    (10, "跨部门对接", "与超算、IDC部门对接，闭环处理历史遗留任务", "邱金宝", "", "in_progress", "mid", None, ""),
    (11, "历史项目回款", "历史项目欠款回收、费用计收", "杨美园晓", "", "in_progress", "high", date(2026, 9, 30),
     "本月必完成，持续跟进"),
    (12, "孔村项目", "本月计收 + 系统内验收工作（前因：公司要房产抵账，孔村已认同视作欠款+项目已验收）",
     "马保俊", "协作：杨美园晓", "blocked", "high", date(2026, 9, 30),
     "本月必完成；阻塞：立项时未支出 → 无法下单（需下单额度）→ 需等合同"),
    (13, "ITO项目受理", "ITO项目受理", "毕泗欣", "协助：邱金宝、杨美园晓", "todo", "mid", None,
     "时间节点：等毕泗欣通知"),
    (14, "锦水河西支项目", "下单和计收工作", "陈卓", "", "in_progress", "urgent", None,
     "紧急：朱总催促项目支出，需明确支出金额、额度及付款节点，尽快落实"),
    (15, "擎雷科技数字化项目", "下单和计收工作", "陈卓", "", "in_progress", "mid", None, ""),
    (16, "云犀业务支撑", "支撑张庆辉的云犀业务", "邱金宝", "", "in_progress", "mid", None, ""),
    (17, "玫瑰研究所项目", "立项签约：和华阳梁经理沟通垫资成本 → 确定项目额度 → 完成签约",
     "邱金宝", "协助：马保俊（负责沟通华阳梁经理）", "todo", "mid", None, ""),
    (18, "澳海二期项目", "无人行车终验（和甲方协商后可以进行终验）", "马保俊", "", "todo", "mid", None,
     "终验具体时间待马保俊补充"),
    (19, "山东天眼安防科技项目", "立项签约：虚增270万元签约项目立项事宜（措辞待确认，是否为“新增”）",
     "陈卓", "协助：马保俊（负责设计合同内容）", "todo", "mid", None, ""),
    (20, "2023年公安局项目", "审计后整改", "马保俊", "协助：陈卓", "todo", "mid", None,
     "整改清单、截止时间待补充"),
    (21, "平阴县教体局教育城域网项目", "教育城域网建设推进", "陈卓", "", "in_progress", "mid", None,
     "建设里程碑、交付节点待补充"),
]

# 废标结束日期（跟踪表记录：9/16 废标）
DONE_AT = datetime(2026, 9, 16, 18, 0, 0)


def main() -> None:
    with SessionLocal() as db:
        admin = db.query(User).filter(User.role == "admin").first()
        if admin is None:
            raise SystemExit("未找到管理员账号，请先启动后端完成初始化")

        # 1. 导入成员
        name_to_user: dict[str, User] = {}
        for username, name, role in MEMBERS:
            user = db.query(User).filter(User.username == username).first()
            if user is None:
                user = User(
                    username=username,
                    password_hash=hash_password(INITIAL_PASSWORD),
                    name=name,
                    role=role,
                )
                db.add(user)
                db.flush()
                print(f"+ 创建成员 {name}（用户名 {username}，初始密码 {INITIAL_PASSWORD}）")
            else:
                print(f"= 成员 {name} 已存在，跳过")
            name_to_user[name] = user

        # 2. 导入任务
        created = skipped = 0
        for seq, module, content, owner, helpers, status, priority, due, note in TASKS:
            title = f"{module}｜{content}"
            exists = db.query(Task).filter(Task.title == title).first()
            if exists is not None:
                skipped += 1
                continue
            assignee = name_to_user.get(owner)
            if assignee is None:
                raise SystemExit(f"序号 {seq} 的负责人「{owner}」不在成员列表中")
            desc_parts = [f"【跟踪表序号 {seq}】"]
            if helpers:
                desc_parts.append(helpers)
            if note:
                desc_parts.append(note)
            task = Task(
                title=title,
                description="\n".join(desc_parts),
                assignee_id=assignee.id,
                creator_id=admin.id,
                priority=priority,
                status=status,
                due_date=due,
                completed_at=DONE_AT if status == "done" else None,
            )
            db.add(task)
            created += 1
            print(f"+ 任务[{seq:>2}] {title[:40]}… → {owner}（{status}/{priority}）")

        db.commit()
        print(f"\n完成：新增任务 {created} 项，跳过 {skipped} 项；成员共 {len(name_to_user)} 人。")


if __name__ == "__main__":
    main()
