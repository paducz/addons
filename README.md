# My Home Assistant Add-ons

Tento repozitář obsahuje vlastní Home Assistant add-on:

## mix_audio_ducking
Generuje první audio přes ElevenLabs TTS a smíchá ji s podkladovou hudbou.

### Efekty:
- 1s hudba před řečí
- ducking během řeči (ztlumení hudby)
- 1s hudba po řeči
- fade-out na konci

### Instalace
1. V Home Assistant → Supervisor → Add-on Store → Repositories
2. Přidej: `https://github.com/tvoje_username/my-ha-addons`
3. Nainstaluj *Mix Audio with Ducking*
4. Vlož svůj ElevenLabs API klíč a spusť

### Volání API `/mix`
```json
{
  "text1": "Ahoj světe",
  "file2": "hudba.mp3",
  "output": "final_mix.mp3",
  "duck_db": -12,
  "intro_ms": 1000,
  "outro_ms": 1000,
  "fade_out_ms": 2000
}
```
