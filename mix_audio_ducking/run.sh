#!/usr/bin/env bash

# ==============================================================================
# = This script runs as a persistent service, listening for jobs on stdin.    =
# = It uses standard 'echo' for logging as it is the main service process.   =
# ==============================================================================

# --- Initial Startup Log ---
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
        echo "================ NEW JOB RECEIVED ================"
        
        # --- Safely parse the JSON data using jq ---
        # Note: We can't use bashio::config, so we MUST pass the API key in the script call.
        
        # We need to make sure the input is valid JSON before proceeding
        if ! echo "$line" | jq -e . >/dev/null; then
            echo "Error: Received invalid JSON. Ignoring request."
        else
            # Extract values, providing 'null' as a default for optional fields
            VOICE_ID=$(echo "$line" | jq -r '.voice_id // null')
            MUSIC_FILENAME=$(echo "$line" | jq -r '.music_filename // null')
            TEXT_TO_SPEAK=$(echo "$line" | jq -r '.text_to_speak // null')
            OUTPUT_FILENAME=$(echo "$line" | jq -r '.output_filename // null')
            API_KEY=$(echo "$line" | jq -r '.api_key // null')

            # --- Validate mandatory parameters ---
            if [[ "$API_KEY" == "null" ]]; then
                 echo "Error: Mandatory parameter 'api_key' was not provided. Aborting job."
            elif [[ "$TEXT_TO_SPEAK" == "null" ]]; then
                echo "Error: Mandatory parameter 'text_to_speak' was not provided. Aborting job."
            elif [[ "$OUTPUT_FILENAME" == "null" ]]; then
                echo "Error: Mandatory parameter 'output_filename' was not provided. Aborting job."
            else
                echo "Job is valid. Starting Python audio processor..."
                # --- Call the Python script with the final, validated data ---
                /process_audio.py \
                    "$API_KEY" \
                    "$VOICE_ID" \
                    "$MUSIC_FILENAME" \
                    "$TEXT_TO_SPEAK" \
                    "$OUTPUT_FILENAME"
            fi
        fi
        
        echo "=============== JOB-HANDLING FINISHED ==============="
        echo "Waiting for next job..."
    fi
    
    # Sleep to prevent high CPU usage in case of a fast-failing loop
    sleep 1
done