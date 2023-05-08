import datetime
from pymongo import MongoClient
from datetime import timedelta


def update_onion(client_downloader_mongo, onions):
    db = client_downloader_mongo["darkweb"] 
    collection = db["onions"] 

    for onion, first_identification in onions.items():
        entry = {
            "first_identification": first_identification
        }
        collection.update_one({"onion":onion}, {"$set": entry}, upsert=False)


def update_downloader_mongo(client_crawlab_mongo, client_downloader_mongo):
    db = client_crawlab_mongo["crawlab_test"]

    onions = {}
    
    for collection_name in ["results_onions_farmer", "results_ioc_repositories", "results_gateways", "results_code_repositories"]:
        collection = db[collection_name]
        documents = collection.find({},{"_id":0, "onion": 1, "timestamp":1}) # retrieve all documents from the collection
        for document in documents:
            onion = document["onion"]
            timestamp = document["timestamp"]
            first_identification = onions.get(onion, False)
            if not first_identification:
                onions[onion]= timestamp
            else:
                if timestamp < first_identification:
                    onions[onion] = timestamp

    update_onion(client_downloader_mongo, onions)



client_crawlab_mongo = MongoClient("mongodb://mongo.crawlab:27017/") 
client_downloader_mongo = MongoClient("mongodb://mongo.oniondownloader:27017/") 
update_downloader_mongo(client_crawlab_mongo, client_downloader_mongo)
client_crawlab_mongo.close()
client_downloader_mongo.close()