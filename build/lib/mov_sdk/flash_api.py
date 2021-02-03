# coding=utf-8

import json
import requests

from .key import get_xpub
from .receiver import get_main_vapor_address

FLASH_BASE_URL = "https://ex.movapi.com"
FLASH_LOCAL_URL = "http://127.0.0.1:1024"


class FlashApi(object):
    def __init__(self, _local_url=FLASH_LOCAL_URL):
        self.headers = {
            'Content-Type': 'application/json; charset=utf-8',
            'Accept': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36'
        }

        self.session = requests.session()
        self.local_url = _local_url

    @staticmethod
    def mov_format_symbol(symbol):
        return symbol.replace('_', '/').upper()

    def _request(self, method, url, param):
        method = method.upper()
        if method in ["GET"]:
            result = self.session.get(url, params=param, timeout=5, headers=self.headers)
        else:
            encoded_data = json.dumps(param).encode('utf-8')
            result = self.session.post(url, data=encoded_data, timeout=5, headers=self.headers)

        if result:
            return result.json()
        else:
            return None

    def get_depth(self, symbol):
        url = FLASH_BASE_URL + "/flashswap/v3/market-depth?symbol={}".format(symbol.replace('_', '/').upper())
        data = self._request("GET", url, {})
        return data

    def send_order(self, symbol, side, price, amount):
        url = self.local_url + "/api/v1/place-order"
        params = {"symbol": self.mov_format_symbol(symbol), "side": side, "price": str(price), "amount": str(amount)}
        data = self._request("POST", url, params)
        return data

    def cancel_order_by_id(self, order_id):
        new_local_url = self.local_url.replace('127.0.0.1', 'localhost')
        url = new_local_url + "/api/v1/cancel-order?order_id={}".format(order_id)
        data = self._request("GET", url, {})
        return data

    def query_list_orders(self, symbol, side):
        symbol = self.mov_format_symbol(symbol)
        url = self.local_url + "/api/v1/orders?symbol={}&side={}".format(symbol, side)
        params = {}
        return self._request("GET", url, params)


if __name__ == "__main__":
    client = FlashApi("Your secret key", _local_url=FLASH_LOCAL_URL)
    print(client.send_order(symbol="btm_usdt", side="buy", price="0.0554", amount="4386.89"))
