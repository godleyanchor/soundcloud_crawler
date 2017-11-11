#!/usr/bin/env python3

import re
import urllib
#from crawler import Crawler, CrawlerCache
import requests
import pickle
#print(content)

class Crawl():
    def __init__(self, url):
        self.url = url
        self.header = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36'}

        self.artists = {}
        self.id = 0

    def load_artists(self):
        self.artists = pickle.load(open("artists.p", "rb"))
        self.id = len(self.artists)
        #print(self.id)

    def dump_artists(self):
        pickle.dump(self.artists, open("artists.p", "wb"))

    def crawl_top_artists(self, url):
        response = requests.get(url, headers=self.header)
        content = response.content.decode('utf-8')

        matches = re.findall('<a href="([^ ]*)">(.*)<\/a>', content)
        for match in matches:
            if (match is not None) & (len(match[1]) > 0):
                if ("?" in match[0]) | ("?" in match[1]):
                    continue

                href = str(match[0])
                name = str(match[1])

                if name not in self.artists:
                    self.artists[name] = {}
                    self.artists[name]["href"] = href
                    self.artists[name]["id"] = self.id
                    self.id += 1
                    #print("href: %s\t| name: %s" % (match[0], match[1]))

    def crawl_artist(self, name, depth=10):
        url = self.artists[name]["href"]
        url_artist = self.url + url
        url_following = url_artist + "/following"

        # Main page info: num_followers, num_tracks
        response = requests.get(url_artist, headers=self.header)
        content = response.content.decode('utf-8')
        print(content)

        matches = re.findall('(([^ ]+) Tracks\. ([^ ]+) Followers\.)|("city":"([^"]+))', content)
        new_artists = []
        print(len(matches))
        for match in matches:
            if match is not None:
                if ("?" in match[0]) | ("?" in match[1]):
                    continue

                num_tracks = match[0]
                num_followers = match[1]

                self.artists[name]["num_tracks"] = num_tracks
                self.artists[name]["num_followers"] = num_followers
                self.id += 1

                #print("tracks: %s\t| followers: %s" % (num_tracks, num_followers))

        # Following page info:
        response = requests.get(url_following, headers=self.header)
        content = response.content.decode('utf-8')

        matches = re.findall('<h2 itemprop="name"><a itemprop="url" href="(.*)">(.*)<\/a><\/h2>', content)
        self.artists[name]["following"] = []
        for match in matches:
            if (match is not None) & (len(match[1]) > 0):
                if ("?" in match[0]) | ("?" in match[1]):
                    continue

                href = str(match[0])
                name_following = str(match[1])

                if name_following not in self.artists:
                    self.artists[name_following] = {}
                    self.artists[name_following]["href"] = href
                    self.artists[name_following]["id"] = self.id
                    self.id += 1
                    #print("href: %s\t| name: %s" % (match[0], match[1]))

                    new_artists.append(name)

                if name_following not in self.artists[name]["following"]:
                    self.artists[name]["following"].append(name_following)

        #print("New Artists: %s" % new_artists)
        return new_artists

    def print_artists(self):
        for name in self.artists:
            print(self.artists[name])

def main(depth=10):
        soundCrawler = Crawl("https://soundcloud.com")

        # Load old data
        #soundCrawler.load_artists()

        id = 0
        url_top = str(soundCrawler.url)+"/charts/top"

        # Initialize artists
        #print("Gathering top artists...")
        soundCrawler.crawl_top_artists(url_top)

        # Start crawling
        artist_list = list(soundCrawler.artists)
        for i in range(depth):
            print("Depth: %s" % i)
            print("->Artists: %s" % artist_list)

            new_artist_list = []
            for name in artist_list:
                new_artists = soundCrawler.crawl_artist(name)
                new_artist_list += new_artists

            try:
                artist_list = new_artist_list
            except:
                artist_list = []

        # Check
        soundCrawler.print_artists()

        # Dump data for use later
        soundCrawler.dump_artists()

if __name__ == '__main__':
    main(depth=10)
