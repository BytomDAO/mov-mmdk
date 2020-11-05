# MOV MMDK
Welcome trading

## Download

You can download flash dealer and sdk here(realease)(https://github.com/Bytom/mov-mmdk/releases)

## Wiki

You can see detail of the descripe of the interface here(https://github.com/Bytom/mov-mmdk/wiki)

You can learn more abount MOV here(https://developer.bymov.io/guide/mov_maker_preparation.html)

## Install SDK

```shell
#first:
pip3 install -r requirements.txt
python3 setup.py install

#then you can import like below:
from mov_sdk.mov_api import MovApi
```

## 1.Get SecretKey And Init

```python
api = MovApi(secret_key="")
config = api.init_from_mnemonic("stereo nominee miss click sock argue valid hole jelly vessel payment fork")
print(api.main_address)
print(api.vapor_address)
print(api.public_key)

or 

api = MovApi(secret_key="Your secretkey")
print(api.main_address)
print(api.vapor_address)
print(api.public_key)

or 

# This way will create a new secret_key
api = MovApi("")
print(api.secret_key)
print(api.main_address)
print(api.vapor_address)
print(api.public_key)


# To generate new secret_key
api = MovApi("")
print(api.get_new_secret_key())
print(api.main_address)
print(api.vapor_address)

# To use delegation submit
api = MovApi(secret_key="Your secretkey", network="mainnet", third_address="Your deletegation address", third_public_key="Your delegation public key") 


```

## 2.Running

```python
print(api.get_exchange_info())
print(api.query_open_orders("BTM/USDT"))
print(api.query_list_orders([710941]))
print(api.cancel_order(710924))
print(api.get_depth("BTC/USDT", 5))
print(api.send_order(symbol="BTC/USDT", side="buy", price=6100, volume=0.01))
print(api.query_balance())
```

# MOV FLASH API DOC

## 1.Prepare

write dealer's configure

```shell
如果是量化托管，则配置如下
{
    "port": 1058,
    "address": "您的侧链地址",
    "xprv": "您的私钥",
    "bycoin_url": "https://ex.movapi.com",
    "flash_swap_url": "172.19.113.215:50052",
    "mnemonic": "您的助记词",
    "derive_rule": {
        "account_idx": 1,
        "address_idx": 1
    },
    "network": "mainnet",
    "logs": {
        "rotate_time": "24h",
        "max_age": "72h"
    }
}


如果是三方多签地址做市，则配置如下
{
    "port": 1024,
    "address": "您的侧链多签地址",
    "xprv": "您的私钥",
    "bycoin_url": "https://ex.movapi.com",
    "flash_swap_url": "172.19.113.215:50052",
    "mnemonic": "您的助记词",
    "derive_rule": {
        "account_idx": 1,
        "address_idx": 1
    },
    "quant_mode": {
        "quant_delegation_url": "https://ex.movapi.com/delegation",
        "funder_pubkey": "三方托管生成的资方公钥",
        "attester_pubkey": "三方托管生成的公钥"
    },
    "network": "mainnet",
    "logs": {
        "rotate_time": "24h",
        "max_age": "72h"
    }
}

port 是本地使用的端口号,默认使用1024
derive_rule 是私钥的派生路径，原则上不用修改
flash_swap_url 闪兑服务器地址
quant_mode 是量化端口时要设置的配置

```

```python
#then you can import like below:
from mov_sdk.flash_api import FlashApi
```

then run the dealer

## 2.Running 

```python
# FLASH_LOCAL_URL = "http://127.0.0.1:1024" , 1024是端口号
client = FlashApi(_local_url=FLASH_LOCAL_URL)
print(client.get_depth("btm_usdt"))
print(client.send_order(symbol="btm_usdt", side="sell", price="5", amount="0.3"))
print(client.send_order(symbol="eth_usdt", side="buy", price="0.22", amount="1"))
print(client.cancel_order_by_id(symbol="eth_usdt", order_id=1))
print(client.query_balance())
print(client.query_list_orders(symbol="btm_usdt", side="sell"))
```

# MOV DELEGATION API DOC

## 1.Init
```python
# coding=utf-8
from mov_sdk.mov_api import MovApi

funder_mov = MovApi(secret_key="Your funder secretkey")
quant_mov = MovApi(secret_key="Your quant secretkey")
```

## To create delegation wallet
```python
data = funder_mov.create_delegation_wallet(mov1.public_key, mov2.public_key)
'''
Then the response is like below
{
    'code': 200, 
    'msg': '', 
    'data': 
    {
        'address': 'vp1qsndypfjuqe3z2t64edaz253ynwwfqrp7wqu5hdd5fz4ervrvpkgs4c32mk', 
        'funder_pubkey': '169536055d02be1caf014eac3c20908b8954ae96886c46c3902d2a4bbd034e8b', 
        'quant_pubkey': 'b66e20a477fefef087cb1fc70c7cea09c53cb072b8b22bf80b5f15890a8a0daf', 
        'attester_pubkey': '968b44ac9836a5325d091755d97297295b976e0fb0b18aa6f1f7d23cb05190aa'
    }
}
'''
# address is the address the quant will use!
# attester_pubkey is the pubkey the quant will use!
```

## To add/delete white list address
```
address = "vp1qsndypfjuqe3z2t64edaz253ynwwfqrp7wqu5hdd5fz4ervrvpkgs4c32mk"
attester_pubkey = "968b44ac9836a5325d091755d97297295b976e0fb0b18aa6f1f7d23cb05190aa"
white_address = "vp1qhg8qjtd5e3thlem569fmt8l8uc6xyd2nmsscks"
data = funder_mov.add_white_list_address(address, white_address)
print(data)

'''
# add white list success!

{'code': 200, 'msg': ''}
'''

data = funder_mov.delete_white_list_address(address, white_address)
print(data)

'''
# delete white list success!

{'code': 200, 'msg': ''}
'''
```

# MOV Maker Strategy

```shell
python3 mov_maker_strategy_demo.py
```

