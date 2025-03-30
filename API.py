from CustomTypes import RequestType
from datetime import datetime
from enum import Enum
import sys
import requests
import json
import time

SECONDS_IN_DAY = 60*60*24

class API:
    def __init__(self, API_KEY):
        self.API_KEY = API_KEY
        self.dailyRateLimit = 100,000
        self.requestCooldownEnd = time.time()
        self.rate_limit_warnings = {
                'count': 0,
                'warnings': [{
                    'unix_time': time.time(),
                    'request_type': ['GetFriendList', 'GetPlayerSummaries'],
                    'requests_per_minute': 0,   
                }]
            }
    def set_request_cooldown(self, request_type: RequestType):
        """
        Set the request cooldown for the specified request type.
        :param request_type: The type of request to set the cooldown for.
        """
        if self.rate_limit_warnings['count'] == 1:
            self.requestCooldownEnd = self.rate_limit_warnings['warnings'][0]['unix_time'] + 60

        if request_type == RequestType.GET_FRIEND_LIST:
            self.requestCooldownEnd = time.time() + 3
        elif request_type == RequestType.GET_PLAYER_SUMMARIES:
            self.requestCooldownEnd = time.time() + 1

    def get_friends(self, steamid:str ) -> tuple[list, bool]:
        """"
        "Get the friends of a user by their steamid.
        "steamid: str: The steamid of the user to get friends for."
        "return: tuple[list, bool]: A tuple containing a list of friends and a boolean indicating success."
        """
        try:
            if not self.__check_steamid(steamid):
                return ([], False)
            time.sleep(3)  # Initial safe sleep to avoid hitting the rate limit during testing
            url = f'https://api.steampowered.com/ISteamUser/GetFriendList/v1/?key={self.API_KEY}&steamid={steamid}&relationship=friend'
            response = requests.get(url)
            response.raise_for_status()
            self.handle_response_code(response)
            response = response.json()
        
        except requests.exceptions.RequestException as e:
            self.__logg_response_error(response, e)
            sys.exit(1)

        try:
            response = response['friendslist']['friends']

        except KeyError as e:
            self.__logg_response_error(response, e)
        
        return (response, True)

    def __check_steamid(self, steamid:str) -> bool:
        try:
            if not steamid:
                raise ValueError("steamid cannot be None or empty")
            if not isinstance(steamid, str):
                raise TypeError(f"steamid must be a string, got {type(steamid)}")
            if len(steamid) != 17:
                raise ValueError(f"steamid must be 17 characters long, got {len(steamid)}")
            if not steamid.isdigit():
                raise ValueError(f"steamid must be a string of digits, got {steamid}")
            if not steamid.startswith("7656119"):
                raise ValueError(f"steamid must be a 64-bit steamid, got {steamid}")
        
        except ValueError as e:
            print(f"Error: {e}")
            return False
        
        return True

    def batched_summaries(self, url, steamids):
        pass

    def handle_response_code(self, response: requests.Response):
        if response.status_code == 200:
            return
        elif response.status_code == 429:
            print(f"Rate limit exceeded: {response.status_code}")
            self.__logg_response_error(response, "Rate limit exceeded")
            print(f"Exiting")
            sys.exit(1)
        elif response.status_code == 404:
            print(f"Not found: {response.status_code}")
            self.__logg_response_error(response, "Not found")
            print(f"Exiting")
            sys.exit(1)
            return
        elif response.status_code == 503:
            print(f"Service unavailable: {response.status_code}")
            return
        elif response.status_code == 401:
            print(f"Unauthorized: {response.status_code}")
            return
        else:
            print(f"Unknown error: {response.status_code}")
            return
        
    def __logg_response_error(self, response: requests.Response, e: Exception) -> requests.Response:
        data = {
                'timestamp': str(datetime.now()),
                'status_code': response.status_code,
                'headers': dict(response.headers),
                'body': response.text,
                'error': f'{e}'
        }
        print("logging error to steam_api_log.json")
        with open("steam_api_log.json", "a+") as f:
            json.dump(data, f)
            f.write("\n")
        
        return response