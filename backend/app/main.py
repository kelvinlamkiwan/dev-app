import json

from fastapi import Depends, FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func
from sqlalchemy.orm import Session

from . import models, schemas
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


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    seed_data()


@app.get("/")
def root():
    return {"app": "dev-app", "status": "ok"}


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
def update_sample(sid: int, payload: schemas.SampleCreate, db: Session = Depends(get_db)):
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
    max_order = db.query(func.max(models.BomItem.sort_order)).filter_by(bom_id=bid).scalar() or 0
    item = models.BomItem(bom_id=bid, sort_order=max_order + 1, **payload.model_dump())
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
