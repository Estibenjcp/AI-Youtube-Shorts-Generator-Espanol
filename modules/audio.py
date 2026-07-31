import os
import re
import asyncio
import subprocess
import edge_tts
from mutagen.mp3 import MP3

# Target peak level for all audio clips (dB). -3 leaves headroom without clipping.
_TARGET_PEAK_DB = -3.0

# Silencio de cabeza/cola que el TTS deja en cada clip. Sin recortarlo, el
# acrossfade del composer solapa cola-de-N con cabeza-de-N+1 (silencio + silencio)
# y aparece un bache de silencio digital audible en cada corte de escena.
_TRIM_THRESHOLD_DB = -45.0   # por debajo de esto se considera silencio
_TRIM_MIN_SILENCE  = 0.06    # no molestarse si hay menos de 60 ms
_TRIM_LEAD_CUSHION = 0.03    # deja 30 ms antes de la primera palabra
_TRIM_TAIL_CUSHION = 0.06    # deja 60 ms tras la ultima palabra


def _trim_edge_silence(path: str) -> float:
    """Recorta el silencio inicial y final de un clip de voz, sobre el mismo archivo.

    Devuelve los segundos eliminados AL PRINCIPIO, para que quien llame pueda
    desplazar los timings por palabra esa misma cantidad (si no, los subtitulos
    se desincronizan). Devuelve 0.0 si no habia nada que recortar o si algo
    fallo: en ese caso el archivo original se deja intacto.
    """
    if not path or not os.path.exists(path):
        return 0.0
    try:
        probe = subprocess.run(
            ['ffmpeg', '-i', path, '-af',
             f'silencedetect=noise={_TRIM_THRESHOLD_DB}dB:d=0.03', '-f', 'null', '-'],
            capture_output=True, text=True, errors='replace', timeout=20,
        )
        err = probe.stderr
        dur_m = re.search(r'Duration:\s*(\d+):(\d+):([\d.]+)', err)
        if not dur_m:
            return 0.0
        duration = int(dur_m.group(1)) * 3600 + int(dur_m.group(2)) * 60 + float(dur_m.group(3))

        starts = [float(m) for m in re.findall(r'silence_start:\s*([-\d.]+)', err)]
        ends   = [float(m) for m in re.findall(r'silence_end:\s*([\d.]+)', err)]

        # Silencio inicial: solo si el primer tramo de silencio arranca pegado al 0.
        lead = 0.0
        if starts and ends and starts[0] <= 0.05:
            lead = max(0.0, ends[0] - _TRIM_LEAD_CUSHION)

        # Silencio final: el ultimo tramo de silencio debe llegar al final del
        # archivo. Segun la version, ffmpeg lo deja sin cerrar O lo cierra con un
        # silence_end justo en el EOF — hay que aceptar las dos formas.
        tail = duration
        if starts:
            _sin_cerrar   = (not ends) or (starts[-1] > ends[-1])
            _cierra_en_eof = (bool(ends) and starts[-1] < ends[-1]
                              and abs(ends[-1] - duration) <= 0.06)
            if _sin_cerrar or _cierra_en_eof:
                tail = min(duration, starts[-1] + _TRIM_TAIL_CUSHION)

        if lead < _TRIM_MIN_SILENCE and (duration - tail) < _TRIM_MIN_SILENCE:
            return 0.0

        keep = tail - lead
        if keep <= 0.20:            # clip practicamente vacio: no tocarlo
            return 0.0

        root, ext = os.path.splitext(path)
        tmp = f"{root}.trim{ext or '.mp3'}"
        if os.path.exists(tmp):
            try:
                os.remove(tmp)
            except Exception:
                pass

        cmd = ['ffmpeg', '-ss', f'{lead:.3f}', '-t', f'{keep:.3f}', '-i', path]
        if (ext or '').lower() == '.mp3':
            cmd += ['-c:a', 'libmp3lame', '-q:a', '2']
        cmd += ['-y', tmp]
        proc = subprocess.run(cmd, capture_output=True, timeout=60)

        if proc.returncode == 0 and os.path.exists(tmp) and os.path.getsize(tmp) > 1024:
            os.replace(tmp, path)
            if lead > 0.001 or (duration - tail) > 0.001:
                print(f"      ✂️  Silencio recortado: {lead*1000:.0f} ms inicio / "
                      f"{(duration - tail)*1000:.0f} ms final")
            return lead
        if os.path.exists(tmp):
            try:
                os.remove(tmp)
            except Exception:
                pass
        return 0.0
    except Exception as e:
        print(f"      ⚠️ Recorte de silencio omitido: {e}")
        return 0.0


def _shift_word_times(word_times: list, lead: float) -> list:
    """Desplaza los timings por palabra tras recortar `lead` segundos del inicio."""
    if not word_times or lead <= 0.001:
        return word_times
    for w in word_times:
        w['start'] = round(max(0.0, w.get('start', 0.0) - lead), 4)
        w['end']   = round(max(0.0, w.get('end', 0.0) - lead), 4)
    return word_times

class AudioEngine:
    def __init__(self, voice: str = "en-US-AvaNeural", rate: str = "+10%", voice_b: str = ""):
        self.voice   = voice
        self.voice_b = voice_b   # voz del "guest" / hablante B
        self.rate = rate
        self.output_dir = os.path.join(os.getcwd(), "assets", "audio_clips")
        os.makedirs(self.output_dir, exist_ok=True)

    def _normalize(self, path: str) -> None:
        """
        Measures the peak volume of an MP3 with ffmpeg volumedetect,
        then applies the exact gain needed to bring it to TARGET_PEAK_DB.
        SAFE: only replaces the original if the normalized file is valid.
        """
        try:
            result = subprocess.run(
                ['ffmpeg', '-i', path, '-af', 'volumedetect', '-f', 'null', '-'],
                capture_output=True, text=True, errors='replace'
            )
            match = re.search(r'max_volume:\s*([-\d.]+)\s*dB', result.stderr)
            if not match:
                return
            max_vol = float(match.group(1))
            gain = _TARGET_PEAK_DB - max_vol
            if abs(gain) < 0.3:
                return  # Already close enough — skip re-encode

            tmp = path + '.norm.mp3'

            # Remove stale tmp if it exists
            if os.path.exists(tmp):
                try:
                    os.remove(tmp)
                except Exception:
                    pass

            proc = subprocess.run(
                ['ffmpeg', '-i', path, '-af', f'volume={gain:.2f}dB', '-y', tmp],
                capture_output=True
            )

            # Only replace if ffmpeg succeeded AND the output file has content
            if proc.returncode == 0 and os.path.exists(tmp) and os.path.getsize(tmp) > 1024:
                os.replace(tmp, path)
            else:
                # Normalization failed — clean up tmp and keep original
                if os.path.exists(tmp):
                    try:
                        os.remove(tmp)
                    except Exception:
                        pass
                print(f"      ⚠️ Normalization skipped — keeping original audio.")

        except Exception as e:
            print(f"      ⚠️ Normalization skipped: {e}")

    @staticmethod
    def _clean_text(text: str) -> str:
        """Sanitize text before sending to Edge TTS.
        - Removes newlines/tabs (confuse TTS, cause dropped words)
        - Replaces '...' with a comma+space so TTS pauses naturally
        - Replaces \u00f1/\u00d1 with n/N as fallback (some voices mispronounce \u00f1)
        - Collapses multiple spaces
        """
        text = text.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
        text = text.replace('...', ',')
        text = text.replace('\u2026', ',')
        # \u00f1 fallback \u2014 LLM should avoid it but this catches any that slip through
        text = text.replace('\u00f1', 'n').replace('\u00d1', 'N')
        text = re.sub(r'\s{2,}', ' ', text)
        text = re.sub(r',\s*,', ',', text)
        return text.strip()

    @staticmethod
    def _adjust_rate(rate_str: str, delta: int) -> str:
        """Adjust a TTS rate string by delta percentage points. E.g. '+10%' + 8 → '+18%'"""
        m = re.match(r'([+-]?\d+)%', rate_str.strip())
        if m:
            val = int(m.group(1)) + delta
            return f"+{val}%" if val >= 0 else f"{val}%"
        return rate_str

    @staticmethod
    async def _stream_tts(communicate, output_path: str) -> list:
        """Stream Edge TTS to file and capture WordBoundary timing events.
        Returns list of {'word', 'start', 'end'} dicts (times in seconds)."""
        word_times = []
        with open(output_path, 'wb') as f:
            async for chunk in communicate.stream():
                if chunk['type'] == 'audio':
                    f.write(chunk['data'])
                elif chunk['type'] == 'WordBoundary':
                    # offset/duration are in 100-nanosecond units
                    start = chunk['offset'] / 10_000_000
                    dur   = chunk['duration'] / 10_000_000
                    word_times.append({
                        'word':  chunk['text'],
                        'start': round(start, 4),
                        'end':   round(start + dur, 4),
                    })
        return word_times

    async def generate_audio(self, text, output_filename, retries=3, rate_override=None, voice_override=None):
        """
        Generates MP3 with retry logic to handle connection drops.
        After generation, verifies the file has valid duration.
        Falls back to no-normalization if file gets corrupted.
        Also saves word-level timing to {output_path}.words.json for subtitle sync.
        """
        import json as _json
        output_path = os.path.join(self.output_dir, output_filename)

        for attempt in range(retries):
            try:
                effective_rate = rate_override if rate_override is not None else self.rate
                _voice = voice_override if voice_override else self.voice
                communicate = edge_tts.Communicate(text, _voice, rate=effective_rate)
                word_times = await self._stream_tts(communicate, output_path)

                # Recortar silencio de cabeza/cola ANTES de guardar el timing:
                # si se quita silencio inicial hay que desplazar los tiempos la
                # misma cantidad o los subtitulos quedan adelantados.
                _lead = _trim_edge_silence(output_path)
                word_times = _shift_word_times(word_times, _lead)

                # Save word timing alongside audio for subtitle sync
                if word_times:
                    with open(output_path + '.words.json', 'w', encoding='utf-8') as tf:
                        _json.dump(word_times, tf, ensure_ascii=False)

                # Verify the file is valid BEFORE normalization
                pre_duration = self.get_audio_duration(output_path)
                if pre_duration <= 0:
                    raise ValueError(f"TTS produced empty/invalid audio (duration={pre_duration})")

                # Normalize volume — safe version checks file integrity
                self._normalize(output_path)

                # Verify the file is STILL valid AFTER normalization
                post_duration = self.get_audio_duration(output_path)
                if post_duration <= 0:
                    # Normalization corrupted it — regenerate clean copy
                    print(f"      ⚠️ File corrupted by normalization — regenerating clean copy...")
                    communicate2 = edge_tts.Communicate(text, _voice, rate=effective_rate)
                    await self._stream_tts(communicate2, output_path)

                return output_path

            except Exception as e:
                print(f"      ⚠️ Audio Error (Attempt {attempt+1}/{retries}): {e}")
                if attempt < retries - 1:
                    await asyncio.sleep(2)
                else:
                    print("      ❌ Failed to generate audio after max retries.")
                    raise e

    def get_audio_duration(self, file_path):
        try:
            audio = MP3(file_path)
            return audio.info.length
        except Exception as e:
            print(f"❌ Error reading audio length: {e}")
            return 0.0

    async def process_script(self, script_data):
        print(f"🎙️ Starting Audio Generation for {len(script_data)} scenes...")
        total_scenes = len(script_data)
        sem = asyncio.Semaphore(3)   # límite de concurrencia (respeta rate limits)

        async def _one(idx, scene):
            scene_id = scene['id']
            text = self._clean_text(scene.get('text', ''))
            if not text:
                print(f"   ⚠️ Scene {scene_id} has empty text — skipping.")
                return
            filename = f"voice_{scene_id}.mp3"

            # Mood "energetic" → todas las escenas al ritmo de hook (+8%)
            # Hook scenes (1-2): +8% faster → urgency; CTA (last): -5% → clarity
            _mood = scene.get('mood', '')
            if _mood == 'energetic':
                scene_rate = self._adjust_rate(self.rate, +8)   # rápido en todo el video
            elif idx < 2:
                scene_rate = self._adjust_rate(self.rate, +8)
            elif idx >= total_scenes - 1:
                scene_rate = self._adjust_rate(self.rate, -5)
            else:
                scene_rate = self.rate

            async with sem:
                try:
                    # Soporte de dos voces para modo podcast/diálogo
                    _speaker = scene.get("speaker", "host")
                    _voice_override = None
                    if self.voice_b and _speaker in ("guest", "b", "invitado"):
                        _voice_override = self.voice_b

                    file_path = await self.generate_audio(text, filename, rate_override=scene_rate, voice_override=_voice_override)
                    duration  = self.get_audio_duration(file_path)

                    if duration <= 0:
                        print(f"   ❌ Scene {scene_id}: audio duration is 0 after generation — skipping.")
                        return

                    scene['audio_path'] = file_path
                    scene['duration']   = duration
                    print(f"   ✅ Scene {scene_id}: {duration:.2f}s generated.")

                except Exception as e:
                    print(f"   ❌ Skipping Scene {scene_id} due to audio error: {e}")

        await asyncio.gather(*[_one(idx, scene) for idx, scene in enumerate(script_data)])
        return script_data


class VoxCPMAudioEngine:
    """High-quality local TTS using VoxCPM2 (2B-parameter model, GPU required).
    Requires: pip install voxcpm soundfile
    Voice adapts automatically to each scene's 'mood' field."""

    # Voice descriptions per mood and language
    MOOD_VOICES = {
        "es": {
            "exciting":     "(narrador masculino, energico, rapido, espanol latino neutro)",
            "dramatic":     "(narrador masculino, voz grave y profunda, lento y pausado, espanol)",
            "calm":         "(narrador masculino, sereno, tranquilo, claro, espanol neutro)",
            "mysterious":   "(narrador masculino, susurro tenso, misterioso y oscuro, espanol)",
            "informative":  "(narrador masculino, claro y periodistico, profesional, espanol neutro)",
            "fun":          "(narrador masculino, alegre, dinamico, juvenil, espanol)",
            "inspiring":    "(narrador masculino, inspirador y motivador, potente, espanol)",
            "professional": "(narrador masculino, formal y profesional, espanol neutro)",
            "energetic":    "(narrador masculino, muy energico, entusiasta, espanol latino)",
        },
        "en": {
            "exciting":     "(male narrator, energetic, fast-paced, clear American English)",
            "dramatic":     "(male narrator, deep grave voice, slow and dramatic, English)",
            "calm":         "(male narrator, calm, soothing, measured pace, English)",
            "mysterious":   "(male narrator, tense whisper, mysterious and dark, English)",
            "informative":  "(male narrator, clear journalistic delivery, professional English)",
            "fun":          "(male narrator, upbeat, enthusiastic, youthful energy, English)",
            "inspiring":    "(male narrator, inspiring, powerful, motivational, English)",
            "professional": "(male narrator, formal and professional tone, English)",
            "energetic":    "(male narrator, very energetic, enthusiastic, English)",
        },
    }

    def __init__(self, voice_description: str = "", lang: str = "es",
                 mood_enabled: bool = True, reference_audio: str = ""):
        """
        voice_description: global override (empty = use mood-based voices)
        lang: "es" or "en"
        mood_enabled: if True, use different voice per scene mood
        reference_audio: path to a WAV/MP3 for voice cloning (optional)
        """
        try:
            from voxcpm import VoxCPM as _VoxCPM
            self._VoxCPM = _VoxCPM
        except ImportError:
            raise ImportError(
                "VoxCPM no esta instalado. Ejecuta: pip install voxcpm soundfile"
            )

        self.voice_description  = voice_description.strip()
        self.lang               = lang
        self.mood_enabled       = mood_enabled
        self.reference_audio    = reference_audio.strip()
        self.output_dir         = os.path.join(os.getcwd(), "assets", "audio_clips")
        os.makedirs(self.output_dir, exist_ok=True)
        self._model             = None   # lazy-load on first use
        self._model_load_failed = False  # prevent re-attempting after failure

    def _get_model(self):
        if self._model_load_failed:
            raise RuntimeError(
                "[VoxCPM] Modelo no disponible. Revisa los logs del pipeline para instrucciones."
            )
        if self._model is None:
            print("[VoxCPM] Cargando modelo (primera vez — puede tardar un minuto)...")

            # Strategy 1: patch ModelScope download to skip the denoiser
            model = self._try_load_with_patch()
            if model is not None:
                self._model = model
                print("[VoxCPM] Modelo listo (sin denoiser de ModelScope).")
                return self._model

            # Strategy 2: normal load (works if user has ModelScope token)
            try:
                self._model = self._VoxCPM.from_pretrained("openbmb/VoxCPM2")
                print("[VoxCPM] Modelo listo.")
                return self._model
            except Exception as e:
                self._model_load_failed = True
                print(
                    "\n[VoxCPM] ERROR: No se pudo cargar el modelo.\n"
                    "El denoiser de speech_zipenhancer esta bloqueado (requiere cuenta ModelScope).\n"
                    "\n--- SOLUCION ---\n"
                    "1. Crea una cuenta GRATIS en: https://modelscope.cn\n"
                    "2. Ve a: https://modelscope.cn/my/myaccesstoken  y copia tu token\n"
                    "3. Ejecuta en Python UNA SOLA VEZ:\n"
                    "   from modelscope.hub.api import HubApi\n"
                    "   HubApi().login('TU_TOKEN_AQUI')\n"
                    "4. Reinicia la app\n"
                    "----------------\n"
                    f"Error original: {e}\n"
                )
                raise RuntimeError("[VoxCPM] Modelo no cargado — ver instrucciones en la consola.") from e
        return self._model

    def _try_load_with_patch(self):
        """Intenta cargar VoxCPM interceptando la descarga del denoiser de ModelScope.
        Si VoxCPM maneja el error internamente, el modelo carga sin denoiser."""
        _patches = []
        try:
            import modelscope.hub.snapshot_download as _sd_mod
            _orig_dl = _sd_mod.snapshot_download

            def _skip_denoiser_download(model_id='', *args, **kwargs):
                if isinstance(model_id, str) and (
                    'zipenhancer' in model_id.lower() or
                    'speech_zipenhancer' in model_id.lower()
                ):
                    print(f"[VoxCPM] Omitiendo denoiser: {model_id}")
                    raise Exception(f"Denoiser skipped: {model_id}")
                return _orig_dl(model_id, *args, **kwargs)

            _sd_mod.snapshot_download = _skip_denoiser_download
            _patches.append((_sd_mod, 'snapshot_download', _orig_dl))
        except Exception:
            return None  # modelscope not importable yet — skip this strategy

        try:
            model = self._VoxCPM.from_pretrained("openbmb/VoxCPM2")
            return model
        except Exception as e:
            print(f"[VoxCPM] Carga con patch fallo: {e}")
            return None
        finally:
            for _mod, _attr, _orig in _patches:
                try:
                    setattr(_mod, _attr, _orig)
                except Exception:
                    pass

    def _voice_for_scene(self, scene: dict) -> str:
        """Return voice description string for a scene."""
        if self.voice_description:
            return self.voice_description
        if self.mood_enabled:
            mood      = scene.get("mood", "informative").lower()
            lang_map  = self.MOOD_VOICES.get(self.lang, self.MOOD_VOICES["es"])
            return lang_map.get(mood, lang_map["informative"])
        # Fallback: neutral
        return "(narrador masculino, espanol neutro)" if self.lang == "es" else "(male narrator, English)"

    @staticmethod
    def _clean_text(text: str) -> str:
        text = text.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
        text = text.replace('...', ',').replace('\u2026', ',')
        text = text.replace('\u00f1', 'n').replace('\u00d1', 'N')
        text = re.sub(r'\s{2,}', ' ', text)
        text = re.sub(r',\s*,', ',', text)
        return text.strip()

    def _generate_wav(self, text: str, voice_desc: str, out_path: str) -> str:
        import soundfile as sf
        model     = self._get_model()
        full_text = f"{voice_desc} {text}"

        kwargs = {"cfg_value": 2.0}
        if self.reference_audio and os.path.exists(self.reference_audio):
            kwargs["prompt"] = self.reference_audio   # voice cloning

        wav = model.generate(full_text, **kwargs)
        sf.write(out_path, wav, 48000)
        # VoxCPM no produce word timing, asi que recortar no desincroniza nada.
        _trim_edge_silence(out_path)
        return out_path

    def get_audio_duration(self, file_path: str) -> float:
        try:
            import soundfile as sf
            info = sf.info(file_path)
            return float(info.duration)
        except Exception:
            try:
                # Fallback via ffprobe
                import subprocess, json
                r = subprocess.run(
                    ['ffprobe', '-v', 'quiet', '-print_format', 'json',
                     '-show_format', file_path],
                    capture_output=True, text=True
                )
                return float(json.loads(r.stdout)['format']['duration'])
            except Exception:
                return 0.0

    async def process_script(self, script_data: list) -> list:
        """Drop-in replacement for AudioEngine.process_script()."""
        total = len(script_data)
        print(f"🎙️ [VoxCPM] Generating audio for {total} scenes "
              f"({'mood-adaptive' if self.mood_enabled else 'fixed voice'})...")

        for idx, scene in enumerate(script_data):
            scene_id = scene["id"]
            text     = self._clean_text(scene.get("text", ""))
            if not text:
                print(f"   ⚠️ Scene {scene_id}: empty text — skipping.")
                continue

            voice_desc = self._voice_for_scene(scene)
            out_path   = os.path.join(self.output_dir, f"voice_{scene_id}.wav")

            try:
                print(f"   🎯 Scene {scene_id} [{scene.get('mood','?')}]: {text[:55]}...")
                self._generate_wav(text, voice_desc, out_path)
                duration = self.get_audio_duration(out_path)
                if duration <= 0:
                    print(f"   ❌ Scene {scene_id}: invalid audio — skipping.")
                    continue

                scene["audio_path"] = out_path
                scene["duration"]   = duration
                print(f"   ✅ Scene {scene_id}: {duration:.2f}s  voice='{voice_desc[:45]}...'")

            except Exception as e:
                print(f"   ❌ Scene {scene_id} error: {e}")
                continue

        return script_data


class GoogleTTSAudioEngine:
    """Google Cloud Text-to-Speech via REST API.
    Only requires a Google Cloud API key — no extra SDK needed.
    Supports Chirp3-HD, Journey, Studio, and Neural2 voices for ES and EN.
    """

    # label → (lang_code, voice_name)
    VOICES_ES = {
        # ── Chirp 3 HD (generación más nueva — nombres de estrellas) ──
        "Achernar     [Chirp3-HD · F · Suave, tono alto]":        ("es-US", "es-US-Chirp3-HD-Achernar"),
        "Achird       [Chirp3-HD · M · Amigable, tono medio-bajo]":("es-US", "es-US-Chirp3-HD-Achird"),
        "Algenib      [Chirp3-HD · M · Ronco, tono bajo]":         ("es-US", "es-US-Chirp3-HD-Algenib"),
        "Algieba      [Chirp3-HD · M · Suave, tono bajo]":         ("es-US", "es-US-Chirp3-HD-Algieba"),
        "Alnilam      [Chirp3-HD · M · Firme, tono medio-bajo]":   ("es-US", "es-US-Chirp3-HD-Alnilam"),
        "Aoede        [Chirp3-HD · F · Brisa, tono medio]":        ("es-US", "es-US-Chirp3-HD-Aoede"),
        "Autonoe      [Chirp3-HD · F · Brillante, tono medio]":    ("es-US", "es-US-Chirp3-HD-Autonoe"),
        "Callirrhoe   [Chirp3-HD · F]":                            ("es-US", "es-US-Chirp3-HD-Callirrhoe"),
        "Charon       [Chirp3-HD · M]":                            ("es-US", "es-US-Chirp3-HD-Charon"),
        "Despina      [Chirp3-HD · F]":                            ("es-US", "es-US-Chirp3-HD-Despina"),
        "Enceladus    [Chirp3-HD · M]":                            ("es-US", "es-US-Chirp3-HD-Enceladus"),
        "Erinome      [Chirp3-HD · F]":                            ("es-US", "es-US-Chirp3-HD-Erinome"),
        "Fenrir       [Chirp3-HD · M]":                            ("es-US", "es-US-Chirp3-HD-Fenrir"),
        "Gacrux       [Chirp3-HD · F]":                            ("es-US", "es-US-Chirp3-HD-Gacrux"),
        "Iapetus      [Chirp3-HD · M]":                            ("es-US", "es-US-Chirp3-HD-Iapetus"),
        "Kore         [Chirp3-HD · F]":                            ("es-US", "es-US-Chirp3-HD-Kore"),
        "Laomedeia    [Chirp3-HD · F]":                            ("es-US", "es-US-Chirp3-HD-Laomedeia"),
        "Leda         [Chirp3-HD · F]":                            ("es-US", "es-US-Chirp3-HD-Leda"),
        "Orus         [Chirp3-HD · M]":                            ("es-US", "es-US-Chirp3-HD-Orus"),
        "Pulcherrima  [Chirp3-HD · F]":                            ("es-US", "es-US-Chirp3-HD-Pulcherrima"),
        "Puck         [Chirp3-HD · M]":                            ("es-US", "es-US-Chirp3-HD-Puck"),
        "Rasalgethi   [Chirp3-HD · M]":                            ("es-US", "es-US-Chirp3-HD-Rasalgethi"),
        "Sadachbia    [Chirp3-HD · M]":                            ("es-US", "es-US-Chirp3-HD-Sadachbia"),
        "Sadaltager   [Chirp3-HD · M]":                            ("es-US", "es-US-Chirp3-HD-Sadaltager"),
        "Schedar      [Chirp3-HD · M]":                            ("es-US", "es-US-Chirp3-HD-Schedar"),
        "Sulafat      [Chirp3-HD · F]":                            ("es-US", "es-US-Chirp3-HD-Sulafat"),
        "Umbriel      [Chirp3-HD · M]":                            ("es-US", "es-US-Chirp3-HD-Umbriel"),
        "Vindemiatrix [Chirp3-HD · F]":                            ("es-US", "es-US-Chirp3-HD-Vindemiatrix"),
        "Zephyr       [Chirp3-HD · F]":                            ("es-US", "es-US-Chirp3-HD-Zephyr"),
        "Zubenelgenubi[Chirp3-HD · M]":                            ("es-US", "es-US-Chirp3-HD-Zubenelgenubi"),
        # ── Journey (generación 3.x — conversacional) ──
        "es-US-Journey-D  (Journey Masculino ★★★)":               ("es-US", "es-US-Journey-D"),
        "es-US-Journey-F  (Journey Femenina ★★★)":                ("es-US", "es-US-Journey-F"),
        "es-US-Journey-O  (Journey Femenina 2 ★★★)":              ("es-US", "es-US-Journey-O"),
        # ── Studio ──
        "es-US-Studio-B   (Studio Masculino ★★)":                 ("es-US", "es-US-Studio-B"),
        # ── Neural2 US ──
        "es-US-Neural2-B  (Masculino Latino ★)":                  ("es-US", "es-US-Neural2-B"),
        "es-US-Neural2-A  (Femenina Latina)":                      ("es-US", "es-US-Neural2-A"),
        "es-US-Neural2-C  (Femenina Latina 2)":                    ("es-US", "es-US-Neural2-C"),
        # ── Neural2 México ──
        "es-MX-Neural2-B  (Masculino México)":                    ("es-MX", "es-MX-Neural2-B"),
        "es-MX-Neural2-A  (Femenina México)":                     ("es-MX", "es-MX-Neural2-A"),
        "es-MX-Neural2-C  (Masculino México 2)":                  ("es-MX", "es-MX-Neural2-C"),
        # ── Neural2 España ──
        "es-ES-Neural2-B  (Masculino España)":                    ("es-ES", "es-ES-Neural2-B"),
        "es-ES-Neural2-A  (Femenina España)":                     ("es-ES", "es-ES-Neural2-A"),
        "es-ES-Neural2-C  (Femenina España 2)":                   ("es-ES", "es-ES-Neural2-C"),
        "es-ES-Neural2-D  (Masculino España 2)":                  ("es-ES", "es-ES-Neural2-D"),
        "es-ES-Neural2-E  (Femenina España 3)":                   ("es-ES", "es-ES-Neural2-E"),
        "es-ES-Neural2-F  (Masculino España 3)":                  ("es-ES", "es-ES-Neural2-F"),
    }

    VOICES_EN = {
        # ── Chirp 3 HD ──
        "Achernar     [Chirp3-HD · F · Soft, higher pitch]":         ("en-US", "en-US-Chirp3-HD-Achernar"),
        "Achird       [Chirp3-HD · M · Friendly, lower-mid pitch]":  ("en-US", "en-US-Chirp3-HD-Achird"),
        "Algenib      [Chirp3-HD · M · Gravelly, lower pitch]":      ("en-US", "en-US-Chirp3-HD-Algenib"),
        "Algieba      [Chirp3-HD · M · Smooth, lower pitch]":        ("en-US", "en-US-Chirp3-HD-Algieba"),
        "Alnilam      [Chirp3-HD · M · Firm, lower-mid pitch]":      ("en-US", "en-US-Chirp3-HD-Alnilam"),
        "Aoede        [Chirp3-HD · F · Breezy, mid pitch]":          ("en-US", "en-US-Chirp3-HD-Aoede"),
        "Autonoe      [Chirp3-HD · F · Bright, mid pitch]":          ("en-US", "en-US-Chirp3-HD-Autonoe"),
        "Callirrhoe   [Chirp3-HD · F]":                              ("en-US", "en-US-Chirp3-HD-Callirrhoe"),
        "Charon       [Chirp3-HD · M]":                              ("en-US", "en-US-Chirp3-HD-Charon"),
        "Despina      [Chirp3-HD · F]":                              ("en-US", "en-US-Chirp3-HD-Despina"),
        "Enceladus    [Chirp3-HD · M]":                              ("en-US", "en-US-Chirp3-HD-Enceladus"),
        "Erinome      [Chirp3-HD · F]":                              ("en-US", "en-US-Chirp3-HD-Erinome"),
        "Fenrir       [Chirp3-HD · M]":                              ("en-US", "en-US-Chirp3-HD-Fenrir"),
        "Gacrux       [Chirp3-HD · F]":                              ("en-US", "en-US-Chirp3-HD-Gacrux"),
        "Iapetus      [Chirp3-HD · M]":                              ("en-US", "en-US-Chirp3-HD-Iapetus"),
        "Kore         [Chirp3-HD · F]":                              ("en-US", "en-US-Chirp3-HD-Kore"),
        "Laomedeia    [Chirp3-HD · F]":                              ("en-US", "en-US-Chirp3-HD-Laomedeia"),
        "Leda         [Chirp3-HD · F]":                              ("en-US", "en-US-Chirp3-HD-Leda"),
        "Orus         [Chirp3-HD · M]":                              ("en-US", "en-US-Chirp3-HD-Orus"),
        "Pulcherrima  [Chirp3-HD · F]":                              ("en-US", "en-US-Chirp3-HD-Pulcherrima"),
        "Puck         [Chirp3-HD · M]":                              ("en-US", "en-US-Chirp3-HD-Puck"),
        "Rasalgethi   [Chirp3-HD · M]":                              ("en-US", "en-US-Chirp3-HD-Rasalgethi"),
        "Sadachbia    [Chirp3-HD · M]":                              ("en-US", "en-US-Chirp3-HD-Sadachbia"),
        "Sadaltager   [Chirp3-HD · M]":                              ("en-US", "en-US-Chirp3-HD-Sadaltager"),
        "Schedar      [Chirp3-HD · M]":                              ("en-US", "en-US-Chirp3-HD-Schedar"),
        "Sulafat      [Chirp3-HD · F]":                              ("en-US", "en-US-Chirp3-HD-Sulafat"),
        "Umbriel      [Chirp3-HD · M]":                              ("en-US", "en-US-Chirp3-HD-Umbriel"),
        "Vindemiatrix [Chirp3-HD · F]":                              ("en-US", "en-US-Chirp3-HD-Vindemiatrix"),
        "Zephyr       [Chirp3-HD · F]":                              ("en-US", "en-US-Chirp3-HD-Zephyr"),
        "Zubenelgenubi[Chirp3-HD · M]":                              ("en-US", "en-US-Chirp3-HD-Zubenelgenubi"),
        # ── Journey ──
        "en-US-Journey-D  (Journey Male ★★★)":                      ("en-US", "en-US-Journey-D"),
        "en-US-Journey-F  (Journey Female ★★★)":                    ("en-US", "en-US-Journey-F"),
        "en-US-Journey-O  (Journey Female 2 ★★★)":                  ("en-US", "en-US-Journey-O"),
        # ── Studio ──
        "en-US-Studio-Q   (Studio Male ★★)":                        ("en-US", "en-US-Studio-Q"),
        "en-US-Studio-O   (Studio Female ★★)":                      ("en-US", "en-US-Studio-O"),
        # ── Neural2 ──
        "en-US-Neural2-D  (Male, US ★)":                            ("en-US", "en-US-Neural2-D"),
        "en-US-Neural2-A  (Female, US)":                             ("en-US", "en-US-Neural2-A"),
        "en-US-Neural2-F  (Female, US 2)":                           ("en-US", "en-US-Neural2-F"),
        "en-US-Neural2-J  (Male, US 2)":                             ("en-US", "en-US-Neural2-J"),
        "en-US-Neural2-I  (Male, US 3)":                             ("en-US", "en-US-Neural2-I"),
        "en-US-Neural2-G  (Female, US 3)":                           ("en-US", "en-US-Neural2-G"),
        "en-US-Neural2-H  (Female, US 4)":                           ("en-US", "en-US-Neural2-H"),
    }

    _URL      = "https://texttospeech.googleapis.com/v1/text:synthesize"
    _URL_BETA = "https://texttospeech.googleapis.com/v1beta1/text:synthesize"

    def __init__(self, api_key: str, voice_name: str, lang_code: str,
                 speaking_rate: float = 1.0, pitch: float = 0.0):
        if not api_key:
            raise ValueError("Google TTS API key is required.")
        self.api_key      = api_key
        self.voice_name   = voice_name
        self.lang_code    = lang_code
        self.speaking_rate = speaking_rate
        self.pitch        = pitch
        self.output_dir   = os.path.join(os.getcwd(), "assets", "audio_clips")
        os.makedirs(self.output_dir, exist_ok=True)

    @staticmethod
    def _clean_text(text: str) -> str:
        text = text.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
        text = text.replace('...', ',').replace('\u2026', ',')
        text = text.replace('\u00f1', 'n').replace('\u00d1', 'N')
        text = re.sub(r'\s{2,}', ' ', text)
        text = re.sub(r',\s*,', ',', text)
        return text.strip()

    @staticmethod
    def _words_from_text(text: str) -> list:
        """Split text into clean words (strips punctuation for display)."""
        import re as _re
        return [w for w in text.split() if w]

    @staticmethod
    def _build_ssml(words: list) -> str:
        """Build a valid SSML string with a <mark> before each word.
        Uses only the 5 predefined XML entities (&amp; &lt; &gt; &apos; &quot;)
        so every character is safe inside an XML document."""
        _XML_ESC = str.maketrans({
            '&':  '&amp;',
            '<':  '&lt;',
            '>':  '&gt;',
            '"':  '&quot;',
            "'":  '&apos;',
        })
        parts = []
        for i, w in enumerate(words):
            safe = w.translate(_XML_ESC)
            parts.append(f'<mark name="{i}"/>{safe}')
        return '<speak>' + ' '.join(parts) + '</speak>'

    def _synthesize(self, text: str, output_path: str,
                    speaking_rate: float | None = None) -> str:
        """Synthesize audio and save per-word timestamps to {output_path}.words.json.

        Tries SSML+marks first (gives exact word timing).
        If Google rejects the SSML (400), falls back to plain-text synthesis
        (audio is saved, no .words.json → proportional subtitle fallback).
        """
        import requests, base64, json as _json, re as _re
        rate      = speaking_rate if speaking_rate is not None else self.speaking_rate
        is_chirp3 = "Chirp3-HD" in self.voice_name

        if is_chirp3:
            audio_cfg = {"audioEncoding": "MP3"}
            url       = self._URL_BETA
        else:
            audio_cfg = {
                "audioEncoding":    "MP3",
                "speakingRate":     round(max(0.25, min(rate, 4.0)), 3),
                "pitch":            round(max(-20.0, min(self.pitch, 20.0)), 1),
                "effectsProfileId": ["headphone-class-device"],
            }
            url = self._URL

        # ── Attempt 1: SSML with marks (exact word timing) ───────────────────
        words   = self._words_from_text(text)
        ssml    = self._build_ssml(words)
        payload = {
            "input":              {"ssml": ssml},
            "voice":              {"languageCode": self.lang_code, "name": self.voice_name},
            "audioConfig":        audio_cfg,
            "enableTimePointing": ["SSML_MARK"],
        }
        r = requests.post(url, params={"key": self.api_key},
                          headers={"Referer": "https://digency.streamlit.app/"},
                          json=payload, timeout=30)

        if r.status_code == 400:
            # SSML rejected — log the reason, retry with plain text
            try:
                reason = r.json().get("error", {}).get("message", r.text[:200])
            except Exception:
                reason = r.text[:200]
            print(f"      ⚠️  SSML rejected (400): {reason}")
            print(f"      🔄  Retrying with plain text (no word timing)...")
            payload_plain = {
                "input":       {"text": text},
                "voice":       {"languageCode": self.lang_code, "name": self.voice_name},
                "audioConfig": audio_cfg,
            }
            r = requests.post(url, params={"key": self.api_key},
                              headers={"Referer": "https://digency.streamlit.app/"},
                              json=payload_plain, timeout=30)
            r.raise_for_status()
            with open(output_path, "wb") as f:
                f.write(base64.b64decode(r.json()["audioContent"]))
            # Sin word timing en esta rama: recortar es seguro, nada que desplazar.
            _trim_edge_silence(output_path)
            print(f"      ✅  Plain-text fallback succeeded (proportional subtitles)")
            return output_path

        r.raise_for_status()
        data = r.json()

        with open(output_path, "wb") as f:
            f.write(base64.b64decode(data["audioContent"]))

        # Recortar silencio de cabeza/cola. El desplazamiento resultante se aplica
        # a los timepoints mas abajo, antes de escribir el .words.json.
        _lead = _trim_edge_silence(output_path)

        # ── Parse timepoints → save .words.json ──────────────────────────────
        timepoints = data.get("timepoints", [])
        if timepoints and words:
            word_times = []
            for tp in timepoints:
                try:
                    idx   = int(tp["markName"])
                    start = float(tp["timeSeconds"])
                    if idx < len(words):
                        clean_w = _re.sub(r'[^\w\s\'\-]', '', words[idx]).strip()
                        word_times.append({
                            "word":  clean_w or words[idx],
                            "start": round(start, 4),
                            "end":   round(start, 4),
                        })
                except (KeyError, ValueError):
                    continue

            for i in range(len(word_times) - 1):
                word_times[i]["end"] = word_times[i + 1]["start"]
            if word_times:
                word_times[-1]["end"] = round(word_times[-1]["start"] + 0.35, 4)
                # Compensar el silencio inicial recortado arriba
                word_times = _shift_word_times(word_times, _lead)
                with open(output_path + ".words.json", "w", encoding="utf-8") as tf:
                    _json.dump(word_times, tf, ensure_ascii=False)
                print(f"      ⏱️  Word timing saved ({len(word_times)} words)")
        else:
            print(f"      ⚠️  No timepoints returned — proportional subtitle fallback")

        return output_path

    def _normalize(self, path: str) -> None:
        """Peak-normalize to _TARGET_PEAK_DB (same logic as AudioEngine)."""
        try:
            result = subprocess.run(
                ['ffmpeg', '-i', path, '-af', 'volumedetect', '-f', 'null', '-'],
                capture_output=True, text=True, errors='replace'
            )
            match = re.search(r'max_volume:\s*([-\d.]+)\s*dB', result.stderr)
            if not match:
                return
            gain = _TARGET_PEAK_DB - float(match.group(1))
            if abs(gain) < 0.3:
                return
            tmp = path + '.norm.mp3'
            if os.path.exists(tmp):
                try:
                    os.remove(tmp)
                except Exception:
                    pass
            proc = subprocess.run(
                ['ffmpeg', '-i', path, '-af', f'volume={gain:.2f}dB', '-y', tmp],
                capture_output=True,
            )
            if proc.returncode == 0 and os.path.exists(tmp) and os.path.getsize(tmp) > 1024:
                os.replace(tmp, path)
            else:
                if os.path.exists(tmp):
                    try:
                        os.remove(tmp)
                    except Exception:
                        pass
        except Exception as e:
            print(f"      ⚠️ Normalization skipped: {e}")

    def get_audio_duration(self, file_path: str) -> float:
        try:
            audio = MP3(file_path)
            return audio.info.length
        except Exception:
            return 0.0

    async def process_script(self, script_data: list) -> list:
        total = len(script_data)
        print(f"🎙️ [Google TTS] Generating audio for {total} scenes "
              f"(voice={self.voice_name}, rate={self.speaking_rate})...")
        sem = asyncio.Semaphore(3)   # límite de concurrencia (respeta rate limits)

        async def _one(idx, scene):
            scene_id = scene["id"]
            text = self._clean_text(scene.get("text", ""))
            if not text:
                print(f"   ⚠️ Scene {scene_id}: empty text — skipping.")
                return
            out_path = os.path.join(self.output_dir, f"voice_{scene_id}.mp3")

            # Mood "energetic" → todo el video rápido (+8%)
            _mood = scene.get("mood", "")
            if _mood == "energetic":
                scene_rate = min(self.speaking_rate * 1.08, 4.0)
            elif idx < 2:
                scene_rate = min(self.speaking_rate * 1.08, 4.0)
            elif idx >= total - 1:
                scene_rate = max(self.speaking_rate * 0.95, 0.25)
            else:
                scene_rate = self.speaking_rate

            async with sem:
                try:
                    # _synthesize (REST) + _normalize (ffmpeg) son bloqueantes →
                    # corren en un hilo para no bloquear el event loop.
                    def _work():
                        self._synthesize(text, out_path, speaking_rate=scene_rate)
                        self._normalize(out_path)
                        return self.get_audio_duration(out_path)
                    duration = await asyncio.to_thread(_work)
                    if duration <= 0:
                        print(f"   ❌ Scene {scene_id}: invalid audio — skipping.")
                        return
                    scene["audio_path"] = out_path
                    scene["duration"]   = duration
                    print(f"   ✅ Scene {scene_id}: {duration:.2f}s")
                except Exception as e:
                    print(f"   ❌ Scene {scene_id} error: {e}")

        await asyncio.gather(*[_one(idx, scene) for idx, scene in enumerate(script_data)])
        return script_data


# ══════════════════════════════════════════════════════════════════════════════
# FISH AUDIO
# ══════════════════════════════════════════════════════════════════════════════

class FishAudioEngine:
    """TTS por API de Fish Audio (https://api.fish.audio/v1/tts).

    Dos particularidades frente a los otros motores:

    1. El modelo va en una CABECERA HTTP obligatoria (`model`), no en el cuerpo.
       El modelo NO es la voz: la voz se elige con `reference_id`.

    2. Las emociones se controlan con marcadores en corchetes DENTRO del texto
       ([calm], [confident], [soft tone]...). Aqui se inyectan a partir del tono
       del guion, de modo que el tono elegido en la UI llega hasta la locucion.

    No devuelve timing por palabra, asi que los subtitulos caen en el modo
    proporcional de composer.py (igual que Chirp3-HD y Journey de Google).
    """

    API_URL = "https://api.fish.audio/v1/tts"

    # La clave es lo que va en la cabecera `model`.
    MODELS = {
        "s2.1-pro-free": "s2.1-pro-free  (gratis - pruebas y proyectos pequenios)",
        "s2.1-pro":      "s2.1-pro       (produccion - mejor latencia y calidad)",
        "s2-pro":        "s2-pro         (generacion anterior - default de la API)",
        "s1":            "s1             (legado - emociones entre parentesis)",
    }

    # Voces en espanol de la Voice Library. reference_id -> etiqueta.
    VOICES_ES = {
        "13d17017d63340a0b9751ffb04561c8d": "Mujer latina *",
        "edbe850c6b7d40f195edd8c043b18748": "Voz de mujer muy real y no artificial",
        "a1070fc5bc824bb79dfa0007c00dfd0f": "Locutora mujer",
        "22550e2d849b44e18c7df57f61e666f9": "Mujer Voz Venezuela",
        "35199d5438854f5d9157c500479ab684": "Narrador v2 (masculina)",
        "dfa5b230c8054f429e434f4a6e9bbdec": "Farid Dieck (masculina)",
    }

    # El guion ya trae un `mood` por escena. Se traduce a un marcador, pero hay
    # que distinguir dos clases: los de EMOCION chocan con los del tono (pedir
    # [determined] y [calm] a la vez da un resultado incoherente), mientras que
    # los de ENTREGA solo afectan al enfasis y se pueden apilar sin conflicto.
    MOOD_EMOCION = {
        "calm":       "[calm]",
        "exciting":   "[excited]",
        "energetic":  "[excited]",
        "mysterious": "[curious]",
        "intriguing": "[curious]",
        "fun":        "[relaxed]",
    }
    MOOD_ENTREGA = {
        "dramatic": "[emphasis]",
    }

    def __init__(self, api_key: str, model: str = "s2.1-pro-free",
                 reference_id: str = "", speed: float = 1.0,
                 emotion_markers: str = "", lang: str = "es"):
        self.api_key         = (api_key or "").strip()
        self.model           = (model or "s2.1-pro-free").strip()
        self.reference_id    = (reference_id or "").strip()
        self.speed           = max(0.5, min(2.0, float(speed or 1.0)))
        self.emotion_markers = (emotion_markers or "").strip()
        self.lang            = lang
        self.output_dir      = os.path.join(os.getcwd(), "assets", "audio_clips")
        os.makedirs(self.output_dir, exist_ok=True)

    # ── utilidades ────────────────────────────────────────────────────────
    @staticmethod
    def _clean_text(text: str) -> str:
        """Limpia el texto sin tocar los corchetes de emocion."""
        text = re.sub(r"[\r\n\t]+", " ", text or "").strip()
        text = re.sub(r"\s{2,}", " ", text)
        # Red de seguridad heredada del resto de motores: varios TTS pronuncian
        # mal la letra n con tilde. El guion ya la evita con sinonimos; esto es
        # el ultimo recurso por si alguna se cuela.
        return text.replace("ñ", "n").replace("Ñ", "N")

    def _build_text(self, scene: dict) -> str:
        """Antepone los marcadores de emocion al texto de la escena.

        El TONO manda sobre el mood: si el tono ya fija una direccion emocional,
        el mood no puede contradecirla. Solo los marcadores de entrega ([emphasis])
        se apilan sobre el tono, porque afectan al enfasis y no a la emocion.
        """
        cuerpo = self._clean_text(scene.get("text", ""))
        if not cuerpo:
            return ""

        mood   = scene.get("mood", "")
        marcas = []

        if self.emotion_markers:
            marcas.append(self.emotion_markers)
            # Con tono activo, solo se anade el matiz de entrega.
            extra = self.MOOD_ENTREGA.get(mood, "")
        else:
            # Sin tono, el mood de la escena es la unica fuente de emocion.
            extra = self.MOOD_EMOCION.get(mood, "") or self.MOOD_ENTREGA.get(mood, "")

        if extra and extra not in (self.emotion_markers or ""):
            marcas.append(extra)

        prefijo = " ".join(marcas)
        return f"{prefijo} {cuerpo}".strip() if prefijo else cuerpo

    def get_audio_duration(self, file_path: str) -> float:
        try:
            out = subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries", "format=duration",
                 "-of", "csv=p=0", file_path],
                capture_output=True, text=True, timeout=20,
            ).stdout.strip()
            return float(out) if out else 0.0
        except Exception:
            return 0.0

    def _normalize(self, path: str) -> None:
        """Iguala el pico a _TARGET_PEAK_DB, como el resto de motores."""
        try:
            result = subprocess.run(
                ["ffmpeg", "-i", path, "-af", "volumedetect", "-f", "null", "-"],
                capture_output=True, text=True, errors="replace",
            )
            m = re.search(r"max_volume:\s*([-\d.]+)\s*dB", result.stderr)
            if not m:
                return
            gain = _TARGET_PEAK_DB - float(m.group(1))
            if abs(gain) < 0.3:
                return
            tmp = path + ".norm.mp3"
            if os.path.exists(tmp):
                try:
                    os.remove(tmp)
                except Exception:
                    pass
            proc = subprocess.run(
                ["ffmpeg", "-i", path, "-af", f"volume={gain:.2f}dB", "-y", tmp],
                capture_output=True,
            )
            if proc.returncode == 0 and os.path.exists(tmp) and os.path.getsize(tmp) > 1024:
                os.replace(tmp, path)
            elif os.path.exists(tmp):
                try:
                    os.remove(tmp)
                except Exception:
                    pass
        except Exception as e:
            print(f"      warning: normalizacion omitida: {e}")

    # ── sintesis ──────────────────────────────────────────────────────────
    def _synthesize(self, text: str, out_path: str) -> None:
        import requests
        payload = {
            "text":        text,
            "format":      "mp3",
            "mp3_bitrate": 128,
            "normalize":   True,
            "latency":     "normal",   # mas estable que balanced para render offline
            "prosody":     {"speed": self.speed, "volume": 0},
        }
        if self.reference_id:
            payload["reference_id"] = self.reference_id

        r = requests.post(
            self.API_URL,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type":  "application/json",
                "model":         self.model,   # OBLIGATORIA en cada peticion
            },
            json=payload, timeout=120,
        )
        if r.status_code != 200:
            raise RuntimeError(f"HTTP {r.status_code}: {r.text[:180]}")
        if len(r.content) < 1024:
            raise RuntimeError(f"respuesta demasiado corta ({len(r.content)} bytes)")
        with open(out_path, "wb") as f:
            f.write(r.content)

    async def process_script(self, script_data: list) -> list:
        total = len(script_data)
        _voz = self.VOICES_ES.get(self.reference_id) or self.reference_id or "por defecto"
        print(f"[Fish Audio] Generando audio para {total} escenas "
              f"(model={self.model}, voz={_voz})")
        if self.emotion_markers:
            print(f"   Marcadores de tono: {self.emotion_markers}")
        sem = asyncio.Semaphore(3)

        async def _one(idx, scene):
            scene_id = scene["id"]
            texto = self._build_text(scene)
            if not texto:
                print(f"   warning: escena {scene_id} sin texto, se omite.")
                return
            out_path = os.path.join(self.output_dir, f"voice_{scene_id}.mp3")

            async with sem:
                try:
                    def _work():
                        self._synthesize(texto, out_path)
                        # Mismo recorte que el resto de motores: sin esto vuelve
                        # el bache de silencio en cada corte de escena.
                        _trim_edge_silence(out_path)
                        self._normalize(out_path)
                        return self.get_audio_duration(out_path)
                    duration = await asyncio.to_thread(_work)
                    if duration <= 0:
                        print(f"   error: escena {scene_id} audio invalido, se omite.")
                        return
                    scene["audio_path"] = out_path
                    scene["duration"]   = duration
                    print(f"   OK escena {scene_id}: {duration:.2f}s")
                except Exception as e:
                    print(f"   error escena {scene_id}: {e}")

        await asyncio.gather(*[_one(i, s) for i, s in enumerate(script_data)])
        return script_data


# ══════════════════════════════════════════════════════════════════════════════
# ELEVENLABS  (preparado, SIN PROBAR: no hay clave disponible todavia)
# ══════════════════════════════════════════════════════════════════════════════

class ElevenLabsEngine:
    """TTS por API de ElevenLabs.

    ADVERTENCIA: esta clase esta escrita segun la API documentada de ElevenLabs
    pero NO se ha ejecutado nunca contra el servicio real, porque no habia clave
    disponible al implementarla. Espera fallos de detalle en la primera prueba
    (nombres de campo, rangos de voice_settings, formato de salida).

    Diferencias con Fish Audio:
    - La voz va en la URL, no en el cuerpo.
    - La clave va en la cabecera `xi-api-key`, no como Bearer.
    - No hay marcadores de emocion en corchetes: la expresividad se ajusta con
      voice_settings (stability / similarity_boost / style). Por eso el tono del
      guion se traduce aqui a valores de esos parametros, no a etiquetas.
    """

    API_BASE = "https://api.elevenlabs.io/v1/text-to-speech"

    MODELS = {
        "eleven_multilingual_v2": "eleven_multilingual_v2  (calidad, 29 idiomas)",
        "eleven_turbo_v2_5":      "eleven_turbo_v2_5       (rapido, buen espanol)",
        "eleven_flash_v2_5":      "eleven_flash_v2_5       (minima latencia)",
    }

    # El tono del guion se traduce a ajustes de voz en lugar de a etiquetas.
    # stability bajo = mas variacion expresiva; alto = mas monotono y estable.
    TONE_SETTINGS = {
        "conductual":    {"stability": 0.55, "similarity_boost": 0.80, "style": 0.15},
        "confrontativo": {"stability": 0.40, "similarity_boost": 0.80, "style": 0.45},
        "motivador":     {"stability": 0.30, "similarity_boost": 0.75, "style": 0.60},
        "emotivo":       {"stability": 0.65, "similarity_boost": 0.85, "style": 0.25},
        "urgente":       {"stability": 0.40, "similarity_boost": 0.80, "style": 0.50},
    }

    def __init__(self, api_key: str, voice_id: str = "",
                 model: str = "eleven_multilingual_v2",
                 tono: str = "conductual", lang: str = "es"):
        self.api_key    = (api_key or "").strip()
        self.voice_id   = (voice_id or "").strip()
        self.model      = (model or "eleven_multilingual_v2").strip()
        self.settings   = self.TONE_SETTINGS.get(tono, self.TONE_SETTINGS["conductual"])
        self.lang       = lang
        self.output_dir = os.path.join(os.getcwd(), "assets", "audio_clips")
        os.makedirs(self.output_dir, exist_ok=True)

    @staticmethod
    def _clean_text(text: str) -> str:
        text = re.sub(r"[\r\n\t]+", " ", text or "").strip()
        text = re.sub(r"\s{2,}", " ", text)
        return text.replace("ñ", "n").replace("Ñ", "N")

    def get_audio_duration(self, file_path: str) -> float:
        try:
            out = subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries", "format=duration",
                 "-of", "csv=p=0", file_path],
                capture_output=True, text=True, timeout=20,
            ).stdout.strip()
            return float(out) if out else 0.0
        except Exception:
            return 0.0

    def _synthesize(self, text: str, out_path: str) -> None:
        import requests
        if not self.voice_id:
            raise RuntimeError("falta el voice_id de ElevenLabs")
        r = requests.post(
            f"{self.API_BASE}/{self.voice_id}",
            headers={"xi-api-key": self.api_key,
                     "Content-Type": "application/json",
                     "Accept": "audio/mpeg"},
            json={"text": text, "model_id": self.model,
                  "voice_settings": {**self.settings, "use_speaker_boost": True}},
            timeout=120,
        )
        if r.status_code != 200:
            raise RuntimeError(f"HTTP {r.status_code}: {r.text[:180]}")
        if len(r.content) < 1024:
            raise RuntimeError(f"respuesta demasiado corta ({len(r.content)} bytes)")
        with open(out_path, "wb") as f:
            f.write(r.content)

    async def process_script(self, script_data: list) -> list:
        total = len(script_data)
        print(f"[ElevenLabs] Generando audio para {total} escenas "
              f"(model={self.model}, voz={self.voice_id or 'sin definir'})")
        print("   NOTA: motor sin probar contra la API real.")
        sem = asyncio.Semaphore(3)

        async def _one(scene):
            scene_id = scene["id"]
            texto = self._clean_text(scene.get("text", ""))
            if not texto:
                print(f"   warning: escena {scene_id} sin texto, se omite.")
                return
            out_path = os.path.join(self.output_dir, f"voice_{scene_id}.mp3")
            async with sem:
                try:
                    def _work():
                        self._synthesize(texto, out_path)
                        _trim_edge_silence(out_path)
                        return self.get_audio_duration(out_path)
                    duration = await asyncio.to_thread(_work)
                    if duration <= 0:
                        print(f"   error: escena {scene_id} audio invalido, se omite.")
                        return
                    scene["audio_path"] = out_path
                    scene["duration"]   = duration
                    print(f"   OK escena {scene_id}: {duration:.2f}s")
                except Exception as e:
                    print(f"   error escena {scene_id}: {e}")

        await asyncio.gather(*[_one(s) for s in script_data])
        return script_data
