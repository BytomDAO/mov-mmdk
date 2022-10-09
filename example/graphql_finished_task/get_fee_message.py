import requests
import time
from pprint import pprint


# function to use requests.post to make an API call to the subgraph url
def run_query(query_data_js):
    headers = {
        'Accept': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36'
    }
    # endpoint where you are making the request
    url = "https://api.sup.finance/subgraphs/name/davekaj/uniswap"
    # url = "https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v2"

    request = requests.post(url,
                            '',
                            json={'query': query_data_js},
                            headers=headers)
    if request.status_code == 200:
        return request.json()
    else:
        raise Exception('Query failed. return code is {}.      {}'.format(request.status_code, query_data_js))

'''
{
  uniswapDayDatas(where:{date_gte:1649030400}){
    id
    date
    dailyVolumeUSD
  }
}
'''
query = '''
{
  uniswapDayDatas(where:{date_gte:%s}){
    id
    date
    dailyVolumeUSD
  }
}
'''

start_date = "2022-07-01"
start_dt = int(time.mktime(time.strptime(start_date, "%Y-%m-%d")))
run_query_msg = query % start_dt
result = run_query(run_query_msg)

ans_arr = [(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(dic["date"])), dic["dailyVolumeUSD"])
           for dic in result["data"]["uniswapDayDatas"]]
ans_arr.sort()
vv = 0
f = open("out.csv", "w")
for dt, score in ans_arr:
    line = f"{dt},{score}"
    f.write(line + "\n")
    vv += float(score)
f.close()

print(vv * 0.0003 / 6)
