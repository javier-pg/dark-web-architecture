FROM python:3.9-alpine

# Dependencies
RUN pip3.9 install kafka-python requests pysocks minio bs4

COPY processing.py /home/processing.py

RUN chmod +x /home/processing.py

ENTRYPOINT ["python3.9","/home/processing.py"]