from mov_sdk.utxo_manager import decode_address, address_to_script

print(address_to_script("btm2", "tn1q5zjfmndnexlx79n98wmjk6mhdd33qfwx78xt4w", "testnet"))

print(address_to_script("btm", "tm1q5zjfmndnexlx79n98wmjk6mhdd33qfwxv7pm3g", "testnet"))

from mov_sdk.mov_api import MovApi

# s1 = MovApi(mnemonic_str="")

# print(s1.main_address)

# print(s1.get_main_chain_balance())

# print(s1.get_exchange_info())

# print(s1.cross_chain_in("btm", "3"))

# print(s1.cross_chain_in("sup", "0.001"))

# print(s1.cross_chain_out("btm", 5, s1.main_address))

# print(s1.cross_chain_out("sup", 0.002, s1.main_address))


s2 = MovApi(mnemonic_str="chalk memory wear dizzy universe govern obtain eye fiber denial judge six")

asset = "btm"
amount = 0.01
address = "0xa6cb31b0a18af665eafaf48ef6a05bd8a4387309"
print(s2.cross_chain_in_to_bmc(asset, amount, address))
