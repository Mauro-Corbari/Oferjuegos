import smtplib
from email.message import EmailMessage
from models.model_currency import Currency
from flask import current_app
def enviar_mail(destinatario, asunto, mensaje):
    email = EmailMessage()
    email["From"] = current_app.config["MAIL_USERNAME"]
    email["To"] = destinatario
    email["Subject"] = asunto
    email.set_content(mensaje)
    with smtplib.SMTP(
        current_app.config["MAIL_SERVER"],
        current_app.config["MAIL_PORT"]
    ) as smtp:
        smtp.starttls()
        smtp.login(
            current_app.config["MAIL_USERNAME"],
            current_app.config["MAIL_PASSWORD"]
        )
        smtp.send_message(email)
def calcular_precios(listing):
    currency = listing.rel_store.rel_currency
    ars = Currency.query.filter_by(code="ars").first()
    discount = listing.discount or 0
    tax = listing.rel_store.tax
    precio_original = (
        listing.price_cents / 100
    )
    precio = precio_original * (
        (100 - discount) / 100
    )
    precio_convertido = (
        precio / currency.value
    ) * ars.value
    precio_final = (
        precio_convertido
        * (1 + tax / 100)
    )
    return {
        "precio_original": precio,
        "precio_convertido": precio_convertido,
        "precio_final": precio_final
    }