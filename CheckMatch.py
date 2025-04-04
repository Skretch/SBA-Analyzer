from API import API
from Database import Steam_MongoDB
from CustomTypes import RequestType
import argparse


##    Intention
# Get the friends of everyone in a lobby
# Check the steam summary with(steam lvl) of all those friends
# Print the number of friends
# Print median steam level of friends
# List number of friends that are banned as count and as a percentage indicate suspicion with color

# ---- Deeper search
# Check the friends list of the friends of everyone in the lobby
# Check the summaries for the friends of friends


#parser = argparse.ArgumentParser(description="Collects Steam Profiles")
#parser.add_argument('--api_key', type=str, help='Steam API key')
#args = parser.parse_args()


def main():
    #apiKey = args.api_key
    print('Enter a SteamID64 like this one 76561197974626949 with only numbers')
    steamid = input("Input: ").strip()
    if len(steamid) != 17:
        print('Steamid must be 17 Characters long')
        return
    steamid = 


    print(steamid)
















































if __name__ == '__main__':
    #api = API()
    main()