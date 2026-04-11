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
    layout="centered",
)

# ── CSS Mobile-first ──────────────────────────────────────────────────────────

st.markdown("""
<style>
/* ── Fuente y base ── */
html, body, [class*="css"] {
    font-family: 'Inter', 'Segoe UI', sans-serif;
}

/* ── Título principal ── */
h1 { font-size: clamp(1.4rem, 5vw, 2.2rem) !important; }
h2 { font-size: clamp(1.1rem, 4vw, 1.6rem) !important; }
h3 { font-size: clamp(1rem, 3.5vw, 1.3rem) !important; }

/* ── Botones grandes táctiles ── */
.stButton > button {
    min-height: 52px !important;
    font-size: 1rem !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    transition: transform 0.1s ease;
}
.stButton > button:active { transform: scale(0.97); }

/* ── Botón primario con gradiente ── */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #7c3aed, #4f46e5) !important;
    border: none !important;
    color: white !important;
    box-shadow: 0 4px 15px rgba(124,58,237,0.4) !important;
}
.stButton > button[kind="primary"]:hover {
    box-shadow: 0 6px 20px rgba(124,58,237,0.6) !important;
}

/* ── Inputs y selects ── */
.stTextInput > div > div > input,
.stSelectbox > div > div {
    min-height: 48px !important;
    font-size: 1rem !important;
    border-radius: 8px !important;
}

/* ── Tarjetas de sugerencias ── */
.suggestion-card .stButton > button {
    white-space: normal !important;
    height: auto !important;
    min-height: 64px !important;
    padding: 12px 16px !important;
    text-align: left !important;
    line-height: 1.4 !important;
    font-size: 0.9rem !important;
    font-weight: 500 !important;
}

/* ── Progress stages ── */
.stage-box {
    border-radius: 8px;
    padding: 8px 4px;
    text-align: center;
    font-size: 0.8rem;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    gap: 4px;
}
.stTabs [data-baseweb="tab"] {
    font-size: 0.9rem !important;
    padding: 8px 12px !important;
    border-radius: 8px 8px 0 0 !important;
}

/* ── Download button grande ── */
.stDownloadButton > button {
    width: 100% !important;
    min-height: 56px !important;
    font-size: 1.05rem !important;
    font-weight: 700 !important;
    border-radius: 12px !important;
    background: linear-gradient(135deg, #059669, #047857) !important;
    color: white !important;
    border: none !important;
    box-shadow: 0 4px 15px rgba(5,150,105,0.4) !important;
}

/* ── Log area ── */
.stTextArea textarea {
    font-size: 0.78rem !important;
    font-family: 'Courier New', monospace !important;
}

/* ── Sidebar táctil ── */
[data-testid="stSidebar"] .stButton > button {
    min-height: 44px !important;
}

/* ── Code blocks en móvil ── */
.stCode {
    font-size: 0.8rem !important;
    overflow-x: auto !important;
}

/* ── Separador de pasos ── */
.step-header {
    background: linear-gradient(90deg, #7c3aed22, transparent);
    border-left: 3px solid #7c3aed;
    padding: 8px 14px;
    border-radius: 0 8px 8px 0;
    margin: 16px 0 8px 0;
    font-weight: 700;
    font-size: 1rem;
}

/* ── Responsive: móvil ── */
@media (max-width: 640px) {
    .stButton > button { min-height: 56px !important; font-size: 0.95rem !important; }
    h1 { font-size: 1.3rem !important; }
    .stTabs [data-baseweb="tab"] { font-size: 0.8rem !important; padding: 6px 8px !important; }
    [data-testid="stSidebar"] { min-width: 280px !important; }
}
</style>
""", unsafe_allow_html=True)

# ── Autenticación ─────────────────────────────────────────────────────────────

def _check_auth():
    app_password = (
        st.secrets.get("APP_PASSWORD", None)
        if hasattr(st, "secrets")
        else None
    ) or os.getenv("APP_PASSWORD", "")

    if not app_password or st.session_state.get("authenticated"):
        return

    st.markdown("""
    <div style="text-align:center; padding: 3rem 1rem 1rem 1rem;">
        <div style="font-size:3rem;">🎬</div>
        <h1 style="margin:0.5rem 0;">AutoShorts AI</h1>
        <p style="color:#888; margin-bottom:2rem;">Ingresa la contraseña para continuar</p>
    </div>
    """, unsafe_allow_html=True)

    col_l, col_c, col_r = st.columns([1, 3, 1])
    with col_c:
        pwd = st.text_input("Contraseña", type="password", key="pwd_input",
                            placeholder="••••••••", label_visibility="collapsed")
        if st.button("Entrar →", use_container_width=True, type="primary"):
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
    "Álvaro — España Masculino (misterio)": "es-ES-AlvaroNeural",
    "Jorge — México Masculino":              "es-MX-JorgeNeural",
    "Dalia — México Femenina":               "es-MX-DaliaNeural",
    "Elvira — España Femenina":              "es-ES-ElviraNeural",
    "Paloma — EE.UU. Femenina":             "es-US-PalomaNeural",
    "Alonso — EE.UU. Masculino":            "es-US-AlonsoNeural",
    "Camila — Perú Femenina":               "es-PE-CamilaNeural",
    "Salomé — Colombia Femenina":           "es-CO-SalomeNeural",
    "Elena — Argentina Femenina":           "es-AR-ElenaNeural",
}

VOICES_EN = {
    "Ryan — UK Male (mystery)":    "en-GB-RyanNeural",
    "Brian — US Male":             "en-US-BrianNeural",
    "Andrew — US Male":            "en-US-AndrewNeural",
    "Ava — US Female":             "en-US-AvaNeural",
    "Emma — US Female":            "en-US-EmmaNeural",
    "Jenny — US Female":           "en-US-JennyNeural",
    "Guy — US Male":               "en-US-GuyNeural",
    "Sonia — UK Female":           "en-GB-SoniaNeural",
    "Natasha — AU Female":         "en-AU-NatashaNeural",
    "William — AU Male":           "en-AU-WilliamNeural",
}

# ── Textos UI por idioma ──────────────────────────────────────────────────────

UI = {
    "es": {
        "page_title":        "AutoShorts AI 🎬",
        "page_caption":      "Genera tu YouTube Short con IA — en minutos.",
        "api_settings":      "⚙️ Configuración de API",
        "ai_provider":       "Proveedor de IA",
        "ai_key":            "Clave API de IA",
        "model":             "Modelo",
        "pexels_key":        "Clave API de Pexels",
        "save_api":          "Guardar Configuración",
        "api_saved":         "✅ Configuración guardada.",
        "video_settings":    "🎬 Configuración de Video",
        "narrator_voice":    "Voz del Narrador",
        "preview_btn":       "▶ Escuchar",
        "preview_text":      "Hola, así es como sueno. Espero que disfrutes este video.",
        "generating":        "Generando...",
        "speech_rate":       "Velocidad de Voz",
        "speech_help":       "0% = normal. Positivo = más rápido.",
        "avatar_toggle":     "Activar Avatar",
        "avatar_help":       "Inserta tu video avatar en escenas del medio.",
        "subtitles_toggle":  "Subtítulos en pantalla",
        "subtitles_help":    "Renderiza el texto como subtítulos en el video.",
        "config_ready":      "✅ API: Lista",
        "config_incomplete": "⚠️ Completa las claves de API arriba.",
        "step1":             "1️⃣ Selecciona una categoría",
        "category_placeholder": "— Elige una categoría —",
        "step2":             "2️⃣ Obtén ideas de temas virales",
        "suggest_btn":       "💡 Sugerir Temas Virales",
        "clear_btn":         "✕",
        "suggest_spinner":   "Generando temas para",
        "suggest_caption":   "Toca un tema para seleccionarlo:",
        "step3":             "3️⃣ Confirma tu tema",
        "topic_label":       "Tema del video",
        "topic_placeholder": "ej. El secreto que casi destruyó la Luna...",
        "scenes_label":      "Escenas",
        "generate_btn":      "🎬 Generar Video",
        "config_info":       "⚙️ Configura tus claves de API en el menú lateral.",
        "log_area":          "Log del proceso",
        "stages_labels":     {"Brain": "🧠 Guion", "Audio": "🎙️ Audio", "Assets": "🎥 Videos", "Composer": "🎬 Edición"},
        "done_msg":          "🎉 ¡Video generado con éxito!",
        "download_zip":      "⬇️ Descargar Kit Completo (.zip)",
        "video_header":      "📱 Video",
        "download_mp4":      "⬇️ Descargar MP4",
        "video_not_found":   "Video no encontrado.",
        "script_header":     "📝 Guion",
        "script_unavail":    "Guion no disponible.",
        "visuals_header":    "🎥 Palabras Clave Visuales",
        "thumb_header":      "🖼️ Prompt para Miniatura",
        "copy_header":       "📣 Copy para Redes",
        "yt_title_label":    "Título",
        "chars_label":       "caracteres",
        "desc_caption":      "Descripción",
        "tiktok_caption_hint": "Gancho · Contexto · CTA + hashtags",
        "fb_caption_hint":   "Gancho · Contexto · CTA + 3 hashtags",
        "error_prefix":      "❌ Error:",
        "error_hint":        "Revisa el log y verifica tus claves de API.",
        "zip_title":         "TÍTULO:",
        "zip_desc":          "DESCRIPCIÓN:",
        "script_scene":      "Escena",
        "default_voice":     "Álvaro — España Masculino (misterio)",
        "tab_video":         "📱 Video",
        "tab_script":        "📝 Guion",
        "tab_copy":          "📣 Copy",
        "tab_thumb":         "🖼️ Miniatura",
    },
    "en": {
        "page_title":        "AutoShorts AI 🎬",
        "page_caption":      "Generate your YouTube Short with AI — in minutes.",
        "api_settings":      "⚙️ API Settings",
        "ai_provider":       "AI Provider",
        "ai_key":            "AI API Key",
        "model":             "Model",
        "pexels_key":        "Pexels API Key",
        "save_api":          "Save Settings",
        "api_saved":         "✅ Settings saved.",
        "video_settings":    "🎬 Video Settings",
        "narrator_voice":    "Narrator Voice",
        "preview_btn":       "▶ Listen",
        "preview_text":      "Hello! This is how I sound. I hope you enjoy this video.",
        "generating":        "Generating...",
        "speech_rate":       "Speech Rate",
        "speech_help":       "0% = normal. Positive = faster.",
        "avatar_toggle":     "Enable Avatar",
        "avatar_help":       "Inserts your avatar into middle scenes.",
        "subtitles_toggle":  "Burn Subtitles",
        "subtitles_help":    "Renders text as on-screen captions.",
        "config_ready":      "✅ API: Ready",
        "config_incomplete": "⚠️ Complete your API keys above.",
        "step1":             "1️⃣ Select a Category",
        "category_placeholder": "— Choose a category —",
        "step2":             "2️⃣ Get Viral Topic Ideas",
        "suggest_btn":       "💡 Suggest Viral Topics",
        "clear_btn":         "✕",
        "suggest_spinner":   "Generating topics for",
        "suggest_caption":   "Tap a topic to select it:",
        "step3":             "3️⃣ Confirm Your Topic",
        "topic_label":       "Video topic",
        "topic_placeholder": "e.g. The experiment that nearly destroyed the Moon...",
        "scenes_label":      "Scenes",
        "generate_btn":      "🎬 Generate Video",
        "config_info":       "⚙️ Configure your API keys in the side menu.",
        "log_area":          "Pipeline log",
        "stages_labels":     {"Brain": "🧠 Script", "Audio": "🎙️ Audio", "Assets": "🎥 Video", "Composer": "🎬 Edit"},
        "done_msg":          "🎉 Video generated successfully!",
        "download_zip":      "⬇️ Download Full Kit (.zip)",
        "video_header":      "📱 Video",
        "download_mp4":      "⬇️ Download MP4",
        "video_not_found":   "Video not found.",
        "script_header":     "📝 Script",
        "script_unavail":    "No script available.",
        "visuals_header":    "🎥 Visual Keywords",
        "thumb_header":      "🖼️ Thumbnail Prompt",
        "copy_header":       "📣 Social Media Copy",
        "yt_title_label":    "Title",
        "chars_label":       "chars",
        "desc_caption":      "Description",
        "tiktok_caption_hint": "Hook · Context · CTA + hashtags",
        "fb_caption_hint":   "Hook · Context · CTA + 3 hashtags",
        "error_prefix":      "❌ Error:",
        "error_hint":        "Check the log and verify your API keys.",
        "zip_title":         "TITLE:",
        "zip_desc":          "DESCRIPTION:",
        "script_scene":      "Scene",
        "default_voice":     "Ryan — UK Male (mystery)",
        "tab_video":         "📱 Video",
        "tab_script":        "📝 Script",
        "tab_copy":          "📣 Copy",
        "tab_thumb":         "🖼️ Thumbnail",
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

lang = st.session_state.lang
T    = UI[lang]

# ── Pipeline runner ───────────────────────────────────────────────────────────

def run_pipeline(log_q: queue.Queue, params: dict):
    import sys, io

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

        log_q.put("STAGE:Brain")
        brain  = ContentBrain()
        topic  = brain.get_trending_topic(params.get("topic", ""), lang=pipeline_lang)
        script = brain.generate_script(topic, num_scenes=params.get("num_scenes", 9), lang=pipeline_lang)
        if not script:
            log_q.put("ERROR:Script generation failed.")
            return

        log_q.put("STAGE:Audio")
        audio_engine = AudioEngine(voice=params.get("voice", "es-ES-AlvaroNeural"), rate=params.get("rate", "+10%"))
        script = asyncio.run(audio_engine.process_script(script))

        log_q.put("STAGE:Assets")
        asset_manager = AssetManager()
        assets_map    = asset_manager.get_videos(script)

        log_q.put("STAGE:Composer")
        composer = Composer(use_avatar=params.get("use_avatar", False))
        final_scene_paths = composer.render_all_scenes(script, assets_map)
        if not final_scene_paths:
            log_q.put("ERROR:No scenes were rendered.")
            return

        composer.concatenate_with_transitions(final_scene_paths, script_data=script,
                                              use_subtitles=params.get("use_subtitles", False))

        for folder in ["audio_clips", "video_clips", "temp"]:
            p = os.path.join(os.path.dirname(__file__), "assets", folder)
            if os.path.exists(p):
                shutil.rmtree(p)
                os.makedirs(p, exist_ok=True)

        copy_data    = brain.generate_copy(topic, script, lang=pipeline_lang)
        thumb_prompt = brain.generate_thumbnail_prompt(topic, script)

        log_q.put(f"COPY:{__import__('json').dumps(copy_data)}")
        log_q.put(f"THUMB:{thumb_prompt}")
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
    st.markdown("# 🎬 AutoShorts AI")

    # Idioma
    lang_option = st.radio(
        "Idioma",
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

    T = UI[lang_option]
    st.divider()

    # API Settings
    st.subheader(T["api_settings"])
    cfg = load_config()

    with st.form("api_form"):
        provider = st.selectbox(T["ai_provider"],
            options=["gemini", "openrouter"],
            index=0 if cfg["AI_PROVIDER"] != "openrouter" else 1,
            format_func=lambda x: PROVIDER_DEFAULTS[x]["label"],
        )
        ai_key     = st.text_input(T["ai_key"], value=cfg["AI_API_KEY"], type="password")
        model      = st.text_input(T["model"],
                        value=cfg["AI_MODEL"] or PROVIDER_DEFAULTS[provider]["model"],
                        placeholder=PROVIDER_DEFAULTS[provider]["model"])
        pexels_key = st.text_input(T["pexels_key"], value=cfg["PEXELS_API_KEY"], type="password")
        api_saved  = st.form_submit_button(T["save_api"], use_container_width=True)

    if api_saved:
        set_key(ENV_PATH, "AI_PROVIDER",    provider)
        set_key(ENV_PATH, "AI_API_KEY",     ai_key)
        set_key(ENV_PATH, "AI_MODEL",       model)
        set_key(ENV_PATH, "PEXELS_API_KEY", pexels_key)
        load_dotenv(ENV_PATH, override=True)
        st.success(T["api_saved"])

    st.divider()

    # Video Settings
    st.subheader(T["video_settings"])

    VOICES        = VOICES_ES if lang_option == "es" else VOICES_EN
    default_voice = T["default_voice"]
    voice_label   = st.selectbox(T["narrator_voice"], options=list(VOICES.keys()),
                        index=list(VOICES.keys()).index(default_voice) if default_voice in VOICES else 0)
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
                await edge_tts.Communicate(text, voice, rate="+10%").save(path)
            asyncio.run(_run())

        import threading as _t
        _t.Thread(target=_gen_preview, args=(selected_voice, T["preview_text"], preview_path), daemon=True).start()
        import time as _time; _time.sleep(4)
        preview_status.empty()
        if os.path.exists(preview_path):
            st.audio(preview_path, format="audio/mp3")

    rate_pct = st.slider(T["speech_rate"], min_value=-30, max_value=50, value=10, step=5,
                         format="%+d%%", help=T["speech_help"])
    rate_str = f"+{rate_pct}%" if rate_pct >= 0 else f"{rate_pct}%"

    use_avatar    = st.toggle(T["avatar_toggle"],    value=False, help=T["avatar_help"])
    use_subtitles = st.toggle(T["subtitles_toggle"], value=False, help=T["subtitles_help"])

    st.divider()
    if check_config():
        st.success(T["config_ready"])
    else:
        st.warning(T["config_incomplete"])

# ── Main area ─────────────────────────────────────────────────────────────────

st.markdown(f"# {T['page_title']}")
st.caption(T["page_caption"])

config_ok  = check_config()
CATEGORIES = TOPIC_CATEGORIES_ES if lang_option == "es" else TOPIC_CATEGORIES_EN

# ── Paso 1 ────────────────────────────────────────────────────────────────────

st.markdown(f"<div class='step-header'>{T['step1']}</div>", unsafe_allow_html=True)

selected_category = st.selectbox(
    "cat", options=[""] + CATEGORIES,
    format_func=lambda x: T["category_placeholder"] if x == "" else x,
    label_visibility="collapsed",
)

# ── Paso 2 ────────────────────────────────────────────────────────────────────

st.markdown(f"<div class='step-header'>{T['step2']}</div>", unsafe_allow_html=True)

col_s, col_c = st.columns([5, 1])
with col_s:
    suggest_clicked = st.button(T["suggest_btn"],
        disabled=(not selected_category or st.session_state.running),
        type="secondary", use_container_width=True)
with col_c:
    if st.button(T["clear_btn"], use_container_width=True, disabled=st.session_state.running):
        st.session_state.topic_suggestions = []
        st.session_state.selected_topic    = ""
        st.rerun()

if suggest_clicked and selected_category:
    with st.spinner(f"{T['suggest_spinner']} '{selected_category}'..."):
        from modules.brain import ContentBrain as _BS
        suggestions = _BS().get_topic_suggestions(selected_category, n=6, lang=lang_option)
        st.session_state.topic_suggestions = suggestions
        st.session_state.selected_topic    = ""
    st.rerun()

if st.session_state.topic_suggestions:
    st.caption(T["suggest_caption"])
    suggestions = st.session_state.topic_suggestions
    st.markdown("<div class='suggestion-card'>", unsafe_allow_html=True)
    col_a, col_b = st.columns(2)
    for idx, sug in enumerate(suggestions):
        col = col_a if idx % 2 == 0 else col_b
        with col:
            is_sel = (st.session_state.selected_topic == sug)
            if st.button(f"{'✓ ' if is_sel else ''}{sug}",
                         key=f"sug_{idx}",
                         type="primary" if is_sel else "secondary",
                         use_container_width=True):
                st.session_state.selected_topic        = sug
                st.session_state["manual_topic_input"] = sug
                st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# ── Paso 3 ────────────────────────────────────────────────────────────────────

st.markdown(f"<div class='step-header'>{T['step3']}</div>", unsafe_allow_html=True)

manual_topic = st.text_input(
    T["topic_label"],
    value=st.session_state.get("selected_topic", ""),
    key="manual_topic_input",
    placeholder=T["topic_placeholder"],
)

num_scenes = st.slider(T["scenes_label"], min_value=5, max_value=12, value=9)

final_topic = st.session_state.get("manual_topic_input", "").strip() or st.session_state.get("selected_topic", "").strip()

# ── Generar ───────────────────────────────────────────────────────────────────

st.markdown("---")
generate_clicked = st.button(T["generate_btn"],
    disabled=st.session_state.running or not config_ok,
    type="primary", use_container_width=True)

if not config_ok:
    st.info(T["config_info"])

if generate_clicked and not st.session_state.running:
    st.session_state.running   = True
    st.session_state.status    = "running"
    st.session_state.log_lines = []
    st.session_state.log_queue = queue.Queue()

    params = {
        "topic": final_topic, "num_scenes": num_scenes,
        "voice": selected_voice, "rate": rate_str,
        "use_avatar": use_avatar, "use_subtitles": use_subtitles,
        "lang": lang_option,
    }
    t = threading.Thread(target=run_pipeline, args=(st.session_state.log_queue, params), daemon=True)
    st.session_state.thread = t
    t.start()
    st.rerun()

# ── Progreso ──────────────────────────────────────────────────────────────────

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
            try: st.session_state.copy_data = __import__('json').loads(line[5:])
            except: pass
        elif line.startswith("THUMB:"):
            st.session_state.thumb_prompt = line[6:]
        elif line.startswith("SCRIPT:"):
            try: st.session_state.script_data = __import__('json').loads(line[7:])
            except: pass

    current_stage = 0
    for line in st.session_state.log_lines:
        if line.startswith("STAGE:"):
            name = line.split(":", 1)[1]
            if name in STAGES:
                current_stage = STAGES.index(name) + 1

    st.progress(min(current_stage / len(STAGES), 1.0))

    stage_labels = T["stages_labels"]
    cols = st.columns(len(STAGES))
    for i, (col, stage) in enumerate(zip(cols, STAGES)):
        with col:
            lbl = stage_labels[stage]
            if i < current_stage - 1:
                st.success(lbl)
            elif i == current_stage - 1:
                st.info(lbl)
            else:
                st.caption(lbl)

    visible = [l for l in st.session_state.log_lines
               if not any(l.startswith(p) for p in ("STAGE:", "COPY:", "THUMB:", "SCRIPT:"))
               and l != "DONE" and not l.startswith("ERROR:")]
    with st.expander("📋 " + T["log_area"], expanded=st.session_state.running):
        st.text_area("", value="\n".join(visible), height=180, disabled=True, label_visibility="collapsed")

    if st.session_state.running:
        time.sleep(0.5)
        st.rerun()

# ── Resultados ────────────────────────────────────────────────────────────────

def _safe_filename(text: str, max_len: int = 50) -> str:
    clean = re.sub(r'[^\w\s-]', '', text).strip()
    return re.sub(r'\s+', '_', clean)[:max_len] or "autoshorts_kit"

def _build_zip(T: dict) -> tuple:
    copy   = st.session_state.get("copy_data", {}) or {}
    thumb  = st.session_state.get("thumb_prompt", "")
    script = st.session_state.get("script_data", []) or []
    zip_name = _safe_filename(copy.get("youtube_title", "autoshorts_video")) + ".zip"

    copy_txt = f"""YOUTUBE SHORTS\n{'='*60}\n{T['zip_title']}\n{copy.get('youtube_title','')}\n\n{T['zip_desc']}\n{copy.get('youtube_description','')}\n\n{'='*60}\nTIKTOK\n{'='*60}\n{copy.get('tiktok_caption','')}\n\n{'='*60}\nFACEBOOK REELS\n{'='*60}\n{copy.get('facebook_caption','')}"""
    scene_lbl = T["script_scene"]
    script_txt = "\n\n".join(f"[{scene_lbl} {s['id']}] {s['text']}" for s in script) if script else ""

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        if os.path.exists(FINAL_VIDEO_PATH): zf.write(FINAL_VIDEO_PATH, "final_short.mp4")
        if thumb:       zf.writestr("thumbnail_prompt.txt", thumb)
        if copy_txt:    zf.writestr("social_copy.txt", copy_txt)
        if script_txt:  zf.writestr("script.txt", script_txt)
    buf.seek(0)
    return buf.getvalue(), zip_name


if st.session_state.status == "done":
    st.markdown("---")
    st.success(T["done_msg"])

    # Botón de descarga grande y prominente
    zip_bytes, zip_name = _build_zip(T)
    st.download_button(label=T["download_zip"], data=zip_bytes, file_name=zip_name,
                       mime="application/zip", type="primary", use_container_width=True)

    st.markdown("---")

    # ── Tabs para móvil ───────────────────────────────────────────────────────
    tab_video, tab_script, tab_copy, tab_thumb = st.tabs([
        T["tab_video"], T["tab_script"], T["tab_copy"], T["tab_thumb"]
    ])

    with tab_video:
        if os.path.exists(FINAL_VIDEO_PATH):
            st.video(FINAL_VIDEO_PATH)
            with open(FINAL_VIDEO_PATH, "rb") as f:
                st.download_button(label=T["download_mp4"], data=f,
                                   file_name="final_short.mp4", mime="video/mp4",
                                   use_container_width=True)
        else:
            st.warning(T["video_not_found"])

    with tab_script:
        script = st.session_state.get("script_data")
        if script:
            full_script = "\n\n".join(f"[{s['id']}] {s['text']}" for s in script)
            st.text_area("", value=full_script, height=400, label_visibility="collapsed")
            st.markdown(f"**{T['visuals_header']}**")
            for scene in script:
                st.caption(f"**{scene['id']}** · A: `{scene.get('visual_1','')}` · B: `{scene.get('visual_2','')}`")
        else:
            st.info(T["script_unavail"])

    with tab_copy:
        copy = st.session_state.get("copy_data")
        if copy:
            yt_title   = copy.get("youtube_title", "")
            yt_desc    = copy.get("youtube_description", "")
            char_count = len(yt_title)
            color      = "green" if char_count <= 70 else "red"

            st.markdown("#### 📺 YouTube Shorts")
            st.markdown(f"{T['yt_title_label']} :{color}[{char_count} {T['chars_label']}]")
            st.code(yt_title, language=None)
            st.caption(T["desc_caption"])
            st.code(yt_desc, language=None)

            st.markdown("#### 🎵 TikTok")
            st.caption(T["tiktok_caption_hint"])
            st.code(copy.get("tiktok_caption", ""), language=None)

            st.markdown("#### 👥 Facebook Reels")
            st.caption(T["fb_caption_hint"])
            st.code(copy.get("facebook_caption", ""), language=None)

    with tab_thumb:
        thumb = st.session_state.get("thumb_prompt")
        if thumb:
            st.caption("Midjourney · DALL·E · Ideogram · Flux")
            st.text_area("", value=thumb, height=320, label_visibility="collapsed")
            st.button("📋 Copiar", key="copy_thumb", use_container_width=True)
        else:
            st.info("No disponible.")

elif st.session_state.status == "error":
    err = next((l.split(":", 1)[1] for l in st.session_state.log_lines if l.startswith("ERROR:")), "Unknown error")
    st.error(f"{T['error_prefix']} {err}")
    st.info(T["error_hint"])
