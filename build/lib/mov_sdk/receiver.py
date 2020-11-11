from .key import *
from .segwit_addr import *
from .utils import *


# get_path_from_index create xpub path from account key index and current address index
# path: purpose(0x2c=44)/coin_type(btm:0x99)/account_index/change(1 or 0)/address_index
# You can find more details from: https://github.com/bitcoin/bips/blob/master/bip-0044.mediawiki
# You can get more test data from: https://gist.github.com/zcc0721/616eaf337673635fa5c9dd5dbb8dd114
# Please attention:
#   account_index_int >= 1
#   address_index_int >= 1
#   change_bool: true or false
# test data 1:
#   account_index_int: 1
#   address_index_int: 1
#   change_bool: true
#   path_list: 2c000000 99000000 01000000 01000000 01000000
# test data 2:
#   account_index_int: 1
#   address_index_int: 1
#   change_bool: false
#   path_list: 2c000000 99000000 01000000 00000000 01000000
# test data 3:
#   account_index_int: 3
#   address_index_int: 1
#   change_bool: false
#   path_list: 2c000000 99000000 03000000 00000000 01000000
def get_path_from_index(account_index_int, address_index_int, change_bool):
    path_list = ['2c000000', '99000000']
    account_index_str = (account_index_int).to_bytes(4, byteorder='little').hex()
    path_list.append(account_index_str)
    change_str = '0'
    if change_bool:
        branch_str = (1).to_bytes(4, byteorder='little').hex()
        change_str = '1'
    else:
        branch_str = (0).to_bytes(4, byteorder='little').hex()
    path_list.append(branch_str)
    address_index_str = (address_index_int).to_bytes(4, byteorder='little').hex()
    path_list.append(address_index_str)
    path_str = 'm/44/153/' + str(account_index_int) + '/' + change_str + '/' + str(address_index_int)
    return {
        "path": path_list,
        "path_str": path_str
    }


# get_control_program create control program
# You can get more test data from: https://gist.github.com/zcc0721/afa12de04b03b9bfc49985a181ebda80
# Please attention:
#   account_index_int >= 1
#   address_index_int >= 1
#   change_bool: true or false
# test data 1:
#   account_index_int: 1
#   address_index_int: 1
#   change_bool: false
#   xpub_str: 3c6664244d2d57168d173c4691dbf8741a67d972b2d3e1b0067eb825e2005d20c5eebd1c26ccad4de5142d7c339bf62cc1fb79a8b3e42a708cd521368dbc9286
#   control_program_str: 0014052620b86a6d5e07311d5019dffa3864ccc8a6bd
# test data 2:
#   account_index_int: 1
#   address_index_int: 1
#   change_bool: true
#   xpub_str: 3c6664244d2d57168d173c4691dbf8741a67d972b2d3e1b0067eb825e2005d20c5eebd1c26ccad4de5142d7c339bf62cc1fb79a8b3e42a708cd521368dbc9286
#   control_program: 001478c3aa31753389fcde04d33d0779bdc2840f0ad4
# test data 3:
#   account_index_int: 1
#   address_index_int: 17
#   change_bool: true
#   xpub_str: 3c6664244d2d57168d173c4691dbf8741a67d972b2d3e1b0067eb825e2005d20c5eebd1c26ccad4de5142d7c339bf62cc1fb79a8b3e42a708cd521368dbc9286
#   control_program: 0014eefb8d0688d7960dfbd79bb3aa1bcaa3ec34415d
# test data 4:
#   account_index_int: 1
#   address_index_int: 1
#   change_bool: false
#   xpub_str: f744493a021b65814ea149118c98aae8d1e217de29fefb7b2024ca341cd834586ee48bbcf1f4ae801ecb8c6784b044fc62a74c58c816d14537e1573c3e20ce79
#   control_program: 001431f2b90b469e89361225aae370f73e5473b9852b
def get_control_program(account_index_int, address_index_int, change_bool, xpub_hexstr):
    path_list = get_path_from_index(account_index_int, address_index_int, change_bool)['path']
    child_xpub_hexstr = get_child_xpub(xpub_hexstr, path_list)
    child_public_key_hexstr = get_public_key(child_xpub_hexstr)
    child_public_key_byte = bytes.fromhex(child_public_key_hexstr)

    ripemd160 = hashlib.new('ripemd160')
    ripemd160.update(child_public_key_byte)
    public_key_hash_hexstr = ripemd160.hexdigest()
    control_program_hexstr = '0014' + public_key_hash_hexstr
    return control_program_hexstr


# get_address create address
# You can get more test data from: https://gist.github.com/zcc0721/8f52d0a80a0a9f964e9d9d9a50e940c5
# Please attention:
#   network_str: mainnet/testnet/solonet
# test data 1:
#   control_program_str: 001431f2b90b469e89361225aae370f73e5473b9852b
#   network_str: mainnet
#   address_str: bm1qx8etjz6xn6ynvy394t3hpae723emnpft3nrwej
# test data 2:
#   control_program_str: 0014eefb8d0688d7960dfbd79bb3aa1bcaa3ec34415d
#   network_str: mainnet
#   address_str: bm1qamac6p5g67tqm77hnwe65x7250krgs2avl0nr6
# test data 3:
#   control_program_str: 0014eefb8d0688d7960dfbd79bb3aa1bcaa3ec34415d
#   network_str: testnet
#   address_str: tm1qamac6p5g67tqm77hnwe65x7250krgs2agfwhrt
# test data 4:
#   control_program_str: 0014d234314ea1533dee584417ecb922f904b8dd6c6b
#   network_str: testnet
#   address_str: tm1q6g6rzn4p2v77ukzyzlktjgheqjud6mrt7emxen
# test data 5:
#   control_program_str: 0014eefb8d0688d7960dfbd79bb3aa1bcaa3ec34415d
#   network_str: solonet
#   address_str: sm1qamac6p5g67tqm77hnwe65x7250krgs2adw9jr5
# test data 6:
#   control_program_str: 0014052620b86a6d5e07311d5019dffa3864ccc8a6bd
#   network_str: solonet
#   address_str: sm1qq5nzpwr2d40qwvga2qval73cvnxv3f4aa9xzh9
def get_address(control_program_hexstr, network_str):
    public_key_hash_hexstr = control_program_hexstr[4:]
    if network_str == 'mainnet':
        hrp = 'bm'
    elif network_str == 'testnet':
        hrp = 'tm'
    else:
        hrp = 'sm'
    address_str = encode(hrp, 0, bytes.fromhex(public_key_hash_hexstr))
    return address_str


def get_vapor_address(control_program_hexstr, network_str):
    public_key_hash_hexstr = control_program_hexstr[4:]
    if network_str == 'mainnet':
        hrp = 'vp'
    elif network_str == 'testnet':
        hrp = 'tp'
    else:
        hrp = 'sp'
    address_str = encode(hrp, 0, bytes.fromhex(public_key_hash_hexstr))
    return address_str


# get_new_address create address and address qrcode
# test data 1:
#   xpub_str: 8fde12d7c9d6b6cbfbf344edd42f2ed86ae6270b36bab714af5fd5bb3b54adcec4265f1de85ece50f17534e42016ee9404a11fec94ddfadd4a064d27ef3f3f4c
#   account_index_int: 1
#   address_index_int: 1
#   change_bool: False
#   network_str: solonet
#   path: m/44/153/1/0/1
#   control_program: 00147640f3c34fe4b2b298e54e54a4692a47ce47aa5e
#   address: sm1qweq08s60ujet9x89fe22g6f2gl8y02j7lgr5v5
#   address_base64: /9j/4AAQSkZJRgABAQ...
# test data 2:
#   xpub_str: 8fde12d7c9d6b6cbfbf344edd42f2ed86ae6270b36bab714af5fd5bb3b54adcec4265f1de85ece50f17534e42016ee9404a11fec94ddfadd4a064d27ef3f3f4c
#   account_index_int: 12
#   address_index_int: 3
#   change_bool: True
#   network_str: mainnet
#   path: m/44/153/12/1/3
#   control_program: 001458b1477abc46ef81905d25011d36389c0788984b
#   address: bm1qtzc5w74ugmhcryzay5q36d3cnsrc3xztzw6u4y
#   address_base64: /9j/4AAQSkZJRgABAQA...
# test data 3:
#   xpub_str: 8fde12d7c9d6b6cbfbf344edd42f2ed86ae6270b36bab714af5fd5bb3b54adcec4265f1de85ece50f17534e42016ee9404a11fec94ddfadd4a064d27ef3f3f4c
#   account_index_int: 200
#   address_index_int: 1
#   change_bool: True
#   network_str: mainnet
#   path: m/44/153/200/1/1
#   control_program: 00144e5c8757c612c21aa2a0c55f1f8e2ab57cfdefca
#   address: bm1qfewgw47xztpp4g4qc403lr32k470mm724cphhp
#   address_base64: /9j/4AAQSkZJRgABAQA...
def get_new_address(xpub_hexstr, account_index_int, address_index_int, change_bool, network_str):
    path_str = get_path_from_index(account_index_int, address_index_int, change_bool)['path_str']
    control_program_hexstr = get_control_program(account_index_int, address_index_int, change_bool, xpub_hexstr)
    address_str = get_address(control_program_hexstr, network_str)
    address_base64 = create_qrcode_base64(address_str)

    vapor_address_str = get_vapor_address(control_program_hexstr, network_str)
    vapor_address_base64 = create_qrcode_base64(vapor_address_str)
    return {
        "path": path_str,
        "control_program": control_program_hexstr,
        "address": address_str,
        "address_base64": address_base64,
        "vapor_address": vapor_address_str,
        "vapor_address_base64": vapor_address_base64
    }


def get_main_vapor_address(private_key, network):
    xpub_hexstr = get_xpub(private_key)
    account_index_int = 1
    address_index_int = 1
    change_bool = False
    data = get_new_address(xpub_hexstr, account_index_int, address_index_int, change_bool, network)
    return data["address"], data["vapor_address"]
