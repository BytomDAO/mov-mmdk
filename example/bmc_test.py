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

    price = btm_client.get_sell_price(symbol="mag_btm", volume=0.01)
    print(price)

    transaction, tx_params = btm_client.trade("mag_btm", Direction.SHORT.value, price, 0.01)
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

    price = btm_client.get_sell_price(symbol="mag_btm", volume=0.01)
    transaction, tx_params = btm_client.trade("mag_btm", Direction.SHORT.value, price, 0.01)
    print(transaction, tx_params)

    print(btm_client.signed_and_send(transaction, tx_params))


def run_test():
    btm_client = BmcClient(address="0x2B522cABE9950D1153c26C1b399B293CaA99FcF9",
                           private_key="1aba488300a9d7297a315d127837be4219107c62c61966ecdf7a75431d75cc61",
                           network=EthNet.BmcTestNet.value,
                           provider="", version=2)
    print(btm_client.get_balance("mag"))
    print(btm_client.get_balance("btm"))


def run_bmc_wallet_main_test():
    btm_client = BmcClient(address="0xa6Cb31B0A18AF665eafAf48EF6A05Bd8a4387309",
                           private_key="37997d1c8ed25c36dc6790c0934dc9686959cee91436fd918d4aa21f0974cdfc",
                           network=EthNet.BmcMainNet.value,
                           provider="", version=2)
    print(btm_client.get_cross_assets())
    print(btm_client.get_balance_from_bmc_wallet())
    # print(btm_client.get_token_info_from_bmc_wallet("0x77197f46435d4cf8fb07953ad5ebc98ee6c8e7f1"))
    # print(btm_client.get_transaction_from_bmc_wallet("0x8B767C4A39599676CD897aB475d1CbAFE1ae1a8d", "0x09d67e0414af36bcd1276445b95a3dceafcc75c1c5a430c77ded073db9543d6e"))
    # print(btm_client.cross_to_main_chain("0x8B767C4A39599676CD897aB475d1CbAFE1ae1a8d",
    #                                      "0x8e173d5115e6706b8c35f80dc005a345da98c1c0",
    #                                      1))

    # btm
    print(btm_client.cross_to_main_chain("0xffffffffffffffffffffffffffffffffffffffff",
                                         "bn1qlc9jhf00w9mqsdczu2m8ehehhp3wgd6ls5njag",
                                         0.011))
    # sup
    # print(btm_client.cross_to_main_chain("0x77197f46435d4cf8fb07953ad5ebc98ee6c8e7f1",
    #                                      "bn1qlc9jhf00w9mqsdczu2m8ehehhp3wgd6ls5njag",
    #                                      0.000011))
    # usdt
    # print(btm_client.cross_to_main_chain("0x8b767c4a39599676cd897ab475d1cbafe1ae1a8d",
    #                                      "0x2B522cABE9950D1153c26C1b399B293CaA99FcF9",
    #                                      5,
    #                                      cross_fee="12.00000000"))

def run_bmc_wallet_test_test():
    btm_client = BmcClient(address="0xa277704db61f45cfff93e19811b311fb640d162c",
                           private_key="53026e58213a23534096b943e49ed3637ec6f693b15d34938d265753d24a4920",
                           network=EthNet.BmcTestNet.value,
                           provider="", version=2)
    print(btm_client.get_cross_assets())
    print(btm_client.get_balance_from_bmc_wallet())
    # print(btm_client.get_token_info_from_bmc_wallet("0x77197f46435d4cf8fb07953ad5ebc98ee6c8e7f1"))
    # print(btm_client.get_transaction_from_bmc_wallet("0x8B767C4A39599676CD897aB475d1CbAFE1ae1a8d", "0x09d67e0414af36bcd1276445b95a3dceafcc75c1c5a430c77ded073db9543d6e"))
    # print(btm_client.cross_to_main_chain("0x8B767C4A39599676CD897aB475d1CbAFE1ae1a8d",
    #                                      "0x8e173d5115e6706b8c35f80dc005a345da98c1c0",
    #                                      1))

    # btm
    # print(btm_client.cross_to_main_chain("0xffffffffffffffffffffffffffffffffffffffff",
    #                                      "tn1qxdl5x7esv6u0uzut0ehwlf0d9u4fkph080jf5p",
    #                                      0.011))
    # sup
    # print(btm_client.cross_to_main_chain("0x6affe5bfd41f7d8112e3ac74fc3b887e272521db",
    #                                      "bn1qlc9jhf00w9mqsdczu2m8ehehhp3wgd6ls5njag",
    #                                      0.000011))
    # usdt
    print(btm_client.cross_to_main_chain("0x8b0a0cc8f426549921317c52ef7abda24f0fa1cc",
                                         "0x2B522cABE9950D1153c26C1b399B293CaA99FcF9",
                                         5,
                                         cross_fee="0.04"))


# run_v2()
# run_v3()
# run_test()
run_bmc_wallet_main_test()
# run_bmc_wallet_test_test()
