import datetime
from pymongo import MongoClient
from datetime import timedelta

def get_onion(client_downloader_mongo, onion):
    db = client_downloader_mongo["darkweb"] 
    collection = db["onions"] 
    result = collection.find_one({"onion": onion}) # find the first document that matches the query
    if result:
        attributes = {
            "onion": result["onion"],
            "downloaded": result["downloaded"],
            "download_date": result["download_date"],
            "onions_farmer": result["onions_farmer"],
            "ioc_repositories": result["ioc_repositories"],
            "gateways": result["gateways"],
            "code_repositories": result["code_repositories"]
        }
        return attributes
    else:
        return None

def insert_onion(client_downloader_mongo,onion,timestamp):
    db = client_downloader_mongo["darkweb"] 
    collection = db["onions"] 
    
    print(f"Including {onion} with the timestamp {timestamp} ({datetime.datetime.fromtimestamp(timestamp)})")

    entry = {
        "downloaded": False,
        "download_date": datetime.datetime.fromtimestamp(timestamp),
        "timestamp": timestamp,
        "onions_farmer": True,
        "ioc_repositories": False,
        "gateways": False,
        "code_repositories": False
    }

    collection.update_one({"onion":onion}, {"$set": entry}, upsert=True) 


def update_onion(client_downloader_mongo, onion):
    db = client_downloader_mongo["darkweb"] 
    collection = db["onions"] 

    entry = {
        "onions_farmer": True
    }

    collection.update_one({"onion":onion}, {"$set": entry}, upsert=False) 


def update_downloader_mongo(client_crawlab_mongo, client_downloader_mongo):
    db = client_crawlab_mongo["crawlab_test"] 
    collection = db["results_onions_farmer"] 
    documents = collection.find() # retrieve all documents from the collection
    total, never_downloaded, downloaded = 0, 0, 0
    for document in documents:
        total += 1
        onion = document["onion"]
        timestamp = document["timestamp"]
        results = get_onion(client_downloader_mongo, onion)
        if results is None:
            never_downloaded+=1
            insert_onion(client_downloader_mongo, onion, timestamp)
        else:
            downloaded+=1
            update_onion(client_downloader_mongo, onion)
    print(f"From {total} onions, {never_downloaded} are not included in downloader db")
    print(f"From {total} onions, {downloaded} are present in downloader db")



client_crawlab_mongo = MongoClient("mongodb://mongo.crawlab:27017/") 
client_downloader_mongo = MongoClient("mongodb://mongo.oniondownloader:27017/") 
update_downloader_mongo(client_crawlab_mongo, client_downloader_mongo)
client_crawlab_mongo.close()
client_downloader_mongo.close()