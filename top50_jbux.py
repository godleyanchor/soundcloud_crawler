#!/usr/bin/env python3

import re
import certifi
import urllib3 as urllib
import html5lib
from urllib.request import urlopen


http = urllib.PoolManager(
        cert_reqs='CERT_REQUIRED',
        ca_certs=certifi.where())

url = 'https://soundcloud.com'
url_top = str(url)+'/charts/top'

headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}

# Open the html document and parse the data
with urlopen(url_top) as conn:
    element = html5lib.parse(conn.read())
    walker = html5lib.getTreeWalker("etree")
    stream = walker(element)
    s = html5lib.serializer.HTMLSerializer()
    output = s.serialize(stream)

    # Parse to the particular section
    data = -1
    for item in output:
        #if item.find('<a href="\/([a-zA-Z]+)" class="sc-link-light">[a-zA-Z\s\</a>]+\n') > 0:
        if item.find('a') > 0:
            print(item)

        if len(item) < 0:
            continue
        #match = re.search('<a href="(.*)" class="sc.link.light">(.*)<\/a>', item)
        match = re.search('<a href="(.*)"', item)
        #print("item: %s\t| match: %s" % (item, match))
        if match is not None:
            href = match.group(1)
            name = match.group(2)
            print("Name: %s\t| href: %s" % (name, href))

    # Parse further to separate into different tracks
    if data != -1:
        data = data.split('<h2>Tracks</h2>')[1]
        data = data.split('<li>')[1:]
        for item in data:
            print(item)
            print('----------------')
        print(len(data))
#textfile.close()
