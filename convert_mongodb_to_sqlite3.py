from pymongo import MongoClient
import sqlite3

# MongoDB connection
client = MongoClient("mongodb://localhost:27017/")
db = client["steam_db"]
collection = db["profiles"]

# SQLite connection
sqlite_conn = sqlite3.connect("steam_db.db")
sqlite_cursor = sqlite_conn.cursor()

# Create tables if they don't exist
sqlite_cursor.execute("""CREATE TABLE IF NOT EXISTS profiles 
                      (steamid INTEGER PRIMARY KEY, 
                      time_added_unix INTEGER, 
                      friends_count INTEGER, 
                      public_friends_list INTEGER,  
                      scan_time_unix INTEGER, 
                      profile_state INTEGER, 
                      public_profile INTEGER, 
                      persona_name TEXT,
                      persona_state INTEGER,
                      persona_state_flags INTEGER,
                      primary_clan_id INTEGER,
                      real_name TEXT,
                      account_creation_time_unix INTEGER)""")
sqlite_cursor.execute("""CREATE TABLE IF NOT EXISTS friend_pairs 
                      (a_steamid INTEGER, 
                      b_steamid INTEGER, 
                      friends_since_unixtime INTEGER,
                      PRIMARY KEY (a_steamid, b_steamid))""")
sqlite_conn.commit()

# Process each profile and insert directly into SQLite
for profile in collection.find():
    # Extract steamid (required field)
    try:
        steamid = int(profile["steamid"])
    except ValueError:
        continue
    
    # Insert into friend_pairs table
    if 'friends' in profile and profile['friends']:
        for friend in profile['friends']:
            friend_id = int(friend['steamid'])
            friend_a, friend_b = (steamid, friend_id) if steamid > friend_id else (friend_id, steamid)
            friend_data = (
                friend_a,
                friend_b,
                int(friend['friend_since'])
            )
            sqlite_cursor.execute(
                "INSERT OR IGNORE INTO friend_pairs (a_steamid, b_steamid, friends_since_unixtime) VALUES (?, ?, ?)",
                friend_data
            )
    
    # Build profile data with only existing fields
    profile_data = {
        'steamid': steamid,
        'time_added_unix': None,
        'friends_count': None,
        'public_friends_list': None,
        'scan_time_unix': None,
        'profile_state': None,
        'public_profile': None,
        'persona_name': None,
        'persona_state': None,
        'persona_state_flags': None,
        'primary_clan_id': None,
        'real_name': None,
        'account_creation_time_unix': None
    }
    
    # Check and set each field if it exists
    if 'time_added_unix' in profile and profile['time_added_unix']:
        profile_data['time_added_unix'] = int(profile['time_added_unix'])
    if 'friends_count' in profile and profile['friends_count']:
        profile_data['friends_count'] = int(profile['friends_count'])
    if 'publicFriendsList' in profile and profile['publicFriendsList'] is not None:
        profile_data['public_friends_list'] = int(profile['publicFriendsList'])
    if 'scanTime' in profile and profile['scanTime']:
        if 'profile' in profile['scanTime']:
            profile_data['scan_time_unix'] = int(profile['scanTime']['profile'])
    if 'profilestate' in profile and profile['profilestate']:
        profile_data['profile_state'] = int(profile['profilestate'])
    if 'publicProfile' in profile and profile['publicProfile'] is not None:
        profile_data['public_profile'] = int(profile['publicProfile'])
    if 'personaname' in profile and profile['personaname']:
        profile_data['persona_name'] = profile['personaname']
    if 'personastate' in profile and profile['personastate'] is not None:
        profile_data['persona_state'] = int(profile['personastate'])
    if 'personastateflags' in profile and profile['personastateflags'] is not None:
        profile_data['persona_state_flags'] = int(profile['personastateflags'])
    if 'primaryclanid' in profile and profile['primaryclanid']:
        profile_data['primary_clan_id'] = int(profile['primaryclanid'])
    if 'realname' in profile and profile['realname']:
        profile_data['real_name'] = profile['realname']
    if 'timecreated' in profile and profile['timecreated']:
        profile_data['account_creation_time_unix'] = int(profile['timecreated'])
    
    # Insert into profiles table
    sqlite_cursor.execute(
        """INSERT OR IGNORE INTO profiles 
        (steamid, time_added_unix, friends_count, public_friends_list, scan_time_unix, 
        profile_state, public_profile, persona_name, persona_state, persona_state_flags, 
        primary_clan_id, real_name, account_creation_time_unix) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            profile_data['steamid'],
            profile_data['time_added_unix'],
            profile_data['friends_count'],
            profile_data['public_friends_list'],
            profile_data['scan_time_unix'],
            profile_data['profile_state'],
            profile_data['public_profile'],
            profile_data['persona_name'],
            profile_data['persona_state'],
            profile_data['persona_state_flags'],
            profile_data['primary_clan_id'],
            profile_data['real_name'],
            profile_data['account_creation_time_unix']
        )
    )

# Commit changes and close connection
sqlite_conn.commit()
sqlite_conn.close()