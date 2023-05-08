# -*- coding: utf-8 -*-
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from scrapy.selector import Selector 
from urllib.parse import urlparse
from datetime import datetime


class OnionsSpider(CrawlSpider):
    name = 'onions'

    custom_settings = {
        "DEPTH_LIMIT": 3,
        "COOKIES_ENABLED": False,
        "DOWNLOAD_DELAY": 0.2
    }

    with open('advertisers.txt', 'r') as f:
        start_urls = f.readlines()

    allowed_domains = []
    for url in start_urls:
        allowed_domains.append(urlparse(url).netloc)

    rules = [Rule(LinkExtractor([]), follow=True, callback='parse_onions')]

    def parse_onions(self, response):
        sel = Selector(response)
        onions = sel.xpath('//body/descendant-or-self::*[not(self::script)]/text()').re(r'[a-z2-7]{55}d\.onion')

        for onion in onions:
            today = datetime.today().timestamp()
            advertiser = urlparse(response.url).netloc
            print(f"[{today}] {onion} found in {advertiser}")
            yield {
                'advertiser': advertiser,
                'onion': onion,
                'timestamp': today
            }