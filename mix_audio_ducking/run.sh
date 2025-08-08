#!/usr/bin/with-contenv bashio

bashio::log.info "Pydub Audio Mixer Add-on spuštěn."

# Načtení konfigurace (zůstává stejné)
INPUT_OPTIONS=$(</dev/stdin)
if [[ -z "$INPUT_OPTIONS" ]]; then
    bashio::log.info "Nebyla nalezena žádná data na vstupu (stdin). Používám výchozí konfiguraci."
    CONFIG=$(cat /data/options.json)
else
    bashio::log.info "Nalezena data na vstupu. Slučuji s výchozí konfigurací."
    CONFIG=$(jq -s '.[0] * .[1]' /data/options.json <(echo "$INPUT_OPTIONS"))
fi

# Načtení finálních hodnot
ELEVENLABS_API_KEY=$(echo "$CONFIG" | jq -r '.elevenlabs_api_key')
VOICE_ID=$(echo "$CONFIG" | jq -r '.voice_id')
MUSIC_FILENAME=$(echo "$CONFIG" | jq -r '.music_filename')
TEXT_TO_SPEAK=$(echo "$CONFIG" | jq -r '.text_to_speak')
OUTPUT_FILENAME=$(echo "$CONFIG" | jq -r '.output_filename')

# Spuštění hlavního Python skriptu s konfigurací jako argumenty
# Používáme uvozovky pro bezpečné předání textu s mezerami a speciálními znaky
/process_audio.py \
    "$ELEVENLABS_API_KEY" \
    "$VOICE_ID" \
    "$MUSIC_FILENAME" \
    "$TEXT_TO_SPEAK" \
    "$OUTPUT_FILENAME"

# Zkontrolujeme exit kód Python skriptu
if [ $? -eq 0 ]; then
    bashio::log.info "Python skript úspěšně dokončen."
else
    bashio::log.error "Python skript selhal. Zkontrolujte log výše pro detaily."
fi