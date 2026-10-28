from config import db

class Store(db.Model):
    __tablename__ = "stores"
    id = db.Column(db.Integer, primary_key = True, autoincrement = True)
    name = db.Column(db.String(45), nullable = False)
    url = db.Column(db.Text, nullable = False)
    currency = db.Column(db.ForeignKey("currencies.code"), nullable = False)
    tax = db.Column(db.Integer, nullable = False)

    rel_listing = db.relationship("Listing", back_populates="rel_store", cascade="all, delete-orphan")
    rel_currency = db.relationship("Currency", back_populates="rel_store")
    rel_hidden = db.relationship("HiddenStore", back_populates="rel_store")