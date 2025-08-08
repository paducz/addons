#!/usr/bin/with-contenv bashio

bashio::log.info "-----------------------------------------------------------"
bashio::log.info "            Audio Mixer Service has started"
bashio::log.info " This add-on is now running as a persistent service."
bashio::log.info " Waiting for requests from Home Assistant scripts..."
bashio::log.info "-----------------------------------------------------------"

# Infinite loop to keep the add-on alive and listening for input
while true; do
    # Read a line of JSON from standard input. This will block until data is sent.
    read -r line
    
    # Check if we actually received data
    if [ -n "$line" ]; then
        bashio::log.info "======== NEW REQUEST RECEIVED ========"
        bashio::log.info "Received data: $line"
        
        # --- Parse the JSON data ---
        # We use the default values from the config as a base
        BASE_CONFIG=$(cat /data/options.json)
        # We merge the received data, which takes precedence
        CONFIG=$(jq -s '.[0] * .[1]' <(echo "$BASE_CONFIG") <(echo "$line"))

        # Extract values
        ELEVENLABS_API_KEY=$(echo "$CONFIG" | jq -r '.elevenlabs_api_key')
        VOICE_ID=$(echo "$CONFIG" | jq -r '.voice_id')
        MUSIC_FILENAME=$(echo "$CONFIG" | jq -r '.music_filename')
        TEXT_TO_SPEAK=$(echo "$CONFIG" | jq -r '.text_to_speak')
        OUTPUT_FILENAME=$(echo "$CONFIG" | jq -r '.output_filename')

        # --- Validate mandatory parameters ---
        if [ -z "$TEXT_TO_SPEAK" ] || [ -z "$OUTPUT_FILENAME" ]; then
            bashio::log.error "Request is missing 'text_to_speak' or 'output_filename'. Aborting."
        else
            # --- Call the Python script with the parsed data ---
            # The Python script will now handle the entire audio processing
            /process_audio.py \
                "$ELEVENLABS_API_KEY" \
                "$VOICE_ID" \
                "$MUSIC_FILENAME" \
                "$TEXT_TO_SPEAK" \
                "$OUTPUT_FILENAME"
        fi
        
        bashio::log.info "======== REQUEST PROCESSING FINISHED ========"
    fi
    
    # Sleep for a short duration to prevent high CPU usage if something goes wrong
    sleep 1
done