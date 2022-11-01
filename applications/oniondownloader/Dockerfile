FROM golang:rc-stretch

# Dependencies
RUN apt update && \
    apt install wget build-essential libreadline-gplv2-dev libncursesw5-dev libssl-dev libsqlite3-dev tk-dev libgdbm-dev libc6-dev libbz2-dev libffi-dev zlib1g-dev -y && \
    wget https://www.python.org/ftp/python/3.9.4/Python-3.9.4.tgz && \
    tar xzf Python-3.9.4.tgz && \
    cd Python-3.9.4 && \
    ./configure --enable-optimizations && \
    make altinstall && \
    pip3.9 install kafka-python requests pysocks minio

# Install onioscan
RUN go install github.com/s-rah/onionscan@latest
  
COPY validation.go /go/pkg/mod/github.com/s-rah/onionscan\@v0.0.0-20170225171031-da42865bb5b1/utils/validation.go

RUN go install github.com/s-rah/onionscan@latest

ENV TZ=Europe/Madrid

WORKDIR /home

RUN mkdir /home/onionscandb

# Downloader

COPY downloader.py /home/downloader.py
RUN chmod +x /home/downloader.py

ENTRYPOINT ["python3.9","downloader.py"]