#!/usr/bin/env python3
import sys
import os
from pydub import AudioSegment
from elevenlabs.client import ElevenLabs

# --- Konfigurace efektů ---
INTRO_DURATION_MS = 1000  # 1 sekunda
OUTRO_DURATION_MS = 1000  # 1 sekunda
FADEOUT_DURATION_MS = 1000 # 1 sekunda
# O kolik decibelů ztlumit hudbu během řeči. Záporné číslo znamená ztlumení.
DUCKING_DB = -15

# Cesta k dočasnému souboru pro TTS
TTS_TEMP_FILE = "/tmp/tts.mp3"

def main():
    # --- 1. Načtení argumentů z run.sh ---
    if len(sys.argv) != 6:
        print(f"Chyba: Očekáváno 5 argumentů, přijato {len(sys.argv) - 1}")
        sys.exit(1)

    api_key = sys.argv[1]
    voice_id = sys.argv[2]
    music_path = sys.argv[3]
    text_to_speak = sys.argv[4]
    output_path = sys.argv[5]

    print("Argumenty úspěšně načteny.")
    print(f"Cílový soubor: {output_path}")

    # --- 2. Generování TTS pomocí ElevenLabs ---
    print("Generuji TTS stopu pomocí ElevenLabs...")
    try:
        client = ElevenLabs(api_key=api_key)
        audio_stream = client.text_to_speech.convert(
            voice_id=voice_id,
            text=text_to_speak,
            model_id="eleven_multilingual_v2"
        )

        with open(TTS_TEMP_FILE, "wb") as f:
            for chunk in audio_stream:
                f.write(chunk)
        
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

        # Ujistíme se, že hudba je dostatečně dlouhá (pomocí prolnutí sama se sebou)
        required_length = INTRO_DURATION_MS + tts_duration_ms + OUTRO_DURATION_MS
        if len(background_music) < required_length:
            print("Hudba je příliš krátká, bude započata smyčka.")
            loops = (required_length // len(background_music)) + 1
            background_music = background_music * loops
        
        background_music = background_music[:required_length]

        # a) Vytvoření intra
        print("Vytvářím intro...")
        intro = background_music[:INTRO_DURATION_MS]

        # b) Vytvoření hlavní části s duckingem
        print(f"Aplikuji ducking ({DUCKING_DB} dB)...")
        main_part_original = background_music[INTRO_DURATION_MS : INTRO_DURATION_MS + tts_duration_ms]
        # Ztlumení hudby
        main_part_quieter = main_part_original.apply_gain(DUCKING_DB)
        # Překrytí řečí
        ducked_part = main_part_quieter.overlay(tts_audio)

        # c) Vytvoření outra
        print("Vytvářím outro...")
        outro_start = INTRO_DURATION_MS + tts_duration_ms
        outro = background_music[outro_start : outro_start + OUTRO_DURATION_MS]

        # d) Spojení všech částí
        print("Spojuji všechny segmenty...")
        final_audio = intro + ducked_part + outro

        # e) Aplikace finálního fade-outu
        print(f"Aplikuji fade-out ({FADEOUT_DURATION_MS}ms)...")
        final_audio = final_audio.fade_out(duration=FADEOUT_DURATION_MS)

        # f) Export finálního souboru
        print(f"Exportuji finální soubor do: {output_path}")
        final_audio.export(output_path, format="mp3")

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