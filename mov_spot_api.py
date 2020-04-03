# coding=utf-8

import json
import requests
from pybtm import key

REST_MARKET_HOST = "http://bcapi.blockmeta.com"
REST_TRADE_HOST = "http://bcapi.blockmeta.com"


class MovApi(object):

    def __init__(self, guid, secret_key):
        self.guid = guid
        self.secret_key = secret_key

        self.headers = {
            'Content-Type': 'application/json; charset=utf-8',
            'Accept': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36'
        }

        self.session = requests.session()

    def get_pub_key(self):
        return key.get_xpub(self.secret_key)

    def get_seed_from_mnemonic(self, mnemonic_str):
        return key.get_seed(mnemonic_str)

    def get_secret_key_from_seed(self, seed_str):
        return key.get_root_xprv(seed_str)

    def get_guid_using_public_key(self, public_key):
        url = REST_TRADE_HOST + "/api/v2/btm/account/list-wallets"
        params = {
            "filter": {"type": "P2PKH"},
            "pubkey": public_key
        }
        data = self._request("POST", url, params)
        guid = data["result"]["data"][0]["guid"]
        return guid

    def get_config_from_mnemonic(self, mnemonic_str):
        seed = self.get_seed_from_mnemonic(mnemonic_str)
        self.secret_key = self.get_secret_key_from_seed(seed)
        public_key = self.get_pub_key()
        self.guid = self.get_guid_using_public_key(public_key)
        return {"guid": self.guid, "secret_key": self.secret_key}

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

    def get_exchange_info(self):
        path = REST_MARKET_HOST + "/api/v2/vapor/mov/common/symbols"
        return self._request("GET", path, {})

    def get_depth(self, symbol, limit=5, decimal=5):
        path = REST_MARKET_HOST + "/api/v2/vapor/mov/market/depth?symbol={}&depth={}&decimal={}".format(symbol, limit,
                                                                                                        decimal)
        return self._request("GET", path, {})

    def _send_order_sign(self, url, data, mock="mock"):
        ret = []
        len_datas = len(data["result"]["data"])
        i = 0
        for info in data["result"]["data"]:
            i = i + 1
            raw_transaction = info["raw_transaction"]
            signing_instructions = info["signing_instructions"]

            arr = []
            for signing in signing_instructions:
                derivation_path = signing["derivation_path"]
                sign_data = signing["sign_data"]
                new_secret_key = key.get_child_xprv(self.secret_key, derivation_path)
                sign_data = [key.xprv_sign(new_secret_key, s) for s in sign_data]
                arr.append(sign_data)

            params = {
                "guid": self.guid,
                "raw_transaction": raw_transaction,
                "signatures": arr,
                "client_id": "123"
            }

            if i < len_datas:
                payment_url = REST_TRADE_HOST + "/api/v2/vapor/merchant/submit-payment"
                data = self._request("POST", payment_url, params)
            else:
                data = self._request("POST", url, params)

            ret.append(data)

        return ret

    def _send_cancel_sign(self, url, data, mock="mock"):
        raw_transaction = data["result"]["data"]["raw_transaction"]
        signing_instructions = data["result"]["data"]["signing_instructions"]

        arr = []
        for signing in signing_instructions:
            derivation_path = signing["derivation_path"]
            sign_data = signing["sign_data"]
            new_secret_key = key.get_child_xprv(self.secret_key, derivation_path)
            sign_data = [key.xprv_sign(new_secret_key, s) for s in sign_data]
            arr.append(sign_data)

        params = {
            "guid": self.guid,
            "raw_transaction": raw_transaction,
            "signatures": arr,
            "client_id": "123"
        }
        data = self._request("POST", url, params)
        return data

    def send_order(self, symbol, side, price, volume, mock="mock"):
        path = REST_TRADE_HOST + "/api/v2/vapor/mov/merchant/build-place-order-tx"
        params = {
            "guid": self.guid,
            "price": str(price),
            "amount": str(volume),
            "side": side,
            "symbol": symbol.replace('_', '/').upper()
        }
        data = self._request("POST", path, params)
        if data:
            path2 = REST_TRADE_HOST + "/api/v2/vapor/mov/merchant/submit-place-order-tx"
            return self._send_order_sign(path2, data, mock)

    def _cancel_order(self, order_id, mock="mock"):
        path1 = REST_TRADE_HOST + "/api/v2/vapor/mov/merchant/build-cancel-order-tx"
        params = {"guid": self.guid, "order_id": int(order_id)}
        data = self._request("POST", path1, params)
        if data:
            if str(data["code"]) == "200":
                path2 = REST_TRADE_HOST + "/api/v2/vapor/mov/merchant/submit-cancel-order-tx"
                data = self._send_cancel_sign(path2, data, mock)
                data["order_id"] = order_id
                return data
            else:
                data["order_id"] = order_id
                return data

    def cancel_order(self, order_id):
        return self._cancel_order(order_id)

    def query_balance(self):
        param = {"guid": self.guid}
        url = REST_TRADE_HOST + "/api/v2/vapor/account/list-addresses"
        return self._request("POST", url, param)

    def query_list_orders(self, order_id_list, states=["open", "partial", "canceled", "filled", "submitted"]):
        param = {
            "guid": self.guid,
            "side": "",
            "filter": {
                "states": states,
                "order_ids": [int(order_id) for order_id in order_id_list]
                # "states":[
                #     "open",
                #     "partial",#//部分成交
                #      "filled", #//完全成交
                #      "canceled",#//已取消
                #      "submitted" #//未上链
                # ]
            }
        }
        path = REST_TRADE_HOST + "/api/v2/vapor/mov/merchant/list-orders?limit=1000"

        return self._request("POST", path, param)

    def query_all_orders(self, symbol):
        param = {
            "guid": self.guid,
            "symbol": symbol,
            "side": "",
            "filter": {
                "states": [
                    # "submitted",
                    "open",
                    "partial"  # //部分成交
                ]
                # "states":[
                #     "open",
                #     "partial",#//部分成交
                #      "filled", #//完全成交
                #      "canceled",#//已取消
                #      "submitted" #//未上链
                # ]
            }
        }
        print(param)
        path = REST_TRADE_HOST + "/api/v2/vapor/mov/merchant/list-orders?limit=1000"

        return self._request("POST", path, param)

    def query_sell_orders(self, symbol):
        param = {
            "guid": self.guid,
            "symbol": symbol,
            "side": "sell",
            "filter": {
                "states": [
                    # "submitted",
                    "open",
                    "partial"  # //部分成交
                ]
                # "states":[
                #     "open",
                #     "partial",#//部分成交
                #      "filled", #//完全成交
                #      "canceled",#//已取消
                #      "submitted" #//未上链
                # ]
            }
        }
        path = REST_TRADE_HOST + "/api/v2/vapor/mov/merchant/list-orders?limit=1000"
        return self._request("POST", path, param)

    def query_buy_orders(self, symbol):
        param = {
            "guid": self.guid,
            "symbol": symbol,
            "side": "buy",
            "filter": {
                "states": [
                    # "submitted",
                    "open",
                    "partial"  # //部分成交
                ]
                # "states":[
                #     "open",
                #     "partial",#//部分成交
                #      "filled", #//完全成交
                #      "canceled",#//已取消
                #      "submitted" #//未上链
                # ]
            }
        }
        path = REST_TRADE_HOST + "/api/v2/vapor/mov/merchant/list-orders?limit=1000"

        return self._request("POST", path, param)


def test():
    api = MovApi(guid="",
                 secret_key="")
    # print(api.get_exchange_info())
    # print(api.query_buy_orders("BTM/ETH"))
    # print(api.query_sell_orders("BTM/ETH"))
    print(api.query_all_orders("BTC/USDT"))
    # print(api.query_list_orders([710941]))
    # print(api.cancel_order(710924))
    # print(api.get_depth("BTC/USDT", 5))
    # print(api.send_order(symbol="BTC/USDT", side="buy", price=6100, volume=0.01))
    # print(api.query_balance())


def test_get_from_mnemonic():
    api = MovApi(guid="", secret_key="")
    config = api.get_config_from_mnemonic("valid hole s vessel abc miss click payment fork nominee sock argue")
    print(config)

    print(api.query_balance())


if __name__ == "__main__":
    # test()
    test_get_from_mnemonic()
