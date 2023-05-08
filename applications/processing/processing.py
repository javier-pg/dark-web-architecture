from kafka import KafkaConsumer
from kafka import TopicPartition, OffsetAndMetadata
from json import loads
import json
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
from bs4 import BeautifulSoup


KAFKA_MAX_POLL_RECORDS = 1
KAFKA_MAX_POLL_INTERVAL_MS = 300000    # max time to call poll() again or partition reassignment
KAFKA_SESSION_TIMEOUT_MS = 10000       # max time to send heartbeat
KAFKA_REQUEST_TIMEOUT_MS = 305000      # max time to send ack


############################ KAFKA ############################

def kafka():
    try:
        consumer = KafkaConsumer(
            bootstrap_servers=['kafka.kafka:9092'],
            auto_offset_reset='earliest',
            group_id='processing',
            enable_auto_commit=False,
            session_timeout_ms=KAFKA_SESSION_TIMEOUT_MS,
            request_timeout_ms=KAFKA_REQUEST_TIMEOUT_MS,
            max_poll_records=KAFKA_MAX_POLL_RECORDS,
            max_poll_interval_ms=KAFKA_MAX_POLL_INTERVAL_MS,
            )
        consumer.subscribe(['minio_events'])
        print("Kafka configured!", flush=True)
    except Exception as e:
        print(f"Error ({e})", end=" ")
        return False
    return consumer


def parse_message(message):
    message = json.loads(message.value.decode('utf-8'))
    event_name = message["EventName"]
    path = message["Key"]
    event_time = message["Records"][0]["eventTime"]
    return event_name, path, event_time


def get_new_events(consumer):
    for message in consumer:
        try:
            print("---")
            event_name, path, timestamp = parse_message(message)
            print(f"{timestamp} ({event_name}) [html] {path} [partition] {message.partition} [offset] {message.offset}")
            yield path, message.topic, TopicPartition(message.topic,message.partition), OffsetAndMetadata(message.offset+1, message.timestamp)
        except Exception as error:
            print(f"Decoding error of {message} ({error})")
            consumer.commit({TopicPartition(message.topic,message.partition):OffsetAndMetadata(message.offset+1, message.timestamp)})
            continue


############################ MINIO ############################

def minio():
    try:
        client = Minio(
            endpoint="minio.minio:9000",
            secure=False,
            access_key='processing',
            secret_key=',TkTV3c7:e6#e}HwiD4R'
        )
        print("MinIO configured!")
    except S3Error as exc:
        print("error occurred.", exc, flush=True)
        return False
        
    # Make 'asiatrip' bucket if not exist.
    assert client.bucket_exists("onions")
    return client


def get_html_from_minio(minio_client, object_path):
    try:
        print(f"Getting '{object_path}' from MinIO...", end=" ", flush=True)
        try:
            response = minio_client.get_object("onions", object_path[7:])
            html = response.data.decode("utf-8")
        finally:
            response.close()
            response.release_conn()
        print("OK! Lets process it...", flush=True)
        return html
    except Exception as err:
        print("Error getting object: ", err, flush=True)
        print("Skipping processing it...", flush=True)
        return None

########################## HTML ################################

def get_title(soup):

    if soup.findAll("title"):
        return soup.find("title").string
    else:
        return ''

def get_description(soup):

    if soup.findAll("meta", attrs={"name": "description"}):
        return soup.find("meta", attrs={"name": "description"}).get("content")
    else:
        return ''

########################## MAIN ################################ 

minio = minio()
if minio is not False:
    consumer = kafka()
    if consumer is not False:
        for path, kafka_topic, tp, om in get_new_events(consumer):
            try:
                html = get_html_from_minio(minio, path)

                bs = BeautifulSoup(html, 'html.parser')

                title = get_title(bs)
                if title is None:
                    title = ''
                description = get_description(bs)
                if description is None:
                    description = ''

                print(f"[Title] {title} [Description] {description}")
                consumer.commit({tp:om})
            except Exception as err:
                print(f"[Error] {err}")
                consumer.commit({tp:om})
                continue