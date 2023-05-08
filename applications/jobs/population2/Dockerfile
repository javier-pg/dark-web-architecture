FROM python:3.9-alpine

RUN pip install minio pymongo

COPY auxdownloader2.py auxdownloader2.py
RUN chmod +x auxdownloader2.py

ENTRYPOINT ["python3.9","auxdownloader2.py"]