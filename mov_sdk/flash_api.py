# coding=utf-8

import json
import requests

from .key import get_xpub
from .receiver import get_main_vapor_address

MOV_BASE_URL = "https://bcapi.movapi.com"
FLASH_BASE_URL = "https://flashswap.bystack.com"
FLASH_LOCAL_URL = "http://127.0.0.1:1024"


class FlashApi(object):

    def __init__(self, _secret_key, _local_url=FLASH_LOCAL_URL, network="mainnet"):
        self.headers = {
            'Content-Type': 'application/json; charset=utf-8',
            'Accept': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36'
        }

        self.session = requests.session()

        self.network = network
        self.main_address = ""
        self.vapor_address = ""
        self.secret_key = _secret_key
        self.guid = ""
        self.vapor_address = ""
        if self.secret_key:
            self.guid = self.get_guid_using_public_key()
            self.main_address, self.vapor_address = get_main_vapor_address(self.secret_key, self.network)

        self.local_url = _local_url

    @staticmethod
    def mov_format_symbol(symbol):
        return symbol.replace('_', '/').upper()

    def get_guid_using_public_key(self):
        url = "https://bcapi.bystack.com" + "/api/v2/btm/account/list-wallets"
        params = {
            "filter": {"type": "P2PKH"},
            "pubkey": get_xpub(self.secret_key)
        }
        data = self._request("POST", url, params)
        if data["result"]["data"]:
            self.guid = data["result"]["data"][0]["guid"]
        return self.guid

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
        url = FLASH_BASE_URL + "/api/v1/market-depth?symbol={}".format(symbol.replace('_', '/').upper())
        data = self._request("GET", url, {})
        return data

    def send_order(self, symbol, side, price, amount):
        url = self.local_url + "/api/v1/place-order"
        params = {"symbol": self.mov_format_symbol(symbol), "side": side, "price": str(price), "amount": str(amount)}
        data = self._request("POST", url, params)
        return data

    def cancel_order(self, symbol, side):
        '''
        新版已经不支持这个接口了
        '''
        url = self.local_url + "/api/v1/cancel-order"
        params = {"symbol": self.mov_format_symbol(symbol), "side": side}
        data = self._request("GET", url, params)
        return data

    def cancel_order_by_id(self, order_id):
        '''
        新版接口支持，旧版不支持
        '''
        url = self.local_url + "/api/v1/cancel-order"
        params = {"order_id": order_id}
        data = self._request("GET", url, params)
        return data

    def get_exchange_info(self):
        path = MOV_BASE_URL + "/magnet/v3/common/symbols"
        return self._request("GET", path, {})

    def get_balance(self):
        param = {"address": self.vapor_address}
        url = MOV_BASE_URL + "/vapor/v3/account/address"
        return self._request("GET", url, param)

    def get_orders(self, symbol, side):
        url = self.local_url + "/api/v1/orders?symbol={}&side={}".format(symbol, side)
        return self._request("GET", url, {})


if __name__ == "__main__":
    client = FlashApi("Your secret key", _local_url=FLASH_LOCAL_URL)
    print(client.send_order(symbol="btm_usdt", side="buy", price="0.0554", amount="4386.89"))
