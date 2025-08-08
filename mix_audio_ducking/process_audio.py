#!/usr/bin/env python3
import sys
import os
from pydub import AudioSegment
from elevenlabs.client import ElevenLabs

# --- KONFIGURACE EFEKTŮ ---
# Upraveno dle vaší nové specifikace
INTRO_DURATION_MS = 4000      # Délka úvodní hudby na plnou hlasitost
OUTRO_DURATION_MS = 3000      # Délka závěrečné hudby na plnou hlasitost
FADEOUT_DURATION_MS = 1000    # Finální zeslabení celého klipu
DUCKING_DB = -18              # O kolik decibelů ztlumit hudbu (doporučuji trochu víc pro lepší srozumitelnost)
# Délka přechodu (crossfade) mezi segmenty. Zajišťuje plynulost.
CROSSFADE_DURATION_MS = 500

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

        # Ujistíme se, že hudba je dostatečně dlouhá
        required_length = INTRO_DURATION_MS + tts_duration_ms + OUTRO_DURATION_MS
        if len(background_music) < required_length:
            print("Hudba je příliš krátká, bude započata smyčka.")
            loops = (required_length // len(background_music)) + 1
            background_music = background_music * loops
        
        # --- Vytvoření jednotlivých segmentů ---
        print("Vytvářím jednotlivé segmenty...")

        # Segment 1: Úvod (4 sekundy, plná hlasitost)
        intro_segment = background_music[0:INTRO_DURATION_MS]

        # Segment 2: Hlavní část pod řečí
        main_segment_start = INTRO_DURATION_MS
        main_segment_end = INTRO_DURATION_MS + tts_duration_ms
        main_segment_music = background_music[main_segment_start:main_segment_end]
        
        # Ztlumení hlavní části a překrytí řečí
        print(f"Aplikuji ducking ({DUCKING_DB} dB) na hlavní část...")
        ducked_main_segment = main_segment_music.apply_gain(DUCKING_DB)
        main_with_tts = ducked_main_segment.overlay(tts_audio)

        # Segment 3: Závěr (3 sekundy, plná hlasitost)
        outro_segment_start = main_segment_end
        outro_segment_end = main_segment_end + OUTRO_DURATION_MS
        outro_segment = background_music[outro_segment_start:outro_segment_end]

        # --- Spojení segmentů s plynulými přechody (Crossfade) ---
        print(f"Spojuji segmenty s plynulým přechodem ({CROSSFADE_DURATION_MS}ms)...")

        # Spojení intra s hlavní částí
        # .append() s crossfade zajistí plynulý přechod z hlasité do tiché
        part1 = intro_segment.append(main_with_tts, crossfade=CROSSFADE_DURATION_MS)

        # Spojení výsledku s outrem
        # .append() s crossfade zde zajistí plynulý přechod z tiché do hlasité
        final_audio_unfaded = part1.append(outro_segment, crossfade=CROSSFADE_DURATION_MS)

        # --- Finální úpravy ---
        print(f"Aplikuji finální fade-out ({FADEOUT_DURATION_MS}ms)...")
        final_audio = final_audio_unfaded.fade_out(duration=FADEOUT_DURATION_MS)

        # Export finálního souboru
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