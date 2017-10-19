#!/usr/bin/env python

import re
import urllib
from crawler import Crawler, CralwerCache

url = "https://soundcloud.com/charts/top"


crawler = Crawler(CrawlerCache('crawler.db',  depth=3))
crawler.crawl(url, no_cache=re.compile('^/$').match)

print crawler.content[url].keys()
