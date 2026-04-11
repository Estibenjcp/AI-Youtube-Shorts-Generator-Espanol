import streamlit as st
import threading
import asyncio
import queue
import os
import re
import time
import zipfile
import importlib
import shutil
import io

from modules.config import load_config, check_config, PROVIDER_DEFAULTS
from modules.categories import TOPIC_CATEGORIES_ES, TOPIC_CATEGORIES_EN
from dotenv import set_key, load_dotenv

# ── Page config ──────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="AutoShorts AI",
    page_icon="🎬",
    layout="wide",
)

# ── Autenticación ─────────────────────────────────────────────────────────────

def _check_auth() -> bool:
    """Bloquea la app con contraseña. Contraseña guardada en st.secrets o .env."""
    app_password = (
        st.secrets.get("APP_PASSWORD", None)
        if hasattr(st, "secrets")
        else None
    ) or os.getenv("APP_PASSWORD", "")

    if not app_password:
        return True  # Sin contraseña configurada = acceso libre

    if st.session_state.get("authenticated"):
        return True

    st.markdown(
        """
        <style>
        .login-box {
            max-width: 380px;
            margin: 10vh auto;
            padding: 2.5rem;
            border-radius: 12px;
            background: #1e1e2e;
            box-shadow: 0 4px 32px rgba(0,0,0,0.4);
            text-align: center;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    with st.container():
        col_l, col_c, col_r = st.columns([1, 2, 1])
        with col_c:
            st.markdown("## 🎬 AutoShorts AI")
            st.markdown("Ingresa la contraseña para continuar.")
            pwd = st.text_input("Contraseña / Password", type="password", key="pwd_input")
            if st.button("Entrar", use_container_width=True, type="primary"):
                if pwd == app_password:
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error("Contraseña incorrecta.")

    st.stop()

_check_auth()

# ── Constants ────────────────────────────────────────────────────────────────

ENV_PATH         = os.path.join(os.path.dirname(__file__), ".env")
FINAL_VIDEO_PATH = os.path.join(os.path.dirname(__file__), "assets", "final", "final_short.mp4")
STAGES           = ["Brain", "Audio", "Assets", "Composer"]

VOICES_ES = {
    "Dalia — México Femenina (recomendada)": "es-MX-DaliaNeural",
    "Jorge — México Masculino":               "es-MX-JorgeNeural",
    "Elvira — España Femenina":               "es-ES-ElviraNeural",
    "Álvaro — España Masculino":              "es-ES-AlvaroNeural",
    "Paloma — EE.UU. Femenina":              "es-US-PalomaNeural",
    "Alonso — EE.UU. Masculino":             "es-US-AlonsoNeural",
    "Camila — Perú Femenina":                "es-PE-CamilaNeural",
    "Salomé — Colombia Femenina":            "es-CO-SalomeNeural",
    "Elena — Argentina Femenina":            "es-AR-ElenaNeural",
}

VOICES_EN = {
    "Ava — US Female (default)":  "en-US-AvaNeural",
    "Andrew — US Male":           "en-US-AndrewNeural",
    "Emma — US Female":           "en-US-EmmaNeural",
    "Brian — US Male":            "en-US-BrianNeural",
    "Jenny — US Female":          "en-US-JennyNeural",
    "Guy — US Male":              "en-US-GuyNeural",
    "Sonia — UK Female":          "en-GB-SoniaNeural",
    "Ryan — UK Male":             "en-GB-RyanNeural",
    "Natasha — AU Female":        "en-AU-NatashaNeural",
    "William — AU Male":          "en-AU-WilliamNeural",
}

# ── Textos de la UI por idioma ────────────────────────────────────────────────

UI = {
    "es": {
        "page_title":        "Generar YouTube Short en Español",
        "page_caption":      "Un clic — video completo sin cara desde el tema hasta el MP4 final.",
        "api_settings":      "Configuración de API",
        "ai_provider":       "Proveedor de IA",
        "ai_key":            "Clave API de IA",
        "model":             "Modelo",
        "pexels_key":        "Clave API de Pexels",
        "save_api":          "Guardar Configuración",
        "api_saved":         "Configuración guardada.",
        "video_settings":    "Configuración de Video",
        "narrator_voice":    "Voz del Narrador",
        "preview_btn":       "▶ Previsualizar",
        "preview_text":      "Hola, así es como sueno. Espero que disfrutes este video.",
        "generating":        "Generando...",
        "speech_rate":       "Velocidad de Voz",
        "speech_help":       "0% = velocidad normal. Positivo = más rápido.",
        "avatar_toggle":     "Activar Avatar",
        "avatar_help":       "Inserta tu video avatar en 1-2 escenas del medio.",
        "subtitles_toggle":  "Quemar Subtítulos",
        "subtitles_help":    "Renderiza el texto de cada escena como subtítulos en pantalla.",
        "config_ready":      "Config: Lista",
        "config_incomplete": "Config: Incompleta — completa los ajustes de API arriba.",
        "step1":             "Paso 1 — Selecciona una categoría",
        "category_placeholder": "— Elige una categoría —",
        "step2":             "Paso 2 — Obtén sugerencias de temas virales",
        "suggest_btn":       "💡 Sugerir Temas Virales",
        "clear_btn":         "Limpiar",
        "suggest_spinner":   "Generando temas virales para",
        "suggest_caption":   "Selecciona un tema para generar tu video:",
        "step3":             "Paso 3 — Confirma tu tema",
        "topic_label":       "Tema (escribe uno propio o usa las sugerencias de arriba)",
        "topic_placeholder": "ej. El experimento secreto que casi destruyó la Luna...",
        "scenes_label":      "Escenas",
        "generate_btn":      "Generar Video",
        "config_info":       "Completa y guarda tu configuración de API en la barra lateral para habilitar la generación.",
        "log_area":          "Log del Pipeline",
        "stages_labels":     {"Brain": "Cerebro", "Audio": "Audio", "Assets": "Assets", "Composer": "Compositor"},
        "done_msg":          "¡Video generado con éxito!",
        "download_zip":      "⬇️ Descargar Kit Completo (.zip)",
        "video_header":      "Video",
        "download_mp4":      "Descargar MP4",
        "video_not_found":   "Video no encontrado.",
        "script_header":     "Guion",
        "script_unavail":    "Guion no disponible.",
        "visuals_header":    "Palabras Clave Visuales",
        "thumb_header":      "Prompt para Miniatura",
        "copy_header":       "Copy para Redes Sociales",
        "yt_title_label":    "Título",
        "chars_label":       "caracteres",
        "desc_caption":      "Descripción",
        "tiktok_caption_hint": "Gancho + keyword · Contexto · CTA + hashtags de nicho",
        "fb_caption_hint":   "Afirmación gancho · Contexto · CTA + 3 hashtags máximo",
        "error_prefix":      "Pipeline fallido:",
        "error_hint":        "Revisa el log de arriba y verifica tus claves de API en la barra lateral.",
        "zip_title":         "TÍTULO:",
        "zip_desc":          "DESCRIPCIÓN:",
        "script_scene":      "Escena",
        "default_voice":     "Álvaro — España Masculino",
    },
    "en": {
        "page_title":        "Generate YouTube Short",
        "page_caption":      "One click — full faceless video from topic to final MP4.",
        "api_settings":      "API Settings",
        "ai_provider":       "AI Provider",
        "ai_key":            "AI API Key",
        "model":             "Model",
        "pexels_key":        "Pexels API Key",
        "save_api":          "Save API Settings",
        "api_saved":         "API settings saved.",
        "video_settings":    "Video Settings",
        "narrator_voice":    "Narrator Voice",
        "preview_btn":       "▶ Preview",
        "preview_text":      "Hello! This is how I sound. I hope you enjoy this video.",
        "generating":        "Generating...",
        "speech_rate":       "Speech Rate",
        "speech_help":       "0% = normal speed. Positive = faster.",
        "avatar_toggle":     "Enable Avatar Injection",
        "avatar_help":       "Inserts your avatar video into 1-2 middle scenes.",
        "subtitles_toggle":  "Burn Subtitles",
        "subtitles_help":    "Renders scene text as on-screen captions.",
        "config_ready":      "Config: Ready",
        "config_incomplete": "Config: Incomplete — fill API settings above.",
        "step1":             "Step 1 — Select a Category",
        "category_placeholder": "— Choose a category —",
        "step2":             "Step 2 — Get Viral Topic Suggestions",
        "suggest_btn":       "💡 Suggest Viral Topics",
        "clear_btn":         "Clear",
        "suggest_spinner":   "Generating viral topics for",
        "suggest_caption":   "Select a topic to generate your video:",
        "step3":             "Step 3 — Confirm Your Topic",
        "topic_label":       "Topic (type your own or use the suggestions above)",
        "topic_placeholder": "e.g. The secret experiment that nearly destroyed the Moon...",
        "scenes_label":      "Scenes",
        "generate_btn":      "Generate Video",
        "config_info":       "Fill and save your API settings in the sidebar to enable generation.",
        "log_area":          "Pipeline Log",
        "stages_labels":     {"Brain": "Brain", "Audio": "Audio", "Assets": "Assets", "Composer": "Composer"},
        "done_msg":          "Video generation complete!",
        "download_zip":      "⬇️ Download Full Kit (.zip)",
        "video_header":      "Video",
        "download_mp4":      "Download MP4",
        "video_not_found":   "Video not found.",
        "script_header":     "Script",
        "script_unavail":    "No script available.",
        "visuals_header":    "Visual Prompts",
        "thumb_header":      "Thumbnail Prompt",
        "copy_header":       "Social Media Copy",
        "yt_title_label":    "Title",
        "chars_label":       "chars",
        "desc_caption":      "Description",
        "tiktok_caption_hint": "Hook + keyword · Context · CTA + niche hashtags",
        "fb_caption_hint":   "Hook statement · Context · CTA + 3 hashtags max",
        "error_prefix":      "Pipeline failed:",
        "error_hint":        "Check the log above and verify your API keys in the sidebar.",
        "zip_title":         "TITLE:",
        "zip_desc":          "DESCRIPTION:",
        "script_scene":      "Scene",
        "default_voice":     "Ryan — UK Male",
    },
}

# ── Session state ────────────────────────────────────────────────────────────

for key, default in [
    ("running",           False),
    ("log_lines",         []),
    ("status",            "idle"),
    ("thread",            None),
    ("copy_data",         None),
    ("thumb_prompt",      None),
    ("script_data",       None),
    ("selected_category", ""),
    ("topic_suggestions", []),
    ("selected_topic",    ""),
    ("lang",              "es"),
]:
    if key not in st.session_state:
        st.session_state[key] = default

if "log_queue" not in st.session_state:
    st.session_state.log_queue = queue.Queue()

# Idioma activo
lang = st.session_state.lang
T    = UI[lang]

# ── Pipeline runner ───────────────────────────────────────────────────────────

def run_pipeline(log_q: queue.Queue, params: dict):
    import sys
    import io

    class QueueWriter(io.TextIOBase):
        def write(self, msg):
            if msg and msg.strip():
                log_q.put(msg.rstrip())
            return len(msg) if msg else 0

    old_stdout = sys.stdout
    sys.stdout = QueueWriter()

    try:
        import modules.brain         as _brain_mod
        import modules.asset_manager as _am_mod
        importlib.reload(_brain_mod)
        importlib.reload(_am_mod)

        from modules.brain         import ContentBrain
        from modules.audio         import AudioEngine
        from modules.asset_manager import AssetManager
        from modules.composer      import Composer

        pipeline_lang = params.get("lang", "es")

        # ── Brain ────────────────────────────────────────────────────────────
        log_q.put("STAGE:Brain")
        brain  = ContentBrain()
        topic  = brain.get_trending_topic(params.get("topic", ""), lang=pipeline_lang)
        script = brain.generate_script(topic, num_scenes=params.get("num_scenes", 9), lang=pipeline_lang)
        if not script:
            log_q.put("ERROR:Script generation failed.")
            return

        # ── Audio ────────────────────────────────────────────────────────────
        log_q.put("STAGE:Audio")
        audio_engine = AudioEngine(
            voice=params.get("voice", "es-ES-AlvaroNeural"),
            rate=params.get("rate",  "+10%"),
        )
        script = asyncio.run(audio_engine.process_script(script))

        # ── Assets ───────────────────────────────────────────────────────────
        log_q.put("STAGE:Assets")
        asset_manager = AssetManager()
        assets_map    = asset_manager.get_videos(script)

        # ── Composer ─────────────────────────────────────────────────────────
        log_q.put("STAGE:Composer")
        composer = Composer(use_avatar=params.get("use_avatar", True))
        final_scene_paths = composer.render_all_scenes(script, assets_map)

        if not final_scene_paths:
            log_q.put("ERROR:No scenes were rendered.")
            return

        composer.concatenate_with_transitions(
            final_scene_paths,
            script_data=script,
            use_subtitles=params.get("use_subtitles", False),
        )

        # Clean temp cache
        for folder in ["audio_clips", "video_clips", "temp"]:
            p = os.path.join(os.path.dirname(__file__), "assets", folder)
            if os.path.exists(p):
                shutil.rmtree(p)
                os.makedirs(p, exist_ok=True)

        # ── Social copy ──────────────────────────────────────────────────────
        copy_data = brain.generate_copy(topic, script, lang=pipeline_lang)
        log_q.put(f"COPY:{__import__('json').dumps(copy_data)}")

        # ── Thumbnail prompt ──────────────────────────────────────────────
        thumb_prompt = brain.generate_thumbnail_prompt(topic, script)
        log_q.put(f"THUMB:{thumb_prompt}")

        # ── Script data ───────────────────────────────────────────────────
        log_q.put(f"SCRIPT:{__import__('json').dumps(script)}")

        log_q.put("DONE")

    except Exception as e:
        import traceback
        log_q.put(f"ERROR:{e}")
        for line in traceback.format_exc().splitlines():
            log_q.put(line)
    finally:
        sys.stdout = old_stdout

# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.title("AutoShorts AI")

    # ── Selector de idioma ────────────────────────────────────────────────────
    st.subheader("🌐 Idioma / Language")
    lang_option = st.radio(
        "Idioma / Language",
        options=["es", "en"],
        format_func=lambda x: "🇪🇸 Español" if x == "es" else "🇺🇸 English",
        index=0 if st.session_state.lang == "es" else 1,
        horizontal=True,
        label_visibility="collapsed",
    )
    if lang_option != st.session_state.lang:
        st.session_state.lang              = lang_option
        st.session_state.topic_suggestions = []
        st.session_state.selected_topic    = ""
        st.session_state.selected_category = ""
        st.rerun()

    # Actualizar T tras posible cambio de idioma
    T = UI[lang_option]

    st.divider()

    # ── API Settings ──────────────────────────────────────────────────────────
    st.subheader(T["api_settings"])
    cfg = load_config()

    with st.form("api_form"):
        provider = st.selectbox(
            T["ai_provider"],
            options=["gemini", "openrouter"],
            index=0 if cfg["AI_PROVIDER"] != "openrouter" else 1,
            format_func=lambda x: PROVIDER_DEFAULTS[x]["label"],
        )
        ai_key = st.text_input(
            T["ai_key"],
            value=cfg["AI_API_KEY"],
            type="password",
            help="Stored locally in .env",
        )
        model = st.text_input(
            T["model"],
            value=cfg["AI_MODEL"] or PROVIDER_DEFAULTS[provider]["model"],
            placeholder=PROVIDER_DEFAULTS[provider]["model"],
        )
        pexels_key = st.text_input(
            T["pexels_key"],
            value=cfg["PEXELS_API_KEY"],
            type="password",
        )
        api_saved = st.form_submit_button(T["save_api"], use_container_width=True)

    if api_saved:
        set_key(ENV_PATH, "AI_PROVIDER",    provider)
        set_key(ENV_PATH, "AI_API_KEY",     ai_key)
        set_key(ENV_PATH, "AI_MODEL",       model)
        set_key(ENV_PATH, "PEXELS_API_KEY", pexels_key)
        load_dotenv(ENV_PATH, override=True)
        st.success(T["api_saved"])

    st.divider()

    # ── Video Settings ────────────────────────────────────────────────────────
    st.subheader(T["video_settings"])

    VOICES       = VOICES_ES if lang_option == "es" else VOICES_EN
    default_voice = T["default_voice"]
    voice_label   = st.selectbox(
        T["narrator_voice"],
        options=list(VOICES.keys()),
        index=list(VOICES.keys()).index(default_voice) if default_voice in VOICES else 0,
    )
    selected_voice = VOICES[voice_label]

    col_prev, col_spin = st.columns([1, 2])
    with col_prev:
        preview_clicked = st.button(T["preview_btn"], use_container_width=True)
    with col_spin:
        preview_status = st.empty()

    if preview_clicked:
        preview_path = os.path.join(os.path.dirname(__file__), "assets", "temp", "voice_preview.mp3")
        os.makedirs(os.path.dirname(preview_path), exist_ok=True)
        preview_status.caption(T["generating"])

        def _gen_preview(voice, text, path):
            import asyncio, edge_tts
            async def _run():
                comm = edge_tts.Communicate(text, voice, rate="+10%")
                await comm.save(path)
            asyncio.run(_run())

        import threading as _threading
        t = _threading.Thread(
            target=_gen_preview,
            args=(selected_voice, T["preview_text"], preview_path),
            daemon=True,
        )
        t.start()
        t.join()
        preview_status.empty()
        if os.path.exists(preview_path):
            st.audio(preview_path, format="audio/mp3")

    rate_pct = st.slider(
        T["speech_rate"],
        min_value=-30,
        max_value=50,
        value=10,
        step=5,
        format="%+d%%",
        help=T["speech_help"],
    )
    rate_str = f"+{rate_pct}%" if rate_pct >= 0 else f"{rate_pct}%"

    use_avatar    = st.toggle(T["avatar_toggle"],    value=False, help=T["avatar_help"])
    use_subtitles = st.toggle(T["subtitles_toggle"], value=False, help=T["subtitles_help"])

    st.divider()

    if check_config():
        st.success(T["config_ready"])
    else:
        st.warning(T["config_incomplete"])

# ── Main area ─────────────────────────────────────────────────────────────────

st.title(T["page_title"])
st.caption(T["page_caption"])

config_ok = check_config()

CATEGORIES = TOPIC_CATEGORIES_ES if lang_option == "es" else TOPIC_CATEGORIES_EN

# ── Step 1: Category ─────────────────────────────────────────────────────────

st.subheader(T["step1"])

selected_category = st.selectbox(
    "category",
    options=[""] + CATEGORIES,
    format_func=lambda x: T["category_placeholder"] if x == "" else x,
    label_visibility="collapsed",
)

# ── Step 2: Viral Suggestions ─────────────────────────────────────────────────

st.subheader(T["step2"])

col_suggest, col_clear = st.columns([4, 1])
with col_suggest:
    suggest_clicked = st.button(
        T["suggest_btn"],
        disabled=(not selected_category or st.session_state.running),
        type="secondary",
        use_container_width=True,
    )
with col_clear:
    if st.button(T["clear_btn"], use_container_width=True, disabled=st.session_state.running):
        st.session_state.topic_suggestions = []
        st.session_state.selected_topic    = ""
        st.rerun()

if suggest_clicked and selected_category:
    with st.spinner(f"{T['suggest_spinner']} '{selected_category}'..."):
        from modules.brain import ContentBrain as _BrainSuggest  # noqa: PLC0415
        _brain_suggest = _BrainSuggest()
        suggestions = _brain_suggest.get_topic_suggestions(selected_category, n=6, lang=lang_option)
        st.session_state.topic_suggestions = suggestions
        st.session_state.selected_topic    = ""
    st.rerun()

if st.session_state.topic_suggestions:
    st.caption(T["suggest_caption"])
    suggestions = st.session_state.topic_suggestions
    col_a, col_b = st.columns(2)
    for idx, suggestion in enumerate(suggestions):
        col = col_a if idx % 2 == 0 else col_b
        with col:
            is_selected = (st.session_state.selected_topic == suggestion)
            label = f"✓ {suggestion}" if is_selected else suggestion
            if st.button(
                label,
                key=f"sug_{idx}",
                type="primary" if is_selected else "secondary",
                use_container_width=True,
            ):
                st.session_state.selected_topic          = suggestion
                st.session_state["manual_topic_input"]   = suggestion
                st.rerun()

# ── Step 3: Confirm topic + scenes ────────────────────────────────────────────

st.subheader(T["step3"])

col_topic, col_scenes = st.columns([3, 1])
with col_topic:
    manual_topic = st.text_input(
        T["topic_label"],
        value=st.session_state.get("selected_topic", ""),
        key="manual_topic_input",
        placeholder=T["topic_placeholder"],
    )
with col_scenes:
    num_scenes = st.slider(T["scenes_label"], min_value=5, max_value=12, value=9)

final_topic = st.session_state.get("manual_topic_input", "").strip() or st.session_state.get("selected_topic", "").strip()

# ── Generate button ───────────────────────────────────────────────────────────

generate_clicked = st.button(
    T["generate_btn"],
    disabled=st.session_state.running or not config_ok,
    type="primary",
)

if not config_ok:
    st.info(T["config_info"])

if generate_clicked and not st.session_state.running:
    st.session_state.running   = True
    st.session_state.status    = "running"
    st.session_state.log_lines = []
    st.session_state.log_queue = queue.Queue()

    params = {
        "topic":         final_topic,
        "num_scenes":    num_scenes,
        "voice":         selected_voice,
        "rate":          rate_str,
        "use_avatar":    use_avatar,
        "use_subtitles": use_subtitles,
        "lang":          lang_option,
    }

    t = threading.Thread(target=run_pipeline, args=(st.session_state.log_queue, params), daemon=True)
    st.session_state.thread = t
    t.start()
    st.rerun()

# ── Progress section ──────────────────────────────────────────────────────────

if st.session_state.status in ("running", "done", "error"):

    try:
        while True:
            msg = st.session_state.log_queue.get_nowait()
            st.session_state.log_lines.append(msg)
    except queue.Empty:
        pass

    for line in st.session_state.log_lines:
        if line == "DONE":
            st.session_state.status  = "done"
            st.session_state.running = False
        elif line.startswith("ERROR:"):
            st.session_state.status  = "error"
            st.session_state.running = False
        elif line.startswith("COPY:"):
            import json as _json
            try:
                st.session_state.copy_data = _json.loads(line[5:])
            except Exception:
                pass
        elif line.startswith("THUMB:"):
            st.session_state.thumb_prompt = line[6:]
        elif line.startswith("SCRIPT:"):
            import json as _json
            try:
                st.session_state.script_data = _json.loads(line[7:])
            except Exception:
                pass

    current_stage = 0
    for line in st.session_state.log_lines:
        if line.startswith("STAGE:"):
            name = line.split(":", 1)[1]
            if name in STAGES:
                current_stage = STAGES.index(name) + 1

    st.progress(min(current_stage / len(STAGES), 1.0))

    stages_labels = T["stages_labels"]
    cols = st.columns(len(STAGES))
    for i, (col, stage) in enumerate(zip(cols, STAGES)):
        label = stages_labels[stage]
        with col:
            if i < current_stage - 1:
                st.success(f"✓ {label}")
            elif i == current_stage - 1:
                st.info(f"▶ {label}")
            else:
                st.text(f"  {label}")

    visible = [
        l for l in st.session_state.log_lines
        if not l.startswith("STAGE:") and l != "DONE"
        and not l.startswith("ERROR:") and not l.startswith("COPY:")
        and not l.startswith("THUMB:") and not l.startswith("SCRIPT:")
    ]
    st.text_area(T["log_area"], value="\n".join(visible), height=260, disabled=True)

    if st.session_state.running:
        time.sleep(0.5)
        st.rerun()

# ── Output section ────────────────────────────────────────────────────────────

def _safe_filename(text: str, max_len: int = 50) -> str:
    clean = re.sub(r'[^\w\s-]', '', text).strip()
    clean = re.sub(r'[\s]+', '_', clean)
    return clean[:max_len] or "autoshorts_kit"

def _build_zip(T: dict) -> tuple:
    copy   = st.session_state.get("copy_data", {}) or {}
    thumb  = st.session_state.get("thumb_prompt", "")
    script = st.session_state.get("script_data", []) or []

    yt_title = copy.get("youtube_title", "autoshorts_video")
    zip_name = _safe_filename(yt_title) + ".zip"

    copy_txt = f"""YOUTUBE SHORTS
{'='*60}
{T['zip_title']}
{copy.get('youtube_title', '')}

{T['zip_desc']}
{copy.get('youtube_description', '')}

{'='*60}
TIKTOK
{'='*60}
{copy.get('tiktok_caption', '')}

{'='*60}
FACEBOOK REELS
{'='*60}
{copy.get('facebook_caption', '')}
"""
    scene_label = T["script_scene"]
    script_txt  = "\n\n".join(
        f"[{scene_label} {s['id']}] {s['text']}" for s in script
    ) if script else ""

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        if os.path.exists(FINAL_VIDEO_PATH):
            zf.write(FINAL_VIDEO_PATH, "final_short.mp4")
        if thumb:
            zf.writestr("thumbnail_prompt.txt", thumb)
        if copy_txt.strip():
            zf.writestr("social_copy.txt", copy_txt)
        if script_txt:
            zf.writestr("script.txt", script_txt)
    buf.seek(0)
    return buf.getvalue(), zip_name


if st.session_state.status == "done":
    st.success(T["done_msg"])

    zip_bytes, zip_name = _build_zip(T)
    st.download_button(
        label=T["download_zip"],
        data=zip_bytes,
        file_name=zip_name,
        mime="application/zip",
        type="primary",
        use_container_width=False,
    )

    st.divider()

    col_video, col_script, col_prompts = st.columns([2, 2, 3], gap="large")

    with col_video:
        st.subheader(T["video_header"])
        if os.path.exists(FINAL_VIDEO_PATH):
            st.video(FINAL_VIDEO_PATH)
            with open(FINAL_VIDEO_PATH, "rb") as f:
                st.download_button(
                    label=T["download_mp4"],
                    data=f,
                    file_name="final_short.mp4",
                    mime="video/mp4",
                    use_container_width=True,
                )
        else:
            st.warning(T["video_not_found"])

    with col_script:
        st.subheader(T["script_header"])
        script = st.session_state.get("script_data")
        if script:
            full_script = "\n\n".join(
                f"[{scene['id']}] {scene['text']}" for scene in script
            )
            st.text_area("", value=full_script, height=420, label_visibility="collapsed")
        else:
            st.info(T["script_unavail"])

    with col_prompts:
        script = st.session_state.get("script_data")
        if script:
            st.subheader(T["visuals_header"])
            for scene in script:
                st.caption(
                    f"**{scene['id']}** · A: `{scene.get('visual_1','')}` "
                    f"· B: `{scene.get('visual_2','')}`"
                )

        st.divider()

        thumb = st.session_state.get("thumb_prompt")
        if thumb:
            st.subheader(T["thumb_header"])
            st.caption("Midjourney · DALL·E · Ideogram · Flux")
            st.text_area("", value=thumb, height=200, label_visibility="collapsed")

        st.divider()

        copy = st.session_state.get("copy_data")
        if copy:
            st.subheader(T["copy_header"])

            yt_title = copy.get("youtube_title", "")
            yt_desc  = copy.get("youtube_description", "")
            st.markdown("**YouTube Shorts**")
            char_count = len(yt_title)
            color = "green" if char_count <= 70 else "red"
            st.markdown(f"{T['yt_title_label']} :{color}[{char_count} {T['chars_label']}]")
            st.code(yt_title, language=None)
            st.caption(T["desc_caption"])
            st.code(yt_desc, language=None)

            st.markdown("---")

            col_t, col_f = st.columns(2)
            with col_t:
                st.markdown("**TikTok**")
                st.caption(T["tiktok_caption_hint"])
                st.code(copy.get("tiktok_caption", ""), language=None)
            with col_f:
                st.markdown("**Facebook Reels**")
                st.caption(T["fb_caption_hint"])
                st.code(copy.get("facebook_caption", ""), language=None)

elif st.session_state.status == "error":
    err = next(
        (l.split(":", 1)[1] for l in st.session_state.log_lines if l.startswith("ERROR:")),
        "Unknown error",
    )
    st.error(f"{T['error_prefix']} {err}")
    st.info(T["error_hint"])
