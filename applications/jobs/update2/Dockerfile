FROM python:3.9-alpine

RUN pip install pymongo

COPY update2.py update2.py
RUN chmod +x update2.py

ENTRYPOINT ["python3.9","update2.py"]