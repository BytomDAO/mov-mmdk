
import hashlib
import json
import time
import requests


msg = "我是傻逼"
print(msg, type(msg))
utf8_msg = msg.encode('utf-8')
print(utf8_msg, type(utf8_msg))

gbk_msg = msg.encode('gbk')
print(gbk_msg, type(gbk_msg))

new_msg = msg.replace('", "', '","').replace('": ', '":').replace(', "', ',"')
print("?", msg.encode('utf-8'))


params = {
	'pubkey': 'cc019eb80526cec2697b8b55d44be0ccb63cff82a46258ae2cedbe5b66340e870d3d61a2a8a8d922a764087d9e9c27d2997e6fe8faf651caf87e7c8ad0bb708f', 'timestamp': 1652965519002, 'name': 'BearRabbitc015', 'content_path': 'prod-t-nft/2022-05-19_210517582.jpg', 'content_md5': 'cf8ad1c23e4ee99799b5f6f2a08d2b62', 'royalty_rate': '15', 'margin_asset': 'ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff', 'margin_amount': '0.1', 
	'description': '我是傻逼'
}

print(params)

msg = json.dumps(params, ensure_ascii=False).replace('", "', '","').replace('": ', '":').replace(', "', ',"').encode('utf-8')
print(msg)

js = json.loads(msg)
print(js)

print(js["description"])

# d = b'"description":"\\u6211\\u662f\\u50bb\\u903c"'
# print(type(d), d.decode('utf-8'))

