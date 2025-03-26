from pymongo import MongoClient
import QueueGenerators
from Display import Display, DisplayType
import random
import time

RED = "\033[31m"
GREEN = "\033[32m"
RESET = "\033[0m"

client = MongoClient('localhost', 27017)
db = client['steam_db']
collection = db['profiles']

def test_Display():
    data = {
        'queue_length': random.randint(20000, 100000),
        'queue_clearing_rate': random.randint(10, 100),
        'queue_clearing_time': random.randint(2000, 10000),
        'profiles_in_db': random.randint(400000, 1000000),
        'profiles_with_friends': random.randint(100000, 200000),
        'profiles_without_friends': random.randint(100000, 200000),
        'profiles_with_less_than_10_friends': random.randint(100000, 200000),
    }
    display = Display(renderMethod=DisplayType.BOTTOM_UP)
    display.update_header_data(data)
    for i in range(30):
        simulate_get_profiles_web_requests(display)
        display.update_header_data({
            'queue_clearing_rate': random.randint(10, 100)
        })
        display.render()
        time.sleep(1)



def simulate_get_profiles_web_requests(display: Display):
    for i in range(20):
        if(i < 10):
            display.add_log(f'Found {GREEN}{random.randint(0,100):3d}{RESET} friends of 7656119{random.randint(1000000000,9999999999)} adding them to database   |   {i}/20  0.96s elapsed')
        display.update_header_data({
            'queue_length': display.header_data['queue_length'] - 1,
        })
        
        display.render()
        time.sleep(1)

test_Display()