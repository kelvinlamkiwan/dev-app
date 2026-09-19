from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


# ---------- Component ----------
class ComponentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str


class ComponentCreate(BaseModel):
    name: str


# ---------- Material ----------
class MaterialOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    material_code: str
    name: str
    type: Optional[str] = None
    color: Optional[str] = None
    color_code: Optional[str] = None
    supplier: Optional[str] = None
    supplier_ref: Optional[str] = None
    unit: Optional[str] = None
    price: Optional[float] = None
    min_order: Optional[str] = None
    spec: Optional[str] = None
    status: Optional[str] = None


class MaterialCreate(BaseModel):
    material_code: str
    name: str
    type: Optional[str] = None
    color: Optional[str] = None
    color_code: Optional[str] = None
    supplier: Optional[str] = None
    supplier_ref: Optional[str] = None
    unit: Optional[str] = None
    price: Optional[float] = None
    min_order: Optional[str] = None
    spec: Optional[str] = None


class MaterialUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    color: Optional[str] = None
    color_code: Optional[str] = None
    supplier: Optional[str] = None
    supplier_ref: Optional[str] = None
    unit: Optional[str] = None
    price: Optional[float] = None
    min_order: Optional[str] = None
    spec: Optional[str] = None
    status: Optional[str] = None


# ---------- BOM ----------
class BomItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    component_id: Optional[int] = None
    material_id: int
    quantity: Optional[float] = None
    unit: Optional[str] = None
    unit_cost: Optional[float] = None
    color: Optional[str] = None
    supplier_ref: Optional[str] = None
    remarks: Optional[str] = None
    sort_order: int = 0
    component: Optional[ComponentOut] = None
    material: Optional[MaterialOut] = None


class BomItemCreate(BaseModel):
    component_id: Optional[int] = None
    material_id: int
    quantity: Optional[float] = None
    unit: Optional[str] = None
    unit_cost: Optional[float] = None
    color: Optional[str] = None
    supplier_ref: Optional[str] = None
    remarks: Optional[str] = None


class BomItemUpdate(BaseModel):
    component_id: Optional[int] = None
    material_id: Optional[int] = None
    quantity: Optional[float] = None
    unit: Optional[str] = None
    unit_cost: Optional[float] = None
    color: Optional[str] = None
    supplier_ref: Optional[str] = None
    remarks: Optional[str] = None


class BomOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    sample_id: int
    version: int = 1
    notes: Optional[str] = None
    confirmed: bool = False
    items: List[BomItemOut] = []


# ---------- Sample ----------
class SampleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    style_id: int
    stage: str
    sample_no: Optional[str] = None
    size: Optional[str] = None
    status: Optional[str] = None
    requested_date: Optional[str] = None
    received_date: Optional[str] = None
    notes: Optional[str] = None
    bom: Optional[BomOut] = None


class SampleCreate(BaseModel):
    stage: str
    sample_no: Optional[str] = None
    size: Optional[str] = None
    status: Optional[str] = None
    requested_date: Optional[str] = None
    received_date: Optional[str] = None
    notes: Optional[str] = None


class SampleUpdate(BaseModel):
    stage: Optional[str] = None
    sample_no: Optional[str] = None
    size: Optional[str] = None
    status: Optional[str] = None
    requested_date: Optional[str] = None
    received_date: Optional[str] = None
    notes: Optional[str] = None


# ---------- Style ----------
class StyleSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    ref_no: str
    customer: Optional[str] = None
    brand: Optional[str] = None
    status: Optional[str] = None
    updated_at: Optional[datetime] = None


class StyleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    ref_no: str
    customer: Optional[str] = None
    brand: Optional[str] = None
    designer: Optional[str] = None
    season: Optional[str] = None
    category: Optional[str] = None
    status: Optional[str] = None
    description: Optional[str] = None
    samples: List[SampleOut] = []


class StyleCreate(BaseModel):
    ref_no: str
    customer: Optional[str] = None
    brand: Optional[str] = None
    designer: Optional[str] = None
    season: Optional[str] = None
    category: Optional[str] = None
    status: Optional[str] = None
    description: Optional[str] = None


# ---------- Material Sync ----------
class MaterialSyncItem(BaseModel):
    material_code: str
    id: int
    action: str  # created | updated


class MaterialSyncRequest(BaseModel):
    materials: List[MaterialCreate]
    delete_missing: bool = False  # True 時：push 入面冇嘅 material_code 會被刪走（full sync）


class MaterialSyncResult(BaseModel):
    created: int = 0
    updated: int = 0
    deleted: int = 0
    errors: List[str] = []
    items: List[MaterialSyncItem] = []


# ---------- Costing ----------
class CostingUpdate(BaseModel):
    labor: Optional[float] = None
    overhead_pct: Optional[float] = None
    margin_pct: Optional[float] = None
    freight: Optional[float] = None
    mold_cost: Optional[float] = None
    order_qty: Optional[int] = None
    target_price: Optional[float] = None
    currency: Optional[str] = None
    notes: Optional[str] = None


class CostingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    sample_id: int
    labor: Optional[float] = 0
    overhead_pct: Optional[float] = 0
    margin_pct: Optional[float] = 0
    freight: Optional[float] = 0
    mold_cost: Optional[float] = 0
    order_qty: Optional[int] = 0
    target_price: Optional[float] = None
    currency: Optional[str] = "USD"
    notes: Optional[str] = None
    computed: Optional[dict] = None


# ---------- Milestone / CPM ----------
class MilestoneOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    style_id: int
    name: str
    planned_date: Optional[str] = None
    actual_date: Optional[str] = None
    sequence: int = 0
    notes: Optional[str] = None


class MilestoneCreate(BaseModel):
    name: str
    planned_date: Optional[str] = None
    actual_date: Optional[str] = None
    sequence: Optional[int] = None
    notes: Optional[str] = None


class MilestoneUpdate(BaseModel):
    name: Optional[str] = None
    planned_date: Optional[str] = None
    actual_date: Optional[str] = None
    sequence: Optional[int] = None
    notes: Optional[str] = None
