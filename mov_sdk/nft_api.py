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


NFT_API_MAIN_ROOT = "https://bcapi.movapi.com/nft/v1"
NFT_API_TEST_ROOT = "https://test-bcapi.movapi.com/nft/v1"

MOV_REST_TRADE_HOST = "https://ex.movapi.com"
MOV_REST_TEST_TRADE_HOST = "https://test-bcapi.movapi.com"

SUPER_REST_TRADE_HOST = "https://supertx.movapi.com"
DELEGATION_REST_TRADE_HOST = "https://ex.movapi.com/delegation"
PLUTUS_REST_TRADE_HOST = "https://ex.movapi.com/plutus"

# networks = ["mainnet", "testnet", "solonet"]

derivation_path = ['2c000000', '99000000', '01000000', '00000000', '01000000']
account_index_int = 1
address_index_int = 1


class NftApi(object):
    def __init__(self, secret_key="", network=Net.MAIN.value, third_address="", third_public_key="", mnemonic_str="",
                 _MOV_REST_TRADE_HOST="", _BYCOIN_URL="", _SUPER_REST_TRADE_HOST="", _DELEGATIOIN_REST_TRADE_HOST="",
                 _NFT_REST_TRADE_HOST="", _PLUTUS_REST_TRADE_HOST = "", _third_use_child=False, _bitcoin_address="",
                 _derivation_path = [], _account_index_int=1, _address_index_int=1, _asset_id_dict={},
                 _id_asset_dict={}, _decimal_dict={}, _margin_rate_dict={}):
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

        if _DELEGATIOIN_REST_TRADE_HOST:
            self.delegation_url = _DELEGATIOIN_REST_TRADE_HOST
        else:
            self.delegation_url = DELEGATION_REST_TRADE_HOST

        if _NFT_REST_TRADE_HOST:
            self.nft_rest_trade_host = _NFT_REST_TRADE_HOST
        else:
            if network == Net.MAIN.value:
                self.nft_rest_trade_host = NFT_API_MAIN_ROOT
            else:
                self.nft_rest_trade_host = NFT_API_TEST_ROOT

        if _PLUTUS_REST_TRADE_HOST:
            self.plutus_url = _PLUTUS_REST_TRADE_HOST
        else:
            self.plutus_url = PLUTUS_REST_TRADE_HOST

        if _derivation_path:
            self.derivation_path = _derivation_path
        else:
            self.derivation_path = derivation_path

        if _account_index_int:
            self.account_index_int = _account_index_int
        else:
            self.account_index_int = account_index_int

        if _address_index_int:
            self.address_index_int = _address_index_int
        else:
            self.address_index_int = address_index_int

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

        self.asset_id_dict = _asset_id_dict
        self.id_asset_dict = _id_asset_dict
        self.decimal_dict = _decimal_dict
        self.margin_rate_dict = _margin_rate_dict

        if not self.asset_id_dict or not self.id_asset_dict or not self.decimal_dict or not self.margin_rate_dict:
            self.get_nft_asset_pairs()

    def is_init_success(self):
        return self.asset_id_dict and self.id_asset_dict and self.decimal_dict and self.margin_rate_dict

    def get_nft_asset_pairs(self):
        for exchange, data in [("nft", self.query_nft_assets())]:
            if data:
                for dic in data["data"]:
                    asset_id = dic["asset"]
                    symbol = dic["symbol"]
                    decimals = dic["decimals"]
                    margin_rate = dic["margin_rate"]

                    self.asset_id_dict[symbol.upper()] = asset_id
                    self.id_asset_dict[asset_id] = symbol
                    self.decimal_dict[asset_id] = dic["decimals"]
                    self.margin_rate_dict[asset_id] = dic["margin_rate"]

    def get_secret_key(self):
        return self.secret_key if not self.third_use_child else self.child_secret_key

    def get_min_volume(self, asset):
        asset_id = self.asset_id_dict[asset.upper()]
        decimal_val = self.decimal_dict[asset_id]
        return 0.1 ** decimal_val

    def get_margin_rate(self, asset):
        asset_id = self.asset_id_dict[asset.upper()]
        return self.margin_rate_dict[asset_id]

    def get_asset_id(self, asset):
        return self.asset_id_dict[asset.upper()]

    def get_asset_from_asset_id(self, asset_id):
        return self.id_asset_dict[asset_id]

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
            self.main_address, self.vapor_address = get_main_vapor_address(self.secret_key, self.network, self.account_index_int, self.address_index_int)
            self.bytom_script = address_to_script(Chain.BYTOM.value, self.main_address, self.network)
            self.vapor_script = address_to_script(Chain.VAPOR.value, self.vapor_address, self.network)
            self.public_key = self.get_child_pub_key()
            self.child_secret_key = get_child_xprv(self.secret_key, self.derivation_path)
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
                print(url, param, result.status_code, result.text)
            if result:
                return result.json()
            else:
                return None
        except Exception as ex:
            print("timeout", ex)
        return None

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

    def get_child_pub_key(self):
        '''
        获得派生公钥
        :return:
        '''
        xpub_hexstr = get_xpub(self.secret_key)
        child_xpub = get_child_xpub(xpub_hexstr, self.derivation_path)
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

    def query_asset(self, asset_id):
        url = self.host + f"/bycoin/bytom2/v1/q/asset?id={asset_id}"

    def query_all_assets(self):
        url = "https://bcapi.movapi.com/blockmeta/bytom2/v1/assets?start=0&limit=1000"
        return self._request(method="GET", url=url, param={})

    #########
    # main balance
    #########
    def get_main_chain_balance(self):
        '''
        获得主链地址
        :return:
        '''
        param = {"address": self.main_address}
        url = self.host + "/bycoin/bytom2/v1/account/address"
        return self._request("GET", url, param)
    
    #########
    # nft api
    #########
    def query_nft_assets(self):
        url = self.nft_rest_trade_host + "/assets"
        return self._request(method="GET", url=url, param={})

    def artist_rank(self, order="profit", sort="asc", start=0, limit=100):
        '''
        艺术家排行榜
        '''
        url = self.nft_rest_trade_host + f"/artist-rank?order={order}&sort={sort}&start={start}&limit={limit}"
        return self._request(method="GET", url=url, param={})

    def trade_rank(self, start, limit, day=7):
        '''
        近七日成交排行榜
        '''
        url = self.nft_rest_trade_host + f"/trade-rank?start={start}&limit={limit}&day={day}"
        return self._request(method="GET", url=url, param={})

    def offer_rank(self, start, limit):
        '''
        求购排行榜
        '''
        url = self.nft_rest_trade_host + f"/offer-rank?start={start}&limit={limit}"
        return self._request(method="GET", url=url, param={})

    def user_info(self, address=None):
        '''
        查看用户 NFT 个人信息
        '''
        if not address:
            address = self.main_address
        url = self.nft_rest_trade_host + f"/user-info?address={address}"
        return self._request(method="GET", url=url, param={})

    def user_own_nfts(self, address=None, start=0, limit=1000):
        '''
        查看用户当前用于的nfts
        '''
        if not address:
            address = self.main_address
        url = self.nft_rest_trade_host + f"/user-own-nfts?address={address}&start={start}&limit={limit}"
        return self._request(method="GET", url=url, param={})

    def user_sold_ntfs(self, address, start=0, limit=100):
        '''
        用户被买走的nft
        '''
        url = self.nft_rest_trade_host + f"/user-sold-nfts?address={address}&start={start}&limit={limit}"
        return self._request(method="GET", url=url, param={})

    def user_mint_ntfs(self, address, start=0, limit=100):
        '''
        查看用户铸造的ntfs
        '''
        url = self.nft_rest_trade_host + f"/user-mint-nfts?address={address}&start={start}&limit={limit}"
        return self._request(method="GET", url=url, param={})

    def user_offer_nfts(self, address, start=0, limit=100):
        '''
        查看用户求购的nfts
        '''
        url = self.nft_rest_trade_host + f"/user-offered-nfts?address={address}&start={start}&limit={limit}"
        return self._request(method="GET", url=url, param={})

    def search_nfts(self, word, start, limit):
        '''
        搜搜市场nfts
        '''
        url = self.nft_rest_trade_host + f"/search-nfts?word={word}&start={start}&limit={limit}"
        params = {"sort_name": "trade_cnt", "order_mode": "desc"}
        return self._request(method="POST", url=url, param=params)

    def fuzzy_search(self, word, start, limit):
        '''
        市场模糊查询
        '''
        url = self.nft_rest_trade_host + f"/fuzzy-search?word={word}&start={start}&limit={limit}"
        return self._request(method="GET", url=url, param={})

    def nft_detail(self, asset):
        '''
        查看nft详情
        '''
        url = self.nft_rest_trade_host + f"/nft-detail?nft_asset={asset}"
        return self._request(method="GET", url=url, param={})

    def nft_margin(self, asset, start=0, limit=100):
        '''
        查看nft 保证金动作
        '''
        url = self.nft_rest_trade_host + f"/margin-actions?nft_asset={asset}&start={start}"
        return self._request(method="GET", url=url, param={})

    def nft_offers(self, nft_asset, start=0, limit=100):
        '''
        NFT 求购列表
        '''
        url = self.nft_rest_trade_host + f"/nft-offers?nft_asset={nft_asset}&start={start}&limit={limit}"
        return self._request(method="POST", url=url, param={})

    def nft_offer(self, tx_hash):
        '''
        查看求购
        '''
        url = self.nft_rest_trade_host + f"/nft-offer?tx_hash={tx_hash}"
        return self._request(method="GET", url=url, param={})

    ######### 
    # nft trade
    ########
    # def issue_nft(self, name, content_path, content_md5, royalty_rate, margin_asset, margin_amount, description, thumbnail_file_path):
    #     '''
    #     接口还有问题
    #     发行 nft
    #     '''
    #     params = {
    #         "name": name, 
    #         "content_path": content_path,
    #         "content_md5": content_md5,
    #         "royalty_rate": royalty_rate,
    #         "margin_asset": margin_asset,
    #         "margin_amount": margin_amount,
    #         "description": description,
    #         "thumbnail_file_path": thumbnail_file_path
    #     }
    #     url = self.nft_rest_trade_host + f"/issue-nft?address={self.main_address}"
    #     return self._request(method="POST", url=url, param=params)

    def build_issue_trade(self, nft_asset, pay_asset, pay_amount, margin_asset, margin_amount):
        '''
        构建资产交易
        '''
        params = {
            "nft_asset": nft_asset,
            "pay_asset": pay_asset,
            "pay_amount": str(pay_amount),
            "margin_asset": margin_asset,
            "margin_amount": str(margin_amount)
        }
        url = self.nft_rest_trade_host + f"/build-issue-trade?address={self.main_address}"
        return self._request(method="POST", url=url, param=params)

    def issue_trade(self, nft_asset, pay_asset, pay_amount, margin_asset, margin_amount):
        # issue_trade
        data =  self.build_issue_trade(nft_asset, pay_asset, pay_amount, margin_asset, margin_amount)
        print(data)
        ret = []
        if self.check_msg(data):
            for info in data["data"]:
                params = self.mov_sign(info)
                params["submit_type"] = "issue_trade"
                data = self.submit_tx(params)
                ret.append(data)
        return ret

    def build_trade(self, nft_asset, pay_asset, pay_amount, margin_asset, margin_amount):
        '''
        构建交易 
        '''
        params = {
            "nft_asset": nft_asset,
            "pay_asset": pay_asset,
            "pay_amount": str(pay_amount),
            "margin_asset": margin_asset,
            "margin_amount": str(margin_amount)
        }
        url = self.nft_rest_trade_host + f"/build-trade?address={self.main_address}"
        return self._request(method="POST", url=url, param=params)

    def trade(self, nft_asset, pay_asset, pay_amount, margin_asset, margin_amount):
        '''
        直接交易
        '''
        data = self.build_trade(nft_asset, pay_asset, pay_amount, margin_asset, margin_amount)
        print(data)
        ret = []
        if self.check_msg(data):
            for info in data["data"]:
                params = self.mov_sign(info)
                params["submit_type"] = "trade"
                data = self.submit_tx(params)
                ret.append(data)
        return ret

    def build_offer(self, nft_asset, pay_asset, pay_amount, margin_asset, margin_amount):
        '''
        构建NFT 求购交易
        '''
        params = {
            "nft_asset": nft_asset,
            "pay_asset": pay_asset,
            "pay_amount": str(pay_amount),
            "margin_asset": margin_asset,
            "margin_amount": str(margin_amount)
        }
        url = self.nft_rest_trade_host + f"/build-offer?address={self.main_address}"
        return self._request(method="POST", url=url, param=params)

    def offer_trade(self, nft_asset, pay_asset, pay_amount, margin_asset, margin_amount):
        # offer
        data = self.build_offer(nft_asset, pay_asset, pay_amount, margin_asset, margin_amount)
        ret = []
        if self.check_msg(data):
            for info in data["data"]:
                params = self.mov_sign(info)
                params["submit_type"] = "offer"
                data = self.submit_tx(params)
                ret.append(data)
        return ret

    def build_edit_margin(self, nft_asset, amount):
        '''
        修改保证金
        '''
        # edit_margin
        params = {
            "nft_asset": nft_asset,
            "amount": amount
        }
        url = self.nft_rest_trade_host + f"/edit-margin?address={self.main_address}"
        return self._request(method="POST", url=url, param=params)

    def edit_margin(self, nft_asset, amount):
        data = self.build_edit_margin(nft_asset, amount)
        print(data)
        ret = []
        if self.check_msg(data):
            for info in data["data"]:
                params = self.mov_sign(info)
                params["submit_type"] = "edit_margin"
                data = self.submit_tx(params)
                ret.append(data)
        return ret

    def build_revoke_offer(self, nft_asset):
        '''
        撤销求购
        '''
        # revoke_offer
        params = {
            "nft_asset": nft_asset
        }
        url = self.nft_rest_trade_host + f"/revoke-offer?address={self.main_address}"
        return self._request(method="POST", url=url, param=params)

    def revoke_offer(self, nft_asset):
        data = self.build_revoke_offer(nft_asset)
        ret = []
        if self.check_msg(data):
            for info in data["data"]:
                params = self.mov_sign(info)
                params["submit_type"] = "revoke_offer"
                data = self.submit_tx(params)
                ret.append(data)
        return ret

    def submit_tx(self, params):
        '''
        params = {
            "submit_type": submit_type, 
            "raw_transaction": raw_transaction,
            "signatures": arr
        }
        '''
        url = self.nft_rest_trade_host + f"/submit-tx?address={self.main_address}"
        return self._request(method="POST", url=url, param=params)


    ##############
    ## 其他 API
    #########
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

    def transfer(self, asset, amount, to_address):
        '''
        bytom2 主链转移某个资产
        '''
        params = self.make_transfer_params(asset, amount, to_address)
        ret = []
        data = self._request("POST",
                             "{}/bycoin/bytom2/v1/merchant/build-payment?address={}".format(self.host, self.main_address),
                             param=params)

        if self.check_msg(data):
            for info in data["data"]:
                params = self.mov_sign(info)
                data = self._request("POST","{}/bycoin/bytom2/v1/merchant/submit-payment?address={}".format(self.host, self.main_address), param=params)
                ret.append(data)
        return ret

    def check_msg(self, data):
        return data and str(data["code"]) == "200"


