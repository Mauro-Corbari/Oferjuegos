from config import db

class Listing(db.Model):
    __tablename__ = "listings"
    id = db.Column(db.Integer, primary_key = True, autoincrement = True)
    game_id = db.Column(db.ForeignKey("games.id"), nullable = False)
    store_id = db.Column(db.ForeignKey("stores.id"), nullable = False)
    url = db.Column(db.Text, nullable = False)
    price_cents = db.Column(db.Integer, nullable = False)
    discount = db.Column(db.Integer)
    
    rel_game = db.relationship("Game", back_populates="rel_listing")
    rel_store = db.relationship("Store", back_populates="rel_listing")