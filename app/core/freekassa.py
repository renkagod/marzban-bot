import hashlib
import urllib.parse

class FreeKassaClient:
    def __init__(self, shop_id: str, secret_1: str, secret_2: str):
        self.shop_id = shop_id
        self.secret_1 = secret_1
        self.secret_2 = secret_2
        self.base_url = "https://pay.fk.money/"

    def generate_payment_link(self, amount: float, order_id: str, currency: str = "RUB") -> str:
        # sign = md5(m:oa:o:currency:secret_word)
        sign_str = f"{self.shop_id}:{amount}:{order_id}:{currency}:{self.secret_1}"
        signature = hashlib.md5(sign_str.encode()).hexdigest()
        
        params = {
            "m": self.shop_id,
            "oa": amount,
            "o": order_id,
            "s": signature,
            "currency": currency,
            "i": 1 # Optional: first payment method selected
        }
        return f"{self.base_url}?{urllib.parse.urlencode(params)}"

    def verify_notification(self, data: dict) -> bool:
        # sign = md5(m:o:oa:currency:id:secret_word_2)
        # m = merchant_id, o = order_id, oa = amount, currency = currency, id = fk_transaction_id
        required = ['m', 'o', 'oa', 'currency', 's']
        if not all(k in data for k in required):
            return False
            
        # Note: transaction_id (id) is usually sent by FK in the notification
        fk_id = data.get('id', '')
        sign_str = f"{data['m']}:{data['o']}:{data['oa']}:{data['currency']}:{fk_id}:{self.secret_2}"
        calculated_sign = hashlib.md5(sign_str.encode()).hexdigest()
        
        return data['s'] == calculated_sign
