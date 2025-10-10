#!/usr/bin/env python3
"""
Process: music + TTS

Timeline:
1) intro_full_ms of music at full volume
2) fade-out to −18 dB (TTS starts at the *middle* of this fade)
3) ducked bed under TTS
4) fade-in back to full (TTS ends at the *middle* of this fade)
5) outro_full_ms of music at full volume
6) final fade-out of whole mix
"""

import os
import sys
from pydub import AudioSegment
from elevenlabs.client import ElevenLabs

# === CONFIG =================================================================
DUCK_FADE_MS    = 1200       # nominal fade length; may shrink if TTS is very short
FINAL_FADE_MS   = 2000       # final fade-out of whole mix
TTS_TEMP_FILE   = "/tmp/tts.mp3"
# ============================================================================

def die(msg: str) -> None:
    """Print error and exit."""
    print(f"❌  {msg}")
    sys.exit(1)

def safe_seg(seg, label):
    """Ensure the segment is not empty."""
    if len(seg) <= 0:
        die(f"Segment '{label}' is empty (bad slice)")
    return seg

def main() -> None:
    # --- Validate arguments ---
    if len(sys.argv) != 10:
        die(f"Expected 9 args, got {len(sys.argv) - 1}")

    api_key, model_id, voice_id, duck_level_db, intro_full_ms, outro_full_ms, music_path, text_to_speak, output_path = sys.argv[1:10]

    try:
        duck_level_db = int(duck_level_db)
        intro_full_ms = int(intro_full_ms)
        outro_full_ms = int(outro_full_ms)
    except ValueError:
        die("duck_level_db, intro_full_ms and outro_full_ms must be integers")

    # --- Generate TTS --------------------------------------------------------
    print("⏳  Generating TTS…")
    try:
        client = ElevenLabs(api_key=api_key)
        stream = client.text_to_speech.convert(
            voice_id=voice_id,
            text=text_to_speak,
            model_id=model_id,
        )
        with open(TTS_TEMP_FILE, "wb") as f:
            for chunk in stream:
                f.write(chunk)

        if not os.path.getsize(TTS_TEMP_FILE):
            die("Generated TTS file is empty.")

        tts_audio = AudioSegment.from_mp3(TTS_TEMP_FILE)
    except Exception as e:
        die(f"TTS failed: {e}")

    tts_len = len(tts_audio)
    if tts_len <= 0:
        die("TTS audio has zero length.")

    print(f"   ✔️  TTS length: {tts_len / 1000:.2f} s")

    # Effective fade ensures TTS starts/ends at fade middles
    eff_fade_ms = min(DUCK_FADE_MS, tts_len)

    # --- Load music ----------------------------------------------------------
    try:
        music = AudioSegment.from_mp3(music_path)
    except Exception as e:
        die(f"Cannot load music '{music_path}': {e}")

    # Calculate required total bed length
    duck_main_len = max(tts_len - eff_fade_ms, 0)  # core ducked section
    need_ms = intro_full_ms + eff_fade_ms + duck_main_len + eff_fade_ms + outro_full_ms

    if len(music) < need_ms:
        loops = -(-need_ms // len(music))  # ceil division
        music *= loops
        print(f"   ℹ️  Music too short → looped ×{loops}")

    # --- Build the segments --------------------------------------------------
    i = 0
    intro_full = safe_seg(music[i : i + intro_full_ms], "intro_full")
    i += intro_full_ms

    # Fade-out: full → duck (TTS will start at the *middle* of this segment)
    fade_out = safe_seg(
        music[i : i + eff_fade_ms].fade(
            from_gain=0,
            to_gain=duck_level_db,
            start=0,                # important: avoid None + int in pydub
            duration=eff_fade_ms,
        ),
        "fade_out",
    )
    i += eff_fade_ms

    duck_main = safe_seg(
        music[i : i + duck_main_len].apply_gain(duck_level_db),
        "duck_main"
    )
    i += duck_main_len

    # Fade-in: duck → full (TTS will end at the *middle* of this segment)
    fade_in = safe_seg(
        music[i : i + eff_fade_ms].fade(
            from_gain=duck_level_db,
            to_gain=0,
            start=0,                # important
            duration=eff_fade_ms,
        ),
        "fade_in",
    )
    i += eff_fade_ms

    outro_full = safe_seg(music[i : i + outro_full_ms], "outro_full")
    i += outro_full_ms

    # Assemble the background music bed
    bed = intro_full + fade_out + duck_main + fade_in + outro_full

    # --- Overlay TTS ---------------------------------------------------------
    # TTS starts at the middle of fade-out and ends at middle of fade-in
    tts_start = intro_full_ms + (eff_fade_ms // 2)
    mix = bed.overlay(tts_audio, position=tts_start)

    # --- Final fade-out and export -------------------------------------------
    final = mix.fade_out(FINAL_FADE_MS)
    final.export(output_path, format="mp3")
    print(f"✅  Done → {output_path}")

    # --- Cleanup -------------------------------------------------------------
    if os.path.exists(TTS_TEMP_FILE):
        os.remove(TTS_TEMP_FILE)

if __name__ == "__main__":
    main()
