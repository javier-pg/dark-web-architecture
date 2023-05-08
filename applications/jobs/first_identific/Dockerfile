FROM python:3.9-alpine

RUN pip install pymongo

COPY first_identification.py first_identification.py
RUN chmod +x first_identification.py

ENTRYPOINT ["python3.9","first_identification.py"]