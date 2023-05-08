from minio import Minio
from minio.error import S3Error
import os
import datetime
from datetime import date, timedelta
from datetime import datetime
from pymongo import MongoClient

def minio():
    try:
        client = Minio(
            endpoint="minio.minio:9000",
            secure=False,
            access_key="topic-modeling",
            secret_key="hP1S!krT783vD?_yc!fb"
        )
        print("MinIO configured!")
        return client
    except S3Error as exc:
        print("error occurred.", exc)
        return False

def get_documents(client, year, month, day):
    for document in client.list_objects(bucket_name="onions", prefix=f"{year}/{month}/{day}/htmls/"):
        # print(day, month, year, document.object_name.split("/")[-1][:-5])
        yield document.object_name.split("/")[-1][:-5], document.object_name

def daterange(start_date, end_date):
    for n in range(int((end_date - start_date).days)):
        yield start_date + timedelta(n)
    

def update_downloader_mongo(client_downloader_mongo, downloaded_onions):
    db = client_downloader_mongo["darkweb"] 
    collection = db["onions"] 
    documents = collection.find() # retrieve all documents from the collection
    
    for document in documents:
        onion = document["onion"]
        collection.update_one({"onion":onion},{"$set": {"downloaded":onion in downloaded_onions}}, upsert=False)

#####################################################################################################################


client = minio()
start_date = date(2022, 11, 1)
today = date.today()
mongo_client = MongoClient("mongodb://mongo.oniondownloader:27017/", replicaSet="rs0") # connect to the MongoDB instance running on localhost

downloaded = []

for single_date in daterange(start_date, today+ timedelta(days=1)):
    print("Downloading data from",single_date.strftime("%d-%m-%Y"), "...")
    for onion, path in get_documents(client, single_date.year, single_date.month, single_date.day):
        downloaded.append(onion)

update_downloader_mongo(mongo_client, downloaded)
mongo_client.close()