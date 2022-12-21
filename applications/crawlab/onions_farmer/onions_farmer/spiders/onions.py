# -*- coding: utf-8 -*-
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from scrapy.selector import Selector 
from urllib.parse import urlparse
from datetime import datetime
import scrapy
from scrapy.http.request import Request

class OnionsSpider(CrawlSpider):

    name = 'onions'
    allowed_domains = ['ahmia.fi','onionranks.com', 'thehiddenwiki.org', 'dark.fail', 'freshonifyfe4rmuh6qwpsexfhdrww7wnt5qmkoertwxmcuvm4woo4ad.onion', 'torchlu7soq4akgqojbby4fgfwsxyppjdlzry2qtn7lbghfalxurbjad.onion', 'tor66sewebgixwhcqfnp5inzp5x5uohhdy3kvtnyfxc2e5mxiuh34iid.onion', 'darknetlive.com', '3bbad7fauom4d6sgppalyqddsqbf5u5p56b5k5uk2zxsy3d6ey2jobad.onion',]
    start_urls = ['http://ahmia.fi', 'https://onionranks.com', 'https://thehiddenwiki.org', 'https://dark.fail', 'http://freshonifyfe4rmuh6qwpsexfhdrww7wnt5qmkoertwxmcuvm4woo4ad.onion', 'http://torchlu7soq4akgqojbby4fgfwsxyppjdlzry2qtn7lbghfalxurbjad.onion', 'http://tor66sewebgixwhcqfnp5inzp5x5uohhdy3kvtnyfxc2e5mxiuh34iid.onion/', 'https://darknetlive.com/onions', 'http://3bbad7fauom4d6sgppalyqddsqbf5u5p56b5k5uk2zxsy3d6ey2jobad.onion/discover']
    

    rules = [Rule(LinkExtractor(allow=[]), follow=True, callback='parse_onions')]

    custom_settings = {
        "DEPTH_LIMIT": 1,
        "COOKIES_ENABLED": False,
        "DOWNLOAD_DELAY": 0.1
    }

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
