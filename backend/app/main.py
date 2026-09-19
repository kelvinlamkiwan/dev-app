import json

from fastapi import Depends, FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, inspect, text
from sqlalchemy.orm import Session

from . import cpm, excel_import, models, schemas
from .database import Base, engine, get_db
from .pdf_parser import parse_spec_sheet
from .seed import seed_data

app = FastAPI(title="dev-app", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _migrate():
    """輕量遷移：bom_items 嘅 cpm→unit_cost rename，同補缺失列。"""
    insp = inspect(engine)
    if "bom_items" in insp.get_table_names():
        cols = {c["name"] for c in insp.get_columns("bom_items")}
        if "cpm" in cols and "unit_cost" not in cols:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE bom_items RENAME COLUMN cpm TO unit_cost"))
        elif "unit_cost" not in cols:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE bom_items ADD COLUMN unit_cost FLOAT"))


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    _migrate()
    seed_data()


@app.get("/")
def root():
    return {"app": "dev-app", "status": "ok"}


@app.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    styles_total = db.query(models.Style).count()
    materials_total = db.query(models.Material).count()
    components_total = db.query(models.Component).count()
    samples_total = db.query(models.Sample).count()
    boms_total = db.query(models.Bom).count()
    boms_confirmed = db.query(models.Bom).filter_by(confirmed=True).count()

    status_rows = db.query(models.Style.status, func.count()).group_by(models.Style.status).all()
    styles_by_status = {s or "draft": n for s, n in status_rows}

    recent = db.query(models.Style).order_by(models.Style.updated_at.desc()).limit(5).all()
    recent_styles = [schemas.StyleSummary.model_validate(s) for s in recent]

    return {
        "styles_total": styles_total,
        "materials_total": materials_total,
        "components_total": components_total,
        "samples_total": samples_total,
        "boms_total": boms_total,
        "boms_confirmed": boms_confirmed,
        "styles_by_status": styles_by_status,
        "recent_styles": recent_styles,
    }


# ---------- Components ----------
@app.get("/components", response_model=list[schemas.ComponentOut])
def list_components(db: Session = Depends(get_db)):
    return db.query(models.Component).order_by(models.Component.name).all()


@app.post("/components", response_model=schemas.ComponentOut)
def create_component(payload: schemas.ComponentCreate, db: Session = Depends(get_db)):
    if db.query(models.Component).filter_by(name=payload.name).first():
        raise HTTPException(409, "component already exists")
    c = models.Component(name=payload.name)
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


# ---------- Materials ----------
@app.get("/materials", response_model=list[schemas.MaterialOut])
def list_materials(q: str = Query(None), db: Session = Depends(get_db)):
    qq = db.query(models.Material)
    if q:
        like = f"%{q}%"
        qq = qq.filter(
            models.Material.name.like(like)
            | models.Material.material_code.like(like)
            | models.Material.supplier.like(like)
            | models.Material.color.like(like)
        )
    return qq.order_by(models.Material.material_code).all()


@app.post("/materials", response_model=schemas.MaterialOut)
def create_material(payload: schemas.MaterialCreate, db: Session = Depends(get_db)):
    if db.query(models.Material).filter_by(material_code=payload.material_code).first():
        raise HTTPException(409, "material_code already exists")
    m = models.Material(**payload.model_dump())
    db.add(m)
    db.commit()
    db.refresh(m)
    return m


@app.put("/materials/{mid}", response_model=schemas.MaterialOut)
def update_material(mid: int, payload: schemas.MaterialUpdate, db: Session = Depends(get_db)):
    m = db.get(models.Material, mid)
    if not m:
        raise HTTPException(404, "material not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(m, k, v)
    db.commit()
    db.refresh(m)
    return m


@app.delete("/materials/{mid}")
def delete_material(mid: int, db: Session = Depends(get_db)):
    m = db.get(models.Material, mid)
    if not m:
        raise HTTPException(404, "material not found")
    db.delete(m)
    db.commit()
    return {"ok": True}


@app.post("/materials/sync", response_model=schemas.MaterialSyncResult)
def sync_materials(payload: schemas.MaterialSyncRequest, db: Session = Depends(get_db)):
    """Bulk upsert material master：有 material_code 就更新、冇就新增。

    - `delete_missing=True` 時做 full sync：push 入面冇嘅 material_code 會被刪走。
    - 每條 record 用 payload 全量覆寫（包括 None 欄位），確保 DB 同 source 一致。
    """
    created = updated = deleted = 0
    items: list = []
    errors: list = []
    seen_codes: list = []

    for m in payload.materials:
        if not m.material_code:
            errors.append(f"缺 material_code：{m.name or '(unnamed)'}")
            continue
        existing = db.query(models.Material).filter_by(material_code=m.material_code).first()
        data = m.model_dump()
        if existing:
            for k, v in data.items():
                setattr(existing, k, v)
            action, item_id = "updated", existing.id
            updated += 1
        else:
            obj = models.Material(**data)
            db.add(obj)
            db.flush()
            action, item_id = "created", obj.id
            created += 1
        seen_codes.append(m.material_code)
        items.append({"material_code": m.material_code, "id": item_id, "action": action})

    if payload.delete_missing and seen_codes:
        to_delete = db.query(models.Material).filter(
            ~models.Material.material_code.in_(seen_codes)
        ).all()
        for d in to_delete:
            db.delete(d)
        deleted = len(to_delete)

    db.commit()
    return schemas.MaterialSyncResult(
        created=created, updated=updated, deleted=deleted, errors=errors, items=items
    )


# ---------- Styles ----------
@app.get("/styles", response_model=list[schemas.StyleSummary])
def list_styles(db: Session = Depends(get_db)):
    return db.query(models.Style).order_by(models.Style.id.desc()).all()


@app.post("/styles", response_model=schemas.StyleOut)
def create_style(payload: schemas.StyleCreate, db: Session = Depends(get_db)):
    if db.query(models.Style).filter_by(ref_no=payload.ref_no).first():
        raise HTTPException(409, "ref_no already exists")
    s = models.Style(**payload.model_dump())
    db.add(s)
    db.flush()
    for m in cpm.DEFAULT_MILESTONES:
        db.add(models.Milestone(style_id=s.id, **m))
    db.commit()
    db.refresh(s)
    return schemas.StyleOut.model_validate(s)


@app.get("/styles/{sid}", response_model=schemas.StyleOut)
def get_style(sid: int, db: Session = Depends(get_db)):
    s = db.get(models.Style, sid)
    if not s:
        raise HTTPException(404, "style not found")
    return schemas.StyleOut.model_validate(s)


@app.put("/styles/{sid}", response_model=schemas.StyleOut)
def update_style(sid: int, payload: schemas.StyleCreate, db: Session = Depends(get_db)):
    s = db.get(models.Style, sid)
    if not s:
        raise HTTPException(404, "style not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(s, k, v)
    db.commit()
    db.refresh(s)
    return schemas.StyleOut.model_validate(s)


@app.delete("/styles/{sid}")
def delete_style(sid: int, db: Session = Depends(get_db)):
    s = db.get(models.Style, sid)
    if not s:
        raise HTTPException(404, "style not found")
    db.delete(s)
    db.commit()
    return {"ok": True}


# ---------- Samples ----------
@app.post("/styles/{sid}/samples", response_model=schemas.SampleOut)
def create_sample(sid: int, payload: schemas.SampleCreate, db: Session = Depends(get_db)):
    if not db.get(models.Style, sid):
        raise HTTPException(404, "style not found")
    sample = models.Sample(style_id=sid, **payload.model_dump())
    db.add(sample)
    db.flush()
    db.add(models.Bom(sample_id=sample.id))  # 每個 sample 一份 BOM
    db.commit()
    db.refresh(sample)
    return schemas.SampleOut.model_validate(sample)


@app.put("/samples/{sid}", response_model=schemas.SampleOut)
def update_sample(sid: int, payload: schemas.SampleUpdate, db: Session = Depends(get_db)):
    s = db.get(models.Sample, sid)
    if not s:
        raise HTTPException(404, "sample not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(s, k, v)
    db.commit()
    db.refresh(s)
    return schemas.SampleOut.model_validate(s)


@app.delete("/samples/{sid}")
def delete_sample(sid: int, db: Session = Depends(get_db)):
    s = db.get(models.Sample, sid)
    if not s:
        raise HTTPException(404, "sample not found")
    db.delete(s)
    db.commit()
    return {"ok": True}


# ---------- BOM ----------
@app.post("/boms/{bid}/items", response_model=schemas.BomOut)
def add_bom_item(bid: int, payload: schemas.BomItemCreate, db: Session = Depends(get_db)):
    bom = db.get(models.Bom, bid)
    if not bom:
        raise HTTPException(404, "bom not found")
    data = payload.model_dump()
    # 未指定 unit_cost 時，預設用 material master 嘅 price
    if data.get("unit_cost") is None:
        mat = db.get(models.Material, payload.material_id)
        if mat and mat.price is not None:
            data["unit_cost"] = mat.price
    max_order = db.query(func.max(models.BomItem.sort_order)).filter_by(bom_id=bid).scalar() or 0
    item = models.BomItem(bom_id=bid, sort_order=max_order + 1, **data)
    db.add(item)
    db.commit()
    db.refresh(bom)
    return schemas.BomOut.model_validate(bom)


@app.put("/bom-items/{iid}", response_model=schemas.BomOut)
def update_bom_item(iid: int, payload: schemas.BomItemUpdate, db: Session = Depends(get_db)):
    item = db.get(models.BomItem, iid)
    if not item:
        raise HTTPException(404, "bom item not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(item, k, v)
    db.commit()
    bom = db.get(models.Bom, item.bom_id)
    db.refresh(bom)
    return schemas.BomOut.model_validate(bom)


@app.delete("/bom-items/{iid}", response_model=schemas.BomOut)
def delete_bom_item(iid: int, db: Session = Depends(get_db)):
    item = db.get(models.BomItem, iid)
    if not item:
        raise HTTPException(404, "bom item not found")
    bom_id = item.bom_id
    db.delete(item)
    db.commit()
    bom = db.get(models.Bom, bom_id)
    return schemas.BomOut.model_validate(bom)


@app.put("/boms/{bid}/confirm", response_model=schemas.BomOut)
def confirm_bom(bid: int, db: Session = Depends(get_db)):
    bom = db.get(models.Bom, bid)
    if not bom:
        raise HTTPException(404, "bom not found")
    bom.confirmed = True
    db.commit()
    db.refresh(bom)
    return schemas.BomOut.model_validate(bom)


# ---------- Costing ----------
def _compute_costing(costing, db: Session) -> dict:
    bom = db.query(models.Bom).filter_by(sample_id=costing.sample_id).first()
    materials = 0.0
    if bom:
        materials = sum((i.quantity or 0) * (i.unit_cost or 0) for i in bom.items)

    labor = costing.labor or 0
    overhead_pct = costing.overhead_pct or 0
    margin_pct = costing.margin_pct or 0
    freight = costing.freight or 0
    mold_cost = costing.mold_cost or 0
    order_qty = costing.order_qty or 0

    mold_per_pair = mold_cost / order_qty if order_qty > 0 else 0
    overhead = (materials + labor) * overhead_pct / 100
    total_cost = materials + labor + overhead + freight + mold_per_pair
    margin = total_cost * margin_pct / 100
    fob_price = total_cost + margin
    target_price = costing.target_price
    variance = (fob_price - target_price) if target_price is not None else None

    return {
        "materials": round(materials, 4),
        "labor": labor,
        "overhead_pct": overhead_pct,
        "overhead": round(overhead, 4),
        "freight": freight,
        "mold_cost": mold_cost,
        "mold_per_pair": round(mold_per_pair, 4),
        "total_cost": round(total_cost, 4),
        "margin_pct": margin_pct,
        "margin": round(margin, 4),
        "fob_price": round(fob_price, 4),
        "target_price": target_price,
        "variance": round(variance, 4) if variance is not None else None,
        "currency": costing.currency or "USD",
    }


def _costing_out(costing, db: Session) -> schemas.CostingOut:
    return schemas.CostingOut(
        id=costing.id,
        sample_id=costing.sample_id,
        labor=costing.labor,
        overhead_pct=costing.overhead_pct,
        margin_pct=costing.margin_pct,
        freight=costing.freight,
        mold_cost=costing.mold_cost,
        order_qty=costing.order_qty,
        target_price=costing.target_price,
        currency=costing.currency,
        notes=costing.notes,
        computed=_compute_costing(costing, db),
    )


@app.get("/samples/{sid}/costing", response_model=schemas.CostingOut)
def get_costing(sid: int, db: Session = Depends(get_db)):
    if not db.get(models.Sample, sid):
        raise HTTPException(404, "sample not found")
    costing = db.query(models.Costing).filter_by(sample_id=sid).first()
    if not costing:
        costing = models.Costing(sample_id=sid)
        db.add(costing)
        db.commit()
        db.refresh(costing)
    return _costing_out(costing, db)


@app.put("/samples/{sid}/costing", response_model=schemas.CostingOut)
def update_costing(sid: int, payload: schemas.CostingUpdate, db: Session = Depends(get_db)):
    if not db.get(models.Sample, sid):
        raise HTTPException(404, "sample not found")
    costing = db.query(models.Costing).filter_by(sample_id=sid).first()
    if not costing:
        costing = models.Costing(sample_id=sid)
        db.add(costing)
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(costing, k, v)
    db.commit()
    db.refresh(costing)
    return _costing_out(costing, db)


@app.get("/costing")
def list_costing(db: Session = Depends(get_db)):
    """所有鞋款嘅成本 summary（每階段材料成本 + FOB 報價）。"""
    styles = db.query(models.Style).order_by(models.Style.id.desc()).all()
    result = []
    for style in styles:
        samples = []
        for s in style.samples:
            costing = db.query(models.Costing).filter_by(sample_id=s.id).first()
            if costing:
                comp = _compute_costing(costing, db)
                samples.append(
                    {
                        "sample_id": s.id,
                        "stage": s.stage,
                        "materials": comp["materials"],
                        "total_cost": comp["total_cost"],
                        "fob_price": comp["fob_price"],
                        "target_price": comp["target_price"],
                        "variance": comp["variance"],
                    }
                )
            else:
                bom = s.bom
                materials = round(sum((i.quantity or 0) * (i.unit_cost or 0) for i in bom.items), 4) if bom else 0.0
                samples.append(
                    {
                        "sample_id": s.id,
                        "stage": s.stage,
                        "materials": materials,
                        "total_cost": None,
                        "fob_price": None,
                        "target_price": None,
                        "variance": None,
                    }
                )
        result.append(
            {
                "style_id": style.id,
                "ref_no": style.ref_no,
                "customer": style.customer,
                "brand": style.brand,
                "samples": samples,
            }
        )
    return result


# ---------- Milestones / CPM ----------
@app.get("/styles/{sid}/milestones", response_model=list[schemas.MilestoneOut])
def list_milestones(sid: int, db: Session = Depends(get_db)):
    if not db.get(models.Style, sid):
        raise HTTPException(404, "style not found")
    return (
        db.query(models.Milestone)
        .filter_by(style_id=sid)
        .order_by(models.Milestone.sequence)
        .all()
    )


@app.post("/styles/{sid}/milestones", response_model=schemas.MilestoneOut)
def create_milestone(sid: int, payload: schemas.MilestoneCreate, db: Session = Depends(get_db)):
    if not db.get(models.Style, sid):
        raise HTTPException(404, "style not found")
    data = payload.model_dump()
    if data.get("sequence") is None:
        max_seq = db.query(func.max(models.Milestone.sequence)).filter_by(style_id=sid).scalar() or 0
        data["sequence"] = max_seq + 10
    m = models.Milestone(style_id=sid, **data)
    db.add(m)
    db.commit()
    db.refresh(m)
    return m


@app.put("/milestones/{mid}", response_model=schemas.MilestoneOut)
def update_milestone(mid: int, payload: schemas.MilestoneUpdate, db: Session = Depends(get_db)):
    m = db.get(models.Milestone, mid)
    if not m:
        raise HTTPException(404, "milestone not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(m, k, v)
    db.commit()
    db.refresh(m)
    return m


@app.delete("/milestones/{mid}")
def delete_milestone(mid: int, db: Session = Depends(get_db)):
    m = db.get(models.Milestone, mid)
    if not m:
        raise HTTPException(404, "milestone not found")
    db.delete(m)
    db.commit()
    return {"ok": True}


@app.get("/styles/{sid}/cpm")
def get_cpm(sid: int, db: Session = Depends(get_db)):
    """CPM 關鍵路徑：Sample 階段時間線 + 自訂里程碑，計 delay / critical。"""
    style = db.get(models.Style, sid)
    if not style:
        raise HTTPException(404, "style not found")

    sample_timeline = []
    for s in sorted(style.samples, key=lambda x: cpm.STAGE_ORDER.get(x.stage, 99)):
        st = cpm.delay_status(s.requested_date, s.received_date)
        sample_timeline.append(
            {
                "kind": "sample",
                "id": s.id,
                "name": s.stage,
                "planned": s.requested_date,
                "actual": s.received_date,
                "status": st["status"],
                "delay_days": st["delay_days"],
                "critical": st["critical"],
            }
        )

    milestones = []
    for m in sorted(style.milestones, key=lambda x: x.sequence or 0):
        st = cpm.delay_status(m.planned_date, m.actual_date)
        milestones.append(
            {
                "kind": "milestone",
                "id": m.id,
                "name": m.name,
                "planned": m.planned_date,
                "actual": m.actual_date,
                "status": st["status"],
                "delay_days": st["delay_days"],
                "critical": st["critical"],
            }
        )

    all_items = sample_timeline + milestones
    critical = sum(1 for x in all_items if x["critical"])
    delayed = sum(1 for x in all_items if x["status"] == "delayed")
    overdue = sum(1 for x in all_items if x["status"] == "overdue")
    done = sum(1 for x in all_items if x["status"] == "done")

    return {
        "ref_no": style.ref_no,
        "sample_timeline": sample_timeline,
        "milestones": milestones,
        "summary": {
            "total": len(all_items),
            "critical": critical,
            "delayed": delayed,
            "overdue": overdue,
            "done": done,
        },
    }


@app.get("/cpm")
def list_cpm(db: Session = Depends(get_db)):
    """所有鞋款嘅 CPM summary（關鍵路徑 dashboard）。"""
    styles = db.query(models.Style).order_by(models.Style.id.desc()).all()
    return [
        {
            "style_id": s.id,
            "ref_no": s.ref_no,
            "customer": s.customer,
            "brand": s.brand,
            "summary": cpm.compute_summary(s),
        }
        for s in styles
    ]


@app.post("/cpm/import")
async def import_cpm_excel(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """由 Development Schedule Excel 匯入 CPM 日期（每行一個 Style）。

    上傳 .xlsx，header 會自動匹配 ref / sample 階段日期 / 里程碑日期。
    """
    data = await file.read()
    try:
        return excel_import.import_workbook(data, db)
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    except Exception as exc:
        raise HTTPException(400, f"Import failed: {exc}")


# ---------- PDF Spec Sheet ----------
@app.post("/pdf/parse")
async def parse_pdf(file: UploadFile = File(...)):
    data = await file.read()
    try:
        result = parse_spec_sheet(data)
    except Exception as exc:
        raise HTTPException(400, f"Failed to parse PDF: {exc}")
    return {"filename": file.filename, "parsed": result}


@app.post("/styles/{sid}/spec-sheets")
async def upload_spec_sheet(sid: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not db.get(models.Style, sid):
        raise HTTPException(404, "style not found")
    data = await file.read()
    try:
        result = parse_spec_sheet(data)
    except Exception:
        result = {}
    sheet = models.SpecSheet(style_id=sid, filename=file.filename, parsed_json=json.dumps(result))
    db.add(sheet)
    db.commit()
    return {"id": sheet.id, "filename": file.filename, "parsed": result}
