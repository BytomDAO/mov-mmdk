from time import sleep
import sys

import getpass
from web3 import Web3
import eth_account

from web3.types import (
    HexBytes,
)
from bmc_sdk.log_service import log_service_manager

from bmc_sdk.constants import EthNet
from bmc_sdk.bmc_client import BmcClient


def load_info(input_txt):
    sum_amount = 0
    total_num = 0
    arr = []
    log_service_manager.write_log(f"[load_info] your file:{input_txt}!")
    f = open(input_txt, "r")
    for line in f:
        line = line.strip()
        if line:
            address, amount = line.split(',')
            sum_amount += float(amount)
            total_num += 1
            arr.append((address, float(amount)))
            log_service_manager.write_log(f"[load_info] to_address:{address}, amount:{amount}!")
    f.close()
    log_service_manager.write_log(f"[load_info] total_num:{total_num}, sum_amount:{sum_amount}")
    return arr


def run(token_symbol, input_txt):
    info_arr = load_info(input_txt)
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

        send_amount_dic = {}
        to_work_dic = {}
        for to_address, amount in info_arr:
            send_amount_dic[to_address] = amount
            to_work_dic[to_address] = ""

        while True:
            now_loop_arr = list(to_work_dic.items())
            if len(now_loop_arr) == 0:
                break

            for to_address, tx_id in now_loop_arr:
                amount = send_amount_dic[to_address]
                try:
                    if tx_id:
                        transaction_info = client.get_transaction_receipt(tx_id)
                        if transaction_info:
                            status = transaction_info.status
                            if status:
                                log_service_manager.write_log(f"[run] to_address:{to_address} amount:{amount} success!")
                                if to_address in to_work_dic.keys():
                                    del to_work_dic[to_address]
                            else:
                                log_service_manager.write_log(f"[run] failed! tx_id:{tx_id} status:{status}!")
                                log_service_manager.write_log(
                                    f"[run] failed! go to transfer {to_address} {amount} again!")

                                transaction_hash = client.transfer(to_address, amount, token_symbol)
                                if transaction_hash:
                                    to_work_dic[to_address] = HexBytes(transaction_hash).hex()
                    else:
                        transaction_hash = client.transfer(to_address, amount, token_symbol)
                        if transaction_hash:
                            to_work_dic[to_address] = HexBytes(transaction_hash).hex()
                except Exception as ex:
                    log_service_manager.write_log(f"[run] ex:{ex}!")

            sleep(10)

        log_service_manager.write_log("[run] all transfer finished!")


if __name__ == "__main__":
    '''
    python3 bmc_batch_send.py btm btm.txt
    python3 bmc_batch_send.py usdt usdt.txt
    '''
    log_service_manager.write_log(f"[main] sys_config:{sys.argv}")

    asset = sys.argv[1]
    input_file = sys.argv[2]
    run(asset.lower(), input_file)
