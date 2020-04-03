# MOV SPOT API DOC
mov's spot trading api doc

## 1.Prepare

```
pip3 install pybtm
```

## 2.Get Guid and SecretKey

```
api = MovApi(guid="", secret_key="")
config = api.get_config_from_mnemonic("stereo nominee miss click sock argue valid hole jelly vessel payment fork")
print(config)
```

## 3.Running

```
print(api.get_exchange_info())
print(api.query_buy_orders("BTM/ETH"))
print(api.query_sell_orders("BTM/ETH"))
print(api.query_all_orders("BTC/USDT"))
print(api.query_list_orders([710941]))
print(api.cancel_order(710924))
print(api.get_depth("BTC/USDT", 5))
print(api.send_order(symbol="BTC/USDT", side="buy", price=6100, volume=0.01))
print(api.query_balance())
```

# MOV FLASH API DOC

## 1.Prepare

write dealer's configure

```
{
	"port": 1024,
	"bycoin_url": "http://52.82.22.99:3000",
	"xprv": "f8de98a4acf22d94fe7ad83992590179fffef7fb2225f2dcb31e2fb40d86eb42e137a6e4758d85e0a4d069766793f0a88974f8d7b0c0b930b0ed200d28fff782",
	"guid": "dd0914eb-5d47-4364-9e30-6c4b728ac2b8",
	"flash_swap_url": "ws://52.82.22.99:1096/api/v1/dealer",
	"log_level": "debug"
}
```

then run the dealer

## 2.Running 

```
client = FlashApi("dd0914eb-5d47-4364-9e30-6c4b728ac2b8", _local_url=FLASH_LOCAL_URL)
print(client.get_depth("btm_usdt"))
print(client.send_order(symbol="btm_usdt", side="sell", price="5", amount="0.3"))
print(client.cancel_order(symbol="eth_usdt", side="buy"))
print(client.cancel_order(symbol="eth_usdt", side="sell"))
print(client.query_balance())
print(client.send_order(symbol="eth_usdt", side="sell", price="0.33", amount="0.3"))
print(client.send_order(symbol="eth_usdt", side="buy", price="0.22", amount="1"))
```