from config import db

class Currency(db.Model):
    __tablename__ = "currencies"

    code = db.Column(db.String(3), primary_key=True)
    value = db.Column(db.Float, nullable=False)

    rel_store = db.relationship("Store", back_populates="rel_currency")