import datetime
from pymongo import MongoClient
from datetime import timedelta

def update_timestamp():
    client = MongoClient("mongodb://mongo.oniondownloader:27017/") # connect to the MongoDB instance running on localhost
    db = client["darkweb"] # select the "mydatabase" database
    collection = db["onions"] # select the "mycollection" collection
    
    documents = collection.find() # retrieve all documents from the collection
    for document in documents:
        download_date = document["download_date"]
        timestamp = datetime.datetime.timestamp(download_date - timedelta(hours=1))
        collection.update_one({"onion": document["onion"]}, {"$set": {"timestamp": timestamp}})
        print(download_date, timestamp)
    client.close()

update_timestamp()