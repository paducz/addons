#!/usr/bin/env python3
import sys
import os
from pydub import AudioSegment
from elevenlabs.client import ElevenLabs

# --- KONFIGURACE EFEKTŮ ---
INTRO_STABLE_MS = 4000      # Délka úvodní hudby na plnou hlasitost
OUTRO_STABLE_MS = 3000     # Délka závěrečné hudby na plnou hlasitost
FADE_DURATION_MS = 500     # Délka přechodu pro fade in/out
DUCKING_DB = -18           # O kolik decibelů ztlumit hudbu
FADEOUT_DURATION_MS = 1000 # Finální zeslabení celého klipu

# Cesta k dočasnému souboru pro TTS
TTS_TEMP_FILE = "/tmp/tts.mp3"

def main():
    # --- 1. Načtení argumentů ---
    if len(sys.argv) != 6:
        print(f"Chyba: Očekáváno 5 argumentů, přijato {len(sys.argv) - 1}")
        sys.exit(1)

    api_key, voice_id, music_path, text_to_speak, output_path = sys.argv[1:6]
    print(f"Argumenty úspěšně načteny. Cílový soubor: {output_path}")

    # --- 2. Generování TTS pomocí ElevenLabs ---
    print("Generuji TTS stopu pomocí ElevenLabs...")
    try:
        client = ElevenLabs(api_key=api_key)
        audio_stream = client.text_to_speech.convert(
            voice_id=voice_id, text=text_to_speak, model_id="eleven_multilingual_v2"
        )
        with open(TTS_TEMP_FILE, "wb") as f:
            for chunk in audio_stream: f.write(chunk)
        if not os.path.exists(TTS_TEMP_FILE) or os.path.getsize(TTS_TEMP_FILE) == 0:
            raise Exception("Vygenerovaný TTS soubor je prázdný.")
        print("TTS stopa úspěšně vygenerována.")
    except Exception as e:
        print(f"Chyba při generování TTS: {e}")
        sys.exit(1)

    # --- 3. Zpracování zvuku pomocí Pydub ---
    try:
        print("Načítám audio soubory pomocí Pydub...")
        tts_audio = AudioSegment.from_mp3(TTS_TEMP_FILE)
        background_music = AudioSegment.from_mp3(music_path)

        tts_duration_ms = len(tts_audio)
        print(f"Délka TTS stopy: {tts_duration_ms / 1000:.2f}s.")

        # Ujistíme se, že hudba je dostatečně dlouhá
        required_length = INTRO_STABLE_MS + tts_duration_ms + OUTRO_STABLE_MS
        if len(background_music) < required_length:
            print("Hudba je příliš krátká, bude započata smyčka.")
            loops = (required_length // len(background_music)) + 1
            background_music = background_music * loops

        # --- Vytvoření jednotlivých částí ---
        print("Vytvářím a ověřuji jednotlivé hudební segmenty...")

        # Úvodní plná hlasitost
        intro_part = background_music[:INTRO_STABLE_MS]

        # Fade-out přechod (ztlumí hudbu)
        transition_out_part = background_music[INTRO_STABLE_MS:INTRO_STABLE_MS + FADE_DURATION_MS].fade(to_gain=DUCKING_DB, duration=FADE_DURATION_MS)

        # Ztlumená část pro TTS
        main_ducked_part = background_music[INTRO_STABLE_MS + FADE_DURATION_MS:INTRO_STABLE_MS + FADE_DURATION_MS + tts_duration_ms].apply_gain(DUCKING_DB)

        # Fade-in přechod (hudba se vrací na plnou hlasitost)
        transition_in_part = background_music[INTRO_STABLE_MS + FADE_DURATION_MS + tts_duration_ms:INTRO_STABLE_MS + FADE_DURATION_MS + tts_duration_ms + FADE_DURATION_MS].fade(from_gain=DUCKING_DB, duration=FADE_DURATION_MS)

        # Závěrečná část hudby na plnou hlasitost
        outro_part = background_music[INTRO_STABLE_MS + FADE_DURATION_MS + tts_duration_ms + FADE_DURATION_MS:INTRO_STABLE_MS + FADE_DURATION_MS + tts_duration_ms + FADE_DURATION_MS + OUTRO_STABLE_MS]

        # --- Spojení všech částí ---
        final_background = intro_part + transition_out_part + main_ducked_part + transition_in_part + outro_part

        # --- Přehrávání TTS na pozadí hudby ---
        tts_position = INTRO_STABLE_MS + FADE_DURATION_MS  # Pozice, kde začíná TTS
        print(f"Překrývám hudbu řečí na pozici {tts_position}ms...")
        final_mix_unfaded = final_background.overlay(tts_audio, position=tts_position)

        # --- Finální úpravy ---
        print(f"Aplikuji finální fade-out ({FADEOUT_DURATION_MS}ms)...")
        final_mix = final_mix_unfaded.fade_out(duration=FADEOUT_DURATION_MS)

        # Export finálního souboru
        print(f"Exportuji finální soubor do: {output_path}")
        final_mix.export(output_path, format="mp3")

    except Exception as e:
        print(f"Chyba při zpracování zvuku s Pydub: {e}")
        sys.exit(1)

    finally:
        # --- 4. Úklid ---
        if os.path.exists(TTS_TEMP_FILE):
            os.remove(TTS_TEMP_FILE)
            print("Dočasný TTS soubor byl smazán.")

    print("Zpracování zvuku úspěšně dokončeno.")

if __name__ == "__main__":
    main()
