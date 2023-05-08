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
    assert client.bucket_exists("onions")
    return client

def get_documents(client, year, month, day):
    for document in client.list_objects(bucket_name="onions", prefix=f"{year}/{month}/{day}/htmls/"):
        # print(day, month, year, document.object_name.split("/")[-1][:-5])
        yield document.object_name.split("/")[-1][:-5], document.object_name
        """
        client.fget_object(bucket_name="onions",
                           object_name=document.object_name,
                           file_path=f"data/{year}/{month}/{day}/htmls/"+document.object_name.split("/")[-1])
        """

def daterange(start_date, end_date):
    for n in range(int((end_date - start_date).days)):
        yield start_date + timedelta(n)



def get_onion(client, onion):
    db = client["darkweb"] 
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

def update_onion(client, onion, entry):
    db = client["darkweb"] 
    collection = db["onions"] 
    r = collection.update_one({"onion":onion}, {"$set": entry}, upsert=True) # insert the new entry


def download():
    return True

def get_topic():
    return "results_onions_farmer"

#####################################################################################################################


client = minio()
start_date = date(2022, 11, 1)
#start_date = date(2023, 1, 24)
today = date.today()
mongo_client = MongoClient("mongodb://mongo.oniondownloader:27017/", replicaSet="rs0") # connect to the MongoDB instance running on localhost

processed_onions = {}
duplicated_onions = []

for single_date in daterange(start_date, today+ timedelta(days=1)):

    print("Downloading data from",single_date.strftime("%d-%m-%Y"), "...")
    
    for onion, path in get_documents(client, single_date.year, single_date.month, single_date.day):

        if onion in processed_onions.keys():
            duplicated_onions.append(processed_onions[onion])
            duplicated_onions.append(path)
        else:
            processed_onions[onion] = path

            # check if onion has been downloaded
            results = get_onion(mongo_client,onion)
            kafka_topic = get_topic() # get the topic of the onion
            source = kafka_topic[8:]
            downloaded = False

            if results is None or results['downloaded'] is False:
                # download onion from HTML
                downloaded = download()
                entry = {
                    "downloaded": downloaded,
                    "download_date": datetime(single_date.year, single_date.month, single_date.day),
                    "onions_farmer": False or source=="onions_farmer" or (results is not None and results['onions_farmer']),
                    "ioc_repositories": False or source=="ioc_repositories" or (results is not None and results['ioc_repositories']),
                    "gateways": False or source=="gateways" or (results is not None and results['gateways']),
                    "code_repositories": False or source=="code_repositories" or (results is not None and results['code_repositories'])
                }

                update_onion(mongo_client,onion,entry)
                
            else:
                if results[source] is not True:  # update with new data source found
                    entry = {
                        source: True
                    }
                    update_onion(mongo_client,onion,entry)
                else:
                    source = False
            
            print(f"{onion} | Seen before: {results!=None} | Downloaded before: {results!=None and results['downloaded']}  | Downloaded now: {downloaded} | Data source: {source}")

print(f"Processed onions: {len(processed_onions)}")
print(f"Duplicated onions: {len(duplicated_onions)}")
for duplicated in duplicated_onions:
    print(f"- {duplicated}")

mongo_client.close()