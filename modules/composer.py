import os
import random
import ffmpeg


def _is_constrained_env() -> bool:
    """Detecta entornos con poca RAM/CPU (p.ej. Streamlit Cloud, ~1GB/1-2 cores).

    En esos entornos correr varios FFmpeg en paralelo agota la memoria y mata el
    proceso ("Error running app"). Señales: el checkout de Streamlit Cloud vive en
    /mount/src, o la máquina tiene <= 2 núcleos.
    """
    if os.path.isdir("/mount/src"):
        return True
    if os.getenv("STREAMLIT_RUNTIME_ENV") or os.getenv("STREAMLIT_SERVER_HEADLESS") == "true":
        # Heurística adicional: en la nube headless con pocos cores, ser conservador.
        try:
            if (os.cpu_count() or 1) <= 2:
                return True
        except Exception:
            pass
    try:
        return (os.cpu_count() or 1) <= 2
    except Exception:
        return False


_CONSTRAINED = _is_constrained_env()

# Hilos para FFmpeg: 0 = auto (todos los núcleos). En entornos limitados se usa 1
# (comportamiento original estable en la nube). Configurable con FFMPEG_THREADS.
_FFMPEG_THREADS = int(os.getenv("FFMPEG_THREADS", "1" if _CONSTRAINED else "0"))

# Workers para render de escenas en paralelo (subprocesos FFmpeg independientes).
# CRÍTICO: en entornos limitados (cloud) el render se hace SECUENCIAL (1 worker)
# para no agotar RAM. En local se usan 4. Override explícito con RENDER_WORKERS.
_RENDER_WORKERS = int(os.getenv("RENDER_WORKERS", "1" if _CONSTRAINED else "4"))

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

    # Fuente para drawtext (subtitulos y hook card).
    #
    # En Windows existe arial.ttf. En un contenedor Linux NO, y si a drawtext no
    # se le pasa 'fontfile' ffmpeg aborta con "Cannot find a valid font for the
    # family Sans" — el render entero muere en el ultimo paso. Por eso se resuelve
    # aqui la primera fuente que exista de verdad.
    #
    # SUBTITLE_FONT va primero para poder cambiar la tipografia desde el entorno
    # (variable del stack en Portainer) sin tocar el codigo.
    #
    # La lista es un literal dentro de la comprension a proposito: asi el iterable
    # se evalua en el ambito de la clase y no depende de nombres de clase.
    _FONT_FILE = ([f for f in [
        os.getenv("SUBTITLE_FONT", ""),
        r'C:\Windows\Fonts\arial.ttf',
        '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
        '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
    ] if f and os.path.exists(f)] + [''])[0].replace('\\', '/')

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
        """Clean text for FFmpeg drawtext.

        Keeps full UTF-8 (Spanish accents, ñ, etc.) — Arial on Windows
        handles them fine.  Only strips:
          • Windows CRLF → LF
          • ASCII control chars (0x00-0x1F, 0x7F) that render as □ boxes
          • Fancy Unicode typography → plain ASCII equivalents
          • Non-breaking space → regular space
          • ¿ ¡ (FFmpeg drawtext can't center them reliably) → drop
        """
        import re as _re
        text = text.replace('\r\n', '\n').replace('\r', '')
        # Typography → plain ASCII
        typo = {
            '\u2026': '...', '\u2014': ' - ', '\u2013': ' - ',
            '\u201c': '"',   '\u201d': '"',
            '\u2018': "'",   '\u2019': "'",
            '\u00ab': '"',   '\u00bb': '"',
            '\u2022': '-',   '\u00b7': '-',
            '\u00a0': ' ',   # non-breaking space
            '\u00bf': '',    # ¿
            '\u00a1': '',    # ¡
        }
        for ch, rep in typo.items():
            text = text.replace(ch, rep)
        # Drop ASCII control characters — they render as □ in drawtext
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
        if self._FONT_FILE:
            kwargs['fontfile'] = self._FONT_FILE
        return kwargs

    # ── Proportional-fallback helpers ────────────────────────────────────────

    @staticmethod
    def _syllables(word: str) -> int:
        """Rough syllable count — works for Spanish and English.
        Consecutive vowels (diphthongs) count as one syllable."""
        vowels = set('aeiouáéíóúüAEIOUÁÉÍÓÚÜ')
        count, prev_vowel = 0, False
        for ch in word:
            v = ch in vowels
            if v and not prev_vowel:
                count += 1
            prev_vowel = v
        return max(1, count)

    @staticmethod
    def _detect_speech_window(audio_path: str, clip_duration: float) -> tuple:
        """Run FFmpeg silencedetect to find where speech starts and ends.
        Returns (speech_start_s, speech_end_s).
        Falls back to (0.12, clip_duration - 0.08) on any error."""
        import subprocess, re as _re
        _DEFAULT = (0.12, max(0.2, clip_duration - 0.08))
        if not audio_path or not os.path.exists(audio_path):
            return _DEFAULT
        try:
            result = subprocess.run(
                ['ffmpeg', '-i', audio_path,
                 '-af', 'silencedetect=noise=-38dB:d=0.04',
                 '-f', 'null', '-'],
                capture_output=True, text=True, errors='replace', timeout=8,
            )
            out = result.stderr
            silence_ends   = [float(m) for m in _re.findall(r'silence_end:\s*([\d.]+)', out)]
            silence_starts = [float(m) for m in _re.findall(r'silence_start:\s*([\d.]+)', out)]

            # First silence_end = end of leading silence = speech start
            speech_start = silence_ends[0] if silence_ends else _DEFAULT[0]
            # Last silence_start = start of trailing silence = speech end
            speech_end = silence_starts[-1] if silence_starts else _DEFAULT[1]

            # Sanity clamps
            speech_start = max(0.0, min(speech_start, clip_duration * 0.25))
            speech_end   = max(clip_duration * 0.5, min(speech_end, clip_duration))
            if speech_end <= speech_start:
                return _DEFAULT
            return speech_start, speech_end
        except Exception:
            return _DEFAULT

    def _apply_subtitles_to_stream(self, stream, scene_list: list, style: dict):
        """Burn subtitles onto a fully-concatenated stream with ABSOLUTE timestamps.

        Must be called AFTER all xfade filters — `t` in drawtext is the global
        PTS of the final video, so timestamps must be absolute.

        scene_list items: abs_start, clip_duration, text, audio_path, idx
        """
        import json as _json

        s            = style
        base_kw      = self._base_drawtext_kwargs(s)
        max_chars    = s.get("max_chars", 28)
        hl_color     = s.get("highlight_color", "")
        hl_opacity   = s.get("highlight_opacity", 0.9)
        hl_fontcolor = s.get("highlight_fontcolor", "black")
        _WPG         = 3   # words per subtitle group

        for scene in scene_list:
            abs_start     = scene["abs_start"]
            clip_duration = scene["clip_duration"]
            text          = scene["text"]
            audio_path    = scene.get("audio_path", "")
            idx           = scene["idx"]

            clean = self._clean_sub_text(text)
            if not clean:
                continue

            # ── Try exact word timing (.words.json) ───────────────────────────
            word_timing = None
            if audio_path:
                timing_file = audio_path + ".words.json"
                if os.path.exists(timing_file):
                    try:
                        with open(timing_file, "r", encoding="utf-8") as f:
                            word_timing = _json.load(f)
                    except Exception:
                        word_timing = None

            def _add_group(chunk_text, t0_abs, t1_abs, counter):
                sub_file = self._write_sub_file(chunk_text, idx * 1000 + counter,
                                                max_chars=max_chars)
                kw = {**base_kw,
                      "textfile": sub_file,
                      "enable":   f"between(t,{t0_abs:.4f},{t1_abs:.4f})"}
                if hl_color:
                    kw["box"]        = 1
                    kw["boxcolor"]   = f"{hl_color}@{hl_opacity:.2f}"
                    kw["boxborderw"] = 10
                    kw["fontcolor"]  = hl_fontcolor
                    kw["borderw"]    = 0
                return kw

            if word_timing:
                # ── Exact timing path ─────────────────────────────────────────
                for gi in range(0, len(word_timing), _WPG):
                    chunk_wt   = word_timing[gi:gi + _WPG]
                    chunk_text = " ".join(
                        self._clean_sub_text(wt.get("word", "")) for wt in chunk_wt
                    ).strip()
                    if not chunk_text:
                        continue
                    t0 = abs_start + chunk_wt[0]["start"]
                    t1 = abs_start + (word_timing[gi + _WPG]["start"]
                                      if gi + _WPG < len(word_timing)
                                      else chunk_wt[-1]["end"] + 0.15)
                    t1 = min(t1, abs_start + clip_duration)
                    stream = stream.filter("drawtext",
                                           **_add_group(chunk_text, t0, t1, gi))

            else:
                # ── Proportional fallback (Chirp3-HD / no timing) ─────────────
                # 1. Detect actual speech window from the audio file
                sp_start, sp_end = self._detect_speech_window(audio_path, clip_duration)
                speech_dur = max(0.1, sp_end - sp_start)

                # 2. Build 3-word chunks
                words  = clean.split()
                chunks = [" ".join(words[i:i + _WPG])
                          for i in range(0, len(words), _WPG)]
                chunks = [c for c in chunks if c]
                n = len(chunks)

                # 3. Weight each chunk by syllable count (more syllables = more time)
                syls       = [sum(self._syllables(w) for w in c.split()) for c in chunks]
                total_syls = max(1, sum(syls))
                chunk_durs = [(s / total_syls) * speech_dur for s in syls]

                # 4. Emit drawtext filters with absolute times
                t_rel = sp_start
                for ci, (chunk, dur) in enumerate(zip(chunks, chunk_durs)):
                    t0 = abs_start + t_rel
                    t1 = abs_start + (t_rel + dur if ci < n - 1 else sp_end)
                    t_rel += dur
                    stream = stream.filter("drawtext",
                                           **_add_group(chunk, t0, t1, ci))

        return stream

    # ── Visual effects helpers ────────────────────────────────────────────────

    # Ken Burns direction pool — randomly picked per clip
    _KB_STYLES = ['zoom_in', 'zoom_out', 'pan_right', 'pan_left', 'pan_up', 'pan_down']

    def _apply_ken_burns(self, stream, duration: float) -> object:
        """Gentle Ken Burns via scale+crop with time expressions.

        Replaces zoompan (too slow/choppy on cloud servers) with a
        scale-up + time-based crop pan. Fast to encode, smooth output.
        720×1280 → scale 6% bigger → crop back to 720×1280 while panning.
        """
        style = random.choice(self._KB_STYLES)
        # Scale 6% bigger so we have room to pan without black borders
        W, H  = 720, 1280
        SW    = int(W * 1.06)   # scaled width  (~763)
        SH    = int(H * 1.06)   # scaled height (~1357)
        dx    = SW - W          # extra pixels available horizontally (~43)
        dy    = SH - H          # extra pixels available vertically  (~77)

        stream = stream.filter('scale', SW, SH)

        if style == 'zoom_in':
            # Static crop centred — effective zoom because frame is bigger
            stream = stream.filter('crop', W, H, x=dx // 2, y=dy // 2)
        elif style == 'zoom_out':
            stream = stream.filter('crop', W, H, x=dx // 2, y=dy // 2)
        elif style == 'pan_right':
            # Crop x moves from 0 → dx over the clip duration
            stream = stream.filter('crop', W, H,
                                   x=f'min(t/{duration:.3f}*{dx},iw-{W})',
                                   y=dy // 2)
        elif style == 'pan_left':
            stream = stream.filter('crop', W, H,
                                   x=f'max({dx}-t/{duration:.3f}*{dx},0)',
                                   y=dy // 2)
        elif style == 'pan_up':
            stream = stream.filter('crop', W, H,
                                   x=dx // 2,
                                   y=f'max({dy}-t/{duration:.3f}*{dy},0)')
        else:  # pan_down
            stream = stream.filter('crop', W, H,
                                   x=dx // 2,
                                   y=f'min(t/{duration:.3f}*{dy},ih-{H})')
        return stream

    # Per-mode color-grade presets
    _GRADES = {
        'viral':      {'saturation': 1.35, 'contrast': 1.12, 'brightness': 0.02,  'gamma': 1.0},
        'biblia':     {'saturation': 0.85, 'contrast': 1.05, 'brightness': 0.015, 'gamma': 1.05},
        'testimonio': {'saturation': 0.92, 'contrast': 1.05, 'brightness': 0.02,  'gamma': 1.0},
        'misterio':   {'saturation': 0.60, 'contrast': 1.20, 'brightness': -0.03, 'gamma': 0.95},
        'libro':      {'saturation': 1.10, 'contrast': 1.08, 'brightness': 0.01,  'gamma': 1.0},
        'auto':       {'saturation': 1.15, 'contrast': 1.08, 'brightness': 0.01,  'gamma': 1.0},
    }

    def _apply_color_grade(self, stream, mode: str = 'auto') -> object:
        """Apply color-grading preset via FFmpeg eq filter."""
        g = self._GRADES.get(mode, self._GRADES['auto'])
        return stream.filter('eq',
                             saturation=g['saturation'],
                             contrast=g['contrast'],
                             brightness=g['brightness'],
                             gamma=g['gamma'])

    def _postprocess_progress_bar(self, video_path: str, total_dur: float,
                                  color: str = 'white', height: int = 7) -> str:
        """Burn a progress bar onto the final video via a separate FFmpeg pass.

        Runs as a subprocess instead of through the ffmpeg-python filter chain
        to avoid the naming conflict between the drawbox 't' thickness option
        and the 't' time variable used in the width expression.
        """
        import subprocess
        tmp = video_path + '.pb.mp4'
        # Use min(t/dur,1) so the bar never overflows past 100%
        vf = (
            f"drawbox=x=0:y=0"
            f":w='iw*min(t/{total_dur:.4f}\\,1)'"
            f":h={height}"
            f":color={color}@0.85"
            f":t={height}"
        )
        cmd = [
            'ffmpeg', '-y', '-i', video_path,
            '-vf', vf,
            '-c:a', 'copy',
            '-preset', 'ultrafast',
            '-crf', '26',
            tmp,
        ]
        r = subprocess.run(cmd, capture_output=True)
        if r.returncode == 0 and os.path.exists(tmp) and os.path.getsize(tmp) > 1024:
            os.replace(tmp, video_path)
            print("📊 Progress bar burned in.")
        else:
            print(f"⚠️ Progress bar failed: {r.stderr.decode(errors='ignore')[-300:]}")
            if os.path.exists(tmp):
                os.remove(tmp)
        return video_path

    def _apply_hook_card(self, stream, hook_text: str, duration: float = 2.5) -> object:
        """Overlay a bold hook title for the first `duration` seconds.

        Uses text= directly (not textfile=) so it works on Linux cloud servers
        where temp-file paths may not be accessible during FFmpeg render.
        """
        clean = self._clean_sub_text(hook_text)
        if not clean:
            return stream

        # FFmpeg drawtext text escaping: backslash, colon, single-quote
        escaped = (clean
                   .replace('\\', '\\\\')
                   .replace(':', '\\:')
                   .replace("'", "\\'"))

        enable_expr = f'between(t,0,{duration:.2f})'

        kwargs = dict(
            text=escaped,
            fontsize=68,
            fontcolor='white',
            x='(w-text_w)/2',
            y='h*0.30',
            borderw=5,
            bordercolor='black',
            box=1,
            boxcolor='black@0.50',
            boxborderw=16,
            enable=enable_expr,
        )
        if self._FONT_FILE:
            kwargs['fontfile'] = self._FONT_FILE

        return stream.drawtext(**kwargs)

    # ── Scene rendering ───────────────────────────────────────────────────────

    def process_scene(self, scene, video_pair, is_avatar=False,
                      ken_burns: bool = False, color_grade: str = None):
        """
        Combines Audio with Visuals.
        - Avatar: Loop single video + crop logo.
        - Stock: Split duration 50/50 between Video A and B.
        """
        scene_id      = scene['id']
        audio_path    = scene['audio_path']
        total_duration = scene['duration']
        output_path   = os.path.join(self.temp_dir, f"scene_{scene_id}.mp4")

        # Helper: scale + crop a single clip to 720×1280
        def _prep(path, dur, dark=False):
            s = (
                ffmpeg.input(path, stream_loop=-1)
                .trim(duration=dur)
                .setpts('PTS-STARTPTS')
                .filter('scale', 720, 1280, force_original_aspect_ratio='increase')
                .filter('crop', 720, 1280)
                .filter('fps', fps=30, round='up')
            )
            if dark:
                s = s.filter('eq', brightness=-0.06, contrast=1.1, saturation=0.75)
            if color_grade and not is_avatar:
                s = self._apply_color_grade(s, color_grade)
            if ken_burns and not is_avatar:
                s = self._apply_ken_burns(s, dur)
            return s

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
                    video_stream = ffmpeg.concat(
                        _prep(path_a, dur_a, dark=True),
                        _prep(path_b, dur_b, dark=True),
                        _prep(path_c, dur_c, dark=True),
                        v=1, a=0,
                    )

                else:
                    path_a = video_pair[0]
                    path_b = video_pair[1] if len(video_pair) > 1 else None

                    if path_b is None:
                        print(f"   ⚙️ Processing Scene {scene_id}: AI Single Clip Mode")
                        video_stream = _prep(path_a, total_duration + 0.5)
                    else:
                        print(f"   ⚙️ Processing Scene {scene_id}: A/B Split Mode")
                        video_stream = ffmpeg.concat(
                            _prep(path_a, total_duration / 2),
                            _prep(path_b, total_duration / 2 + 0.5),
                            v=1, a=0,
                        )

            # Pad audio with 0.5 s of silence so the crossfade in
            # concatenate_with_transitions (d=0.5 s) consumes only
            # silence — never the actual speech.  The video stream
            # is already built to total_duration + 0.5 s, so streams match.
            padded_audio = input_audio.audio.filter('apad', pad_dur=0.5)

            ffmpeg.output(
                video_stream,
                padded_audio,
                output_path,
                vcodec='libx264',
                acodec='aac',
                pix_fmt='yuv420p',
                preset='ultrafast',
                crf=26,
                threads=_FFMPEG_THREADS,
            ).run(overwrite_output=True, quiet=True)

            return output_path

        except ffmpeg.Error as e:
            print(f"❌ Render Fail Scene {scene_id}: {e.stderr.decode('utf8') if e.stderr else str(e)}")
            return None

    def render_all_scenes(self, script_data, video_pairs,
                          ken_burns: bool = False, color_grade: str = None):
        from concurrent.futures import ThreadPoolExecutor

        # Pick avatar scenes only if enabled and avatar file exists
        avatar_indices = []
        if self.use_avatar and len(script_data) >= 4 and os.path.exists(self.avatar_path):
            valid_range = list(range(1, len(script_data) - 1))
            count = 2 if len(valid_range) >= 2 else 1
            avatar_indices = sorted(random.sample(valid_range, count))
            print(f"🎲 Avatar set for Scenes: {[i+1 for i in avatar_indices]}")

        # ── Fase 1: decisión secuencial (barata) — qué clip usa cada escena ─────
        # Construye la lista de trabajos respetando el orden posicional. Los
        # descartes (sin audio / sin clip) NO generan trabajo.
        jobs = []   # (orden_original, scene, current_pair, is_avatar)
        for i, scene in enumerate(script_data):
            audio_path = scene.get('audio_path', '')
            if not audio_path or not os.path.exists(audio_path):
                print(f"   ⚠️ Skipping Scene {scene['id']} — audio file not found.")
                continue
            if scene.get('duration', 0) <= 0:
                print(f"   ⚠️ Skipping Scene {scene['id']} — duration is zero or invalid.")
                continue

            current_pair = video_pairs[i] if i < len(video_pairs) else None
            is_avatar    = False

            if i in avatar_indices:
                current_pair = (self.avatar_path, None)
                is_avatar    = True
            elif current_pair is None:
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

            jobs.append((i, scene, current_pair, is_avatar))

        if not jobs:
            return []

        # ── Fase 2: render en paralelo (subprocesos FFmpeg independientes) ──────
        # Cada process_scene lanza su propio ffmpeg → se solapan en CPU/IO.
        # Se preserva el orden posicional indexando por la posición del trabajo.
        results = [None] * len(jobs)

        def _render(job_idx, scene, pair, is_av):
            return job_idx, self.process_scene(
                scene, pair, is_av,
                ken_burns=ken_burns, color_grade=color_grade,
            )

        workers = max(1, min(_RENDER_WORKERS, len(jobs)))
        with ThreadPoolExecutor(max_workers=workers) as ex:
            futures = [
                ex.submit(_render, jidx, scene, pair, is_av)
                for jidx, (_orig, scene, pair, is_av) in enumerate(jobs)
            ]
            for fut in futures:
                jidx, path = fut.result()
                results[jidx] = path

        # Mantener orden y descartar fallos (None)
        return [p for p in results if p]

    def concatenate_with_transitions(
        self,
        video_paths,
        output_filename: str = "final_short.mp4",
        script_data=None,
        use_subtitles: bool = False,
        subtitle_style: dict = None,
        progress_bar: bool = False,
        progress_bar_color: str = 'white',
        hook_text: str = '',
        hook_duration: float = 2.5,
    ):
        """Stitch rendered scenes with xfade transitions.

        Optional effects applied to the final concatenated stream:
          • Subtitles (word-by-word, exact or proportional timing)
          • Progress bar (thin bar at top that fills over total duration)
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
        # v_trans == a_trans == 0.5 s — MUST be equal so video and audio streams
        # have the same total duration in the output.  If they differ the shorter
        # stream ends first and the video freezes while audio keeps playing
        # (or vice-versa) for N_transitions × |v_trans-a_trans| seconds.
        #
        # Using c1='exp' c2='exp' on acrossfade: exponential curves fade each
        # voice out/in very quickly, so the 0.5 s window doesn't sound like two
        # people talking at once — the outgoing voice drops to near-silence within
        # the first ~0.1 s, then the incoming voice rises to full volume.
        a_trans     = v_trans   # keep equal → no freeze at end
        input0      = ffmpeg.input(valid_paths[0])
        v_stream    = input0.video
        a_stream    = input0.audio
        current_dur = valid_durs[0]

        for i in range(1, len(valid_paths)):
            next_clip = ffmpeg.input(valid_paths[i])
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
                # c1='tri': la cola del clip saliente es el silencio del apad, asi que
                #   este fundido de salida es inaudible.
                # c2='nofade': la voz entrante ARRANCA A VOLUMEN PLENO. Es obligatorio:
                #   con cualquier curva de entrada (tri, exp...) la voz sube desde cero
                #   durante a_trans segundos y se oye "viniendo desde abajo", porque
                #   audio.py recorta el silencio de cabeza y la rampa cae sobre habla.
                #   No hay riesgo de dos voces solapadas MIENTRAS apad >= a_trans:
                #   el apad de 0.5 s garantiza que el tramo solapado del clip saliente
                #   sea silencio. Si algun dia se baja el apad, revisar esto.
                c1='tri',
                c2='nofade',
            )
            current_dur = (current_dur + valid_durs[i]) - v_trans

        # ── Step 2: Absolute start time of each clip (same offset for audio & video)
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

        # ── Step 4: Hook card (bold opener text, first N seconds) ────────────
        if hook_text and hook_text.strip():
            print(f"   🪝 Hook card: \"{hook_text[:50]}\"")
            v_stream = self._apply_hook_card(v_stream, hook_text, duration=hook_duration)

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
                threads=_FFMPEG_THREADS,
            ).run(overwrite_output=True, quiet=False)

            print(f"✅ FINAL VIDEO SAVED: {output_path}")
            self._strip_metadata(output_path)

            # ── Step 5: Progress bar — separate FFmpeg pass after main encode ──
            # Done post-encode to avoid the drawbox 't' option conflicting with
            # the 't' time variable inside the width expression.
            if progress_bar:
                self._postprocess_progress_bar(output_path, current_dur,
                                               color=progress_bar_color)

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
