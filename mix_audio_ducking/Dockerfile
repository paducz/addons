# Použijeme oficiální základní obraz pro doplňky Home Assistant
FROM homeassistant/base-debian:bullseye

# Aktualizujeme a nainstalujeme potřebné balíčky
# - python3 a pip pro spuštění skriptu pro ElevenLabs
# - ffmpeg pro veškeré operace se zvukem
# - jq pro snadnější práci s JSON (i když zde používáme bashio)
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    ffmpeg \
    jq \
    && rm -rf /var/lib/apt/lists/*

# Nainstalujeme Python knihovnu pro ElevenLabs
RUN pip3 install elevenlabs

# Zkopírujeme spouštěcí skript do kontejneru a nastavíme mu práva pro spuštění
COPY run.sh /
RUN chmod +x /run.sh

# Příkaz, který se spustí při startu kontejneru
CMD [ "/run.sh" ]