# coding=utf-8

import hashlib
import json
import time
import requests
from collections import defaultdict
from pprint import pprint
from .key import xprv_my_sign
from .key import get_xpub, get_child_xpub, get_seed, get_child_xprv, get_root_xprv, xprv_sign
from .key import get_entropy, get_mnemonic
from .receiver import get_main_vapor_address, get_public_key
from .utxo_manager import address_to_script, Net, Chain

MOV_REST_TRADE_HOST = "https://ex.movapi.com"
SUPER_REST_TRADE_HOST = "https://supertx.movapi.com"


# networks = ["mainnet", "testnet", "solonet"]

derivation_path = ['2c000000', '99000000', '01000000', '00000000', '01000000']


class MovApi(object):
    def __init__(self, secret_key="", network=Net.MAIN.value, third_address="", third_public_key="", mnemonic_str="",
                 _MOV_REST_TRADE_HOST="", _BYCOIN_URL="", _SUPER_REST_TRADE_HOST="", _third_use_child=False,
                 _bitcoin_address="", _third_main_address=""):
        self.headers = {
            'Content-Type': 'application/json; charset=utf-8',
            'Accept': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36'
        }
        if _MOV_REST_TRADE_HOST:
            self.host = _MOV_REST_TRADE_HOST
            self.bycoin_url = _MOV_REST_TRADE_HOST
            self.flash_url = _MOV_REST_TRADE_HOST
        else:
            self.host = MOV_REST_TRADE_HOST
            self.bycoin_url = MOV_REST_TRADE_HOST
            self.flash_url = MOV_REST_TRADE_HOST

        if _BYCOIN_URL:
            self.bycoin_url = _BYCOIN_URL

        if _SUPER_REST_TRADE_HOST:
            self.super_url = _SUPER_REST_TRADE_HOST
        else:
            self.super_url = SUPER_REST_TRADE_HOST

        self.session = requests.session()

        self.network = network
        self.main_address = ""
        self.bytom_script = ""
        self.vapor_address = ""
        self.vapor_script = ""
        self.public_key = ""
        self.child_secret_key = ""

        self.bitcoin_address = _bitcoin_address

        self.mnemonic_str = mnemonic_str
        self.third_address = third_address
        self.third_main_address = _third_main_address
        self.third_public_key = third_public_key
        self.third_use_child = _third_use_child

        self.set_third_info()

        if secret_key:
            self.secret_key = secret_key
            self.init()
        elif self.mnemonic_str:
            self.init_from_mnemonic(mnemonic_str)
        else:
            self.secret_key = self.get_new_secret_key()

        self.asset_id_dict = {}
        self.decimal_dict = {}
        self.id_asset_dict = {}
        self.all_pairs = set([])
        self.get_all_pairs()

    def get_all_pairs(self):
        '''
        获得所有交易对信息
        :return:
        '''
        if not self.all_pairs:
            for exchange, data in [("mov", self.get_exchange_info()), ("super", self.get_super_exchange_info())]:
                if data:
                    for dic in data["data"]:
                        base_asset = dic["base_asset"]
                        quote_asset = dic["quote_asset"]
                        symbol = (base_asset["symbol"] + "/" + quote_asset["symbol"]).upper()
                        if exchange == "mov":
                            self.all_pairs.add(symbol)
                        self.asset_id_dict[base_asset["symbol"].upper()] = base_asset["asset_id"]
                        self.asset_id_dict[quote_asset["symbol"].upper()] = quote_asset["asset_id"]

                        self.id_asset_dict[base_asset["asset_id"]] = base_asset["symbol"].upper()
                        self.id_asset_dict[quote_asset["asset_id"]] = quote_asset["symbol"].upper()

            data = self.get_assets()
            if data:
                for dic in data["data"]:
                    self.asset_id_dict[dic["symbol"].upper()] = dic["asset_id"]
                    self.id_asset_dict[dic["asset_id"]] = dic["symbol"].upper()
                    self.decimal_dict[dic["asset_id"]] = dic["decimals"]

        return self.all_pairs

    def get_min_volume(self, asset):
        asset_id = self.asset_id_dict[asset.upper()]
        decimal_val = self.decimal_dict[asset_id]
        return 0.1 ** decimal_val

    def get_new_secret_key(self):
        '''
        获得一个新的私钥
        :return:
        '''
        entropy_hexstr = get_entropy()
        self.mnemonic_str = get_mnemonic(entropy_hexstr)
        return self.init_from_mnemonic(self.mnemonic_str)

    def init_from_mnemonic(self, nemonic_str):
        '''
        使用助记词来初始化
        :param nemonic_str:
        :return:
        '''
        self.secret_key = self.get_secret_key_from_mnemonic(nemonic_str)
        self.init()
        return self.secret_key

    def set_third_info(self):
        '''
        设置托管做市信息
        :return:
        '''
        if self.third_address:
            self.vapor_address = self.third_address
            self.vapor_script = address_to_script(Chain.VAPOR.value, self.vapor_address, self.network)
        if self.third_public_key:
            self.public_key = self.third_public_key

    def init(self):
        '''
        初始化
        :return:
        '''
        if self.secret_key:
            self.main_address, self.vapor_address = get_main_vapor_address(self.secret_key, self.network)
            self.bytom_script = address_to_script(Chain.BYTOM.value, self.main_address, self.network)
            self.vapor_script = address_to_script(Chain.VAPOR.value, self.vapor_address, self.network)
            self.public_key = self.get_child_pub_key()
            self.child_secret_key = get_child_xprv(self.secret_key, derivation_path)
            self.set_third_info()

    def _request(self, method, url, param):
        try:
            method = method.upper()
            if method in ["GET"]:
                result = self.session.get(url, params=param, timeout=7, headers=self.headers)
            else:
                encoded_data = json.dumps(param).encode('utf-8')
                result = self.session.post(url, data=encoded_data, timeout=7, headers=self.headers)

            if result.status_code != requests.codes.ok:
                print(result.status_code, result.text)
            if result:
                return result.json()
            else:
                return None
        except Exception as ex:
            print("timeout", ex)
        return None

    def get_child_pub_key(self):
        '''
        获得派生公钥
        :return:
        '''
        xpub_hexstr = get_xpub(self.secret_key)
        child_xpub = get_child_xpub(xpub_hexstr, derivation_path)
        return get_public_key(child_xpub)

    def get_secret_key_from_mnemonic(self, mnemonic_str):
        '''
        通过助记词获得私钥
        :param mnemonic_str:
        :return:
        '''
        seed = get_seed(mnemonic_str)
        secret_key = get_root_xprv(seed)
        return secret_key

    def get_balance(self):
        '''
        获得余额数据
        :return:
        '''
        param = {"address": self.vapor_address}
        url = self.bycoin_url + "/vapor/v3/account/address"
        return self._request("GET", url, param)

    def get_bitcoin_balance(self):
        '''
        获得bycoin 里面, bitcoin地址上的余额
        :return:
        '''
        param = {"address": self.bitcoin_address}
        url = self.bycoin_url + "/bitcoin/v1/account/address?address={}".format(self.bitcoin_address)
        return self._request("GET", url, param)

    def get_main_chain_balance(self):
        '''
        获得主链地址
        :return:
        '''
        if self.third_main_address:
            param = {"address": self.third_main_address}
        else:
            param = {"address": self.main_address}
        url = self.host + "/bytom/v3/account/address"
        return self._request("GET", url, param)

    def get_exchange_info(self):
        '''
        获得磁力交易对信息
        :return:
        '''
        path = self.host + "/magnet/v3/common/symbols"
        return self._request("GET", path, {})

    def get_assets(self):
        '''
        获得资产细节信息
        '''
        path = self.host + "/vapor/v3/q/assets"
        return self._request("POST", path, {})

    def get_depth(self, symbol, limit=5):
        '''
        获得磁力兑换深度
        :param symbol:
        :param limit:
        :return:
        '''
        path = self.host + "/magnet/v3/market/depth?symbol={}&depth={}".format(symbol, limit)
        return self._request("GET", path, {})

    def mov_sign(self, info, is_build_order=True):
        '''
        签名
        :param info:
        :param is_build_order:
        :return:
        '''
        raw_transaction = info["raw_transaction"]
        signing_instructions = info["signing_instructions"]

        params = {}
        arr = []
        for signing in signing_instructions:
            if self.third_address:
                new_secret_key = self.secret_key
                if self.third_use_child:
                    new_secret_key = self.child_secret_key
                sign_data = signing["sign_data"]
                sign_data = [xprv_sign(new_secret_key, s) for s in sign_data]
                arr.append(sign_data)

                params = {
                    "signing_instructions": signing_instructions,
                    "raw_transaction": raw_transaction,
                    "signatures": arr
                }
            else:
                new_derivation_path = signing["derivation_path"]
                sign_data = signing["sign_data"]

                if new_derivation_path:
                    new_secret_key = get_child_xprv(self.secret_key, new_derivation_path)
                    sign_data = [xprv_sign(new_secret_key, s) for s in sign_data]
                else:
                    new_secret_key = self.child_secret_key
                    sign_data = [xprv_sign(new_secret_key, s) for s in sign_data]
                    if is_build_order:
                        sign_data.append(self.public_key)

                arr.append(sign_data)
                params = {
                    "raw_transaction": raw_transaction,
                    "signatures": arr
                }
        return params

    def _send_order_sign(self, url, data):
        '''
        发送磁力签名交易
        :param url:
        :param data:
        :return:
        '''
        ret = []
        len_datas = len(data["data"])
        i = 0
        for info in data["data"]:
            i = i + 1
            params = self.mov_sign(info)
            if i < len_datas:
                data = self._request("POST", self.host + "/vapor/v3/merchant/submit-payment?address={}".format(
                    self.vapor_address), params)
            else:
                data = self._request("POST", url, params)
            ret.append(data)
        return ret

    def build_order(self, symbol, side, price, volume, address):
        '''
        构建磁力交易
        :param symbol:
        :param side:
        :param price:
        :param volume:
        :param address:
        :return:
        '''
        path = self.host + "/magnet/v3/merchant/build-place-order-tx?address={}".format(address)
        params = {
            "pubkey": self.public_key,
            "price": str(price),
            "amount": str(volume),
            "side": side,
            "symbol": symbol.replace('_', '/').upper()
        }
        return self._request("POST", path, params)

    def send_order(self, symbol, side, price, volume):
        '''
        发送磁力交易订单
        :param symbol:
        :param side:
        :param price:
        :param volume:
        :return:
        '''
        data = self.build_order(symbol, side, price, volume, self.vapor_address)
        if data:
            if int(data["code"]) == 200:
                if self.third_address:
                    return self._new_send_order_sign(data)
                else:
                    path2 = self.host + "/magnet/v3/merchant/submit-place-order-tx?address={}".format(
                        self.vapor_address)
                    return self._send_order_sign(path2, data)
            else:
                return data
        else:
            return data

    def _new_send_order_sign(self, data):
        '''
        提交托管签名单子
        :param data:
        :return:
        '''
        ret = []
        url = self.host + "/delegation/v1/merchant/submit-place-order-tx?address={}".format(self.third_address)
        for info in data["data"]:
            params = self.mov_sign(info)
            data = self._request("POST", url, params)
            ret.append(data)
        return ret

    def _send_cancel_sign(self, url, data):
        '''
        提交托管撤销单子
        :param url:
        :param data:
        :return:
        '''
        params = self.mov_sign(data["data"], is_build_order=False)
        data = self._request("POST", url, params)
        return data

    def cancel_order(self, order_id):
        '''
        磁力撤单
        :param order_id:
        :return:
        '''
        path1 = self.host + "/magnet/v3/merchant/build-cancel-order-tx?address={}".format(
            self.vapor_address)
        params = {"order_id": order_id}
        data = self._request("POST", path1, params)
        if data:
            if str(data["code"]) == "200":
                if self.third_address:
                    path2 = self.host + "/delegation/v1/merchant/submit-cancel-order-tx?address={}".format(
                        self.third_address)
                    data = self._send_cancel_sign(path2, data)
                else:
                    path2 = self.host + "/magnet/v3/merchant/submit-cancel-order-tx?address={}".format(
                        self.vapor_address)
                    data = self._send_cancel_sign(path2, data)
                return data
            else:
                return data

    def make_transfer_params(self, asset, amount, to_address):
        '''
        构建基础转账，提交交易参数
        :param asset:
        :param amount:
        :param to_address:
        :return:
        '''
        params = {
            "asset": self.asset_id_dict[asset.upper()],
            "recipients": {to_address: str('%.8f' % amount)},
            "confirmations": 1,
            "memo": "memo",
            "forbid_chain_tx": False,
        }
        return params

    def submit_payment(self, data):
        '''
        提交基础交易、转账类支付
        :param data:
        :return:
        '''
        ret = []
        for info in data["data"]:
            params = self.mov_sign(info)
            if self.third_address:
                data = self._request("POST",
                                     "{}/delegation/v1/merchant/submit-withdrawal-tx?address={}".format(
                                         self.host,
                                         self.vapor_address),
                                     param=params)
            else:
                data = self._request("POST",
                                     "{}/vapor/v3/merchant/submit-payment?address={}".format(self.host,
                                                                                             self.vapor_address),
                                     param=params)
            if data and str(data["code"]) == "200":
                ret.append(data)
            else:
                print("Error in submit payment:{}".format(data))
        return ret

    def inside_transfer(self, asset, amount, to_address):
        '''
        内部转账
        :param asset:
        :param amount:
        :param to_address:
        :return:
        '''
        params = self.make_transfer_params(asset, amount, to_address)
        data = self._request("POST", "{}/vapor/v3/merchant/build-payment?address={}".
                             format(self.host, self.vapor_address), param=params)
        if data and str(data["code"]) == "200":
            return self.submit_payment(data)
        return []

    def sign_cross_chain(self, params):
        sign_url = self.host + "/delegation/v1/merchant/sign-crosschain-tx?address={}".format(self.vapor_address)
        data = self._request("POST", sign_url, params)
        if data and int(data["code"]) == 200:
            return data["data"]

    def cross_chain_out(self, asset, amount, address):
        '''
        跨链交易
        :param asset:
        :param amount:
        :param address:
        :return:
        '''
        params = self.make_transfer_params(asset, amount, address)
        ret = []
        data = self._request("POST", "{}/vapor/v3/merchant/build-crosschain?address={}".format(self.host,
                                                                                               self.vapor_address),
                             param=params)
        if data and str(data["code"]) == "200":
            for info in data["data"]:
                params = self.mov_sign(info)
                if self.third_address:
                    params = self.sign_cross_chain(params)
                if params:
                    data = self._request("POST",
                                         "{}/vapor/v3/merchant/submit-payment?address={}".format(self.host,
                                                                                                 self.vapor_address),
                                         param=params)
                    ret.append(data)
        return ret

    def bytom_transfer(self, asset, amount, address):
        '''
        主链转账
        :param asset:
        :param amount:
        :param address:
        :return:
        '''
        params = self.make_transfer_params(asset, amount, address)
        ret = []
        data = self._request("POST",
                             "{}/bytom/v3/merchant/build-payment?address={}".format(self.host, self.main_address),
                             param=params)
        if data and str(data["code"]) == "200":
            for info in data["data"]:
                params = self.mov_sign(info)
                data = self._request("POST",
                                     "{}/bytom/v3/merchant/submit-payment?address={}".format(self.host,
                                                                                             self.main_address),
                                     param=params)
                ret.append(data)
        return ret

    def cross_chain_in(self, asset, amount):
        '''
        跨链跨入
        :param amount:
        :return:
        '''
        return self.bytom_transfer(asset, amount, "bm1qlp5zd4jqsy8tpz3tldcxuqyjyulqt6d860t3l82n7nmvct3ad34qfktwv7")

    def query_list_orders(self, order_id_list, states=["open", "partial", "canceled", "filled", "submitted"]):
        '''
        查询磁力订单
        :param order_id_list:
        :param states:
        :return:
        '''
        param = {
            "side": "",
            "filter": {
                "states": states,
                "order_ids": [int(order_id) for order_id in order_id_list]
            }
        }
        path = self.host + "/magnet/v3/merchant/list-orders?address={}&limit=1000".format(
            self.vapor_address)
        return self._request("POST", path, param)

    def query_open_orders(self, symbol):
        '''
        查询所有公开的磁力订单
        :param symbol:
        :return:
        '''
        param = {
            "symbol": symbol,
            "side": "",
            "filter": {
                "states": [
                    "open",
                    "partial"  # //部分成交
                ]
            }
        }
        path = self.host + "/magnet/v3/merchant/list-orders?address={}&limit=1000".format(
            self.vapor_address)
        return self._request("POST", path, param)

    def query_all_orders(self, symbol, states=[]):
        '''
        查询所有的订单
        :param symbol:
        :param states:
        :return:
        '''
        start = 0
        param = {
            "symbol": symbol,
            "side": "",
            "filter": {
                "states": states
            }
        }
        path = self.host + "/magnet/v3/merchant/list-orders?address={}&limit=1000&start={}"\
            .format(self.vapor_address, start)
        data = self._request("POST", path, param)
        ret = data
        while data and len(data["data"]) == 1000:
            start += 1000
            path = self.host + "/magnet/v3/merchant/list-orders?address={}&limit=1000&start={}" \
                .format(self.vapor_address, start)
            data = self._request("POST", path, param)
            ret["data"].extend(data["data"])
        return ret

    def query_traded_orders(self, symbol):
        '''
        查询有交易的订单
        :param symbol:
        :return:
        '''
        param = {
            "symbol": symbol,
            "side": "",
            "filter": {
                "states": [
                    "partial",  # //部分成交
                    # 'canceled',  # 完成撤销
                    "filled",  # //全部成交
                ]
            }
        }
        path = self.host + "/magnet/v3/merchant/list-orders?address={}&limit=1000".format(
            self.vapor_address)
        data = self._request("POST", path, param)
        td1 = [d for d in data["data"] if float(d["filled_amount"]) > 0]

        param = {
            "symbol": symbol,
            "side": "",
            "filter": {
                "states": [
                    'canceled'  # 完成撤销
                ]
            }
        }
        path = self.host + "/magnet/v3/merchant/list-orders?address={}&limit=1000".format(
            self.vapor_address)
        data = self._request("POST", path, param)
        td2 = [d for d in data["data"] if float(d["filled_amount"]) > 0]
        data["data"] = td1 + td2
        return data

    def query_finished_orders(self, symbol):
        '''
        已经所有完成的订单
        :param symbol:
        :return:
        '''
        param = {
            "symbol": symbol,
            "side": "",
            "filter": {
                "states": [
                    "canceled",  # //完全撤销
                    "filled",  # //全部成交
                ]
            }
        }
        path = self.host + "/magnet/v3/merchant/list-orders?address={}&limit=1000".format(
            self.vapor_address)
        return self._request("POST", path, param)

    def generate_timestamp(self):
        return str(int(time.time()))

    def get_signature(self, path, use_address, white_address, timestamp):
        '''
        托管做市签名信息
        :param path:
        :param use_address:
        :param white_address:
        :param timestamp:
        :return:
        '''
        msg = 'POST\n/v1/account/' + path + '\naddress=' + use_address + '&timestamp=' + timestamp + '\n{"address":"' + white_address + '"}'
        hash = hashlib.sha256()
        hash.update(msg.encode('utf-8'))
        msg = hash.hexdigest()

        return xprv_sign(self.child_secret_key, msg)

    def create_delegation_wallet(self, funder_pubkey, quant_pubkey):
        '''
        创建做市托管钱包
        :param funder_pubkey:
        :param quant_pubkey:
        :return:
        '''
        param = {
            "funder_pubkey": funder_pubkey,
            "quant_pubkey": quant_pubkey
        }
        path = self.host + "/delegation/v1/account/create-wallet"
        return self._request("POST", path, param)

    def add_white_list_address(self, use_address, white_address):
        '''
        添加做市转账白名单
        :param use_address:
        :param white_address:
        :return:
        '''
        param = {
            "address": white_address
        }
        timestamp = self.generate_timestamp()
        signature = self.get_signature("add-white-list-address", use_address, white_address, timestamp)
        path = self.host + "/delegation/v1/account/add-white-list-address?address={}&timestamp={}&signature={}".format(
            use_address, timestamp, signature
        )
        return self._request("POST", path, param)

    def delete_white_list_address(self, use_address, white_address):
        '''
        删除做市转账白名单
        :param use_address:
        :param white_address:
        :return:
        '''
        param = {
            "address": white_address
        }
        timestamp = self.generate_timestamp()
        signature = self.get_signature("del-white-list-address", use_address, white_address, timestamp)
        path = self.host + "/delegation/v1/account/del-white-list-address?address={}&timestamp={}&signature={}".format(
            use_address, timestamp, signature
        )
        return self._request("POST", path, param)

    def get_super_exchange_info(self):
        '''
        获得超导交易所信息
        :return:
        '''
        path = self.super_url + "/v1/symbols"
        return self._request("GET", path, {})

    def get_super_exchange_order_history(self, start=0, limit=1000):
        '''
        获得超导历史交易订单
        :return:
        '''
        path = self.super_url + "/v1/exchange-order-history?address={}&start={}&limit={}".format(self.vapor_address, start, limit)
        return self._request("GET", path, {})

    def get_super_exchange_rate(self, symbol, volume, side):
        '''
        获得超导数据接口
        :param symbol:
        :param volume:
        :param side:
        :return:
        '''
        path = self.super_url + "/v1/exchange-rate?symbol={}&amount={}&side={}".format(symbol, volume, side)
        return self._request("GET", path, {})

    def sign_delegation_superconducting(self, params):
        sign_url = self.host + "/delegation/v1/merchant/sign-superconducting-tx?address={}".format(self.vapor_address)
        data = self._request("POST", sign_url, params)
        if data and int(data["code"]) == 200:
            return data["data"]

    def get_super_asset_proportion(self, symbol):
        '''
        获得某个币池的资产比例
        :param symbol:
        :return:
        '''
        path = self.super_url + "/v1/asset-proportion?symbol={}".format(symbol)
        return self._request("GET", path, {})

    def get_multi_asset_available(self, address):
        '''
        获得超导多资产可用余额信息
        :param address:
        :return:
        '''
        path = self.super_url + "/v1/multi-asset-available?address={}".format(self.vapor_address)
        return self._request("GET", path, {})

    def submit_multi_asset_withdralal(self, symbol, amount):
        '''
        双资产移除流动性
        :param symbol: 代币
        :param amount: 移出多少个份额
        :return:
        '''
        proportion_info = self.get_super_asset_proportion(symbol)
        if self.check_msg(proportion_info):
            params = {
                "pubkey": get_xpub(self.secret_key),
                "symbol": symbol,
                "quantity_proportion": proportion_info["data"],
                "amount": str(amount),
                "time_stamp": self.generate_timestamp()
            }
            data = json.dumps(params).replace(' ', '').encode('utf-8')
            signature_data = xprv_my_sign(self.secret_key, data)
            path = self.super_url + "/v1/submit-multi-asset-withdrawal?signature={}&address={}".format(signature_data, self.vapor_address)
            return self._request("POST", path, params)

    def build_super_exchange_order(self, symbol, side, price, volume):
        '''
        构建超导交易订单
        :param symbol:
        :param side:
        :param price:
        :param volume:
        :return:
        '''
        path = self.super_url + "/v1/build-exchange-request?address={}".format(self.vapor_address)
        params = {
            "pubkey": self.public_key,
            "symbol": symbol,
            "side": side,
            "amount": str(volume),
            "exchange_rate": str(price)
        }
        return self._request("POST", path, params)

    def _send_super_order_sign(self, data):
        '''
        提交超导交易签名
        :param data:
        :return:
        '''
        ret = []
        url = self.super_url + "/v1/submit-exchange-request?address={}".format(self.vapor_address)
        for info in data["data"]:
            params = self.mov_sign(info, is_build_order=True)
            if self.third_address:
                params = self.sign_delegation_superconducting(params)
            if params:
                data = self._request("POST", url, params)
            ret.append(data)
        return ret

    def send_super_exchange_order(self, symbol, side, price, volume):
        '''
        发送超导交易订单
        :param symbol:
        :param side:
        :param price:
        :param volume:
        :return:
        '''
        data = self.build_super_exchange_order(symbol, side, price, volume)
        if data:
            if str(data["code"]) == "200":
                return self._send_super_order_sign(data)
            else:
                return data

    def get_super_conducting_pool_info(self):
        '''
        获得超导池各个池子的信息
        :return:
        '''
        url = self.super_url + "/v1/pool-info"
        return self._request("GET", url, {})

    def get_transaction(self, tx_hash):
        '''
        通过哈希获得某个交易的信息
        :param tx_hash:
        :return:
        '''
        url = self.host + "/vapor/v3/merchant/transaction?tx_hash={}".format(tx_hash)
        return self._request("GET", url, {})

    def get_vapor_chain_status(self):
        '''
        获得vapor chain status状态
        '''
        url = "http://ex.movapi.com/vapor/v3/q/chain-status"
        return self._request("GET", url, {})

    def get_btm_chain_status(self):
        '''
        获得btm chain status状态
        '''
        url = "http://ex.movapi.com/bytom/v3/q/chain-status"
        return self._request("GET", url, {})

    def list_utxos(self, asset, limit=10):
        '''
        列出所有的utxos
        :param asset:
        :param limit:
        :return:
        '''
        url = self.host + "/vapor/v3/q/utxos?limit={}".format(limit)
        params = {
            "filter": {
                "asset": self.asset_id_dict[asset.upper()],
                "script": self.vapor_script,
                "sort": {
                    "by": "amount"
                }
            }
        }
        return self._request("POST", url, params)

    def build_advanced_order(self, inputs, outputs):
        '''
        构建高级高级
        :param inputs:
        :param outputs:
        :return:
        '''
        url = self.host + "/vapor/v3/merchant/build-advanced-tx?address={}".format(self.vapor_address)
        params = {
            "fee": "0",
            "confirmations": 1,
            "inputs": inputs,
            "outputs": outputs,
            "forbid_chain_tx": False
        }
        return self._request("POST", url, params)

    def get_flash_depth(self, symbol, limit=5):
        '''
        symbol: BTM/ETH
        获得闪兑深度
        '''
        url = self.host + "/flashswap/v3/market-depth?symbol={}&depth={}".format(symbol, limit)
        return self._request("GET", url, {})

    def build_flash_swap_order(self, symbol, side, price, volume):
        '''
        构建闪兑交易请求
        :param symbol:
        :param side:
        :param price:
        :param volume:
        :return:
        '''
        #self.flash_url = "http://52.82.57.178:3002"
        url = self.flash_url + "/flashswap/v3/swap?address={}".format(self.vapor_address)
        params = {
            "amount": str(volume),
            "price": str(price),
            "side": side,
            "symbol": symbol
        }
        return self._request("POST", url, params)

    def send_flash_swap_order(self, symbol, side, price, volume):
        '''
        构建闪兑交易请求
        :param symbol:
        :param side:
        :param price:
        :param volume:
        :return:
        '''
        ret = []
        data = self.build_flash_swap_order(symbol, side, price, volume)
        if data and str(data["code"]) == "200":
            for info in data["data"]:
                params = self.mov_sign(info, is_build_order=True)
                new_url = self.host + "/magnet/v3/merchant/submit-swap-order-tx?address={}".format(self.vapor_address)
                data = self._request("POST", new_url, params)
                ret.append(data)
            return ret
        return []

    def check_msg(self, data):
        return data and str(data["code"]) == "200"


