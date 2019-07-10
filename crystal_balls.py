##This script will run to scrape 247 for the team image ids. We'll build a dictionary of those to use in our crootbot function to tell what team a recruit has committed to. 
import requests
from bs4 import BeautifulSoup
import time
import json
import datetime

pages = [1, 2, 3, 4]
headers = {'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36'}
now = datetime.datetime.now()


def scrape_crystal_balls(year=now.year+1):
    url = 'https://247sports.com/User/Steve%20Wiltfong/Predictions/?PlayerInstitution.PrimaryPlayerSport.Sport=Football&PlayerInstitution.PrimaryPlayerSport.Recruitment.Year={}'.format(year)
    page = requests.get(url=url, headers=headers)
    soup = BeautifulSoup(page.text, 'html.parser')

    crystal_balls = soup.find_all(class_='target')

    for x in range(len(crystal_balls)):
        print(crystal_balls[x])

    # with open('crystal_balls.json', 'w') as fp:
        # json.dump(crystal_balls, fp, sort_keys=True, indent=4)


scrape_crystal_balls()
