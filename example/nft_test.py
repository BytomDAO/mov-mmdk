# coding=utf-8
import time

from pprint import pprint


from tumbler.encryption import my_decrypt
from mov_sdk.nft_api import NftApi, Net


host = "https://test-bcapi.movapi.com"
mnemonic_str = ""
nft_api = NftApi(mnemonic_str=mnemonic_str,
				_MOV_REST_TRADE_HOST=host,
				_NFT_REST_TRADE_HOST="http://47.100.237.157:3000/nft/v1", network=Net.TEST.value)

# print(nft_api.main_address)
# print(nft_api.get_main_chain_balance())

# print(nft_api.query_nft_assets())

# 还没测
# print(nft_api.artist_rank(order="profit", sort="asc", start=0, limit=100))

# print(nft_api.trade_rank(start=0, limit=10, day=7))

# print(nft_api.offer_rank(start=0, limit=10))

# False
# print(nft_api.user_info())

# False
# print(nft_api.user_own_nfts())

# False
# print(nft_api.user_sold_ntfs(address=nft_api.main_address))

# False
# print(nft_api.user_mint_ntfs(address=nft_api.main_address))

# False
# print(nft_api.user_offer_nfts(address=nft_api.main_address))

# False
# print(nft_api.search_nfts(word="abc", start=0, limit=10))

# print(nft_api.fuzzy_search_nfts(word="abc", start=0, limit=10))

# print(nft_api.nft_detail(asset="6a973e43226c22e534906edbf7621a222be740b991465d0b261c2e47286dae98"))
# print(nft_api.nft_detail(asset="bb3eae95ed9808f6c7831f4c1905811a9bbe171357a506419d9dd2f934221f45"))

# print(nft_api.nft_margin(asset="6a973e43226c22e534906edbf7621a222be740b991465d0b261c2e47286dae98"))

# print(nft_api.nft_offers(nft_asset="6a973e43226c22e534906edbf7621a222be740b991465d0b261c2e47286dae98"))

# print(nft_api.nft_offer(tx_hash="90fc17c47cee222b520acb4c2d5e4892401dc27ee78bea4c102c47c25bd9e0e7"))

# print(nft_api.issue_nft(name="abc", content_path="d", content_md5="", royalty_rate=0.1, margin_asset="", margin_amount=0.1, description="", thumbnail_file_path=""))

nft_asset = "bb3eae95ed9808f6c7831f4c1905811a9bbe171357a506419d9dd2f934221f45"
pay_asset = "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"
pay_amount = 40
margin_asset = "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"
margin_amount = 4.96

# print(nft_api.build_issue_trade(nft_asset, pay_asset, pay_amount, margin_asset, margin_amount))

# print(nft_api.issue_trade(nft_asset, pay_asset, pay_amount, margin_asset, margin_amount))

# print(nft_api.build_trade(nft_asset, pay_asset, pay_amount, margin_asset, margin_amount))

print(nft_api.trade(nft_asset, pay_asset, pay_amount, margin_asset, margin_amount))

# print(nft_api.build_offer(nft_asset, pay_asset, pay_amount, margin_asset, margin_amount))

# tx_hash: e7dee99c2ba0bcb79b753d296b5bff941d622709df334f1e969da6fe75d16bfb
# tx_hash: 0ba3be15b5893b7314b21a1cc5edb0f8e039e685970d19684f8788f5f1b6aceb
# print(nft_api.offer_trade(nft_asset, pay_asset, pay_amount, margin_asset, margin_amount))


amount = 4

# print(nft_api.build_edit_margin(nft_asset, amount))
# print(nft_api.edit_margin(nft_asset, amount))

# print(nft_api.build_revoke_offer(nft_asset))
# print(nft_asset)
# print(nft_api.revoke_offer(nft_asset))


# print(nft_api.submit_tx(params))

