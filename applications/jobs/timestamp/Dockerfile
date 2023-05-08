FROM python:3.9-alpine

RUN pip install pymongo

COPY timestamp.py timestamp.py
RUN chmod +x timestamp.py

ENTRYPOINT ["python3.9","timestamp.py"]