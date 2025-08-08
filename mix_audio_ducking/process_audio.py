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

        # --- Výpočet celkové délky a příprava základní hudební stopy ---
        total_duration_ms = INTRO_DURATION_MS + tts_duration_ms + OUTRO_DURATION_MS
        
        if len(background_music) < total_duration_ms:
            print("Hudba je příliš krátká, bude započata smyčka.")
            loops = (total_duration_ms // len(background_music)) + 1
            background_music = background_music * loops
        
        # Toto je naše základní plátno v plné hlasitosti
        final_background = background_music[:total_duration_ms]
        print(f"Připraveno základní hudební plátno o délce {len(final_background) / 1000:.2f}s.")

        # --- Příprava ztlumené "záplaty" ---
        # Tato záplata pokryje celou dobu, kdy je hudba ztlumená, včetně přechodů
        duck_start_pos = INTRO_DURATION_MS
        duck_end_pos = INTRO_DURATION_MS + tts_duration_ms
        duck_duration = duck_end_pos - duck_start_pos
        
        print(f"Vytvářím ztlumenou 'záplatu' o délce {duck_duration / 1000:.2f}s.")
        ducked_segment = final_background[duck_start_pos:duck_end_pos]
        
        # Aplikujeme plynulé přechody na okrajích této záplaty
        ducked_segment = ducked_segment.fade_in(TRANSITION_FADE_MS).fade_out(TRANSITION_FADE_MS)
        
        # Ztlumíme celou záplatu
        ducked_segment = ducked_segment.apply_gain(DUCKING_DB)

        # --- Aplikace ztlumené záplaty na hlavní hudební stopu ---
        print(f"Aplikuji ztlumenou záplatu na hudební plátno na pozici {duck_start_pos}ms.")
        final_background = final_background.overlay(ducked_segment, position=duck_start_pos)
        
        # --- Příprava hlasové stopy s tichem na začátku ---
        print(f"Vytvářím hlasovou stopu s {INTRO_DURATION_MS}ms ticha na začátku...")
        silence_before = AudioSegment.silent(duration=INTRO_DURATION_MS)
        vocal_track = silence_before + tts_audio
        
        # --- Finální mix ---
        print("Pokládám hlasovou stopu na finální hudební podkres...")
        final_mix_unfaded = final_background.overlay(vocal_track)
        
        # --- Finální úpravy ---
        print(f"Aplikuji finální fade-out na konci celé stopy...")
        final_mix = final_mix_unfaded.fade_out(duration=FADEOUT_DURATION_MS)

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