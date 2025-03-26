from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection

def ProfilesWithoutFriendsList(db: Database , collection: Collection) -> list:
    """
    Update friends lists gathering queue of profiles in the database
      that have not had their friends list checked, without crawling friends list.
      queue is in the queues collection.
    :param collection: pymongo.collection.Collection
    :param db: pymongo.database.Database
    """

    # Get the profiles that have not had their friends list checked
    profiles_collection = collection.find({
        '$and': [
            {
                'friends': {'$exists': False}
            },
            {
                '$or': [
                    {
                        'publicProfile': {'$exists': False}
                    },
                    {
                        'publicProfile': True
                    }
                ]
            }
        ]
    })
    friends = list(profile['steamid'] for profile in profiles_collection)

    return friends
