from functools import wraps
from flask import Blueprint, render_template, redirect, url_for, session, flash, request, jsonify
from sqlalchemy.exc import IntegrityError
from config import db
from models.model_user import User
from models.model_game import Game
from models.model_genre import Genre
from models.model_game_genre import GameGenre
from models.model_listing import Listing
from models.model_store import Store
from models.model_currency import Currency
import os
import requests
from PIL import Image

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Tenés que iniciar sesión para acceder al panel de administración.", "info")
            return redirect(url_for("auth.auth", tab="login"))
        user = db.session.get(User, session["user_id"])
        if not user or not user.admin:
            flash("No tenés permisos para acceder al panel de administración.", "danger")
            return redirect(url_for("index"))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route("/")
@admin_required
def admin_panel():
    return render_template("admin.html")

@admin_bp.route("/games/search")
@admin_required
def search_games():
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify([])
    games = (
        Game.query
        .filter(Game.title.ilike(f"%{query}%"))
        .order_by(Game.title.asc())
        .limit(20)
        .all()
    )
    return jsonify([
        {
            "id": game.id,
            "title": game.title,
            "image": game.image_url
        }
        for game in games
    ])

@admin_bp.route("/games/<int:game_id>")
@admin_required
def get_game(game_id):
    game = db.session.get(Game, game_id)
    if not game:
        return jsonify({"error": "Juego no encontrado."}), 404
    genres = [
        {
            "id": relation.genre_id,
            "name": relation.rel_genre.genre
        }
        for relation in game.rel_game
    ]
    listings = [
        {
            "id": listing.id,
            "store_id": listing.store_id,
            "store_name": listing.rel_store.name,
            "currency": listing.rel_store.currency,
            "price_cents": listing.price_cents,
            "discount": listing.discount or 0,
            "url": listing.url
        }
        for listing in game.rel_listing
    ]
    return jsonify({
        "id": game.id,
        "title": game.title,
        "slug": game.slug,
        "image_url": game.image_url,
        "genres": genres,
        "listings": listings
    })

@admin_bp.route("/data")
@admin_required
def admin_data():
    genres = Genre.query.order_by(Genre.genre.asc()).all()
    stores = Store.query.order_by(Store.name.asc()).all()
    return jsonify({
        "genres": [
            {
                "id": genre.id,
                "name": genre.genre
            }
            for genre in genres
        ],
        "stores": [
            {
                "id": store.id,
                "name": store.name,
                "currency": store.currency
            }
            for store in stores
        ]
    })
@admin_bp.route("/stores")
@admin_required
def get_stores():
    stores = Store.query.order_by(Store.name.asc()).all()

    return jsonify([
        {
            "id": store.id,
            "name": store.name,
            "url": store.url,
            "currency": store.currency,
            "tax": store.tax
        }
        for store in stores
    ])
@admin_bp.route("/currencies")
@admin_required
def get_currencies():
    currencies = Currency.query.order_by(Currency.code.asc()).all()

    return jsonify([
        {
            "code": currency.code
        }
        for currency in currencies
    ])
@admin_bp.route("/stores/create", methods=["POST"])
@admin_required
def create_store():
    data = request.get_json()

    if not data:
        return jsonify({"error": "No se recibieron datos."}), 400

    name = data.get("name", "").strip()
    url = data.get("url", "").strip()
    currency = data.get("currency", "").strip()
    tax = data.get("tax")

    if not name:
        return jsonify({"error": "El nombre de la tienda es obligatorio."}), 400

    if not url:
        return jsonify({"error": "La URL de la tienda es obligatoria."}), 400

    if not currency:
        return jsonify({"error": "La moneda es obligatoria."}), 400

    if tax is None:
        return jsonify({"error": "El impuesto es obligatorio."}), 400

    store = Store(
        name=name,
        url=url,
        currency=currency,
        tax=tax
    )

    try:
        db.session.add(store)
        db.session.commit()

        return jsonify({
            "success": True,
            "id": store.id,
            "name": store.name,
            "url": store.url,
            "currency": store.currency,
            "tax": store.tax
        })
    except Exception as error:
        db.session.rollback()
        print("ERROR:", error)
        return jsonify({"error": "No se pudo crear la tienda."}), 500
@admin_bp.route("/stores/save", methods=["POST"])
@admin_required
def save_store():
    data = request.get_json()

    if not data:
        return jsonify({"error": "No se recibieron datos."}), 400

    store_id = data.get("id")
    name = data.get("name", "").strip()
    url = data.get("url", "").strip()
    currency = data.get("currency", "").strip()
    tax = data.get("tax")

    if not store_id:
        return jsonify({"error": "No se indicó la tienda."}), 400

    if not name:
        return jsonify({"error": "El nombre de la tienda es obligatorio."}), 400

    if not url:
        return jsonify({"error": "La URL de la tienda es obligatoria."}), 400

    if not currency:
        return jsonify({"error": "La moneda es obligatoria."}), 400

    if tax is None:
        return jsonify({"error": "El impuesto es obligatorio."}), 400

    store = db.session.get(Store, store_id)

    if not store:
        return jsonify({"error": "Tienda no encontrada."}), 404

    store.name = name
    store.url = url
    store.currency = currency
    store.tax = tax

    try:
        db.session.commit()
        return jsonify({"success": True})
    except Exception as error:
        db.session.rollback()
        print("ERROR:", error)
        return jsonify({"error": "No se pudieron guardar los cambios."}), 500
@admin_bp.route("/stores/<int:store_id>", methods=["DELETE"])
@admin_required
def delete_store(store_id):
    store = db.session.get(Store, store_id)

    if not store:
        return jsonify({"error": "Tienda no encontrada."}), 404

    try:
        for listing in store.rel_listing:
            db.session.delete(listing)

        db.session.delete(store)
        db.session.commit()

        return jsonify({"success": True})
    except Exception:
        db.session.rollback()
        return jsonify({"error": "No se pudo borrar la tienda."}), 500
@admin_bp.route("/stores/<int:store_id>")
@admin_required
def get_store(store_id):
    store = db.session.get(Store, store_id)

    if not store:
        return jsonify({"error": "Tienda no encontrada."}), 404

    return jsonify({
        "id": store.id,
        "name": store.name,
        "url": store.url,
        "currency": store.currency,
        "tax": store.tax
    })
@admin_bp.route("/genres/create", methods=["POST"])
@admin_required
def create_genre():
    data = request.get_json()

    if not data:
        return jsonify({"error": "No se recibieron datos."}), 400

    name = data.get("name", "").strip()
    game_ids = data.get("games", [])

    if not name:
        return jsonify({"error": "El nombre del género es obligatorio."}), 400

    genre = Genre(genre=name)

    try:
        db.session.add(genre)
        db.session.flush()

        for game_id in game_ids:
            game = db.session.get(Game, game_id)

            if not game:
                db.session.rollback()
                return jsonify({
                    "error": f"El juego con ID {game_id} no existe."
                }), 404

            db.session.add(
                GameGenre(
                    game_id=game.id,
                    genre_id=genre.id
                )
            )

        db.session.commit()

        return jsonify({
            "success": True,
            "id": genre.id,
            "name": genre.genre
        })
    except Exception as error:
        db.session.rollback()
        print("ERROR:", error)
        return jsonify({"error": "No se pudo crear el género."}), 500
@admin_bp.route("/genres/<int:genre_id>")
@admin_required
def get_genre(genre_id):
    genre = db.session.get(Genre, genre_id)
    if not genre:
        return jsonify({"error": "Género no encontrado."}), 404

    return jsonify({
        "id": genre.id,
        "name": genre.genre,
        "games": [
            {
                "id": relation.game_id,
                "title": relation.rel_game.title
            }
            for relation in genre.rel_genre
        ]
    })
@admin_bp.route("/genres/save", methods=["POST"])
@admin_required
def save_genre():
    import json
    data = request.get_json()

    if not data:
        return jsonify({"error": "No se recibieron datos."}), 400

    genre_id = data.get("id")
    name = data.get("name", "").strip()
    game_ids = data.get("games", [])

    if not genre_id:
        return jsonify({"error": "No se indicó el género."}), 400

    if not name:
        return jsonify({"error": "El nombre del género es obligatorio."}), 400
    genre = db.session.get(Genre, genre_id)

    if not genre:
        return jsonify({"error": "El género no existe."}), 404

    genre.genre = name
    GameGenre.query.filter_by(genre_id=genre.id).delete()

    for game_id in game_ids:
        game = db.session.get(Game, game_id)

        if not game:
            return jsonify({
                "error": f"El juego con ID {game_id} no existe."
            }), 404

        db.session.add(
            GameGenre(
                game_id=game.id,
                genre_id=genre.id
            )
        )
    try:
        db.session.commit()
    except Exception as error:
        db.session.rollback()
        print("ERROR:", error)
        return jsonify({"error": "No se pudieron guardar los cambios."}), 500

    return jsonify({"success": True})
@admin_bp.route("/genres/<int:genre_id>", methods=["DELETE"])
@admin_required
def delete_genre(genre_id):
    genre = db.session.get(Genre, genre_id)

    if not genre:
        return jsonify({"error": "Género no encontrado."}), 404

    try:
        db.session.delete(genre)
        db.session.commit()

        return jsonify({"success": True})
    except Exception as error:
        db.session.rollback()
        print("ERROR:", error)
        return jsonify({"error": "No se pudo eliminar el género."}), 500
@admin_bp.route("/genres/games/search")
@admin_required
def search_genre_games():
    query = request.args.get("q", "").strip()

    if not query:
        return jsonify([])

    games = (
        Game.query
        .filter(Game.title.ilike(f"%{query}%"))
        .order_by(Game.title.asc())
        .limit(20)
        .all()
    )

    return jsonify([
        {
            "id": game.id,
            "title": game.title
        }
        for game in games
    ])
@admin_bp.route("/games/save", methods=["POST"])
@admin_required
def save_game():
    data = request.form.get("data")
    if not data:
        return jsonify({"error": "No se recibieron datos."}), 400

    import json
    try:
        data = json.loads(data)
    except json.JSONDecodeError:
        return jsonify({"error": "Los datos recibidos no son válidos."}), 400
    game_id = data.get("id")
    title = data.get("title", "").strip()
    slug = data.get("slug", "").strip()
    image_url = data.get("image_url", "").strip()
    genre_ids = data.get("genres", [])
    listings = data.get("listings", [])
    image_file = request.files.get("image")
    if not image_file and image_url:
        try:
            response = requests.get(image_url, timeout=10)
            response.raise_for_status()

            from io import BytesIO
            image_file = BytesIO(response.content)
        except requests.RequestException:
            return jsonify({"error": "No se pudo descargar la imagen desde la URL."}), 400
    if image_file:
        try:
            image = Image.open(image_file)
            image.verify()
            image_file.seek(0)
            image = Image.open(image_file)
            image_format = image.format.lower()
        except Exception:
            return jsonify({"error": "El archivo recibido no es una imagen válida."}), 400
    image_path = None
    if image_file:
        extension = "jpg" if image_format == "jpeg" else image_format
        filename = f"{slug}.{extension}"
        image_path = os.path.join("static", "images", filename)
        image.save(image_path)
#    if not image_file:
#        return jsonify({"error": "El juego debe tener una imagen."}), 400
    if not title:
        return jsonify({"error": "El título del juego es obligatorio."}), 400
    if not slug:
        return jsonify({"error": "El slug es obligatorio."}), 400
    print("GAME ID:", game_id)
    print("IMAGE FILE:", bool(image_file))
    try:
        if game_id:
            game = db.session.get(Game, game_id)
            if not game:
                return jsonify({"error": "El juego no existe."}), 404
        else:
            if not image_file:
                return jsonify({"error": "El juego debe tener una imagen."}), 400

            game = Game()
            game.title = title
            game.slug = slug
            db.session.add(game)
        existing_slug = Game.query.filter(Game.slug == slug).first()

        if existing_slug and existing_slug.id != game.id:
            return jsonify({"error": "Ya existe un juego con ese slug."}), 409
        game.title = title
        game.slug = slug
        if image_path:
            game.image_url = f"/static/images/{filename}"
        elif image_url:
            game.image_url = image_url
        game.rel_game.clear()
        for genre_id in genre_ids:
            genre = db.session.get(Genre, genre_id)
            if not genre:
                raise ValueError(f"El género con ID {genre_id} no existe.")
            game.rel_game.append(GameGenre(genre_id=genre.id))
        if game_id:
            game.rel_listing.clear()
        for listing_data in listings:
            store_id = listing_data.get("store_id")
            price_cents = listing_data.get("price_cents")
            discount = listing_data.get("discount", 0)
            url = listing_data.get("url", "").strip()
            if not store_id:
                raise ValueError("Todos los listados deben tener una tienda.")
            if price_cents is None:
                raise ValueError("Todos los listados deben tener un precio.")
            if not url:
                raise ValueError("Todos los listados deben tener una URL.")
            store = db.session.get(Store, store_id)
            if not store:
                raise ValueError(f"La tienda con ID {store_id} no existe.")
            try:
                price_cents = int(price_cents)
                discount = int(discount or 0)
            except (TypeError, ValueError):
                raise ValueError("El precio y el descuento deben ser números.")
            if price_cents < 0:
                raise ValueError("El precio no puede ser negativo.")
            if discount < 0 or discount > 100:
                raise ValueError("El descuento debe estar entre 0 y 100.")
            game.rel_listing.append(
                Listing(
                    store_id=store.id,
                    url=url,
                    price_cents=price_cents,
                    discount=discount
                )
            )
        db.session.commit()
        return jsonify({
            "success": True,
            "id": game.id
        })
    except ValueError as error:
        db.session.rollback()
        return jsonify({"error": str(error)}), 400
    except IntegrityError as error:
        db.session.rollback()
        print("INTEGRITY ERROR:", error)
        return jsonify({"error": str(error.orig)}), 409
    except Exception as error:
        db.session.rollback()
        print("ERROR:", error)
        return jsonify({"error": str(error)}), 500
@admin_bp.route("/games/<int:game_id>", methods=["DELETE"])
@admin_required
def delete_game(game_id):
    game = db.session.get(Game, game_id)
    if not game:
        return jsonify({"error": "Juego no encontrado."}), 404
    try:
        for relation in game.rel_game:
            db.session.delete(relation)

        db.session.delete(game)
        db.session.commit()
        return jsonify({"success": True})
    except Exception:
        db.session.rollback()
        return jsonify({"error": "No se pudo eliminar el juego."}), 500
@admin_bp.route("/users")
@admin_required
def admin_users():
    users = User.query.order_by(User.username.asc()).all()

    return jsonify([
        {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "admin": user.admin
        }
        for user in users
    ])


@admin_bp.route("/users/<int:user_id>/toggle-admin", methods=["POST"])
@admin_required
def toggle_admin(user_id):
    user = db.session.get(User, user_id)

    if not user:
        return jsonify({"error": "El usuario no existe."}), 404

    if user.admin:
        admin_count = User.query.filter_by(admin=True).count()

        if admin_count <= 1:
            return jsonify({
                "error": "No podés quitar el permiso al último administrador."
            }), 400

    user.admin = not user.admin
    db.session.commit()

    return jsonify({
        "success": True,
        "admin": user.admin
    })