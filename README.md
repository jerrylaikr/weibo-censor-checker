# weibo-censor-checker
Check modified/censored weibo posts. 

本程序可结合weibo-feed-spider或weiboSpider，检测爬取到的微博中有哪些被删改了，并将被删改的微博永久保存。

暂时不支持图片、视频保存。

现版本仅支持使用MongoDB存储，之后会考虑加入其他更方便本地运行的读写方式。

## Installation
Install dependency `weibo-spider`
```bash
git clone https://github.com/dataabc/weiboSpider.git
cd weiboSpider/
pip install -r requirements.txt .
```

Install dependency `weibo-feed-spider`
```bash
git clone https://github.com/jerrylaikr/weibo-feed-spider.git
cd weibo-feed-spider/
pip install .
```

Install from source code
```bash
$ git clone https://github.com/jerrylaikr/weibo-censor-checker.git
$ cd weibo-censor-checker
$ pip install .
```
Prepare `config.json`


## Run script

```bash
$ python3 -m weibo-censor-checker
```

也可以写个bash script放在根目录，方便后台运行
```bash
cd ~/weibo-censor-checker
nohup python3 -m wb_checker >/dev/null 2>&1 &
```

假设文件名是`run_checker.sh`
```bash
$ bash ~/run_checker.sh
```

---
## 思路

写个daemon挂在后台和weibo-feed-spider并行跑。

首先在weibo collection里面发布时间顺序排序：
```
find().sort({"publish_time":1})
```
以 `observation_interval = 24` 为例（一条微博24小时没有被夹即算存活）
对于每一个doc，检查 publish_time 是否小于（早于） now - 24h。

### 需要检查

如果`publish_time < now - 24h`，说明该微博发布后已经过了观察期24小时，需要检查该微博是否被夹。

检查被夹的方式是通过`doc["id"]`，爬取:`https://weibo.cn/comment/<doc["id"]>`

如果爬取失败（`weibo.content`为空）或`weibo.content`不等于`doc["content"]`说明被夹了。此时将该doc写入`keeper` collection永久保存。

如果`weibo.content`等于`doc["content"]`，说明该微博存活过了观察期，不需要把任何玩意写入`keeper` collection。

之后可以选择将该doc从`weibo` collection中移除。


### 不需要检查的情况

如果`publish_time > now - 24h`，说明这条微博发出来后还没经过24小时的观察期，还有被夹的可能性。因为按发布时间顺序排序，所以该cursor之后的doc也都不需要检测。此处可以直接休眠到`publish_time + 24h`。


## 现有的一些问题
原创短微博使用PageParser解析时会把用户名包括在content中，而原创长微博是用CommentParser解析，content不会包含发布者用户名。

计划A：让我自己魔改的Parser模仿原爬虫的解析方式，问题是难以判断是原创长微博还是短微博

**计划B：在compare时忽略可能存在的用户名。现在fetch_content原创未必都会有用户名加冒号，转发微博则是以`转发理由:`开头，直接再加一个条件。**

计划C：继续魔改weibo-feed-spider的Parser，用我的风格统一weibo_content储存格式。简单的改动就是让原创长短微博都不包含用户名。甚至可以每条微博都用CommentParser，问题在于不知道会不会触发反爬机制。