import requests
import getpass
import time

import eth_account
import os

from web3 import Web3
import json
import codecs

from bmc_sdk.constants import Direction
from bmc_sdk.bmc_client import BmcClient
from bmc_sdk.constants import EthNet

from bmc_sdk.log_service import log_service_manager
from bmc_sdk.maze_client import MazeClient


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


def work_client(client):
    contract_address = Web3.toChecksumAddress("0x0b45Ad27866C8E05ED610cd8A0ec78de94B18202")
    log_service_manager.write_log("[work_client]")
    data = client.get_supported_contracts()
    log_service_manager.write_log(f"[work_client] get_supported_contracts: {data}")
    print(client.address, client.maze_contract_address)
    data = client.is_approval_for_all(client.address, client.maze_contract_address)
    log_service_manager.write_log(f"[work_client] is_approval_for_all: {data}")

    # data = client.check_and_go_approve_for_maze(contract_address)
    # log_service_manager.write_log(f"[work_client] check_and_go_approve, data:{data}")
    #
    # transaction, tx_params = client.set_approval_for_all(client.maze_contract_address, True)
    # log_service_manager.write_log(f"[work_client] set_approval_for_all transaction:{transaction},"
    #                               f" tx_params:{tx_params}")
    # data = client.signed_and_send(transaction, tx_params)
    # log_service_manager.write_log(f"[work_client] data:{data}")

    erc721address = "0x1819BFe00C0c0aEe24B88aCE7bff36d574d70180"
    token_id = 23
    #token_id = 24
    deposit = 1004
    # transaction, tx_params = client.create_auction(erc721address, token_id, deposit, contract_address=contract_address)
    # print(transaction, tx_params)
    # data = client.estimate_gas(transaction)
    # print(data)
    # data = client.signed_and_send(transaction, tx_params)
    # log_service_manager.write_log(f"[work_client] create_auction transaction:{transaction}, tx_params:{tx_params}")
    # log_service_manager.write_log(f"[work_client] data:{data}")

    # amount = 2
    # transaction, tx_params = client.increase_deposit(erc721address, token_id, amount, contract_address)
    # log_service_manager.write_log(f"[work_client] increase_deposit transaction:{transaction}, tx_params:{tx_params}")
    # data = client.signed_and_send(transaction, tx_params)
    # log_service_manager.write_log(f"[work_client] data:{data}")

    # transaction, tx_params = client.decrease_deposit(erc721address, token_id, amount, contract_address)
    # data = client.signed_and_send(transaction, tx_params)
    # log_service_manager.write_log(f"[work_client] decrease_deposit transaction:{transaction}, tx_params:{tx_params}")
    # log_service_manager.write_log(f"[work_client] data:{data}!")

    # transaction, tx_params = client.bid_auction(erc721address, token_id, deposit, contract_address)
    # data = client.estimate_gas(transaction)
    # print(data)
    # data = client.signed_and_send(transaction, tx_params)
    # log_service_manager.write_log(f"[work_client] bid_auction transaction:{transaction}, tx_params:{tx_params}")
    # log_service_manager.write_log(f"[work_client] data:{data}!")

    offer_price = 888
    deadline = int(time.time()) + 10 * 60
    deadline = 1749413950
    transaction, tx_params = client.apply_offer(erc721address, token_id, offer_price, deposit, deadline)
    data = client.signed_and_send(transaction, tx_params)
    # log_service_manager.write_log(f"[work_client] apply_offer transaction:{transaction}, tx_params:{tx_params}")
    log_service_manager.write_log(f"[work_client] data:{data}!")

    # data = client.get_offers(erc721address, token_id)
    # log_service_manager.write_log(f"[work_client] get_offers data:{data}")

    data = client.get_auction(erc721address, token_id)
    log_service_manager.write_log(f"[work_client] get_auction data:{data}")

    # buyer = "0xa6Cb31B0A18AF665eafAf48EF6A05Bd8a4387309"
    # buyer = "0x2B522cABE9950D1153c26C1b399B293CaA99FcF9"
    # transaction, tx_params = client.accept_offer(erc721address, token_id, buyer)
    # data = client.estimate_gas(transaction)
    # print(data)
    # log_service_manager.write_log(f"[work_client] accept_offer transaction:{transaction}, tx_params:{tx_params}")
    # data = client.signed_and_send(transaction, tx_params)
    # log_service_manager.write_log(f"[work_client] data:{data}!")

    # transaction, tx_params = client.cancel_offer(erc721address, token_id)
    # data = client.estimate_gas(transaction)
    # data = client.signed_and_send(transaction, tx_params)
    # log_service_manager.write_log(f"[work_client] cancel_offer transaction:{transaction}, tx_params:{tx_params}")
    # log_service_manager.write_log(f"[work_client] data:{data}!")

    # data = client.get_auction_param(erc721address)
    # log_service_manager.write_log(f"[work_client] get_auction_param data:{data}")


def run1():
    keystore_file_path = "./eth_keystore.json"
    passwd = getpass.getpass("请输入你的密码： ")

    with open(keystore_file_path) as keyfile:
        encrypted_key = keyfile.read()

        provider = "https://testnet.bmcchain.com"
        use_w3 = Web3(
            Web3.HTTPProvider(provider, request_kwargs={"timeout": 60})
        )
        private_key = use_w3.eth.account.decrypt(encrypted_key, passwd)
        work_address = eth_account.Account.from_key(private_key).address

        client = MazeClient(address=work_address, private_key=private_key,
                            network=EthNet.BmcTestNet.value, provider=provider)

        work_client(client)


def run2():
    config_json = load_json("config_env.json")
    provider = "https://testnet.bmcchain.com"
    print(config_json)
    client = MazeClient(address=config_json["address"], private_key=config_json["private_key"],
                        network=EthNet.BmcTestNet.value, provider=provider)
    work_client(client)


# run1()
run2()
