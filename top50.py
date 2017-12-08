#!/usr/bin/env python3
import re
import urllib
import requests
import pickle
import time
from geopy.geocoders import Nominatim
from selenium import webdriver

class Crawl():
    def __init__(self, url):
        self.url = url
        self.header = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36'}

        self.artists = {}
        self.id = 0

    def load_artists(self, fname="artists.p"):
        self.artists = pickle.load(open(fname, "rb"))
        self.id = len(self.artists)
        #print(self.id)

    def dump_artists(self, fname="artists.p"):
        pickle.dump(self.artists, open(fname, "wb"))

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

    def scrub_follow(self, url, name, key):

        # Following page info:
        #response = requests.get(url, headers=self.header)
        ######
        #driver = webdriver.Chrome('/mnt/c/chromedriver_win32/chromedriver.exe')
        driver = webdriver.Chrome('C:/Users/jbuxofplenty/Desktop/chromedriver_win32/chromedriver.exe')
        driver.get(url)
        #driver.find_element_by_link_text("All").click()
        for i in range(1, 100):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(0.01)
        html_source = driver.page_source
        content = html_source
        driver.close()
        #print(content)

        new_artists = []
        matches = re.findall('<div class="userBadgeListItem__title">[\s\n]+<a href="([^"]+)[^\n]+>[\r\n\s]+([^<]*)\n', content)
        self.artists[name][key] = []
        for match in matches:
            #print("href: %s\t name: %s" % (match[0], match[1]))
            if (match is not None) & (len(match) > 1):
                if ("." in match) | ("," in match):
                    continue

                href = match[0]
                name_follower = match[1]

                # Add artist to total set of artists
                if name_follower not in self.artists:
                    self.artists[name_follower] = {}
                    self.artists[name_follower]["href"] = href
                    self.artists[name_follower]["id"] = self.id
                    self.id += 1
                    # print("href: %s\t name: %s" % (match[0], match[1]))

                    new_artists.append(name_follower)

                # Add artist to followers of parent artist if not already scrubbed
                if name_follower not in self.artists[name][key]:
                    self.artists[name][key].append(name_follower)

        print("New Artists: %s" % new_artists)
        print("Length New Artists: %d" % len(new_artists))
        return new_artists

    def crawl_artist(self, name, depth=3):
        print(name)
        if type(name) is list:
            return []
        url = self.artists[name]["href"]
        url_artist = self.url + url
        url_following = url_artist + "/following"
        url_followers = url_artist + "/followers"

        # Main page info: num_followers, num_tracks
        response = requests.get(url_artist, headers=self.header)
        content = response.content.decode('utf-8')
        #print(content)

        matches = re.findall('([^ ]+) Tracks\. ([^ ]+) Followers\.', content)
        #print("Found %s matches" % len(matches))
        for match in matches:
            if (match is not None) & (len(match) > 1):
                if ("?" in match[0]) | ("?" in match[1]):
                    continue

                num_tracks = match[0]
                num_followers = match[1]

                self.artists[name]["num_tracks"] = num_tracks
                self.artists[name]["num_followers"] = num_followers
                self.id += 1

                #print("tracks: %s\t| followers: %s" % (num_tracks, num_followers))
        # Parse in the location
        matches = re.findall('"city":"([^"]+)', content)
        for match in matches:
            if (match is not None):
                if len(match) > 0 and match != 'Boulder':
                    artist_city = match
                    geolocator = Nominatim()
                    try:
                        location = geolocator.geocode(artist_city)
                    except:
                        location = None
                    if not location is None:
                        latitude = location.latitude
                        longitude = location.longitude
                    else:
                        latitude = ''
                        longitude = ''
                else:
                    artist_city = ''
                    latitude = ''
                    longitude = ''
                self.artists[name]["city"] = artist_city
                self.artists[name]["latitude"] = latitude
                self.artists[name]["longitude"] = longitude

        self.artists[name]["num_tracks"] = self.try_key(name, "num_tracks")
        self.artists[name]["num_followers"] = self.try_key(name, "num_followers")
        self.artists[name]["city"] = self.try_key(name, "city")
        self.artists[name]["latitude"] = self.try_key(name, "latitude")
        self.artists[name]["longitude"] = self.try_key(name, "longitude")

        print("name: %s\t num_tracks: %s\t num_followers: %s\t artist_city: %s" % (name, self.artists[name]["num_tracks"], self.artists[name]["num_followers"], self.artists[name]["city"]))
        new_artists = []
        new_artists = self.scrub_follow(url=url_following, name=name, key="following")
        new_artists.append(self.scrub_follow(url_followers, name=name, key="followers"))

        return new_artists

    def print_artists(self):
        for name in self.artists:
            print(self.artists[name])

    def try_key(self, artist, key):
        try:
            var = self.artists[artist][key]
            return var
        except:
            self.artists[artist][key] = ''
            return ''

def main(depth=3):
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
        count = 0
        for i in range(depth):
            print("Depth: %s" % i)
            print("->Artists: %s" % artist_list)

            new_artist_list = []
            for name in artist_list:
                new_artists = soundCrawler.crawl_artist(name)
                count += 1
                new_artist_list += new_artists
                if count % 50:
                    print("----------------\nArtists dumped to artists_large.p.\n-------------------------")
                    soundCrawler.dump_artists("artists_large.p")

            try:
                artist_list = new_artist_list
            except:
                artist_list = []

        # Check
        soundCrawler.print_artists()

        # Dump data for use later
        soundCrawler.dump_artists("artists_large.p")

if __name__ == '__main__':
    main(depth=3)
