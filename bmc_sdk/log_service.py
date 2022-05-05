# coding=utf-8

import logging
import os
from pathlib import Path
from multiprocessing import Value
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler

from .config import SETTINGS


def _get_trader_dir(temp_name):
    """
    Get path where trader is running in.
    """
    cwd = Path.cwd()
    temp_path = cwd.joinpath(temp_name)

    # If .tumbler folder exists in current working directory,
    # then use it as trader running path.
    if temp_path.exists():
        return cwd, temp_path

    # Otherwise use home path of system.
    # home_path = os.environ.get("HOME",".")
    home_path = "."
    temp_path = os.path.join(home_path, temp_name)

    # Create .tumbler folder under home path if not exist.
    if not os.path.exists(temp_path):
        os.mkdir(temp_path)

    return home_path, temp_path


TRADER_DIR, TEMP_DIR = _get_trader_dir(".tumbler")


def get_folder_path(folder_name):
    """
    Get path for temp folder with folder name.
    """
    folder_path = os.path.join(str(TEMP_DIR), str(folder_name))
    if not os.path.exists(folder_path):
        os.mkdir(folder_path)
    return folder_path


def get_module_logger(module_name, level=None):
    """
    Get a logger for a specific module.

    :param module_name: str
        Logic module name.
    :param level: int
    :param sh_level: int
        Stream handler log level.
    :param log_format: str
    :return: Logger
        Logger object.
    """
    if level is None:
        level = logging.INFO

    module_name = "qlib.{}".format(module_name)
    # Get logger.
    module_logger = logging.getLogger(module_name)
    module_logger.setLevel(level)
    return module_logger


class LogService(object):

    def __init__(self):
        self.level = SETTINGS["log.level"]
        self.logger = logging.getLogger("tumbler")
        self.logger.setLevel(self.level)

        self.lock_counter = Value('i', 0)

        self.formatter = logging.Formatter('%(asctime)s  %(levelname)s: %(message)s')

        self.add_null_handler()

        if SETTINGS["log.console"]:
            self.add_console_handler()

        if SETTINGS["log.file"]:
            self.add_file_handler()

    def write_log(self, msg, level=logging.INFO):
        """
        write log info
        """
        with self.lock_counter.get_lock():
            self.logger.log(level, msg)

    def add_null_handler(self):
        """
        Add null handler for logger.
        """
        null_handler = logging.NullHandler()
        self.logger.addHandler(null_handler)

    def add_console_handler(self):
        """
        Add console output of log.
        """
        console_handler = logging.StreamHandler()
        console_handler.setLevel(self.level)
        console_handler.setFormatter(self.formatter)
        self.logger.addHandler(console_handler)

    def add_file_handler(self):
        """
        Add file output of log.
        """
        today_date = datetime.now().strftime("%Y%m%d")
        filename = "tb_run_{}.log".format(today_date)
        log_path = get_folder_path("log")
        file_path = os.path.join(log_path, filename)

        file_handler = TimedRotatingFileHandler(filename=file_path, when="D", interval=1, backupCount=0,
                                                encoding='utf-8', delay=False)
        file_handler.suffix = "%Y%m%d%H%M%S"
        file_handler.setFormatter(self.formatter)
        file_handler.setLevel(self.level)

        self.logger.addHandler(file_handler)

    def debug(self, msg):
        with self.lock_counter.get_lock():
            self.logger.debug(msg)

    def info(self, msg):
        with self.lock_counter.get_lock():
            self.logger.info(msg)

    def warning(self, msg):
        with self.lock_counter.get_lock():
            self.logger.warning(msg)

    def error(self, msg):
        with self.lock_counter.get_lock():
            self.logger.error(msg)


log_service_manager = LogService()
