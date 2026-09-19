from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from .database import Base


def now():
    return datetime.now(timezone.utc)


class Component(Base):
    """部件主檔（Vamp/Quarter/Tongue/Sole/...）"""

    __tablename__ = "components"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)


class Material(Base):
    """Master material data（物料主檔）"""

    __tablename__ = "materials"
    id = Column(Integer, primary_key=True)
    material_code = Column(String, unique=True, nullable=False)  # SKU
    name = Column(String, nullable=False)
    type = Column(String)  # leather / synthetic / textile / rubber / metal ...
    color = Column(String)
    color_code = Column(String)
    supplier = Column(String)
    supplier_ref = Column(String)
    unit = Column(String)
    price = Column(Float)
    min_order = Column(String)
    spec = Column(Text)
    status = Column(String, default="active")


class Style(Base):
    """鞋款"""

    __tablename__ = "styles"
    id = Column(Integer, primary_key=True)
    ref_no = Column(String, unique=True, nullable=False)
    customer = Column(String)
    brand = Column(String)
    designer = Column(String)
    season = Column(String)
    category = Column(String)
    status = Column(String, default="draft")
    description = Column(Text)
    created_at = Column(DateTime, default=now)
    updated_at = Column(DateTime, default=now, onupdate=now)

    samples = relationship(
        "Sample", back_populates="style", cascade="all, delete-orphan"
    )
    spec_sheets = relationship(
        "SpecSheet", back_populates="style", cascade="all, delete-orphan"
    )
    milestones = relationship(
        "Milestone",
        back_populates="style",
        cascade="all, delete-orphan",
        order_by="Milestone.sequence",
    )


class Sample(Base):
    """樣本（每個開發階段一個）"""

    __tablename__ = "samples"
    id = Column(Integer, primary_key=True)
    style_id = Column(Integer, ForeignKey("styles.id"), nullable=False)
    stage = Column(String, nullable=False)  # development / confirmation / ...
    sample_no = Column(String)
    size = Column(String)
    status = Column(String)
    status_changed_at = Column(DateTime)  # status 最後一次變更時間
    requested_date = Column(String)
    received_date = Column(String)
    notes = Column(Text)

    style = relationship("Style", back_populates="samples")
    bom = relationship(
        "Bom", back_populates="sample", uselist=False, cascade="all, delete-orphan"
    )
    images = relationship(
        "SampleImage", back_populates="sample", cascade="all, delete-orphan"
    )
    costing = relationship(
        "Costing", back_populates="sample", uselist=False, cascade="all, delete-orphan"
    )


class Bom(Base):
    """物料清單（每個 Sample 一份）"""

    __tablename__ = "boms"
    id = Column(Integer, primary_key=True)
    sample_id = Column(Integer, ForeignKey("samples.id"), nullable=False)
    version = Column(Integer, default=1)
    notes = Column(Text)
    confirmed = Column(Boolean, default=False)

    sample = relationship("Sample", back_populates="bom")
    items = relationship(
        "BomItem",
        back_populates="bom",
        cascade="all, delete-orphan",
        order_by="BomItem.sort_order",
    )


class BomItem(Base):
    """BOM 行項目"""

    __tablename__ = "bom_items"
    id = Column(Integer, primary_key=True)
    bom_id = Column(Integer, ForeignKey("boms.id"), nullable=False)
    component_id = Column(Integer, ForeignKey("components.id"))
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=False)
    quantity = Column(Float)
    unit = Column(String)
    unit_cost = Column(Float)  # 物料單位成本（per unit）
    color = Column(String)
    supplier_ref = Column(String)
    remarks = Column(Text)
    sort_order = Column(Integer, default=0)

    bom = relationship("Bom", back_populates="items")
    component = relationship("Component")
    material = relationship("Material")


class SampleImage(Base):
    """樣本圖片"""

    __tablename__ = "sample_images"
    id = Column(Integer, primary_key=True)
    sample_id = Column(Integer, ForeignKey("samples.id"), nullable=False)
    filename = Column(String)
    caption = Column(String)
    image_type = Column(String)

    sample = relationship("Sample", back_populates="images")


class Costing(Base):
    """成本表（每個 Sample 一份，材料成本由 BOM 自動計）"""

    __tablename__ = "costings"
    id = Column(Integer, primary_key=True)
    sample_id = Column(Integer, ForeignKey("samples.id"), nullable=False, unique=True)
    labor = Column(Float, default=0)  # 加工費 CM（per pair）
    overhead_pct = Column(Float, default=0)  # 間接成本 %
    margin_pct = Column(Float, default=0)  # 利潤 %
    freight = Column(Float, default=0)  # 運費（per pair）
    mold_cost = Column(Float, default=0)  # 模具費（總額，攤銷落訂單量）
    order_qty = Column(Integer, default=0)  # 訂單量（for mold 攤銷）
    target_price = Column(Float)  # 目標售價
    currency = Column(String, default="USD")
    notes = Column(Text)

    sample = relationship("Sample", back_populates="costing")


class SpecSheet(Base):
    """客戶 PDF 規格表"""

    __tablename__ = "spec_sheets"
    id = Column(Integer, primary_key=True)
    style_id = Column(Integer, ForeignKey("styles.id"), nullable=False)
    filename = Column(String)
    parsed_json = Column(Text)  # JSON 字串，儲存解析結果
    uploaded_at = Column(DateTime, default=now)

    style = relationship("Style", back_populates="spec_sheets")


class Milestone(Base):
    """CPM 里程碑（每個 Style 一組關鍵日期，如訂單確認／物料到廠／出貨）"""

    __tablename__ = "milestones"
    id = Column(Integer, primary_key=True)
    style_id = Column(Integer, ForeignKey("styles.id"), nullable=False)
    name = Column(String, nullable=False)
    status = Column(String, default="pending")  # pending / in progress / done ...
    status_changed_at = Column(DateTime)  # status 最後一次變更時間
    planned_date = Column(String)  # 計劃日期
    actual_date = Column(String)  # 實際日期
    sequence = Column(Integer, default=0)  # 排序
    notes = Column(Text)

    style = relationship("Style", back_populates="milestones")


class StatusLog(Base):
    """狀態變更 audit log（邊個 entity 嘅 field 幾時由咩轉做咩）。"""

    __tablename__ = "status_logs"
    id = Column(Integer, primary_key=True)
    entity_type = Column(String, nullable=False)  # sample / milestone / style / bom
    entity_id = Column(Integer, nullable=False)
    ref_no = Column(String)  # 關聯嘅 Style ref（方便 display）
    field = Column(String, default="status")
    old_value = Column(String)
    new_value = Column(String)
    note = Column(Text)
    changed_at = Column(DateTime, default=now)
