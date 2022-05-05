# encoding: UTF-8

import requests
import json
from copy import copy

from web3.types import Wei, HexBytes
from web3 import Web3

from .util import addr_to_str, get_two_currency
from .constants import ETH_ADDRESS

from .constants import Direction
from .tokens import EthNet
from .uniswap import Uniswap
from .log_service import log_service_manager


class BmcClient(Uniswap):
    '''
    免费: 100,000 次/天
    50美元/月: 200,000 次/天
    225美元/月: 1000,000  次/天
    1000美元/月: 5,000,000  次/天
    '''

    def __init__(self, address, private_key, network=EthNet.MainNet.value, provider="", version=2):
        if not provider:
            if network == EthNet.BmcTestNet.value:
                provider = "https://testnet.bmcchain.com"
            elif network == EthNet.BmcMainNet.value:
                provider = "https://mainnet.bmcchain.com"
            else:
                provider = "https://mainnet.infura.io/v3/8d2b78ac1e7447b59aba185c155477a3"  # my key
        super(BmcClient, self).__init__(address=address, private_key=private_key,
                                        network=network,
                                        provider=provider, version=version)
        if network == EthNet.BmcMainNet.value:
            self.host = "https://bcapi.movapi.com"
            self.chain_id = 188
            # self.graph_host = "http://47.243.34.114:8000"
        elif network == EthNet.BmcTestNet.value:
            self.host = "https://test-bcapi.movapi.com"
            self.chain_id = 189
            # self.graph_host = "https://api.sup.finance"
        else:
            self.host = ""
            self.chain_id = 0
            # self.graph_host = ""
            log_service_manager.write_log(f"[BmcClient] init failed! network error:{network}")

        self.session = requests.session()
        self.headers = {
            'Accept': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36'
        }

        self.default_cross_chain_fee_dic = {}

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
            log_service_manager.write_log(f"[_request] timeout:{ex}")
        return None

    def run_query(self, url, query_data_js):
        headers = {
            'Accept': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36'
        }
        # endpoint where you are making the request
        # url = "https://api.sup.finance/subgraphs/name/davekaj/uniswap"
        # url = "https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v2"

        request = requests.post(url,
                                '',
                                json={'query': query_data_js},
                                headers=headers)
        if request.status_code == 200:
            return request.json()
        else:
            raise Exception('Query failed. return code is {}.      {}'.format(request.status_code, query_data_js))

    def query_seller_by_address(self, address):
        seller_sql = '''
        {
          histories(where:{type:"deal",seller:"%s"},
          orderBy: timestamp, orderDirection: asc){
            id
            erc721Address
            tokenId
            buyer
            seller
            price
            type
            txHash
            timestamp
          }
        }
        ''' % (address)
        url = self.host + "/subgraphs/name/bytom/maze-subgraph"
        return self.run_query(url, seller_sql)

    def query_buyer_by_address(self, address):
        buyer_sqll = '''
        {
          histories(where:{type:"deal",buyer:"%s"},
          orderBy: timestamp, orderDirection: asc){
            id
            erc721Address
            tokenId
            buyer
            seller
            price
            type
            txHash
            timestamp
          }
        }
        ''' % (address)
        url = self.host + "/subgraphs/name/bytom/maze-subgraph"
        return self.run_query(url, buyer_sqll)

    def query_erc721_by_address(self, address):
        # subgraphs/name/maze-erc721-subgraph/graphql
        query_sql = '''
        {
             tokens(where:{owner:"%s"}){
                    id
                    owner{
                      id
                    }
                    uri
                    contract {
                      id
                    }
                    tokenId
              }
        }
        ''' % address
        url = self.host + "/subgraphs/name/maze-erc721-subgraph"
        return self.run_query(url, query_sql)

    def get_cross_assets(self):
        url = self.host + "/bmc/v1/cross-assets"
        data = self._request("GET", url, {})
        return data

    def get_default_cross_fee(self, asset_address):
        if asset_address in self.default_cross_chain_fee_dic.keys():
            return self.default_cross_chain_fee_dic[asset_address]
        else:
            t = self.get_cross_assets()
            if t:
                self.default_cross_chain_fee_dic = copy(t)
            return self.default_cross_chain_fee_dic.get(asset_address, "0")

    def cross_to_main_chain(self, asset_address, cross_address, amount, gas_price=None, cross_fee=None):
        params = {
            "asset_address": asset_address,
            "cross_address": cross_address,
            "amount": str(amount),
            "gas_price": str(gas_price),
            "cross_fee": str(cross_fee)
        }
        if gas_price:
            params["gas_price"] = str(gas_price)
        else:
            params["gas_price"] = self.get_gas_price()
        if cross_fee:
            params["cross_fee"] = str(cross_fee)
        else:
            params["cross_fee"] = self.get_default_cross_fee(asset_address)

        url = self.host + "/bmc/v1/build-cross?address={}".format(self.str_address)
        data = self._request("POST", url, param=params)
        if self.check_msg(data):
            return self.submit_payment(data)
        else:
            print(f"[cross_to_main_chain] check_msg failed:{data}")
        return []

    def get_transaction_from_bmc_wallet(self, asset_address, tx_hash):
        params = {
            "asset_address": asset_address,
            "tx_hash": tx_hash
        }
        url = self.host + "/bmc/v1/transaction"
        return self._request("POST", url, param=params)

    def get_balance_from_bmc_wallet(self):
        url = self.host + "/bmc/v1/balance?address=" + self.str_address
        return self._request("GET", url, {})

    def get_token_info_from_bmc_wallet(self, token_address):
        url = self.host + "/bmc/v1/query-token"
        params = {
            "token_address": token_address
        }
        return self._request("POST", url, param=params)

    '''
    # btm
    # {'type': '0x0', 'nonce': '0x2', 'gasPrice': '0x59682f00', 'gas': '0xea60', 'value': '0xde0b6b3a7640000',
    #  'input': '0x7b2263726f73735f61646472657373223a22626e31716c63396a6866303077396d717364637a75326d3865686568687033776764366c73356e6a6167222c22666565223a2230227d',
    #  'v': '0x0', 'r': '0x0', 's': '0x0', 'to': '0xf5cd39cc2a42cd19c80ebd60bf5e2446a3dc1548',
    #  'hash': '0x2f6bf7b2f2449154dd32567db82f0ba149f12096b17e41959c061e229ce4ad27'}

    # sup
    # {"type": "0x0", "nonce": "0xa", "gasPrice": "0x59682f00", "gas": "0x13880", "value": "0x0",
    #  "input": "0x23d1e5f2000000000000000000000000f5cd39cc2a42cd19c80ebd60bf5e2446a3dc154800000000000000000000000000000000000000000000000000005af3107a4000000000000000000000000000000000000000000000000000000000000000006000000000000000000000000000000000000000000000000000000000000000487b2263726f73735f61646472657373223a22626e31716c63396a6866303077396d717364637a75326d3865686568687033776764366c73356e6a6167222c22666565223a2230227d000000000000000000000000000000000000000000000000",
    #  "v": "0x0", "r": "0x0", "s": "0x0", "to": "0x77197f46435d4cf8fb07953ad5ebc98ee6c8e7f1",
    #  "hash": "0x97ccd71418ec05ed894c56ee2b7dcfa3575d745bf27f581159802c68fb0a15b3"}

    # usdt
    # {"type": "0x0", "nonce": "0x10", "gasPrice": "0x12a05f200", "gas": "0xea60", "value": "0x27147114878000",
    #  "input": "0x7b2263726f73735f61646472657373223a22626e31716c63396a6866303077396d717364637a75326d3865686568687033776764366c73356e6a6167222c22666565223a2230227d",
    #  "v": "0x0", "r": "0x0", "s": "0x0", "to": "0xf5cd39cc2a42cd19c80ebd60bf5e2446a3dc1548",
    #  "hash": "0xc53daf3e8bd2d4d7da5af1fbd561289d4d4d7f16e14baafb17fd9271614992ef"}

    '''
    def submit_payment(self, data):
        url = self.host + "/bmc/v1/submit-payment?address={}".format(self.str_address)
        raw_transaction = data["data"]["raw_transaction"]
        if isinstance(raw_transaction, str):
            raw_transaction = json.loads(raw_transaction)

        raw_transaction = {
            "from": addr_to_str(self.address),
            "value": eval(raw_transaction["value"]),
            "gas": eval(raw_transaction["gas"]),
            "gasPrice": self.get_gas_price(),
            "to": Web3.toChecksumAddress(raw_transaction["to"]),
            "nonce": self.get_latest_nonce(),
            "data": raw_transaction["input"],
            "chainId": self.chain_id
        }
        signed_txn = self.w3.eth.account.sign_transaction(
            raw_transaction, private_key=self.private_key
        )
        raw_transaction = HexBytes(signed_txn.rawTransaction).hex()
        params = {
            "raw_transaction": raw_transaction[2:]
        }
        return self._request("POST", url, params)

    def check_msg(self, data):
        return data and str(data["code"]) == "200"

    @staticmethod
    def get_bytom_client_from_keystore(keystore_file_path, password='', net=EthNet.BmcTestNet.value):
        return BmcClient.get_client_from_keystore(BmcClient, keystore_file_path, password, net)

    def get_sell_price(self, symbol, volume=3, fee=None, route=None):
        target_symbol, base_symbol = get_two_currency(symbol)
        target_symbol = target_symbol.upper()
        base_symbol = base_symbol.upper()
        if not route:
            route = [self.get_contract_address(target_symbol),
                     self.get_contract_address(base_symbol)]
        return self.get_price_input(self.get_contract_address(target_symbol),
                                    self.get_contract_address(base_symbol),
                                    int(self.get_decimal_mul(target_symbol) * volume),
                                    fee=fee,
                                    route=route
                                    ) / (
                       self.get_decimal_mul(base_symbol) * volume)

    def get_buy_price(self, symbol, volume=3000, fee=None, route=None):
        target_symbol, base_symbol = get_two_currency(symbol)
        target_symbol = target_symbol.upper()
        base_symbol = base_symbol.upper()

        if not route:
            route = [self.get_contract_address(base_symbol),
                     self.get_contract_address(target_symbol)]
        price = self.get_price_input(self.get_contract_address(base_symbol),
                                     self.get_contract_address(target_symbol),
                                     int(self.get_decimal_mul(base_symbol) * volume),
                                     fee=fee,
                                     route=route
                                     ) / (
                        self.get_decimal_mul(target_symbol) * volume)
        return 1.0 / price

    def trade(self, symbol, direction, price, volume):
        target_symbol, base_symbol = get_two_currency(symbol)
        target_symbol = target_symbol.upper()
        base_symbol = base_symbol.upper()

        if direction == Direction.LONG.value:
            target_symbol, base_symbol = base_symbol, target_symbol
            volume = price * volume

        qty = Wei(int(volume * self.get_decimal_mul(target_symbol)))
        log_service_manager.write_log(f"[trade] symbol:{symbol}"
                                      f" direction:{direction},"
                                      f" price:{price},"
                                      f" volume:{volume},"
                                      f" qty:{qty}")
        transaction, tx_params = self.make_trade(self.get_contract_address(target_symbol),
                                                 self.get_contract_address(base_symbol),
                                                 qty)
        return transaction, tx_params

    def simple_trade(self, symbol, direction, price, volume, route=None):
        target_symbol, base_symbol = get_two_currency(symbol)
        target_symbol = target_symbol.upper()
        base_symbol = base_symbol.upper()

        if direction == Direction.LONG.value:
            target_symbol, base_symbol = base_symbol, target_symbol
            input_volume = price * volume
            output_volume = volume
        else:
            input_volume = volume
            output_volume = price * volume

        input_amount = Wei(int(input_volume * self.get_decimal_mul(target_symbol)))
        output_amount = Wei(int(output_volume * self.get_decimal_mul(base_symbol)))
        log_service_manager.write_log(f"[trade] symbol:{symbol}"
                                      f" direction:{direction},"
                                      f" price:{price},"
                                      f" volume:{volume},"
                                      f" input_amount:{input_amount},"
                                      f" output_amount:{output_amount},"
                                      f" route:{route}")
        transaction, tx_params = self.simple_make_trade(
                                                        self.get_contract_address(target_symbol),
                                                        self.get_contract_address(base_symbol),
                                                        input_amount,
                                                        output_amount,
                                                        route
                                                        )
        return transaction, tx_params

    def check_approve_and_go_approve(self, symbol):
        all_ok = True
        target_symbol, base_symbol = get_two_currency(symbol)

        for token_symbol in [target_symbol, base_symbol]:
            token = self.get_contract_address(token_symbol)
            if addr_to_str(token) == ETH_ADDRESS:
                log_service_manager.write_log("[check_approve_and_go_approve] ETH_ADDRESS no need to approve!")
            else:
                is_approved = self._is_approved(token)
                # logger.warning(f"Approved? {token}: {is_approved}")
                if not is_approved:
                    log_service_manager.write_log(f"[check_approve_and_go_approve] go to approve {addr_to_str(token)}")
                    self.approve(token)

                    if not self._is_approved(token):
                        log_service_manager.write_log(f"[check_approve_and_go_approve] some error may existed!")
                        all_ok = False
                else:
                    log_service_manager.write_log(f"[check_approve_and_go_approve] {addr_to_str(token)}"
                                                  f" already approved ! no need to approve!")
        return all_ok

