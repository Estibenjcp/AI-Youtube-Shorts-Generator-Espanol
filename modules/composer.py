import os
import random
import ffmpeg

class Composer:
    def __init__(self, use_avatar: bool = True):
        self.temp_dir    = os.path.join(os.getcwd(), "assets", "temp")
        self.final_dir   = os.path.join(os.getcwd(), "assets", "final")
        self.avatar_path = os.path.join(os.getcwd(), "assets", "avatar", "avatars.mp4")
        self.outro_path  = os.path.join(os.getcwd(), "assets", "avatar", "final.mp4")
        self.use_avatar  = use_avatar

        os.makedirs(self.temp_dir,  exist_ok=True)
        os.makedirs(self.final_dir, exist_ok=True)

        self.transitions = ['fade', 'diagbr', 'diagtl']

    def get_duration(self, filepath):
        try:
            probe = ffmpeg.probe(filepath)
            return float(probe['format']['duration'])
        except:
            return 0.0

    # ── Subtitle helpers ──────────────────────────────────────────────────────

    _WINDOWS_FONT = r'C:\Windows\Fonts\arial.ttf'

    # Default subtitle style — all keys can be overridden via the style dict
    _DEFAULT_STYLE = {
        "fontsize":    44,
        "fontcolor":   "white",
        "y":           "h*0.82",
        "borderw":     3,
        "bordercolor": "black",
        "box":         0,
        "boxcolor":    "black@0.4",
        "max_chars":   28,
    }

    @staticmethod
    def _wrap_text_file(text: str, max_chars: int = 28) -> str:
        """Wraps text with real newlines for writing to a temp file."""
        words = text.split()
        lines, current = [], []
        for word in words:
            current.append(word)
            if len(' '.join(current)) > max_chars:
                lines.append(' '.join(current[:-1]))
                current = [word]
        if current:
            lines.append(' '.join(current))
        return '\n'.join(lines)

    @staticmethod
    def _clean_sub_text(text: str) -> str:
        """Strip Unicode chars that fonts can't render (avoids □ boxes)."""
        import re as _re
        # Strip carriage returns first (Windows CRLF → LF)
        text = text.replace('\r\n', '\n').replace('\r', '')
        replacements = {
            '\u2026': ',', '\u2014': '-', '\u2013': '-',
            '\u201c': '"', '\u201d': '"', '\u2018': "'", '\u2019': "'",
            '\u00ab': '"', '\u00bb': '"', '\u2022': '-', '\u00b7': '-',
            '\u00a0': ' ',  # non-breaking space → regular space
            '\u00bf': '',   # ¿ → drop
            '\u00a1': '',   # ¡ → drop
            '\u00e1': 'a', '\u00e9': 'e', '\u00ed': 'i', '\u00f3': 'o', '\u00fa': 'u',
            '\u00c1': 'A', '\u00c9': 'E', '\u00cd': 'I', '\u00d3': 'O', '\u00da': 'U',
            '\u00f1': 'n', '\u00d1': 'N', '\u00fc': 'u', '\u00dc': 'U',
        }
        for ch, rep in replacements.items():
            text = text.replace(ch, rep)
        # Drop any remaining non-ASCII
        text = _re.sub(r'[^\x00-\x7F]', '', text)
        # Drop ASCII control characters (0x00-0x08, 0x0B, 0x0C, 0x0E-0x1F, 0x7F)
        # that FFmpeg drawtext renders as □ boxes
        text = _re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
        return _re.sub(r'\s+', ' ', text).strip()

    def _write_sub_file(self, text: str, index: int, max_chars: int = 28) -> str:
        """Cleans text, wraps it, writes to a temp file with LF-only line endings.
        Returns forward-slash path for FFmpeg."""
        path = os.path.join(self.temp_dir, f"sub_{index}.txt")
        content = self._wrap_text_file(self._clean_sub_text(text), max_chars=max_chars)
        # Use newline='\n' to prevent Python on Windows from writing \r\n
        # (FFmpeg drawtext reads \r as a glyph → shows □)
        with open(path, 'w', encoding='utf-8', newline='\n') as f:
            f.write(content)
        return path.replace('\\', '/')

    def _base_drawtext_kwargs(self, s: dict) -> dict:
        """Shared drawtext kwargs from a resolved style dict."""
        kwargs = dict(
            fontsize=s["fontsize"],
            fontcolor=s["fontcolor"],
            x='(w-text_w)/2',
            y=s["y"],
            borderw=s["borderw"],
            bordercolor=s["bordercolor"],
        )
        if s.get("box"):
            kwargs["box"]        = 1
            kwargs["boxcolor"]   = s["boxcolor"]
            kwargs["boxborderw"] = 8
        if os.path.exists(self._WINDOWS_FONT):
            kwargs['fontfile'] = self._WINDOWS_FONT.replace('\\', '/')
        return kwargs

    def _apply_subtitles_to_stream(self, stream, scene_list: list, style: dict):
        """Burn subtitles onto a fully-concatenated stream with ABSOLUTE timestamps.

        This must be called AFTER all xfade/concat filters so that `t` in FFmpeg
        drawtext refers to the global PTS of the final video, not a per-clip PTS.

        scene_list: list of dicts, each with keys:
            abs_start   – absolute start time of this clip in the final video (s)
            clip_duration – duration of this clip (s)
            text        – subtitle text
            audio_path  – path to the .mp3 (used to find .words.json)
            idx         – global index (for unique temp-file naming)
        """
        import json as _json

        s         = style
        base_kw   = self._base_drawtext_kwargs(s)
        max_chars = s.get("max_chars", 28)
        hl_color  = s.get("highlight_color", "")
        hl_opacity   = s.get("highlight_opacity", 0.9)
        hl_fontcolor = s.get("highlight_fontcolor", "black")

        _WPG = 3   # words shown per subtitle group

        for scene in scene_list:
            abs_start     = scene["abs_start"]
            clip_duration = scene["clip_duration"]
            text          = scene["text"]
            audio_path    = scene.get("audio_path", "")
            idx           = scene["idx"]

            clean = self._clean_sub_text(text)
            if not clean:
                continue

            # ── Try exact word timing from .words.json ────────────────────────
            word_timing = None
            if audio_path:
                timing_file = audio_path + ".words.json"
                if os.path.exists(timing_file):
                    try:
                        with open(timing_file, "r", encoding="utf-8") as f:
                            word_timing = _json.load(f)
                    except Exception:
                        word_timing = None

            if word_timing:
                # Build 3-word groups with exact timing, offset to absolute time
                for gi in range(0, len(word_timing), _WPG):
                    chunk_wt = word_timing[gi:gi + _WPG]
                    chunk_text = " ".join(
                        self._clean_sub_text(wt.get("word", "")) for wt in chunk_wt
                    ).strip()
                    if not chunk_text:
                        continue
                    # Absolute times in the final video
                    t0 = abs_start + chunk_wt[0]["start"]
                    if gi + _WPG < len(word_timing):
                        t1 = abs_start + word_timing[gi + _WPG]["start"]
                    else:
                        t1 = abs_start + chunk_wt[-1]["end"] + 0.15
                    t1 = min(t1, abs_start + clip_duration)

                    sub_file = self._write_sub_file(chunk_text, idx * 1000 + gi,
                                                    max_chars=max_chars)
                    kw = {**base_kw,
                          "textfile": sub_file,
                          "enable":   f"between(t,{t0:.4f},{t1:.4f})"}
                    if hl_color:
                        kw["box"]        = 1
                        kw["boxcolor"]   = f"{hl_color}@{hl_opacity:.2f}"
                        kw["boxborderw"] = 10
                        kw["fontcolor"]  = hl_fontcolor
                        kw["borderw"]    = 0
                    stream = stream.filter("drawtext", **kw)

            else:
                # ── Proportional fallback (no .words.json) ────────────────────
                words = clean.split()
                if not words:
                    continue
                chunks = [" ".join(words[i:i + _WPG]) for i in range(0, len(words), _WPG)]
                chunks = [c for c in chunks if c]
                n = len(chunks)

                # Uniform distribution over the speech window (skip TTS leading silence)
                _LEAD  = 0.15
                _TRAIL = 0.10
                speech_dur = max(0.1, clip_duration - _LEAD - _TRAIL)
                chunk_dur  = speech_dur / n

                t_rel = _LEAD
                for ci, chunk in enumerate(chunks):
                    t0 = abs_start + t_rel
                    t1 = abs_start + (t_rel + chunk_dur if ci < n - 1 else clip_duration)
                    t_rel += chunk_dur
                    sub_file = self._write_sub_file(chunk, idx * 1000 + ci,
                                                    max_chars=max_chars)
                    kw = {**base_kw,
                          "textfile": sub_file,
                          "enable":   f"between(t,{t0:.3f},{t1:.3f})"}
                    if hl_color:
                        kw["box"]        = 1
                        kw["boxcolor"]   = f"{hl_color}@{hl_opacity:.2f}"
                        kw["boxborderw"] = 10
                        kw["fontcolor"]  = hl_fontcolor
                        kw["borderw"]    = 0
                    stream = stream.filter("drawtext", **kw)

        return stream

    # ── Scene rendering ───────────────────────────────────────────────────────

    def process_scene(self, scene, video_pair, is_avatar=False):
        """
        Combines Audio with Visuals.
        - Avatar: Loop single video + crop logo.
        - Stock: Split duration 50/50 between Video A and B.
        """
        scene_id      = scene['id']
        audio_path    = scene['audio_path']
        total_duration = scene['duration']
        output_path   = os.path.join(self.temp_dir, f"scene_{scene_id}.mp4")

        try:
            input_audio = ffmpeg.input(audio_path)

            if is_avatar:
                print(f"   ⚙️ Processing Scene {scene_id}: Avatar Mode")
                video_stream = (
                    ffmpeg.input(video_pair[0], stream_loop=-1)
                    .trim(duration=total_duration + 0.5)
                    .setpts('PTS-STARTPTS')
                    .filter('crop', 'iw', 'ih-150', 0, 0)
                    .filter('scale', 720, 1280, force_original_aspect_ratio='increase')
                    .filter('crop', 720, 1280)
                    .filter('fps', fps=30, round='up')
                )
            else:
                if len(video_pair) == 3:
                    print(f"   ⚙️ Processing Scene {scene_id}: A/B/C Testimonio Mode")
                    path_a, path_b, path_c = video_pair
                    dur_a = total_duration / 3
                    dur_b = total_duration / 3
                    dur_c = total_duration - dur_a - dur_b + 0.5

                    def _dark_stream(path, dur):
                        return (
                            ffmpeg.input(path, stream_loop=-1)
                            .trim(duration=dur)
                            .setpts('PTS-STARTPTS')
                            .filter('scale', 720, 1280, force_original_aspect_ratio='increase')
                            .filter('crop', 720, 1280)
                            .filter('fps', fps=30, round='up')
                            .filter('eq', brightness=-0.06, contrast=1.1, saturation=0.75)
                        )

                    stream_a = _dark_stream(path_a, dur_a)
                    stream_b = _dark_stream(path_b, dur_b)
                    stream_c = _dark_stream(path_c, dur_c)
                    video_stream = ffmpeg.concat(stream_a, stream_b, stream_c, v=1, a=0)

                else:
                    path_a = video_pair[0]
                    path_b = video_pair[1] if len(video_pair) > 1 else None

                    if path_b is None:
                        # Single AI-generated clip — loop it for the full scene duration
                        print(f"   ⚙️ Processing Scene {scene_id}: AI Single Clip Mode")
                        video_stream = (
                            ffmpeg.input(path_a, stream_loop=-1)
                            .trim(duration=total_duration + 0.5)
                            .setpts('PTS-STARTPTS')
                            .filter('scale', 720, 1280, force_original_aspect_ratio='increase')
                            .filter('crop', 720, 1280)
                            .filter('fps', fps=30, round='up')
                        )
                    else:
                        print(f"   ⚙️ Processing Scene {scene_id}: A/B Split Mode")
                        duration_a = total_duration / 2
                        duration_b = (total_duration / 2) + 0.5

                        stream_a = (
                            ffmpeg.input(path_a, stream_loop=-1)
                            .trim(duration=duration_a)
                            .setpts('PTS-STARTPTS')
                            .filter('scale', 720, 1280)
                            .filter('crop', 720, 1280)
                            .filter('fps', fps=30, round='up')
                        )
                        stream_b = (
                            ffmpeg.input(path_b, stream_loop=-1)
                            .trim(duration=duration_b)
                            .setpts('PTS-STARTPTS')
                            .filter('scale', 720, 1280)
                            .filter('crop', 720, 1280)
                            .filter('fps', fps=30, round='up')
                        )
                        video_stream = ffmpeg.concat(stream_a, stream_b, v=1, a=0)

            ffmpeg.output(
                video_stream,
                input_audio,
                output_path,
                vcodec='libx264',
                acodec='aac',
                pix_fmt='yuv420p',
                preset='ultrafast',
                crf=26,
                threads=1,
                shortest=None,
            ).run(overwrite_output=True, quiet=True)

            return output_path

        except ffmpeg.Error as e:
            print(f"❌ Render Fail Scene {scene_id}: {e.stderr.decode('utf8') if e.stderr else str(e)}")
            return None

    def render_all_scenes(self, script_data, video_pairs):
        rendered_paths = []

        # Pick avatar scenes only if enabled and avatar file exists
        avatar_indices = []
        if self.use_avatar and len(script_data) >= 4 and os.path.exists(self.avatar_path):
            valid_range = list(range(1, len(script_data) - 1))
            count = 2 if len(valid_range) >= 2 else 1
            avatar_indices = sorted(random.sample(valid_range, count))
            print(f"🎲 Avatar set for Scenes: {[i+1 for i in avatar_indices]}")

        for i, scene in enumerate(script_data):
            # Guard: skip scene if audio file is missing
            audio_path = scene.get('audio_path', '')
            if not audio_path or not os.path.exists(audio_path):
                print(f"   ⚠️ Skipping Scene {scene['id']} — audio file not found.")
                continue

            # Guard: skip scene if duration is zero (failed audio generation)
            if scene.get('duration', 0) <= 0:
                print(f"   ⚠️ Skipping Scene {scene['id']} — duration is zero or invalid.")
                continue

            current_pair = video_pairs[i] if i < len(video_pairs) else None
            is_avatar    = False

            if i in avatar_indices:
                current_pair = (self.avatar_path, None)
                is_avatar    = True
            elif current_pair is None:
                # ── Fallback: borrow video from the nearest scene that succeeded ──
                fallback_pair = None
                for offset in range(1, len(video_pairs)):
                    for candidate in [i - offset, i + offset]:
                        if 0 <= candidate < len(video_pairs) and video_pairs[candidate] is not None:
                            fallback_pair = video_pairs[candidate]
                            print(f"   ♻️  Scene {scene['id']} video failed — borrowing clip from scene {candidate+1}.")
                            break
                    if fallback_pair:
                        break
                if fallback_pair is None:
                    print(f"   ❌ Scene {scene['id']} — no video fallback found, skipping.")
                    continue
                current_pair = fallback_pair

            path = self.process_scene(scene, current_pair, is_avatar)
            if path:
                rendered_paths.append(path)

        return rendered_paths

    def concatenate_with_transitions(
        self,
        video_paths,
        output_filename: str = "final_short.mp4",
        script_data=None,
        use_subtitles: bool = False,
        subtitle_style: dict = None,
    ):
        """
        Stitches rendered scenes with xfade transitions.
        Optionally burns subtitles from script_data onto each scene.
        subtitle_style: dict with keys fontsize, fontcolor, y, borderw, bordercolor, box, boxcolor, max_chars.
        """
        print("🎬 Stitching final video...")
        output_path = os.path.join(self.final_dir, output_filename)

        if os.path.exists(output_path):
            try:
                os.remove(output_path)
            except:
                print("⚠️ Could not delete old file — it may be open in a player.")

        if not video_paths:
            return None

        # Append outro if it exists — normalize to 1080x1920 and ensure audio track
        if os.path.exists(self.outro_path):
            outro_normalized = os.path.join(self.temp_dir, "outro_normalized.mp4")
            try:
                probe      = ffmpeg.probe(self.outro_path)
                has_audio  = any(s['codec_type'] == 'audio' for s in probe['streams'])
                outro_dur  = float(probe['format']['duration'])

                video_in = (
                    ffmpeg.input(self.outro_path)
                    .filter('scale', 720, 1280, force_original_aspect_ratio='increase')
                    .filter('crop', 720, 1280)
                    .filter('fps', fps=30, round='up')
                )

                if has_audio:
                    audio_in = ffmpeg.input(self.outro_path).audio
                else:
                    audio_in = (
                        ffmpeg
                        .input('anullsrc=r=44100:cl=stereo', format='lavfi', t=outro_dur)
                        .audio
                    )

                (
                    ffmpeg
                    .output(video_in, audio_in, outro_normalized,
                            vcodec='libx264', acodec='aac',
                            pix_fmt='yuv420p', movflags='faststart')
                    .run(overwrite_output=True, quiet=True)
                )
                video_paths = list(video_paths) + [outro_normalized]
                print("🎬 Outro appended.")
            except Exception as e:
                print(f"⚠️ Could not normalize outro: {e} — skipping.")

        # Merge user style with defaults
        _style = {**self._DEFAULT_STYLE, **(subtitle_style or {})}

        # Collect raw scene texts + audio paths (indexed by original video position)
        sub_texts       = {}
        sub_audio_paths = {}
        if use_subtitles and script_data:
            for i, scene in enumerate(script_data):
                if i < len(video_paths):
                    sub_texts[i]       = scene.get('text', '')
                    sub_audio_paths[i] = scene.get('audio_path', '')

        # Pre-filter: drop any clip whose duration cannot be probed or is too short for xfade
        v_trans           = 0.5
        valid_paths       = []
        valid_texts       = {}
        valid_audio_paths = {}
        valid_durs        = []   # actual duration of each valid clip (needed for abs offset calc)
        for orig_i, vp in enumerate(video_paths):
            d = self.get_duration(vp)
            if d <= v_trans:
                print(f"   ⚠️ Skipping clip {orig_i} in stitch — duration {d:.2f}s too short.")
                continue
            ni = len(valid_paths)
            valid_texts[ni]       = sub_texts.get(orig_i, '')
            valid_audio_paths[ni] = sub_audio_paths.get(orig_i, '')
            valid_durs.append(d)
            valid_paths.append(vp)

        if not valid_paths:
            print("❌ No valid clips left after duration check.")
            return None

        # ── Step 1: Build xfade chain WITHOUT subtitles ───────────────────────
        input0      = ffmpeg.input(valid_paths[0])
        v_stream    = input0.video
        a_stream    = input0.audio
        current_dur = valid_durs[0]

        for i in range(1, len(valid_paths)):
            next_clip = ffmpeg.input(valid_paths[i])
            a_trans   = 0.05
            offset    = current_dur - v_trans
            effect    = random.choice(self.transitions)
            print(f"   ✨ Transition {i}: '{effect}' at {offset:.2f}s")

            v_stream = ffmpeg.filter(
                [v_stream, next_clip.video],
                'xfade',
                transition=effect,
                duration=v_trans,
                offset=offset,
            )
            a_stream = ffmpeg.filter(
                [a_stream, next_clip.audio],
                'acrossfade',
                d=a_trans,
            )
            current_dur = (current_dur + valid_durs[i]) - v_trans

        # ── Step 2: Calculate absolute start time of each clip in the final video
        # clip[0] starts at 0; each subsequent clip starts after the previous
        # duration minus the xfade overlap (v_trans = 0.5s per transition).
        abs_starts = [0.0]
        for i in range(1, len(valid_paths)):
            abs_starts.append(abs_starts[i - 1] + valid_durs[i - 1] - v_trans)

        # ── Step 3: Burn subtitles onto the fully-concatenated v_stream ────────
        if use_subtitles:
            scene_list = []
            for i in range(len(valid_paths)):
                if valid_texts.get(i):
                    scene_list.append({
                        "idx":          i,
                        "abs_start":    abs_starts[i],
                        "clip_duration": valid_durs[i],
                        "text":         valid_texts[i],
                        "audio_path":   valid_audio_paths.get(i, ''),
                    })
            if scene_list:
                v_stream = self._apply_subtitles_to_stream(v_stream, scene_list, _style)

        try:
            ffmpeg.output(
                v_stream,
                a_stream,
                output_path,
                vcodec='libx264',
                acodec='aac',
                pix_fmt='yuv420p',
                movflags='faststart',
                preset='ultrafast',
                crf=26,
                threads=1,
            ).run(overwrite_output=True, quiet=False)

            print(f"✅ FINAL VIDEO SAVED: {output_path}")
            self._strip_metadata(output_path)
            return output_path

        except ffmpeg.Error as e:
            print(f"❌ Stitching Error: {e.stderr.decode('utf8') if e.stderr else str(e)}")
            return None

    def mix_background_music(self, video_path: str, music_path: str,
                             volume: float = 0.15, fade_in: float = 1.0,
                             fade_out: float = 2.0, loop: bool = True) -> str:
        """Mezcla música de fondo bajo el audio TTS del video final."""
        import subprocess
        if not os.path.exists(music_path):
            print(f"⚠️ Music file not found: {music_path}")
            return video_path
        vid_dur = self.get_duration(video_path)
        if vid_dur <= 0:
            return video_path
        fade_out_start = max(0.0, vid_dur - fade_out)
        out_tmp = video_path.replace(".mp4", "_bgm.mp4")
        vol_clamped = max(0.01, min(float(volume), 2.0))
        if loop:
            music_prep = f"[1:a]aloop=loop=-1:size=2000000000,atrim=duration={vid_dur},asetpts=PTS-STARTPTS,volume={vol_clamped},afade=t=in:d={fade_in},afade=t=out:st={fade_out_start}:d={fade_out}[bgm]"
        else:
            music_prep = f"[1:a]volume={vol_clamped},afade=t=in:d={fade_in},afade=t=out:st={fade_out_start}:d={fade_out}[bgm]"
        filter_graph = f"{music_prep};[0:a][bgm]amix=inputs=2:duration=first:dropout_transition=2[aout]"
        cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-i", music_path,
            "-filter_complex", filter_graph,
            "-map", "0:v",
            "-map", "[aout]",
            "-c:v", "copy",
            "-c:a", "aac",
            "-shortest",
            out_tmp,
        ]
        result = subprocess.run(cmd, capture_output=True)
        if result.returncode == 0 and os.path.exists(out_tmp):
            os.replace(out_tmp, video_path)
            print("🎵 Background music mixed successfully.")
        else:
            print(f"❌ Music mix failed: {result.stderr.decode('utf-8', errors='ignore')[-300:]}")
            if os.path.exists(out_tmp):
                os.remove(out_tmp)
        return video_path

    @staticmethod
    def _strip_metadata(video_path: str) -> None:
        """Remove all metadata from the final video using FFmpeg stream copy (no re-encode).
        Overwrites the file in-place via a temp file."""
        import subprocess, os, shutil
        tmp = video_path + ".clean.mp4"
        try:
            result = subprocess.run(
                [
                    "ffmpeg", "-y",
                    "-i", video_path,
                    "-map_metadata", "-1",   # drop all global metadata
                    "-map_chapters", "-1",   # drop chapter markers
                    "-c", "copy",            # no re-encode — instant
                    "-movflags", "faststart",
                    tmp,
                ],
                capture_output=True,
            )
            if result.returncode == 0 and os.path.exists(tmp) and os.path.getsize(tmp) > 1024:
                shutil.move(tmp, video_path)
                print("🧹 Metadata stripped from final video.")
            else:
                print("⚠️  Metadata strip skipped (ffmpeg error) — keeping original.")
                if os.path.exists(tmp):
                    os.remove(tmp)
        except Exception as e:
            print(f"⚠️  Metadata strip failed: {e}")
