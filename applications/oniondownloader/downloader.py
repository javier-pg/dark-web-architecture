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

# logging.basicConfig(level=logging.INFO)
HTML_TIMEOUT = 60
SCAN_TIMEOUT = HTML_TIMEOUT
HTML_RETRIES = 3
SCAN_RETRIES = 3
MAX_PROCESSING_TIME = 1000*(HTML_RETRIES*HTML_TIMEOUT+SCAN_RETRIES*SCAN_TIMEOUT)

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
        consumer.subscribe(['crawlab_test.results_onions_farmer'])
        print("Kafka configured!", flush=True)
    except Exception as e:
        print(f"Error ({e})", end=" ")
        return False
    return consumer

def get_onions(consumer):
    for message in consumer:
        tp=TopicPartition(message.topic,message.partition)
        om = OffsetAndMetadata(message.offset+1, message.timestamp)
        consumer.commit({tp:om})
        try:
            print("---")
            m = loads(message.value.decode('utf-8'))
            onion = loads(m).get('onion',False)
            
            if onion is False:
                print(f"New record {message} does not have the 'onion' field")
            else:
                print(f"{datetime.datetime.now()} [onion] {onion} [partition] {message.partition} [offset] {message.offset}")
                yield onion
        except Exception as error:
            print(f"Decoding error of {message} ({error})")
            continue

############################ MINIO ############################
def minio():
    try:
        client = Minio(
            endpoint=os.environ['MINIO_ENDPOINT'],
            secure=False,
            access_key=os.environ['MINIO_AKEY'],
            secret_key=os.environ['MINIO_SKEY']
        )
        print("MinIO configured!")
    except S3Error as exc:
        print("error occurred.", exc, flush=True)
    
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
        except Exception as e:
            print(f"ERROR ({e})", end="; ", flush=True)
            time.sleep(2.0)
            attempts = attempts + 1
    
    if html is False:
        print(f"After {attempts} attempts, skipping {onion}", flush=True)
    else:
        print("OK", end="; ", flush=True)

    return html

def save_html(client, onion, html):
    print("Saving HTML...", end=" ", flush=True)
    bhtml = html.text.encode('utf-8')
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
        print("OK", end="; ", flush=True)
    except S3Error as exc:
        print(f"ERROR ({exc})", end="; ", flush=True)

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
    

minio = minio()
consumer = kafka()

if consumer is not False:
    for onion in get_onions(consumer):
        
        print(f"{onion} ", end="-> ", flush=True)

        # get HTML
        html = get_html(onion)
        if html is not False:
            save_html(minio, onion, html)
            # get SCANNING
            scan = run_onionscan(onion)
            if scan is not False:
                save_scan(minio, onion, scan)