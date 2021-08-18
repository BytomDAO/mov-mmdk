from enum import Enum


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


# Copyright (c) 2017 Pieter Wuille
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
# Please Ref: https://github.com/bitcoin/bips/blob/master/bip-0173.mediawiki

"""Reference implementation for Bech32 and segwit addresses."""

CHARSET = "qpzry9x8gf2tvdw0s3jn54khce6mua7l"


def bech32_polymod(values):
    """Internal function that computes the Bech32 checksum."""
    generator = [0x3b6a57b2, 0x26508e6d, 0x1ea119fa, 0x3d4233dd, 0x2a1462b3]
    chk = 1
    for value in values:
        top = chk >> 25
        chk = (chk & 0x1ffffff) << 5 ^ value
        for i in range(5):
            chk ^= generator[i] if ((top >> i) & 1) else 0
    return chk


def bech32_hrp_expand(hrp):
    """Expand the HRP into values for checksum computation."""
    return [ord(x) >> 5 for x in hrp] + [0] + [ord(x) & 31 for x in hrp]


def bech32_verify_checksum(hrp, data):
    """Verify a checksum given HRP and converted data characters."""
    return bech32_polymod(bech32_hrp_expand(hrp) + data) == 1


def bech32_create_checksum(hrp, data):
    """Compute the checksum values given HRP and data."""
    values = bech32_hrp_expand(hrp) + data
    polymod = bech32_polymod(values + [0, 0, 0, 0, 0, 0]) ^ 1
    return [(polymod >> 5 * (5 - i)) & 31 for i in range(6)]


def bech32_encode(hrp, data):
    """Compute a Bech32 string given HRP and data values."""
    combined = data + bech32_create_checksum(hrp, data)
    return hrp + '1' + ''.join([CHARSET[d] for d in combined])


def bech32_decode(bech):
    """Validate a Bech32 string, and determine HRP and data."""
    if ((any(ord(x) < 33 or ord(x) > 126 for x in bech)) or
            (bech.lower() != bech and bech.upper() != bech)):
        return (None, None)
    bech = bech.lower()
    pos = bech.rfind('1')
    if pos < 1 or pos + 7 > len(bech) or len(bech) > 90:
        return (None, None)
    if not all(x in CHARSET for x in bech[pos + 1:]):
        return (None, None)
    hrp = bech[:pos]
    data = [CHARSET.find(x) for x in bech[pos + 1:]]
    if not bech32_verify_checksum(hrp, data):
        return (None, None)
    return (hrp, data[:-6])


def convertbits(data, frombits, tobits, pad=True):
    """General power-of-2 base conversion."""
    acc = 0
    bits = 0
    ret = []
    maxv = (1 << tobits) - 1
    max_acc = (1 << (frombits + tobits - 1)) - 1
    for value in data:
        if value < 0 or (value >> frombits):
            return None
        acc = ((acc << frombits) | value) & max_acc
        bits += frombits
        while bits >= tobits:
            bits -= tobits
            ret.append((acc >> bits) & maxv)
    if pad:
        if bits:
            ret.append((acc << (tobits - bits)) & maxv)
    elif bits >= frombits or ((acc << (tobits - bits)) & maxv):
        return None
    return ret


def decode(hrp, addr):
    """Decode a segwit address."""
    hrpgot, data = bech32_decode(addr)
    if hrpgot != hrp:
        return (None, None)
    decoded = convertbits(data[1:], 5, 8, False)
    if decoded is None or len(decoded) < 2 or len(decoded) > 40:
        return (None, None)
    if data[0] > 16:
        return (None, None)
    if data[0] == 0 and len(decoded) != 20 and len(decoded) != 32:
        return (None, None)
    return (data[0], decoded)


def encode(hrp, witver, witprog):
    """Encode a segwit address."""
    ret = bech32_encode(hrp, [witver] + convertbits(witprog, 8, 5))
    if decode(hrp, ret) == (None, None):
        return None
    return ret


def get_byte(v: int):
    return v & 0xff


def get_uint16(v: int):
    return [get_byte(v), get_byte(v >> 8)]


def get_uint32(v: int):
    return [get_byte(v), get_byte(v >> 8), get_byte(v >> 16), get_byte(v >> 24)]


class Opcodes(Enum):
    OP_0 = 0
    OP_1 = 81
    OP_DATA_1 = 1
    OP_PUSHDATA1 = 76
    OP_PUSHDATA2 = 77
    OP_PUSHDATA4 = 78


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
                    self.program[placeholder + i] = b[i]
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


print(address_from_chain_to_chain(
    address="tm1q5zjfmndnexlx79n98wmjk6mhdd33qfwxv7pm3g",
    from_chain_name=Chain.BYTOM.value,
    to_chain_name=Chain.BYTOM2.value,
    net_name=Net.TEST.value
))

# print(address_to_script("btm2", "tn1q5zjfmndnexlx79n98wmjk6mhdd33qfwx78xt4w", "testnet"))
#
# print(address_to_script("btm", "tm1q5zjfmndnexlx79n98wmjk6mhdd33qfwxv7pm3g", "testnet"))
