#!/usr/bin/env bash

# ==============================================================================
# = This script runs as a persistent service, listening for jobs on stdin.    =
# = It uses a single, robust jq command to parse the incoming JSON payload.  =
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
        
        # --- Create environment variables from the JSON payload ---
        # This is the most robust method. It uses one jq command to export all variables.
        # It provides default values for optional fields.
        # If a mandatory field is missing, its variable will be empty ('').
        eval "$(echo "$line" | jq -r '
            @sh "
            API_KEY=\(.api_key // "")
            VOICE_ID=\(.voice_id // "21m00Tcm4TlvDq8ikWAM")
            MUSIC_FILENAME=\(.music_filename // "/media/sounds/ambient_story_1.mp3")
            TEXT_TO_SPEAK=\(.text_to_speak // "")
            OUTPUT_FILENAME=\(.output_filename // "")
            "
        ')"

        # --- Validate mandatory parameters ---
        if [ -z "$API_KEY" ]; then
             echo "Error: Mandatory parameter 'api_key' was not provided. Aborting job."
        elif [ -z "$TEXT_TO_SPEAK" ]; then
            echo "Error: Mandatory parameter 'text_to_speak' was not provided. Aborting job."
        elif [ -z "$OUTPUT_FILENAME" ]; then
            echo "Error: Mandatory parameter 'output_filename' was not provided. Aborting job."
        else
            echo "Job is valid. Starting Python audio processor..."
            echo "  - Voice ID: $VOICE_ID"
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