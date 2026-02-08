import os

import requests


class ChapaService:
    def __init__(self):
        self.secret_key = os.getenv("CHAPA_SECRET_KEY")
        self.base_url = "https://api.chapa.co/v1/"
        self.headers = {
            "Authorization": f"Bearer {os.getenv('CHAPA_SECRET_KEY')}",
            "Content-Type": "application/json",
        }

    def initiate_payment(self, first_name, last_name, email, amount, tx_ref):
        url = f"{self.base_url}transaction/initialize"
        payload = {
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "amount": float(amount),
            "tx_ref": str(tx_ref),
            "currency": "ETB",
            "return_url": "http://127.0.0.1:8000/api/products/verify_payment/",
            "customization": {
                "title": "Payment for Product",
                "description": "Payment for purchasing a product",
            },
        }
        try:
            res = requests.post(url, json=payload, headers=self.headers)
            res.raise_for_status()
            return res.json()
        except requests.exceptions.RequestException as e:
            print(f"Error initiating payment: {e}")
            return {"status": "error", "message": str(e)}

    def verify_payment(self, tx_ref):
        url = self.base_url + f"transaction/verify/{tx_ref}"

        try:
            res = requests.get(url, headers=self.headers)
            res.raise_for_status()
            return res.json()
        except requests.exceptions.RequestException as e:
            print(f"Error verifying payment: {e}")
            return {"status": "error", "message": str(e)}
