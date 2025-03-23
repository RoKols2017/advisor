from app.extensions import db
from sqlalchemy import func
from sqlalchemy.orm import relationship
from datetime import datetime


class PrintEvent(db.Model):
    __tablename__ = "print_events"

    id = db.Column(db.Integer, primary_key=True, index=True)
    document_id = db.Column(db.Integer, nullable=False, index=True)
    document_name = db.Column(db.String(512), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    printer_id = db.Column(db.Integer, db.ForeignKey("printers.id"), nullable=False, index=True)
    job_id = db.Column(db.String(50), nullable=False, index=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    byte_size = db.Column(db.Integer, nullable=False)
    pages = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())
    computer_id = db.Column(db.Integer, db.ForeignKey("computers.id"), nullable=True)
    port_id = db.Column(db.Integer, db.ForeignKey("ports.id"), nullable=True)
    computer = relationship("Computer", back_populates="print_events")
    port = relationship("Port", back_populates="print_events")

    user = relationship("User", back_populates="print_events")
    printer = relationship("Printer", back_populates="print_events")
