#!/usr/bin/env python3
import sys
import os
from pydub import AudioSegment
from elevenlabs.client import ElevenLabs

# --- KONFIGURACE EFEKTŮ ---
# Přesně podle vaší specifikace
INTRO_STABLE_MS = 4000      # Délka úvodní hudby na plnou hlasitost
OUTRO_STABLE_MS = 3000      # Délka závěrečné hudby na plnou hlasitost
TRANSITION_FADE_MS = 500    # Délka plynulého přechodu (fade in/out) pro ducking
FADEOUT_DURATION_MS = 1000    # Finální zeslabení celého klipu na konci
DUCKING_DB = -18              # O kolik decibelů ztlumit hudbu

# Cesta k dočasnému souboru pro TTS
TTS_TEMP_FILE = "/tmp/tts.mp3"

def main():
    # --- 1. Načtení argumentů ---
    if len(sys.argv) != 6:
        print(f"Chyba: Očekáváno 5 argumentů, přijato {len(sys.argv) - 1}")
        sys.exit(1)
    api_key, voice_id, music_path, text_to_speak, output_path = sys.argv[1:6]
    print(f"Argumenty úspěšně načteny. Cílový soubor: {output_path}")

    # --- 2. Generování TTS ---
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
        required_length = INTRO_STABLE_MS + TRANSITION_FADE_MS + tts_duration_ms + TRANSITION_FADE_MS + OUTRO_STABLE_MS
        if len(background_music) < required_length:
            print("Hudba je příliš krátká, bude započata smyčka.")
            loops = (required_length // len(background_music)) + 1
            background_music = background_music * loops

        # --- Definice časových bodů ---
        print("Počítám časové body...")
        t1 = INTRO_STABLE_MS                          # Konec stabilního intra
        t2 = t1 + TRANSITION_FADE_MS                  # Konec fade-out přechodu
        t3 = t2 + tts_duration_ms                     # Konec hlavní ztlumené části
        t4 = t3 + TRANSITION_FADE_MS                  # Konec fade-in přechodu
        t5 = t4 + OUTRO_STABLE_MS                     # Konec stabilního outra
        print(f"Časové body (v ms): t1={t1}, t2={t2}, t3={t3}, t4={t4}, t5={t5}")

        # --- Vytvoření 5 přesných segmentů hudby ---
        print("Vytvářím 5 hudebních segmentů...")

        # Segment 1: Stabilní Intro (plná hlasitost)
        intro_part = background_music[0:t1]

        # Segment 2: Přechod Fade Out
        fade_out_source = background_music[t1:t2]
        # Fade z 0dB (původní hlasitost) na DUCKING_DB
        fade_out_part = fade_out_source.fade(from_gain=0, to_gain=DUCKING_DB, duration=TRANSITION_FADE_MS)
        assert isinstance(fade_out_part, AudioSegment), "Selhalo vytvoření 'fade_out_part'."
        
        # Segment 3: Hlavní část (ztlumená)
        main_ducked_part = background_music[t2:t3].apply_gain(DUCKING_DB)
        
        # Segment 4: Přechod Fade In
        fade_in_source = background_music[t3:t4]
        # Fade z DUCKING_DB zpět na 0dB (původní hlasitost)
        fade_in_part = fade_in_source.fade(from_gain=DUCKING_DB, to_gain=0, duration=TRANSITION_FADE_MS)
        assert isinstance(fade_in_part, AudioSegment), "Selhalo vytvoření 'fade_in_part'."
        
        # Segment 5: Stabilní Outro (plná hlasitost)
        outro_part = background_music[t4:t5]

        # --- Spojení hudebních segmentů do jednoho celku ---
        print("Spojuji hudební segmenty...")
        final_background = intro_part + fade_out_part + main_ducked_part + fade_in_part + outro_part
        
        # --- Překrytí řečí na správné místo ---
        # Řeč začíná přesně na začátku stabilní ztlumené části
        tts_position = t2
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