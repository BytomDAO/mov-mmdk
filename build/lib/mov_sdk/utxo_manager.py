# coding=utf-8

import hashlib
import json
import time
import requests
from enum import Enum
from .key import get_xpub, get_child_xpub, get_seed, get_child_xprv, get_root_xprv, xprv_sign
from .key import get_entropy, get_mnemonic
from .receiver import get_main_vapor_address, get_public_key
from .segwit_addr import decode, encode
from .build import P2WPKH_program, P2WSH_program


class Net(Enum):
    MAIN = "mainnet"
    TEST = "testnet"
    SOLO = "solonet"


class Chain(Enum):
    BYTOM2 = "btm2"
    BYTOM = "btm"
    VAPOR = "vapor"


bytom2_net_hrp = {
    Net.MAIN.value: "bn",
    Net.TEST.value: "tn",
    Net.SOLO.value: "sn"
}

bytom_net_hrp = {
    Net.MAIN.value: "bm",
    Net.TEST.value: "tm",
    Net.SOLO.value: "sm"
}

vapor_net_hrp = {
    Net.MAIN.value: "vp",
    Net.TEST.value: "tp",
    Net.SOLO.value: "sp"
}


def use_hex(u: int):
    s = (hex(u))[2:].zfill(2)
    return s


def array_hex(l: list):
    s = ""
    for i in l:
        s = s + use_hex(i)
    return s


def get_hrp(chain_name, net_name):
    if chain_name == Chain.BYTOM.value:
        return bytom_net_hrp[net_name]
    elif chain_name == Chain.VAPOR.value:
        return vapor_net_hrp[net_name]
    elif chain_name == Chain.BYTOM2.value:
        return bytom2_net_hrp[net_name]


def decode_address(chain_name, address, net_name):
    one_index = address.rindex('1')
    hrp = address[:one_index]
    if hrp == get_hrp(chain_name, net_name):
        data, decoded = decode(hrp, address)
        return decoded


def address_to_script(chain_name, address, net_name):
    decode_hash = decode_address(chain_name, address, net_name)
    if decode_hash:
        if len(address) == 42:
            return array_hex(P2WPKH_program(decode_hash))
        else:
            return array_hex(P2WSH_program(decode_hash))


def address_from_chain_to_chain(address, from_chain_name, to_chain_name, net_name):
    from_hrp = get_hrp(from_chain_name, net_name)
    to_hrp = get_hrp(to_chain_name, net_name)
    data, decoded = decode(from_hrp, address)
    new_address = encode(to_hrp, data, decoded)

    print(f"{address} --> {new_address}")
    return new_address


class Utxo(object):
    def __init__(self):
        self.hash = ""
        self.asset = ""
        self.amount = 0
        self.is_locked = False


class UtxoSelectAlgorithm(object):
    pass


class UtxoManager(object):
    def __init__(self, address):
        pass
