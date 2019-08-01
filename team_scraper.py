##This script will run to scrape 247 for the team image ids. We'll build a dictionary of those to use in our crootbot function to tell what team a recruit has committed to. 
import requests
from bs4 import BeautifulSoup
import time
import json

pages = [1, 2, 3, 4]
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36'}

team_images = []
for p in pages:
    url = 'https://247sports.com/Season/2020-Football/CompositeTeamRankings/?ViewPath=~%2FViews%2FSkyNet%2FInstitutionRanking%2F_SimpleSetForSeason.ascx&Page={}&_=1562733003972'.format(p)
    page = requests.get(url=url, headers=headers)
    soup = BeautifulSoup(page.text, 'html.parser')
    team_images += soup.find_all(class_='team-image-block')
    time.sleep(1)

team_dict = {}

for t in team_images:
    image_url = t.find('img').get('data-src')
    team_id = (image_url.split('/')[-1].split('_')[-1].split('.')[0])

    print(t.find('img').get('title'))

    team_name = t.find('img').get('title')
    team_dict[team_id] = team_name

with open('team_ids.json', 'w') as fp:
    json.dump(team_dict, fp, sort_keys=True, indent=4)
