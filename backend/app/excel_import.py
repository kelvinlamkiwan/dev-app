"""Import CPM dates from a Development Schedule Excel into dev-app.

每行一個 Style：
  - ref 欄 → Style.ref_no（冇就建立、有就更新 designer/customer）
  - 各 sample 階段（development/confirmation/salesman/production/photo）嘅
    request（計劃）／receive（實際）日期 → Sample.requested_date / received_date
  - 各里程碑（訂單確認／物料到廠／生產開始／出廠／出貨）日期 → Milestone

欄位靠 header 彈性匹配（case-insensitive、substring），唔使跟死某一版 header。
"""

import io
from datetime import date, datetime

from . import cpm, models

# 順序重要：先里程碑（多字、較具體），後 sample 階段（避免 "production" vs "production start" 撞）
MILESTONE_ALIASES = {
    "訂單確認 Order Confirmation": ["order confirm", "order confirmation", "confirm order", "po confirm"],
    "物料到廠 Raw Material Arrival": ["raw material", "material arrival", "rm arrival", "material arrive"],
    "生產開始 Production Start": ["production start", "prod start", "bulk start", "bulk prod"],
    "出廠 Ex-Factory": ["ex-factory", "ex factory", "exfactory", "ex-fty", "ready date"],
    "出貨 Shipment": ["shipment", "ship date", "shipping date", "delivery"],
}

STAGE_ALIASES = {
    "development": ["development", "dev"],
    "confirmation": ["confirmation", "confirm", "conf"],
    "salesman": ["salesman", "sales", "sms"],
    "production": ["production", "prod", "pp"],
    "photo": ["photo"],
}

ACTUAL_KEYWORDS = ["actual", "received", "recv", "arrived", "completed", "done", "delivered"]
PLAN_KEYWORDS = ["plan", "request", "req", "due", "target", "expected", "eta", "requested", "planned"]

REF_KEYWORDS = ["ref", "reference", "style", "model", "article", "art no", "art number", "art code"]
DESIGNER_KEYWORDS = ["designer", "design"]
CUSTOMER_KEYWORDS = ["customer", "buyer", "brand", "account"]


def _classify(header_lower):
    """將 header 分類成 col_map 嘅 value tuple。"""
    if not header_lower:
        return None
    if any(k in header_lower for k in REF_KEYWORDS):
        return ("ref",)
    if any(k in header_lower for k in DESIGNER_KEYWORDS):
        return ("designer",)
    if any(k in header_lower for k in CUSTOMER_KEYWORDS):
        return ("customer",)

    # 里程碑（先，多字較具體）
    for mname, aliases in MILESTONE_ALIASES.items():
        if any(a in header_lower for a in aliases):
            which = "actual" if any(k in header_lower for k in ACTUAL_KEYWORDS) else "planned"
            return ("milestone", mname, which)

    # sample 階段
    for stage, aliases in STAGE_ALIASES.items():
        if any(a in header_lower for a in aliases):
            if any(k in header_lower for k in ACTUAL_KEYWORDS):
                which = "actual"
            elif any(k in header_lower for k in PLAN_KEYWORDS):
                which = "planned"
            else:
                which = "planned"  # 冇 plan/actual 字眼，default 計劃日期
            return ("sample", stage, which)

    return None


def _to_date_str(val):
    if val is None or val == "":
        return None
    if isinstance(val, datetime):
        return val.date().isoformat()
    if isinstance(val, date):
        return val.isoformat()
    s = str(val).strip()
    d = cpm.parse_date(s)
    return d.isoformat() if d else s


def parse_workbook(data: bytes):
    """回傳 (data_rows, col_map, headers)。col_map: col_idx -> tuple。"""
    import openpyxl

    wb = openpyxl.load_workbook(io.BytesIO(data), data_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        return [], {}, []

    headers = [str(h).strip() if h is not None else "" for h in rows[0]]
    col_map = {}
    for idx, h in enumerate(headers):
        m = _classify(h.lower())
        if m:
            col_map[idx] = m

    data_rows = []
    for row in rows[1:]:
        if row is None or all(v is None or str(v).strip() == "" for v in row):
            continue
        data_rows.append(row)

    return data_rows, col_map, headers


def import_workbook(data: bytes, db):
    data_rows, col_map, headers = parse_workbook(data)

    if not any(m[0] == "ref" for m in col_map.values()):
        raise ValueError("搵唔到 ref 欄（搵唔到 header 含 ref/style/art/model/article 嘅欄）")

    summary = {
        "rows": 0,
        "styles_created": 0,
        "styles_updated": 0,
        "samples_created": 0,
        "samples_updated": 0,
        "milestones_updated": 0,
        "recognized_columns": {headers[i]: m for i, m in col_map.items()},
        "unrecognized_columns": [h for i, h in enumerate(headers) if i not in col_map and h],
    }

    for row in data_rows:
        ref = None
        designer = None
        customer = None
        sample_dates = {}
        milestone_dates = {}

        for idx, val in enumerate(row):
            if idx not in col_map:
                continue
            m = col_map[idx]
            if m[0] == "ref":
                v = str(val).strip() if val not in (None, "") else None
                if v and ref is None:
                    ref = v
            elif m[0] == "designer":
                designer = str(val).strip() if val not in (None, "") else None
            elif m[0] == "customer":
                customer = str(val).strip() if val not in (None, "") else None
            elif m[0] == "sample":
                _, stage, which = m
                sample_dates.setdefault(stage, {})[which] = _to_date_str(val)
            elif m[0] == "milestone":
                _, mname, which = m
                milestone_dates.setdefault(mname, {})[which] = _to_date_str(val)

        if not ref:
            continue

        # Style upsert
        style = db.query(models.Style).filter_by(ref_no=ref).first()
        if not style:
            style = models.Style(ref_no=ref, designer=designer, customer=customer)
            db.add(style)
            db.flush()
            for dm in cpm.DEFAULT_MILESTONES:
                db.add(models.Milestone(style_id=style.id, **dm))
            summary["styles_created"] += 1
        else:
            if designer:
                style.designer = designer
            if customer:
                style.customer = customer
            summary["styles_updated"] += 1

        # Samples
        for stage, dates in sample_dates.items():
            sample = db.query(models.Sample).filter_by(style_id=style.id, stage=stage).first()
            if not sample:
                sample = models.Sample(style_id=style.id, stage=stage)
                db.add(sample)
                db.flush()
                db.add(models.Bom(sample_id=sample.id))
                summary["samples_created"] += 1
            else:
                summary["samples_updated"] += 1
            if "planned" in dates and dates["planned"]:
                sample.requested_date = dates["planned"]
            if "actual" in dates and dates["actual"]:
                sample.received_date = dates["actual"]

        # Milestones
        for mname, dates in milestone_dates.items():
            ms = db.query(models.Milestone).filter_by(style_id=style.id, name=mname).first()
            if not ms:
                ms = models.Milestone(style_id=style.id, name=mname, sequence=99)
                db.add(ms)
                db.flush()
            if "planned" in dates and dates["planned"]:
                ms.planned_date = dates["planned"]
            if "actual" in dates and dates["actual"]:
                ms.actual_date = dates["actual"]
            summary["milestones_updated"] += 1

        summary["rows"] += 1

    db.commit()
    return summary
