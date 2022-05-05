import requests
import getpass
import time

import eth_account

from web3 import Web3

from bmc_sdk.constants import Direction
from bmc_sdk.bmc_client import BmcClient
from bmc_sdk.constants import EthNet

from bmc_sdk.log_service import log_service_manager


def run_query(query_data_js):
    headers = {
        'Accept': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36'
    }
    # endpoint where you are making the request
    url = "https://api.sup.finance/subgraphs/name/davekaj/uniswap?asdadsasd"
    # url = "https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v2"

    request = requests.post(url,
                            '',
                            json=query_data_js,
                            headers=headers)
    if request.status_code == 200:
        return request.json()
    else:
        raise Exception('Query failed. return code is {}.      {}'.format(request.status_code, query_data_js))


query_pair_js = {
    "query":
        '''
        {
            pairs {
              id
              token0 {
                id
                symbol
              }
              token1 {
                id
                symbol
              }
              totalSupply
              reserveUSD
            }
        }
        '''
}


def work_client(pairs, client):
    #####
    # 取出所有交易lp交易对
    #####
    pair_use_dic = {}
    all_pair_sets = set([])
    for pair_dic in pairs:
        pair_id = pair_dic["id"]
        token0_id = pair_dic["token0"]["id"]
        token1_id = pair_dic["token1"]["id"]
        token0name = pair_dic["token0"]["symbol"]
        token1name = pair_dic["token1"]["symbol"]

        symbol = f"{token0name.lower()}_{token1name.lower()}"
        pair_use_dic[symbol] = pair_dic
        all_pair_sets.add(symbol)

        volume = client.get_token_balance(pair_id)
        log_service_manager.write_log(f"[work_client] symbol:{symbol}, volume:{volume}"
                                      f", pair_id:{Web3.toChecksumAddress(pair_id)}!")
        if volume > 0:
            log_service_manager.write_log(f"[work_client] pair_id:{Web3.toChecksumAddress(pair_id)},"
                                          f" {Web3.toChecksumAddress(token0_id)},"
                                          f" {Web3.toChecksumAddress(token1_id)},"
                                          f" {volume},"
                                          f" {Web3.toChecksumAddress(client.address)}")
            data = client.remove_liquidity_v2(Web3.toChecksumAddress(pair_id),
                                              token0_id, token1_id, volume, client.address)
            log_service_manager.write_log(f"[work_client] data:{data}!")

    return

    # 后面资产兑换的先不换，比较繁琐

    ####
    # 对所有资产先全部换成btm
    ####
    asset_data = client.get_balance_from_bmc_wallet()
    for asset_dic in asset_data["data"]:
        asset = asset_dic["asset"]["symbol"].lower()
        contract_address = asset_dic["asset"]["contract_address"]
        if asset in ["sup", "btc"]:
            log_service_manager.write_log(f"[work_client] no need to work:{asset}")
            continue

        if asset == "btm":
            # change to wbtm
            contract_address = "0xcd109943f45587D589cAE7b66F3FcF4a3097A288"
        log_service_manager.write_log(f"[work_client] go to approve asset:{asset} contract_address:{contract_address}!")
        client.check_and_go_aprove(Web3.toChecksumAddress(contract_address))
        t1 = asset + "_wbtm"
        t2 = "wbtm_" + asset
        volume = float(asset_dic["balance"]) - 1e-8
        # volume = client.get_balance_from_contract(asset)
        if volume > 1e-8:
            log_service_manager.write_log(f"[work_client] asset:{asset} volume:{volume}, now do!")

            if t1 in all_pair_sets or t2 in all_pair_sets:
                log_service_manager.write_log(f"[work_client] t1:{t1} t2:{t2}?")
                if t1 in all_pair_sets:
                    use_symbol = t1.replace('wbtm', 'btm')
                    direction = Direction.SHORT.value
                    log_service_manager.write_log(f"[work_client] use_symbol:{use_symbol}")
                    price = client.get_sell_price(use_symbol, volume)
                    log_service_manager.write_log(f"[work_client]get_sell_price {use_symbol},{price}!")
                    transaction, tx_params = client.simple_trade(use_symbol, direction, price, volume)
                else:
                    use_symbol = t2.replace('wbtm', 'btm')
                    direction = Direction.LONG.value
                    log_service_manager.write_log(f"[work_client] use_symbol:{use_symbol}")
                    price = client.get_buy_price(use_symbol, volume)
                    log_service_manager.write_log(f"[work_client] get_buy_price {use_symbol},{price}!")
                    transaction, tx_params = client.simple_trade(use_symbol, direction, price, volume/price)
                # pair_dic = pair_use_dic[use_symbol]
                # pair_id = pair_dic["id"]
                log_service_manager.write_log(f"[work_client] transaction:{transaction}, tx_params:{tx_params}")
                data = client.signed_and_send(transaction, tx_params)
                log_service_manager.write_log(f"[work_client] data:{data}")
        else:
            log_service_manager.write_log(f"[work_client] asset:{asset} volume:{volume}, so continue!")

    # 将 btm 换成 sup
    time.sleep(5)
    volume = client.get_balance("btm") - 1
    if volume > 1:
        use_symbol = "sup_btm"
        direction = Direction.LONG.value
        log_service_manager.write_log(f"[work_client] use_symbol:{use_symbol}")
        price = client.get_buy_price(use_symbol, volume)
        log_service_manager.write_log(f"[work_client] get_buy_price {use_symbol}, {price}!")
        transaction, tx_params = client.simple_trade(use_symbol, direction, price, volume / price)
        log_service_manager.write_log(f"[work_client] transaction:{transaction}, tx_params:{tx_params}")
        data = client.signed_and_send(transaction, tx_params)
        log_service_manager.write_log(f"[work_client] data:{data}")


def run(pairs):
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

        work_client(pairs, client)


result = run_query(query_pair_js)
pairs = result["data"]["pairs"]
log_service_manager.write_log(f"pairs:{pairs}")

run(pairs)
