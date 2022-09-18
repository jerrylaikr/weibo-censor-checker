from weibo_spider.parser.comment_parser import CommentParser
from weibo_spider.parser.util import handle_garbled


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
