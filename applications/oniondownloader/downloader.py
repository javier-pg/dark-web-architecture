from kafka import KafkaConsumer
from json import loads
import requests
import subprocess
from threading import Timer
from minio import Minio
from minio.error import S3Error
import os
import io
import datetime

SCAN_TIMEOUT = 125


############################ KAFKA ############################

def kafka():
    try:
        consumer = KafkaConsumer(
            bootstrap_servers=['kafka.kafka.svc.cluster.local:9092'],
            auto_offset_reset='latest',
            enable_auto_commit=True,
            group_id='breacher',)
            #value_deserializer=lambda x: loads(x.decode('utf-8')))
        consumer.subscribe(['crawlab_test.results_onions_farmer'])
    except Exception as e:
        print(f"Error ({e})")
        return False
    return consumer

def get_onions(consumer):
    for message in consumer:
        try:
            m = loads(message.value.decode('utf-8'))
            onion = m.get('onion',False)
            if onion is False:
                print(f"New record {message} does not have the 'onion' field")
            else:
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
    except S3Error as exc:
        print("error occurred.", exc, flush=True)
    
    # Make 'asiatrip' bucket if not exist.
    assert client.bucket_exists("onions")
    return client

############################ HTML ############################
def get_html(onion):
    onion = "".join(("http://", onion))
    print("Downloading HMTL...", end=" ", flush=True)
    html=False
    try: 
        with requests.session() as session:
            session.proxies = {'http': 'socks5h://torproxy.torproxy.svc.cluster.local:9050', 'https': 'socks5h://torproxy.torproxy.svc.cluster.local:9050'}
            html = session.get(onion, timeout=180) # Prints the contents of the page
    except Exception as e:
        print(f"ERROR ({e})", end="; ", flush=True)
        return html
    print("OK", end="; ") 
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

    try: 
        # fire up onionscan
        process = subprocess.Popen(["/go/bin/onionscan", "--torProxyAddress", "torproxy.torproxy.svc.cluster.local:9050", "--depth", "0", "--webport", "0", "--jsonReport", onion],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        
        # start the timer and let it run till timeout minutes
        process_timer = Timer(SCAN_TIMEOUT,handle_timeout,args=[process])
        process_timer.start()

        # wait for the onion scan results
        stdout = process.communicate()[0]

        # we have received valid results so we can kill the timer
        if process_timer.is_alive():
            process_timer.cancel()

        print("OK", end="; ", flush=True)
        return stdout

    except Exception as e:
        print(f"ERROR ({e})", end="; ", flush=True)
        return False

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