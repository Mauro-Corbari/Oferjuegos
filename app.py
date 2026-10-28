from flask import Flask, render_template, session, redirect, url_for, g
from config import init_app, db
from sqlalchemy import func

from models.model_currency import Currency
from models.model_game import Game
from models.model_game_genre import GameGenre
from models.model_genre import Genre
from models.model_listing import Listing
from models.model_store import Store
from models.model_user import User
from models.model_wishlist import Wishlist
from models.model_hidden_stores import HiddenStore

from controllers.game_controller import game_bp
from controllers.user_controller import auth_bp
from controllers.store_controller import store_bp
from controllers.admin_controller import admin_bp
from currency_controller import update_ars

from utils.notify import enviar_mail
from utils.wishlist_notifications import revisar_wishlist

app = Flask(__name__)
init_app(app)

app.register_blueprint(game_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(store_bp)
app.register_blueprint(admin_bp)

@app.route("/")
def index():
    return redirect(url_for("game.game_list"))

@app.context_processor
def inject_user():
    user = None
    if "user_id" in session:
        user = User.query.get(session["user_id"])
    return dict(current_user=user)

if __name__ == "__main__":
    app.run(debug=True)