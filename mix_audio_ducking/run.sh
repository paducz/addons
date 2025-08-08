#!/usr/bin/with-contenv bashio

bashio::log.info "Audio Mixer Add-on spuštěn."

# --- 1. Načtení a sloučení konfigurace ---
INPUT_OPTIONS=$(</dev/stdin)
if [[ -z "$INPUT_OPTIONS" ]]; then
    bashio::log.info "Nebyla nalezena žádná data na vstupu (stdin). Používám výchozí konfiguraci."
    CONFIG=$(cat /data/options.json)
else
    bashio::log.info "Nalezena data na vstupu. Slučuji s výchozí konfigurací."
    CONFIG=$(jq -s '.[0] * .[1]' /data/options.json <(echo "$INPUT_OPTIONS"))
fi

ELEVENLABS_API_KEY=$(echo "$CONFIG" | jq -r '.elevenlabs_api_key')
VOICE_ID=$(echo "$CONFIG" | jq -r '.voice_id')
MUSIC_FILENAME=$(echo "$CONFIG" | jq -r '.music_filename')
TEXT_TO_SPEAK=$(echo "$CONFIG" | jq -r '.text_to_speak')
OUTPUT_FILENAME=$(echo "$CONFIG" | jq -r '.output_filename')

bashio::log.info "Cílový výstupní soubor: /share/${OUTPUT_FILENAME}"
bashio::log.info "Hudební soubor: '${MUSIC_FILENAME}'"
bashio::log.info "Text k přečtení: '${TEXT_TO_SPEAK}'"

# --- 2. Definice cest k souborům ---
MUSIC_PATH="${MUSIC_FILENAME}"
TTS_PATH="/tmp/tts.mp3"
OUTPUT_PATH="/share/${OUTPUT_FILENAME}"
INTRO_PATH="/tmp/intro.mp3"
MAIN_MUSIC_PATH="/tmp/main_music.mp3"
DUCKED_PART_PATH="/tmp/ducked_part.mp3"
OUTRO_PATH="/tmp/outro.mp3"
CONCAT_LIST_PATH="/tmp/concat_list.txt"
FINAL_UNFADED_PATH="/tmp/final_unfaded.mp3"

# --- 3. Validace vstupů ---
if [[ "$ELEVENLABS_API_KEY" == "YOUR_ELEVENLABS_API_KEY" || -z "$ELEVENLABS_API_KEY" ]]; then
    bashio::log.fatal "Prosím, nastavte váš API klíč pro ElevenLabs v konfiguraci doplňku."
    exit 1
fi
if [ ! -f "$MUSIC_PATH" ]; then
    bashio::log.fatal "Hudební soubor nebyl nalezen na zadané cestě: '${MUSIC_PATH}'. Ujistěte se, že cesta je správná a doplněk má k ní přístup (přes 'map' v config.yaml)."
    exit 1
fi

# --- 4. Generování TTS stopy ---
# FINÁLNÍ OPRAVA: API vrací proud dat (generátor), který musíme zpracovat ve smyčce.
bashio::log.info "Generuji řečovou stopu pomocí ElevenLabs..."
cat << EOF > /tmp/generate_tts.py
from elevenlabs.client import ElevenLabs

# Inicializace klienta
client = ElevenLabs(
    api_key="${ELEVENLABS_API_KEY}",
)

# Vygenerování proudu audio dat (generátoru)
audio_stream = client.text_to_speech.convert(
    voice_id="${VOICE_ID}",
    text="""${TEXT_TO_SPEAK}""",
    model_id="eleven_multilingual_v2"
)

# Zápis proudu dat do souboru kousek po kousku
with open("${TTS_PATH}", "wb") as f:
    for chunk in audio_stream:
        f.write(chunk)

EOF

python3 /tmp/generate_tts.py
if [ ! -f "$TTS_PATH" ]; then
    bashio::log.fatal "Generování TTS selhalo. Zkontrolujte API klíč, ID hlasu a připojení k internetu."
    exit 1
fi

# --- 5. Zpracování zvuku pomocí FFMPEG ---
TTS_DURATION=$(ffprobe -i "$TTS_PATH" -show_entries format=duration -v quiet -of csv="p=0")
bashio::log.info "Délka řečové stopy: ${TTS_DURATION}s."
bashio::log.info "Vytvářím 1s intro..."
ffmpeg -y -i "$MUSIC_PATH" -t 1 -c:a copy "$INTRO_PATH" > /dev/null 2>&1
bashio::log.info "Připravuji hudební segment pro ducking..."
ffmpeg -y -i "$MUSIC_PATH" -filter_complex "aloop=loop=-1:size=2e+09" -t "$TTS_DURATION" -c:a libmp3lame "$MAIN_MUSIC_PATH" > /dev/null 2>&1
bashio::log.info "Aplikuji ducking..."
ffmpeg -y -i "$MAIN_MUSIC_PATH" -i "$TTS_PATH" -filter_complex "[0:a][1:a]sidechaincompress=threshold=0.1:ratio=5[a]" -map "[a]" "$DUCKED_PART_PATH" > /dev/null 2>&1
bashio::log.info "Vytvářím 1s outro..."
MUSIC_OUTRO_START_TIME=$(echo "1 + $TTS_DURATION" | bc)
ffmpeg -y -i "$MUSIC_PATH" -ss "$MUSIC_OUTRO_START_TIME" -t 1 -c:a copy "$OUTRO_PATH" > /dev/null 2>&1
bashio::log.info "Spojuji segmenty..."
echo "file '$INTRO_PATH'" > "$CONCAT_LIST_PATH"
echo "file '$DUCKED_PART_PATH'" >> "$CONCAT_LIST_PATH"
echo "file '$OUTRO_PATH'" >> "$CONCAT_LIST_PATH"
ffmpeg -y -f concat -safe 0 -i "$CONCAT_LIST_PATH" -c copy "$FINAL_UNFADED_PATH" > /dev/null 2>&1
bashio::log.info "Aplikuji fade-out..."
FINAL_DURATION=$(echo "1 + $TTS_DURATION + 1" | bc)
FADEOUT_START_TIME=$(echo "$FINAL_DURATION - 1" | bc)
ffmpeg -y -i "$FINAL_UNFADED_PATH" -af "afade=t=out:st=${FADEOUT_START_TIME}:d=1" "$OUTPUT_PATH" > /dev/null 2>&1

# --- 6. Závěr ---
if [ -f "$OUTPUT_PATH" ]; then
    bashio::log.info "Hotovo! Finální soubor byl uložen do /share/${OUTPUT_FILENAME}"
else
    bashio::log.error "Nepodařilo se vytvořit finální soubor."
    exit 1
fi