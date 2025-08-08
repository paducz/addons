ARG BUILD_FROM=ghcr.io/home-assistant/amd64-base:latest
FROM ${BUILD_FROM}

LABEL maintainer="TvojeJmeno <email@example.com>"

RUN apt-get update          && apt-get install -y --no-install-recommends ffmpeg python3 python3-pip          && apt-get clean          && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /requirements.txt
RUN pip3 install --no-cache-dir -r /requirements.txt

COPY run.sh /run.sh
COPY mix.py /mix.py
RUN chmod a+x /run.sh

CMD [ "/run.sh" ]
