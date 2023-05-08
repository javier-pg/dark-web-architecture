FROM python:3.9-alpine

RUN pip install pymongo minio

COPY coherence.py coherence.py
RUN chmod +x coherence.py

ENTRYPOINT ["python3.9","coherence.py"]