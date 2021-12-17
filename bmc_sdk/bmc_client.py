# encoding: UTF-8


from web3.types import Wei

from .util import addr_to_str, get_two_currency
from .constants import ETH_ADDRESS

from .constants import Direction
from .tokens import EthNet
from .uniswap import Uniswap
from .log_service import log_service_manager


class BmcClient(Uniswap):
    '''
    免费: 100,000 次/天
    50美元/月: 200,000 次/天
    225美元/月: 1000,000  次/天
    1000美元/月: 5,000,000  次/天
    '''

    def __init__(self, address, private_key, network=EthNet.MainNet.value, provider="", version=2):
        if not provider:
            if network == EthNet.BmcTestNet.value:
                provider = "http://8.218.17.184:8545"
            else:
                provider = "https://mainnet.infura.io/v3/8d2b78ac1e7447b59aba185c155477a3"  # my key
        super(BmcClient, self).__init__(address=address, private_key=private_key,
                                            network=network,
                                            provider=provider, version=version)

    @staticmethod
    def get_bytom_client_from_keystore(keystore_file_path, password='', net=EthNet.BmcTestNet.value):
        return BmcClient.get_client_from_keystore(BmcClient, keystore_file_path, password, net)

    def get_sell_price(self, symbol, volume=3):
        target_symbol, base_symbol = get_two_currency(symbol)
        target_symbol = target_symbol.upper()
        base_symbol = base_symbol.upper()
        return self.get_price_input(self.get_contract_address(target_symbol),
                                    self.get_contract_address(base_symbol),
                                    int(self.get_decimal_mul(target_symbol) * volume)) / (
                       self.get_decimal_mul(base_symbol) * volume)

    def get_buy_price(self, symbol, volume=3000):
        target_symbol, base_symbol = get_two_currency(symbol)
        target_symbol = target_symbol.upper()
        base_symbol = base_symbol.upper()

        price = self.get_price_input(self.get_contract_address(base_symbol),
                                     self.get_contract_address(target_symbol),
                                     int(self.get_decimal_mul(base_symbol) * volume)) / (
                        self.get_decimal_mul(target_symbol) * volume)
        return 1.0 / price

    def trade(self, symbol, direction, price, volume):
        target_symbol, base_symbol = get_two_currency(symbol)
        target_symbol = target_symbol.upper()
        base_symbol = base_symbol.upper()

        if direction == Direction.LONG.value:
            target_symbol, base_symbol = base_symbol, target_symbol
            volume = price * volume

        qty = Wei(int(volume * self.get_decimal_mul(target_symbol)))
        log_service_manager.write_log(f"[trade] symbol:{symbol}"
                                      f" direction:{direction},"
                                      f" price:{price},"
                                      f" volume:{volume},"
                                      f" qty:{qty}")
        transaction, tx_params = self.make_trade(self.get_contract_address(target_symbol),
                                                 self.get_contract_address(base_symbol),
                                                 qty)
        return transaction, tx_params

    def simple_trade(self, symbol, direction, price, volume):
        target_symbol, base_symbol = get_two_currency(symbol)
        target_symbol = target_symbol.upper()
        base_symbol = base_symbol.upper()

        if direction == Direction.LONG.value:
            target_symbol, base_symbol = base_symbol, target_symbol
            input_volume = price * volume
            output_volume = volume
        else:
            input_volume = volume
            output_volume = price * volume

        input_amount = Wei(int(input_volume * self.get_decimal_mul(target_symbol)))
        output_amount = Wei(int(output_volume * self.get_decimal_mul(base_symbol)))
        log_service_manager.write_log(f"[trade] symbol:{symbol}"
                                      f" direction:{direction},"
                                      f" price:{price},"
                                      f" volume:{volume},"
                                      f" input_amount:{input_amount}"
                                      f" output_amount:{output_amount}")
        transaction, tx_params = self.simple_make_trade(
                                                        self.get_contract_address(target_symbol),
                                                        self.get_contract_address(base_symbol),
                                                        input_amount,
                                                        output_amount
                                                        )
        return transaction, tx_params

    def check_approve_and_go_approve(self, symbol):
        all_ok = True
        target_symbol, base_symbol = get_two_currency(symbol)

        for token_symbol in [target_symbol, base_symbol]:
            token = self.get_contract_address(token_symbol)
            if addr_to_str(token) == ETH_ADDRESS:
                log_service_manager.write_log("[check_approve_and_go_approve] ETH_ADDRESS no need to approve!")
            else:
                is_approved = self._is_approved(token)
                # logger.warning(f"Approved? {token}: {is_approved}")
                if not is_approved:
                    log_service_manager.write_log(f"[check_approve_and_go_approve] go to approve {addr_to_str(token)}")
                    self.approve(token)

                    if not self._is_approved(token):
                        log_service_manager.write_log(f"[check_approve_and_go_approve] some error may existed!")
                        all_ok = False
                else:
                    log_service_manager.write_log(f"[check_approve_and_go_approve] {addr_to_str(token)}"
                                                  f" already approved ! no need to approve!")
        return all_ok
