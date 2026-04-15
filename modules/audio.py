import os
import re
import asyncio
import subprocess
import edge_tts
from mutagen.mp3 import MP3

# Target peak level for all audio clips (dB). -3 leaves headroom without clipping.
_TARGET_PEAK_DB = -3.0

class AudioEngine:
    def __init__(self, voice: str = "en-US-AvaNeural", rate: str = "+10%"):
        self.voice = voice
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
          instead of potentially generating short/silent audio
        - Collapses multiple spaces
        """
        # Replace newlines / tabs with a space
        text = text.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
        # Replace ellipsis variants with a comma pause (TTS-friendly)
        text = text.replace('...', ',')
        text = text.replace('\u2026', ',')
        # Collapse multiple whitespace into one
        text = re.sub(r'\s{2,}', ' ', text)
        # Remove any double commas that might result
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

    async def generate_audio(self, text, output_filename, retries=3, rate_override=None):
        """
        Generates MP3 with retry logic to handle connection drops.
        After generation, verifies the file has valid duration.
        Falls back to no-normalization if file gets corrupted.
        """
        output_path = os.path.join(self.output_dir, output_filename)

        for attempt in range(retries):
            try:
                effective_rate = rate_override if rate_override is not None else self.rate
                communicate = edge_tts.Communicate(text, self.voice, rate=effective_rate)
                await communicate.save(output_path)

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
                    communicate2 = edge_tts.Communicate(text, self.voice, rate=effective_rate)
                    await communicate2.save(output_path)

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

        for idx, scene in enumerate(script_data):
            scene_id = scene['id']
            text = self._clean_text(scene.get('text', ''))
            if not text:
                print(f"   ⚠️ Scene {scene_id} has empty text — skipping.")
                continue
            filename = f"voice_{scene_id}.mp3"

            # Hook scenes (1-2): +8% faster → urgency; CTA (last): -5% → clarity
            if idx < 2:
                scene_rate = self._adjust_rate(self.rate, +8)
            elif idx >= total_scenes - 1:
                scene_rate = self._adjust_rate(self.rate, -5)
            else:
                scene_rate = self.rate

            try:
                file_path = await self.generate_audio(text, filename, rate_override=scene_rate)
                duration  = self.get_audio_duration(file_path)

                if duration <= 0:
                    print(f"   ❌ Scene {scene_id}: audio duration is 0 after generation — skipping.")
                    continue

                scene['audio_path'] = file_path
                scene['duration']   = duration
                print(f"   ✅ Scene {scene_id}: {duration:.2f}s generated.")

                await asyncio.sleep(1)

            except Exception as e:
                print(f"   ❌ Skipping Scene {scene_id} due to audio error: {e}")
                continue

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
            raise RuntimeError("VoxCPM model failed to load — check logs above.")
        if self._model is None:
            print("[VoxCPM] Loading model (first run — may take a minute)...")
            try:
                # load_denoiser=False skips the ModelScope speech_zipenhancer
                # dependency that may be geo-blocked or require authentication.
                self._model = self._VoxCPM.from_pretrained(
                    "openbmb/VoxCPM2",
                    load_denoiser=False,
                )
                print("[VoxCPM] Model ready (denoiser disabled — faster load).")
            except Exception as e:
                self._model_load_failed = True
                raise RuntimeError(f"[VoxCPM] Failed to load model: {e}") from e
        return self._model

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
