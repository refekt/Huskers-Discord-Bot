# Source: http://www.huskers.com/SportSelect.dbml?DB_OEM_ID=100&SPID=22&SPSID=4&KEY=&Q_SEASON=2019
from bs4 import BeautifulSoup
import requests
import re

husker_roster_url = 'http://www.huskers.com/SportSelect.dbml?DB_OEM_ID=100&SPID=22&SPSID=4&KEY=&Q_SEASON='


async def download_roster(year=2019):
    print("***\nDownload Roster")

    global husker_roster_url
    husker_roster_url += str(year)

    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36'}
    page = requests.get(url=husker_roster_url, headers=headers)

    # Convert into a BeautifulSoup4 object
    soup = BeautifulSoup(page.text, 'html.parser')

    roster_body = soup.find_all('div', id='roster-grid-layout')

    # re_string = 'player left desktop-(first|second|third)\\stablet-(first|second|third)'
    for tag in soup.find_all(re.compile("player left desktop-")):
        print(tag.name)

    print("***")