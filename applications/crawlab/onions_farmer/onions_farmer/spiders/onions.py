# -*- coding: utf-8 -*-
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from scrapy.selector import Selector 
from urllib.parse import urlparse
from datetime import datetime


class OnionsSpider(CrawlSpider):
    name = 'onions'
    allowed_domains = ['ahmia.fi']
    start_urls = ['http://ahmia.fi']
    rules = [Rule(LinkExtractor(allow=[]), follow=True, callback='parse_onions')]

    def parse_onions(self, response):
        #self.logger.info('LOGGER %s')

        sel = Selector(response)
        onions = sel.xpath('//body/descendant-or-self::*[not(self::script)]/text()').re(r'[a-z2-7]{55}d\.onion')

       
        for onion in onions:
            today = datetime.today().timestamp()
            yield {
                'advertiser': urlparse(response.url).netloc,
                'onion': onion,
                'timestamp': today
            }