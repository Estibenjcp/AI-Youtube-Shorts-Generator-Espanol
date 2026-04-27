"""
Quick 2-scene render test — supports Edge TTS or Google TTS.
Run:  python test_render.py
Output: assets/final/test_output.mp4

Edit the CONFIG section below to test different configurations.
"""
import asyncio
import os
import ffmpeg

# ── CONFIG ───────────────────────────────────────────────────────────────────

# Choose TTS engine: "edge" or "google"
TTS_ENGINE = "google"

# ── Edge TTS settings (used when TTS_ENGINE = "edge") ──
EDGE_VOICE = "es-ES-AlvaroNeural"
EDGE_RATE  = "+0%"

# ── Google TTS settings (used when TTS_ENGINE = "google") ──
GOOGLE_API_KEY   = os.environ.get("GOOGLE_TTS_API_KEY", "")   # or paste key here
GOOGLE_VOICE     = "es-US-Neural2-B"     # any Neural2 / Studio / Journey / Chirp3-HD name
GOOGLE_LANG_CODE = "es-US"
GOOGLE_RATE      = 1.0                   # 0.25 – 4.0

# ── Script ──
SCENES_TEXT = [
    "Hace miles de años, una civilización olvidada construyó monumentos que todavía hoy desafían toda explicación conocida por la ciencia moderna.",
    "Los secretos enterrados bajo sus ruinas revelan una tecnología tan avanzada que ningún experto ha podido explicar cómo fue posible crearla.",
]

# ── Subtitle style ──
SUBTITLE_STYLE = {
    "fontsize":    44,
    "fontcolor":   "white",
    "y":           "h*0.82",
    "borderw":     3,
    "bordercolor": "black",
    "box":         0,
    "boxcolor":    "black@0.4",
    "max_chars":   28,
    # Uncomment to test highlight:
    # "highlight_color":     "0xFFD700",
    # "highlight_fontcolor": "black",
}

# Background colors (one per scene) — any FFmpeg color string
BG_COLORS = ["0x1a1a2e", "0x16213e"]

# ── Hook card (set HOOK_TEXT="" to disable, or leave blank for auto from first scene) ──
HOOK_TEXT     = ""      # e.g. "¿Sabías que esto existía?"
HOOK_DURATION = 2.5     # seconds the hook card is visible

# ── Progress bar ──
PROGRESS_BAR       = False
PROGRESS_BAR_COLOR = "white"

# ─────────────────────────────────────────────────────────────────────────────

TEMP_DIR  = os.path.join("assets", "temp")
FINAL_DIR = os.path.join("assets", "final")


def _make_bg_clip(color: str, duration: float, out_path: str):
    """Generate a solid-color 720x1280 background clip via FFmpeg lavfi."""
    (
        ffmpeg
        .input(f"color=c={color}:s=720x1280:r=30", format="lavfi", t=duration + 0.5)
        .output(out_path, vcodec="libx264", pix_fmt="yuv420p", movflags="faststart")
        .run(overwrite_output=True, quiet=True)
    )


async def _gen_edge(scenes_text: list) -> list:
    from modules.audio import EdgeTTS
    from mutagen.mp3 import MP3
    tts    = EdgeTTS(voice=EDGE_VOICE, rate=EDGE_RATE, output_dir=TEMP_DIR)
    scenes = []
    for idx, text in enumerate(scenes_text, start=1):
        filename   = f"test_voice_{idx}.mp3"
        audio_path = await tts.generate_audio(text, filename)
        duration   = MP3(audio_path).info.length
        scenes.append({"id": idx, "text": text, "audio_path": audio_path, "duration": duration})
        print(f"   Scene {idx}: {duration:.2f}s → {audio_path}")
    return scenes


def _gen_google(scenes_text: list) -> list:
    from modules.audio import GoogleTTSAudioEngine
    from mutagen.mp3 import MP3

    if not GOOGLE_API_KEY:
        raise ValueError(
            "GOOGLE_API_KEY is empty.\n"
            "Set the GOOGLE_TTS_API_KEY env var or paste the key into test_render.py."
        )

    engine = GoogleTTSAudioEngine(
        api_key      = GOOGLE_API_KEY,
        voice_name   = GOOGLE_VOICE,
        lang_code    = GOOGLE_LANG_CODE,
        speaking_rate= GOOGLE_RATE,
    )

    scenes = []
    for idx, text in enumerate(scenes_text, start=1):
        out_path = os.path.join(TEMP_DIR, f"test_voice_{idx}.mp3")
        engine._synthesize(text, out_path)
        duration = MP3(out_path).info.length
        words_file = out_path + ".words.json"
        has_timing = os.path.exists(words_file)
        scenes.append({"id": idx, "text": text, "audio_path": out_path, "duration": duration})
        print(f"   Scene {idx}: {duration:.2f}s → {out_path}"
              f"  {'✅ word timing' if has_timing else '⚠️ no timing (Chirp3-HD fallback)'}")
    return scenes


async def main():
    from modules.composer import Composer

    os.makedirs(TEMP_DIR,  exist_ok=True)
    os.makedirs(FINAL_DIR, exist_ok=True)

    # ── 1. Synthesize audio ───────────────────────────────────────────────────
    print(f"🎙️  Generating audio via {TTS_ENGINE.upper()} TTS...")
    if TTS_ENGINE == "google":
        scenes = _gen_google(SCENES_TEXT)
    else:
        scenes = await _gen_edge(SCENES_TEXT)

    # ── 2. Generate solid-color background clips ──────────────────────────────
    print("\n🎨 Generating background clips...")
    video_pairs = []
    for i, scene in enumerate(scenes):
        color   = BG_COLORS[i % len(BG_COLORS)]
        bg_path = os.path.join(TEMP_DIR, f"test_bg_{scene['id']}.mp4")
        _make_bg_clip(color, scene["duration"], bg_path)
        video_pairs.append((bg_path, None))
        print(f"   BG {scene['id']}: {color} → {bg_path}")

    # ── 3. Render scenes ──────────────────────────────────────────────────────
    print("\n🎞️  Rendering scenes...")
    composer = Composer(use_avatar=False)
    rendered = []
    for i, scene in enumerate(scenes):
        path = composer.process_scene(scene, video_pairs[i], is_avatar=False)
        if path:
            rendered.append(path)
            print(f"   ✅ Scene {scene['id']}: {path}")
        else:
            print(f"   ❌ Scene {scene['id']}: render failed")

    # ── 4. Stitch with subtitles ──────────────────────────────────────────────
    # Auto hook: first sentence of first scene if HOOK_TEXT is blank
    _hook = HOOK_TEXT.strip()
    if not _hook and HOOK_DURATION > 0:
        _hook = scenes[0]["text"].split(".")[0].strip()[:55]

    print("\n🔗 Stitching with subtitles...")
    out = composer.concatenate_with_transitions(
        rendered,
        output_filename="test_output.mp4",
        script_data=scenes,
        use_subtitles=True,
        subtitle_style=SUBTITLE_STYLE,
        progress_bar=PROGRESS_BAR,
        progress_bar_color=PROGRESS_BAR_COLOR,
        hook_text=_hook,
        hook_duration=HOOK_DURATION,
    )

    if out:
        print(f"\n✅ Done → {out}")
    else:
        print("\n❌ Stitching failed.")


if __name__ == "__main__":
    asyncio.run(main())
