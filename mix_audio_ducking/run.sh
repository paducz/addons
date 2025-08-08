#!/usr/bin/env bash
set -e

AUDIO_DIR="${AUDIO_DIR:-/share/audio}"
PORT="${PORT:-8080}"
AUTH_TOKEN="${AUTH_TOKEN:-}"
ELEVEN_KEY="${ELEVEN_KEY:-}"

mkdir -p "$AUDIO_DIR"

exec python3 /mix.py             --audio-dir "$AUDIO_DIR"             --port "$PORT"             --auth "$AUTH_TOKEN"             --eleven-key "$ELEVEN_KEY"
