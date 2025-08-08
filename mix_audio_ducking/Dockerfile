# !! NOUZOVÉ ŘEŠENÍ POUZE PRO aarch64 (Raspberry Pi atd.) !!
FROM ghcr.io/home-assistant/aarch64-base-debian:bullseye

# Aktualizujeme a nainstalujeme potřebné balíčky
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    ffmpeg \
    jq \
    bc \
    && rm -rf /var/lib/apt/lists/*

# Nainstalujeme Python knihovnu pro ElevenLabs
RUN pip3 install elevenlabs

# Zkopírujeme spouštěcí skript do kontejneru a nastavíme mu práva pro spuštění
COPY run.sh /
RUN chmod +x /run.sh

# Příkaz, který se spustí při startu kontejneru
CMD [ "/run.sh" ]