from enum import Enum



class RequestType(Enum):
    GET_FRIEND_LIST = 'GetFriendList'
    GET_PLAYER_SUMMARIES = 'GetPlayerSummaries'
    GET_PLAYER_BAN_LIST = 'GetPlayerBanList'
    GET_PLAYER_ACHIEVEMENTS = 'GetPlayerAchievements'
    GET_PLAYER_RECENT_GAMES = 'GetRecentlyPlayedGames'
    GET_PLAYER_OWNED_GAMES = 'GetOwnedGames'
    GET_PLAYER_BADGES = 'GetBadges'
    GET_PLAYER_LEVEL = 'GetSteamLevel'
    GET_PLAYER_PROFILE = 'GetPlayerProfile'
    GET_PLAYER_INVENTORY = 'GetPlayerInventory'

class MongoDBCollections(Enum):
    PROFILES = 'profiles'