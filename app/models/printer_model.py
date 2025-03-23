from app.extensions import db
from sqlalchemy import func
from sqlalchemy.orm import relationship


class PrinterModel(db.Model):
    __tablename__ = "models"

    id = db.Column(db.Integer, primary_key=True, index=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    manufacturer = db.Column(db.String(100), nullable=False)
    model = db.Column(db.String(50), nullable=False)
    is_color = db.Column(db.Boolean, default=False)
    is_duplex = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())

    printers = relationship("Printer", back_populates="model")
