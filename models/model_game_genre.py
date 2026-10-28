from config import db

class GameGenre(db.Model):
    __tablename__ = "game_genres"
    game_id = db.Column(db.ForeignKey("games.id"), primary_key = True, nullable = False)
    genre_id = db.Column(db.ForeignKey("genres.id"), primary_key = True, nullable = False)
    
    rel_game = db.relationship("Game", back_populates="rel_game")
    rel_genre = db.relationship("Genre", back_populates="rel_genre")