import argparse
import os
import logging
import requests
from aiohttp import web
from pydub import AudioSegment

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mix-addon")

ELEVENLABS_API_URL = "https://api.elevenlabs.io/v1/text-to-speech"

def generate_tts(text, output_path, api_key, voice_id="21m00Tcm4TlvDq8ikWAM"):
    headers = {
        "xi-api-key": api_key,
        "Content-Type": "application/json"
    }
    payload = {
        "text": text,
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {
            "stability": 0.3,
            "similarity_boost": 0.7
        }
    }
    url = f"{ELEVENLABS_API_URL}/{voice_id}"
    logger.info(f"Generating TTS for text: {text[:30]}...")
    resp = requests.post(url, json=payload, headers=headers)
    resp.raise_for_status()
    with open(output_path, "wb") as f:
        f.write(resp.content)
    logger.info(f"TTS saved to {output_path}")
    return output_path

def smart_mix_with_ducking(bg_path, tts_path, output_path,
                            duck_db=-10.0, intro_ms=1000, outro_ms=1000, fade_out_ms=1000):
    bg = AudioSegment.from_file(bg_path)
    tts = AudioSegment.from_file(tts_path)

    # Ensure bg long enough: if background shorter than needed, loop it
    total_needed = intro_ms + len(tts) + outro_ms
    if len(bg) < total_needed:
        # loop bg to reach required length
        times = (total_needed // len(bg)) + 1
        bg = bg * times

    intro = bg[:intro_ms]
    bg_ducked = bg[intro_ms:intro_ms + len(tts)] + duck_db
    outro_start = intro_ms + len(tts)
    outro = bg[outro_start:outro_start + outro_ms]

    part_with_tts = bg_ducked.overlay(tts)
    final = intro + part_with_tts + outro
    final = final.fade_out(fade_out_ms)

    ext = os.path.splitext(output_path)[1].lower().lstrip('.') or 'mp3'
    final.export(output_path, format=ext)
    return output_path

async def handle_mix(request):
    token = request.app['auth_token']
    if token:
        header = request.headers.get('Authorization', '')
        if header != f'Bearer {token}':
            return web.json_response({'ok': False, 'error': 'Unauthorized'}, status=401)

    data = await request.json()
    audio_dir = request.app['audio_dir']
    eleven_key = request.app['eleven_key']

    text1 = data.get('text1')
    file2 = data.get('file2')
    output = data.get('output', 'final_mix.mp3')
    voice_id = data.get('voice_id', '21m00Tcm4TlvDq8ikWAM')

    duck_db = float(data.get('duck_db', -10.0))
    intro_ms = int(data.get('intro_ms', 1000))
    outro_ms = int(data.get('outro_ms', 1000))
    fade_out_ms = int(data.get('fade_out_ms', 1000))

    if not text1 or not file2:
        return web.json_response({'ok': False, 'error': 'text1 and file2 required'}, status=400)

    file1_path = os.path.join(audio_dir, 'tts1.mp3')
    try:
        generate_tts(text1, file1_path, eleven_key, voice_id)
    except Exception as e:
        logger.exception('TTS generation failed')
        return web.json_response({'ok': False, 'error': str(e)}, status=500)

    p2 = os.path.join(audio_dir, file2)
    if not os.path.isfile(p2):
        return web.json_response({'ok': False, 'error': 'background music file not found'}, status=404)

    outp = os.path.join(audio_dir, output)
    try:
        smart_mix_with_ducking(
            bg_path=p2,
            tts_path=file1_path,
            output_path=outp,
            duck_db=duck_db,
            intro_ms=intro_ms,
            outro_ms=outro_ms,
            fade_out_ms=fade_out_ms
        )
    except Exception as e:
        logger.exception('Mix failed')
        return web.json_response({'ok': False, 'error': str(e)}, status=500)

    return web.json_response({'ok': True, 'output': output})

async def handle_health(request):
    return web.json_response({'ok': True})

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--audio-dir', default='/share/audio')
    parser.add_argument('--port', type=int, default=8080)
    parser.add_argument('--auth', default='')
    parser.add_argument('--eleven-key', default='')
    args = parser.parse_args()

    app = web.Application()
    app['audio_dir'] = args.audio_dir
    app['auth_token'] = args.auth
    app['eleven_key'] = args.eleven_key

    app.router.add_post('/mix', handle_mix)
    app.router.add_get('/health', handle_health)

    web.run_app(app, port=args.port, host='0.0.0.0')

if __name__ == '__main__':
    main()
