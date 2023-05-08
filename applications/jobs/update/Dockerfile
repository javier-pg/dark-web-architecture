FROM python:3.9-alpine

RUN pip install pymongo

COPY update.py update.py
RUN chmod +x update.py

ENTRYPOINT ["python3.9","update.py"]