from datetime import datetime, timedelta
import random
import json
import requests
import os
from time import sleep
from dotenv import load_dotenv


# load environment variables
load_dotenv()
api_url = os.environ.get('API_REVIEW')
key_total = os.environ.get('KEY_TOTAL')
key_ratings = os.environ.get('KEY_RATINGS')
key_score = os.environ.get('KEY_SCORE')
key_pc = os.environ.get('KEY_PERC')
key_count = os.environ.get('KEY_COUNT')
key_update = os.environ.get('KEY_UPDATE')


DATE_FORMAT = "%Y-%m-%d"
TIME_FORMAT = "%H:%M:%S"

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "accept-language": "en-US,en;q=0.9"
}


# read last_updated file 
# collect restaurants that are pending updates
# return random 50 restaurants
def get_rest_to_fetch():

    # read file
    with open('last_updated.json', 'r') as f:
        last_updated_data = json.load(f)

    now = datetime.now()
    to_update = []

    for rest, last_updated_str in last_updated_data.items():
        # if never updated, add to list
        if last_updated_str == "":
            to_update.append(rest)
            continue
        # if last updated over 80 hours ago, add to list
        last_updated = datetime.strptime(last_updated_str, DATE_FORMAT)
        if (now - last_updated) > timedelta(hours=80):
            to_update.append(rest)

    # get 50 random restaurants
    will_update = random.sample(to_update, 50)
    return will_update


# get the api url with the restaurant code
def get_url(restaurant):
    return api_url.replace('rest_code', restaurant)


# get the count and % for particular score
def get_count_pc_by_score(score, ratings):
    for r in ratings:
        if r[key_score] == score:
            count = r[key_count]
            pc = r[key_pc]
            return count, pc


# review json to csv string
def data_to_csv_line(rest, data):
    cells = []
    cells.append(rest)
    try:
        # update time
        updated = data[key_update]
        cells.append(str(updated))
        # total review count
        total = data[key_total]
        cells.append(str(total))
        # get the count, % for each score
        ratings = data[key_ratings]
        for i in range(1, 6):
            count, pc = get_count_pc_by_score(i, ratings)
            cells.append(str(count))
            cells.append(str(pc))

    except Exception as e:
        cells.append(repr(e))

    return ', '.join(cells)


# save csv file
def save_csv(lines):
    fname = datetime.now().strftime(DATE_FORMAT + ' ' + TIME_FORMAT)
    csv_header = 'rest, updated, total'
    for i in range(1, 6):
        csv_header = f'{csv_header}, count{i}, pc{i}'
    with open(f'./data/{fname}.csv', 'w') as f:
        f.write('\n'.join([csv_header] + lines))


# update last_updated file
def update_last_updated(to_fetch):
    updated_at = datetime.now().strftime(DATE_FORMAT)
    with open('last_updated.json', 'r+') as f:
        # read json
        last_updated_data = json.load(f)
        # bring pointer to start
        f.seek(0)
        # update the dates
        for rest in to_fetch:
            last_updated_data[rest] = updated_at
        # write json
        json.dump(last_updated_data, f, indent=4)
        f.truncate()


# fetch review data for list of restaurants
# save data to file and update last_updated file
def fetch_review(to_fetch):

    lines = []

    # loop through 50 restaurants
    for rest in to_fetch:
        # pause for 1.5 seconds
        sleep(1.5)
        # fetch restaurant review
        url = get_url(rest)
        res = requests.get(url, headers=headers)
        
        # get the review data 
        # convert it to csv line
        if res.ok:    
            data = res.json()
            line = data_to_csv_line(rest, data)
        else:
            line = f'{rest}, status={res.status_code}'
        lines.append(line)

    # save review data and update last_updated
    save_csv(lines)
    update_last_updated(to_fetch)



def main():
    to_fetch = get_rest_to_fetch()
    fetch_review(to_fetch)


main()