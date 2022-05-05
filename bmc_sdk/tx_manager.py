from threading import Lock

from .eth_client import EthClient
from .log_service import log_service_manager


class TxManager(object):
    def __init__(self, _client):
        self.client = _client

        self.tx_hash_set = set([])
        self.mutex = Lock()

    def add_tx(self, tx_hash):
        self.mutex.acquire()
        self.tx_hash_set.add(tx_hash)
        self.mutex.release()

    def loop_clear(self):
        to_test_arr = list(self.tx_hash_set)
        for tx_id in to_test_arr:
            try:
                transaction_info = self.client.get_transaction_receipt(tx_id)
                if transaction_info:
                    self.mutex.acquire()
                    if tx_id in self.tx_hash_set:
                        self.tx_hash_set.remove(tx_id)
                    self.mutex.release()

                    status = transaction_info["status"]
                    if status:
                        log_service_manager.write_log(f"[loop_clear] transaction tx_id:{tx_id} status:{status} ok!")
                    else:
                        log_service_manager.write_log(f"[loop_clear] transaction tx_id:{tx_id} failed!")
            except Exception as ex:
                log_service_manager.write_log(f"[loop_clear] {ex}")

    def is_empty(self):
        self.mutex.acquire()
        flag = (len(self.tx_hash_set) == 0)
        self.mutex.release()
        return flag





