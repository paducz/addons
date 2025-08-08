# Použijeme speciální proměnnou, kterou Home Assistant Supervisor
# automaticky nahradí správným a aktuálním základním obrazem.
FROM %%BASE_IMAGE%%

# Aktualizujeme a nainstalujeme potřebné balíčky
# PŘIDÁNA PODPORA PRO 'bc' (Basic Calculator) pro matematické operace s desetinnými čísly
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