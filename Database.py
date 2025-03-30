from CustomTypes import MongoDBCollections
from Display import Display
import time
import QueueGenerators
from pymongo import MongoClient




class Steam_MongoDB:
    def __init__(self, db_address: str, db_port: int, display: Display):
        """
        Initialize the MongoDB connection."
        "param db_name: The name of the database to connect to.""
        "param db_collection: The collection to use within the database."
        """

        self.db_address = db_address
        self.db_port = db_port
        self.display = display

        self.db_name = 'steam_db'
        self.db_client = None
        self.db = None
        self.collection = None
        
        self.__connect()
        self.select_collection('profiles')


    def __connect(self):
        """
        Connect to the MongoDB database.
        :return: True if the connection was successful, False otherwise.
        """
        print(f"Connecting to MongoDB database: {self.db_name}")
        try:
            client = MongoClient(self.db_address, self.db_port)
            self.db_client = client
            self.db = self.db_client[self.db_name]
            print(f"Connected to MongoDB database: {self.db_name}")
        except Exception as e:
            print(f"Error connecting to MongoDB database: {self.db_name}, Error: {e}")

    def select_collection(self, collection: str):
        """
        Select a collection within the database.
        :param collection: The collection to select.
        """
        print(f"Selecting collection: {collection} in database: {self.db_name}")
        try:
            self.collection = self.db[collection]
            print(f"Selected collection: {self.collection}")
        except Exception as e:
            print(f"Error selecting collection: {collection}, Error: {e}")

    def get_profiles_without_friendslist(self)  -> set[str]:
        """
        Get all profiles without a friends list from the database.
        :return: List of profiles without a friends list.
        """
        
        try:
            profiles = set(profile for profile in QueueGenerators.ProfilesWithoutFriendsList(self.db, self.collection))
            return profiles
        except Exception as e:
            print(f"Error fetching profiles without friends list: {e}")
            return set()

    def add_friends_to_db(self, friends: list):
        for friend in friends:
            if not self.collection.find_one({'steamid': friend['steamid']}):
                self.collection.insert_one({
                    'steamid': friend['steamid'],
                    'time_added_unix': int(time.time()),
                    })

    def update_profile(self, steamid: str, friends: list):
        """
        Update a profile in the database.
        :param steamid: The steamid of the profile to update.
        :param friends: The friends list to update.
        """
        try:
            self.collection.update_one(
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
        except Exception as e:
            print(f"Error updating profile {steamid}: {e}")

    def update_header_data(self, queue_length:int = 0, profiles_in_db:int = 0, profiles_with_friends:int = 0, profiles_without_friends:int = 0, profiles_with_less_than_10_friends:int = 0):
        """
        Update the header data in the display.
        :param display: The display object to update.
        """

        header_queue_length   = self.display.header_data.get('queue_length', queue_length)
        queue_length          = queue_length if header_queue_length in (None, 0) else header_queue_length

        header_profiles_in_db = self.display.header_data.get('profiles_in_db', profiles_in_db)
        profiles_in_db        = self.collection.estimated_document_count() if header_profiles_in_db in (None, 0) else header_profiles_in_db + profiles_in_db

        header_profiles_with_friends    = self.display.header_data.get('profiles_with_friends', profiles_with_friends)
        profiles_with_friends           = self.collection.count_documents({'friends': {'$exists': True}}) if header_profiles_with_friends in (None, 0) else header_profiles_with_friends + profiles_with_friends

        header_profiles_without_friends = self.display.header_data.get('profiles_without_friends', profiles_without_friends)
        profiles_without_friends        = self.collection.count_documents({'friends': {'$exists': False}}) if header_profiles_without_friends in (None, 0) else header_profiles_without_friends + profiles_without_friends

        header_profiles_with_less_than_10_friends = self.display.header_data.get('profiles_with_less_than_10_friends', profiles_with_less_than_10_friends)
        profiles_with_less_than_10_friends        = self.collection.count_documents({'friends_count': {'$lt': 10}}) if header_profiles_with_less_than_10_friends in (None, 0) else header_profiles_with_less_than_10_friends + profiles_with_less_than_10_friends

        self.display.update_header_data({
            'queue_length': queue_length,
            'profiles_in_db': profiles_in_db,
            'profiles_with_friends': profiles_with_friends,
            'profiles_without_friends': profiles_without_friends,
            'profiles_with_less_than_10_friends': profiles_with_less_than_10_friends 
        })


    def close(self):
        # Placeholder for closing the MongoDB connection
        print(f"Closing connection to MongoDB database: {self.db_name}")
        if self.db_client:
            self.db_client.close()
            print(f"Connection to MongoDB database: {self.db_name} closed")
        else:
            print(f"No connection to close for MongoDB database: {self.db_name}")