# 获得超导每日交易额,用于计算手续费
# 手续费 = 每日交易额 * 0.003

import requests

import json


# pretty print is used to print the output in the console in an easy to read format


# function to use requests.post to make an API call to the subgraph url
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
        raise Exception('Query failed. return code is {}.      {}'.format(request.status_code, query))


# address = "0x34e04379327ec76ad1b77c02f05d4977b6be88fd"
address = "0x6c409ceb8f2afea52698d34493c415b9178d539b".lower()


def get_btm_num_from_address(address):
    query_data_js = {
        "operationName": "liquidityPositions",
        "variables": {
            "user": address
        },
        "query": "query liquidityPositions($user: Bytes!) "
                 "{liquidityPositions(where: {user: $user}) "
                 "{pair {\n      id\n      reserve0\n      reserve1\n      reserveUSD\n      token0 {\n        id\n        symbol\n        derivedETH\n        __typename\n      }\n      token1 {\n        id\n        symbol\n        derivedETH\n        __typename\n      }\n      totalSupply\n      __typename\n    }\n    liquidityTokenBalance\n    __typename\n  }\n}\n"
    }
    data = run_query(query_data_js)

    total_usd_val = 0
    for dic in data["data"]["liquidityPositions"]:
        token0name = dic["pair"]["token0"]["symbol"]
        token1name = dic["pair"]["token1"]["symbol"]
        symbol = f"{token0name}-{token1name}".lower()
        # 计算出该池子的USD 值
        pair_usd_val = float(dic["liquidityTokenBalance"]) / float(dic["pair"]["totalSupply"]) * float(
            dic["pair"]["reserveUSD"])
        print(symbol, pair_usd_val)

        total_usd_val += pair_usd_val

    btm_price_ticker = requests.get(
        "http://bcapi.movapi.com/flashex/v1/swap-assets-info?main_chain=ethereum&symbol=usdt&amount=10")
    price = btm_price_ticker.json()["data"]["price"]

    return total_usd_val / float(price)


sum_btm_val = get_btm_num_from_address(address)
print("sum_btm:", sum_btm_val)
