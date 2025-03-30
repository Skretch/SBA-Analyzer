#Throws a wide net so that it doesn't miss any SBAs

# Collect friends list
# Convert unix timestamp to human readable datetime
# Sort by datetime added
# Check if account is already in database
# If account is in database skip
# If account is not in database add to database

# If friends list is less then 20 accounts add to search list
# If friends list is greater then 20 accounts store in database


from API import API
from itertools import islice
from Display import Display, DisplayType
from Database import Steam_MongoDB
import argparse
import msvcrt

RED = "\033[31m"
GREEN = "\033[32m"
RESET = "\033[0m"

global quiting
quiting = False

parser = argparse.ArgumentParser(description='Collects Steam profiles')
parser.add_argument('--steamid', type=int, help='Steam ID to start from')
parser.add_argument('--api_key', type=str, help='Steam API key')
args = parser.parse_args()

S_DAY = 60*60*24
API_KEY = args.api_key

def main():

    display = Display(DisplayType.BOTTOM_UP)
    db = Steam_MongoDB('localhost', 27017, display)
    scan_queue = db.get_profiles_without_friendslist()
    apiHandler = API(API_KEY)
    batch_size = 20
    
    if args.steamid:
        if args.steamid not in scan_queue:
            scan_queue.add(args.steamid)
            display.add_log(f"Adding {args.steamid} to scan queue")
        else:
            display.add_log(f"{args.steamid} already in scan queue")
    

    main_loop(display, db, apiHandler, batch_size, scan_queue)


    display.add_log('Exiting')
    display.render()
    
    db.close()


def main_loop(display: Display, db: Steam_MongoDB, apiHandler: API, batch_size: int, scan_queue: set[str]):
        
        while scan_queue and not quiting:

            db.update_header_data(queue_length=len(scan_queue))
            display.render()
            if scan_profiles(list(islice(scan_queue, batch_size)), display, apiHandler, db, scan_queue):
                display.add_log(f"Scan ended with {len(scan_queue)} profiles in queue")
                if quiting:
                    break

            profiles_without_friends_lists = db.get_profiles_without_friendslist()
            if len(profiles_without_friends_lists) == 0:
                display.add_log(f'No profiles without friends list found')
                break


def scan_profiles(steamids: list[int], display: Display, apiHandler: API, db: Steam_MongoDB, scan_queue:set[str]) -> bool:

    for index, steamid in enumerate(steamids):
        if quit_check():
            break

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

            display.add_log(f"Found {RED}{friend_count:3d}{RESET} friends of {RED}{str(steamid)[:7]}{RESET}\
                            {hyperlink} skipping them           | {index+1:3d}/{len(steamids)}  \
                            {GREEN}SOMETIME SHOULD BE HERE!{RESET}s elapsed")
            db.update_header_data(profiles_in_db=friend_count, 
                                  profiles_without_friends=-1, 
                                  profiles_with_friends=1)
            display.render()
        
    
        if friend_count <= 10:

            display.add_log(f"Found {GREEN}{friend_count:3d}{RESET} friends of {GREEN}{str(steamid)[:7]}{RESET}\
                            {hyperlink} adding them to database | {index+1:3d}/{len(steamids)}  \
                            {GREEN}SOMETIME SHOULD BE HERE!{RESET}s elapsed")
            db.update_header_data(profiles_in_db=friend_count, 
                                  profiles_without_friends=-1, 
                                  profiles_with_friends=1, 
                                  profiles_with_less_than_10_friends=1)
            display.render()
            db.add_friends_to_db(friends)
        
        db.update_profile(steamid, friends)

    return False

def quit_check():
    global quiting
    if msvcrt.kbhit():
        if msvcrt.getch() == b'q':
            quiting = True
            return True
    return False

if __name__ == '__main__':
    main()
    




