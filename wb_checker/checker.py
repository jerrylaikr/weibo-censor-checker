import json
import logging
import os
import shutil
import sys

import pymongo

logging_path = os.path.split(os.path.realpath(__file__))[0] + os.sep + "logging.conf"
logging.config.fileConfig(logging_path)
logger = logging.getLogger("checker")


class Checker:
    def __init__(self, config) -> None:
        # get deltatime after which a post is considered safe
        self.observation_interval = config["observation_interval"]

        # get user cookie
        self.cookie = config["cookie"]

        # get DB configs
        self.mongo_config = config.get("mongo_config")

        pass

    def check_post(self, weibo_id: str) -> bool:
        pass

    def remove_post(self, weibo_id: str) -> None:
        pass

    def do_smth_to_censored_post(self, weibo_id: str):
        pass

    def run(self):
        """Start checking posts."""
        try:
            pass
        except Exception as e:
            logger.exception(e)


def _get_config() -> dict:
    """Get config from config.json"""
    src = os.path.split(os.path.realpath(__file__))[0] + os.sep + "config_sample.json"
    config_path = os.getcwd() + os.sep + "config.json"

    if not os.path.isfile(config_path):
        shutil.copy(src, config_path)
        logger.info(f"请先配置当前目录({os.getcwd()})下的config.json文件")
        sys.exit()
    try:
        with open(config_path) as f:
            config = json.loads(f.read())
            return config
    except ValueError:
        logger.error("config.json 格式不正确")
        sys.exit()


def main():
    try:
        config = _get_config()
        # config_util.validate_config(config)
        checker = Checker(config)

        checker.run()  # start running

    except Exception as e:
        logger.exception(e)


if __name__ == "__main__":
    main()
