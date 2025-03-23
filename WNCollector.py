#Throws a wide net so that it doesn't miss any SBAs

# Collect friends list
# Convert unix timestamp to human readable datetime
# Sort by datetime added
# Check if account is already in database
# If account is in database skip
# If account is not in database add to database

# If friends list is less then 20 accounts add to search list
# If friends list is greater then 20 accounts store in database

from pymongo import MongoClient
from itertools import islice
from datetime import datetime
import requests
import argparse
import msvcrt
import time
import json
import sys

RED = "\033[31m"
GREEN = "\033[32m"
RESET = "\033[0m"

global timer
timer = (time.time(), 0.0)
global sleep_time

parser = argparse.ArgumentParser(description='Collects Steam profiles')
#parser.add_argument('--steamid', type=int, help='Steam ID to start from')
parser.add_argument('--api_key', type=str, help='Steam API key')
args = parser.parse_args()


DAY_SECONDS = 60*60*24
API_KEY = args.api_key
RATE_LIMIT = ((100000-10000)/DAY_SECONDS) # 90,000 requests per day
sleep_time = RATE_LIMIT
to_be_scanned = set()

def get_unscanned_profiles():
    unscanned_profiles = collection.find({
    '$and': [
        {
            "$or": 
            [
                {'publicFriendsList': True},
                {'publicFriendsList': {'$exists': False}}
            ]
        },
        {
            "$or":
            [
                {'friends': {'$exists': False}},
                {'friends': []}
            ]
        },
        {
            '$or':
            [
                {'friends_count': {'$exists': False}},
                {'friends_count': {'$lt': 10}}
            ]
        },
        {
            '$or':
            [
                {'publicProfile': {'$exists': False}},
                {'publicProfile': True}
            ]
        }
    ]
})
    return unscanned_profiles
def get_unkown_visibility_profiles():
    visibility_unknown = collection.find(
        { 'publicProfile': { '$exists': False } }
    )
    return visibility_unknown

def get_friends(steamid: int) -> list:
    global RATE_LIMIT
    global timer
    global sleep_time
    try:

        timer = (time.time(), time.time()-timer[0])

        if timer[1] < RATE_LIMIT:
            sleep_time += sleep_time*0.01
        else:
            sleep_time -= sleep_time*0.01

        time.sleep(sleep_time)
        url = f'https://api.steampowered.com/ISteamUser/GetFriendList/v1/?key={API_KEY}&steamid={steamid}&relationship=friend'
        response = requests.get(url)

        rcode = response.status_code
        
        print(f'{RED if rcode > 400 else GREEN}{rcode}{RESET}')

        if response.status_code == 401:
            print(f'{RED}Unauthorized {response.status_code} {response.reason} for response {response.url}{RESET}')
            return []
        if response.status_code == 403:
            print(f'{RED}Forbidden {response.status_code} {response.reason} for response {response.url}{RESET}')
            sys.exit()
        if response.status_code == 404:
            print(f'{RED}Not found {response.status_code} {response.reason} for response {response.url}{RESET}')
            sys.exit()
        if response.status_code == 500:
            print(f'{RED}Internal server error {response.status_code} {response.reason} for response {response.url}{RESET}')
            sys.exit()
        if response.status_code == 503:
            print(f'{RED}Service unavailable {response.status_code} {response.reason} for response {response.url}{RESET}')
            sys.exit()
        if response.status_code == 429:
            print(f'{RED}Rate limit reached {response.status_code} {response.reason} for response {response.url}{RESET}')
            RATE_LIMIT = RATE_LIMIT*1.1
            sleep_time = RATE_LIMIT
            data = {
                'timestamp': str(datetime.now()),
                'status_code': response.status_code,
                'headers': dict(response.headers),
                'body': response.text
            }
            with open("steam_api_log.json", "a+") as f:
                json.dump(data, f)
                f.write("\n")
            time.sleep(10)
            response = requests.get(url)
            if response.status_code == 429:
                print('Rate limit reached again, exiting')
                sys.exit()
        
    except requests.exceptions.RequestException as e:
        with open("steam_api_log.json", "a+") as f:
            json.dump({"timestamp": str(datetime.now()), "error": str(e)}, f)
            f.write("\n")
            
    friends = response.json()['friendslist']['friends']
    return friends


def scan_profiles(steamids: list[int]):
    global timer
    for index, steamid in enumerate(steamids):
        if msvcrt.kbhit():
            if msvcrt.getch() == b'q':
                return True
        to_be_scanned.discard(steamid)
        profile = collection.find_one({'steamid': steamid}, {'friends': 1})
        if profile and 'friends' in profile:
            continue
        friends = get_friends(steamid)
        print('Found ' + (f'{GREEN}' if len(friends)<10 else f'{RED}') + f'{len(friends):3d}{RESET} friends of {GREEN}{str(steamid)[:7]}{RESET}{str(steamid)[7:]}', end=' ')
        print(f'skipping all friends   | {index:3d}/50  {timer[1]:3.2f}s elapsed' if len(friends) > 10 or True else f'{GREEN}adding to search{RESET} | {index:3d}/50', end=' ') # skipping friends,  Remove True to add print statement correctly
        if len(friends) < 10 and False: # Remove False to add friends to search
            #print('something is wrong')
            for friend in friends:
                to_be_scanned.add(friend['steamid'])
                if not collection.find_one({'steamid': friend['steamid']}):
                    collection.insert_one({
                        'steamid': friend['steamid'],
                        'time_added_unix': int(time.time()),
                        })
        
        collection.update_one(
            {'steamid': str(steamid)},
            {
                '$setOnInsert': {
                    'time_added_unix': int(time.time())
                },
                '$set': {
                    'friends': friends,
                    'friends_count': len(friends),
                    'publicFriendsList': len(friends) > 0,
                    'scanTime': {
                        'friends': int(time.time())
                    }
                }, 
            }, upsert=True)
    return False

def get_visibility_100_profiles(steamids: str):
    try:
        url = f'https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/?key={API_KEY}&steamids={steamids}'
        response = requests.get(url)
        if response.status_code == 429:
                print('Rate limit reached')
                global RATE_LIMIT
                RATE_LIMIT = RATE_LIMIT*1.01
                time.sleep(10)
                response = requests.get(url)
                if response.status_code == 429:
                    print('Rate limit reached again, exiting')
                    sys.exit()
                    
    except Exception as e:
        print(f'Error: {e}')
        return

    time.sleep(RATE_LIMIT)
    profiles = response.json()['response']['players']
    if len(profiles) == 0:
        steamids = (steamids[1:-1]).split(',')

        print(f'{RED}DEBUG RESPONSE:{RESET}')
        print(f'Requests failed: {response.status_code} {response.reason} for response {response.url}')
        print(f'Response: {response.text}[:200]')
        print('-'*50)
        print(response.json())
        print('-'*50)
        print(f'{RED}DEBUG END{RESET}')
        print(f'Profiles {steamids} not found, possibly deleted profiles input 1 to sett to private, 2 to skip')
        choice = input()
        if choice == '1':
            for steamid in steamids:
                to_be_scanned.discard(steamid)
                collection.update_one(
                {'steamid': steamid},
                {
                    '$set': {
                        'publicProfile': False,
                    }, 
                }, upsert=True)

    for profile in profiles:
        visibility = profile.get('communityvisibilitystate', 0)
        if visibility == 3:
            collection.update_one(
            {'steamid': profile['steamid']},
            {
                '$set': {
                    'publicProfile': True,
                    'scanTime': {
                        'profile': int(time.time())
                    },
                    'profilestate': profile.get('profilestate', 0),
                    'lastlogoff': profile.get('lastlogoff', 0),
                    'timecreated': profile.get('timecreated', 0),
                    'personaname': profile.get('personaname', ''),
                    'primaryclanid': profile.get('primaryclanid', 0),
                    'personastate': profile.get('personastate', 0),
                    'personastateflags': profile.get('personastateflags', 0),
                    'realname': profile.get('realname', ''),
                }, 
            }, upsert=True)
        else:
            to_be_scanned.discard(profile['steamid'])
            collection.update_one(
            {'steamid': profile['steamid']},
            {
                '$set': {
                    'publicProfile': False,
                    'scanTime': {
                        'profile': int(time.time())
                    },
                    'profilestate': profile.get('profilestate', 0),
                    'lastlogoff': profile.get('lastlogoff', 0),
                    'timecreated': profile.get('timecreated', 0),
                    'personaname': profile.get('personaname', ''),
                    'primaryclanid': profile.get('primaryclanid', 0),
                    'personastate': profile.get('personastate', 0),
                    'personastateflags': profile.get('personastateflags', 0),
                    'realname': profile.get('realname', ''),
                }, 
            }, upsert=True)
            


if __name__ == '__main__':
    timer = (time.time(), time.time()-timer[0])
    print(timer[1])

    unknown_border = 500

    client = MongoClient('localhost', 27017)
    db = client['steam_db']
    collection = db['profiles']

    unscanned_profiles_from_db = get_unscanned_profiles()
    to_be_scanned.update(doc['steamid'] for doc in unscanned_profiles_from_db)
    #to_be_scanned.add(args.steamid)

    print('')
    print('-'*64)
    print(f'{GREEN}{len(to_be_scanned):6d}{RESET} Profiles left to be scanned, {GREEN}{collection.estimated_document_count():6d}{RESET} Profiles stored')
    while to_be_scanned:
        unkown_visibility_profiles = get_unkown_visibility_profiles()
        unkown_visibility_profiles = list(profile['steamid'] for profile in unkown_visibility_profiles)
        print(f'{GREEN}{len(unkown_visibility_profiles):6d}{RESET} Unknown visibility profiles, {GREEN}{unknown_border - len(unkown_visibility_profiles):6d}{RESET} Unknown remaining')
        if len(unkown_visibility_profiles) > 500:
            batches = [unkown_visibility_profiles[i: i + 100] for i in range(0, len(unkown_visibility_profiles), 100)]
            print(f'Scanning {len(unkown_visibility_profiles)} profiles with unknown visibility')
            print('Pausing for 10 seconds to')
            time.sleep(10)
            for batch in batches:
                if msvcrt.kbhit():
                    if msvcrt.getch() == b'q':
                        client.close()
                        break
                steamids = f'[{','.join(batch)}]'
                get_visibility_100_profiles(steamids)
        print('-'*64)
        beforeQueue = len(to_be_scanned)
        beforeStored = collection.estimated_document_count()
        beforeTime = time.time()
        if scan_profiles(list(islice(to_be_scanned, 50))):
            client.close()
            break
        print()
        print('-'*(33-8) + f'{GREEN}Rate of progress{RESET}' + '-'*31)
        deltatime = time.time() - beforeTime
        deltaQueue = len(to_be_scanned) - beforeQueue
        afterStored = collection.estimated_document_count()
        deltaStored = afterStored - beforeStored
        requestsPerDay = (50/deltatime)*DAY_SECONDS
        print(('Clearing queue' if deltaQueue < 0 else 'Adding to queue'), end=' ')
        print(f'at a rate of {GREEN}{((abs(deltaQueue)/deltatime)*DAY_SECONDS):3.1f}{RESET} profiles per day')
        print(f'-------------------Making {GREEN}{requestsPerDay:3.1f}{RESET} requests per day')
        print(f'Adding {GREEN}{deltaStored/deltatime:3.2f}{RESET} profiles per second to the database')
        print('-'*(33-8) + f'{GREEN}Progress{RESET}' + '-'*31)
        print(f'{GREEN}{len(to_be_scanned):6d}{RESET} profiles left to be scanned, {GREEN}{afterStored:6d}{RESET} Profiles in stored')