# 获得超导每日交易额,用于计算手续费
# 手续费 = 每日交易额 * 0.003

import requests
import time
# pretty print is used to print the output in the console in an easy to read format
from pprint import pprint

from tumbler.function import get_str_dt_use_timestamp


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
    transactions(first: 1000, timestamplt: %s, filter:{name:{eq : "123"}},orderBy: timestamp, orderDirection: desc) {
      swaps(orderBy: timestamp, orderDirection: desc) {
        transaction {
          id
          timestamp
          __typename
        }
        pair {
          token0 {
            id
            symbol
            __typename
          }
          token1 {
            id
            symbol
            __typename
          }
          __typename
        }
        amount0In
        amount0Out
        amount1In
        amount1Out
        amountUSD
        to
        __typename
      }
      __typename
    }
}
'''

now_time = int(time.time())
end_start_time = int(time.time()) - 3600 * 24

f = open("transactions.csv", "w")
while now_time > end_start_time:
    print("start:", now_time, end_start_time)
    query_msg = str(query % str(now_time))
    print(query_msg)
    result = run_query(query_msg)
    #print(result["data"]["transactions"][0])

    for swap_dic in result["data"]["transactions"]:
        # print(swap_dic)
        # print(swap_dic["swaps"])
        arr = swap_dic["swaps"]
        for dic in arr:
            # print(dic)
            transcation_id = dic["transaction"]["id"]
            timestamp = dic["transaction"]["timestamp"]
            pair_token0_name = dic["pair"]["token0"]["symbol"]
            amount0In = dic["amount0In"]
            amount0Out = dic["amount0Out"]

            pair_token1_name = dic["pair"]["token1"]["symbol"]
            amount1In = dic["amount1In"]
            amount1Out = dic["amount1Out"]
            arr = [transcation_id, get_str_dt_use_timestamp(timestamp, 1), pair_token0_name, pair_token1_name, amount0In, amount0Out, amount1In, amount1Out]
            line = ','.join([str(x) for x in arr])
            # print(arr)
            
            now_time = int(timestamp)
            f.write(line + "\n")
        f.flush()
    print("end:", now_time, end_start_time)

f.close()




