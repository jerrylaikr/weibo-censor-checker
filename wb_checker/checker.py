#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from datetime import datetime, timedelta
import json
import logging
import logging.config
import os
import random
import shutil
import sys
from time import sleep

import pymongo
from tqdm import tqdm

from wb_feed_spider.datetime_util import str_to_time
from wb_checker.parser.single_weibo_parser import SingleWeiboParser

logging_path = os.path.split(os.path.realpath(__file__))[0] + os.sep + "logging.conf"
logging.config.fileConfig(logging_path)
logger = logging.getLogger("checker")


class Checker:
    def __init__(self, config) -> None:
        # get deltatime after which a post is considered safe
        self.observation_interval = timedelta(hours=int(config["observation_interval"]))

        # get user cookie
        self.cookie = config["cookie"]

        # get DB configs
        self.mongo_config = config.get("mongo_config")

        # connect to MongoDB
        client = pymongo.MongoClient(self.mongo_config["connection_string"])
        db = client["weibo"]
        self.coll_wb, self.coll_keeper = db["weibo"], db["keeper"]

    def get_weibo_content_by_id(self, weibo_id) -> str:
        try:
            for i in range(6):
                if i > 0:
                    logger.info(f"Retry {i}/5")
                parser = SingleWeiboParser(self.cookie, weibo_id)
                weibo_content = parser.get_content()
                if weibo_content is not None:
                    return weibo_content
                sleep(random.randint(6, 16))

        except Exception as e:
            logger.exception(e)

    def _run(self):
        while True:
            ## sort weibo posts in chronogical order
            # doc_cursor = (
            #     self.coll_wb.find({}, {"_id": False}, no_cursor_timeout=True)
            #     .sort("publish_time", pymongo.ASCENDING)
            #     .batch_size(5)
            # )

            ## process finite amount of docs at a time
            ## to avoid CursorNotFound error
            doc_cursor = (
                self.coll_wb.find({}, {"_id": False}, no_cursor_timeout=True)
                .sort("publish_time", pymongo.ASCENDING)
                .limit(10)
            )

            for doc in doc_cursor:
                weibo_id = doc["id"]
                orig_content: str = doc["content"]

                logger.info("*" * 100)
                logger.info(doc["id"] + ", " + doc["publish_time"])

                # check if need to pause
                publish_time = str_to_time(doc["publish_time"])
                if publish_time > datetime.now() - self.observation_interval:
                    delta = publish_time + self.observation_interval - datetime.now()
                    logger.info(
                        f"sleep until {publish_time + self.observation_interval} ..."
                    )
                    logger.info(f"sleep for {int(delta.total_seconds())} seconds")
                    for _ in tqdm(range(int(delta.total_seconds()))):
                        sleep(1)

                # check for censor/modification
                logger.info("Checking...")
                fetched_content = self.get_weibo_content_by_id(weibo_id)

                # remove white spaces for comparison
                orig_content = "".join(orig_content.split())
                fetched_content = "".join(fetched_content.split())

                if (
                    orig_content == fetched_content
                    or orig_content == fetched_content[fetched_content.find(":") + 1 :]
                    or orig_content[orig_content.find(":") + 1 :] == fetched_content
                ):
                    logger.info("O" * 30 + "    SAME    " + "O" * 30)
                else:
                    logger.info("orig:\n" + orig_content)
                    logger.info("fetched:\n" + fetched_content)
                    logger.info("X" * 30 + "  NOT SAME  " + "X" * 30)
                    # add orig doc to keeper coll
                    doc_copy = {k: v for k, v in doc.items() if k != "_id"}
                    doc_copy["state"] = (
                        "DELETED" if not fetched_content else "MODIFIED"
                    )  # reason to keep this post
                    self.coll_keeper.update_one(
                        {"id": weibo_id},
                        {"$set": doc_copy},
                        upsert=True,
                    )

                # remove doc from weibo coll
                self.coll_wb.delete_one({"id": weibo_id})

                # for _ in tqdm(range(5)):
                #     sleep(0.2)

            doc_cursor.close()

            for _ in tqdm(range(30)):
                sleep(1)

    def run(self):
        """Start checking posts."""
        logger.info(
            "Approximate end time: {}".format(
                (datetime.now() - self.observation_interval).strftime("%Y-%m-%d %H:%M")
            )
        )
        try:
            self._run()
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
