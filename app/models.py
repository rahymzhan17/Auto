from decimal import Decimal

from .db import db
from .services import format_money


class Car(db.Model):
    __tablename__ = "cars"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(160), nullable=False)
    price = db.Column(db.Numeric(12, 2), nullable=False)
    image_url = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=db.func.now())

    def to_dict(self):
        amount = Decimal(self.price or 0)
        return {
            "id": self.id,
            "name": self.name,
            "price": str(amount),
            "price_display": format_money(amount),
            "image_url": self.image_url,
            "description": self.description,
        }
