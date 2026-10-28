from models.model_listing import Listing
from models.model_wishlist import Wishlist
from utils.notify import calcular_precios
from utils.notify import enviar_mail
from config import db
def revisar_wishlist(wishlist_item):
    if not wishlist_item.notify:
        return
    if wishlist_item.target_price_cents is None:
        return
    game = wishlist_item.rel_game
    listings = Listing.query.filter_by(
        game_id=game.id
    ).all()
    precio_objetivo = wishlist_item.target_price_cents
    for listing in listings:
        precios = calcular_precios(listing)
        precio_final_cents = round(
            precios["precio_final"] * 100
        )
        if precio_final_cents <= precio_objetivo:
            usuario = wishlist_item.rel_user
            enviar_mail(
                usuario.email,
                f"¡{game.title} alcanzó tu precio deseado!",
                f"""¡Buenas!

El juego {game.title} llegó a tu precio deseado en {listing.rel_store.name}.

Precio actual: ${precios["precio_final"]:.2f}
Precio deseado: ${precio_objetivo / 100:.2f}

Tienda: {listing.rel_store.name}

Podés ver la oferta acá:
{listing.url}

Saludos,
Oferjuegos
"""
            )
            wishlist_item.notify = False
            db.session.commit()
            break