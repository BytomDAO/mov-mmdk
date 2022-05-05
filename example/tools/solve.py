import requests
import getpass
import time

import eth_account

from web3 import Web3

from bmc_sdk.constants import Direction
from bmc_sdk.bmc_client import BmcClient
from bmc_sdk.constants import EthNet

from bmc_sdk.log_service import log_service_manager


def run():
    keystore_file_path = "./eth_keystore.json"
    passwd = getpass.getpass("请输入你的密码： ")

    with open(keystore_file_path) as keyfile:
        encrypted_key = keyfile.read()

        provider = "https://mainnet.bmcchain.com"
        use_w3 = Web3(
            Web3.HTTPProvider(provider, request_kwargs={"timeout": 60})
        )
        private_key = use_w3.eth.account.decrypt(encrypted_key, passwd)
        work_address = eth_account.Account.from_key(private_key).address

        client = BmcClient(address=work_address, private_key=private_key,
                           network=EthNet.BmcMainNet.value, provider=provider)
        volume = 0.001
        use_symbol = "btm_btc"
        direction = Direction.SHORT.value
        log_service_manager.write_log(f"[work_client] use_symbol:{use_symbol}")
        price = client.get_sell_price(use_symbol, volume)
        log_service_manager.write_log(f"[work_client] get_sell_price {use_symbol}, {price}!")
        transaction, tx_params = client.simple_trade(use_symbol, direction, price, volume)
        log_service_manager.write_log(f"[work_client] transaction:{transaction}, tx_params:{tx_params}")
        data = client.signed_and_send(transaction, tx_params)
        log_service_manager.write_log(f"[work_client] data:{data}")


run()
