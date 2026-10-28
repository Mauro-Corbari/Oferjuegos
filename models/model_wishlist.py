from config import db

class Wishlist(db.Model):
    __tablename__ = "wishlists"
    user_id = db.Column(db.ForeignKey("users.id"), primary_key = True, nullable = False)
    game_id = db.Column(db.ForeignKey("games.id"), primary_key = True, nullable = False)
    target_price_cents = db.Column(db.Integer)
    notify = db.Column(db.Boolean, default = False)
    
    rel_user = db.relationship("User", back_populates="rel_wishlist")
    rel_game = db.relationship("Game", back_populates="rel_wishlist")