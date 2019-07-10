##This script will run to scrape 247 for the team image ids. We'll build a dictionary of those to use in our crootbot function to tell what team a recruit has committed to. 
import requests
from bs4 import BeautifulSoup
import time
import json
import datetime

pages = [1, 2, 3, 4]
headers = {'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36'}
now = datetime.datetime.now()


def scrape_crystal_balls(year = now.year):
    crystal_balls = []

    url = 'https://247sports.com/college/nebraska/Season/{}-Football/TargetPredictions/'.format(year)
    page = requests.get(url=url, headers=headers)
    soup = BeautifulSoup(page.text, 'html.parser')

    cb_urls = set()

    for link in soup.find_all('a'):
        grab_url = link.get('href')
        if "https://247sports.com/player/" in grab_url.lower():
            # print("Found player", grab_url.lower())
            cb_urls.add(grab_url)

    print(cb_urls)

    """with open('team_ids.json', 'w') as fp:
        json.dump(team_dict, fp, sort_keys = True, indent = 4)"""


scrape_crystal_balls()
