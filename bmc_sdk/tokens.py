from typing import Dict

from web3 import Web3
from web3.types import ChecksumAddress

from .constants import EthNet


net_2_main_symbol_dic = {
    EthNet.MainNet.value: "ETH",
    EthNet.BscNet.value: "BNB",
    EthNet.BmcTestNet.value: "BTM",
    EthNet.BmcMainNet.value: "BTM"
}

symbol_2_decimals_mainnet_dict = {
    "USDT": 6,
    "ETH": 18,
    "DAI": 18,
    "UNI": 18
}

symbol_2_decimals_bsc_dict = {
    "USDT": 18,
    "ETH": 18,
    "DAI": 18,
    "UNI": 18
}

symbol_2_decimals_btmtest_dic = {
    "BTM": 18,
    "WBTM": 18,
    "MAG": 18,
}

symbol_2_decimals_btmmain_dic = {
    "BTM": 18,
    "WBTM": 18,
    "MAG": 18
}

tokens: Dict[str, ChecksumAddress] = {
    k: Web3.toChecksumAddress(v)
    for k, v in {
        "ETH": "0x0000000000000000000000000000000000000000",
        "WETH": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
        "DAI": "0x6B175474E89094C44Da98b954EedeAC495271d0F",
        "BAT": "0x0D8775F648430679A709E98d2b0Cb6250d2887EF",
        "WBTC": "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599",
        "UNI": "0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984",
        "USDC": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
        "USDT": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
        "SUSHI": "0x6b3595068778dd592e39a122f4f5a5cf09c90fe2"
    }.items()
}

tokens_rinkeby: Dict[str, ChecksumAddress] = {
    k: Web3.toChecksumAddress(v)
    for k, v in {
        "ETH": "0x0000000000000000000000000000000000000000",
        "DAI": "0x2448eE2641d78CC42D7AD76498917359D961A783",
        "BAT": "0xDA5B056Cfb861282B4b59d29c9B395bcC238D29B",
    }.items()
}

# source: https://bscscan.com/tokens/label/binance-pegged
tokens_bscnet: Dict[str, ChecksumAddress] = {
    k: Web3.toChecksumAddress(v)
    for k, v in {
        "BNB": Web3.toChecksumAddress("0x0000000000000000000000000000000000000000"),
        "BTC": Web3.toChecksumAddress("0x7130d2a12b9bcbfae4f2634d864a1ee1ce3ead9c"),
        "USDT": Web3.toChecksumAddress("0x55d398326f99059ff775485246999027b3197955"),
        "WBNB": Web3.toChecksumAddress("0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c"),
        "ETH": Web3.toChecksumAddress("0x2170ed0880ac9a755fd29b2688956bd959f933f8"),
        "CAKE": Web3.toChecksumAddress("0x0e09fabb73bd3ade0a17ecc321fd13a19e81ce82"),
        "USDC": Web3.toChecksumAddress("0x8ac76a51cc950d9822d68b83fe1ad97b32cd580d"),
    }.items()
}

tokens_bmctestnet: Dict[str, ChecksumAddress] = {
    k: Web3.toChecksumAddress(v)
    for k, v in {
        "BTM": Web3.toChecksumAddress("0x0000000000000000000000000000000000000000"),
        "WBTM": Web3.toChecksumAddress("0x0b45Ad27866C8E05ED610cd8A0ec78de94B18202"),
        "MAG": Web3.toChecksumAddress("0xF6084Ad447076da0246cD28e104533f9f51dbD2F"),
    }.items()
}

tokens_bmcmainnet: Dict[str, ChecksumAddress] = {
    k: Web3.toChecksumAddress(v)
    for k, v in {
        "BTM": Web3.toChecksumAddress("0x0000000000000000000000000000000000000000"),
        "WBTM": Web3.toChecksumAddress("0xcd109943f45587D589cAE7b66F3FcF4a3097A288"),
        "SUP": Web3.toChecksumAddress("0x77197f46435D4cf8fB07953ad5ebC98EE6C8E7F1"),
    }.items()
}

contract_2_symbol_mainnet_dict = {}
for k, v in tokens.items():
    contract_2_symbol_mainnet_dict[v] = k

contract_2_symbol_bscnet_dict = {}
for k, v in tokens_bscnet.items():
    contract_2_symbol_bscnet_dict[v] = k

contract_2_symbol_btmtest_dict = {}
for k, v in contract_2_symbol_btmtest_dict.items():
    contract_2_symbol_btmtest_dict[v] = k

contract_2_symbol_btmmain_dict = {}
for k, v in contract_2_symbol_btmmain_dict.items():
    contract_2_symbol_btmmain_dict[v] = k

net_2_symbol_2_decimals_dict = {
    EthNet.MainNet.value: symbol_2_decimals_mainnet_dict,
    EthNet.BscNet.value: symbol_2_decimals_bsc_dict,
    EthNet.BmcTestNet.value: symbol_2_decimals_btmtest_dic,
    EthNet.BmcMainNet.value: symbol_2_decimals_btmmain_dic
}

net_2_symbol_2_contract_dict = {
    EthNet.MainNet.value: tokens,
    EthNet.BscNet.value: tokens_bscnet,
    EthNet.BmcTestNet.value: tokens_bmctestnet,
    EthNet.BmcMainNet.value: tokens_bmcmainnet
}

net_2_contract_2_symbol_dict = {
    EthNet.MainNet.value: contract_2_symbol_mainnet_dict,
    EthNet.BscNet.value: contract_2_symbol_bscnet_dict,
    EthNet.BmcTestNet.value: contract_2_symbol_btmtest_dict,
    EthNet.BmcMainNet.value: contract_2_symbol_btmmain_dict
}


def get_symbol_2_decimal_dict(net):
    return net_2_symbol_2_decimals_dict[net]


def get_symbol_2_contract_dict(net):
    return net_2_symbol_2_contract_dict[net]


def get_contract_2_symbol_dict(net):
    return net_2_contract_2_symbol_dict[net]


def get_main_symbol_from_net(net):
    return net_2_main_symbol_dic[net]
