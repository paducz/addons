# Mix Audio with Ducking Add-on

## Co dělá
- Vygeneruje první stopu přes ElevenLabs TTS
- Smíchá ji s hudbou (background music)
- Přidá efekty: intro, ducking, outro, fade-out

## Instalace
1. Nakopíruj složku `mix_audio_ducking` do `addons/local/` v Home Assistantu
2. V Add-on Store najdi "Mix Audio with Ducking" → Nainstaluj
3. Nastav `eleven_key` (API klíč z ElevenLabs) a volitelně `auth_token`
4. Spusť add-on

## Volání API
POST na `/mix` s JSON:
{
  "text1": "Ahoj světe",
  "file2": "background.mp3",
  "output": "final.mp3",
  "duck_db": -12,
  "intro_ms": 1000,
  "outro_ms": 1000,
  "fade_out_ms": 2000
}
