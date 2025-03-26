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
from Display import Display, DisplayType
import QueueGenerators
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
global quiting
quiting = False

SUMMARY_RATE_MODIFIER = 5


parser = argparse.ArgumentParser(description='Collects Steam profiles')
parser.add_argument('--steamid', type=int, help='Steam ID to start from')
parser.add_argument('--api_key', type=str, help='Steam API key')
args = parser.parse_args()

S_DAY = 60*60*24
S_HOUR = 60*60
S_MINUTE = 60
API_KEY = args.api_key
RATE_LIMIT = ((100000-10000)/S_DAY) # 90,000 requests per day
sleep_time = RATE_LIMIT
scan_queue = set()



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

def get_friends(steamid: int, display: Display) -> list:
    global RATE_LIMIT
    global timer
    global sleep_time
    try:

        timer = (time.time(), time.time()-timer[0])

        time.sleep(sleep_time)
        url = f'https://api.steampowered.com/ISteamUser/GetFriendList/v1/?key={API_KEY}&steamid={steamid}&relationship=friend'
        response = requests.get(url)

        rcode = response.status_code

        if response.status_code == 401:
            display.add_log(f'{RED}{response.status_code} {response.reason} for response {response.url[28:]}{RESET}')
            return []
        if response.status_code == 403:
            display.add_log(f'{RED}Forbidden {response.status_code} {response.reason} for response {response.url}{RESET}')
            return []
        if response.status_code == 404:
            display.add_log(f'{RED}Not found {response.status_code} {response.reason} for response {response.url}{RESET}')
            return []
        if response.status_code == 500:
            display.add_log(f'{RED}Internal server error {response.status_code} {response.reason} for response {response.url}{RESET}')
            return []
        if response.status_code == 503:
            display.add_log(f'{RED}Service unavailable {response.status_code} {response.reason} for response {response.url}{RESET}')
            return []
        if response.status_code == 429:
            display.add_log(f'{RED}Rate limit reached {response.status_code} {response.reason} for response {response.url}{RESET}')
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
            display.add_log('Pausing for 600 seconds to wait for rate limit to reset')
            for  i in range(0, 600):
                display.add_log(f'----------------- {GREEN}{600-i}{RESET}S -----------------')
                time.sleep(1)
            response = requests.get(url)
            if response.status_code == 429:
                display.add_log('Pausing for 24 hours to wait for rate limit to reset')
                for  i in range(0, S_DAY):
                    display.add_log(f'----------------- {GREEN}{S_DAY-i}{RESET}S -----------------')
                    time.sleep(1)
                return []
        
    except requests.exceptions.RequestException as e:
        with open("steam_api_log.json", "a+") as f:
            json.dump({"timestamp": str(datetime.now()), "error": str(e)}, f)
            f.write("\n")
            
    friends = response.json()['friendslist']['friends']

    return friends

def add_friends_to_db(friends: list):
    for friend in friends:
        if not collection.find_one({'steamid': friend['steamid']}):
            collection.insert_one({
                'steamid': friend['steamid'],
                'time_added_unix': int(time.time()),
                })

def scan_profiles(steamids: list[int], display: Display) -> bool:
    global timer
    global quiting
    for index, steamid in enumerate(steamids):
        if msvcrt.kbhit():
            if msvcrt.getch() == b'q':
                quiting = True
                return True
        scan_queue.discard(steamid)
        display.update_header_data({
            'queue_length': len(scan_queue),
        })
        if type(steamid) == str:
            try:
                steamid = int(steamid)
            except (ValueError, TypeError, OverflowError):
                display.add_log(f'Error: {steamid} is not a valid steamid')
                continue
            
        friends = get_friends(steamid, display)

        friend_count = len(friends)

        url = f'https://steamcommunity.com/profiles/{steamid}'
        hyperlink = f"\033]8;;{url}\033\\{str(steamid)[7:]}\033]8;;\033\\"

        if friend_count > 10:
            display.add_log(f"Found {RED}{friend_count:3d}{RESET} friends of {RED}{str(steamid)[:7]}{RESET}{hyperlink} skipping them           | {index+1:3d}/{len(steamids)}  {GREEN}{timer[1]:3.2f}{RESET}s elapsed")
            display.update_header_data({
                'profiles_in_db': display.header_data['profiles_in_db'] + friend_count,
                'profiles_without_friends': display.header_data['profiles_without_friends'] - 1,
                'profiles_with_friends': (display.header_data['profiles_with_friends'] + 1)
            })
            display.render()
        if friend_count <= 10:
            display.add_log(f"Found {GREEN}{friend_count:3d}{RESET} friends of {GREEN}{str(steamid)[:7]}{RESET}{hyperlink} adding them to database | {index+1:3d}/{len(steamids)}  {GREEN}{timer[1]:3.2f}{RESET}s elapsed")
            display.update_header_data({
                'profiles_in_db': display.header_data['profiles_in_db'] + friend_count,
                'profiles_without_friends': display.header_data['profiles_without_friends'] + friend_count - 1,
                'profiles_with_less_than_10_friends': display.header_data['profiles_with_less_than_10_friends'] + 1,
                'profiles_with_friends': (display.header_data['profiles_with_friends'] + 1 if friend_count > 0 else display.header_data['profiles_with_friends'])
            })
            display.render()
            add_friends_to_db(friends)
        
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
    global SUMMARY_RATE_MODIFIER
    try:
        print(f'Pausing for {GREEN}{sleep_time*SUMMARY_RATE_MODIFIER}{RESET} seconds')
        time.sleep(sleep_time*SUMMARY_RATE_MODIFIER)
        url = f'https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/?key={API_KEY}&steamids={steamids}'
        response = requests.get(url)
        if response.status_code == 429:
            print(f'Rate limit reached: {response.status_code}')
            SUMMARY_RATE_MODIFIER *= 2
            data = {
                'timestamp': str(datetime.now()),
                'status_code': response.status_code,
                'headers': dict(response.headers),
                'body': response.text
            }
            with open("steam_api_log.json", "a+") as f:
                json.dump(data, f)
                f.write("\n")
            
            print('Pausing for 3600 seconds')
            for i in range(0, 3600):
                print(f'----------------- {RED}{3600-i}{RESET}s -----------------' , end='\r')
                time.sleep(1)

            response = requests.get(url)
            if response.status_code == 429:
                print('Rate limit reached again, exiting')
                print('Pausing for 24 hours seconds')
                for i in range(0, S_DAY):
                    if msvcrt.kbhit():
                        if msvcrt.getch() == b'q':
                            client.close()
                            return
                    #seconds = i%S_MINUTE
                    #minutes = seconds%S_HOUR
                    #hour = minutes%S_DAY
                    #print(f'----------------- {RED}{hour}h {minutes}m {seconds}s{RESET}S -----------------' , end='\r')
                    print(f'----------------- {RED}{S_DAY-i}{RESET}s remainig HOLD Q to end program-----------------' , end='\r')
                    time.sleep(1)
                    
    except Exception as e:
        print(f'Error: {e}')
        return

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
                scan_queue.discard(steamid)
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
            scan_queue.discard(profile['steamid'])
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

    display = Display(DisplayType.BOTTOM_UP)

    client = MongoClient('localhost', 27017)
    db = client['steam_db']
    collection = db['profiles']
    batch_size = 20

    profiles_without_friends_lists = QueueGenerators.ProfilesWithoutFriendsList(db, collection)
    scan_queue.update(int(profile) for profile in profiles_without_friends_lists)

    if len(scan_queue) == 0:
        scan_queue.add(args.steamid)    


    while scan_queue:

        display.update_header_data({
            'queue_length': len(scan_queue),
            'profiles_in_db': collection.estimated_document_count(),
            'profiles_with_friends': collection.count_documents({'friends': {'$exists': True}}),
            'profiles_without_friends': collection.count_documents({'friends': {'$exists': False}}),
            'profiles_with_less_than_10_friends': collection.count_documents({'friends_count': {'$lt': 10}})
        })
        display.render()
        beforeTime = time.time()

        if scan_profiles(list(islice(scan_queue, batch_size)), display):
            if quiting:
                break

            profiles_without_friends_lists = QueueGenerators.ProfilesWithoutFriendsList(db, collection)
            if(len(profiles_without_friends_lists) > 0):
                scan_queue.update(int(profile) for profile in profiles_without_friends_lists)
            else:
                break

        deltatime = time.time() - beforeTime
        requestsPerDay = (batch_size/deltatime)*S_DAY

        if requestsPerDay > 100000-5000:
            sleep_time += sleep_time*0.3
        else:
            sleep_time -= sleep_time*0.1

        #print_status_update(deltatime, deltaQueue, deltaStored, afterStored, len(scan_queue),requestsPerDay)
    
    print(f'Scan ended with {len(scan_queue)} profiles in queue')
    print('Exiting')
    client.close()