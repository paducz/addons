#!/usr/bin/env python3
import sys
import os
from pydub import AudioSegment
from elevenlabs.client import ElevenLabs

# --- KONFIGURACE EFEKTŮ ---
INTRO_DURATION_MS = 4000      # Délka úvodní hudby na plnou hlasitost
OUTRO_DURATION_MS = 3000      # Délka závěrečné hudby na plnou hlasitost
TRANSITION_FADE_MS = 500      # Délka přechodu (fade in/out) pro ducking
FADEOUT_DURATION_MS = 1000    # Finální zeslabení celého klipu
DUCKING_DB = -18              # O kolik decibelů ztlumit hudbu

# Cesta k dočasnému souboru pro TTS
TTS_TEMP_FILE = "/tmp/tts.mp3"

def main():
    # --- 1. Načtení argumentů z run.sh ---
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

        # --- A. Příprava hudebního podkresu s duckingem ---
        
        # Výpočet celkové délky finálního souboru
        total_duration_ms = INTRO_DURATION_MS + tts_duration_ms + OUTRO_DURATION_MS
        
        # Ujistíme se, že hudba je dostatečně dlouhá a ořízneme ji na finální délku
        if len(background_music) < total_duration_ms:
            print("Hudba je příliš krátká, bude započata smyčka.")
            loops = (total_duration_ms // len(background_music)) + 1
            background_music = background_music * loops
        
        music_bed = background_music[:total_duration_ms]
        print(f"Připraven hudební podkres o délce {len(music_bed) / 1000:.2f}s.")

        # Definice časů pro ducking
        duck_start_time = INTRO_DURATION_MS - (TRANSITION_FADE_MS // 2)
        duck_end_time = INTRO_DURATION_MS + tts_duration_ms + (TRANSITION_FADE_MS // 2)

        # Vytvoření ztlumené verze hudby
        ducked_music = music_bed.apply_gain(DUCKING_DB)

        # Plynulý přechod DO ztlumení
        music_bed = music_bed.fade(
            to_gain=DUCKING_DB,
            start=duck_start_time,
            duration=TRANSITION_FADE_MS
        )

        # Plynulý přechod ZPĚT Z ztlumení
        music_bed = music_bed.fade(
            from_gain=DUCKING_DB,
            start=duck_end_time,
            duration=TRANSITION_FADE_MS
        )

        # --- B. Příprava hlasové stopy s tichem na začátku ---
        print(f"Vytvářím hlasovou stopu s {INTRO_DURATION_MS}ms ticha na začátku...")
        silence_before = AudioSegment.silent(duration=INTRO_DURATION_MS)
        vocal_track = silence_before + tts_audio
        
        # --- C. Finální mix ---
        print("Pokládám hlasovou stopu na připravený hudební podkres...")
        final_mix = music_bed.overlay(vocal_track)
        
        # --- D. Finální úpravy ---
        print(f"Aplikuji finální fade-out ({FADEOUT_DURATION_MS}ms) na konci celé stopy...")
        final_mix = final_mix.fade_out(duration=FADEOUT_DURATION_MS)

        # Export finálního souboru
        print(f"Exportuji finální soubor do: {output_path}")
        final_mix.export(output_path, format="mp3")

    except Exception as e:
        print(f"Chyba při zpracování zvuku s Pydub: {e}")
        sys.exit(1)

    finally:
        # --- Úklid ---
        if os.path.exists(TTS_TEMP_FILE):
            os.remove(TTS_TEMP_FILE)
            print("Dočasný TTS soubor byl smazán.")

    print("Zpracování zvuku úspěšně dokončeno.")

if __name__ == "__main__":
    main()