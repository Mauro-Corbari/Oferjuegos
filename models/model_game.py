from config import db
from models.model_game_genre import GameGenre

class Game(db.Model):
    __tablename__ = "games"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.Text, nullable=False)
    slug = db.Column(db.String(128), nullable=False)
    image_url = db.Column(db.Text)
    
    rel_listing = db.relationship("Listing", back_populates="rel_game", cascade="all, delete-orphan")
    rel_wishlist = db.relationship("Wishlist", back_populates="rel_game", cascade="all, delete-orphan")
    rel_game = db.relationship("GameGenre", back_populates="rel_game", cascade="all, delete-orphan")