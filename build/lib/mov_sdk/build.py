# coding=utf-8

import hashlib
import json
import time
import requests
from enum import Enum
from collections import defaultdict
from .key import get_xpub, get_child_xpub, get_seed, get_child_xprv, get_root_xprv, xprv_sign
from .key import get_entropy, get_mnemonic
from .receiver import get_main_vapor_address, get_public_key
from .segwit_addr import decode
from .opcodes import Opcodes


def get_byte(v: int):
    return v & 0xff


def get_uint16(v: int):
    return [get_byte(v), get_byte(v >> 8)]


def get_uint32(v: int):
    return [get_byte(v), get_byte(v >> 8), get_byte(v >> 16), get_byte(v >> 24)]


class VM(object):
    @staticmethod
    def pushdata_int64(n):
        if n == 0:
            return [Opcodes.OP_0.value]
        if 1 <= n <= 16:
            return [Opcodes.OP_1.value + n - 1]
        return VM.pushdata_bytes(n)

    @staticmethod
    def pushdata_bytes(hash: list):
        l = len(hash)
        if 0 == l:
            return [Opcodes.OP_0.value]
        if l <= 75:
            return [Opcodes.OP_DATA_1.value + l - 1] + hash
        if l < 256:
            return [Opcodes.OP_PUSHDATA1.value, l] + hash
        if l < 65536:
            b: list = get_uint16(l)
            return [Opcodes.OP_PUSHDATA2.value] + b + hash
        b: list = get_uint32(l)
        return [Opcodes.OP_PUSHDATA4.value] + b + hash


class Builder(object):
    def __init__(self):
        self.program: list = []
        self.jump_counter = 0
        self.jump_addr = {}
        self.jump_place_holds = {}  # {3:[1,2,3]}

    def add_int64(self, n):
        self.program.extend(VM.pushdata_int64(n))

    def add_data(self, hash: list):
        self.program.extend(VM.pushdata_bytes(hash))

    def build(self):
        for target, placeholders in self.jump_place_holds.items():
            addr = self.jump_addr[target]
            for placeholder in placeholders:
                b: list = get_uint32(addr)
                for i in range(len(b)):
                    self.program[placeholder+i] = b[i]
        return self.program


def P2WPKH_program(hash: list):
    builder = Builder()
    builder.add_int64(0)
    builder.add_data(hash)
    return builder.build()


def P2WSH_program(hash: list):
    builder = Builder()
    builder.add_int64(0)
    builder.add_data(hash)
    return builder.build()
