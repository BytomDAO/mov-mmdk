import requests
import getpass
import time

import eth_account
import os

from web3 import Web3
import json
import codecs
from collections import defaultdict

from bmc_sdk.constants import Direction
from bmc_sdk.bmc_client import BmcClient
from bmc_sdk.constants import EthNet
from bmc_sdk.bmc_client import ETH_ADDRESS

from bmc_sdk.log_service import log_service_manager
from bmc_sdk.maze_client import MazeClient
from bmc_sdk.util import load_json, save_json


class MazeMachine(object):
    def __init__(self, encrypt_password, network, file_name="account.json"):
        self.network = network
        self.encrypt_password = encrypt_password
        self.account = None
        self.private_key = ""
        self.address = ""
        self.keystore = ""

        self.client = None

        self.contract_dic = {}
        self.balance_dic = {}

        self.file_name = file_name

        self.load_account()

    def load_account(self, file_name=""):
        '''
        从默认路径导入账户
        '''
        if not file_name:
            file_name = self.file_name
        if os.path.exists(file_name):
            account_dic = load_json(file_name)
            self.private_key = account_dic["private_key"]
            self.address = account_dic["address"]
            self.keystore = account_dic["keystore"]
            self.client = MazeClient(address=self.address, private_key=self.private_key, network=self.network)
            log_service_manager.write_log(f"[load_account] address:{self.address}, file_name:{file_name}!")
        else:
            log_service_manager.write_log(f"[load_account] not found filename:{file_name}!")

    def output_account(self, file_name=""):
        '''
        导出账户到默认路径
        '''
        if not file_name:
            file_name = self.file_name
        account_dic = {
            "address": self.address,
            "private_key": self.private_key,
            "keystore": self.keystore
        }
        save_json(file_name, account_dic)
        log_service_manager.write_log("[output_account] ")

    def create_account(self):
        w3 = Web3()
        self.account = w3.eth.account.create()
        self.private_key = self.account.key.hex()
        self.address = self.account.address
        self.keystore = self.account.encrypt(self.encrypt_password)

        self.output_account()

        # print(self.account.address, self.address, self.private_key)

        log_service_manager.write_log(f"[create_account] your account:"
                                      f" private_key:{self.private_key},"
                                      f" address:{self.address},"
                                      f" keystore:{self.keystore}")

        self.client = MazeClient(address=self.address, private_key=self.private_key, network=self.network)

        return self.private_key, self.address, self.keystore

    def update_account(self):
        log_service_manager.write_log("[update_account] not support now!")

    def query_account_info(self, address):
        '''
        查询账户信息（余额，持有NFT）
        :param address: 账户地址
        :return:
        '''
        log_service_manager.write_log(f"[query_account] address:{address}!")

        if not self.contract_dic:
            if not self.client:
                self.client = MazeClient(address=address, private_key="", network=self.network)
            asset_data = self.client.get_balance_from_bmc_wallet()
            log_service_manager.write_log(f"[query_account] account:{asset_data}!")

            query_assets_contracts = [(dic["asset"]["symbol"].lower(),
                                       dic["asset"]["contract_address"].lower()) for dic in asset_data["data"]]
            for asset, contract_address in query_assets_contracts:
                self.contract_dic[asset] = contract_address

        ## 输出账户余额
        for asset, contract_address in list(self.contract_dic.items()):
            if asset == "btm":
                contract_address = ETH_ADDRESS
            bal = self.client.get_token_balance(contract_address)
            self.balance_dic[asset] = bal

            print(f"[query_account] {asset}:{bal}")

        ## 输出持有哪些nft
        data = self.client.query_erc721_by_address(address)
        for dic in data["data"]["tokens"]:
            contract_address = dic["contract"]["id"]
            token_id = dic["tokenId"]
            print(f"[query_account] now has nft: {contract_address}:{token_id}")
            seller, deposit, current_price, started_at = self.client.get_auction(
                Web3.toChecksumAddress(contract_address), int(token_id))
            print(f"[query_account] {seller}, {deposit}, {current_price}, {started_at}!")

    def query_account_income(self, address):
        '''
        查询账户的盈利情况 （买入的，卖出的， 差价）
        :param address: 账户地址
        :return:
        '''
        data = self.client.query_buyer_by_address(address)
        log_service_manager.write_log(f"[query_account_income] data:{data}!")
        data = self.client.query_seller_by_address(address)
        log_service_manager.write_log(f"[query_account_income] data:{data}!")

    def buy_nft(self, erc721address, token_id, deposit):
        '''
        对指定NFT进行购买
        :param erc721address:
        :param contract_address:
        :param token_id:
        '''
        log_service_manager.write_log("[buy_nft] buy_nft!")
        data = self.client.bid_auction(erc721address, token_id, deposit)
        log_service_manager.write_log(f"[buy_nft] data:{data}!")

    def adjust_nft_caution_money(self, erc721address, token_id, amount):
        '''
        对指定NFT进行保证金调整
        :param erc721address:
        :param token_id:
        :param amount:
        '''
        log_service_manager.write_log("[adjust_nft_caution_money] ")
        if amount > 0:
            data = self.client.increase_deposit(erc721address, token_id, amount)
        else:
            data = self.client.decrease_deposit(erc721address, token_id, abs(amount))
        log_service_manager.write_log(f"[adjust_nft_caution_money] data:{data}!")

    def apply_offer(self, erc721address, token_id, offer_price, deposit):
        '''
        :param contract_address:
        :param token_id:
        :param amount:
        :return:
        '''
        log_service_manager.write_log("[apply_offer]")
        deadline = int(time.time()) + 10 * 60
        data = self.client.apply_offer(erc721address, token_id, offer_price, deposit, deadline)
        log_service_manager.write_log(f"[apply_offer] data:{data}!")

    def give_nft(self, contract_address, token_id, to_address):
        '''
        :param contract_address:
        :param token_id:
        :param to_address:
        :return:
        '''
        log_service_manager.write_log("[give_nft]")

    @staticmethod
    def print_menu():
        print("0.从默认路径导入账户")
        print("1.创建账户")
        print("2.更改账户信息")
        print("3.查看账户信息")
        print("4.查看账户盈利情况")
        print("5.对指定NFT进行购买")
        print("6.对指定NFT进行保证金调整")
        print("7.对指定NFT进行询价购买")
        print("8.对指定NFT进行赠送")


def test1():
    password = "123"
    maze_machine = MazeMachine(password, EthNet.BmcTestNet.value)
    maze_machine.create_account()

    keystore = maze_machine.keystore
    print(keystore)

    private_key = Web3().eth.account.decrypt(keystore, password)
    print(private_key.hex())


def test2():
    client = MazeClient(address="0x88ad4fd94a05602e595101a3e3171f91289c8f6b",
                        private_key="", network=EthNet.BmcTestNet.value)
    # data = client.query_erc721_by_address("0x88ad4fd94a05602e595101a3e3171f91289c8f6b")
    # print(data)

    all_dic = defaultdict(float)

    data = client.query_buyer_by_address("0x673f03b59a0484cb3e601b46f0f017a0757446c7")
    print(data)

    for dic in data["data"]["histories"]:
        buyer = dic["buyer"]
        erc721Address = dic["erc721Address"]
        tokenId = dic["id"]
        price = float(dic["price"])
        seller = dic["seller"]

        fee_ratio, tax_ratio, tax_receiver, erc20_address \
            = client.get_auction_param(Web3.toChecksumAddress(erc721Address))
        token = client.get_token(erc20_address)

        all_dic[erc721Address] -= price
        print("buyer", erc20_address, price)

    data = client.query_seller_by_address("0x673f03b59a0484cb3e601b46f0f017a0757446c7")
    print(data)

    for dic in data["data"]["histories"]:
        buyer = dic["buyer"]
        erc721Address = dic["erc721Address"]
        _id = dic["id"]
        price = float(dic["price"])
        seller = dic["seller"]

        fee_ratio, tax_ratio, tax_receiver, erc20_address = client.get_auction_param(Web3.toChecksumAddress(erc721Address))

        all_dic[erc721Address] += price
        print("seller", erc20_address, price)

    print("all_dic", all_dic)

    data = client.query_erc721_by_address("0x673f03b59a0484cb3e601b46f0f017a0757446c7")
    print(data)

    for dic in data["data"]["tokens"]:
        erc721_address = dic["contract"]["id"]
        token_id = dic["tokenId"]

        print("why", erc721_address, token_id)
        # seller, deposit, current_price, started_at = client.get_auction(
        #     Web3.toChecksumAddress(erc721_address), int(token_id))
        # print(f"[get_auction] {seller}, {deposit}, {current_price}, {started_at}!")


def run():
    password = getpass.getpass("请输入你的密码： ")
    maze_machine = MazeMachine(password, EthNet.BmcTestNet.value)
    maze_machine.print_menu()
    while True:
        try:
            msg = input("请输入您的操作:").strip()
            print(msg)
            if msg == "1":
                # 创建账户
                maze_machine.create_account()

            elif msg == "2":
                # 更新账户
                maze_machine.update_account()

            elif msg == "3":
                # 查看账户信息
                address = input("请输入您要查看的地址:")
                maze_machine.query_account_info(address)

            elif msg == "4":
                # 输入你要查看的地址
                address = input("请输入您要查看的地址:")
                maze_machine.query_account_income(address)

            elif msg == "5":
                erc721address = input("要购买的nft合约地址:")
                token_id = input("要购买的nft token ID:")
                deposit = input("要存储的金额:")
                maze_machine.buy_nft(erc721address, int(token_id), int(deposit))

            elif msg == "6":
                contract_address = input("要调整的nft合约地址:")
                token_id = input("要购买的nft token ID:")
                amount = input("调整的保证金金额,正数增加,负数减少:")
                maze_machine.adjust_nft_caution_money(contract_address, int(token_id), int(amount))

            elif msg == "7":
                contract_address = input("要询价购买的nft合约地址:")
                token_id = input("要询价购买的nft token ID:")
                offer_price = input("询价价格:")
                deposit = input("要存储的保证金金额:")
                maze_machine.apply_offer(contract_address, int(token_id), offer_price, deposit)

            elif msg == "8":
                contract_address = input("要赠送的nft合约地址:")
                token_id = input("要赠送的nft token ID:")
                to_address = input("要转去的nft地址:")
                maze_machine.give_nft(contract_address, int(token_id), to_address)

        except Exception as ex:
            log_service_manager.write_log(f"[run] ex:{ex}!")


if __name__ == "__main__":
    # test()
    test2()
    # run()
