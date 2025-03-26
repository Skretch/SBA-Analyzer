from datetime import datetime
import requests
import json
import time

DAY_IN_SECONDS = 60*60*24


class API:
    def __init__(self):
        self.dailyRateLimit = 100,000
        self.rateLimit = 100,000/DAY_IN_SECONDS
        self.rateAdjustment = 1.1
        self.rateLimits = 0
        pass


    def getFriends(self, API_KEY, steamid) -> list:
        try:
            time.sleep(self.rateLimit * self.rateAdjustment)
            url = f'https://api.steampowered.com/ISteamUser/GetFriendList/v1/?key={API_KEY}&steamid={steamid}&relationship=friend'
            response = requests.get(url)
            response.raise_for_status()
            self.handleResponseCode(response.status_code)
        
        except requests.exceptions.RequestException as e:
            with open("steam_api_log.json", "a+") as f:
                json.dump({"timestamp": str(datetime.now()), "error": str(e)}, f)
                f.write("\n")        
        
        return response.json()['response']['players']

    def batchedSummaries(self, url, steamids):
        pass

    def handleResponseCode(self, status_code):
        if status_code == 200:
            return
        elif status_code == 429:
            print(f"Rate limit exceeded: {status_code}")
            print("Pausing for 20 seconds")
            self.rateAdjustment *= 2
            time.sleep(20)
            return
        elif status_code == 503:
            print(f"Service unavailable: {status_code}")
            return
        elif status_code == 401:
            print(f"Unauthorized: {status_code}")
            return
        else:
            print(f"Unknown error: {status_code}")
            return
