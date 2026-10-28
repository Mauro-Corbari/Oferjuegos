from flask_sqlalchemy import SQLAlchemy
from flask import Flask
import os
from dotenv import load_dotenv

db = SQLAlchemy()
load_dotenv()

def init_app(app):
    app.secret_key = "whythehelldoihavetodothisonethingforaloginsystem"
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///oferjuegos.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["MAIL_SERVER"] = "smtp.gmail.com"
    app.config["MAIL_PORT"] = 587
    app.config["MAIL_USERNAME"] = "oferjuegos.oficial@gmail.com"
    app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD")
    app.config["MAIL_USE_TLS"] = True
    db.init_app(app)
    print("Mail configurado:", bool(app.config["MAIL_PASSWORD"]))
    return app