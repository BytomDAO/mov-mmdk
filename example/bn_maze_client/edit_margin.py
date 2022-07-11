import json
from mov_sdk.nft_api import NftApi, xprv_my_sign, Net


s = NftApi(secret_key="sdsds", network=Net.TEST.value)
nft_asset = ""
amount = 0.000001
data = s.edit_margin(nft_asset, amount)
print(data)

