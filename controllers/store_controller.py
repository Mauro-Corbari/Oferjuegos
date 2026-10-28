from flask import Blueprint, render_template, session, redirect, url_for, flash
from config import db
from models.model_store import Store
from models.model_hidden_stores import HiddenStore
store_bp = Blueprint("store", __name__)
@store_bp.route("/stores")
def store_list():
    stores = Store.query.order_by(Store.name.asc()).all()
    if "user_id" in session:
        hidden_stores = {
            hidden.store_id
            for hidden in HiddenStore.query.filter_by(
                user_id=session["user_id"]
            ).all()
        }
    else:
        hidden_stores = set(session.get("hidden_stores", []))
    return render_template(
        "tiendas.html",
        stores=stores,
        hidden_stores=hidden_stores
    )
@store_bp.route("/stores/<int:store_id>/hide", methods=["POST"])
def hide_store(store_id):
    Store.query.get_or_404(store_id)
    if "user_id" in session:
        hidden = HiddenStore.query.filter_by(
            store_id=store_id,
            user_id=session["user_id"]
        ).first()
        if not hidden:
            hidden = HiddenStore(
                store_id=store_id,
                user_id=session["user_id"]
            )
            db.session.add(hidden)
            db.session.commit()
    else:
        hidden_stores = session.get("hidden_stores", [])
        if store_id not in hidden_stores:
            hidden_stores.append(store_id)
        session["hidden_stores"] = hidden_stores
    return redirect(url_for("store.store_list"))
@store_bp.route("/stores/<int:store_id>/unhide", methods=["POST"])
def unhide_store(store_id):
    Store.query.get_or_404(store_id)
    if "user_id" in session:
        hidden = HiddenStore.query.filter_by(
            store_id=store_id,
            user_id=session["user_id"]
        ).first()
        if hidden:
            db.session.delete(hidden)
            db.session.commit()
    else:
        hidden_stores = session.get("hidden_stores", [])
        if store_id in hidden_stores:
            hidden_stores.remove(store_id)
        session["hidden_stores"] = hidden_stores
    return redirect(url_for("store.store_list"))