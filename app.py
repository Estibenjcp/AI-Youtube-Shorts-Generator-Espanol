import warnings
warnings.filterwarnings("ignore", message="Accessing `__path__`")

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
from modules.categories import (
    TOPIC_CATEGORIES_ES, TOPIC_CATEGORIES_EN,
    VIRAL_CATEGORIES, VIRAL_CATEGORIES_EN,
    TESTIMONIO_CATEGORIES, TESTIMONIO_CATEGORIES_EN,
    BOOK_CATEGORIES, BOOK_CATEGORIES_EN,
)
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

/* ── MODE SELECTOR BUTTONS: compactos y uniformes ── */
div[data-testid="stSidebar"] .mode-grid-btn button {
    font-size: 0.82rem !important;
    padding: 7px 4px !important;
    min-height: 42px !important;
    white-space: normal !important;
    line-height: 1.2 !important;
}

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

/* ── TOGGLE DE IDIOMA compacto (emoji only, horizontal) ── */
.lang-toggle {
    display: flex;
    justify-content: flex-end;
    padding-top: 6px;
}
.lang-toggle [data-testid="stRadio"] {
    background: var(--surface) !important;
    border-radius: 99px !important;
    padding: 3px !important;
    border: 1.5px solid var(--border) !important;
    box-shadow: var(--shadow-sm) !important;
    width: fit-content !important;
    min-width: unset !important;
}
.lang-toggle [data-testid="stRadio"] > div {
    flex-direction: row !important;
    gap: 2px !important;
    flex-wrap: nowrap !important;
    width: fit-content !important;
}
.lang-toggle [data-testid="stRadio"] label {
    padding: 6px 12px !important;
    font-size: 1.1rem !important;
    border-radius: 99px !important;
    color: var(--text-muted) !important;
    text-align: center !important;
    flex: unset !important;
    width: auto !important;
    min-width: unset !important;
    white-space: nowrap !important;
}
.lang-toggle [data-testid="stRadio"] label:has(input:checked) {
    background: var(--brand) !important;
    color: #fff !important;
    box-shadow: 0 2px 8px var(--brand-glow) !important;
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
    # ── México ────────────────────────────────────────────────
    "Álvaro — España Masculino ⭐ (misterio)": "es-ES-AlvaroNeural",
    "Jorge — México Masculino ⭐":              "es-MX-JorgeNeural",
    "Dalia — México Femenina ⭐":               "es-MX-DaliaNeural",
    "Gerardo — México Masculino":               "es-MX-GerardoNeural",
    "Luciano — México Masculino":               "es-MX-LucianoNeural",
    "Pelayo — México Masculino":                "es-MX-PelayoNeural",
    "Yago — México Masculino":                  "es-MX-YagoNeural",
    "Beatriz — México Femenina":                "es-MX-BeatrizNeural",
    "Candela — México Femenina":                "es-MX-CandelaNeural",
    "Carlota — México Femenina":                "es-MX-CarlotaNeural",
    "Larissa — México Femenina":                "es-MX-LarissaNeural",
    "Marina — México Femenina":                 "es-MX-MarinaNeural",
    "Nuria — México Femenina":                  "es-MX-NuriaNeural",
    # ── España ────────────────────────────────────────────────
    "Elvira — España Femenina":                 "es-ES-ElviraNeural",
    "Dario — España Masculino":                 "es-ES-DarioNeural",
    "Elias — España Masculino":                 "es-ES-EliasNeural",
    "Saul — España Masculino":                  "es-ES-SaulNeural",
    "Teo — España Masculino":                   "es-ES-TeoNeural",
    "Abril — España Femenina":                  "es-ES-AbrilNeural",
    "Estrella — España Femenina":               "es-ES-EstrellaNeural",
    "Irene — España Femenina":                  "es-ES-IreneNeural",
    "Triana — España Femenina":                 "es-ES-TrianaNeural",
    "Vera — España Femenina":                   "es-ES-VeraNeural",
    "Ximena — España Femenina":                 "es-ES-XimenaNeural",
    # ── Latinoamérica ─────────────────────────────────────────
    "Paloma — EE.UU. Femenina":                 "es-US-PalomaNeural",
    "Alonso — EE.UU. Masculino":                "es-US-AlonsoNeural",
    "Camila — Perú Femenina":                   "es-PE-CamilaNeural",
    "Alex — Perú Masculino":                    "es-PE-AlexNeural",
    "Salomé — Colombia Femenina":               "es-CO-SalomeNeural",
    "Gonzalo — Colombia Masculino":             "es-CO-GonzaloNeural",
    "Elena — Argentina Femenina":               "es-AR-ElenaNeural",
    "Tomas — Argentina Masculino":              "es-AR-TomasNeural",
    "Paola — Venezuela Femenina":               "es-VE-PaolaNeural",
    "Sebastian — Venezuela Masculino":          "es-VE-SebastianNeural",
    "Catalina — Chile Femenina":                "es-CL-CatalinaNeural",
    "Lorenzo — Chile Masculino":                "es-CL-LorenzoNeural",
    "Mateo — Uruguay Masculino":                "es-UY-MateoNeural",
    "Valentina — Uruguay Femenina":             "es-UY-ValentinaNeural",
    "Karina — Puerto Rico Femenina":            "es-PR-KarinaNeural",
    "Victor — Puerto Rico Masculino":           "es-PR-VictorNeural",
}

VOICES_EN = {
    # ── US ────────────────────────────────────────────────────
    "Ryan — UK Male ⭐ (mystery)":   "en-GB-RyanNeural",
    "Andrew — US Male ⭐":            "en-US-AndrewNeural",
    "Ava — US Female ⭐":             "en-US-AvaNeural",
    "Brian — US Male":               "en-US-BrianNeural",
    "Davis — US Male":               "en-US-DavisNeural",
    "Guy — US Male":                 "en-US-GuyNeural",
    "Jason — US Male":               "en-US-JasonNeural",
    "Roger — US Male":               "en-US-RogerNeural",
    "Steffan — US Male":             "en-US-SteffanNeural",
    "Tony — US Male":                "en-US-TonyNeural",
    "Aria — US Female":              "en-US-AriaNeural",
    "Amber — US Female":             "en-US-AmberNeural",
    "Emma — US Female":              "en-US-EmmaNeural",
    "Jenny — US Female":             "en-US-JennyNeural",
    "Michelle — US Female":          "en-US-MichelleNeural",
    "Monica — US Female":            "en-US-MonicaNeural",
    "Nancy — US Female":             "en-US-NancyNeural",
    "Sara — US Female":              "en-US-SaraNeural",
    # ── UK ────────────────────────────────────────────────────
    "Sonia — UK Female":             "en-GB-SoniaNeural",
    "Libby — UK Female":             "en-GB-LibbyNeural",
    "Thomas — UK Male":              "en-GB-ThomasNeural",
    # ── AU ────────────────────────────────────────────────────
    "Natasha — AU Female":           "en-AU-NatashaNeural",
    "William — AU Male":             "en-AU-WilliamNeural",
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
        "viral_mode_info":   "🔥 Guion ultra-viral de 45-60 seg — estructura MrBeast + Dark History. Hook demoledor, giro inesperado y CTA que engancha.",
        "viral_category":    "Categoría del tema",
        "viral_topic":       "Tema (opcional — déjalo vacío para que la IA elija)",
        "viral_topic_ph":    "ej. La conspiración del Proyecto MKUltra...",
        "testimonio_info":   "👁️ Narra como un testimonio real — estilo terror cinematográfico. 3 clips por escena, tono oscuro y voz grave.",
        "testimonio_cat":    "Categoría del testimonio",
        "testimonio_topic":  "Tema (opcional — déjalo vacío para que la IA elija)",
        "testimonio_topic_ph": "ej. La secta que operaba en las catacumbas de Roma...",
        "libro_info":        "📚 Resumen de 60 seg que enseña, aplica y motiva a leer el libro. Tono inspirador y educativo.",
        "libro_cat":         "Género del libro",
        "libro_topic":       "Título del libro (opcional — déjalo vacío para que la IA elija)",
        "libro_topic_ph":    "ej. Hábitos Atómicos — James Clear...",
        "empleo_info":       "💼 Pega la oferta de empleo y la IA la convierte en un video promocional atractivo, sin inventar ni exagerar nada.",
        "empleo_label":      "Texto de la oferta de empleo",
        "empleo_ph":         "Pega aquí el texto completo: puesto, empresa, requisitos, salario, beneficios, cómo aplicar...",
        "empleo_warning":    "Por favor pega el texto de la oferta antes de generar.",
        "guion_info":        "✍️ Pega cualquier texto — noticia, chisme, dato curioso, reflexión o pensamiento — y la IA detecta el tono y lo convierte en un Short viral.",
        "guion_label":       "Tu texto (noticia, chisme, reflexión, lo que sea...)",
        "guion_ph":          "Pega aquí la noticia, el chisme, tu opinión, el dato curioso... La IA adaptará el tono automáticamente.",
        "guion_warning":     "Por favor pega o escribe tu texto antes de generar.",
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
        "viral_mode_info":   "🔥 Ultra-viral 45-60 sec script — MrBeast + Dark History structure. Devastating hook, unexpected twist and addictive CTA.",
        "viral_category":    "Topic category",
        "viral_topic":       "Topic (optional — leave blank for AI to choose)",
        "viral_topic_ph":    "e.g. The MKUltra mind control conspiracy...",
        "testimonio_info":   "👁️ Narrated as a real testimony — cinematic horror style. 3 clips per scene, dark tone and deep voice.",
        "testimonio_cat":    "Testimony category",
        "testimonio_topic":  "Topic (optional — leave blank for AI to choose)",
        "testimonio_topic_ph": "e.g. The cult operating in the catacombs of Rome...",
        "libro_info":        "📚 60-sec summary that teaches, applies and motivates reading. Inspiring and educational tone.",
        "libro_cat":         "Book genre",
        "libro_topic":       "Book title (optional — leave blank for AI to choose)",
        "libro_topic_ph":    "e.g. Atomic Habits — James Clear...",
        "empleo_info":       "💼 Paste the job offer and AI turns it into an attractive promotional video — no invented or exaggerated details.",
        "empleo_label":      "Job offer text",
        "empleo_ph":         "Paste the full text here: position, company, requirements, salary, benefits, how to apply...",
        "empleo_warning":    "Please paste the job offer text before generating.",
        "guion_info":        "✍️ Paste any text — news, gossip, fun fact, reflection or thought — and the AI detects the tone and turns it into a viral Short.",
        "guion_label":       "Your text (news, gossip, reflection, anything...)",
        "guion_ph":          "Paste your news article, gossip, opinion, fun fact... The AI will auto-detect the tone.",
        "guion_warning":     "Please paste or write your text before generating.",
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
    ("webhook_enabled",   False),
    ("webhook_url_input", "https://n8n.digency.lat/webhook/0a98a5c2-e3ec-4aa4-924d-e27ec8893125"),
    ("video_topic",       ""),
    ("hook_options",      []),
    ("chosen_hook",       ""),
    ("_pending_topic_desc", ""),
    ("job_offer_text",    ""),
    ("guion_raw_text",    ""),
    ("generation_mode",   "auto"),
    ("hook_step",         "idle"),
    ("tts_engine",        "edge_tts"),
    ("vox_voice_desc",    ""),
    ("vox_mood_enabled",  True),
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

        def flush(self):
            pass

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
        brain         = ContentBrain()
        pipeline_mode = params.get("mode", "auto")

        if pipeline_mode == "viral":
            topic       = params.get("topic", "").strip()
            category    = params.get("category", "").strip()
            chosen_hook = params.get("chosen_hook", "").strip()
            if not topic:
                topic = brain.get_trending_topic("", lang=pipeline_lang,
                                                 category_hint=category, mode="viral")
            script = brain.generate_viral_script(topic, category, lang=pipeline_lang, chosen_hook=chosen_hook)

        elif pipeline_mode == "testimonio":
            topic       = params.get("topic", "").strip()
            category    = params.get("category", "").strip()
            chosen_hook = params.get("chosen_hook", "").strip()
            if not topic:
                topic = brain.get_trending_topic("", lang=pipeline_lang,
                                                 category_hint=category, mode="testimonio")
            script = brain.generate_testimonio_script(topic, category, lang=pipeline_lang,
                                                      chosen_hook=chosen_hook)

        elif pipeline_mode == "libro":
            topic       = params.get("topic", "").strip()
            category    = params.get("category", "").strip()
            chosen_hook = params.get("chosen_hook", "").strip()
            if not topic:
                topic = brain.get_trending_topic("", lang=pipeline_lang,
                                                 category_hint=category, mode="libro")
            script = brain.generate_book_summary_script(topic, category, lang=pipeline_lang,
                                                        chosen_hook=chosen_hook)

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

        else:
            chosen_hook = params.get("chosen_hook", "").strip()
            topic  = brain.get_trending_topic(params.get("topic", ""),
                                              lang=pipeline_lang, mode="auto")
            script = brain.generate_script(topic, num_scenes=params.get("num_scenes", 9),
                                           lang=pipeline_lang, chosen_hook=chosen_hook)

        if not script:
            log_q.put("ERROR:Script generation failed.")
            return

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
        else:
            audio_engine = AudioEngine(
                voice = params.get("voice", "es-ES-AlvaroNeural"),
                rate  = params.get("rate", "+10%"),
            )
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
                                              use_subtitles=params.get("use_subtitles", False),
                                              subtitle_style=params.get("subtitle_style", {}))

        for folder in ["audio_clips", "video_clips", "temp"]:
            p = os.path.join(os.path.dirname(__file__), "assets", folder)
            if os.path.exists(p):
                shutil.rmtree(p)
                os.makedirs(p, exist_ok=True)

        copy_data    = brain.generate_copy(topic, script, lang=pipeline_lang, mode=pipeline_mode)
        thumb_prompt = brain.generate_thumbnail_prompt(topic, script, lang=pipeline_lang)

        log_q.put(f"COPY:{__import__('json').dumps(copy_data)}")
        log_q.put(f"THUMB:{thumb_prompt}")
        log_q.put(f"SCRIPT:{__import__('json').dumps(script)}")
        log_q.put(f"TOPIC:{topic}")

        # ── Enviar a webhook n8n ──────────────────────────────
        webhook_url = params.get("webhook_url", "").strip()
        if webhook_url:
            try:
                import requests as _req, base64 as _b64
                video_path  = os.path.join(os.path.dirname(__file__), "assets", "final", "final_short.mp4")
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

    # ── Webhook n8n ───────────────────────────────────────
    st.divider()
    st.caption("🔗 Webhook n8n")
    webhook_enabled = st.toggle(
        "Enviar a n8n" if lang_option == "es" else "Send to n8n",
        key="webhook_enabled",
    )
    st.text_input(
        "URL del webhook",
        placeholder="https://n8n.../webhook/...",
        label_visibility="collapsed",
        key="webhook_url_input",
    )
    if webhook_enabled:
        st.caption("✅ " + ("Datos + video se enviarán al generar." if lang_option == "es" else "Data + video will be sent on generate."))

    # Botón de prueba
    _wh_url_now = st.session_state.get("webhook_url_input", "").strip()
    if st.button("🧪 " + ("Probar conexión" if lang_option == "es" else "Test connection"),
                 use_container_width=True, disabled=not _wh_url_now):
        import requests as _r
        _test_payload = {
            "test": True,
            "topic": "Test desde AutoShorts AI",
            "lang": lang_option,
            "mode": "test",
            "script_text": "Este es un mensaje de prueba del webhook.",
            "youtube_title": "Test YouTube Title #Shorts",
            "youtube_description": "Descripción de prueba.",
            "tiktok_caption": "Caption de prueba TikTok",
            "facebook_caption": "Caption de prueba Facebook",
            "thumbnail_prompt": "Test thumbnail prompt",
            "video_base64": "",
            "video_filename": "",
            "video_mimetype": "video/mp4",
        }
        try:
            with st.spinner("Probando..."):
                _resp = _r.post(
                    _wh_url_now,
                    json=_test_payload,
                    headers={"Content-Type": "application/json"},
                    timeout=15,
                )
            if _resp.status_code in (200, 201, 202):
                st.success(f"✅ Conexión OK ({_resp.status_code})")
            else:
                st.error(f"❌ Error {_resp.status_code}: {_resp.text[:200]}")
        except Exception as _e:
            st.error(f"❌ {_e}")

    # ── Export / Import config ────────────────────────────
    st.divider()
    st.caption("💾 " + ("Exportar / Importar configuración" if lang_option == "es" else "Export / Import config"))

    # Export
    import json as _json
    export_data = _json.dumps({
        "AI_PROVIDER":    cfg["AI_PROVIDER"],
        "AI_API_KEY":     cfg["AI_API_KEY"],
        "AI_MODEL":       cfg["AI_MODEL"],
        "PEXELS_API_KEY": cfg["PEXELS_API_KEY"],
    }, indent=2)
    st.download_button(
        label="⬇️ " + ("Exportar claves" if lang_option == "es" else "Export keys"),
        data=export_data,
        file_name="autoshorts_config.json",
        mime="application/json",
        use_container_width=True,
    )

    # Import
    uploaded = st.file_uploader(
        "⬆️ " + ("Importar claves (.json)" if lang_option == "es" else "Import keys (.json)"),
        type="json",
        label_visibility="collapsed",
    )
    if uploaded is not None:
        try:
            imported = _json.loads(uploaded.read())
            set_key(ENV_PATH, "AI_PROVIDER",    imported.get("AI_PROVIDER", ""))
            set_key(ENV_PATH, "AI_API_KEY",     imported.get("AI_API_KEY", ""))
            set_key(ENV_PATH, "AI_MODEL",       imported.get("AI_MODEL", ""))
            set_key(ENV_PATH, "PEXELS_API_KEY", imported.get("PEXELS_API_KEY", ""))
            load_dotenv(ENV_PATH, override=True)
            st.success("✅ " + ("Configuración importada. Recarga la página." if lang_option == "es" else "Config imported. Reload the page."))
        except Exception as _e:
            st.error(f"❌ Error: {_e}")

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
        format_func=lambda x: "🇪🇸" if x == "es" else "🇺🇸",
        index=0 if st.session_state.lang == "es" else 1,
        horizontal=True,
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

# Reset voice selection when language changes so default always matches
_voice_lang_key = f"voice_lang_{lang_option}"
if _voice_lang_key not in st.session_state:
    # New language — clear any stale voice_select state
    st.session_state.pop("voice_select", None)
    st.session_state[_voice_lang_key] = True

voice_label_hint = "🎙️ Voz y velocidad" if lang_option == "es" else "🎙️ Voice & speed"
with st.expander(voice_label_hint, expanded=False):

    # ── Motor TTS ─────────────────────────────────────────────────────────
    _tts_labels = {
        "edge_tts": "☁️ Edge TTS (nube, rápido)" if lang_option == "es" else "☁️ Edge TTS (cloud, fast)",
        "voxcpm":   "🤖 VoxCPM 2B (local, GPU)" if lang_option == "es" else "🤖 VoxCPM 2B (local, GPU)",
    }
    tts_engine = st.radio(
        "Motor TTS" if lang_option == "es" else "TTS Engine",
        options=list(_tts_labels.keys()),
        format_func=lambda x: _tts_labels[x],
        horizontal=True,
        index=0 if st.session_state.get("tts_engine", "edge_tts") == "edge_tts" else 1,
        key="tts_engine_radio",
    )
    st.session_state["tts_engine"] = tts_engine

    st.markdown("---")

    if tts_engine == "edge_tts":
        # ── Edge TTS controls (existing) ──────────────────────────────────
        _voice_options = list(VOICES.keys())
        _default_idx   = _voice_options.index(default_voice) if default_voice in _voice_options else 0
        voice_label = st.selectbox(
            T["narrator_voice"],
            options=_voice_options,
            index=_default_idx,
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

    else:
        # ── VoxCPM controls ───────────────────────────────────────────────
        selected_voice = ""   # not used by VoxCPM
        rate_str       = "+0%"

        # Check availability
        _vox_ok = False
        try:
            import voxcpm as _vox_check  # noqa
            _vox_ok = True
        except ImportError:
            pass

        if _vox_ok:
            st.success("✅ VoxCPM instalado y listo." if lang_option == "es" else "✅ VoxCPM installed and ready.")
        else:
            st.error("❌ VoxCPM no encontrado. Instala con:" if lang_option == "es" else "❌ VoxCPM not found. Install with:")
            st.code("pip install voxcpm soundfile", language="bash")

        # Mood-adaptive toggle
        vox_mood = st.toggle(
            "🎭 Voz adaptada al mood de cada escena" if lang_option == "es" else "🎭 Mood-adaptive voice per scene",
            value=st.session_state.get("vox_mood_enabled", True),
            key="vox_mood_toggle",
            help=(
                "Cada escena usa una descripción de voz diferente según su mood (dramatic, calm, exciting…)"
                if lang_option == "es" else
                "Each scene uses a different voice description based on its mood (dramatic, calm, exciting…)"
            ),
        )
        st.session_state["vox_mood_enabled"] = vox_mood

        if not vox_mood:
            # Manual global description
            vox_desc = st.text_input(
                "Descripción de voz global" if lang_option == "es" else "Global voice description",
                value=st.session_state.get("vox_voice_desc", ""),
                key="vox_voice_desc_input",
                placeholder="(narrador masculino, voz grave y dramática, español neutro latino)",
            )
            st.session_state["vox_voice_desc"] = vox_desc
        else:
            st.session_state["vox_voice_desc"] = ""
            # Show mood → voice preview
            from modules.audio import VoxCPMAudioEngine as _VEng
            _mood_map = _VEng.MOOD_VOICES.get(lang_option, _VEng.MOOD_VOICES["es"])
            with st.expander("👁️ Ver voces por mood" if lang_option == "es" else "👁️ View voices by mood", expanded=False):
                for _m, _d in _mood_map.items():
                    st.caption(f"**{_m}** → {_d}")

        # ── Preview de voz VoxCPM ─────────────────────────────────────────
        _prev_text_vox = (
            "Hola, esta es mi voz. El video que estás a punto de crear será increíble."
            if lang_option == "es" else
            "Hello, this is my voice. The video you are about to create will be incredible."
        )
        _col_vp, _col_vs = st.columns([1, 2])
        with _col_vp:
            _vox_preview_clicked = st.button(
                "▶ Escuchar" if lang_option == "es" else "▶ Listen",
                use_container_width=True, key="vox_preview_btn",
                disabled=not _vox_ok,
            )
        with _col_vs:
            _vox_prev_status = st.empty()

        if _vox_preview_clicked and _vox_ok:
            _vox_prev_status.caption("Generando muestra..." if lang_option == "es" else "Generating sample...")
            _vox_prev_path = os.path.join(os.path.dirname(__file__), "assets", "temp", "vox_preview.wav")
            os.makedirs(os.path.dirname(_vox_prev_path), exist_ok=True)

            # Choose voice: manual desc, or the "dramatic" mood as representative sample
            _prev_desc = st.session_state.get("vox_voice_desc", "").strip()
            if not _prev_desc:
                from modules.audio import VoxCPMAudioEngine as _VEP
                _prev_desc = _VEP.MOOD_VOICES.get(lang_option, _VEP.MOOD_VOICES["es"]).get("dramatic", "")

            def _gen_vox_preview(desc, text, path):
                try:
                    from voxcpm import VoxCPM as _VC
                    import soundfile as _sf
                    _m = _VC.from_pretrained("openbmb/VoxCPM2", load_denoiser=False)
                    _wav = _m.generate(f"{desc} {text}", cfg_value=2.0)
                    _sf.write(path, _wav, 48000)
                except Exception as _e:
                    print(f"VoxCPM preview error: {_e}")

            import threading as _vt
            _vt.Thread(target=_gen_vox_preview,
                       args=(_prev_desc, _prev_text_vox, _vox_prev_path), daemon=True).start()
            import time as _vtime
            _vox_prev_status.caption("⏳ Procesando (~30s primera vez)..." if lang_option == "es" else "⏳ Processing (~30s first time)...")
            _vtime.sleep(35)
            _vox_prev_status.empty()
            if os.path.exists(_vox_prev_path) and os.path.getsize(_vox_prev_path) > 1000:
                st.audio(_vox_prev_path, format="audio/wav")
            else:
                st.warning("No se generó el audio. Verifica que VoxCPM está funcionando." if lang_option == "es" else "Audio not generated. Check VoxCPM is working.")

        # Optional: voice cloning reference
        _clone_label = "🎤 Audio de referencia para clonar tu voz (opcional)" if lang_option == "es" else "🎤 Reference audio for voice cloning (optional)"
        vox_clone_file = st.file_uploader(_clone_label, type=["wav", "mp3"], key="vox_clone_upload")
        if vox_clone_file is not None:
            _clone_path = os.path.join(os.path.dirname(__file__), "assets", "temp", "voice_ref" + os.path.splitext(vox_clone_file.name)[1])
            os.makedirs(os.path.dirname(_clone_path), exist_ok=True)
            with open(_clone_path, "wb") as _cf:
                _cf.write(vox_clone_file.read())
            st.session_state["vox_clone_ref"] = _clone_path
            st.success("✅ Referencia guardada." if lang_option == "es" else "✅ Reference saved.")
        else:
            st.session_state.setdefault("vox_clone_ref", "")

    use_avatar    = st.toggle(T["avatar_toggle"],    value=False, help=T["avatar_help"],    key="avatar_toggle")
    use_subtitles = st.toggle(T["subtitles_toggle"], value=True,  help=T["subtitles_help"], key="subs_toggle")

    # ── Configuración de subtítulos (visible solo si están activados) ──────────
    subtitle_style = {}
    if use_subtitles:
        _is_es = lang_option == "es"
        with st.expander("🎨 " + ("Estilo de subtítulos" if _is_es else "Subtitle Style"), expanded=False):

            # Tamaño
            _size_opts = (["Pequeño", "Mediano", "Grande", "Extra"] if _is_es
                          else ["Small", "Medium", "Large", "Extra"])
            _size_map  = dict(zip(_size_opts, [32, 44, 56, 72]))
            _size_sel  = st.select_slider(
                "Tamaño" if _is_es else "Size",
                options=_size_opts, value=_size_opts[2], key="sub_size"
            )
            subtitle_style["fontsize"] = _size_map[_size_sel]

            # Color de texto
            _color_opts = (["Blanco", "Amarillo", "Cian", "Verde"] if _is_es
                           else ["White", "Yellow", "Cyan", "Green"])
            _color_map  = dict(zip(_color_opts, ["white", "yellow", "00FFFF", "00FF88"]))
            _color_sel  = st.radio(
                "Color" if _is_es else "Color",
                options=_color_opts, horizontal=True, index=0, key="sub_color",
                label_visibility="visible"
            )
            subtitle_style["fontcolor"] = _color_map[_color_sel]

            # Posición vertical — slider de 0% (arriba) a 92% (abajo)
            _y_pct = st.slider(
                ("Posición vertical (0 = arriba · 85 = abajo)" if _is_es
                 else "Vertical position (0 = top · 85 = bottom)"),
                min_value=0, max_value=92, value=78, step=1, key="sub_y_pct"
            )
            subtitle_style["y"] = f"h*{_y_pct/100:.2f}"

            # Borde
            _outline = st.slider(
                "Borde (grosor)" if _is_es else "Outline (thickness)",
                min_value=0, max_value=6, value=3, key="sub_outline"
            )
            subtitle_style["borderw"] = _outline

            # Fondo
            _bg = st.toggle(
                "Fondo semitransparente" if _is_es else "Semi-transparent background",
                value=False, key="sub_bg"
            )
            subtitle_style["box"]      = 1 if _bg else 0
            subtitle_style["boxcolor"] = "black@0.45"

            # Palabras por línea
            _wrap = st.slider(
                "Palabras por línea" if _is_es else "Words per line",
                min_value=10, max_value=36, value=22, step=2, key="sub_wrap"
            )
            subtitle_style["max_chars"] = _wrap

# ── Selector de modo (grid 2×N de botones) ───────────────────────────────────

_mode_buttons = (
    [
        ("auto",       "⚡ Auto"),
        ("category",   "🗂️ Categorías"),
        ("viral",      "🔥 Viral"),
        ("testimonio", "👁️ Misterio"),
        ("libro",      "📚 Libro"),
        ("empleo",     "💼 Empleo"),
        ("guion",      "✍️ Guión"),
    ]
    if lang_option == "es"
    else [
        ("auto",       "⚡ Auto"),
        ("category",   "🗂️ Category"),
        ("viral",      "🔥 Viral"),
        ("testimonio", "👁️ Mystery"),
        ("libro",      "📚 Book"),
        ("empleo",     "💼 Job Ad"),
        ("guion",      "✍️ Script"),
    ]
)

st.markdown(
    f"<p class='section-label'>{'Modo de generación' if lang_option == 'es' else 'Generation mode'}</p>",
    unsafe_allow_html=True,
)

_cur_mode = st.session_state.get("generation_mode", "auto")

def _set_mode(new_mode: str):
    if st.session_state.get("generation_mode") != new_mode:
        st.session_state.generation_mode  = new_mode
        st.session_state.topic_suggestions = []
        st.session_state.selected_topic    = ""
        st.session_state.hook_step         = "idle"
        st.session_state.hook_options      = []
        st.session_state.chosen_hook       = ""

for _i in range(0, len(_mode_buttons), 2):
    _col1, _col2 = st.columns(2, gap="small")
    _mk1, _ml1 = _mode_buttons[_i]
    with _col1:
        st.button(
            _ml1, key=f"mdbtn_{_mk1}",
            type="primary" if _cur_mode == _mk1 else "secondary",
            use_container_width=True,
            on_click=_set_mode, args=(_mk1,),
        )
    if _i + 1 < len(_mode_buttons):
        _mk2, _ml2 = _mode_buttons[_i + 1]
        with _col2:
            st.button(
                _ml2, key=f"mdbtn_{_mk2}",
                type="primary" if _cur_mode == _mk2 else "secondary",
                use_container_width=True,
                on_click=_set_mode, args=(_mk2,),
            )

mode = st.session_state.get("generation_mode", "auto")

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

    num_scenes     = st.slider(T["scenes_label"], min_value=5, max_value=12, value=9)
    final_topic    = manual_topic_auto.strip()
    final_category = ""

# ══════════════════════════════════════════════════════════════════════════════
# MODO POR CATEGORÍA
# ══════════════════════════════════════════════════════════════════════════════

elif mode == "category":

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

    num_scenes     = st.slider(T["scenes_label"], min_value=5, max_value=12, value=9)
    final_category = selected_category
    final_topic    = st.session_state.get("manual_topic_input", "").strip() or st.session_state.get("selected_topic", "").strip()

# ══════════════════════════════════════════════════════════════════════════════
# MODO MÁS VIRALES
# ══════════════════════════════════════════════════════════════════════════════

elif mode == "viral":

    st.markdown(f"<div class='auto-info'>{T['viral_mode_info']}</div>", unsafe_allow_html=True)

    st.markdown(f"<div class='step-header'>🎯 {T['viral_category']}</div>", unsafe_allow_html=True)
    _viral_cats = VIRAL_CATEGORIES if lang_option == "es" else VIRAL_CATEGORIES_EN
    viral_category = st.selectbox(
        "vcat", options=[""] + _viral_cats,
        format_func=lambda x: T["category_placeholder"] if x == "" else x,
        label_visibility="collapsed",
        key="viral_cat_select",
    )

    st.markdown(f"<div class='step-header'>✍️ {T['viral_topic']}</div>", unsafe_allow_html=True)
    viral_topic_input = st.text_input(
        "vtopic",
        key="viral_topic_input",
        placeholder=T["viral_topic_ph"],
        label_visibility="collapsed",
    )

    final_topic   = viral_topic_input.strip()
    final_category = viral_category
    num_scenes    = 9  # no usado en modo viral, la IA decide

# ══════════════════════════════════════════════════════════════════════════════
# MODO TESTIMONIO MISTERIOSO
# ══════════════════════════════════════════════════════════════════════════════

elif mode == "testimonio":

    st.markdown(f"<div class='auto-info'>{T['testimonio_info']}</div>", unsafe_allow_html=True)

    st.markdown(f"<div class='step-header'>🎯 {T['testimonio_cat']}</div>", unsafe_allow_html=True)
    _test_cats = TESTIMONIO_CATEGORIES if lang_option == "es" else TESTIMONIO_CATEGORIES_EN
    test_category = st.selectbox(
        "tcat", options=[""] + _test_cats,
        format_func=lambda x: T["category_placeholder"] if x == "" else x,
        label_visibility="collapsed",
        key="test_cat_select",
    )

    st.markdown(f"<div class='step-header'>✍️ {T['testimonio_topic']}</div>", unsafe_allow_html=True)
    test_topic_input = st.text_input(
        "ttopic",
        key="test_topic_input",
        placeholder=T["testimonio_topic_ph"],
        label_visibility="collapsed",
    )

    final_topic    = test_topic_input.strip()
    final_category = test_category
    num_scenes     = 9

# ══════════════════════════════════════════════════════════════════════════════
# MODO RESUMEN DE LIBRO
# ══════════════════════════════════════════════════════════════════════════════

elif mode == "libro":

    st.markdown(f"<div class='auto-info'>{T['libro_info']}</div>", unsafe_allow_html=True)

    _book_cats = BOOK_CATEGORIES if lang_option == "es" else BOOK_CATEGORIES_EN
    st.markdown(f"<div class='step-header'>📖 {T['libro_cat']}</div>", unsafe_allow_html=True)
    libro_category = st.selectbox(
        "lcat", options=[""] + _book_cats,
        format_func=lambda x: T["category_placeholder"] if x == "" else x,
        label_visibility="collapsed",
        key="libro_cat_select",
    )

    st.markdown(f"<div class='step-header'>✍️ {T['libro_topic']}</div>", unsafe_allow_html=True)
    libro_topic_input = st.text_input(
        "ltopic",
        key="libro_topic_input",
        placeholder=T["libro_topic_ph"],
        label_visibility="collapsed",
    )

    final_topic    = libro_topic_input.strip()
    final_category = libro_category
    num_scenes     = 9

# ══════════════════════════════════════════════════════════════════════════════
# MODO OFERTA DE EMPLEO
# ══════════════════════════════════════════════════════════════════════════════

elif mode == "empleo":

    st.markdown(f"<div class='auto-info'>{T['empleo_info']}</div>", unsafe_allow_html=True)

    st.markdown(f"<div class='step-header'>📋 {T['empleo_label']}</div>", unsafe_allow_html=True)
    job_offer_raw = st.text_area(
        "job_offer",
        key="job_offer_input",
        placeholder=T["empleo_ph"],
        height=260,
        label_visibility="collapsed",
    )

    if job_offer_raw.strip():
        # Use first non-empty line as short topic label (for filename/copy)
        _first_line = next((l.strip() for l in job_offer_raw.splitlines() if l.strip()), "")
        final_topic = _first_line[:60]
    else:
        final_topic = ""

    final_category = ""
    num_scenes     = 9

# ══════════════════════════════════════════════════════════════════════════════
# MODO GUIÓN LIBRE
# ══════════════════════════════════════════════════════════════════════════════

elif mode == "guion":

    st.markdown(f"<div class='auto-info'>{T['guion_info']}</div>", unsafe_allow_html=True)

    st.markdown(f"<div class='step-header'>✍️ {T['guion_label']}</div>", unsafe_allow_html=True)
    guion_raw = st.text_area(
        "guion_text",
        key="guion_raw_input",
        placeholder=T["guion_ph"],
        height=280,
        label_visibility="collapsed",
    )

    if guion_raw.strip():
        _first_guion_line = next((l.strip() for l in guion_raw.splitlines() if l.strip()), "")
        final_topic = _first_guion_line[:60]
    else:
        final_topic = ""

    final_category = ""
    num_scenes     = 9

# ── Generar / Hook flow ───────────────────────────────────────────────────────
# Modos donde el hook se inyecta en la Escena 1 del guion
_HOOK_MODES = {"auto", "category", "viral", "testimonio", "libro"}
# "empleo" y "guion" no usan hooks — el texto ya viene definido por el usuario

st.markdown("---")

def _launch_pipeline():
    """Inicia el pipeline en un thread y hace rerun."""
    st.session_state.running   = True
    st.session_state.status    = "running"
    st.session_state.log_lines = []
    st.session_state.log_queue = queue.Queue()
    _wh_enabled = st.session_state.get("webhook_enabled", False)
    _wh_url = st.session_state.get("webhook_url_input", "").strip() if _wh_enabled else ""
    params = {
        "topic": final_topic, "num_scenes": num_scenes,
        "voice": selected_voice, "rate": rate_str,
        "use_avatar": use_avatar, "use_subtitles": use_subtitles,
        "subtitle_style": subtitle_style,
        "lang": lang_option, "mode": mode,
        "category": final_category,
        "webhook_url": _wh_url,
        "chosen_hook": st.session_state.get("chosen_hook", ""),
        "job_offer_text": st.session_state.get("job_offer_input", ""),
        "guion_raw_text": st.session_state.get("guion_raw_input", ""),
        "tts_engine":      st.session_state.get("tts_engine", "edge_tts"),
        "vox_voice_desc":  st.session_state.get("vox_voice_desc", ""),
        "vox_mood_enabled": st.session_state.get("vox_mood_enabled", True),
        "vox_clone_ref":   st.session_state.get("vox_clone_ref", ""),
    }
    t = threading.Thread(target=run_pipeline, args=(st.session_state.log_queue, params), daemon=True)
    st.session_state.thread = t
    t.start()
    st.rerun()

_hook_step = st.session_state.get("hook_step", "idle")

# ── PASO 1: botón principal de generación ────────────────────────────────────
if _hook_step == "idle":
    st.markdown("<div class='generate-btn'>", unsafe_allow_html=True)
    generate_clicked = st.button(T["generate_btn"],
        disabled=st.session_state.running or not config_ok,
        type="primary", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    if not config_ok:
        st.info(T["config_info"])

    if generate_clicked and not st.session_state.running:
        # Validación modo empleo
        if mode == "empleo" and not st.session_state.get("job_offer_input", "").strip():
            st.warning(T["empleo_warning"])

        # Validación modo guion
        elif mode == "guion" and not st.session_state.get("guion_raw_input", "").strip():
            st.warning(T["guion_warning"])

        # Modos con hook: resolver tema → descripción → hooks
        elif mode in _HOOK_MODES:
            _ht = final_topic or st.session_state.get("selected_topic", "")
            _hc = final_category or ""
            _is_es_hook = lang_option == "es"
            try:
                from modules.brain import ContentBrain as _HB
                _brain_h = _HB()

                # Paso 1: resolver tema + descripción
                with st.spinner("🎯 " + ("Resolviendo tema del video..." if _is_es_hook else "Resolving video topic...")):
                    _td = _brain_h.get_topic_and_description(_ht, _hc, mode, lang_option)
                    _resolved_topic = _td["topic"]
                    _topic_desc     = _td["description"]
                    st.session_state["_pending_topic"]      = _resolved_topic
                    st.session_state["_pending_topic_desc"] = _topic_desc
                    st.session_state["_pending_category"]   = _hc
                    st.session_state["_pending_scenes"]     = num_scenes

                # Paso 2: generar ganchos
                with st.spinner("🎣 " + ("Generando opciones de gancho..." if _is_es_hook else "Generating hook options...")):
                    _hooks = _brain_h.get_hook_options(_resolved_topic, _hc, mode, lang_option, n=3)
                    st.session_state["hook_options"] = _hooks
                    st.session_state["chosen_hook"]  = ""
                    st.session_state["hook_step"]    = "selecting"

            except Exception as _he:
                _msg = str(_he)
                if "NotFound" in _msg or "404" in _msg or "model" in _msg.lower():
                    st.error("❌ Modelo de IA no encontrado. Verifica **AI_MODEL** en los Secrets de Streamlit Cloud.")
                elif "auth" in _msg.lower() or "401" in _msg or "403" in _msg:
                    st.error("❌ Clave de API inválida. Verifica **AI_API_KEY** en los Secrets.")
                else:
                    st.error(f"❌ Error: {_msg[:200]}")
            st.rerun()

        # Modos sin hook: lanzar directamente
        else:
            _launch_pipeline()

# ── PASO 2: selección de hook ────────────────────────────────────────────────
elif _hook_step == "selecting":
    _is_es = lang_option == "es"

    # ── Tarjeta del tema resuelto ─────────────────────────────────────────────
    _show_topic = st.session_state.get("_pending_topic", "") or final_topic
    _show_desc  = st.session_state.get("_pending_topic_desc", "")
    if _show_topic:
        st.markdown(
            f"<div style='background:#f0f4ff;border:1px solid #c7d2fe;border-left:4px solid #6366f1;"
            f"border-radius:8px;padding:12px 16px;margin-bottom:14px;'>"
            f"<div style='font-size:0.75rem;font-weight:700;color:#6366f1;text-transform:uppercase;"
            f"letter-spacing:.06em;margin-bottom:4px;'>{'🎯 Tema del video' if _is_es else '🎯 Video topic'}</div>"
            f"<div style='font-size:1rem;font-weight:700;color:#1e1b4b;margin-bottom:{'6px' if _show_desc else '0'};'>{_show_topic}</div>"
            + (f"<div style='font-size:0.83rem;color:#4b5563;line-height:1.45;'>{_show_desc}</div>" if _show_desc else "")
            + "</div>",
            unsafe_allow_html=True,
        )

    st.markdown(f"### 🎣 {'Elige el gancho para tu video' if _is_es else 'Pick your video hook'}")
    st.caption(
        "El gancho es la primera frase — los primeros 2 segundos que deciden si el espectador sigue viendo o hace scroll. "
        "Elige el que más impacte para tu tema."
        if _is_es else
        "The hook is the first sentence — the 2 seconds that decide whether the viewer stays or scrolls away. "
        "Pick the one that hits hardest for your topic."
    )

    _hook_opts = st.session_state.get("hook_options", [])
    _chosen    = st.session_state.get("chosen_hook", "")
    _types_es  = ["A — Número shockeante", "B — Controversia", "C — Curiosidad", "D — Pregunta trampa"]
    _types_en  = ["A — Shocking number",   "B — Controversy",  "C — Curiosity",  "D — Trap question"]
    _type_lbls = _types_es if _is_es else _types_en

    for _hi, _hk in enumerate(_hook_opts):
        _is_chosen = (_chosen == _hk)
        _lbl = _type_lbls[_hi] if _hi < len(_type_lbls) else f"Opción {_hi+1}"
        st.markdown(f"**{_lbl}**")
        if st.button(
            f"{'✓ ' if _is_chosen else ''}{_hk}",
            key=f"hook_sel_{_hi}",
            type="primary" if _is_chosen else "secondary",
            use_container_width=True,
        ):
            st.session_state["chosen_hook"] = _hk
            st.rerun()

    st.markdown("")
    _col_a, _col_b = st.columns(2)
    with _col_a:
        if st.button("↩ " + ("Cambiar tema" if _is_es else "Change topic"),
                     use_container_width=True, type="secondary", key="hook_back"):
            st.session_state["hook_step"]    = "idle"
            st.session_state["hook_options"] = []
            st.session_state["chosen_hook"]  = ""
            st.rerun()
    with _col_b:
        _can_confirm = bool(_chosen) and not st.session_state.running
        if st.button(
            "🎬 " + ("Producir video" if _is_es else "Produce video"),
            disabled=not _can_confirm,
            type="primary", use_container_width=True, key="hook_confirm"
        ):
            # Leer hook elegido ANTES de limpiar
            _chosen_hook_val = st.session_state.get("chosen_hook", "")

            # Limpiar estado de hooks para que no queden en pantalla
            st.session_state["hook_step"]            = "idle"
            st.session_state["hook_options"]         = []
            st.session_state["chosen_hook"]          = ""
            st.session_state["_pending_topic_desc"]  = ""

            # Restaurar contexto guardado
            _ft = st.session_state.pop("_pending_topic", final_topic)
            _fc = st.session_state.pop("_pending_category", final_category)
            _fn = st.session_state.pop("_pending_scenes", num_scenes)

            st.session_state.running   = True
            st.session_state.status    = "running"
            st.session_state.log_lines = []
            st.session_state.log_queue = queue.Queue()
            _wh_enabled = st.session_state.get("webhook_enabled", False)
            _wh_url = st.session_state.get("webhook_url_input", "").strip() if _wh_enabled else ""
            _params = {
                "topic": _ft, "num_scenes": _fn,
                "voice": selected_voice, "rate": rate_str,
                "use_avatar": use_avatar, "use_subtitles": use_subtitles,
                "subtitle_style": subtitle_style,
                "lang": lang_option, "mode": mode,
                "category": _fc,
                "webhook_url": _wh_url,
                "chosen_hook": _chosen_hook_val,
                "job_offer_text": st.session_state.get("job_offer_input", ""),
                "tts_engine":      st.session_state.get("tts_engine", "edge_tts"),
                "vox_voice_desc":  st.session_state.get("vox_voice_desc", ""),
                "vox_mood_enabled": st.session_state.get("vox_mood_enabled", True),
                "vox_clone_ref":   st.session_state.get("vox_clone_ref", ""),
            }
            _t = threading.Thread(target=run_pipeline, args=(st.session_state.log_queue, _params), daemon=True)
            st.session_state.thread = _t
            _t.start()
            st.rerun()

    if not _chosen:
        st.info("Selecciona uno de los ganchos arriba para continuar." if _is_es else "Select one of the hooks above to continue.")

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
        elif line.startswith("TOPIC:"):
            st.session_state.video_topic = line[6:]

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
            _vid_topic = st.session_state.get("video_topic", "")
            _vid_fname = (re.sub(r'[^\w\s-]', '', _vid_topic).strip().replace(' ', '_')[:40] + ".mp4") if _vid_topic else "final_short.mp4"
            with open(FINAL_VIDEO_PATH, "rb") as f:
                st.download_button(label=T["download_mp4"], data=f,
                                   file_name=_vid_fname, mime="video/mp4",
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
            st.caption("Midjourney · DALL·E · Ideogram · Flux — " + (
                "Usa el ícono 📋 de la esquina para copiar" if lang_option == "es"
                else "Use the 📋 icon in the corner to copy"
            ))
            st.code(thumb, language=None)
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
