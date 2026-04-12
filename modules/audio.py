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
        This ensures every TTS clip plays at the same volume level.
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
            subprocess.run(
                ['ffmpeg', '-i', path, '-af', f'volume={gain:.2f}dB', '-y', tmp],
                capture_output=True
            )
            os.replace(tmp, path)
        except Exception as e:
            print(f"      ⚠️ Normalization skipped: {e}")

    async def generate_audio(self, text, output_filename, retries=3):
        """
        Generates MP3 with retry logic to handle connection drops.
        """
        output_path = os.path.join(self.output_dir, output_filename)

        for attempt in range(retries):
            try:
                communicate = edge_tts.Communicate(text, self.voice, rate=self.rate)
                await communicate.save(output_path)
                self._normalize(output_path)
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

    @staticmethod
    def _clean_text(text: str) -> str:
        """Sanitize text before sending to Edge TTS.
        Newlines, tabs and multiple spaces confuse the TTS engine and cause
        words to be dropped or the request to fail silently."""
        import re as _re
        # Replace newlines / tabs with a space
        text = text.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
        # Collapse multiple whitespace into one
        text = _re.sub(r'\s{2,}', ' ', text)
        # Strip leading/trailing
        return text.strip()

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
                # Generate Audio
                file_path = await self.generate_audio(text, filename)
                
                # Get Duration
                duration = self.get_audio_duration(file_path)
                
                # Update Scene Data
                scene['audio_path'] = file_path
                scene['duration'] = duration
                
                print(f"   ✅ Scene {scene_id}: {duration:.2f}s generated.")
                
                # CRITICAL: Sleep for 1 second to be polite to the API
                # This prevents the "Connection Timeout" error
                await asyncio.sleep(1) 
                
            except Exception as e:
                print(f"   ❌ Skipping Scene {scene_id} due to audio error.")
                continue
            
        return script_data