from pymongo import MongoClient
import datetime
from datetime import date, timedelta
from minio import Minio
from minio.error import S3Error

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


def daterange(start_date, end_date):
    for n in range(int((end_date - start_date).days)):
        yield start_date + timedelta(n)

def get_documents(client, year, month, day):
    documents = []
    for document in client.list_objects(bucket_name="onions", prefix=f"{year}/{month}/{day}/htmls/"):
        if document is not None:
            documents.append(document.object_name)
    return documents


def get_onions_minio():
    client = minio()
    start_date = date(2022, 11, 1)
    #end_date = date(2023, 2, 16)
    today = date.today()

    onion_addresses = []
    onion_documents = []
    i=0
    for single_date in daterange(start_date, today):
        print("Downloading data from",single_date.strftime("%d-%m-%Y"), "...")
        for i, document in enumerate(get_documents(client, single_date.year, single_date.month, single_date.day)):
            if document[-67:-5] in onion_addresses:
                print(f"Duplicated_onion: {document}")
            else:
                onion_addresses.append(document[-67:-5])
                onion_documents.append(document)
    print(f"Processed onions: {i+1}")
    print(f"Unique onions: {len(onion_addresses)}")
    return onion_addresses, onion_documents


def get_incoherences(onions, minio_documents):
    client = MongoClient("mongodb://mongo.oniondownloader:27017/") # connect to the MongoDB instance running on localhost
    db = client["darkweb"] # select the "mydatabase" database
    collection = db["onions"] # select the "mycollection" collection
    
    saved_onions = []
    mongo_documents = collection.find({"downloaded":True},{"onion":1}) # retrieve all documents from the collection
    for document in mongo_documents:
        onion = document["onion"]
        saved_onions.append(onion)
    client.close()

    for i,onion in enumerate(onions):
        if onion not in saved_onions:
            print(f"The onion {onion} of MinIO is not in MongoDB")
            print(f"The associated document is {minio_documents[i]}")


onion_addresses, onion_documents = get_onions_minio()
get_incoherences(onion_addresses,onion_documents)