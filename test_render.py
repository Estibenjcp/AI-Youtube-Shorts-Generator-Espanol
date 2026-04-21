"""
Quick 2-scene render test.
Run:  python test_render.py
Output: assets/final/test_output.mp4

Edit SCENES, VOICE and STYLE below to test different configurations.
"""
import asyncio
import os
import ffmpeg

# ── Configure your test here ─────────────────────────────────────────────────

VOICE = "es-ES-AlvaroNeural"   # Edge TTS voice to test
RATE  = "+0%"                  # speaking rate

SCENES_TEXT = [
    "Hace miles de años, una civilización olvidada construyó monumentos que todavía hoy desafían toda explicación conocida por la ciencia moderna.",
    "Los secretos enterrados bajo sus ruinas revelan una tecnología tan avanzada que ningún experto ha podido explicar cómo fue posible crearla.",
]

SUBTITLE_STYLE = {
    "fontsize":    44,
    "fontcolor":   "white",
    "y":           "h*0.82",
    "borderw":     3,
    "bordercolor": "black",
    "box":         0,
    "boxcolor":    "black@0.4",
    "max_chars":   28,
    # Uncomment to test highlight box:
    # "highlight_color":    "0xFFD700",
    # "highlight_fontcolor": "black",
}

# Background colors (one per scene) — any FFmpeg color string
BG_COLORS = ["0x1a1a2e", "0x16213e"]

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


async def main():
    from modules.audio import EdgeTTS
    from modules.composer import Composer
    from mutagen.mp3 import MP3

    os.makedirs(TEMP_DIR,  exist_ok=True)
    os.makedirs(FINAL_DIR, exist_ok=True)

    # ── 1. Synthesize audio ───────────────────────────────────────────────────
    tts    = EdgeTTS(voice=VOICE, rate=RATE, output_dir=TEMP_DIR)
    scenes = []

    print("🎙️  Generating audio...")
    for idx, text in enumerate(SCENES_TEXT, start=1):
        filename   = f"test_voice_{idx}.mp3"
        audio_path = await tts.generate_audio(text, filename)
        duration   = MP3(audio_path).info.length
        scenes.append({"id": idx, "text": text, "audio_path": audio_path, "duration": duration})
        print(f"   Scene {idx}: {duration:.2f}s → {audio_path}")

    # ── 2. Generate solid-color background clips ──────────────────────────────
    print("\n🎨 Generating background clips...")
    video_pairs = []
    for i, scene in enumerate(scenes):
        color    = BG_COLORS[i % len(BG_COLORS)]
        bg_path  = os.path.join(TEMP_DIR, f"test_bg_{scene['id']}.mp4")
        _make_bg_clip(color, scene["duration"], bg_path)
        video_pairs.append((bg_path, None))   # single-clip mode → loops bg
        print(f"   BG {scene['id']}: {color} → {bg_path}")

    # ── 3. Render scenes (audio + video) ─────────────────────────────────────
    print("\n🎞️  Rendering scenes...")
    composer  = Composer(use_avatar=False)
    rendered  = []
    for i, scene in enumerate(scenes):
        path = composer.process_scene(scene, video_pairs[i], is_avatar=False)
        if path:
            rendered.append(path)
            print(f"   ✅ Scene {scene['id']}: {path}")
        else:
            print(f"   ❌ Scene {scene['id']}: render failed")

    # ── 4. Stitch with subtitles ──────────────────────────────────────────────
    print("\n🔗 Stitching with subtitles...")
    out = composer.concatenate_with_transitions(
        rendered,
        output_filename="test_output.mp4",
        script_data=scenes,
        use_subtitles=True,
        subtitle_style=SUBTITLE_STYLE,
    )

    if out:
        print(f"\n✅ Done → {out}")
    else:
        print("\n❌ Stitching failed.")


if __name__ == "__main__":
    asyncio.run(main())
