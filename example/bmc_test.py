# coding=utf-8

from bmc_sdk.bmc_client import BmcClient, EthNet, Direction


def run_v2():
    btm_client = BmcClient(address="0x2B522cABE9950D1153c26C1b399B293CaA99FcF9",
                             private_key="1aba488300a9d7297a315d127837be4219107c62c61966ecdf7a75431d75cc61",
                             network=EthNet.BmcTestNet.value,
                             provider="", version=2)

    price = btm_client.get_buy_price(symbol="mag_btm", volume=0.01)
    print(price)

    transaction, tx_params = btm_client.trade("mag_btm", Direction.LONG.value, price, 0.01)
    print(transaction, tx_params)

    print(btm_client.signed_and_send(transaction, tx_params))


def run_v3():
    btm_client = BmcClient(address="0x2B522cABE9950D1153c26C1b399B293CaA99FcF9",
                             private_key="1aba488300a9d7297a315d127837be4219107c62c61966ecdf7a75431d75cc61",
                             network=EthNet.BmcTestNet.value,
                             provider="", version=3)

    price = btm_client.get_buy_price(symbol="mag_btm", volume=0.01)
    print(price)

    transaction, tx_params = btm_client.trade("mag_btm", Direction.LONG.value, price, 0.01)
    print(transaction, tx_params)

    print(btm_client.signed_and_send(transaction, tx_params))


#run_v2()
run_v3()



