#!/usr/bin/env python
# encoding: utf-8

import json
from scrapy import Spider
from scrapy.http import Request
from spiders.common import parse_user_info, parse_time, url_to_mid

class CommentSpider(Spider):
    """
    微博评论数据采集
    """
    name = "comment"

    def start_requests(self):
        """
        爬虫入口
        """
        # 这里tweet_ids可替换成实际待采集的数据
        tweet_ids = ['Mb15BDYR0']
        for tweet_id in tweet_ids:
            mid = url_to_mid(tweet_id)
            url = f"https://weibo.com/ajax/statuses/buildComments?" \
                  f"is_reload=1&id={mid}&is_show_bulletin=2&is_mix=0&count=20"
            yield Request(url, callback=self.parse, meta={'source_url': url})

    def parse(self, response, **kwargs):
        """
        网页解析
        """
        data = json.loads(response.text)
        for comment_info in data['data']:
            item = self.parse_comment(comment_info)
            yield item
            # 解析二级评论
            if 'more_info' in comment_info:
                url = f"https://weibo.com/ajax/statuses/buildComments?is_reload=1&id={comment_info['id']}" \
                      f"&is_show_bulletin=2&is_mix=1&fetch_level=1&max_id=0&count=100"
                yield Request(url, callback=self.parse, priority=20)
        if data.get('max_id', 0) != 0 and 'fetch_level=1' not in response.url:
            url = response.meta['source_url'] + '&max_id=' + str(data['max_id'])
            yield Request(url, callback=self.parse, meta=response.meta)

    @staticmethod
    def parse_comment(data):
        """
        解析comment
        """
        item = dict()
        item['created_at'] = parse_time(data['created_at'])
        item['_id'] = data['id']
        item['like_counts'] = data['like_counts']
        item['ip_location'] = data.get('source', '')
        item['content'] = data['text_raw']
        item['comment_user'] = parse_user_info(data['user'])
        if 'reply_comment' in data:
            item['reply_comment'] = {
                '_id': data['reply_comment']['id'],
                'text': data['reply_comment']['text'],
                'user': parse_user_info(data['reply_comment']['user']),
            }
        return item
