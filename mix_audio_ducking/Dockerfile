# !! NOUZOVÉ ŘEŠENÍ POUZE PRO aarch64 (Raspberry Pi atd.) !!
# bookworm: bullseye je mimo běžnou podporu a jeho balíčky z debian-security mizí (404)
FROM ghcr.io/home-assistant/aarch64-base-debian:bookworm

# Aktualizujeme a nainstalujeme potřebné balíčky.
# ffmpeg je stále potřeba, protože pydub ho používá na pozadí.
# bc a jq už nejsou potřeba.
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    ffmpeg \
    jq \
    && rm -rf /var/lib/apt/lists/*

# Nainstalujeme potřebné Python knihovny
# (bookworm chrání systémový Python podle PEP 668 — kontejner je jednoúčelový)
RUN pip3 install --no-cache-dir --break-system-packages elevenlabs pydub

# Zkopírujeme OBA skripty do kontejneru a nastavíme jim práva pro spuštění
COPY run.sh /
COPY process_audio.py /
RUN chmod +x /run.sh
RUN chmod +x /process_audio.py

# Příkaz, který se spustí při startu kontejneru
CMD [ "/run.sh" ]