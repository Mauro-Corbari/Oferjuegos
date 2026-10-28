from config import db

class Genre(db.Model):
    __tablename__ = "genres"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    genre = db.Column(db.String(64), nullable=False)
    
    rel_genre = db.relationship("GameGenre", back_populates="rel_genre", cascade="all, delete-orphan")


def obtener_generos():
    """Devuelve la lista de todos los géneros ordenados alfabéticamente."""
    return Genre.query.order_by(Genre.genre.asc()).all()