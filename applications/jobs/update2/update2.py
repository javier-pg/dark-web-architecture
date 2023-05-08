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
            "timestamp": result["timestamp"],
            "onions_farmer": result["onions_farmer"],
            "ioc_repositories": result["ioc_repositories"],
            "gateways": result["gateways"],
            "code_repositories": result["code_repositories"]
        }
        return attributes
    else:
        return None

def insert_onion(client_downloader_mongo,onion,timestamp,collection_name):
    db = client_downloader_mongo["darkweb"] 
    collection = db["onions"] 
    
    print(f"Including not downloaded {onion} ({collection_name}) with the timestamp {timestamp} ({datetime.datetime.fromtimestamp(timestamp)})")

    entry = {
        "downloaded": False,
        "download_date": datetime.datetime.fromtimestamp(timestamp),
        "timestamp": timestamp,
        "onions_farmer": collection_name == "results_onions_farmer",
        "ioc_repositories": collection_name == "results_ioc_repositories",
        "gateways": collection_name  == "results_gateways",
        "code_repositories": collection_name == "results_code_repositories"
    }

    collection.update_one({"onion":onion}, {"$set": entry}, upsert=True)


def update_onion(client_downloader_mongo, onion, crawlab_timestamp, downloader_timestamp, collection_name):
    db = client_downloader_mongo["darkweb"] 
    collection = db["onions"] 

    if crawlab_timestamp > downloader_timestamp:
        timestamp = crawlab_timestamp
    else:
        timestamp = downloader_timestamp

    entry = {
        "downloaded": False,
        "timestamp": timestamp,
        "download_date": datetime.datetime.fromtimestamp(timestamp),
        collection_name[8:]: True
    }

    collection.update_one({"onion":onion}, {"$set": entry}, upsert=False)


def update_downloader_mongo(client_crawlab_mongo, client_downloader_mongo):
    db = client_crawlab_mongo["crawlab_test"] 
    
    for collection_name in ["results_onions_farmer", "results_ioc_repositories", "results_gateways", "results_code_repositories"]:
        collection = db[collection_name]
        documents = collection.find({},{"_id":0, "onion": 1, "timestamp":1}) # retrieve all documents from the collection
        total, never_downloaded, downloaded = 0, 0, 0
        
        for document in documents:
            total += 1
            onion = document["onion"]
            timestamp = document["timestamp"]
            results = get_onion(client_downloader_mongo, onion)
            
            # insert an onion that was not downloaded
            if results is None:
                never_downloaded+=1
                insert_onion(client_downloader_mongo, onion, timestamp, collection_name)
            else:
                downloaded+=1
                update_onion(client_downloader_mongo, onion, timestamp, results["timestamp"], collection_name)

    print(f"From {total} onions, {never_downloaded} are not included in downloader db")
    print(f"From {total} onions, {downloaded} are present in downloader db")

client_crawlab_mongo = MongoClient("mongodb://mongo.crawlab:27017/") 
client_downloader_mongo = MongoClient("mongodb://mongo.oniondownloader:27017/") 
update_downloader_mongo(client_crawlab_mongo, client_downloader_mongo)
client_crawlab_mongo.close()
client_downloader_mongo.close()