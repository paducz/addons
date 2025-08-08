ARG BUILD_FROM=ghcr.io/home-assistant/amd64-base:latest
FROM ${BUILD_FROM}

LABEL maintainer="TvojeJmeno <email@example.com>"

RUN apk add --no-cache ffmpeg python3 py3-pip

COPY requirements.txt /requirements.txt
RUN pip3 install --no-cache-dir -r /requirements.txt

COPY run.sh /run.sh
COPY mix.py /mix.py
RUN chmod a+x /run.sh

CMD [ "/run.sh" ]
