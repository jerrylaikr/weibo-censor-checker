import logging
from weibo_spider.parser.comment_parser import CommentParser
from weibo_spider.parser.util import handle_garbled

logger = logging.getLogger("checker.single_weibo_parser")


class SingleWeiboParser(CommentParser):
    def __init__(self, cookie, weibo_id):
        super().__init__(cookie, weibo_id)

    def is_removed(self) -> bool:
        # 被夹了
        return self.selector.xpath("//div[@class='me']")

    def is_original_weibo(self):
        is_original = self.selector.xpath("//div[@class='c']/div/span[@class='cmt']")
        if len(is_original) >= 3:
            return False
        else:
            return True

    def get_content(self):
        """
        原创微博：
            不论长短，返回：用户名+":"+微博内容
        转发微博：
            返回"转发理由: "+转发理由+"原始用户: "+原po用户名+"转发内容: "+原po内容
        """
        try:
            if self.is_removed():
                # 被夹了
                logger.info("这条微博消失了！！！")
                return ""

            info = self.selector.xpath("//div[@class='c']")[1]
            if self.is_original_weibo():
                # 原创微博，需要加入用户名
                original_user = info.xpath("div/a/text()")[0]
                for i in range(3):
                    if i > 0:
                        logger.info(f"Retry {i}/3")
                    weibo_content = self.get_long_weibo()
                    if weibo_content is not None:
                        return original_user + ":" + weibo_content
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

        except Exception as e:
            logger.exception("网络出错")
            logger.exception(e)
