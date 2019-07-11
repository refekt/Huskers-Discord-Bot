##This script will run to scrape 247 for the team image ids. We'll build a dictionary of those to use in our crootbot function to tell what team a recruit has committed to. 
import requests
from bs4 import BeautifulSoup
import time
import json
import datetime

cb_list = []

def scrape_crystal_balls(year):
    headers = {'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36'}
    url = 'https://247sports.com/User/Steve-Wiltfong-73/Predictions/?Page=1&playerinstitution.primaryplayersport.recruitment.year={}&playerinstitution.primaryplayersport.sport=Football'.format(year)
    page = requests.get(url=url, headers=headers)
    soup = BeautifulSoup(page.text, 'html.parser')

    #pull every 'target' block
    targets = soup.find_all('li', class_='target')
    
    #This is a tough cookie. I'm going to loop over every target block we pulled and grab the info you want, then store in a nested dictionary, then add it to a list.
    for t in targets:
        #for the current target block, grab the main photo url. I also split around ? and picked the first item from the result to get a url without the 
        #image width and height args
        main_photo = t.find(class_='main-photo').find('img').get('data-src').split('?')[0]
        #Grab the recruit's name. I'll also pull the profile url
        name = t.find(class_='name').find('a').get_text()
        profile = t.find(class_='name').find('a').get('href')

        #I assume we want the percentages for each team from the predicted-by section. I'm going to do yet another dictionary lol
        teams = {}
        predicted_by = t.find(class_='predicted-by')

        if predicted_by.find('a'):
            committed_team = predicted_by.find('a').find('img').get('alt')
            teams[committed_team] = "Committed"
        else:
            predicted_by = predicted_by.find_all('li')
            for p in predicted_by:
                #team name
                if p.find('img'):
                    p_team = p.find('img').get('alt')
                else:
                    p_team = 'Unknown'
                #percentage
                p_percent = p.find('span').get_text()
                teams[p_team] = p_percent

        #since we are looking at a free page, the prediction can differ if its a locked pick or free pick. I'm going to first check if it's locked or not and handle it from there
        unlock =  t.find(class_='prediction').find('div').find('div')
        #I noticed locked picks are two nested divs while free picks are one div containing a team image
        pick = 'Locked'
        if not unlock:
            pick = t.find(class_='prediction').find('div').find('img').get('alt')
        #Correct is tough
        result_exist = t.find(class_='correct').find('svg')
        correct = 'Unknown'
        if result_exist:
            correct = 'Correct'
            correct_incorrect = result_exist.find('g').find('circle')
            if correct_incorrect:
                correct = 'Incorrect'
        
        #Now build the dictionary
        sub_dict = {'Photo' : main_photo,
                    'Profile' : profile,
                    'Teams' : teams,
                    'Prediction' : pick,
                    'Result' : correct
                    }
        t_dict = {name : sub_dict}
        cb_list.append(t_dict)

    # Should I dump all the contents of crystal_balls into a new string to make a new soup?
    # To search for sub items?

    """crystal_balls = soup.find_all(class_='target')
    for x in range(len(crystal_balls)):
        print(crystal_balls[x])"""

    with open('crystal_balls.json', 'w') as fp:
        json.dump(cb_list, fp, sort_keys=True, indent=4)


now = datetime.datetime.now()
scrape_crystal_balls(now.year + 1)
