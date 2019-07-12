import json
import datetime
from bs4 import BeautifulSoup
import requests
import time

cb_list = []


def scrape_crystal_balls(year, page=1):
    # Headers are requires to avoid the Interal Server Error (500) when using request.get()
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36'}
    # URL for Steve Wiltfong's Crystal Ball predictdion history
    url = 'https://247sports.com/User/Steve-Wiltfong-73/Predictions/?Page={}&playerinstitution.primaryplayersport.recruitment.year={}&playerinstitution.primaryplayersport.sport=Football'.format(page, year)
    print("Opening {}".format(url))
    # Pull all data from the aforementioned URL
    page = requests.get(url=url, headers=headers)
    # Convert into a BeautifulSoup4 object
    soup = BeautifulSoup(page.text, 'html.parser')

    # Estbalishing variables for all desired data
    # We are pulling data from the HTML element <li class='...'></li>
    main_photo = soup.find_all('li', class_='main-photo')
    name = soup.find_all('li', class_='name')
    predicted_by = soup.find_all('li', class_='predicted-by')
    prediction = soup.find_all('li', class_='prediction')
    correct = soup.find_all('li', class_='correct')

    # This is a tough cookie. I'm going to loop over every target block we pulled and grab the info you want
    # Then store in a nested dictionary, then add it to a list.
    targets = soup.find_all('li', class_='target')
    for t in targets:
        # for the current target block, grab the main photo url.
        # I also split around ? and picked the first item from the result to get a url without the image width and height args
        main_photo = t.find(class_='main-photo').find('img').get('data-src').split('?')[0]
        # Grab the recruit's name. I'll also pull the profile url
        # <li class='name'><a ...>FirstName LastName</a>
        name = t.find(class_='name').find('a').get_text()
        # <li class='name'><a href='URL'>...</a>
        profile = t.find(class_='name').find('a').get('href')

        # I assume we want the percentages for each team from the predicted-by section. I'm going to do yet another dictionary lol
        teams = {}
        predicted_by = t.find(class_='predicted-by')
        # If a recruit is commmited an <a> tag will be present with a nested <img> tag. 
        if predicted_by.find('a'):
            committed_team = predicted_by.find('a').find('img').get('alt')
            teams[committed_team] = "Committed"
        # Predictions are stored in <li> elements
        else:
            # Change predicted_by from <li class='predicted-by'> to a list of all <li> elements within <li class='predicted-by'>
            predicted_by = predicted_by.find_all('li')
            for p in predicted_by:
                # team name
                if p.find('img'):
                    p_team = p.find('img').get('alt')
                else:
                    p_team = 'Unknown'
                # percentage
                p_percent = p.find('span').get_text()
                teams[p_team] = p_percent

        # Since we are looking at a free page, the prediction can differ if its a locked pick or free pick.
        # I'm going to first check if it's locked or not and handle it from there
        unlock = t.find(class_='prediction').find('div').find('div')
        # I noticed locked picks are two nested divs while free picks are one div containing a team image
        pick = 'VIP'
        if t.find(class_='prediction').find('div').find(class_='question-icon'):
            pick = 'Cloudy'
        elif t.find(class_='prediction').find('div').find(class_='icon-zero'):
            pick = 'Zero'
        elif not unlock:
            pick = t.find(class_='prediction').find('div').find('img').get('alt')
        # Correct is tough
        result_exist = t.find(class_='correct').find('svg')
        correct = 'TBD'
        if result_exist:
            correct = 'Correct'
            correct_incorrect = result_exist.find('g').find('circle')
            if correct_incorrect:
                correct = 'Incorrect'
        # YES!!! WOOO!
        prediction_time = t.find(class_='prediction-date')
        prediction_time = prediction_time.get_text().strip()

        # Now build the dictionary
        sub_dict = {'Name': name,
                    'Photo': main_photo,
                    'Profile': profile,
                    'Teams': teams,
                    'Prediction': pick,
                    'PredictionDate': str(prediction_time),
                    'Result': correct
                    }
        cb_list.append(sub_dict)
        
        # Now for the real work. Steve Wiltfong's historical predictions need to be gathered and stored.
        # Last checked there was 14 pages. This should only have to be pulled one time and then saved.
        # When pulling new CBs, we will pull the first page and compare that dict/list, sub_dict, against
        # the JSON file for identical matches. If a non-match is found, it'll have to be added to the 
        # JSON and sorted by prediction_time if possible. If not, reverse the JSON and append the list, dict, 
        # or JSON and add all together for historical data.


def compile_all_predictions(jsonDump=False):
    now = datetime.datetime.now()
    i = 1
    while i <= 14:
        print("*** Starting to pull page {} of data.".format(i))
        scrape_crystal_balls(now.year + 1, i)
        time.sleep(1)
        print("** Completed page {}.".format(i))
        i += 1
    # Dumps cb_list into a JSON file
    if jsonDump:
        with open('crystal_balls.json', 'w') as fp:
            json.dump(cb_list, fp, sort_keys=True, indent=4)


compile_all_predictions()
