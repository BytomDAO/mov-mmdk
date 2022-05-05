import json
from mov_sdk.nft_api import NftApi, xprv_my_sign, Net

params = {
    "pubkey": "cc019eb80526cec2697b8b55d44be0ccb63cff82a46258ae2cedbe5b66340e870d3d61a2a8a8d922a764087d9e9c27d2997e6fe8faf651caf87e7c8ad0bb708f",
    "timestamp": 1651740524247,
    "name": "ab",
    "content_path": "nft/nft-testnet/2022-05-05/tn1qhf09n6xfwr6vdw0tjd0n7v6ejny8lfrtc0cmp4/1651740516313.png",
    "content_md5": "09656f5bc232757d50c157abae7d941f",
    "royalty_rate": "10",
    "margin_asset": "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
    "margin_amount": "0.1",
    "description": "11"
}

params = {
    'pubkey': 'cc019eb80526cec2697b8b55d44be0ccb63cff82a46258ae2cedbe5b66340e870d3d61a2a8a8d922a764087d9e9c27d2997e6fe8faf651caf87e7c8ad0bb708f',
    'timestamp': 1651743804426,
    'name': 'crypto_sanguo',
    'content_path': 'https://bycoin.oss-cn-shanghai.aliyuncs.com/prod-t-nft/2022-05-05_174322884.png',
    'content_md5': 'cf8ad1c23e4ee99799b5f6f2a08d2b62',
    'royalty_rate': '15',
    'margin_asset': 'ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff',
    'margin_amount': '0.1',
    'description': 'kxc'
}


params = {
    'pubkey': 'cc019eb80526cec2697b8b55d44be0ccb63cff82a46258ae2cedbe5b66340e870d3d61a2a8a8d922a764087d9e9c27d2997e6fe8faf651caf87e7c8ad0bb708f',
    'timestamp': '1651743106554',
    'name': 'crypto_sanguo',
    'content_path': 'https://bycoin.oss-cn-shanghai.aliyuncs.com/prod-t-nft/2022-05-05_173145560.png',
    'content_md5': '09656f5bc232757d50c157abae7d941f',
    'royalty_rate': '0.015',
    'margin_asset': 'ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff',
    'margin_amount': '1.0',
    'description': 'kxc'
}

s = NftApi(mnemonic_str="major skull dinner crucial trip weird thumb grunt absent note motion primary", network=Net.TEST.value)
print(s.secret_key)
print(s.main_address)
msg = json.dumps(params).replace(' ', '').encode('utf-8')
xprv_sign_msg = xprv_my_sign(s.secret_key, msg)
print(xprv_sign_msg)