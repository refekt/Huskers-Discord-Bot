import json
import datetime
from bs4 import BeautifulSoup
import requests
import time
import datetime
import cb_settings
import threading

CB_REFRESH_INTERVAL = 240
cb_list = []


def pull_crystal_balls_from_pages(year, page=1):
    # Headers are requires to avoid the Interal Server Error (500) when using request.get()
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36'}
    # URL for Steve Wiltfong's Crystal Ball predictdion history
    url = 'https://247sports.com/User/Steve-Wiltfong-73/Predictions/?Page={}&playerinstitution.primaryplayersport.recruitment.year={}&playerinstitution.primaryplayersport.sport=Football'.format(page, year)
    # print("Opening {}".format(url))
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


def load_cb_to_list():
    # This function will load the JSON into cb_list
    f = open('crystal_balls.json', 'r')
    temp_json = f.read()
    global cb_list
    cb_list = json.loads(temp_json)


def move_cb_to_list_and_json(pages=14, json_dump=False):
    # Loops through pull_crystal_balls_from_pages() 'pages' times.
    # Dumps to JSON is json_dump == True
    print("Starting")
    i = 1
    while i <= pages:
        print("*** Starting to pull page {} of data.".format(i))
        now = datetime.datetime.now()
        pull_crystal_balls_from_pages(now.year + 1, i)
        time.sleep(1)
        print("** Completed page {}.".format(i))
        i += 1
    print("*** All finished")
    # Sort cb_list[] by 'PredictedDate'

    # Dumps cb_list into a JSON file
    if json_dump:
        with open('crystal_balls.json', 'w') as fp:
            json.dump(cb_list, fp, sort_keys=True, indent=4)
        fp.close()


def check_last_run():
    now = datetime.datetime.now()
    check = cb_settings.last_run + datetime.timedelta(minutes=CB_REFRESH_INTERVAL)

    if now > check:
        print("Last time the JSON was pulled exceeded threshold")
        move_cb_to_list_and_json(json_dump=True)

        f = open('cb_settings.py', 'w')
        f.write('import datetime\nlast_run = datetime.datetime({}, {}, {}), {}, {}\n'.format(now.year, now.month, now.day, now.hour, now.minute))
        f.close()
    else:
        print("Last time JSON was pulled does not exceed threshold")
        load_cb_to_list()


def start_timer():
    # Start a timer
    check_timer = threading.Timer(CB_REFRESH_INTERVAL * 60)
    check_timer.start()
    print("Starting a timer to check back in {} minutes".format(CB_REFRESH_INTERVAL))


check_last_run()
start_timer()
