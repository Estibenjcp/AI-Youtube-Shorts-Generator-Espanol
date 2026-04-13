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

    async def generate_audio(self, text, output_filename, retries=3):
        """
        Generates MP3 with retry logic to handle connection drops.
        After generation, verifies the file has valid duration.
        Falls back to no-normalization if file gets corrupted.
        """
        output_path = os.path.join(self.output_dir, output_filename)

        for attempt in range(retries):
            try:
                communicate = edge_tts.Communicate(text, self.voice, rate=self.rate)
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
                    communicate2 = edge_tts.Communicate(text, self.voice, rate=self.rate)
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

        for scene in script_data:
            scene_id = scene['id']
            text = self._clean_text(scene.get('text', ''))
            if not text:
                print(f"   ⚠️ Scene {scene_id} has empty text — skipping.")
                continue
            filename = f"voice_{scene_id}.mp3"

            try:
                file_path = await self.generate_audio(text, filename)
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
