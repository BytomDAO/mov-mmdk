import qrcode
import pybase64
import six
import hmac
from io import BytesIO
from binascii import hexlify
from binascii import unhexlify
from .edwards25519 import *


# create_qrcode_base64 create qrcode, then encode it to base64
# type(s) is str
def create_qrcode_base64(s):
    img = qrcode.make(s)
    buffered = BytesIO()
    img.save(buffered, format="JPEG")
    base64_str = pybase64.b64encode(buffered.getvalue()).decode("utf-8")
    return base64_str


if six.PY3:
    def byte2int(b):
        return b


    def int2byte(i):
        return bytes(chr(i % 256), encoding="UTF-8")

elif six.PY2:
    def byte2int(b):
        return ord(b)


    def int2byte(i):
        return chr(i % 256)

L = 2 ** 252 + 27742317777372353535851937790883648493


def hmac_sha_512(data, key):
    digest = hmac.new(key, msg=data, digestmod=hashlib.sha512).digest()
    return digest


def sha_512(data):
    md = hashlib.sha512()
    md.update(data)
    return md.digest()


def hex2int(hex):
    ## converts a hex string to integer
    unhex = unhexlify(hex)
    s = 0
    for i in range(len(unhex)):
        s += 256 ** i * byte2int(unhex[i])
    return s


def int2hex(int):
    ## converts an integer to a little endian encoded hex string
    return hexlify(encodeint(int))


def sc_reduce32(input):
    ## convert hex string input to integer
    int = hex2int(input)
    ## reduce mod l
    modulo = int % L
    ## convert back to hex string for return value
    return int2hex(modulo)


def sc_muladd(a, b, c):
    a_int = hex2int(a)
    b_int = hex2int(b)
    c_int = hex2int(c)

    s = a_int * b_int + c_int
    modulo = s % L
    return int2hex(modulo)
