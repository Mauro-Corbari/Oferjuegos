from app import app
from config import db
from models.model_wishlist import Wishlist
from currency_controller import update_ars
from utils.wishlist_notifications import revisar_wishlist
with app.app_context():
    print("Actualizando dólar...")
    update_ars()
    print("Revisando Wishlists...")
    wishlist_items = Wishlist.query.filter_by(
        notify=True
    ).all()
    for wishlist_item in wishlist_items:
        revisar_wishlist(wishlist_item)
    print("Proceso terminado.")