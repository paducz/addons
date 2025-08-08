#!/usr/bin/env python3
"""
Mixne podkresovou hudbu s TTS přesně takto:

1) 4 s hudba na plnou hlasitost
2) 0,5 s plynulý fade-out (−18 dB)
3) během ztlumení hraje TTS
4) po TTS 0,5 s fade-in zpět na plnou hlasitost
5) 3 s hudba na plnou hlasitost
6) závěrečný 1 s fade-out celého klipu
"""

import os
import sys
from pydub import AudioSegment
from elevenlabs.client import ElevenLabs

# ==== KONSTANTY – lze doladit bez dalších úprav kódu ====
INTRO_FULL_MS   = 4_000      # 1) úvod
DUCK_FADE_MS    =   500      # 2) & 4) délka obou přechodů
DUCK_LEVEL_DB   =  -18       # 2) útlum během TTS
OUTRO_FULL_MS   = 3_000      # 5) závěrečný plný úsek
FINAL_FADE_MS   = 1_000      # 6) úplný fade-out na konci
TTS_TEMP_FILE   = "/tmp/tts.mp3"
# =========================================================

def die(msg):
    print(f"❌  {msg}")
    sys.exit(1)

def safe_seg(seg, label):
    """Ověří, že segment existuje a má smysluplnou délku."""
    if seg is None:
        die(f"Segment '{label}' je None (pravděpodobně špatný slice)")
    return seg

def main() -> None:
    if len(sys.argv) != 6:
        die(f"Očekáváno 5 argumentů, dostal jsem {len(sys.argv)-1}")

    api_key, voice_id, music_path, text_to_speak, output_path = sys.argv[1:6]

    # --- 1) Vygeneruj TTS ---------------------------------------------------
    print("⏳  Generuji TTS u ElevenLabs…")
    try:
        client = ElevenLabs(api_key=api_key)
        stream = client.text_to_speech.convert(
            voice_id=voice_id,
            text=text_to_speak,
            model_id="eleven_multilingual_v2",
        )
        with open(TTS_TEMP_FILE, "wb") as f:
            for chunk in stream:
                f.write(chunk)
        if not os.path.getsize(TTS_TEMP_FILE):
            die("Vygenerovaný TTS soubor je prázdný.")
        tts_audio = AudioSegment.from_mp3(TTS_TEMP_FILE)
    except Exception as e:
        die(f"Generování TTS se nezdařilo: {e}")

    tts_len = len(tts_audio)
    print(f"   ✔️  TTS délka: {tts_len/1000:.2f} s")

    # --- 2) Načti hudbu a případně ji nasmyčkuj -----------------------------
    try:
        music = AudioSegment.from_mp3(music_path)
    except Exception as e:
        die(f"Nejde načíst hudba '{music_path}': {e}")

    # kolik hudby minimálně potřebujeme?
    need_ms = INTRO_FULL_MS + DUCK_FADE_MS + tts_len + DUCK_FADE_MS + OUTRO_FULL_MS
    if len(music) < need_ms:
        loops = -(-need_ms // len(music))   # zaokrouhlení nahoru
        music *= loops
        print(f"   ℹ️  Hudba byla krátká → nasmyčkováno ×{loops}")

    # --- 3) Rozkouskuj hudbu přesně podle scénáře ---------------------------
    i  = 0
    intro_full     = safe_seg(music[i : i+INTRO_FULL_MS], "intro_full")
    i += INTRO_FULL_MS

    intro_fade_out = safe_seg(music[i : i+DUCK_FADE_MS]
                              .fade(from_gain=0, to_gain=DUCK_LEVEL_DB,
                                    duration=DUCK_FADE_MS),
                              "intro_fade_out")
    i += DUCK_FADE_MS

    tts_bg         = safe_seg(music[i : i+tts_len].apply_gain(DUCK_LEVEL_DB),
                              "tts_bg")
    i += tts_len

    outro_fade_in  = safe_seg(music[i : i+DUCK_FADE_MS]
                              .fade(from_gain=DUCK_LEVEL_DB, to_gain=0,
                                    duration=DUCK_FADE_MS),
                              "outro_fade_in")
    i += DUCK_FADE_MS

    outro_full     = safe_seg(music[i : i+OUTRO_FULL_MS], "outro_full")
    i += OUTRO_FULL_MS

    # --- 4) Slep dohromady a přidej TTS overlay ----------------------------
    bg_mix = intro_full + intro_fade_out + tts_bg + outro_fade_in + outro_full
    tts_start = INTRO_FULL_MS + DUCK_FADE_MS       # = 4 s + 0,5 s
    mix = bg_mix.overlay(tts_audio, position=tts_start)

    # --- 5) Finální fade-out a export --------------------------------------
    final = mix.fade_out(FINAL_FADE_MS)
    final.export(output_path, format="mp3")
    print(f"✅  Hotovo → {output_path}")

    # --- 6) Úklid -----------------------------------------------------------
    if os.path.exists(TTS_TEMP_FILE):
        os.remove(TTS_TEMP_FILE)

if __name__ == "__main__":
    main()
