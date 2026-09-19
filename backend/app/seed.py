from . import models
from .database import SessionLocal


def seed_data():
    db = SessionLocal()
    try:
        if db.query(models.Component).count() == 0:
            for name in [
                "Vamp", "Quarter", "Tongue", "Collar", "Sole", "Midsole",
                "Insole", "Lining", "Lace", "Eyelet", "Heel", "Toe Cap",
            ]:
                db.add(models.Component(name=name))

        if db.query(models.Material).count() == 0:
            for m in [
                {"material_code": "LEA-BLK-001", "name": "Cow Leather Black", "type": "leather", "color": "Black", "color_code": "#000000", "supplier": "Prime Asia", "unit": "sqft", "price": 2.5},
                {"material_code": "SYN-WHT-002", "name": "Synthetic PU White", "type": "synthetic", "color": "White", "color_code": "#FFFFFF", "supplier": "Nan Ya", "unit": "yard", "price": 1.8},
                {"material_code": "TEX-GRY-003", "name": "Mesh Textile Grey", "type": "textile", "color": "Grey", "color_code": "#888888", "supplier": "Li Peng", "unit": "yard", "price": 1.2},
                {"material_code": "RUB-WHT-004", "name": "Rubber Outsole White", "type": "rubber", "color": "White", "color_code": "#FFFFFF", "supplier": "Feng Tay", "unit": "pair", "price": 3.0},
                {"material_code": "EVA-WHT-005", "name": "EVA Midsole White", "type": "foam", "color": "White", "color_code": "#FFFFFF", "supplier": "Feng Tay", "unit": "pair", "price": 1.5},
                {"material_code": "MET-SLV-006", "name": "Metal Eyelet Silver", "type": "metal", "color": "Silver", "color_code": "#C0C0C0", "supplier": "YKK", "unit": "pcs", "price": 0.05},
            ]:
                db.add(models.Material(**m))

        db.commit()

        if db.query(models.Style).count() == 0:
            style = models.Style(
                ref_no="ZARA-SS26-001", customer="ZARA", brand="DEPORTIVOS",
                designer="Kelvin", season="SS26", category="Sneaker", status="development",
            )
            db.add(style)
            db.flush()

            sample = models.Sample(
                style_id=style.id, stage="development", sample_no="DEV-001",
                size="US9", status="in progress",
            )
            db.add(sample)
            db.flush()

            bom = models.Bom(sample_id=sample.id)
            db.add(bom)
            db.flush()

            comp = {c.name: c for c in db.query(models.Component).all()}
            mat = {m.name: m for m in db.query(models.Material).all()}

            db.add(models.BomItem(bom_id=bom.id, component_id=comp["Vamp"].id, material_id=mat["Cow Leather Black"].id, quantity=2.0, unit="sqft", cpm=2.5, color="Black", sort_order=1))
            db.add(models.BomItem(bom_id=bom.id, component_id=comp["Sole"].id, material_id=mat["Rubber Outsole White"].id, quantity=1.0, unit="pair", cpm=3.0, color="White", sort_order=2))
            db.add(models.BomItem(bom_id=bom.id, component_id=comp["Midsole"].id, material_id=mat["EVA Midsole White"].id, quantity=1.0, unit="pair", cpm=1.5, color="White", sort_order=3))
            db.commit()
    finally:
        db.close()
