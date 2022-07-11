# 获得超导每日交易额,用于计算手续费
# 手续费 = 每日交易额 * 0.003

import requests
# pretty print is used to print the output in the console in an easy to read format
from pprint import pprint


# function to use requests.post to make an API call to the subgraph url
def run_query(q):
    headers = {
        'Accept': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36'
    }
    # endpoint where you are making the request
    url = "https://api.sup.finance/subgraphs/name/davekaj/uniswap?asdadsasd"
    # url = "https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v2"
    request = requests.post(url,
                            '',
                            json={'query': q},
                            headers=headers)

    if request.status_code == 200:
        return request.json()
    else:
        raise Exception('Query failed. return code is {}.      {}'.format(request.status_code, query))


query = '''
{
  liquidityPositionSnapshots {
    id
    user{
      id
    }
    pair{
      token0{
        id
        symbol
      }
      token1{
        id
        symbol
      }
      totalSupply
    }
    reserveUSD
    liquidityTokenBalance
  }
}
'''

# {
#   "operationName": "lps",
#   "variables": {
#     "pair": "0xc3675ed34aeefcdf5980ae23ce2d198e591735f1"
#   },
#   "query": "query lps($pair: Bytes!) {\n  liquidityPositions(where: {pair: $pair}, orderBy: liquidityTokenBalance, orderDirection: desc, first: 10) {\n    user {\n      id\n      __typename\n    }\n    pair {\n      id\n      __typename\n    }\n    liquidityTokenBalance\n    __typename\n  }\n}\n"
# }
result = run_query(query)

# print the results
# print('Print Result - {}'.format(result))
# print('#############')

f = open("out.csv", "w")
data = result["data"]["liquidityPositionSnapshots"]
for dic in data:
    user_id = dic["user"]["id"]
    token0name = dic["pair"]["token0"]["symbol"]
    token1name = dic["pair"]["token1"]["symbol"]
    reserveUSD = dic["reserveUSD"]
    totalSupply = dic["pair"]["totalSupply"]
    liquidityTokenBalance = dic["liquidityTokenBalance"]
    ans = float(liquidityTokenBalance) / float(totalSupply) * float(reserveUSD)
    line = f"{user_id},{token0name}-{token1name},{reserveUSD}\n"
    f.write(line)
f.close()
