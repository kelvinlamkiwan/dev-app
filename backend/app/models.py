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


class Sample(Base):
    """樣本（每個開發階段一個）"""

    __tablename__ = "samples"
    id = Column(Integer, primary_key=True)
    style_id = Column(Integer, ForeignKey("styles.id"), nullable=False)
    stage = Column(String, nullable=False)  # development / confirmation / ...
    sample_no = Column(String)
    size = Column(String)
    status = Column(String)
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
    cpm = Column(Float)  # Cost Per Material：物料單位成本
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


class SpecSheet(Base):
    """客戶 PDF 規格表"""

    __tablename__ = "spec_sheets"
    id = Column(Integer, primary_key=True)
    style_id = Column(Integer, ForeignKey("styles.id"), nullable=False)
    filename = Column(String)
    parsed_json = Column(Text)  # JSON 字串，儲存解析結果
    uploaded_at = Column(DateTime, default=now)

    style = relationship("Style", back_populates="spec_sheets")
