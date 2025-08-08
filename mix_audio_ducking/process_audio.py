#!/usr/bin/env python3
import sys
import os
from pydub import AudioSegment
from elevenlabs.client import ElevenLabs

# --- Konfigurace efektů ---
INTRO_DURATION_MS = 1000      # 1 sekunda
OUTRO_DURATION_MS = 1000      # 1 sekunda
FADEOUT_DURATION_MS = 1000    # Finální zeslabení celého klipu
# O kolik decibelů ztlumit hudbu během řeči. Záporné číslo znamená ztlumení.
DUCKING_DB = -15
# Délka přechodu (fade) pro ducking efekt. Zajišťuje plynulost.
DUCKING_FADE_MS = 250

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
        
        # Ořízneme hudbu na přesnou potřebnou délku
        final_music = background_music[:required_length]

        # --- Aplikace plynulého duckingu s přechody (crossfading) ---
        
        # 1. Plynulé zeslabení před začátkem řeči
        print("Vytvářím plynulé intro...")
        start_of_tts = INTRO_DURATION_MS
        final_mix = final_music.fade(
            to_gain=DUCKING_DB,
            start=start_of_tts - DUCKING_FADE_MS,
            duration=DUCKING_FADE_MS # OPRAVA: Odstraněn argument 'end'
        )

        # 2. Plynulé zesílení po skončení řeči
        print("Vytvářím plynulé outro...")
        end_of_tts = INTRO_DURATION_MS + tts_duration_ms
        final_mix = final_mix.fade(
            from_gain=DUCKING_DB,
            start=end_of_tts,
            duration=DUCKING_FADE_MS # OPRAVA: Odstraněn argument 'end'
        )
        
        # 3. Překrytí řečí
        print("Překrývám hudbu řečí...")
        final_mix = final_mix.overlay(tts_audio, position=INTRO_DURATION_MS)

        # 4. Finální zeslabení (fade-out) na konci celé stopy
        print(f"Aplikuji finální fade-out ({FADEOUT_DURATION_MS}ms)...")
        final_mix = final_mix.fade_out(duration=FADEOUT_DURATION_MS)

        # 5. Export finálního souboru
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