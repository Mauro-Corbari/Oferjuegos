from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from config import db
from models.model_user import User
auth_bp = Blueprint("auth", __name__)
@auth_bp.route("/auth", methods=["GET", "POST"])
def auth():
    tab = request.args.get("tab", "login")
    if request.method == "POST":
        if "login" in request.form:
            email = request.form["email"]
            password = request.form["password"]
            user = User.query.filter_by(email=email).first()
            if user and check_password_hash(user.pass_hash, password):
                session["user_id"] = user.id
                session["username"] = user.username
                flash(f"Bienvenido, {user.username}.", "info")
                return redirect(url_for("index"))
            flash("Correo o contraseña incorrectos.", "info")
            tab = "login"
        elif "register" in request.form:
            username = request.form["username"]
            email = request.form["email"].strip().lower()
            password = request.form["password"]
            password_confirm = request.form["password_confirm"]
            if password != password_confirm:
                flash("Las contraseñas no coinciden.", "info")
                tab = "register"
            elif User.query.filter_by(email=email).first():
                flash("Ese correo ya está registrado.", "info")
                tab = "register"
            else:
                user = User(
                    username=username,
                    email=email,
                    pass_hash=generate_password_hash(password)
                )
                db.session.add(user)
                db.session.commit()
                flash("Registro exitoso. Ya podés iniciar sesión.", "info")
                tab = "login"
        elif "delete_account" in request.form:
            email = request.form["delete_email"].strip().lower()
            password = request.form["delete_password"]
            password_confirm = request.form["delete_password_confirm"]

            if password != password_confirm:
                flash("Las contraseñas no coinciden.", "info")
                tab = "delete"
            else:
                user = User.query.filter_by(email=email).first()

                if not user or not check_password_hash(user.pass_hash, password):
                    flash("Correo o contraseña incorrectos.", "info")
                    tab = "delete"
                elif user.admin and User.query.filter_by(admin=True).count() <= 1:
                    flash("No podés eliminar la cuenta del último administrador.", "danger")
                    tab = "delete"
                else:
                    db.session.delete(user)
                    db.session.commit()
                    session.clear()
                    flash("Tu cuenta fue eliminada correctamente.", "info")
                    return redirect(url_for("index"))
    return render_template("auth.html", tab=tab)
@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("Sesión cerrada.", "info")
    return redirect(url_for("auth.auth"))