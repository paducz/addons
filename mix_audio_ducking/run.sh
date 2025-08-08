#!/usr/bin/with-contenv bashio

# ==============================================================================
# = This script runs as a persistent service, listening for jobs on stdin.    =
# ==============================================================================

# ------------------------------------------------------------------------------
# M A I N   S E R V I C E   L O O P
#
# This function contains the infinite loop that waits for jobs.
# ------------------------------------------------------------------------------
main_loop() {
    bashio::log.info "-----------------------------------------------------------"
    bashio::log.info "            Audio Mixer Service is now running"
    bashio::log.info " This add-on is ready and waiting for JSON requests on stdin."
    bashio::log.info "-----------------------------------------------------------"

    while true; do
        # The 'read' command is a blocking call. It will wait here until
        # the hassio.addon_stdin service sends a line of data.
        local line
        read -r line

        # Check if we actually received a non-empty line of data
        if [[ -n "$line" ]]; then
            bashio::log.info "================ NEW JOB RECEIVED ================"
            
            # Log the raw received data for debugging
            bashio::log.debug "Raw JSON received: $line"

            # Use default values from config and merge stdin data which takes precedence.
            local api_key
            local voice_id
            local music_filename
            local text_to_speak
            local output_filename
            
            api_key=$(bashio::config 'elevenlabs_api_key')
            voice_id=$(echo "$line" | jq -e -r ".voice_id // \"$(bashio::config 'voice_id')\"")
            music_filename=$(echo "$line" | jq -e -r ".music_filename // \"$(bashio::config 'music_filename')\"")
            text_to_speak=$(echo "$line" | jq -e -r '.text_to_speak // empty')
            output_filename=$(echo "$line" | jq -e -r '.output_filename // empty')

            # --- Validate mandatory parameters ---
            if ! bashio::config.has_value 'elevenlabs_api_key'; then
                 bashio::log.error "Mandatory parameter 'elevenlabs_api_key' is not set in the configuration. Aborting job."
            elif [[ -z "$text_to_speak" ]]; then
                bashio::log.error "Mandatory parameter 'text_to_speak' was not provided in the request. Aborting job."
            elif [[ -z "$output_filename" ]]; then
                bashio::log.error "Mandatory parameter 'output_filename' was not provided in the request. Aborting job."
            else
                bashio::log.info "Job is valid. Starting Python audio processor..."
                # --- Call the Python script with the final, validated data ---
                /process_audio.py \
                    "$api_key" \
                    "$voice_id" \
                    "$music_filename" \
                    "$text_to_speak" \
                    "$output_filename"
            fi
            
            bashio::log.info "=============== JOB-HANDLING FINISHED ==============="
        fi
        
        # This sleep is a safety net.
        sleep 1
    done
}

# --- SCRIPT EXECUTION ---
# This line calls the main loop function, starting the persistent service.
main_loop