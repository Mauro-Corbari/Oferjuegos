from flask import Flask
from config import init_app, db
from models.model_currency import Currency
from models.model_game import Game
from models.model_game_genre import GameGenre
from models.model_genre import Genre
from models.model_listing import Listing
from models.model_store import Store
from models.model_user import User
from models.model_wishlist import Wishlist
from models.model_hidden_stores import HiddenStore


app = Flask(__name__)
init_app(app)

with app.app_context():
    db.create_all()
    print("Base de datos 'oferjuegos.db' creada correctamente.")
