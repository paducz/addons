ARG BUILD_FROM=ghcr.io/home-assistant/amd64-base:latest
FROM ${BUILD_FROM}

LABEL maintainer="TvojeJmeno <email@example.com>"

RUN apk add --no-cache ffmpeg python3 py3-pip

COPY requirements.txt /requirements.txt
RUN pip3 install --no-cache-dir --break-system-packages -r /requirements.txt

# S6 service script
COPY run.sh /etc/services.d/mix_audio/run
RUN chmod +x /etc/services.d/mix_audio/run
