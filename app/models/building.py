from app.extensions import db
from sqlalchemy import func
from sqlalchemy.orm import relationship

class Building(db.Model):
    __tablename__ = "buildings"

    id = db.Column(db.Integer, primary_key=True, index=True)
    code = db.Column(db.String(10), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())

    printers = relationship("Printer", back_populates="building")
