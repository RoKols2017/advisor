from app.extensions import db
from sqlalchemy import func
from sqlalchemy.orm import relationship


class Department(db.Model):
    __tablename__ = "departments"

    id = db.Column(db.Integer, primary_key=True, index=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())

    users = relationship("User", back_populates="department")
    printers = relationship("Printer", back_populates="department")
