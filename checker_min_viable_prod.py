from datetime import datetime, timedelta
from time import sleep
import pymongo
from tqdm import tqdm
from weibo_spider.datetime_util import str_to_time
from weibo_spider.parser.util import handle_garbled


def main():
    observation_interval = timedelta(hours=24)
    cookie = ""
    connection_string = ""

    # connect to MongoDB
    client = pymongo.MongoClient(connection_string)

    db = client["weibo"]
    coll_wb, coll_keeper = db["weibo"], db["keeper"]

    # start running
    while True:
        doc_cursor = coll_wb.find({}, {"_id": False}).sort(
            "publish_time", pymongo.ASCENDING
        )
        while doc_cursor.alive:
            doc = doc_cursor.next()
            weibo_id = doc["id"]
            orig_content: str = doc["content"]

            print("*" * 100)
            print(doc["id"])
            print(doc["publish_time"])

            # check if need to pause
            publish_time = str_to_time(doc["publish_time"])
            if publish_time > datetime.now() - observation_interval:
                delta = publish_time + observation_interval - datetime.now()
                print(f"sleep until {publish_time + observation_interval} ...")
                print(f"sleep for {int(delta.total_seconds())} seconds")
                for _ in tqdm(range(int(delta.total_seconds()))):
                    sleep(1)

            # check for censor/modification
            print("Checking...")
            fetched_content = get_weibo_content_by_id(cookie, weibo_id)

            orig_content = "".join(orig_content.split())
            fetched_content = "".join(fetched_content.split())

            print("orig:\n" + orig_content)
            print("fetched:\n" + fetched_content)

            if orig_content == fetched_content:
                print("O" * 50 + "   SAME   " + "O" * 50)
            else:
                print("X" * 50 + " NOT SAME " + "X" * 50)
                # add orig doc to keeper coll
                coll_keeper.update_one(
                    {"id": weibo_id},
                    {"$set": doc},
                    upsert=True,
                )

            # remove doc from weibo coll
            coll_wb.delete_one({"id": weibo_id})

            # for _ in tqdm(range(5)):
            #     sleep(0.2)
        for _ in tqdm(range(60)):
            sleep(1)


from weibo_spider.parser.comment_parser import CommentParser


class SingleWeiboParser(CommentParser):
    def __init__(self, cookie, weibo_id):
        super().__init__(cookie, weibo_id)

    def is_removed(self):
        # 被夹了
        return self.selector.xpath("//div[@class='me']")

    def is_original_weibo(self):
        is_original = self.selector.xpath("//div[@class='c']/div/span[@class='cmt']")
        if len(is_original) >= 3:
            return False
        else:
            return True

    def get_content(self):
        if self.is_removed():
            # 被夹了
            return ""

        weibo_content = ""
        info = self.selector.xpath("//div[@class='c']")[1]
        if self.is_original_weibo():
            # 原创微博，需要加入用户名
            original_user = info.xpath("div/a/text()")[0]
            return original_user + ":" + self.get_long_weibo()
        else:
            # 拼接转发信息
            orig_post = self.get_long_retweet()
            wb_time = info.xpath("//span[@class='ct']/text()")[0]
            retweet_reason = handle_garbled(info.xpath("div")[-1])
            retweet_reason = retweet_reason[: retweet_reason.rindex(wb_time)]
            original_user = info.xpath("div/span[@class='cmt']/a/text()")
            if original_user:
                original_user = original_user[0].replace("@", "")
                weibo_content = (
                    retweet_reason
                    + "\n"
                    + "原始用户: "
                    + original_user
                    + "\n"
                    + "转发内容: "
                    + orig_post
                )
            else:
                weibo_content = retweet_reason + "\n" + "转发内容: " + orig_post
            return weibo_content


def get_weibo_content_by_id(cookie, weibo_id) -> str:
    try:
        parser = SingleWeiboParser(cookie, weibo_id)
        return parser.get_content()

    except Exception as e:
        # logger.exception(e)
        print(e)


def is_original_weibo(selector):
    is_original = selector.xpath("//div[@class='c']/div/span[@class='cmt']")
    if len(is_original) >= 3:
        return False
    else:
        return True


if __name__ == "__main__":
    main()
