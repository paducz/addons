ARG BUILD_FROM=ghcr.io/home-assistant/amd64-base:latest
FROM ${BUILD_FROM}

LABEL maintainer="TvojeJmeno <email@example.com>"

RUN apk add --no-cache ffmpeg python3 py3-pip py3-virtualenv

COPY requirements.txt /requirements.txt
RUN python3 -m venv /venv && \
    /venv/bin/pip install --no-cache-dir -r /requirements.txt

ENV PATH="/venv/bin:$PATH"

COPY run.sh /run.sh
COPY mix.py /mix.py
RUN chmod a+x /run.sh

COPY run.sh /run.sh
COPY etc /etc
RUN chmod +x /run.sh /etc/services.d/mix/run