FROM python:3.9-alpine

RUN pip install minio pymongo

COPY auxdownloader.py auxdownloader.py
RUN chmod +x auxdownloader.py

ENTRYPOINT ["python3.9","auxdownloader.py"]