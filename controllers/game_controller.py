from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from sqlalchemy import func
from flask_sqlalchemy.pagination import Pagination
from rapidfuzz import process, fuzz
from config import db
from models.model_genre import obtener_generos
from models.model_game import Game
from models.model_game_genre import GameGenre
from models.model_listing import Listing
from models.model_store import Store
from models.model_currency import Currency
from models.model_wishlist import Wishlist
from models.model_hidden_stores import HiddenStore
from utils.notify import calcular_precios
game_bp = Blueprint('game', __name__)
@game_bp.route('/games')
def game_list():
    if "user_id" in session:
        hidden_stores = {
            hidden.store_id
            for hidden in HiddenStore.query.filter_by(
                user_id=session["user_id"]
            ).all()
        }
    else:
        hidden_stores = set(session.get("hidden_stores", []))
    page = request.args.get('page', 1, type=int)
    search = request.args.get('q', '').strip()
    min_price = request.args.get("min_price", type=float)
    max_price = request.args.get("max_price", type=float)
    genero_id = request.args.get('genero_id', type=int)
    discount_filter = request.args.get("discount", type=int)
    print("MIN:", min_price)
    print("MAX:", max_price)
    generos = obtener_generos()
    games_query = Game.query
    per_page = 20
    if search:
        juegos = Game.query.all()
        search_lower = search.lower()
        coincidencias = [
            juego for juego in juegos
            if search_lower in juego.title.lower()
        ]
        if coincidencias:
            ids_encontrados = [
                juego.id
                for juego in coincidencias
            ]
        else:
            titulos = {
                juego.title: juego.id
                for juego in juegos
            }
            resultados = process.extract(
                search,
                titulos.keys(),
                scorer=fuzz.WRatio,
                score_cutoff=60,
                limit=per_page
            )
            ids_encontrados = [
                titulos[titulo]
                for titulo, score, _ in resultados
            ]
        games_query = games_query.filter(
            Game.id.in_(ids_encontrados)
        )
    if genero_id:
        games_query = games_query.join(GameGenre).filter(
            GameGenre.genre_id == genero_id
        )
    games_query = games_query.order_by(Game.title.asc())
    games = games_query.all()
    ars = Currency.query.filter_by(code="ars").first()
    juegos_con_precio = []
    for juego in games:
        precio_minimo = None
        has_discount = False
        has_free = False
        max_discount = 0
        for listing in juego.rel_listing:
            if listing.store_id in hidden_stores:
                continue
            if listing.discount is not None and listing.discount > 0:
                has_discount = True
            if listing.discount == 100:
                has_free = True
            if listing.discount is not None and listing.discount > max_discount:
                max_discount = listing.discount
            currency = listing.rel_store.rel_currency
            discount = listing.discount or 0
            precio = (
                listing.price_cents
                * ((100 - discount) / 100)
                / 100
            )
            precio_pesos = (precio / currency.value) * ars.value
            precio_final = (
                precio_pesos
                * (1 + listing.rel_store.tax / 100)
            )
            if precio_minimo is None or precio_final < precio_minimo:
                precio_minimo = precio_final
        juegos_con_precio.append({
            "title": juego.title,
            "slug": juego.slug,
            "image": juego.image_url.strip(),
            "price": precio_minimo,
            "has_discount": has_discount,
            "has_free": has_free,
            "discount": max_discount
        })
    if discount_filter == 1:
        juegos_con_precio = [
            juego for juego in juegos_con_precio
            if juego["has_discount"]
        ]
        print("\n--- DESPUÉS DEL FILTRO ---")
        for juego in juegos_con_precio:
            if juego["slug"] == "resident-evil-requiem":
                print("REQUiem SIGUE:", juego)
    elif discount_filter == 100:
        juegos_con_precio = [
            juego for juego in juegos_con_precio
            if juego["has_free"]
        ]
    precios = [
        juego["price"]
        for juego in juegos_con_precio
        if juego["price"] is not None
    ]
    precio_maximo = max(precios) if precios else 0
    precio_slider_max = (
        ((int(precio_maximo) + 99) // 100) * 100
        if precio_maximo > 0
        else 0
    )
    print(f"Precio maximo: ${precio_maximo}")
    if min_price is not None:
        juegos_con_precio = [
            juego for juego in juegos_con_precio
            if juego["price"] is not None
            and juego["price"] >= min_price
        ]
    if max_price is not None:
        juegos_con_precio = [
            juego for juego in juegos_con_precio
            if juego["price"] is not None
            and juego["price"] <= max_price
        ]
    total = len(juegos_con_precio)
    total_pages = (total + per_page - 1) // per_page
    inicio = (page - 1) * per_page
    fin = inicio + per_page
    juegos_con_precio = juegos_con_precio[inicio:fin]
    return render_template(
        'index.html',
        games=juegos_con_precio,
        search_query=search,
        generos=generos,
        genero_seleccionado=genero_id,
        max_price=precio_maximo,
        selected_max_price=max_price,
        slider_max_price=precio_slider_max,
        total_pages=total_pages,
        current_page=page
    )
@game_bp.route('/games/<slug>')
def game_details(slug):
    game = Game.query.filter_by(slug=slug).first_or_404()
    if "user_id" in session:
        in_wishlist = Wishlist.query.filter_by(
            user_id=session["user_id"],
            game_id=game.id
        ).first() is not None
    else:
        in_wishlist = False
    listings = Listing.query.filter_by(game_id=game.id)\
                            .join(Store)\
                            .all()
    if "user_id" in session:
        hidden_stores = {
            hidden.store_id
            for hidden in HiddenStore.query.filter_by(
                user_id=session["user_id"]
            ).all()
        }
    else:
        hidden_stores = set(session.get("hidden_stores", []))
    offertas = []
    for listing in listings:
        if listing.store_id in hidden_stores:
            continue
        currency = listing.rel_store.rel_currency
        tax = listing.rel_store.tax
        discount = listing.discount or 0
        ars = Currency.query.filter_by(code="ars").first()
        precios = calcular_precios(listing)
        offertas.append({
            'store_name': listing.rel_store.name,
            'store_url': listing.rel_store.url,
            'precio_original': precios["precio_original"],
            'precio_convertido': precios["precio_convertido"],
            'moneda': listing.rel_store.rel_currency.code,
            'impuesto': listing.rel_store.tax,
            'precio_final': precios["precio_final"],
            'descuento': discount,
            'url_juego': listing.url
        })
    offertas.sort(key=lambda o: o["precio_final"])
    print("USER ID:", session.get("user_id"))
    print("GAME ID:", game.id)
    print("IN WISHLIST:", in_wishlist)
    return render_template(
        'detalle_juego.html',
        game=game,
        ofertas=offertas,
        in_wishlist=in_wishlist
    )
@game_bp.route('/games/<slug>/wishlist', methods=['POST'])
def toggle_wishlist(slug):
    if "user_id" not in session:
        flash(
            "Tenés que iniciar sesión para usar la Wishlist.",
            "info"
        )
        return redirect(
            url_for("auth.auth", tab="login")
        )
    game = Game.query.filter_by(slug=slug).first_or_404()
    user_id = session["user_id"]
    wishlist_item = Wishlist.query.filter_by(
        user_id=user_id,
        game_id=game.id
    ).first()
    if wishlist_item:
        db.session.delete(wishlist_item)
        flash(
            f"{game.title} fue eliminado de tu Wishlist.",
            "info"
        )
    else:
        wishlist_item = Wishlist(
            user_id=user_id,
            game_id=game.id
        )
        db.session.add(wishlist_item)
        flash(
            f"{game.title} fue agregado a tu Wishlist.",
            "info"
        )
    db.session.commit()
    return redirect(
        url_for(
            "game.game_details",
            slug=game.slug
        )
    )
@game_bp.route('/wishlist')
def wishlist():
    if "user_id" not in session:
        flash(
            "Tenés que iniciar sesión para ver tu Wishlist.",
            "info"
        )
        return redirect(
            url_for("auth.auth", tab="login")
        )
    wishlist_items = Wishlist.query.filter_by(
        user_id=session["user_id"]
    ).all()
    games = [
        item.rel_game
        for item in wishlist_items
    ]
    return render_template(
        "wishlist.html",
        wishlist_items=wishlist_items
    )
@game_bp.route('/games/<slug>/wishlist/config', methods=['POST'])
def configure_wishlist(slug):
    if "user_id" not in session:
        flash(
            "Tenés que iniciar sesión para configurar tu Wishlist.",
            "info"
        )
        return redirect(url_for("auth.auth", tab="login"))
    game = Game.query.filter_by(slug=slug).first_or_404()
    wishlist_item = Wishlist.query.filter_by(
        user_id=session["user_id"],
        game_id=game.id
    ).first_or_404()
    target_price = request.form.get("target_price", "").strip()
    notify = request.form.get("notify") == "on"
    if target_price:
        try:
            target_price_cents = round(float(target_price) * 100)
        except ValueError:
            flash("El precio objetivo no es válido.", "danger")
            return redirect(
                url_for("game.wishlist")
            )
    else:
        target_price_cents = None
    wishlist_item.target_price_cents = target_price_cents
    wishlist_item.notify = notify
    db.session.commit()
    flash(
        f"Configuración de {game.title} actualizada.",
        "success"
    )
    return redirect(
        url_for("game.wishlist")
    )