#!/usr/bin/env bash

# ==============================================================================
# = This script runs as a persistent service, listening for jobs on stdin.     =
# = It reads defaults from /data/options.json and merges them with stdin.      =
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

        # Step 2: Validate stdin JSON and set it as config.
        if echo "$line" | jq -e . >/dev/null 2>&1; then
            STDIN_CONFIG="$line"
        else
            echo "Error: Received invalid JSON on stdin. Ignoring request."
            STDIN_CONFIG="{}"
        fi

        # Step 3: Merge the two JSON objects.
        # The stdin data (`.[1]`) overwrites defaults (`.[0]`).
        FINAL_CONFIG=$(jq -s '.[0] * .[1]' <(echo "$DEFAULT_CONFIG") <(echo "$STDIN_CONFIG"))
        
        # --- Extract final values from the merged JSON ---
        API_KEY=$(echo "$FINAL_CONFIG" | jq -r '.elevenlabs_api_key // ""')
        MODEL_ID=$(echo "$FINAL_CONFIG" | jq -r '.model_id // ""')
        VOICE_ID=$(echo "$FINAL_CONFIG" | jq -r '.voice_id // ""')
        DUCK_LEVEL_DB=$(echo "$FINAL_CONFIG" | jq -r '.duck_level_db // 0')
        INTRO_FULL_MS=$(echo "$FINAL_CONFIG" | jq -r '.intro_full_ms // 0')
        OUTRO_FULL_MS=$(echo "$FINAL_CONFIG" | jq -r '.outro_full_ms // 0')
        MUSIC_FILENAME=$(echo "$FINAL_CONFIG" | jq -r '.music_filename // ""')
        TEXT_TO_SPEAK=$(echo "$FINAL_CONFIG" | jq -r '.text_to_speak // ""')
        OUTPUT_FILENAME=$(echo "$FINAL_CONFIG" | jq -r '.output_filename // ""')
        # Optional ElevenLabs post-processing, e.g. {"filter_preset_id": "old_radio"}
        AUDIO_EFFECTS=$(echo "$FINAL_CONFIG" | jq -c '.audio_effects // {}')

        # --- Validate mandatory parameters ---
        if [ -z "$API_KEY" ] || [[ "$API_KEY" == "YOUR_ELEVENLABS_API_KEY" ]]; then
            echo "Error: Mandatory parameter 'elevenlabs_api_key' is not set in the add-on configuration. Aborting job."
        elif [ -z "$MODEL_ID" ]; then
            echo "Error: Mandatory parameter 'model_id' was not provided in the request. Aborting job."
        elif [ -z "$VOICE_ID" ]; then
            echo "Error: Mandatory parameter 'voice_id' was not provided in the request. Aborting job."
        elif ! [[ "$DUCK_LEVEL_DB" =~ ^-?[0-9]+$ ]]; then
            echo "Error: duck_level_db must be a valid number. Aborting job."
        elif ! [[ "$INTRO_FULL_MS" =~ ^[0-9]+$ ]]; then
            echo "Error: intro_full_ms must be a valid number. Aborting job."
        elif ! [[ "$OUTRO_FULL_MS" =~ ^[0-9]+$ ]]; then
            echo "Error: outro_full_ms must be a valid number. Aborting job."
        elif [ -z "$TEXT_TO_SPEAK" ]; then
            echo "Error: Mandatory parameter 'text_to_speak' was not provided in the request. Aborting job."
        elif [ -z "$OUTPUT_FILENAME" ]; then
            echo "Error: Mandatory parameter 'output_filename' was not provided in the request. Aborting job."
        else
            echo "Job is valid. Starting Python audio processor..."
            echo "  - Voice: $VOICE_ID"
            echo "  - Music: $MUSIC_FILENAME"
            echo "  - Duck Level: ${DUCK_LEVEL_DB}dB"
            echo "  - Intro Fade Duration: ${INTRO_FULL_MS}ms"
            echo "  - Outro Fade Duration: ${OUTRO_FULL_MS}ms"
            echo "  - Output File: $OUTPUT_FILENAME"
            echo "  - Audio Effects: $AUDIO_EFFECTS"

            # --- Call the Python script with the final, validated data ---
            /process_audio.py \
                "$API_KEY" \
                "$MODEL_ID" \
                "$VOICE_ID" \
                "$DUCK_LEVEL_DB" \
                "$INTRO_FULL_MS" \
                "$OUTRO_FULL_MS" \
                "$MUSIC_FILENAME" \
                "$TEXT_TO_SPEAK" \
                "$OUTPUT_FILENAME" \
                "$AUDIO_EFFECTS"
        fi
        
        echo "=============== JOB-HANDLING FINISHED ==============="
        echo "Waiting for next job..."
    fi
    
    # Small delay to prevent tight looping
    sleep 1
done
