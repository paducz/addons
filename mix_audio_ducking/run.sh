#!/usr/bin/env bash

# ==============================================================================
# = This script runs as a persistent service, listening for jobs on stdin.    =
# = It reads defaults from /data/options.json and merges them with stdin.    =
# = THIS VERSION DOES NOT USE BASHIO AND IS THE CORRECT SERVICE PATTERN.       =
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
        echo "================ NEW JOB RECEIVED ================"
        
        # --- Safely build the final configuration ---
        
        # Step 1: Read the default configuration file.
        # Default to an empty JSON object '{}' if the file doesn't exist or is empty.
        if [ -s /data/options.json ]; then
            DEFAULT_CONFIG=$(cat /data/options.json)
        else
            DEFAULT_CONFIG="{}"
        fi

        # Step 2: Read the configuration from stdin.
        # Default to an empty JSON object '{}' if the stdin is not valid JSON.
        if echo "$line" | jq -e . >/dev/null; then
            STDIN_CONFIG="$line"
        else
            echo "Error: Received invalid JSON on stdin. Ignoring request."
            STDIN_CONFIG="{}"
        fi

        # Step 3: Merge the two. The stdin data (`.[1]`) will overwrite the defaults (`.[0]`).
        FINAL_CONFIG=$(jq -s '.[0] * .[1]' <(echo "$DEFAULT_CONFIG") <(echo "$STDIN_CONFIG"))
        
        # --- Extract final values from the merged JSON ---
        API_KEY=$(echo "$FINAL_CONFIG" | jq -r '.elevenlabs_api_key // ""')
        VOICE_ID=$(echo "$FINAL_CONFIG" | jq -r '.voice_id // ""')
        MUSIC_FILENAME=$(echo "$FINAL_CONFIG" | jq -r '.music_filename // ""')
        TEXT_TO_SPEAK=$(echo "$FINAL_CONFIG" | jq -r '.text_to_speak // ""')
        OUTPUT_FILENAME=$(echo "$FINAL_CONFIG" | jq -r '.output_filename // ""')

        # --- Validate mandatory parameters ---
        if [ -z "$API_KEY" ] || [[ "$API_KEY" == "YOUR_ELEVENLABS_API_KEY" ]]; then
             echo "Error: Mandatory parameter 'elevenlabs_api_key' is not set in the add-on configuration. Aborting job."
        elif [ -z "$TEXT_TO_SPEAK" ]; then
            echo "Error: Mandatory parameter 'text_to_speak' was not provided in the request. Aborting job."
        elif [ -z "$OUTPUT_FILENAME" ]; then
            echo "Error: Mandatory parameter 'output_filename' was not provided in the request. Aborting job."
        else
            echo "Job is valid. Starting Python audio processor..."
            echo "  - Voice: $VOICE_ID"
            echo "  - Music: $MUSIC_FILENAME"
            # --- Call the Python script with the final, validated data ---
            /process_audio.py \
                "$API_KEY" \
                "$VOICE_ID" \
                "$MUSIC_FILENAME" \
                "$TEXT_TO_SPEAK" \
                "$OUTPUT_FILENAME"
        fi
        
        echo "=============== JOB-HANDLING FINISHED ==============="
        echo "Waiting for next job..."
    fi
    
    sleep 1
done