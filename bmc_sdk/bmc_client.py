# encoding: UTF-8

import requests
import json
from web3.types import Wei

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
        elif network == EthNet.BmcTestNet.value:
            self.host = "https://test-bcapi.movapi.com"
        else:
            self.host = ""
            log_service_manager.write_log(f"[BmcClient] init failed! network error:{network}")

        self.session = requests.session()
        self.headers = {
            'Accept': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36'
        }

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

    def get_cross_assets(self):
        url = self.host + "/bmc/v1/cross-assets"
        data = self._request("GET", url, {})
        return data

    def cross_to_main_chain(self, asset_address, cross_address, amount, gas_price="1500000000", cross_fee="0"):
        params = {
            "asset_address": asset_address,
            "cross_address": cross_address,
            "amount": str(amount),
            "gas_price": str(gas_price),
            "cross_fee": str(cross_fee)
        }
        url = self.host + "/bmc/v1/build-cross?address={}".format(self.str_address)
        data = self._request("POST", url, param=params)
        if self.check_msg(data):
            return self.submit_payment(data)
        return []

    def get_transaction_from_bmc_wallet(self, asset_address, tx_hash):
        params = {
            "asset_address": asset_address,
            "tx_hash": tx_hash
        }
        url = self.host + "/transaction"
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

    def submit_payment(self, data):
        url = self.host + "/bmc/v1/submit-payment?address={}".format(self.str_address)
        raw_transaction = data["data"]["raw_transaction"]
        signed_txn = self.w3.eth.account.sign_transaction(
            raw_transaction, private_key=self.private_key
        )
        raw_transaction = signed_txn.rawTransaction
        params = {
            "raw_transaction": raw_transaction
        }
        return self._request("POST", url, params)

    def check_msg(self, data):
        return data and str(data["code"]) == "200"

    @staticmethod
    def get_bytom_client_from_keystore(keystore_file_path, password='', net=EthNet.BmcTestNet.value):
        return BmcClient.get_client_from_keystore(BmcClient, keystore_file_path, password, net)

    def get_sell_price(self, symbol, volume=3):
        target_symbol, base_symbol = get_two_currency(symbol)
        target_symbol = target_symbol.upper()
        base_symbol = base_symbol.upper()
        return self.get_price_input(self.get_contract_address(target_symbol),
                                    self.get_contract_address(base_symbol),
                                    int(self.get_decimal_mul(target_symbol) * volume)) / (
                       self.get_decimal_mul(base_symbol) * volume)

    def get_buy_price(self, symbol, volume=3000):
        target_symbol, base_symbol = get_two_currency(symbol)
        target_symbol = target_symbol.upper()
        base_symbol = base_symbol.upper()

        price = self.get_price_input(self.get_contract_address(base_symbol),
                                     self.get_contract_address(target_symbol),
                                     int(self.get_decimal_mul(base_symbol) * volume)) / (
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

    def simple_trade(self, symbol, direction, price, volume):
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
                                      f" input_amount:{input_amount}"
                                      f" output_amount:{output_amount}")
        transaction, tx_params = self.simple_make_trade(
            self.get_contract_address(target_symbol),
            self.get_contract_address(base_symbol),
            input_amount,
            output_amount
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

