#!/usr/bin/env python

import re
import certifi
import urllib3 as urllib
import html5lib
from urllib.request import urlopen


http = urllib.PoolManager(
        cert_reqs='CERT_REQUIRED',
        ca_certs=certifi.where())

url = 'https://soundcloud.com/charts/top'

# Open the html document and parse the data
with urlopen(url) as conn:
    element = html5lib.parse(conn.read())
    walker = html5lib.getTreeWalker("etree")
    stream = walker(element)
    s = html5lib.serializer.HTMLSerializer()
    output = s.serialize(stream)

    # Parse to the particular section
    for item in output:
        if item.find('<h1>Charts</h1>\n') > 0:
            data = item

    # Parse further to separate into different tracks
    data = data.split('<h2>Tracks</h2>')[1]
    data = data.split('<li>')[1:]
    for item in data:
        print(item)
        print('----------------')
    print(len(data))
#textfile.close()
