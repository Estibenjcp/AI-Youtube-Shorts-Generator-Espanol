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

    def _write_sub_file(self, text: str, index: int, max_chars: int = 28) -> str:
        """Writes scene text to a temp file and returns its path (forward slashes)."""
        path = os.path.join(self.temp_dir, f"sub_{index}.txt")
        with open(path, 'w', encoding='utf-8') as f:
            f.write(self._wrap_text_file(text, max_chars=max_chars))
        # FFmpeg requires forward slashes even on Windows
        return path.replace('\\', '/')

    def _apply_subtitle(self, stream, text_file_path: str, style: dict = None):
        """Adds subtitle overlay using a textfile. Style dict overrides defaults."""
        s = {**self._DEFAULT_STYLE, **(style or {})}
        kwargs = dict(
            textfile=text_file_path,
            fontsize=s["fontsize"],
            fontcolor=s["fontcolor"],
            x='(w-text_w)/2',
            y=s["y"],
            borderw=s["borderw"],
            bordercolor=s["bordercolor"],
        )
        if s.get("box"):
            kwargs["box"]      = 1
            kwargs["boxcolor"] = s["boxcolor"]
            kwargs["boxborderw"] = 8
        if os.path.exists(self._WINDOWS_FONT):
            kwargs['fontfile'] = self._WINDOWS_FONT.replace('\\', '/')
        return stream.filter('drawtext', **kwargs)

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
                    print(f"   ⚙️ Processing Scene {scene_id}: A/B Split Mode")
                    path_a, path_b = video_pair
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

        # Pre-create subtitle text files before building the filter graph
        sub_files = {}
        if use_subtitles and script_data:
            for i, scene in enumerate(script_data):
                if i < len(video_paths):
                    sub_files[i] = self._write_sub_file(scene.get('text', ''), i,
                                                        max_chars=_style["max_chars"])

        # Pre-filter: drop any clip whose duration cannot be probed or is too short for xfade
        v_trans = 0.5
        valid_paths  = []
        valid_subs   = {}
        for orig_i, vp in enumerate(video_paths):
            d = self.get_duration(vp)
            if d <= v_trans:
                print(f"   ⚠️ Skipping clip {orig_i} in stitch — duration {d:.2f}s too short.")
                continue
            valid_subs[len(valid_paths)] = sub_files.get(orig_i)
            valid_paths.append(vp)

        if not valid_paths:
            print("❌ No valid clips left after duration check.")
            return None

        input0   = ffmpeg.input(valid_paths[0])
        v_stream = input0.video
        a_stream = input0.audio

        if valid_subs.get(0):
            v_stream = self._apply_subtitle(v_stream, valid_subs[0], style=_style)

        current_dur = self.get_duration(valid_paths[0])

        for i in range(1, len(valid_paths)):
            next_clip = ffmpeg.input(valid_paths[i])
            next_v    = next_clip.video
            next_dur  = self.get_duration(valid_paths[i])

            if valid_subs.get(i):
                next_v = self._apply_subtitle(next_v, valid_subs[i], style=_style)

            v_trans = 0.5   # video xfade duration
            a_trans = 0.05  # audio crossfade — near-instant cut, no pop, no overlap
            offset  = current_dur - v_trans
            effect  = random.choice(self.transitions)
            print(f"   ✨ Transition {i}: '{effect}' at {offset:.2f}s")

            v_stream = ffmpeg.filter(
                [v_stream, next_v],
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
            current_dur = (current_dur + next_dur) - v_trans

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
            return output_path

        except ffmpeg.Error as e:
            print(f"❌ Stitching Error: {e.stderr.decode('utf8') if e.stderr else str(e)}")
            return None
