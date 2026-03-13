import requests
from django.conf import settings

class PaystackProvider:
    def __init__(self):
        self.secret_key = settings.PAYSTACK_SECRET_KEY
        self.base_url = "https://api.paystack.co"
        self.headers = {
            "Authorization": f"Bearer {self.secret_key}",
            "Content-Type": "application/json"
        }

    def initialize_transaction(self, email, amount, plan_code):
        url = f"{self.base_url}/transaction/initialize"
        data = {
            "email": email,
            "amount": str(amount),
            "plan": plan_code
        }
        response = requests.post(url, headers=self.headers, json=data)
        return response.json()

    def create_subscription(self, customer_code, plan_code):
        url = f"{self.base_url}/subscription"
        data = {
            "customer": customer_code,
            "plan": plan_code
        }
        response = requests.post(url, headers=self.headers, json=data)
        return response.json()

    def verify_transaction(self, reference):
        url = f"{self.base_url}/transaction/verify/{reference}"
        response = requests.get(url, headers=self.headers)
        return response.json()
