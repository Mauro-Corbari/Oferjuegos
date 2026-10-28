from config import db

class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key = True, autoincrement = True)
    email = db.Column(db.String(128), nullable = False, unique = True)
    pass_hash = db.Column(db.String(256), nullable = False)
    username = db.Column(db.String(32), nullable = False)
    admin = db.Column(db.Boolean, default=False)

    rel_wishlist = db.relationship("Wishlist", back_populates="rel_user", cascade="all, delete-orphan")
    rel_hidden = db.relationship("HiddenStore", back_populates="rel_user", cascade="all, delete-orphan")