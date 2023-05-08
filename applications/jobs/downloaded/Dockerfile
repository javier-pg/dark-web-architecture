FROM python:3.9-alpine

RUN pip install minio pymongo

COPY downloaded.py downloaded.py
RUN chmod +x downloaded.py

ENTRYPOINT ["python3.9","downloaded.py"]