#!/usr/bin/env python

import re
import urllib

url = "https://soundcloud.com/charts/top"
for i in re.findall("charTrack__username.*href=\"(.*)\"", urllib.urlopen(url).read(), re.I):
    print(i)

textfile.close()
