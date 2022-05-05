import requests
import getpass
import time

import eth_account
import os

from web3 import Web3
import json
import codecs

from copy import copy

from bmc_sdk.constants import Direction
from bmc_sdk.bmc_client import BmcClient
from bmc_sdk.constants import EthNet

from bmc_sdk.log_service import log_service_manager
from bmc_sdk.maze_client import MazeClient, ETH_ADDRESS


def load_json(filename):
    """
    Load data from json file in temp path.
    """
    if os.path.exists(filename):
        with codecs.open(filename, mode="r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    else:
        return {}


class MazeBuyMachine(object):
    def __init__(self, json_path):
        self.setting = load_json(json_path)
        self.network = self.setting.get("network")
        self.private_key = self.setting.get("private_key")
        self.address = self.setting.get("address")

        self.client = MazeClient(address=self.address, private_key=self.private_key, network=self.network)

        self.to_query_symbol_dic = {}
        self.balance_dic = {}
        self.erc721address_token_dic = {}

    def check_setting(self):
        log_service_manager.write_log("[run] go check setting!")
        flag = True
        nft_list = self.setting["nft_list"]
        for nft_contract_dic in nft_list:
            erc721address = nft_contract_dic["erc721address"]
            token_id_list = nft_contract_dic["token_id_list"]
            for token_id_dic in token_id_list:
                token_id = token_id_dic["token_id"]
                min_buy_price = token_id_dic["min_buy_price"]
                fix_sell_price = token_id_dic["fix_sell_price"]
                if min_buy_price > fix_sell_price:
                    log_service_manager.write_log(f"[check_setting] [Error]"
                                                  f" erc721address:{erc721address}, token_id:{token_id},"
                                                  f" min_buy_price:{min_buy_price} > fix_sell_price:{fix_sell_price}.")
                    flag = False
                    return flag

            fee_ratio, tax_ratio, tax_receiver, erc20address = self.client.get_auction_param(erc721address)
            log_service_manager.write_log(f"[check_setting] erc20address:{erc20address}")
            if erc20address == ETH_ADDRESS:
                token = self.client.get_main_symbol_token()
            else:
                token = self.client.get_token(erc20address)
            self.to_query_symbol_dic[token.symbol] = (copy(token), erc20address)
            self.erc721address_token_dic[erc721address] = token

        return flag

    def update_account_balance(self):
        log_service_manager.write_log("[update_account_balance]")
        query_items = list(self.to_query_symbol_dic.items())
        for symbol, two_items in query_items:
            token, erc20address = two_items
            balance = self.client.get_balance_from_contract(Web3.toChecksumAddress(erc20address))
            self.balance_dic[token.symbol.lower()] = balance
        log_service_manager.write_log(f"[update_account_balance] balance_dic:{self.balance_dic}!")

    def run(self):
        '''
        1.查询nft 列表里的 NFT 的价格，如果低于买入价，则买入，然后用卖出价卖出
        '''
        flag = self.check_setting()
        if not flag:
            log_service_manager.write_log("[run] program exit!")
            return

        while True:
            log_service_manager.write_log("[run] MazeBuyMachine running!")
            try:
                self.update_account_balance()
                nft_list = self.setting["nft_list"]
                for nft_contract_dic in nft_list:
                    erc721address = nft_contract_dic["erc721address"]
                    token_id_list = nft_contract_dic["token_id_list"]
                    for token_id_dic in token_id_list:
                        token_id = token_id_dic["token_id"]
                        min_buy_price = token_id_dic["min_buy_price"]
                        fix_sell_price = token_id_dic["fix_sell_price"]
                        log_service_manager.write_log(f"[run] now work:{erc721address}:{token_id}!")

                        seller, deposit, current_price, start_at = self.client.get_auction(erc721address, token_id)
                        log_service_manager.write_log(f"[run] seller:{seller}, deposit:{deposit}, "
                                                      f" current_price:{current_price}, start_at:{start_at}!")

                        token = self.erc721address_token_dic.get(erc721address)
                        if seller == self.address:
                            if current_price < min_buy_price:
                                log_service_manager.write_log(f"[run] increase, current_price:{current_price}"
                                                              f" < min_buy_price:{min_buy_price}!")
                                to_increase_deposit = int((min_buy_price - current_price) / 10)
                                balance = self.balance_dic.get(token.symbol.lower())
                                log_service_manager.write_log(f"[run] token.symbol:{token.symbol},"
                                                              f" new deposit:{deposit},"
                                                              f" to_increase_deposit:{to_increase_deposit},"
                                                              f" balance:{balance}")

                                if balance > to_increase_deposit:
                                    log_service_manager.write_log(f"[run] to_increase_deposit:{to_increase_deposit}!")
                                    transaction, tx_params = self.client.increase_deposit(
                                        erc721address, token_id, to_increase_deposit)

                                    log_service_manager.write_log(f"[run] transaction:{transaction}"
                                                                  f", tx_params:{tx_params}!")
                                    data = self.client.signed_and_send(transaction, tx_params)
                                    log_service_manager.write_log(f"[run] send data:{data}!")
                                else:
                                    log_service_manager.write_log(f"[run] 1: balance not enough!")
                        else:
                            if current_price < min_buy_price:
                                log_service_manager.write_log(f"[run] go buy, current_price:{current_price}"
                                                              f" < min_buy_price:{min_buy_price}!")
                                deposit = int(fix_sell_price / 10)
                                will_use_amount = self.client.get_need_bid_amount(deposit, erc721address, token_id)

                                balance = self.balance_dic.get(token.symbol.lower())
                                log_service_manager.write_log(f"[run] token.symbol:{token.symbol},"
                                                              f" new deposit:{deposit},"
                                                              f" will_use_amount:{will_use_amount},"
                                                              f" balance:{balance}")
                                if balance > will_use_amount:
                                    log_service_manager.write_log(f"[run] balance:{balance} "
                                                                  f" > will_use_amount:{will_use_amount}!")
                                    transaction, tx_params = self.client.bid_auction(
                                        erc721address, token_id, deposit)
                                    log_service_manager.write_log(f"[run] transaction:{transaction}"
                                                                  f", tx_params:{tx_params}!")
                                    data = self.client.signed_and_send(transaction, tx_params)
                                    log_service_manager.write_log(f"[run] send data:{data}!")
                                else:
                                    log_service_manager.write_log(f"[run] 2: balance not enough!")

            except Exception as ex:
                log_service_manager.write_log(f"[run] ex:{ex}!")

            time.sleep(60 * 3)


if __name__ == "__main__":
    maze_buy_machine = MazeBuyMachine("config_env.json")
    maze_buy_machine.run()
