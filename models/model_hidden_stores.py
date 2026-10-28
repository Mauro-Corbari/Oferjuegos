from config import db

class HiddenStore(db.Model):
    __tablename__ = "hidden_stores"
    store_id = db.Column(db.ForeignKey("stores.id"), primary_key = True, nullable = False)
    user_id = db.Column(db.ForeignKey("users.id"), primary_key = True, nullable = False)
    
    rel_user = db.relationship("User", back_populates="rel_hidden")
    rel_store = db.relationship("Store", back_populates="rel_hidden")