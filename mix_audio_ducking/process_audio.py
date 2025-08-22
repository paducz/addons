#!/usr/bin/env python3
"""
Process: music + TTS

Timeline:
1) 4 s music full
2) fade-out to −18 dB (TTS starts at the *middle* of this fade)
3) ducked bed under TTS
4) fade-in back to full (TTS ends at the *middle* of this fade)
5) 3 s music full
6) final 1 s fade-out (whole mix)
"""

import os
import sys
from pydub import AudioSegment
from elevenlabs.client import ElevenLabs

# === CONFIG =================================================================
INTRO_FULL_MS   = 5_000      # 4 s full intro
DUCK_FADE_MS    =  1200      # nominal fade length; may shrink if TTS is very short
DUCK_LEVEL_DB   =  -19       # duck amount during TTS
OUTRO_FULL_MS   = 5_000      # 3 s full at the end
FINAL_FADE_MS   = 2_000      # final fade-out of whole mix
TTS_TEMP_FILE   = "/tmp/tts.mp3"
# ============================================================================

def die(msg: str) -> None:
    print(f"❌  {msg}")
    sys.exit(1)

def safe_seg(seg, label):
    if seg is None:
        die(f"Segment '{label}' is None (bad slice)")
    return seg

def main() -> None:
    if len(sys.argv) != 6:
        die(f"Expected 5 args, got {len(sys.argv) - 1}")

    api_key, model_id, voice_id, music_path, text_to_speak, output_path = sys.argv[1:6]

    # --- TTS -----------------------------------------------------------------
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
    print(f"   ✔️  TTS length: {tts_len/1000:.2f} s")

    # Use an effective fade that guarantees: start/end happen at fade middles
    eff_fade_ms = min(DUCK_FADE_MS, tts_len)

    # --- Music ---------------------------------------------------------------
    try:
        music = AudioSegment.from_mp3(music_path)
    except Exception as e:
        die(f"Cannot load music '{music_path}': {e}")

    # Required total bed length:
    # intro + (fade-out + duck + fade-in) + outro
    duck_main_len = max(tts_len - eff_fade_ms, 0)  # TTS spans half-fade + duck + half-fade
    need_ms = INTRO_FULL_MS + eff_fade_ms + duck_main_len + eff_fade_ms + OUTRO_FULL_MS

    if len(music) < need_ms:
        loops = -(-need_ms // len(music))  # ceil division
        music *= loops
        print(f"   ℹ️  Music too short → looped ×{loops}")

    # --- Segment the bed -----------------------------------------------------
    i = 0
    intro_full = safe_seg(music[i : i + INTRO_FULL_MS], "intro_full")
    i += INTRO_FULL_MS

    # Fade-out: full → duck (TTS will start at the *middle* of this segment)
    fade_out = safe_seg(
        music[i : i + eff_fade_ms].fade(
            from_gain=0,
            to_gain=DUCK_LEVEL_DB,
            start=0,                # important: avoid None + int in pydub
            duration=eff_fade_ms,
        ),
        "fade_out",
    )
    i += eff_fade_ms

    # Ducked main (under the body of TTS)
    duck_main = safe_seg(
        music[i : i + duck_main_len].apply_gain(DUCK_LEVEL_DB),
        "duck_main",
    )
    i += duck_main_len

    # Fade-in: duck → full (TTS will end at the *middle* of this segment)
    fade_in = safe_seg(
        music[i : i + eff_fade_ms].fade(
            from_gain=DUCK_LEVEL_DB,
            to_gain=0,
            start=0,                # important
            duration=eff_fade_ms,
        ),
        "fade_in",
    )
    i += eff_fade_ms

    outro_full = safe_seg(music[i : i + OUTRO_FULL_MS], "outro_full")
    i += OUTRO_FULL_MS

    # Assemble the bed
    bed = intro_full + fade_out + duck_main + fade_in + outro_full

    # --- Overlay TTS ---------------------------------------------------------
    # TTS starts at the middle of fade-out, ends at the middle of fade-in
    tts_start = INTRO_FULL_MS + (eff_fade_ms // 2)
    mix = bed.overlay(tts_audio, position=tts_start)

    # --- Final fade & export -------------------------------------------------
    final = mix.fade_out(FINAL_FADE_MS)
    final.export(output_path, format="mp3")
    print(f"✅  Done → {output_path}")

    # --- Cleanup -------------------------------------------------------------
    if os.path.exists(TTS_TEMP_FILE):
        os.remove(TTS_TEMP_FILE)

if __name__ == "__main__":
    main()
