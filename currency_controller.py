import requests
from config import db
from models.model_currency import Currency
def update_ars():
    response = requests.get(
        "https://dolarapi.com/v1/dolares/oficial",
        timeout=10
    )
    response.raise_for_status()
    data = response.json()
    ars = Currency.query.filter_by(code="ars").first()
    if ars:
        ars.value = data["venta"]
        db.session.commit()
        print(f"Dólar actualizado: ${data['venta']}")