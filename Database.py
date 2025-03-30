from CustomTypes import MongoDBCollections
import time
import QueueGenerators
from pymongo import MongoClient




class Steam_MongoDB:
    def __init__(self, db_address: str, db_port: int):
        """
        Initialize the MongoDB connection."
        "param db_name: The name of the database to connect to.""
        "param db_collection: The collection to use within the database."
        """
        
        self.db_address = db_address
        self.db_port = db_port

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

    def select_collection(self, collection: MongoDBCollections):
        """
        Select a collection within the database.
        :param collection: The collection to select.
        """
        print(f"Selecting collection: {collection.value} in database: {self.db_name}")
        try:
            self.collection = self.db[collection.value]
            print(f"Selected collection: {self.collection}")
        except Exception as e:
            print(f"Error selecting collection: {collection.value}, Error: {e}")

    def get_profiles_without_friendslist(self)  -> set[str]:
        """
        Get all profiles without a friends list from the database.
        :return: List of profiles without a friends list.
        """
        print(f"Fetching profiles without friends list from collection: {self.collection}")
        
        try:
            return set(profile for profile in QueueGenerators.ProfilesWithoutFriendsList(self.db, self.collection))
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



    def close(self):
        # Placeholder for closing the MongoDB connection
        print(f"Closing connection to MongoDB database: {self.db_name}")
        if self.db_client:
            self.db_client.close()
            print(f"Connection to MongoDB database: {self.db_name} closed")
        else:
            print(f"No connection to close for MongoDB database: {self.db_name}")