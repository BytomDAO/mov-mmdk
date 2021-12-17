import os
import json
import functools
from typing import Union, List, Tuple

from web3 import Web3

from .local_types import AddressLike, Address, Contract
from .exceptions import InvalidToken


def str_to_addr(s: Union[AddressLike, str]) -> Address:
    """Idempotent"""
    if isinstance(s, str):
        if s.startswith("0x"):
            return Address(bytes.fromhex(s[2:]))
        else:
            raise Exception(f"Couldn't convert string '{s}' to AddressLike")
    else:
        return s


def addr_to_str(a: AddressLike) -> str:
    if isinstance(a, bytes):
        # Address or ChecksumAddress
        addr: str = Web3.toChecksumAddress("0x" + bytes(a).hex())
        return addr
    elif isinstance(a, str) and a.startswith("0x"):
        addr = Web3.toChecksumAddress(a)
        return addr

    raise InvalidToken(a)


def is_same_address(a1: Union[AddressLike, str], a2: Union[AddressLike, str]) -> bool:
    return str_to_addr(a1) == str_to_addr(a2)


def validate_address(a: AddressLike) -> None:
    assert addr_to_str(a)


def load_abi(name: str) -> str:
    path = f"{os.path.dirname(os.path.abspath(__file__))}/assets/"
    with open(os.path.abspath(path + f"{name}.abi")) as f:
        abi: str = json.load(f)
    return abi


@functools.lru_cache()
def load_contract(w3: Web3, abi_name: str, address: AddressLike) -> Contract:
    address = Web3.toChecksumAddress(address)
    return w3.eth.contract(address=address, abi=load_abi(abi_name))


def load_contract_erc20(w3: Web3, address: AddressLike) -> Contract:
    return load_contract(w3, "erc20", address)


def _encode_path(token_in: AddressLike, route: List[Tuple[int, AddressLike]]) -> bytes:
    """
    Needed for multi-hop swaps in V3.

    https://github.com/Uniswap/uniswap-v3-sdk/blob/1a74d5f0a31040fec4aeb1f83bba01d7c03f4870/src/utils/encodeRouteToPath.ts
    """
    raise NotImplementedError


target_symbols = ["cdc", "yee", "ost", "vet", "gtc", "ela", "arpa",
                  "bnb", "lrc", "get", "itc", "zla", "tnt", "trx",
                  "she", "cmt", "btt", "bts", "btc", "btm", "mds",
                  "neo", "smt", "wicc", "abt", "swftc", "cnn", "new",
                  "omg", "ast", "uuu", "let", "egcc", "mex", "qun",
                  "iris", "etc", "etf", "eth", "bch", "elf", "ong",
                  "usdt", "ont", "top", "pc", "zil", "mco", "bsv",
                  "gas", "but", "qsp", "iic", "atom", "hc", "iost",
                  "18c", "aac", "dta", "bcd", "tnb", "meet", "cvc",
                  "uc", "ae", "dash", "uip", "inc", "lamb", "aidoc",
                  "enj", "hpt", "nas", "hot", "lxt", "datx", "bsv",
                  "bifi", "bcpt", "portal", "ht", "ruff", "topc",
                  "man", "sbtc", "qtum", "eos", "gsc", "bcx", "bkbt"]

base_symbols = ["btc", "eth", "bnb", "bch", "ht", "okb", "qc", "usdk", "usdt",
                "usds", "tusd", "usdc", "busd"]

real_symbols = list(set(target_symbols + base_symbols))
global_dic = {}
for target_symbol in real_symbols:
    for base_symbol in real_symbols:
        key = '{}{}'.format(target_symbol, base_symbol)
        val = '{}_{}'.format(target_symbol, base_symbol)
        global_dic[key] = val


def get_format_lower_symbol(symbol):
    """
    ethusdt --> eth_usdt
    etcbtc  --> etc_btc
    ethusdt.HUOBI --> eth_usdt
    etcbtc.HUOBI  --> etc_btc
    """
    global global_dic, base_symbols
    symbol = symbol.replace('_', '')
    symbol = ((symbol.split('.'))[0]).lower()
    n_symbol = global_dic.get(symbol, None)

    if n_symbol:
        return n_symbol
    else:
        for base_symbol in base_symbols:
            if symbol.endswith(base_symbol):
                ll = len(base_symbol)
                return '{}_{}'.format(symbol[:-ll], base_symbol)
        return '{}_{}'.format(symbol[:-3], symbol[-3:])


def get_two_currency(symbol):
    """
    ethusdt --> (eth,usdt)
    etcbtc  --> (etc,btc)
    ethusdt.HUOBI --> (eth,usdt)
    etcbtc.HUOBI  --> (etc,btc)
    """
    arr = get_format_lower_symbol(symbol).split("_")
    return (arr[0], arr[1])


