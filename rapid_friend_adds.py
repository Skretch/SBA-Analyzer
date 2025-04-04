import pandas as pd
from pymongo import MongoClient
import time

# MongoDB connection
client = MongoClient("mongodb://localhost:27017/")
db = client["steam_db"]
collection = db["profiles"]


all_profiles_with_friends = collection.find({"friends": {"$exists": True, "$ne":[]}})

all_profiles_with_friends = list(all_profiles_with_friends)

df = pd.DataFrame(all_profiles_with_friends)
df = df.drop(columns=["_id"])


