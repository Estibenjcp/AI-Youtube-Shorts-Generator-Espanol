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

# ── CSS ───────────────────────────────────────────────────────────────────────

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Plus+Jakarta+Sans:wght@600;700;800&display=swap');

/* ═══════════════════════════════════════════════════════════
   AUTOSHORTS AI — PREMIUM UI 2026
   Paleta: Índigo/Violeta + Neutros
   Fuentes: Plus Jakarta Sans (títulos) + Inter (cuerpo)
═══════════════════════════════════════════════════════════ */

/* ── RESET & TOKENS ── */
:root {
    /* Sobreescribir la variable interna de Streamlit (rojo → índigo) */
    --primary-color:    #6366f1 !important;
    --secondary-color:  #4f46e5 !important;

    --brand:        #6366f1;
    --brand-dark:   #4f46e5;
    --brand-light:  #eef2ff;
    --brand-glow:   rgba(99,102,241,0.25);
    --surface:      #ffffff;
    --surface-2:    #f9fafb;
    --surface-3:    #f3f4f6;
    --border:       #e5e7eb;
    --border-focus: #6366f1;
    --text-primary: #111827;
    --text-secondary:#4b5563;
    --text-muted:   #9ca3af;
    --success:      #10b981;
    --radius-sm:    8px;
    --radius-md:    12px;
    --radius-lg:    16px;
    --radius-xl:    20px;
    --shadow-sm:    0 1px 3px rgba(0,0,0,0.07), 0 1px 2px rgba(0,0,0,0.04);
    --shadow-md:    0 4px 12px rgba(0,0,0,0.08), 0 2px 6px rgba(0,0,0,0.05);
    --shadow-lg:    0 10px 30px rgba(0,0,0,0.1), 0 4px 12px rgba(0,0,0,0.06);
    --shadow-brand: 0 6px 24px rgba(99,102,241,0.35);
    --transition:   all 0.18s cubic-bezier(0.4,0,0.2,1);
}

/* ── OCULTAR UI NATIVA DE STREAMLIT ── */
#MainMenu, footer, header,
[data-testid="stDecoration"],
[data-testid="stStatusWidget"],
.viewerBadge_container__1QSob { display: none !important; }

/* ── BASE ── */
*, *::before, *::after { box-sizing: border-box; }

html, body, [class*="css"], .stApp {
    font-family: 'Inter', system-ui, -apple-system, sans-serif !important;
    font-size: 15px;
    line-height: 1.6;
    -webkit-font-smoothing: antialiased;
}

h1, h2, h3, h4, .hero-title {
    font-family: 'Plus Jakarta Sans', 'Inter', sans-serif !important;
}

/* ── APP BACKGROUND ── */
.stApp {
    background: var(--surface-2) !important;
    min-height: 100vh;
}

/* ── CONTENEDOR PRINCIPAL — más estrecho, más elegante ── */
.block-container {
    max-width: 720px !important;
    padding: 2rem 1.5rem 4rem !important;
    margin: 0 auto !important;
}

/* ── SIDEBAR ── */
[data-testid="stSidebar"] {
    background: var(--surface) !important;
    border-right: 1px solid var(--border) !important;
    box-shadow: var(--shadow-sm) !important;
    overflow-y: auto !important;
    overflow-x: hidden !important;
}
[data-testid="stSidebar"] > div:first-child {
    padding: 1.25rem 0.875rem 3rem !important;
    min-height: 100vh;
}
/* Título del sidebar */
[data-testid="stSidebar"] h1 {
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-size: 1.1rem !important;
    font-weight: 700 !important;
    color: var(--text-primary) !important;
    letter-spacing: -0.3px !important;
}

/* ── TIPOGRAFÍA GENERAL ── */
h1 { font-size: clamp(1.5rem,4vw,2.2rem)!important; font-weight:800!important; letter-spacing:-0.5px!important; color:var(--text-primary)!important; }
h2 { font-size: clamp(1.1rem,3vw,1.4rem)!important; font-weight:700!important; color:var(--text-primary)!important; }
h3 { font-size: clamp(0.95rem,2.5vw,1.1rem)!important; font-weight:600!important; color:var(--text-secondary)!important; }
p, .stMarkdown p { color: var(--text-secondary) !important; }
label, .stWidgetLabel { color: var(--text-secondary) !important; font-weight: 500 !important; font-size: 0.88rem !important; }
strong { color: var(--text-primary) !important; }

/* ── HERO HEADER ── */
.hero-title {
    font-size: clamp(1.75rem, 5.5vw, 2.6rem);
    font-weight: 800;
    letter-spacing: -0.8px;
    line-height: 1.15;
    background: linear-gradient(135deg, #4f46e5 0%, #6366f1 50%, #818cf8 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 2px;
}
.hero-sub {
    color: var(--text-muted);
    font-size: 0.95rem;
    font-weight: 400;
    margin: 0 0 1.5rem;
    line-height: 1.5;
}

/* ── RADIO / PILL TOGGLE ── */
[data-testid="stRadio"] {
    background: var(--surface-3) !important;
    border-radius: var(--radius-lg) !important;
    padding: 4px !important;
    border: 1px solid var(--border) !important;
    box-shadow: var(--shadow-sm) !important;
}
[data-testid="stRadio"] > div {
    gap: 2px !important;
    flex-direction: row !important;
    flex-wrap: nowrap !important;
}
[data-testid="stRadio"] label {
    background: transparent !important;
    border-radius: var(--radius-md) !important;
    padding: 9px 22px !important;
    font-weight: 600 !important;
    font-size: 0.9rem !important;
    cursor: pointer !important;
    transition: var(--transition) !important;
    flex: 1 !important;
    text-align: center !important;
    color: var(--text-muted) !important;
    white-space: nowrap !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    gap: 0 !important;
}
[data-testid="stRadio"] label:has(input:checked) {
    background: var(--brand) !important;
    color: #ffffff !important;
    box-shadow: var(--shadow-md) !important;
    font-weight: 700 !important;
}
/* Ocultar TODA la parte del círculo nativo (BaseUI radio) */
[data-testid="stRadio"] input[type="radio"]          { display:none!important; }
[data-testid="stRadio"] [data-baseweb="radio"]        { gap:0!important; }
[data-testid="stRadio"] [data-baseweb="radio"] > div:first-child { display:none!important; }
[data-testid="stRadio"] [data-baseweb="radio"] svg    { display:none!important; }
/* Círculo coloreado de BaseUI */
[data-testid="stRadio"] label > div:first-child       { display:none!important; }

/* ── STEP HEADERS ── */
.step-header {
    display: flex;
    align-items: center;
    gap: 10px;
    background: var(--brand-light);
    border: 1px solid #c7d2fe;
    border-left: 3px solid var(--brand);
    padding: 11px 16px;
    border-radius: 0 var(--radius-md) var(--radius-md) 0;
    margin: 24px 0 12px;
    font-weight: 700;
    font-size: 0.92rem;
    color: #3730a3;
    font-family: 'Plus Jakarta Sans', sans-serif;
    letter-spacing: -0.2px;
}

/* ── AUTO INFO BOX ── */
.auto-info {
    background: #eff6ff;
    border: 1px solid #bfdbfe;
    border-left: 3px solid #60a5fa;
    padding: 13px 18px;
    border-radius: 0 var(--radius-md) var(--radius-md) 0;
    color: #1e40af;
    font-size: 0.875rem;
    margin-bottom: 20px;
    line-height: 1.55;
}

/* ── BOTONES — BASE ── */
.stButton > button {
    width: 100% !important;
    min-height: 48px !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.9rem !important;
    font-weight: 600 !important;
    border-radius: var(--radius-md) !important;
    transition: var(--transition) !important;
    cursor: pointer !important;
    letter-spacing: 0.1px !important;
}
.stButton > button:active {
    transform: scale(0.975) !important;
}

/* Primario — forzar texto blanco en todos los elementos hijos */
.stButton > button[kind="primary"],
.stButton > button[kind="primary"] p,
.stButton > button[kind="primary"] span,
.stButton > button[kind="primary"] div {
    background: linear-gradient(135deg, var(--brand) 0%, var(--brand-dark) 100%) !important;
    color: #ffffff !important;
    border: none !important;
    box-shadow: var(--shadow-brand) !important;
}
.stButton > button[kind="primary"]:hover {
    filter: brightness(1.08) !important;
    box-shadow: 0 8px 30px rgba(99,102,241,0.45) !important;
    transform: translateY(-1px) !important;
}

/* Secundario */
.stButton > button[kind="secondary"] {
    background: var(--surface) !important;
    color: var(--text-primary) !important;
    border: 1.5px solid var(--border) !important;
    box-shadow: var(--shadow-sm) !important;
}
.stButton > button[kind="secondary"]:hover {
    border-color: var(--brand) !important;
    color: var(--brand) !important;
    background: var(--brand-light) !important;
    box-shadow: var(--shadow-md) !important;
    transform: translateY(-1px) !important;
}

/* ── TARJETAS DE SUGERENCIAS ── */
.suggestion-card .stButton > button {
    white-space: normal !important;
    height: auto !important;
    min-height: 76px !important;
    padding: 14px 16px !important;
    text-align: left !important;
    line-height: 1.5 !important;
    font-size: 0.875rem !important;
    font-weight: 500 !important;
    background: var(--surface) !important;
    border: 1.5px solid var(--border) !important;
    color: var(--text-primary) !important;
    border-radius: var(--radius-md) !important;
    box-shadow: var(--shadow-sm) !important;
    transition: var(--transition) !important;
}
.suggestion-card .stButton > button:hover {
    border-color: var(--brand) !important;
    background: var(--brand-light) !important;
    color: #3730a3 !important;
    box-shadow: 0 4px 16px rgba(99,102,241,0.15) !important;
    transform: translateY(-2px) !important;
}
.suggestion-card .stButton > button[kind="primary"] {
    background: linear-gradient(135deg, var(--brand) 0%, var(--brand-dark) 100%) !important;
    border: 2px solid var(--brand-dark) !important;
    color: #ffffff !important;
    box-shadow: 0 4px 14px rgba(99,102,241,0.35) !important;
    font-weight: 700 !important;
}

/* ── BOTÓN GENERAR ── */
.generate-btn .stButton > button,
.generate-btn .stButton > button p,
.generate-btn .stButton > button span,
.generate-btn .stButton > button div {
    min-height: 62px !important;
    font-size: 1.1rem !important;
    font-weight: 800 !important;
    letter-spacing: 0.4px !important;
    border-radius: var(--radius-lg) !important;
    background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%) !important;
    box-shadow: 0 8px 28px rgba(99,102,241,0.4) !important;
    border: none !important;
    color: #ffffff !important;
    text-shadow: 0 1px 2px rgba(0,0,0,0.15) !important;
}
.generate-btn .stButton > button:hover {
    box-shadow: 0 10px 36px rgba(99,102,241,0.55) !important;
    transform: translateY(-2px) !important;
    filter: brightness(1.08) !important;
}

/* ── DOWNLOAD ── */
.stDownloadButton > button {
    width: 100% !important;
    min-height: 56px !important;
    font-size: 0.98rem !important;
    font-weight: 700 !important;
    border-radius: var(--radius-lg) !important;
    background: linear-gradient(135deg, #059669, #047857) !important;
    color: #ffffff !important;
    border: none !important;
    box-shadow: 0 6px 20px rgba(5,150,105,0.3) !important;
    letter-spacing: 0.2px !important;
    transition: var(--transition) !important;
}
.stDownloadButton > button:hover {
    box-shadow: 0 8px 28px rgba(5,150,105,0.45) !important;
    transform: translateY(-2px) !important;
    filter: brightness(1.06) !important;
}

/* ── INPUTS ── */
.stTextInput > div > div > input,
.stTextInput > div > div > input:not([disabled]) {
    min-height: 52px !important;
    height: 52px !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.95rem !important;
    line-height: 1.5 !important;
    border-radius: var(--radius-md) !important;
    background: var(--surface) !important;
    border: 1.5px solid var(--border) !important;
    color: var(--text-primary) !important;
    padding: 14px 16px !important;
    transition: var(--transition) !important;
    box-shadow: var(--shadow-sm) !important;
    overflow: visible !important;
}
.stTextInput > div > div > input:focus {
    border-color: var(--brand) !important;
    box-shadow: 0 0 0 3px var(--brand-glow) !important;
    outline: none !important;
}
.stTextInput > div > div > input::placeholder {
    color: var(--text-muted) !important;
    font-weight: 400 !important;
}

/* Textarea (log, script) */
.stTextArea textarea {
    font-family: 'JetBrains Mono', 'Courier New', monospace !important;
    font-size: 0.78rem !important;
    background: #fafafa !important;
    border: 1.5px solid var(--border) !important;
    border-radius: var(--radius-md) !important;
    color: var(--text-secondary) !important;
    line-height: 1.6 !important;
    transition: var(--transition) !important;
}
.stTextArea textarea:focus {
    border-color: var(--brand) !important;
    box-shadow: 0 0 0 3px var(--brand-glow) !important;
}

/* ── SELECTBOX ── */
.stSelectbox > div > div {
    min-height: 48px !important;
    border-radius: var(--radius-md) !important;
    background: var(--surface) !important;
    border: 1.5px solid var(--border) !important;
    box-shadow: var(--shadow-sm) !important;
    transition: var(--transition) !important;
}
.stSelectbox > div > div:focus-within {
    border-color: var(--brand) !important;
    box-shadow: 0 0 0 3px var(--brand-glow) !important;
}
.stSelectbox [data-baseweb="select"] div {
    color: var(--text-primary) !important;
    font-size: 0.93rem !important;
}

/* ── PASSWORD INPUT ── */
.stTextInput[data-baseweb="input"] { border-radius: var(--radius-md) !important; }

/* ── SLIDER — forzar color índigo sobre el rojo de Streamlit ── */
/* Thumb (círculo arrastrable) */
[data-testid="stSlider"] [role="slider"],
[data-testid="stSlider"] div[role="slider"],
[data-baseweb="slider"] div[role="slider"] {
    background: var(--brand) !important;
    border: 3px solid #ffffff !important;
    box-shadow: 0 0 0 2px var(--brand), 0 2px 8px var(--brand-glow) !important;
    width: 20px !important; height: 20px !important;
}
/* Valor encima del thumb */
[data-testid="stSlider"] [data-testid="stThumbValue"],
[data-testid="stSlider"] [data-baseweb="slider"] [data-testid="stThumbValue"] {
    color: var(--brand) !important;
    font-weight: 700 !important;
    font-size: 0.82rem !important;
}
/* Track llenado (la parte izquierda del slider) */
[data-baseweb="slider-track-fill"],
[data-testid="stSlider"] [data-baseweb="slider-track-fill"],
[data-testid="stSlider"] [data-baseweb="slider"] > div > div:first-child > div:first-child {
    background: var(--brand) !important;
}
/* Trick global: accent-color cubre inputs range en navegadores modernos */
[data-testid="stSlider"] { accent-color: var(--brand) !important; }
[data-testid="stSlider"] input[type="range"] {
    accent-color: var(--brand) !important;
}

/* ── TOGGLE / CHECKBOX ── */
.stCheckbox > label, .stToggle > label {
    font-size: 0.9rem !important;
    font-weight: 500 !important;
    color: var(--text-secondary) !important;
}

/* ── PROGRESS BAR ── */
.stProgress > div > div {
    background: linear-gradient(90deg, var(--brand), #818cf8) !important;
    border-radius: 99px !important;
    transition: width 0.4s ease !important;
}
.stProgress > div {
    background: var(--surface-3) !important;
    border-radius: 99px !important;
    height: 7px !important;
    box-shadow: inset 0 1px 2px rgba(0,0,0,0.06) !important;
}

/* ── TABS ── */
.stTabs [data-baseweb="tab-list"] {
    background: var(--surface-3) !important;
    border-radius: var(--radius-md) var(--radius-md) 0 0 !important;
    padding: 4px !important;
    gap: 2px !important;
    border: 1px solid var(--border) !important;
    border-bottom: none !important;
}
.stTabs [data-baseweb="tab"] {
    font-size: 0.85rem !important;
    font-weight: 600 !important;
    padding: 9px 16px !important;
    border-radius: var(--radius-sm) !important;
    color: var(--text-muted) !important;
    border: none !important;
    background: transparent !important;
    transition: var(--transition) !important;
}
.stTabs [data-baseweb="tab"]:hover {
    color: var(--brand) !important;
    background: var(--brand-light) !important;
}
.stTabs [aria-selected="true"] {
    background: var(--surface) !important;
    color: var(--brand) !important;
    box-shadow: var(--shadow-sm) !important;
    font-weight: 700 !important;
}
.stTabs [data-baseweb="tab-highlight"] {
    display: none !important;
}
.stTabs [data-baseweb="tab-panel"] {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-top: none !important;
    border-radius: 0 0 var(--radius-md) var(--radius-md) !important;
    padding: 20px !important;
}

/* ── EXPANDER ── */
.stExpander {
    border: 1.5px solid var(--border) !important;
    border-radius: var(--radius-md) !important;
    background: var(--surface) !important;
    box-shadow: var(--shadow-sm) !important;
    overflow: hidden !important;
    margin-bottom: 12px !important;
}
.stExpander summary {
    font-weight: 600 !important;
    font-size: 0.9rem !important;
    color: var(--text-secondary) !important;
    padding: 14px 18px !important;
}
.stExpander summary:hover { color: var(--brand) !important; }

/* Expander de voz — highlight sutil */
.stExpander:has(summary:first-child) {
    border-color: #c7d2fe !important;
}

/* ── OCULTAR labels internos "lang" y "mode" de Streamlit ── */
[data-testid="stWidgetLabel"]:has(+ [data-testid="stRadio"]) {
    display: none !important;
}
/* Por si Streamlit usa otra estructura */
.stRadio > label { display: none !important; }

/* ── TOGGLE DE IDIOMA compacto (columna derecha del hero) ── */
.lang-toggle [data-testid="stRadio"] {
    background: var(--surface) !important;
    border-radius: var(--radius-md) !important;
    padding: 3px !important;
    border: 1.5px solid var(--border) !important;
    box-shadow: var(--shadow-sm) !important;
    margin-top: 8px !important;
}
.lang-toggle [data-testid="stRadio"] > div {
    flex-direction: column !important;
    gap: 2px !important;
}
.lang-toggle [data-testid="stRadio"] label {
    padding: 7px 10px !important;
    font-size: 0.82rem !important;
    font-weight: 600 !important;
    border-radius: 8px !important;
    color: var(--text-muted) !important;
    text-align: center !important;
    flex: unset !important;
}
.lang-toggle [data-testid="stRadio"] label:has(input:checked) {
    background: var(--brand) !important;
    color: #fff !important;
    box-shadow: none !important;
}

/* ── ALERTS ── */
.stSuccess > div {
    background: #ecfdf5 !important;
    border: 1px solid #a7f3d0 !important;
    border-radius: var(--radius-md) !important;
    color: #065f46 !important;
}
.stInfo > div {
    background: #eff6ff !important;
    border: 1px solid #bfdbfe !important;
    border-radius: var(--radius-md) !important;
    color: #1e40af !important;
}
.stWarning > div {
    background: #fffbeb !important;
    border: 1px solid #fde68a !important;
    border-radius: var(--radius-md) !important;
    color: #92400e !important;
}
.stError > div {
    background: #fef2f2 !important;
    border: 1px solid #fecaca !important;
    border-radius: var(--radius-md) !important;
    color: #991b1b !important;
}

/* ── CODE BLOCKS ── */
.stCode, pre, code {
    font-family: 'JetBrains Mono', 'Courier New', monospace !important;
    background: #f8fafc !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-sm) !important;
    font-size: 0.82rem !important;
    color: #1e293b !important;
}

/* ── DIVIDER ── */
hr {
    border: none !important;
    border-top: 1px solid var(--border) !important;
    margin: 24px 0 !important;
}

/* ── CAPTION ── */
.stCaption {
    color: var(--text-muted) !important;
    font-size: 0.8rem !important;
}

/* ── VIDEO PLAYER ── */
.stVideo video {
    border-radius: var(--radius-lg) !important;
    box-shadow: var(--shadow-lg) !important;
}

/* ── SIDEBAR AJUSTES ── */
[data-testid="stSidebar"] .stButton > button {
    min-height: 42px !important;
    font-size: 0.85rem !important;
}
[data-testid="stSidebar"] .stTextInput > div > div > input {
    min-height: 42px !important;
    font-size: 0.88rem !important;
}
[data-testid="stSidebar"] hr {
    border-color: #f3f4f6 !important;
    margin: 14px 0 !important;
}
[data-testid="stSidebar"] .stSelectbox > div > div {
    min-height: 42px !important;
}
[data-testid="stSidebar"] label {
    font-size: 0.82rem !important;
}
[data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
    font-size: 0.95rem !important;
    font-weight: 700 !important;
    color: var(--text-primary) !important;
    margin-bottom: 8px !important;
}

/* ── BOTÓN REINICIAR ── */
.restart-btn .stButton > button,
.restart-btn .stButton > button p,
.restart-btn .stButton > button span {
    min-height: 52px !important;
    font-size: 0.95rem !important;
    font-weight: 600 !important;
    border-radius: var(--radius-md) !important;
    background: var(--surface-3) !important;
    color: var(--text-secondary) !important;
    border: 1.5px solid var(--border) !important;
    transition: var(--transition) !important;
}
.restart-btn .stButton > button:hover,
.restart-btn .stButton > button:hover p,
.restart-btn .stButton > button:hover span {
    background: #fef2f2 !important;
    border-color: #fca5a5 !important;
    color: #b91c1c !important;
}

/* ── SECTION LABEL ── */
.section-label {
    font-size: 0.78rem !important;
    font-weight: 600 !important;
    color: var(--text-muted) !important;
    text-transform: uppercase !important;
    letter-spacing: 0.8px !important;
    margin: 0 0 6px 2px !important;
}

/* ── RESPONSIVE: TABLET ── */
@media (max-width: 1024px) {
    .block-container { padding: 1.5rem 1.25rem 3rem !important; }
}

/* ── RESPONSIVE: MOBILE ── */
@media (max-width: 640px) {
    .block-container { padding: 1rem 0.75rem 3rem !important; }
    .hero-title { font-size: 1.65rem !important; letter-spacing: -0.4px !important; }
    .hero-sub   { font-size: 0.88rem !important; }
    .stButton > button { min-height: 54px !important; font-size: 0.92rem !important; }
    .generate-btn .stButton > button { min-height: 60px !important; font-size: 1rem !important; }
    .stTabs [data-baseweb="tab"] { font-size: 0.78rem !important; padding: 8px 10px !important; }
    [data-testid="stSidebar"] { min-width: 280px !important; max-width: 300px !important; }
    .step-header { font-size: 0.85rem !important; padding: 10px 14px !important; }
    .suggestion-card .stButton > button { min-height: 68px !important; font-size: 0.83rem !important; }
    h1 { font-size: 1.3rem !important; }
    h2 { font-size: 1.05rem !important; }
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
        <h1 style="margin:0.5rem 0; font-family:'Plus Jakarta Sans',sans-serif;">AutoShorts AI</h1>
        <p style="color:#9ca3af; margin-bottom:2rem; font-size:0.95rem;">Ingresa la contraseña para continuar</p>
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
        "restart_btn":       "🔄 Crear Otro Video",
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
        "restart_btn":       "🔄 Create Another Video",
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

# ── Sidebar — solo API keys (configuración única) ────────────────────────────

# Necesitamos lang_option antes del sidebar para el diccionario T
lang_option = st.session_state.lang
T = UI[lang_option]

with st.sidebar:
    st.markdown("# ⚙️ AutoShorts AI")
    st.caption("Configuración de API" if lang_option == "es" else "API Settings")
    st.divider()

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
    if check_config():
        st.success(T["config_ready"])
    else:
        st.warning(T["config_incomplete"])

# ── Main area ─────────────────────────────────────────────────────────────────

# ── Header: título + toggle de idioma en la misma fila ───────────────────────
col_hero, col_lang = st.columns([3, 1])

with col_hero:
    T = UI[lang_option]
    st.markdown(
        f"<div class='hero-title'>{T['page_title']}</div>"
        f"<p class='hero-sub'>{T['page_caption']}</p>",
        unsafe_allow_html=True,
    )

with col_lang:
    st.markdown("<div class='lang-toggle'>", unsafe_allow_html=True)
    lang_option = st.radio(
        "lang",
        options=["es", "en"],
        format_func=lambda x: "🇪🇸 ES" if x == "es" else "🇺🇸 EN",
        index=0 if st.session_state.lang == "es" else 1,
        horizontal=False,
        label_visibility="collapsed",
        key="lang_main",
    )
    st.markdown("</div>", unsafe_allow_html=True)

if lang_option != st.session_state.lang:
    st.session_state.lang              = lang_option
    st.session_state.topic_suggestions = []
    st.session_state.selected_topic    = ""
    st.session_state.selected_category = ""
    st.rerun()

T = UI[lang_option]

config_ok  = check_config()
CATEGORIES = TOPIC_CATEGORIES_ES if lang_option == "es" else TOPIC_CATEGORIES_EN

# ── Configuración de Voz (expander accesible en móvil) ───────────────────────

VOICES        = VOICES_ES if lang_option == "es" else VOICES_EN
default_voice = T["default_voice"]

voice_label_hint = "🎙️ Voz y velocidad" if lang_option == "es" else "🎙️ Voice & speed"
with st.expander(voice_label_hint, expanded=False):
    voice_label = st.selectbox(
        T["narrator_voice"],
        options=list(VOICES.keys()),
        index=list(VOICES.keys()).index(default_voice) if default_voice in VOICES else 0,
        key="voice_select",
    )
    selected_voice = VOICES[voice_label]

    col_prev, col_spin = st.columns([1, 2])
    with col_prev:
        preview_clicked = st.button(T["preview_btn"], use_container_width=True, key="preview_btn_main")
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
                         format="%+d%%", help=T["speech_help"], key="rate_slider")
    rate_str = f"+{rate_pct}%" if rate_pct >= 0 else f"{rate_pct}%"

    use_avatar    = st.toggle(T["avatar_toggle"],    value=False, help=T["avatar_help"],    key="avatar_toggle")
    use_subtitles = st.toggle(T["subtitles_toggle"], value=False, help=T["subtitles_help"], key="subs_toggle")

# ── Selector de modo ──────────────────────────────────────────────────────────

mode_labels = (
    ["⚡ Automático", "🗂️ Por Categoría"]
    if lang_option == "es"
    else ["⚡ Automatic", "🗂️ By Category"]
)
st.markdown(
    f"<p class='section-label'>{'Modo de generación' if lang_option == 'es' else 'Generation mode'}</p>",
    unsafe_allow_html=True,
)
mode = st.radio(
    "mode",
    options=["auto", "category"],
    format_func=lambda x: mode_labels[0] if x == "auto" else mode_labels[1],
    horizontal=True,
    label_visibility="collapsed",
    key="generation_mode",
)

if mode != st.session_state.get("_last_mode"):
    st.session_state.topic_suggestions = []
    st.session_state.selected_topic    = ""
    st.session_state["_last_mode"]     = mode

st.markdown("---")

# ══════════════════════════════════════════════════════════════════════════════
# MODO AUTOMÁTICO
# ══════════════════════════════════════════════════════════════════════════════

if mode == "auto":

    auto_hint = (
        "La IA elige una categoría y tema viral automáticamente. Solo presiona Generar."
        if lang_option == "es"
        else "The AI picks a category and viral topic automatically. Just press Generate."
    )
    st.markdown(f"<div class='auto-info'>✨ {auto_hint}</div>", unsafe_allow_html=True)

    manual_topic_auto = st.text_input(
        "Tema opcional" if lang_option == "es" else "Optional topic",
        key="manual_topic_input",
        placeholder=(
            "Déjalo vacío para que la IA elija, o escribe tu propio tema..."
            if lang_option == "es"
            else "Leave blank for AI to choose, or type your own topic..."
        ),
    )

    num_scenes = st.slider(T["scenes_label"], min_value=5, max_value=12, value=9)
    final_topic = manual_topic_auto.strip()

# ══════════════════════════════════════════════════════════════════════════════
# MODO POR CATEGORÍA
# ══════════════════════════════════════════════════════════════════════════════

else:

    # ── Paso 1 ────────────────────────────────────────────────────────────────
    st.markdown(f"<div class='step-header'>{T['step1']}</div>", unsafe_allow_html=True)

    selected_category = st.selectbox(
        "cat", options=[""] + CATEGORIES,
        format_func=lambda x: T["category_placeholder"] if x == "" else x,
        label_visibility="collapsed",
    )

    # ── Paso 2 ────────────────────────────────────────────────────────────────
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
            try:
                from modules.brain import ContentBrain as _BS
                suggestions = _BS().get_topic_suggestions(selected_category, n=6, lang=lang_option)
                st.session_state.topic_suggestions = suggestions
                st.session_state.selected_topic    = ""
                st.rerun()
            except Exception as _err:
                _msg = str(_err)
                if "NotFound" in _msg or "404" in _msg or "model" in _msg.lower():
                    st.error("❌ Modelo de IA no encontrado. Verifica **AI_MODEL** en los Secrets de Streamlit Cloud.")
                elif "auth" in _msg.lower() or "401" in _msg or "403" in _msg:
                    st.error("❌ Clave de API inválida. Verifica **AI_API_KEY** en los Secrets.")
                else:
                    st.error(f"❌ Error: {_msg[:200]}")

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

    # ── Paso 3 ────────────────────────────────────────────────────────────────
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
st.markdown("<div class='generate-btn'>", unsafe_allow_html=True)
generate_clicked = st.button(T["generate_btn"],
    disabled=st.session_state.running or not config_ok,
    type="primary", use_container_width=True)
st.markdown("</div>", unsafe_allow_html=True)

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
        st.text_area("log", value="\n".join(visible), height=180, disabled=True, label_visibility="collapsed")

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


def _reset_session():
    """Limpia todo el estado para empezar de nuevo."""
    keys_to_reset = [
        "running", "log_lines", "status", "thread",
        "copy_data", "thumb_prompt", "script_data",
        "selected_category", "topic_suggestions", "selected_topic",
        "_last_mode",
    ]
    for k in keys_to_reset:
        if k in st.session_state:
            del st.session_state[k]
    # Limpiar el input de tema si existe
    for k in list(st.session_state.keys()):
        if "manual_topic" in k or "topic_input" in k:
            del st.session_state[k]
    st.rerun()


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
            st.text_area("script", value=full_script, height=400, label_visibility="collapsed")
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
            st.text_area("thumb", value=thumb, height=320, label_visibility="collapsed")
            st.button("📋 Copiar", key="copy_thumb", use_container_width=True)
        else:
            st.info("No disponible.")

    # ── Botón Volver a Comenzar ───────────────────────────────────────────────
    st.markdown("---")
    st.markdown("<div class='restart-btn'>", unsafe_allow_html=True)
    if st.button(T["restart_btn"], key="restart_done", use_container_width=True, type="secondary"):
        _reset_session()
    st.markdown("</div>", unsafe_allow_html=True)

elif st.session_state.status == "error":
    err = next((l.split(":", 1)[1] for l in st.session_state.log_lines if l.startswith("ERROR:")), "Unknown error")
    st.error(f"{T['error_prefix']} {err}")
    st.info(T["error_hint"])
    st.markdown("<div class='restart-btn'>", unsafe_allow_html=True)
    if st.button(T["restart_btn"], key="restart_error", use_container_width=True, type="secondary"):
        _reset_session()
    st.markdown("</div>", unsafe_allow_html=True)
