from app.extensions import db
from sqlalchemy import func
from sqlalchemy.orm import relationship


class Printer(db.Model):
    __tablename__ = "printers"

    id = db.Column(db.Integer, primary_key=True, index=True)
    model_id = db.Column(db.Integer, db.ForeignKey("models.id"), nullable=False)
    building_id = db.Column(db.Integer, db.ForeignKey("buildings.id"), nullable=False, index=True)
    department_id = db.Column(db.Integer, db.ForeignKey("departments.id"), nullable=False, index=True)
    room_number = db.Column(db.String(10), nullable=False)
    printer_index = db.Column(db.Integer, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        db.UniqueConstraint('building_id', 'room_number', 'printer_index', name='uix_building_room_index'),
    )

    model = relationship("PrinterModel", back_populates="printers")
    building = relationship("Building", back_populates="printers")
    department = relationship("Department", back_populates="printers")
    print_events = relationship("PrintEvent", back_populates="printer")
