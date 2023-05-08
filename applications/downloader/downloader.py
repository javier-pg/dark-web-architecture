from kafka import KafkaConsumer
from kafka import TopicPartition, OffsetAndMetadata
from json import loads
import requests
import subprocess
from threading import Timer
from minio import Minio
from minio.error import S3Error
import os
import io
import datetime
import time
import logging
from pymongo import MongoClient

# logging.basicConfig(level=logging.INFO)
HTML_TIMEOUT = 60
SCAN_TIMEOUT = HTML_TIMEOUT
HTML_RETRIES = 3
SCAN_RETRIES = 3
MAX_PROCESSING_TIME = 1000*HTML_RETRIES*HTML_TIMEOUT
#MAX_PROCESSING_TIME = 1000*(HTML_RETRIES*HTML_TIMEOUT+SCAN_RETRIES*SCAN_TIMEOUT)

KAFKA_MAX_POLL_RECORDS = 5
KAFKA_MAX_POLL_INTERVAL_MS = int(KAFKA_MAX_POLL_RECORDS * MAX_PROCESSING_TIME * 0.5)
KAFKA_SESSION_TIMEOUT_MS = 10000
KAFKA_REQUEST_TIMEOUT_MS = 305000


############################ KAFKA ############################

def kafka():
    try:
        consumer = KafkaConsumer(
            bootstrap_servers=['kafka.kafka.svc.cluster.local:9092'],
            auto_offset_reset='earliest',
            group_id='downloader',
            enable_auto_commit=False,
            session_timeout_ms=KAFKA_SESSION_TIMEOUT_MS,
            request_timeout_ms=KAFKA_REQUEST_TIMEOUT_MS,
            max_poll_records=KAFKA_MAX_POLL_RECORDS,
            max_poll_interval_ms=KAFKA_MAX_POLL_INTERVAL_MS,
            )
        consumer.subscribe(['crawlab_test.results_onions_farmer', 'crawlab_test.results_gateways', 'crawlab_test.results_code_repositories', 'crawlab_test.results_ioc_repositories'])
        print("Kafka configured!", flush=True)
    except Exception as e:
        print(f"Error ({e})", end=" ")
        return False
    return consumer

def get_onions(consumer):
    for message in consumer:
        try:
            print("---")
            m = loads(message.value.decode('utf-8'))
            onion = loads(m).get('onion',False)
            
            if onion is False:
                print(f"New record {message} does not have the 'onion' field")
            else:
                print(f"{datetime.datetime.now()} [onion] {onion} [partition] {message.partition} [offset] {message.offset}")
                yield onion, message.topic, TopicPartition(message.topic,message.partition), OffsetAndMetadata(message.offset+1, message.timestamp)
        except Exception as error:
            print(f"Decoding error of {message} ({error})")
            consumer.commit({tp:om})
            continue

############################ MINIO ############################
def minio():
    try:
        client = Minio(
            endpoint="minio.minio.svc.cluster.local:9000",
            secure=False,
            access_key=os.environ['MINIO_ONION_ACCESS_KEY'],
            secret_key=os.environ['MINIO_ONION_SECRET_KEY']
        )
        print("MinIO configured!")
    except S3Error as exc:
        print("error occurred.", exc, flush=True)
        return False
        
    # Make 'asiatrip' bucket if not exist.
    assert client.bucket_exists("onions")
    return client

############################ HTML ############################
def get_html(onion):
    http_onion = "".join(("http://", onion))
    print("Downloading HTML...", end=" ", flush=True)
    html=False
    attempts = 0
    while (html is False and attempts < HTML_RETRIES):
        print(f"[Attempt {attempts}]", end=" ", flush=True) 
        try: 
            with requests.session() as session:
                session.proxies = {'http': 'socks5h://torproxy.torproxy.svc.cluster.local:9050', 'https': 'socks5h://torproxy.torproxy.svc.cluster.local:9050'}
                html = session.get(http_onion, timeout=HTML_TIMEOUT) # Prints the contents of the page
                html.encoding = 'utf-8'
        except Exception as e:
            print(f"ERROR ({e})", end="; ", flush=True)
            time.sleep(2*attempts)
            attempts = attempts + 1
    
    if html is False:
        print(f"After {attempts} attempts, skipping {onion}", flush=True)
    else:
        print("OK", end="; ", flush=True)

    return html

def save_html(client, onion, html):
    print("Saving HTML...", end=" ", flush=True)
    bhtml = html.content
    buffer = io.BytesIO(bhtml)
    today = datetime.date.today()
    try:
        client.put_object(
            bucket_name="onions",
            object_name=f"/{today.year}/{today.month}/{today.day}/htmls/{onion}.html",
            data=buffer,
            length=len(bhtml),
            content_type='application/html'
        )
        print("OK;", flush=True)
        return True
    except S3Error as exc:
        print(f"ERROR ({exc})", flush=True)
        return False

############################ SCAN ############################
def handle_timeout(process):
    try:
        process.kill()
    except:
        pass

def run_onionscan(onion):
    print("Scanning...", end=" ", flush=True)
    attempts = 0
    stdout = b''
    while (stdout == b'' and attempts < SCAN_RETRIES):
        try: 
            print(f"[Attempt {attempts}]", end=" ", flush=True)

            # fire up onionscan
            process = subprocess.Popen(["/go/bin/onionscan", "--torProxyAddress", "torproxy.torproxy.svc.cluster.local:9050", "--depth", "0", "--webport", "0", "--jsonReport", onion],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            
            # start the timer and let it run till timeout minutes
            process_timer = Timer(SCAN_TIMEOUT,handle_timeout,args=[process])
            process_timer.start()

            # wait for the onion scan results
            stdout = process.communicate()[0]
            
            if stdout == b'':
                print(f"OnionScan empty answer", end="; ", flush=True)

            # we have received valid results so we can kill the timer
            if process_timer.is_alive():
                process_timer.cancel()

        except Exception as e:
            print(f"ERROR ({e})", end="; ", flush=True)
            stdout = b''
        
        attempts = attempts+1

    if stdout == b'':
        print(f"After {attempts} attempts, skipping scan of {onion}", flush=True)
        return False
    else:
        print("OK", end="; ", flush=True)
        return stdout

def save_scan(client, onion, json):
    print("Saving scan...", end=" ", flush=True)
    buffer = io.BytesIO(json)
    today = datetime.date.today()
    try:
        client.put_object(
            bucket_name="onions",
            object_name=f"/{today.year}/{today.month}/{today.day}/scans/{onion}.json",
            data=buffer,
            length=len(json),
            content_type='application/json'
    )
    except S3Error as exc:
        print(f"ERROR ({exc})", end="; ", flush=True)

    print("Finished!", flush=True)


############################ MONGO ############################

def mongo():
    client = MongoClient("mongodb://mongo.oniondownloader:27017/", replicaSet="rs0")
    print("MongoDB configured!")
    return client

def get_info(client, onion):
    db = client["darkweb"] # select the "mydatabase" database
    collection = db["onions"] # select the "mycollection" collection
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

def update_onion(client, onion, entry):
    db = client["darkweb"] 
    collection = db["onions"] 
    r = collection.update_one({"onion":onion}, {"$set": entry}, upsert=True)


minio = minio()
consumer = kafka()
mongo = mongo()

if consumer is not False:
    for onion, kafka_topic, tp, om in get_onions(consumer):
        
        #print(f"{onion} ", end="-> ", flush=True)
        onion_info = get_info(mongo, onion)
        source = kafka_topic[21:]
        downloaded = False

        # need to download HTML and save new associated entry in Mongo
        if onion_info is None or onion_info['downloaded'] is False:
            
            # get HTML
            html = get_html(onion)
            if html is not False:
                downloaded = save_html(minio, onion, html)
            else:
                downloaded = False

            now = datetime.datetime.now()
            timestamp = datetime.datetime.timestamp(now)

            entry = {
                "downloaded": downloaded,
                "download_date": now,
                "timestamp": timestamp,
                "onions_farmer": False or source=="onions_farmer" or (onion_info is not None and onion_info['onions_farmer']),
                "ioc_repositories": False or source=="ioc_repositories" or (onion_info is not None and onion_info['ioc_repositories']),
                "gateways": False or source=="gateways" or (onion_info is not None and onion_info['gateways']),
                "code_repositories": False or source=="code_repositories" or (onion_info is not None and onion_info['code_repositories'])
            }
            update_onion(mongo,onion,entry)

        else:
            if onion_info[source] is not True:  # update with new data source found
                entry = {
                    source: True
                }
                update_onion(mongo,onion,entry)
            else:
                # should never happen (no duplicates in a particular type of source)
                source = False       
        
        print(f"Seen before: {onion_info!=None}; Downloaded before: {onion_info!=None and onion_info['downloaded']}; Downloaded now: {downloaded}; Data source: {source}")
        consumer.commit({tp:om})