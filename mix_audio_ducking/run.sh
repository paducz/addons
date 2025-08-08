#!/usr/bin/with-contenv bashio

# ==============================================================================
# = This script runs as a persistent service, listening for jobs on stdin.    =
# = It safely merges default values from the configuration with stdin data.  =
# ==============================================================================

echo "-----------------------------------------------------------"
echo "            Audio Mixer Service has started"
echo " This add-on is now running as a persistent service."
echo " Waiting for JSON requests on stdin from Home Assistant..."
echo "-----------------------------------------------------------"

# --- Main Service Loop ---
while true; do
    # 'read' is a blocking call. It waits here until data is piped.
    read -r line

    # Check for non-empty data
    if [ -n "$line" ]; then
        bashio::log.info "================ NEW JOB RECEIVED ================"
        bashio::log.debug "Raw stdin data: $line"

        # --- Safely build the final configuration ---
        
        # Start with the default configuration from the UI.
        # Handle the case where there are no options by defaulting to an empty JSON object '{}'.
        DEFAULT_CONFIG=$(bashio::config | jq --compact-output 'select(length > 0) // {}')

        # Handle the case where stdin might be invalid JSON by defaulting to an empty JSON object.
        STDIN_CONFIG=$(echo "$line" | jq --compact-output '. // {}')
        
        # Merge the two. The stdin data (`.[1]`) will overwrite the defaults (`.[0]`).
        # This is now safe even if one or both inputs are empty.
        FINAL_CONFIG=$(jq -s '.[0] * .[1]' <(echo "$DEFAULT_CONFIG") <(echo "$STDIN_CONFIG"))
        
        bashio::log.debug "Final merged config: $FINAL_CONFIG"

        # --- Extract final values from the merged JSON ---
        API_KEY=$(echo "$FINAL_CONFIG" | jq -r '.elevenlabs_api_key // ""')
        VOICE_ID=$(echo "$FINAL_CONFIG" | jq -r '.voice_id // ""')
        MUSIC_FILENAME=$(echo "$FINAL_CONFIG" | jq -r '.music_filename // ""')
        TEXT_TO_SPEAK=$(echo "$FINAL_CONFIG" | jq -r '.text_to_speak // ""')
        OUTPUT_FILENAME=$(echo "$FINAL_CONFIG" | jq -r '.output_filename // ""')

        # --- Validate mandatory parameters ---
        # The API key MUST be in the configuration.
        if ! bashio::config.has_value 'elevenlabs_api_key'; then
             bashio::log.error "Mandatory parameter 'elevenlabs_api_key' is not set in the add-on configuration. Aborting job."
        elif [ -z "$TEXT_TO_SPEAK" ]; then
            bashio::log.error "Mandatory parameter 'text_to_speak' was not provided in the request. Aborting job."
        elif [ -z "$OUTPUT_FILENAME" ]; then
            bashio::log.error "Mandatory parameter 'output_filename' was not provided in the request. Aborting job."
        else
            bashio::log.info "Job is valid. Starting Python audio processor..."
            bashio::log.info "  - Voice: $VOICE_ID"
            bashio::log.info "  - Music: $MUSIC_FILENAME"
            # --- Call the Python script with the final, validated data ---
            /process_audio.py \
                "$API_KEY" \
                "$VOICE_ID" \
                "$MUSIC_FILENAME" \
                "$TEXT_TO_SPEAK" \
                "$OUTPUT_FILENAME"
        fi
        
        bashio::log.info "=============== JOB-HANDLING FINISHED ==============="
        bashio::log.info "Waiting for next job..."
    fi
    
    sleep 1
done