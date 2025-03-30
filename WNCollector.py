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
from API import API
from itertools import islice
from Display import Display, DisplayType
from Database import Steam_MongoDB
import QueueGenerators
import argparse
import msvcrt
import time

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
RATE_LIMIT = (S_DAY/(100000-91000)) # 8100 requests per day
sleep_time = RATE_LIMIT
scan_queue = set()


def scan_profiles(steamids: list[int], display: Display, apiHandler: API, db: Steam_MongoDB) -> bool:
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
            
        friends, responseSuccess = apiHandler.get_friends(str(steamid))
        
        if not responseSuccess:
            display.add_log(f"Error: {steamid} is not a valid steamid")
            continue
        
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
            db.add_friends_to_db(friends)
        
        db.collection.update_one(
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


if __name__ == '__main__':

    display = Display(DisplayType.BOTTOM_UP)

    db = Steam_MongoDB('localhost', 27017)
    batch_size = 20

    apiHandler = API(API_KEY)

    scan_queue = db.get_profiles_without_friendslist()
    
    if args.steamid:
        if args.steamid not in scan_queue:
            scan_queue.add(args.steamid)
            display.add_log(f"Adding {args.steamid} to scan queue")
        else:
            display.add_log(f"{args.steamid} already in scan queue")

    while scan_queue:

        display.update_header_data({
            'queue_length': len(scan_queue),
            'profiles_in_db': db.collection.estimated_document_count(),
            'profiles_with_friends': db.collection.count_documents({'friends': {'$exists': True}}),
            'profiles_without_friends': db.collection.count_documents({'friends': {'$exists': False}}),
            'profiles_with_less_than_10_friends': db.collection.count_documents({'friends_count': {'$lt': 10}})
        })
        
        display.render()
        beforeTime = time.time()

        if scan_profiles(list(islice(scan_queue, batch_size)), display, apiHandler):
            if quiting:
                break

        profiles_without_friends_lists = db.get_profiles_without_friendslist()
        if len(profiles_without_friends_lists) == 0:
            display.add_log(f'No profiles without friends list found')
            break
        if(len(profiles_without_friends_lists) > 0):
            scan_queue.update(int(profile) for profile in profiles_without_friends_lists)

        deltatime = time.time() - beforeTime
        requestsPerDay = (batch_size/deltatime)*S_DAY

        if requestsPerDay > 100000-5000:
            sleep_time += sleep_time*0.3
        else:
            sleep_time -= sleep_time*0.1


    display.add_log(f'Scan ended with {len(scan_queue)} profiles in queue')
    display.add_log('Exiting')
    display.render()
    
    db.close()