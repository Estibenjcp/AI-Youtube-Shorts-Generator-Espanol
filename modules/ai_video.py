"""
ai_video.py — AIVideoEngine
Generates short silent video clips via FAL.ai (primary) or Kling direct API
(secondary) for each scene in a script, then trims/loops each clip to match
the TTS audio duration exactly.  Returns {scene_id: [clip_path]} compatible
with the existing Composer.
"""

import os
import re
import json
import asyncio
import subprocess
import time

import requests

# ---------------------------------------------------------------------------
# Module-level constants (exported)
# ---------------------------------------------------------------------------

VIDEO_STYLES = {
    "cinematic": {
        "label": "🎥 Cinematográfico",
        "label_en": "🎥 Cinematic",
        "suffix": (
            "Hollywood cinematic, anamorphic lens, dramatic color grading, "
            "shallow depth of field, film grain"
        ),
    },
    "realistic": {
        "label": "📷 Realista",
        "label_en": "📷 Realistic",
        "suffix": (
            "photorealistic, natural lighting, authentic documentary, "
            "handheld camera, 8K"
        ),
    },
    "documentary": {
        "label": "📺 Documental",
        "label_en": "📺 Documentary",
        "suffix": (
            "documentary style, handheld camera, raw authentic footage, "
            "news reportage"
        ),
    },
    "noir": {
        "label": "🌙 Noir / Dramático",
        "label_en": "🌙 Noir / Dramatic",
        "suffix": (
            "film noir, high contrast, dark shadows, moody atmosphere, "
            "chiaroscuro lighting"
        ),
    },
    "neon_futurism": {
        "label": "✨ Neon / Futurista",
        "label_en": "✨ Neon / Futurist",
        "suffix": (
            "neon glow, cyberpunk aesthetic, sci-fi vibes, "
            "vibrant electric colors, futuristic"
        ),
    },
    "anime": {
        "label": "🎨 Anime",
        "label_en": "🎨 Anime",
        "suffix": (
            "Japanese anime style, vibrant colors, expressive characters, "
            "cel-shaded"
        ),
    },
    "animation_3d": {
        "label": "🧊 Animación 3D",
        "label_en": "🧊 3D Animation",
        "suffix": (
            "Pixar-style 3D animation, colorful, smooth motion, polished render"
        ),
    },
}

# ---------------------------------------------------------------------------
# Internal constants
# ---------------------------------------------------------------------------

_MODEL_DURATIONS = {
    "fal-ai/kling-video/v2/standard/text-to-video": [5, 10],
    "fal-ai/kling-video/v1.6/standard/text-to-video": [5, 10],
    "fal-ai/minimax/video-01-live": [6],
    "fal-ai/runway-gen3/turbo/text-to-video": [5, 10],
    "fal-ai/luma-dream-machine": [5],
    "fal-ai/wan-i2v": [5],
}

_DEFAULT_MODELS = {
    "fal":     "fal-ai/kling-video/v2/standard/text-to-video",
    "kling":   "fal-ai/kling-video/v2/standard/text-to-video",
    "runway":  "fal-ai/runway-gen3/turbo/text-to-video",
    "luma":    "fal-ai/luma-dream-machine",
    "minimax": "fal-ai/minimax/video-01-live",
    "pika":    "fal-ai/kling-video/v2/standard/text-to-video",
    "otro":    "fal-ai/kling-video/v2/standard/text-to-video",
}

_MOOD_MOTION = {
    "energetic":    "fast dynamic motion, high energy movement",
    "dramatic":     "slow dramatic push-in, intense atmosphere",
    "mysterious":   "slow creeping camera, eerie tension",
    "calm":         "gentle slow pan, peaceful serene",
    "inspiring":    "upward camera movement, uplifting energy",
    "professional": "clean smooth dolly shot, polished",
    "exciting":     "dynamic handheld, thrilling action",
    "fun":          "bouncy playful movement, vibrant",
    "informative":  "steady tripod shot, clear focused",
}

_FAL_BASE        = "https://queue.fal.run"
_KLING_BASE      = "https://api.klingai.com/v1/videos/text2video"
_POLL_INTERVAL   = 5      # seconds between status polls
_POLL_TIMEOUT    = 180    # maximum seconds to wait for a clip
_OUTPUT_DIR      = "assets/video_clips"


# ---------------------------------------------------------------------------
# AIVideoEngine
# ---------------------------------------------------------------------------

class AIVideoEngine:
    """
    Generate AI video clips for every scene in a script.

    Parameters
    ----------
    provider : str
        One of the keys in _DEFAULT_MODELS  ("fal", "kling", "runway", etc.).
        When provider == "kling" the Kling direct REST API is used instead of
        the FAL.ai queue.
    api_key : str
        API key / Bearer token for the chosen provider.
    model : str
        Optional model override.  Falls back to _DEFAULT_MODELS[provider].
    style : str
        One of the VIDEO_STYLES keys.  Defaults to "cinematic".
    max_parallel : int
        Maximum number of scenes generated concurrently.
    """

    def __init__(
        self,
        provider: str,
        api_key: str,
        model: str = "",
        style: str = "cinematic",
        clip_duration: int = 0,   # 0 = auto-detect from audio; 5 or 10 = forced
        max_parallel: int = 2,
    ):
        self.provider      = provider.lower().strip()
        self.api_key       = api_key.strip()
        self.model         = model.strip() if model.strip() else self._default_model(self.provider)
        self.style         = style if style in VIDEO_STYLES else "cinematic"
        self.clip_duration = int(clip_duration)   # user-forced duration (0 = auto)
        self.max_parallel  = max(1, int(max_parallel))
        self.output_dir    = _OUTPUT_DIR
        os.makedirs(self.output_dir, exist_ok=True)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _default_model(self, provider: str) -> str:
        return _DEFAULT_MODELS.get(provider, _DEFAULT_MODELS["fal"])

    def _best_duration(self, audio_dur: float) -> int:
        """
        Return the clip duration to request from the AI model.
        - If self.clip_duration is set (>0), use it directly (user preference).
        - Otherwise auto-pick the shortest supported duration >= audio_dur.
        """
        if self.clip_duration > 0:
            # Clamp to a supported duration (pick closest >=)
            durations = sorted(_MODEL_DURATIONS.get(self.model, [5, 10]))
            for d in durations:
                if d >= self.clip_duration:
                    return d
            return durations[-1]
        # Auto-detect: pick shortest clip that covers the audio
        durations = sorted(_MODEL_DURATIONS.get(self.model, [5, 10]))
        for d in durations:
            if d >= audio_dur:
                return d
        return durations[-1]

    def _build_prompt(self, scene: dict) -> str:
        """
        Compose the text-to-video prompt from scene metadata.
        Priority: scene["video_prompt"] > visual_1 + visual_2.
        Appended: mood motion hint + style suffix + format notice.
        """
        if scene.get("video_prompt", "").strip():
            base = scene["video_prompt"].strip()
        else:
            parts = []
            if scene.get("visual_1", "").strip():
                parts.append(scene["visual_1"].strip())
            if scene.get("visual_2", "").strip():
                parts.append(scene["visual_2"].strip())
            base = ". ".join(parts) if parts else "cinematic scene"

        mood = scene.get("mood", "").lower().strip()
        motion_hint = _MOOD_MOTION.get(mood, "smooth camera movement")

        style_suffix = VIDEO_STYLES[self.style]["suffix"]

        prompt = (
            f"{base}. "
            f"{motion_hint}. "
            f"{style_suffix}. "
            "No text overlays, no watermarks. "
            "Vertical 9:16 format, mobile optimized."
        )
        return prompt

    # ------------------------------------------------------------------
    # FAL.ai provider (primary)
    # ------------------------------------------------------------------

    async def _submit_fal(self, prompt: str, duration: int, session_headers: dict) -> str:
        """Submit a generation request to the FAL.ai queue, return request_id."""
        url  = f"{_FAL_BASE}/{self.model}"
        body = {
            "prompt":       prompt,
            "duration":     str(duration),
            "aspect_ratio": "9:16",
        }

        def _post():
            resp = requests.post(url, headers=session_headers, json=body, timeout=30)
            resp.raise_for_status()
            return resp.json()

        data = await asyncio.to_thread(_post)
        request_id = data.get("request_id") or data.get("id")
        if not request_id:
            raise RuntimeError(f"FAL submit: no request_id in response: {data}")
        return request_id

    async def _poll_fal(self, request_id: str, session_headers: dict) -> str:
        """Poll the FAL.ai queue until the job is COMPLETED, return video URL."""
        status_url = f"{_FAL_BASE}/{self.model}/requests/{request_id}/status"
        result_url = f"{_FAL_BASE}/{self.model}/requests/{request_id}"
        deadline   = time.monotonic() + _POLL_TIMEOUT

        while time.monotonic() < deadline:
            await asyncio.sleep(_POLL_INTERVAL)

            def _get_status():
                r = requests.get(status_url, headers=session_headers, timeout=20)
                r.raise_for_status()
                return r.json()

            status_data = await asyncio.to_thread(_get_status)
            status = status_data.get("status", "").upper()

            if status == "FAILED":
                raise RuntimeError(f"FAL job {request_id} failed: {status_data}")

            if status == "COMPLETED":
                def _get_result():
                    r = requests.get(result_url, headers=session_headers, timeout=20)
                    r.raise_for_status()
                    return r.json()

                result = await asyncio.to_thread(_get_result)

                # Try multiple response shapes
                video_url = (
                    (result.get("video") or {}).get("url")
                    or (((result.get("outputs") or [{}])[0]) or {}).get("url")
                    or (result.get("output") or {}).get("video_url")
                )
                if not video_url:
                    raise RuntimeError(f"FAL result: cannot find video URL in {result}")
                return video_url

            # IN_QUEUE or IN_PROGRESS — keep polling

        raise TimeoutError(f"FAL job {request_id} timed out after {_POLL_TIMEOUT}s")

    # ------------------------------------------------------------------
    # Kling direct API (secondary)
    # ------------------------------------------------------------------

    async def _submit_kling_direct(
        self, prompt: str, duration: int, headers: dict
    ) -> str:
        """Submit a request to the Kling direct REST API, return task_id."""
        body = {
            "model_name":   "kling-v2-master",
            "prompt":       prompt,
            "duration":     str(duration),
            "aspect_ratio": "9:16",
        }

        def _post():
            r = requests.post(_KLING_BASE, headers=headers, json=body, timeout=30)
            r.raise_for_status()
            return r.json()

        data    = await asyncio.to_thread(_post)
        task_id = (data.get("data") or {}).get("task_id")
        if not task_id:
            raise RuntimeError(f"Kling submit: no task_id in response: {data}")
        return task_id

    async def _poll_kling_direct(self, task_id: str, headers: dict) -> str:
        """Poll Kling until the task succeeds, return video URL."""
        poll_url = f"{_KLING_BASE}/{task_id}"
        deadline = time.monotonic() + _POLL_TIMEOUT

        while time.monotonic() < deadline:
            await asyncio.sleep(_POLL_INTERVAL)

            def _get():
                r = requests.get(poll_url, headers=headers, timeout=20)
                r.raise_for_status()
                return r.json()

            result = await asyncio.to_thread(_get)
            data   = result.get("data") or {}
            status = data.get("task_status", "").lower()

            if status in ("failed", "error"):
                raise RuntimeError(f"Kling task {task_id} failed: {result}")

            if status == "succeed":
                videos = (data.get("task_result") or {}).get("videos") or []
                if not videos or not videos[0].get("url"):
                    raise RuntimeError(
                        f"Kling task {task_id}: no video URL in result: {result}"
                    )
                return videos[0]["url"]

        raise TimeoutError(f"Kling task {task_id} timed out after {_POLL_TIMEOUT}s")

    # ------------------------------------------------------------------
    # Download & trim helpers
    # ------------------------------------------------------------------

    async def _download_clip(self, url: str, out_path: str) -> str:
        """Download a video URL to out_path, return out_path."""

        def _fetch():
            with requests.get(url, stream=True, timeout=120) as r:
                r.raise_for_status()
                with open(out_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=65536):
                        if chunk:
                            f.write(chunk)

        await asyncio.to_thread(_fetch)
        return out_path

    def _trim_clip(self, raw_path: str, target_dur: float, out_path: str) -> str:
        """
        Trim / loop raw_path to exactly target_dur seconds and scale to
        720x1280, writing the result to out_path.  Audio track is stripped.
        """
        subprocess.run(
            [
                "ffmpeg", "-y",
                "-stream_loop", "-1",       # loop source if shorter than target
                "-i", raw_path,
                "-t", f"{target_dur:.3f}",
                "-c:v", "libx264",
                "-preset", "fast",
                "-crf", "23",
                "-vf", (
                    "scale=720:1280:"
                    "force_original_aspect_ratio=decrease,"
                    "pad=720:1280:(ow-iw)/2:(oh-ih)/2"
                ),
                "-an",
                out_path,
            ],
            capture_output=True,
        )
        return out_path

    # ------------------------------------------------------------------
    # Per-scene generation
    # ------------------------------------------------------------------

    async def _generate_scene_clip(
        self, scene: dict, semaphore: asyncio.Semaphore
    ) -> dict:
        """
        Generate, download, and trim a clip for a single scene.
        Sets scene["video_path"] to the trimmed file path, or None on failure.
        Returns the (mutated) scene dict.
        """
        scene_id = scene.get("id", "unknown")

        async with semaphore:
            try:
                # ---- determine duration ----
                audio_dur = float(scene.get("audio_duration", 5.0))
                clip_dur  = self._best_duration(audio_dur)

                # ---- build prompt ----
                prompt = self._build_prompt(scene)

                # ---- file paths ----
                safe_id  = re.sub(r"[^\w\-]", "_", str(scene_id))
                raw_path = os.path.join(self.output_dir, f"raw_{safe_id}.mp4")
                out_path = os.path.join(self.output_dir, f"aivid_{safe_id}.mp4")

                # ---- generate via provider ----
                if self.provider == "kling":
                    headers = {
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type":  "application/json",
                    }
                    task_id   = await self._submit_kling_direct(prompt, clip_dur, headers)
                    video_url = await self._poll_kling_direct(task_id, headers)
                else:
                    headers = {
                        "Authorization": f"Key {self.api_key}",
                        "Content-Type":  "application/json",
                    }
                    request_id = await self._submit_fal(prompt, clip_dur, headers)
                    video_url  = await self._poll_fal(request_id, headers)

                # ---- download ----
                await self._download_clip(video_url, raw_path)

                # ---- trim / loop to exact audio duration ----
                self._trim_clip(raw_path, audio_dur, out_path)

                scene["video_path"] = out_path
                print(f"✅ Scene {scene_id}: clip ready → {out_path}")

            except Exception as exc:
                scene["video_path"] = None
                print(f"❌ Scene {scene_id}: generation failed — {exc}")

        return scene

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def process_script(self, script_data: list) -> dict:
        """
        Generate clips for all scenes concurrently (bounded by max_parallel).

        Parameters
        ----------
        script_data : list of scene dicts
            Each dict must have at least an "id" key.
            Optionally: "audio_duration", "visual_1", "visual_2",
                        "mood", "video_prompt".

        Returns
        -------
        dict
            {scene_id: [clip_path]}  — only scenes that succeeded are included.
        """
        semaphore = asyncio.Semaphore(self.max_parallel)

        results = await asyncio.gather(
            *[self._generate_scene_clip(scene, semaphore) for scene in script_data],
            return_exceptions=False,
        )

        output = {}
        for scene in results:
            scene_id   = scene.get("id")
            video_path = scene.get("video_path")
            if scene_id is not None and video_path is not None:
                output[scene_id] = [video_path]

        return output
