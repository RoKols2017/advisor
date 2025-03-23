from app.extensions import db
from sqlalchemy import func
from sqlalchemy.orm import relationship

class Port(db.Model):
    __tablename__ = "ports"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True, nullable=False, index=True)

    building_id = db.Column(db.Integer, db.ForeignKey("buildings.id"), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey("departments.id"), nullable=False)
    room_number = db.Column(db.String(50), nullable=False)
    printer_index = db.Column(db.Integer, nullable=False)

    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())

    building = relationship("Building")
    department = relationship("Department")
    print_events = relationship("PrintEvent", back_populates="port")
