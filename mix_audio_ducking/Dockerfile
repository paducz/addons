# !! NOUZOVÉ ŘEŠENÍ POUZE PRO aarch64 (Raspberry Pi atd.) !!
# Toto řešení není přenositelné na jiné platformy (např. Intel PC).
# Správný způsob je `FROM %%BASE_IMAGE%%`, ale toto může pomoci, pokud
# je váš Supervisor zaseknutý.
FROM ghcr.io/home-assistant/aarch64-base-debian:bullseye

# Aktualizujeme a nainstalujeme potřebné balíčky
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