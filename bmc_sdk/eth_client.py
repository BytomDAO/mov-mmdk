import os
import time
import logging
import functools
from typing import List, Any, Optional, Union, Tuple, Dict

from web3 import Web3
from web3.eth import Contract
from web3.contract import ContractFunction
from web3.types import (
    TxParams,
    Wei,
    Address,
    ChecksumAddress,
    Nonce,
    HexBytes,
)

import eth_account
from web3 import Web3, middleware
from web3.auto import w3
# 下面这个算gas 太慢了，还是用rpc吧
# from web3.gas_strategies.time_based import fast_gas_price_strategy
from web3.gas_strategies.rpc import rpc_gas_price_strategy

from web3.middleware import geth_poa_middleware

from .tokens import EthNet, get_symbol_2_contract_dict, get_symbol_2_decimal_dict
from .tokens import get_main_symbol_from_net
from .local_types import AddressLike
from .util import str_to_addr, validate_address, load_contract_erc20, addr_to_str
from .constants import ETH_ADDRESS, CROSS_ETH_RECEIVER_ADDRESS, CROSS_USDT_ERC20_RECEIVER_ADDRESS
from .config import SETTINGS

from .token import ERC20Token
from .util import load_contract
from .exceptions import InvalidToken

from .log_service import log_service_manager


class EthClient(object):
    def __init__(
            self,
            address,
            private_key,
            network=EthNet.MainNet.value,
            provider: str = None,
            web3: Web3 = None
    ):
        self.private_key = private_key

        if address:
            self.address = str_to_addr(address)
        else:
            self.address = eth_account.Account.from_key(self.private_key).address
        self.str_address = addr_to_str(self.address)

        self.network = network
        self.main_symbol = get_main_symbol_from_net(self.network)

        log_service_manager.write_log(f"[INFO] address:{addr_to_str(self.address)}, network:{self.network}")

        if web3:
            self.w3 = web3
        else:
            # Initialize web3. Extra provider for testing.
            self.provider = provider or SETTINGS["ETH_PROVIDER"]
            self.w3 = Web3(
                Web3.HTTPProvider(self.provider, request_kwargs={"timeout": 60})
            )

            if self.network in [EthNet.BscNet.value, EthNet.BmcTestNet.value, EthNet.BmcMainNet.value]:
                self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)

        self.w3.middleware_onion.add(middleware.time_based_cache_middleware)
        self.w3.middleware_onion.add(middleware.latest_block_based_cache_middleware)
        self.w3.middleware_onion.add(middleware.simple_cache_middleware)

        # self.w3.eth.setGasPriceStrategy(fast_gas_price_strategy)
        self.w3.eth.setGasPriceStrategy(rpc_gas_price_strategy)

        log_service_manager.info(f"Using {self.w3} ('{self.network}')")
        self.last_nonce: Nonce = self.w3.eth.getTransactionCount(self.address)

    def get_latest_nonce(self):
        self.last_nonce = self.w3.eth.getTransactionCount(self.address)
        return self.last_nonce

    @staticmethod
    def get_private_key_and_address_from_keystore(keystore_file_path, password=''):
        with open(keystore_file_path) as keyfile:
            encrypted_key = keyfile.read()
            private_key = w3.eth.account.decrypt(encrypted_key, password)
            address = eth_account.Account.from_key(private_key).address
            return private_key, address

    @staticmethod
    def get_client_from_keystore(obj, keystore_file_path, password='', net=EthNet.MainNet.value, provider=None):
        with open(keystore_file_path) as keyfile:
            encrypted_key = keyfile.read()
            private_key = w3.eth.account.decrypt(encrypted_key, password)
            address = eth_account.Account.from_key(private_key).address
            return obj(address, private_key, net, provider)

    @staticmethod
    def get_eth_client_from_keystore(keystore_file_path, password='Shabi86458043.', net=EthNet.MainNet.value, provider=None):
        return EthClient.get_client_from_keystore(EthClient, keystore_file_path, password, net, provider)

    def get_main_symbol(self):
        return self.main_symbol

    def get_main_symbol_token(self):
        symbol = get_main_symbol_from_net(self.network)
        decimals = get_symbol_2_decimal_dict(self.network)[symbol]
        return ERC20Token(self.main_symbol, ETH_ADDRESS, symbol, decimals)

    # ------ Test utilities ------------------------------------------------------------
    def get_token_addresses(self) -> Dict[str, ChecksumAddress]:
        """
        Returns a dict with addresses for tokens for the current net.
        Used in testing.
        """
        return get_symbol_2_contract_dict(self.network)

    # ------ Helpers ------------------------------------------------------------
    def get_token(self, address: AddressLike) -> ERC20Token:
        """
        Retrieves metadata from the ERC20 contract of a given token, like its name, symbol, and decimals.
        """
        # FIXME: This function should always return the same output for the same input
        #        and would therefore benefit from caching
        token_contract = load_contract(self.w3, abi_name="erc20", address=address)
        try:
            name = token_contract.functions.name().call()
            symbol = token_contract.functions.symbol().call()
            decimals = token_contract.functions.decimals().call()
        except Exception as e:
            log_service_manager.warning(
                f"Exception occurred while trying to get token {addr_to_str(address)}: {e}"
            )
            raise InvalidToken(address)
        return ERC20Token(symbol, address, name, decimals)

    def get_erc_20_token(self, token_symbol) -> ERC20Token:
        """
        Retrieves metadata from the ERC20 contract of a given token, like its name, symbol, and decimals.
        """
        token: AddressLike = self.get_contract_address(token_symbol)
        return self.get_token(token)

    def get_decimal(self, token_symbol) -> int:
        """Get the decimal of a token for your address. """
        dic = get_symbol_2_decimal_dict(self.network)
        if token_symbol in dic.keys():
            return dic[token_symbol]
        else:
            token: AddressLike = self.get_contract_address(token_symbol)
            if addr_to_str(token) == ETH_ADDRESS:
                dic[token] = 18
                return 18
            else:
                decimal = self.get_token(token).decimals
                dic[token] = decimal
                return decimal

    def get_decimal_from_contract(self, token: AddressLike):
        if addr_to_str(token) == ETH_ADDRESS:
            return 18
        else:
            return self.get_token(token).decimals

    def get_decimal_mul(self, token_symbol):
        """Get the decimal mul of a token for your address. """
        return 10 ** self.get_decimal(token_symbol)

    def get_decimal_mul_from_contract(self, token: AddressLike):
        """Get the decimal mul of a token for your address. """
        return 10 ** self.get_decimal_from_contract(token)

    def get_contract_address(self, token_symbol) -> AddressLike:
        """Get the contract address of a token """
        address: AddressLike = Web3.toChecksumAddress(
            get_symbol_2_contract_dict(self.network).get(token_symbol.upper(), None))
        if not address:
            log_service_manager.error(f"[get_contract_address] {token_symbol} not found!")
        return address

    # ------ Wallet balance ------------------------------------------------------------
    def get_eth_balance(self) -> Wei:
        """Get the balance of ETH for your address."""
        return self.w3.eth.get_balance(self.address)

    def get_token_balance(self, token: AddressLike) -> int:
        """Get the balance of a token for your address."""
        validate_address(token)
        if addr_to_str(token) == ETH_ADDRESS:
            return self.get_eth_balance()
        erc20 = load_contract_erc20(self.w3, token)
        balance: int = erc20.functions.balanceOf(self.address).call()
        return balance

    def get_balance(self, token_symbol) -> float:
        """Get the balance of a token for your address. """
        token: AddressLike = self.get_contract_address(token_symbol)
        balance = self.get_token_balance(token)
        return balance / self.get_decimal_mul(token_symbol)

    def get_balance_from_contract(self, token_address: AddressLike) -> float:
        balance = self.get_token_balance(token_address)
        return balance / self.get_decimal_mul_from_contract(token_address)

    def transfer_eth(self, to_address: AddressLike, qty: Wei):
        tx_params = self._get_tx_params(qty)
        tx_params["to"] = to_address
        return self.signed_and_send(tx_params, tx_params)

    def transfer_token(self, to_address: AddressLike, qty: Wei, token_symbol):
        if token_symbol.upper() == self.main_symbol:
            return self.transfer_eth(to_address, qty)
        else:
            token_address = self.get_contract_address(token_symbol)
            erc20_contract = load_contract_erc20(self.w3, token_address)

            return self.build_and_send_tx(
                erc20_contract.functions.transfer(
                    Web3.toChecksumAddress(to_address),
                    qty,
                )
            )

    def transfer(self, to_address: str, amount: float, token_symbol):
        qty = Wei(int(amount * self.get_decimal_mul(token_symbol.upper())))
        return self.transfer_token(Web3.toChecksumAddress(to_address), qty, token_symbol)

    def cross_eth(self, amount):
        return self.transfer_eth(CROSS_ETH_RECEIVER_ADDRESS, amount)

    def cross_usdt(self, amount):
        return self.transfer_token(CROSS_USDT_ERC20_RECEIVER_ADDRESS, amount, "USDT")

    # ------ Tx Utils ------------------------------------------------------------------
    def get_gas_price(self):
        return self.w3.eth.generateGasPrice()

    def estimate_gas(self, tx_params: Optional[TxParams]) -> int:
        return self.w3.eth.estimate_gas(tx_params)

    def estimate_function_gas(self, function: ContractFunction, tx_params: Optional[TxParams] = None)-> int:
        """Build and send a transaction."""
        if not tx_params:
            tx_params = self._get_tx_params()
        gas = function.estimateGas(tx_params)
        log_service_manager.debug(f"[estimateFunctionGas]:{tx_params}, gas:{gas}")
        return gas

    def build_tx(
            self, function: ContractFunction, tx_params: Optional[TxParams] = None
    ) -> (HexBytes, Optional[TxParams]):
        """Build and send a transaction."""
        if not tx_params:
            tx_params = self._get_tx_params()
        # tx_params['gasPrice'] = 5073058238
        transaction = function.buildTransaction(tx_params)
        log_service_manager.debug(f"transaction:{transaction}")
        return transaction, tx_params

    def signed_and_send(self, transaction: TxParams, tx_params: Optional[TxParams]) -> HexBytes:
        signed_txn = self.w3.eth.account.sign_transaction(
            transaction, private_key=self.private_key
        )
        # TODO: This needs to get more complicated if we want to support replacing a transaction
        # FIXME: This does not play nice if transactions are sent from other places using the same wallet.
        try:
            log_service_manager.debug(f"send_raw_transaction:{signed_txn.rawTransaction}")
            transaction_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            log_service_manager.debug(f"transaction_hash:{HexBytes(transaction_hash).hex()}")
            return transaction_hash
        finally:
            log_service_manager.debug(f"nonce: {tx_params['nonce']}")
            self.last_nonce = Nonce(tx_params["nonce"] + 1)

    def build_and_send_tx(
            self, function: ContractFunction, tx_params: Optional[TxParams] = None
    ) -> HexBytes:
        """Build and send a transaction."""
        transaction, tx_params = self.build_tx(function, tx_params)
        return self.signed_and_send(transaction, tx_params)

    def _get_tx_params(self, value: Wei = Wei(0), gas: Wei = Wei(250000)) -> TxParams:
        """Get generic transaction parameters."""
        return {
            "from": addr_to_str(self.address),
            "value": value,
            "gas": gas,
            "gasPrice": self.w3.eth.generate_gas_price(),
            "nonce": max(
                self.last_nonce, self.w3.eth.getTransactionCount(self.address)
            ),
        }

    def get_transaction(self, tx_id):
        '''
        AttributeDict({'blockHash': HexBytes('0x3a3263c953d968d1bf5bd1819e06c39c3b35ead3f62f0011bcadee3569e72029'), 'blockNumber': 12955975, 'from': '0x0a3D9a7221e2E2BD5E68C5ff592bF27DEA642Af1', 'gas': 54004, 'gasPrice': 25000000000, 'hash': HexBytes('0x7503996cbe1045d164b1b8115bea2d0a30b4e13632e4b391f10d6d5889746fe3'), 'input': '0x2e1a7d4d00000000000000000000000000000000000000000000000000d529ae9e860000', 'nonce': 15, 'r': HexBytes('0x08204ff6cc20566c24eaddfe8bbb2ce6239a57fd0ccb67cbd467c5caf80859c1'), 's': HexBytes('0x4b0f2e72f6e52a02f7d311431b76ca6dde09c5913a1ea305a4f7d68119528c95'), 'to': '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2', 'transactionIndex': 8, 'type': '0x0', 'v': 37, 'value': 0})
        AttributeDict({'blockHash': None, 'blockNumber': None, 'from': '0x5791A402700e7266Bb4Ec99E508fA25a05c762f0', 'gas': 69168, 'gasPrice': 23000000000, 'hash': HexBytes('0xb65c13fd363ea94dcf19eb3640479bbc3c219eb0add30217b2e5a7e35da78842'), 'input': '0x095ea7b300000000000000000000000065383abd40f9f831018df243287f7ae3612c62ac00000000000000000000000000000000000000000005aa3e9e1dac3156d72b20', 'nonce': 485, 'r': HexBytes('0x5263e55b5bc04ebe97540f8a4740ab19b3974e3392c2f270dd298260204603d4'), 's': HexBytes('0x3a471caea0587fcd45bba38b19352e495a89d82f70290f589cf923de6603311e'), 'to': '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2', 'transactionIndex': None, 'type': '0x0', 'v': 38, 'value': 0})

        失败的tx
        AttributeDict({'blockHash': HexBytes('0x312df2a453f14f6e1fdd4bf938abf70ef8ec35841451db80efeee7e619f60ee9'), 'blockNumber': 4891840, 'from': '0x18C91698658E510837CB483BB21a70B19E087c8B', 'gas': 90000, 'gasPrice': 130000000000, 'hash': HexBytes('0x0ed9f4f76312a7141975d29f40e042fecc8a9bc7f380e3a45156ddca7590750b'), 'input': '0x', 'nonce': 0, 'r': HexBytes('0xd080ad5e77ccda6b9d72c40e318f3f15ebf023200d17c20629957a1c75cc449c'), 's': HexBytes('0x47fb7f03395fc73736f5825e740f31116a5d7d4feda984b38da502b74a010d24'), 'to': '0xEDab973D01970f6F83962FE3AaaE818F1Cd13487', 'transactionIndex': 41, 'type': '0x0', 'v': 37, 'value': 100000000000000000})

        发现区分不出来失败的tx
        '''
        transaction_info = self.w3.eth.get_transaction(tx_id)
        return transaction_info

    def get_transaction_receipt(self, tx_id):
        '''
        失败交易
        AttributeDict({'blockHash': HexBytes('0x312df2a453f14f6e1fdd4bf938abf70ef8ec35841451db80efeee7e619f60ee9'), 'blockNumber': 4891840, 'contractAddress': None, 'cumulativeGasUsed': 882334, 'effectiveGasPrice': '0x1e449a9400', 'from': '0x18C91698658E510837CB483BB21a70B19E087c8B', 'gasUsed': 21334, 'logs': [], 'logsBloom': HexBytes('0x00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000'), 'status': 0, 'to': '0xEDab973D01970f6F83962FE3AaaE818F1Cd13487', 'transactionHash': HexBytes('0x0ed9f4f76312a7141975d29f40e042fecc8a9bc7f380e3a45156ddca7590750b'), 'transactionIndex': 41, 'type': '0x0'})
        成功交易
        AttributeDict({'blockHash': HexBytes('0xb3a8092f10edee46d37726613e9bd3630fe6a17da5e9188ac6d7c23c48c0a1c7'), 'blockNumber': 12955985, 'contractAddress': None, 'cumulativeGasUsed': 14612624, 'effectiveGasPrice': '0x55ae82600', 'from': '0x5791A402700e7266Bb4Ec99E508fA25a05c762f0', 'gasUsed': 46112, 'logs': [AttributeDict({'address': '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2', 'blockHash': HexBytes('0xb3a8092f10edee46d37726613e9bd3630fe6a17da5e9188ac6d7c23c48c0a1c7'), 'blockNumber': 12955985, 'data': '0x00000000000000000000000000000000000000000005aa3e9e1dac3156d72b20', 'logIndex': 339, 'removed': False, 'topics': [HexBytes('0x8c5be1e5ebec7d5bd14f71427d1e84f3dd0314c0f7b2291e5b200ac8c7c3b925'), HexBytes('0x0000000000000000000000005791a402700e7266bb4ec99e508fa25a05c762f0'), HexBytes('0x00000000000000000000000065383abd40f9f831018df243287f7ae3612c62ac')], 'transactionHash': HexBytes('0xb65c13fd363ea94dcf19eb3640479bbc3c219eb0add30217b2e5a7e35da78842'), 'transactionIndex': 107})], 'logsBloom': HexBytes('0x00000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000002000000080000000000042000200000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000400000000000000000000000000000020000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000010200000000000000000000000000000000000000000000000000000080000'), 'status': 1, 'to': '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2', 'transactionHash': HexBytes('0xb65c13fd363ea94dcf19eb3640479bbc3c219eb0add30217b2e5a7e35da78842'), 'transactionIndex': 107, 'type': '0x0'})

        能同过status 区分失败的交易
        找不到这笔交易的话，需要捕捉处理异常
        '''
        try:
            transaction_info = self.w3.eth.get_transaction_receipt(tx_id)
            return transaction_info
        except Exception as ex:
            log_service_manager.write_log(f"[get_transaction_receipt] ex:{ex}, tx_id:{tx_id}")
