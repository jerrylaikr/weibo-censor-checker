# weibo-censor-checker
Check modified/censored weibo posts. 


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
