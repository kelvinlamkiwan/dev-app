"""CPM (Critical Path Management) — 關鍵路徑管理計算。

將 Sample 階段（development→confirmation→salesman→production→photo）＋
自訂里程碑（訂單確認／物料到廠／生產開始／出廠／出貨）合埋做一條時間線，
計每項嘅 delay 同 critical 狀態。
"""

from datetime import date, datetime

# Sample 階段排序（開發流程先後）
STAGE_ORDER = {
    "development": 0,
    "confirmation": 1,
    "salesman": 2,
    "production": 3,
    "photo": 4,
}

# 新 Style 預設里程碑（非 sample 階段，屬訂單／生產層面）
DEFAULT_MILESTONES = [
    {"name": "訂單確認 Order Confirmation", "sequence": 10},
    {"name": "物料到廠 Raw Material Arrival", "sequence": 60},
    {"name": "生產開始 Production Start", "sequence": 70},
    {"name": "出廠 Ex-Factory", "sequence": 80},
    {"name": "出貨 Shipment", "sequence": 90},
]


def parse_date(s):
    """寬鬆解析日期字串，支援多種格式；失敗回 None。"""
    if not s:
        return None
    s = str(s).strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%m/%d/%Y", "%d.%m.%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def delay_status(planned_s, actual_s, today=None):
    """計一項里程碑嘅 delay 同 critical 狀態。

    回傳 dict: {status, delay_days, critical}
    status 值：
      - delayed   實際 > 計劃（遲到完成）
      - overdue   計劃已過但未完成
      - done      已完成且準時
      - scheduled 有計劃日期、未到期
      - not_started 冇日期
    """
    today = today or date.today()
    planned = parse_date(planned_s)
    actual = parse_date(actual_s)

    if actual is not None:
        if planned is not None and actual > planned:
            return {"status": "delayed", "delay_days": (actual - planned).days, "critical": True}
        delay = (actual - planned).days if planned is not None else 0
        return {"status": "done", "delay_days": delay, "critical": False}

    # 未有實際日期
    if planned is not None:
        if planned < today:
            return {"status": "overdue", "delay_days": (today - planned).days, "critical": True}
        return {"status": "scheduled", "delay_days": 0, "critical": False}

    return {"status": "not_started", "delay_days": 0, "critical": False}
