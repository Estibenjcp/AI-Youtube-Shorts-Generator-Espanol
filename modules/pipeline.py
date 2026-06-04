"""Pipeline de generacion de video (extraido de app.py en el refactor).

Orquesta el flujo completo: guion (brain) -> audio -> assets (Pexels/IA)
-> render (composer) -> copy/thumbnail/webhook.

Se comunica con la UI a traves de log_q (queue) y recibe toda la
configuracion por params (dict). No depende del estado de Streamlit.
"""
import os
import sys
import io
import json
import shutil
import asyncio
import queue
import importlib  # re-exportado por compatibilidad; ya no se usa reload

import modules.topic_history as _topic_history

# Raiz del proyecto (este archivo vive en modules/, subimos un nivel).
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def run_pipeline(log_q: queue.Queue, params: dict):
    import sys, io

    class QueueWriter(io.TextIOBase):
        def write(self, msg):
            if msg and msg.strip():
                log_q.put(msg.rstrip())
            return len(msg) if msg else 0

        def flush(self):
            pass

    old_stdout = sys.stdout
    sys.stdout = QueueWriter()

    try:
        # Nota: ya no se usa importlib.reload aquí. Los cambios de API key/secrets
        # desde la UI se aplican con load_dotenv(override=True) + _get_client.cache_clear()
        # en el momento de guardar (ver sección de configuración).
        from modules.brain         import ContentBrain
        from modules.audio         import AudioEngine
        from modules.asset_manager import AssetManager
        from modules.composer      import Composer

        pipeline_lang = params.get("lang", "es")

        log_q.put("STAGE:Brain")
        brain         = ContentBrain()
        pipeline_mode = params.get("mode", "auto")

        # Si el usuario usa Video IA, sobrescribe num_scenes con el cálculo duracion/clip
        _video_src = params.get("video_source", "pexels")
        if _video_src == "ai_video_test":
            # Test Mode: fuerza 1 escena de 5s sin importar los sliders
            _ai_num_scenes = 1
            _ai_clip_dur   = 5
            log_q.put("🧪 Test Mode: generando 1 escena de 5s para verificar el modelo...")
        elif _video_src == "ai_video":
            _ai_num_scenes = int(params.get("ai_video_num_scenes", 6))
            _ai_clip_dur   = int(params.get("ai_video_clip_duration", 5))
            log_q.put(f"⏱️ Video IA: {_ai_num_scenes} escenas × {_ai_clip_dur}s = ~{_ai_num_scenes * _ai_clip_dur}s")
        else:
            _ai_num_scenes = params.get("num_scenes", 9)
            _ai_clip_dur   = 5

        # Palabras máx por escena para guiar al LLM (TTS ≈ 2.3 pal/s)
        if _video_src in ("ai_video", "ai_video_test"):
            _max_wpsc = max(8, int(_ai_clip_dur * 2.3))
        else:
            _target_secs   = params.get("target_total_secs", 0)
            _secs_per_scene = (_target_secs / max(1, _ai_num_scenes)) if _target_secs > 0 else 0
            _max_wpsc = max(8, int(_secs_per_scene * 2.3)) if _secs_per_scene > 0 else 999

        if pipeline_mode == "viral":
            topic       = params.get("topic", "").strip()
            category    = params.get("category", "").strip()
            chosen_hook = params.get("chosen_hook", "").strip()
            if not topic:
                topic = brain.get_trending_topic("", lang=pipeline_lang,
                                                 category_hint=category, mode="viral")
                # Local dedup retry — zero extra tokens
                for _ in range(3):
                    if not _topic_history.is_duplicate(topic, lang=pipeline_lang): break
                    topic = brain.get_trending_topic("", lang=pipeline_lang,
                                                     category_hint=category, mode="viral")
            script = brain.generate_viral_script(topic, category, lang=pipeline_lang,
                                                 chosen_hook=chosen_hook, num_scenes=_ai_num_scenes,
                                                 max_words_per_scene=_max_wpsc)

        elif pipeline_mode == "testimonio":
            topic       = params.get("topic", "").strip()
            category    = params.get("category", "").strip()
            chosen_hook = params.get("chosen_hook", "").strip()
            if not topic:
                topic = brain.get_trending_topic("", lang=pipeline_lang,
                                                 category_hint=category, mode="testimonio")
                for _ in range(3):
                    if not _topic_history.is_duplicate(topic, lang=pipeline_lang): break
                    topic = brain.get_trending_topic("", lang=pipeline_lang,
                                                     category_hint=category, mode="testimonio")
            script = brain.generate_testimonio_script(topic, category, lang=pipeline_lang,
                                                      chosen_hook=chosen_hook, num_scenes=_ai_num_scenes,
                                                      max_words_per_scene=_max_wpsc)

        elif pipeline_mode == "misterio_biblico":
            topic       = params.get("topic", "").strip()
            category    = params.get("category", "").strip()
            chosen_hook = params.get("chosen_hook", "").strip()
            if not topic:
                topic = brain.get_trending_topic("", lang=pipeline_lang,
                                                 category_hint=category, mode="misterio_biblico")
                for _ in range(3):
                    if not _topic_history.is_duplicate(topic, lang=pipeline_lang): break
                    topic = brain.get_trending_topic("", lang=pipeline_lang,
                                                     category_hint=category, mode="misterio_biblico")
            script = brain.generate_misterio_biblico_script(topic, category, lang=pipeline_lang,
                                                             chosen_hook=chosen_hook, num_scenes=_ai_num_scenes,
                                                             max_words_per_scene=_max_wpsc)

        elif pipeline_mode == "libro":
            topic       = params.get("topic", "").strip()
            category    = params.get("category", "").strip()
            chosen_hook = params.get("chosen_hook", "").strip()
            if not topic:
                topic = brain.get_trending_topic("", lang=pipeline_lang,
                                                 category_hint=category, mode="libro")
                for _ in range(3):
                    if not _topic_history.is_duplicate(topic, lang=pipeline_lang): break
                    topic = brain.get_trending_topic("", lang=pipeline_lang,
                                                     category_hint=category, mode="libro")
            script = brain.generate_book_summary_script(topic, category, lang=pipeline_lang,
                                                        chosen_hook=chosen_hook, num_scenes=_ai_num_scenes,
                                                        max_words_per_scene=_max_wpsc)

        elif pipeline_mode == "biblia":
            topic       = params.get("topic", "").strip()
            category    = params.get("category", "").strip()
            chosen_hook = params.get("chosen_hook", "").strip()
            if not topic:
                topic = brain.get_trending_topic("", lang=pipeline_lang,
                                                 category_hint=category, mode="biblia")
                for _ in range(3):
                    if not _topic_history.is_duplicate(topic, lang=pipeline_lang): break
                    topic = brain.get_trending_topic("", lang=pipeline_lang,
                                                     category_hint=category, mode="biblia")
            script = brain.generate_bible_script(topic, category, lang=pipeline_lang,
                                                 chosen_hook=chosen_hook, num_scenes=_ai_num_scenes,
                                                 max_words_per_scene=_max_wpsc)

        elif pipeline_mode == "empleo":
            offer_text = params.get("job_offer_text", "").strip()
            if not offer_text:
                log_q.put("ERROR:No se proporcionó texto de oferta de empleo.")
                return
            script = brain.generate_job_offer_script(offer_text, lang=pipeline_lang)
            # Derive a clean topic from the first line of the offer for copy/filename
            _lines = [l.strip() for l in offer_text.splitlines() if l.strip()]
            topic  = _lines[0][:70] if _lines else ("Oferta de Empleo" if pipeline_lang == "es" else "Job Offer")
            print(f"💼 Topic derivado: {topic}")

        elif pipeline_mode == "guion":
            guion_text = params.get("guion_raw_text", "").strip()
            if not guion_text:
                log_q.put("ERROR:No se proporcionó texto para el guion libre.")
                return
            script = brain.generate_freeform_script(guion_text, lang=pipeline_lang)
            # Derive topic from first non-empty line for copy/filename
            _lines = [l.strip() for l in guion_text.splitlines() if l.strip()]
            topic  = _lines[0][:70] if _lines else ("Guion Libre" if pipeline_lang == "es" else "Freeform Script")
            print(f"✍️ Topic derivado: {topic}")

        elif pipeline_mode == "podcast":
            _pod_topic  = params.get("podcast_topic", params.get("topic", "")).strip()
            _host_name  = params.get("host_name", "Host")
            _guest_name = params.get("guest_name", "Invitado")
            _n_exc      = int(params.get("num_exchanges", 6))
            # Use podcast_voice_a as the primary voice if provided
            _pod_voice_a = params.get("podcast_voice_a", "").strip()
            if _pod_voice_a:
                params["voice"] = _pod_voice_a
            topic = _pod_topic or ("Episodio de podcast" if pipeline_lang == "es" else "Podcast episode")
            script = brain.generate_podcast_script(
                topic         = _pod_topic or topic,
                host_name     = _host_name,
                guest_name    = _guest_name,
                lang          = pipeline_lang,
                num_exchanges = _n_exc,
                max_words_per_scene = _max_wpsc,
            )

        elif pipeline_mode == "novela":
            novela_theme = params.get("novela_theme", "").strip()
            if not novela_theme:
                log_q.put("ERROR:Por favor describe el tema de la mini historia.")
                return
            log_q.put("🎬 [Mininovela] Generando biblia creativa...")
            bible = brain.generate_miniseries_bible(novela_theme, lang=pipeline_lang)
            topic = bible.get("title", novela_theme[:60])
            log_q.put(f"🎬 [Mininovela] Historia: {topic} ({bible.get('genre','')})")
            log_q.put(f"🎭 Personajes: {', '.join(c['name'] for c in bible.get('characters',[]))}")
            log_q.put("📝 [Mininovela] Escribiendo guión por escenas...")
            script = brain.generate_miniseries_script(bible, lang=pipeline_lang, num_scenes=_ai_num_scenes)

        elif pipeline_mode == "true_crime":
            topic       = params.get("topic", "").strip()
            category    = params.get("category", "").strip()
            chosen_hook = params.get("chosen_hook", "").strip()
            if not topic:
                topic = brain.get_trending_topic("", lang=pipeline_lang,
                                                 category_hint=category, mode="true_crime")
                for _ in range(3):
                    if not _topic_history.is_duplicate(topic, lang=pipeline_lang): break
                    topic = brain.get_trending_topic("", lang=pipeline_lang,
                                                     category_hint=category, mode="true_crime")
            script = brain.generate_script(topic, num_scenes=_ai_num_scenes,
                                           lang=pipeline_lang, chosen_hook=chosen_hook)

        elif pipeline_mode == "psicologia_oscura":
            topic       = params.get("topic", "").strip()
            category    = params.get("category", "").strip()
            chosen_hook = params.get("chosen_hook", "").strip()
            if not topic:
                topic = brain.get_trending_topic("", lang=pipeline_lang,
                                                 category_hint=category, mode="psicologia_oscura")
                for _ in range(3):
                    if not _topic_history.is_duplicate(topic, lang=pipeline_lang): break
                    topic = brain.get_trending_topic("", lang=pipeline_lang,
                                                     category_hint=category, mode="psicologia_oscura")
            script = brain.generate_script(topic, num_scenes=_ai_num_scenes,
                                           lang=pipeline_lang, chosen_hook=chosen_hook)

        elif pipeline_mode == "conspiracion":
            topic       = params.get("topic", "").strip()
            category    = params.get("category", "").strip()
            chosen_hook = params.get("chosen_hook", "").strip()
            if not topic:
                topic = brain.get_trending_topic("", lang=pipeline_lang,
                                                 category_hint=category, mode="conspiracion")
                for _ in range(3):
                    if not _topic_history.is_duplicate(topic, lang=pipeline_lang): break
                    topic = brain.get_trending_topic("", lang=pipeline_lang,
                                                     category_hint=category, mode="conspiracion")
            script = brain.generate_script(topic, num_scenes=_ai_num_scenes,
                                           lang=pipeline_lang, chosen_hook=chosen_hook)

        elif pipeline_mode == "ciencia_misterio":
            topic       = params.get("topic", "").strip()
            category    = params.get("category", "").strip()
            chosen_hook = params.get("chosen_hook", "").strip()
            if not topic:
                topic = brain.get_trending_topic("", lang=pipeline_lang,
                                                 category_hint=category, mode="ciencia_misterio")
                for _ in range(3):
                    if not _topic_history.is_duplicate(topic, lang=pipeline_lang): break
                    topic = brain.get_trending_topic("", lang=pipeline_lang,
                                                     category_hint=category, mode="ciencia_misterio")
            script = brain.generate_script(topic, num_scenes=_ai_num_scenes,
                                           lang=pipeline_lang, chosen_hook=chosen_hook)

        elif pipeline_mode == "finanzas":
            topic       = params.get("topic", "").strip()
            category    = params.get("category", "").strip()
            chosen_hook = params.get("chosen_hook", "").strip()
            if not topic:
                topic = brain.get_trending_topic("", lang=pipeline_lang,
                                                 category_hint=category, mode="finanzas")
                for _ in range(3):
                    if not _topic_history.is_duplicate(topic, lang=pipeline_lang): break
                    topic = brain.get_trending_topic("", lang=pipeline_lang,
                                                     category_hint=category, mode="finanzas")
            script = brain.generate_script(topic, num_scenes=_ai_num_scenes,
                                           lang=pipeline_lang, chosen_hook=chosen_hook)

        elif pipeline_mode == "mentalidad":
            topic       = params.get("topic", "").strip()
            category    = params.get("category", "").strip()
            chosen_hook = params.get("chosen_hook", "").strip()
            if not topic:
                topic = brain.get_trending_topic("", lang=pipeline_lang,
                                                 category_hint=category, mode="mentalidad")
                for _ in range(3):
                    if not _topic_history.is_duplicate(topic, lang=pipeline_lang): break
                    topic = brain.get_trending_topic("", lang=pipeline_lang,
                                                     category_hint=category, mode="mentalidad")
            script = brain.generate_script(topic, num_scenes=_ai_num_scenes,
                                           lang=pipeline_lang, chosen_hook=chosen_hook)

        elif pipeline_mode == "historia_epica":
            topic       = params.get("topic", "").strip()
            category    = params.get("category", "").strip()
            chosen_hook = params.get("chosen_hook", "").strip()
            if not topic:
                topic = brain.get_trending_topic("", lang=pipeline_lang,
                                                 category_hint=category, mode="historia_epica")
                for _ in range(3):
                    if not _topic_history.is_duplicate(topic, lang=pipeline_lang): break
                    topic = brain.get_trending_topic("", lang=pipeline_lang,
                                                     category_hint=category, mode="historia_epica")
            script = brain.generate_script(topic, num_scenes=_ai_num_scenes,
                                           lang=pipeline_lang, chosen_hook=chosen_hook)

        elif pipeline_mode == "psicologia_positiva":
            topic       = params.get("topic", "").strip()
            category    = params.get("category", "").strip()
            chosen_hook = params.get("chosen_hook", "").strip()
            if not topic:
                topic = brain.get_trending_topic("", lang=pipeline_lang,
                                                 category_hint=category, mode="psicologia_positiva")
                for _ in range(3):
                    if not _topic_history.is_duplicate(topic, lang=pipeline_lang): break
                    topic = brain.get_trending_topic("", lang=pipeline_lang,
                                                     category_hint=category, mode="psicologia_positiva")
            script = brain.generate_script(topic, num_scenes=_ai_num_scenes,
                                           lang=pipeline_lang, chosen_hook=chosen_hook)

        elif pipeline_mode == "mente_masculina":
            topic       = params.get("topic", "").strip()
            category    = params.get("category", "").strip()
            chosen_hook = params.get("chosen_hook", "").strip()
            if not topic:
                topic = brain.get_trending_topic("", lang=pipeline_lang,
                                                 category_hint=category, mode="mente_masculina")
                for _ in range(3):
                    if not _topic_history.is_duplicate(topic, lang=pipeline_lang): break
                    topic = brain.get_trending_topic("", lang=pipeline_lang,
                                                     category_hint=category, mode="mente_masculina")
            script = brain.generate_script(topic, num_scenes=_ai_num_scenes,
                                           lang=pipeline_lang, chosen_hook=chosen_hook)

        elif pipeline_mode == "mujer_consciente":
            topic       = params.get("topic", "").strip()
            category    = params.get("category", "").strip()
            chosen_hook = params.get("chosen_hook", "").strip()
            if not topic:
                topic = brain.get_trending_topic("", lang=pipeline_lang,
                                                 category_hint=category, mode="mujer_consciente")
                for _ in range(3):
                    if not _topic_history.is_duplicate(topic, lang=pipeline_lang): break
                    topic = brain.get_trending_topic("", lang=pipeline_lang,
                                                     category_hint=category, mode="mujer_consciente")
            script = brain.generate_script(topic, num_scenes=_ai_num_scenes,
                                           lang=pipeline_lang, chosen_hook=chosen_hook)

        elif pipeline_mode == "indignacion":
            topic       = params.get("topic", "").strip()
            category    = params.get("category", "").strip()
            chosen_hook = params.get("chosen_hook", "").strip()
            if not topic:
                topic = brain.get_trending_topic("", lang=pipeline_lang,
                                                 category_hint=category, mode="indignacion")
                for _ in range(3):
                    if not _topic_history.is_duplicate(topic, lang=pipeline_lang): break
                    topic = brain.get_trending_topic("", lang=pipeline_lang,
                                                     category_hint=category, mode="indignacion")
            script = brain.generate_script(topic, num_scenes=_ai_num_scenes,
                                           lang=pipeline_lang, chosen_hook=chosen_hook)

        elif pipeline_mode == "indignacion_meme":
            category   = params.get("category", "").strip()
            _n_memes   = int(params.get("num_scenes", 7))
            # Memes no tienen topic per se — la categoría es suficiente
            # Si el usuario escribió algo lo usamos como context hint para el prompt
            _meme_hint = params.get("topic", "").strip()
            _cat_with_hint = f"{category} — enfocado en: {_meme_hint}" if _meme_hint and category else (
                _meme_hint or category or ""
            )
            topic  = _meme_hint or category or ("Meme Laboral" if pipeline_lang == "es" else "Work Meme")
            script = brain.generate_meme_laboral_script(
                category  = _cat_with_hint,
                lang      = pipeline_lang,
                num_memes = _n_memes,
            )

        elif pipeline_mode == "ciencia_facil":
            topic       = params.get("topic", "").strip()
            category    = params.get("category", "").strip()
            chosen_hook = params.get("chosen_hook", "").strip()
            if not topic:
                topic = brain.get_trending_topic("", lang=pipeline_lang,
                                                 category_hint=category, mode="ciencia_facil")
                for _ in range(3):
                    if not _topic_history.is_duplicate(topic, lang=pipeline_lang): break
                    topic = brain.get_trending_topic("", lang=pipeline_lang,
                                                     category_hint=category, mode="ciencia_facil")
            script = brain.generate_ciencia_facil_script(topic, category=category,
                                                         lang=pipeline_lang,
                                                         chosen_hook=chosen_hook,
                                                         num_scenes=_ai_num_scenes,
                                                         max_words_per_scene=_max_wpsc)

        else:
            chosen_hook = params.get("chosen_hook", "").strip()
            topic  = brain.get_trending_topic(params.get("topic", ""),
                                              lang=pipeline_lang, mode="auto")
            if not params.get("topic", "").strip():
                for _ in range(3):
                    if not _topic_history.is_duplicate(topic, lang=pipeline_lang): break
                    topic = brain.get_trending_topic("", lang=pipeline_lang, mode="auto")
            script = brain.generate_script(topic, num_scenes=_ai_num_scenes,
                                           lang=pipeline_lang, chosen_hook=chosen_hook)

        if not script:
            log_q.put("ERROR:Script generation failed.")
            return

        # ── TEST MODE: reemplaza el texto de la escena con frase corta (~3s TTS)
        if _video_src == "ai_video_test":
            _test_phrase = (
                "Verificando modelo de video con inteligencia artificial."
                if pipeline_lang == "es"
                else "Testing AI video model generation clip."
            )
            script = [script[0]]
            script[0]["text"] = _test_phrase
            log_q.put(f"🧪 Texto de test forzado: \"{_test_phrase}\"")

        # ── AI VIDEO MODE: recortar texto de cada escena para que el TTS no supere
        # la duración del clip de IA.  TTS ≈ 2.3 palabras/segundo en español.
        # Sin este límite el LLM puede escribir 20+ seg de narración por escena,
        # y FFmpeg loopeará el clip de 5s muchas veces.
        if _video_src in ("ai_video", "ai_video_test") and script:
            _words_per_sec = 2.3          # velocidad conservadora (con margen)
            _max_words     = max(8, int(_ai_clip_dur * _words_per_sec))
            _capped_count  = 0
            for _sc in script:
                _wlist = _sc.get("text", "").split()
                if len(_wlist) > _max_words:
                    # Cortar en el último punto o coma antes del límite si existe
                    _truncated = " ".join(_wlist[:_max_words])
                    # Asegurar que termine en punto
                    if not _truncated.endswith((".", "!", "?")):
                        _truncated = _truncated.rstrip(",;:") + "."
                    _sc["text"] = _truncated
                    _capped_count += 1
            if _capped_count:
                log_q.put(
                    f"✂️ {_capped_count} escena(s) recortadas a ≤{_max_words} palabras "
                    f"para caber en {_ai_clip_dur}s por clip"
                )

        log_q.put("STAGE:Audio")
        _tts_choice = params.get("tts_engine", "edge_tts")
        if _tts_choice == "voxcpm":
            from modules.audio import VoxCPMAudioEngine
            audio_engine = VoxCPMAudioEngine(
                voice_description = params.get("vox_voice_desc", ""),
                lang              = pipeline_lang,
                mood_enabled      = params.get("vox_mood_enabled", True),
                reference_audio   = params.get("vox_clone_ref", ""),
            )
            log_q.put("🤖 [VoxCPM] Motor de voz local activado (mood-adaptive)")
        elif _tts_choice == "google_tts":
            from modules.audio import GoogleTTSAudioEngine
            audio_engine = GoogleTTSAudioEngine(
                api_key      = params.get("gtts_api_key", ""),
                voice_name   = params.get("gtts_voice_name", "es-US-Neural2-B"),
                lang_code    = params.get("gtts_lang_code", "es-US"),
                speaking_rate= params.get("gtts_rate", 1.0),
                pitch        = params.get("gtts_pitch", 0.0),
            )
            log_q.put(f"🔵 [Google TTS] Voz: {params.get('gtts_voice_name')} · rate={params.get('gtts_rate', 1.0):.2f}×")
        else:
            audio_engine = AudioEngine(
                voice   = params.get("voice", "es-ES-AlvaroNeural"),
                rate    = params.get("rate", "+10%"),
                voice_b = params.get("podcast_voice_b", ""),
            )
        _video_src = params.get("video_source", "pexels")
        if _video_src in ("ai_video", "ai_video_test"):
            # AI video usa audio_duration (best_duration) → audio PRIMERO, luego clips.
            script = asyncio.run(audio_engine.process_script(script))
            log_q.put("STAGE:Assets")
            from modules.ai_video import AIVideoEngine
            _ai_vid_engine = AIVideoEngine(
                provider      = params.get("ai_video_provider", "fal"),
                api_key       = params.get("ai_video_key", ""),
                model         = params.get("ai_video_model", ""),
                style         = params.get("ai_video_style", "cinematic"),
                clip_duration = _ai_clip_dur,
                max_parallel  = 2,
            )
            log_q.put(f"🤖 [AI Video] Proveedor: {params.get('ai_video_provider','fal').upper()} · Estilo: {params.get('ai_video_style','cinematic')}")
            # Mostrar el prompt que se enviará al modelo para cada escena
            for _sc_prev in script[:3]:  # máximo 3 para no saturar el log
                _prev_prompt = _ai_vid_engine._build_prompt(_sc_prev)
                log_q.put(f"📽️ Prompt escena {_sc_prev['id']}: {_prev_prompt[:120]}…")
            log_q.put("⏳ Generando clips de video con IA (puede tardar varios minutos)...")
            _ai_result = asyncio.run(_ai_vid_engine.process_script(script))
            # {scene_id: [path]} → lista posicional [(path_a, path_b), ...] igual que AssetManager
            _failed_scenes = []
            _assets_list = []
            for _sc in script:
                _sid = _sc["id"]
                if _sid in _ai_result:
                    _assets_list.append((_ai_result[_sid][0], None))
                else:
                    _assets_list.append(None)
                    _failed_scenes.append(_sc)
            if _failed_scenes:
                log_q.put(f"⚠️ {len(_failed_scenes)} escenas sin clip IA — usando Pexels como respaldo...")
                asset_manager = AssetManager()
                _fallback_list = asset_manager.get_videos(_failed_scenes)
                _fb_idx = 0
                for _k in range(len(_assets_list)):
                    if _assets_list[_k] is None and _fb_idx < len(_fallback_list):
                        _assets_list[_k] = _fallback_list[_fb_idx]
                        _fb_idx += 1
            assets_map = _assets_list
        else:
            # Pexels NO depende del audio → generar audio y descargar clips EN PARALELO.
            log_q.put("STAGE:Assets")
            asset_manager = AssetManager()

            async def _audio_and_assets():
                t_audio  = asyncio.create_task(audio_engine.process_script(script))
                t_assets = asyncio.create_task(asyncio.to_thread(asset_manager.get_videos, script))
                return await asyncio.gather(t_audio, t_assets)

            script, assets_map = asyncio.run(_audio_and_assets())

        log_q.put("STAGE:Composer")
        composer = Composer(use_avatar=params.get("use_avatar", False))

        # ── Visual effects from params ────────────────────────────────────────
        _ken_burns    = params.get("fx_ken_burns", False)
        _color_grade  = params.get("video_mode", "auto") if params.get("fx_color_grade", True) else None
        _progress_bar = params.get("fx_progress_bar", False)
        _pb_color     = params.get("fx_progress_bar_color", "#FFFFFF").lstrip("#")
        _pb_color_ffmpeg = f"0x{_pb_color}" if _pb_color else "white"

        # ── Hook card: LLM-generated if enabled and text is blank ────────────
        _hook_text = ""
        if params.get("fx_hook_card", False):
            _hook_text = (params.get("fx_hook_text") or "").strip()
            if not _hook_text and script:
                log_q.put("🪝 Generando texto de enganche con IA...")
                try:
                    _hook_text = brain.generate_hook_text(
                        topic=topic,
                        script=script,
                        lang=pipeline_lang,
                        mode=pipeline_mode,
                    )
                    log_q.put(f"🪝 Hook: \"{_hook_text}\"")
                except Exception as _he:
                    print(f"⚠️ Hook generation error: {_he}")
                    _hook_text = script[0].get("text", "").split(".")[0].strip()[:50]
        _hook_dur = float(params.get("fx_hook_duration", 2.5))

        final_scene_paths = composer.render_all_scenes(
            script, assets_map,
            ken_burns=_ken_burns,
            color_grade=_color_grade,
        )
        if not final_scene_paths:
            log_q.put("ERROR:No scenes were rendered.")
            return

        final_video_path = composer.concatenate_with_transitions(
            final_scene_paths, script_data=script,
            use_subtitles=params.get("use_subtitles", False),
            subtitle_style=params.get("subtitle_style", {}),
            progress_bar=_progress_bar,
            progress_bar_color=_pb_color_ffmpeg,
            hook_text=_hook_text,
            hook_duration=_hook_dur,
        )

        if params.get("use_music") and params.get("music_file_path") and final_video_path:
            log_q.put("🎵 Mezclando música de fondo...")
            composer.mix_background_music(
                final_video_path,
                music_path=params["music_file_path"],
                volume=params.get("music_volume", 0.15),
                fade_in=params.get("music_fade_in", 1.0),
                fade_out=params.get("music_fade_out", 2.0),
                loop=params.get("music_loop", True),
            )

        log_q.put("🧹 Metadatos eliminados del video final.")

        for folder in ["audio_clips", "video_clips", "temp"]:
            p = os.path.join(_BASE_DIR, "assets", folder)
            if os.path.exists(p):
                shutil.rmtree(p)
                os.makedirs(p, exist_ok=True)

        copy_data    = brain.generate_copy(topic, script, lang=pipeline_lang, mode=pipeline_mode)
        thumb_prompt = brain.generate_thumbnail_prompt(
            topic, script, lang=pipeline_lang,
            mode=pipeline_mode,
            offer_text=params.get("job_offer_text", ""),
        )

        log_q.put(f"COPY:{__import__('json').dumps(copy_data)}")
        log_q.put(f"THUMB:{thumb_prompt}")
        log_q.put(f"SCRIPT:{__import__('json').dumps(script)}")
        log_q.put(f"TOPIC:{topic}")

        # ── Registrar tema usado (evita repeticiones futuras) ─────────────────
        try:
            from modules import topic_history as _th
            _th.add_topic(
                topic,
                mode=pipeline_mode,
                lang=pipeline_lang,
                category=params.get("category", ""),
            )
        except Exception:
            pass

        # ── Enviar a webhook n8n ──────────────────────────────
        webhook_url = params.get("webhook_url", "").strip()
        if webhook_url:
            try:
                import requests as _req, base64 as _b64
                video_path  = os.path.join(_BASE_DIR, "assets", "final", "final_short.mp4")
                script_text = " ".join(s.get("text", "") for s in script)

                payload = {
                    "topic":               topic,
                    "lang":                pipeline_lang,
                    "mode":                pipeline_mode,
                    "script_text":         script_text,
                    "youtube_title":       copy_data.get("youtube_title", ""),
                    "youtube_description": copy_data.get("youtube_description", ""),
                    "tiktok_caption":      copy_data.get("tiktok_caption", ""),
                    "facebook_caption":    copy_data.get("facebook_caption", ""),
                    "thumbnail_prompt":    thumb_prompt,
                    "video_base64":        "",
                    "video_filename":      "final_short.mp4",
                    "video_mimetype":      "video/mp4",
                }

                if os.path.exists(video_path):
                    with open(video_path, "rb") as _vf:
                        payload["video_base64"] = _b64.b64encode(_vf.read()).decode("utf-8")
                    print(f"📡 Enviando video + datos al webhook n8n...")
                else:
                    print("📡 Enviando datos al webhook n8n (sin video)...")

                resp = _req.post(
                    webhook_url,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=180,
                )
                if resp.status_code in (200, 201, 202):
                    print(f"✅ Webhook n8n OK ({resp.status_code})")
                else:
                    print(f"⚠️ Webhook respondió {resp.status_code}: {resp.text[:200]}")
            except Exception as _we:
                print(f"⚠️ Webhook error: {_we}")

        log_q.put("DONE")

    except Exception as e:
        import traceback
        log_q.put(f"ERROR:{e}")
        for line in traceback.format_exc().splitlines():
            log_q.put(line)
    finally:
        sys.stdout = old_stdout
