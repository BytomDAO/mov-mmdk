# coding=utf-8

import json
import requests

MOV_BASE_URL = "http://bcapi.blockmeta.com"
FLASH_BASE_URL = "http://flashswap.blockmeta.com"
FLASH_LOCAL_URL = "http://127.0.0.1:1024"


class FlashApi(object):

    def __init__(self, _guid, _local_url):
        self.guid = _guid
        self.local_url = _local_url

        self.headers = {
            'Content-Type': 'application/json; charset=utf-8',
            'Accept': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36'
        }

        self.session = requests.session()

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
        params = {"symbol": symbol.replace('_', '/').upper(), "side": side, "price": str(price), "amount": str(amount)}
        data = self._request("POST", url, params)
        return data

    def cancel_order(self, symbol, side):
        url = self.local_url + "/api/v1/cancel-order"
        params = {"symbol": symbol.replace('_', '/').upper(), "side": side}
        data = self._request("GET", url, params)
        return data

    def query_contract(self):
        url = MOV_BASE_URL + "/api/v2/vapor/mov/common/symbols"
        data = self._request("GET", url, {})
        return data


def testAccount1():
    client = FlashApi("dd0914eb-5d47-4364-9e30-6c4b728ac2b8", _local_url=FLASH_LOCAL_URL)
    # print(client.get_depth("btm_usdt"))
    # print(client.send_order(symbol="btm_usdt", side="sell", price="5", amount="0.3"))
    print(client.cancel_order(symbol="eth_usdt", side="buy"))
    print(client.cancel_order(symbol="eth_usdt", side="sell"))
    # print(client.query_balance())

    # print(client.send_order(symbol="eth_usdt", side="sell", price="0.33", amount="0.3"))
    # print(client.send_order(symbol="eth_usdt", side="buy", price="0.22", amount="1"))


def testAccount2():
    client = FlashApi("1fc375bb-afcb-4d83-9746-af76c9fb4c2e", _local_url="http://127.0.0.1:1025")
    # print(client.get_depth("btm_usdt"))
    print(client.cancel_order(symbol="eth_usdt", side="buy"))
    print(client.cancel_order(symbol="eth_usdt", side="sell"))
    # print(client.send_order(symbol="btm_usdt", side="sell", price="100", amount="0.7"))
    # print(client.send_order(symbol="btm_usdt", side="buy", price="0.01", amount="0.6"))
    # # #print(client.cancel_order(symbol="btm_usdt", side="buy"))
    # # print(client.query_balance())
    #
    # print(client.send_order(symbol="eth_usdt", side="sell", price="0.36", amount="0.6"))
    # print(client.send_order(symbol="eth_usdt", side="buy", price="0.233", amount="0.7"))


if __name__ == "__main__":
    # test()
    testAccount1()
    testAccount2()
