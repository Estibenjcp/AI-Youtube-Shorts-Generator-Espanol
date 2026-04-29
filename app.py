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
import modules.topic_history as _topic_history
from modules.categories import (
    TOPIC_CATEGORIES_ES, TOPIC_CATEGORIES_EN,
    VIRAL_CATEGORIES, VIRAL_CATEGORIES_EN,
    TESTIMONIO_CATEGORIES, TESTIMONIO_CATEGORIES_EN,
    BOOK_CATEGORIES, BOOK_CATEGORIES_EN,
    BIBLE_CATEGORIES, BIBLE_CATEGORIES_EN,
    MISTERIO_BIBLICO_CATEGORIES, MISTERIO_BIBLICO_CATEGORIES_EN,
)
from dotenv import set_key, load_dotenv

# ── Page config ──────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="AutoShorts AI",
    page_icon="🎬",
    layout="centered",
    initial_sidebar_state="expanded",
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
#MainMenu, footer,
[data-testid="stDecoration"],
[data-testid="stStatusWidget"],
[data-testid="stToolbar"],
.viewerBadge_container__1QSob { display: none !important; }
/* Ocultar deploy/share button pero NO el toggle del sidebar */
[data-testid="stAppDeployButton"] { display: none !important; }

/* ── FORZAR VISIBLE el nav automático de páginas ── */
[data-testid="stSidebarNav"],
[data-testid="stSidebarNavItems"],
[data-testid="stSidebarNavLink"],
section[data-testid="stSidebarNav"] {
    display: block !important;
    visibility: visible !important;
    height: auto !important;
    max-height: none !important;
    overflow: visible !important;
    opacity: 1 !important;
}

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

/* ── SIDEBAR — forzar visible en Streamlit 1.44+ ── */
[data-testid="stSidebar"] {
    background: var(--surface) !important;
    border-right: 1px solid var(--border) !important;
    box-shadow: var(--shadow-sm) !important;
    overflow-y: auto !important;
    overflow-x: hidden !important;
    display: block !important;
    visibility: visible !important;
    opacity: 1 !important;
    transform: translateX(0) !important;
    min-width: 280px !important;
    width: 280px !important;
}
[data-testid="stSidebar"] > div:first-child {
    padding: 1.25rem 0.875rem 3rem !important;
    min-height: 100vh;
}
/* Mostrar botón de colapso/expand del sidebar */
[data-testid="collapsedControl"],
[data-testid="stSidebarCollapseButton"] {
    display: flex !important;
    visibility: visible !important;
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
        "misterio_biblico_info":     "📖 Secretos oscuros y misterios poco conocidos de la Biblia — tono cinematográfico y revelador. 3 clips por escena.",
        "misterio_biblico_cat":      "Categoría del misterio",
        "misterio_biblico_topic":    "Tema (opcional — déjalo vacío para que la IA elija)",
        "misterio_biblico_topic_ph": "ej. Los Nefilim del Génesis y su verdadera naturaleza...",
        "libro_info":        "📚 Resumen de 60 seg que enseña, aplica y motiva a leer el libro. Tono inspirador y educativo.",
        "libro_cat":         "Género del libro",
        "libro_topic":       "Título del libro (opcional — déjalo vacío para que la IA elija)",
        "libro_topic_ph":    "ej. Hábitos Atómicos — James Clear...",
        "biblia_info":       "✝️ Reflexiones bíblicas de 60 seg que inspiran, edifican y tocan el corazón. Tono espiritual y esperanzador.",
        "biblia_cat":        "Categoría espiritual",
        "biblia_topic":      "Versículo o tema bíblico (opcional — déjalo vacío para que la IA elija)",
        "biblia_topic_ph":   "ej. Juan 3:16 — Fe y amor de Dios...",
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
        "misterio_biblico_info":     "📖 Dark secrets and little-known biblical mysteries — cinematic and revealing tone. 3 clips per scene.",
        "misterio_biblico_cat":      "Mystery category",
        "misterio_biblico_topic":    "Topic (optional — leave blank for AI to choose)",
        "misterio_biblico_topic_ph": "e.g. The Nephilim in Genesis and their true nature...",
        "libro_info":        "📚 60-sec summary that teaches, applies and motivates reading. Inspiring and educational tone.",
        "libro_cat":         "Book genre",
        "libro_topic":       "Book title (optional — leave blank for AI to choose)",
        "libro_topic_ph":    "e.g. Atomic Habits — James Clear...",
        "biblia_info":       "✝️ 60-sec biblical reflections that inspire, uplift and touch the heart. Spiritual and hopeful tone.",
        "biblia_cat":        "Spiritual category",
        "biblia_topic":      "Verse or biblical theme (optional — leave blank for AI to choose)",
        "biblia_topic_ph":   "e.g. John 3:16 — Faith and God's love...",
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
    ("libro_used_books",        []),    # libros ya sugeridos — evita repetición
    ("biblia_used_topics",      []),   # temas bíblicos ya sugeridos — evita repetición
    ("recommended_voice_label",  ""),  # label de la voz sugerida por IA
    ("recommended_voice_value",  ""),  # valor real de la voz (string o JSON de tuple)
    ("recommended_voice_engine", ""),  # engine al que pertenece la voz recomendada
    ("rec_voice_preview_path",   ""),  # ruta del audio preview de la voz recomendada
    # ── Subtítulos ──
    ("use_subtitles",    False),
    ("sub_position",     "bottom"),
    ("sub_fontsize",     44),
    ("sub_fontcolor",    "#FFFFFF"),
    ("sub_borderw",      3),
    ("sub_bordercolor",  "#000000"),
    ("sub_box",              False),
    ("sub_boxcolor",         "#000000"),
    ("sub_box_opacity",      0.4),
    ("sub_max_chars",        28),
    ("sub_highlight",        False),
    ("sub_highlight_color",  "#FFD700"),
    ("sub_highlight_fontcolor", "#000000"),
    # ── Duración y estructura ──
    ("target_total_secs",   60),
    ("global_num_scenes",    9),
    # ── Efectos visuales ──
    ("fx_ken_burns",        False),
    ("fx_color_grade",      True),
    ("fx_progress_bar",     False),
    ("fx_progress_bar_color", "#FFFFFF"),
    ("fx_hook_card",        False),
    ("fx_hook_text",        ""),
    ("fx_hook_duration",    2.5),
    # ── Música de fondo ──
    ("use_music",        False),
    ("music_volume",     15),
    ("music_fade_in",    1.0),
    ("music_fade_out",   2.0),
    ("music_loop",       True),
    ("music_file_path",  ""),
    # ──
    ("video_source",      "pexels"),   # "pexels" | "ai_video" | "ai_video_test"
    ("tts_engine",        "edge_tts"),
    ("vox_voice_desc",    ""),
    ("vox_mood_enabled",  True),
    ("ai_video_style",          "cinematic"),
    ("ai_video_total_duration", 30),
    ("ai_video_clip_duration",  5),
    ("ai_video_num_scenes",     6),
    ("novela_theme",            ""),
    ("gtts_rate",         1.0),
    ("gtts_pitch",        0.0),
    ("gtts_lang_code",    "es-US"),
    ("gtts_voice_name",   "es-US-Neural2-B"),
    ("gtts_voice_es",     "es-US-Neural2-B  (Masculino Latino ★)"),
    ("gtts_voice_en",     "en-US-Neural2-D  (Male, US ★)"),
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
        script = asyncio.run(audio_engine.process_script(script))

        log_q.put("STAGE:Assets")
        _video_src = params.get("video_source", "pexels")
        if _video_src in ("ai_video", "ai_video_test"):
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
            asset_manager = AssetManager()
            assets_map    = asset_manager.get_videos(script)

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
            p = os.path.join(os.path.dirname(__file__), "assets", folder)
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
    if "app_seccion" not in st.session_state:
        st.session_state["app_seccion"] = "generador"
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🎬 Generador", use_container_width=True, key="nav_gen"):
            st.session_state["app_seccion"] = "generador"
    with col2:
        if st.button("✨ Prompts", use_container_width=True, key="nav_pf"):
            st.session_state["app_seccion"] = "prompts_flow"
    st.divider()

# ── Si el usuario seleccionó Prompts Flow, mostrarlo y parar aquí ────────────
if st.session_state.get("app_seccion") == "prompts_flow":
    import streamlit.components.v1 as _components
    import pathlib as _pl
    import json as _json
    _pf_file = _pl.Path(__file__).parent / "pages" / "2_Prompts_Flow.py"
    _pf_src  = _pf_file.read_text(encoding="utf-8")
    _html_start = _pf_src.find('HTML = r"""') + len('HTML = r"""')
    _html_end   = _pf_src.rfind('"""')
    _html_block = _pf_src[_html_start:_html_end]
    # Inyectar la API key de OpenRouter del generador principal
    _cfg_pf = load_config()
    _injected_key = ""
    if _cfg_pf.get("AI_PROVIDER") == "openrouter":
        _injected_key = _cfg_pf.get("AI_API_KEY", "")
    if _injected_key:
        _html_block = _html_block.replace(
            "let _orKey  = localStorage.getItem('or_key')   || '';",
            f"let _orKey  = localStorage.getItem('or_key') || {_json.dumps(_injected_key)};",
        )
    st.markdown("## ✨ Prompts Flow / Veo 3")
    _components.html(_html_block, height=2400, scrolling=True)
    st.stop()

# ── A partir de aquí: lógica normal del Generador ───────────────────────────
with st.sidebar:
    st.caption("Configuración de API" if lang_option == "es" else "API Settings")

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
        pexels_key  = st.text_input(T["pexels_key"], value=cfg["PEXELS_API_KEY"], type="password")
        google_tts_key = st.text_input(
            "🔵 Google TTS API Key",
            value=os.getenv("GOOGLE_TTS_KEY", ""),
            type="password",
            placeholder="AIza... (opcional)",
            help=(
                "Solo si usas Google TTS como motor de voz. Obtén la clave en console.cloud.google.com"
                if lang_option == "es" else
                "Only needed if using Google TTS as voice engine. Get it at console.cloud.google.com"
            ),
        )
        st.markdown("---")
        st.caption("🎬 " + ("Generación de Video con IA (opcional)" if lang_option == "es" else "AI Video Generation (optional)"))
        _vid_providers = ["fal", "kling", "runway", "luma", "pika", "otro"]
        _vid_provider_labels = {
            "fal":    "FAL.ai",
            "kling":  "Kling AI",
            "runway": "Runway ML",
            "luma":   "Luma Dream Machine",
            "pika":   "Pika Labs",
            "otro":   "Otro / Other",
        }
        ai_video_provider = st.selectbox(
            "Proveedor de Video IA" if lang_option == "es" else "AI Video Provider",
            options=_vid_providers,
            index=_vid_providers.index(os.getenv("AI_VIDEO_PROVIDER", "fal"))
                  if os.getenv("AI_VIDEO_PROVIDER", "fal") in _vid_providers else 0,
            format_func=lambda x: _vid_provider_labels.get(x, x),
        )
        ai_video_key = st.text_input(
            "API Key de Video IA" if lang_option == "es" else "AI Video API Key",
            value=os.getenv("AI_VIDEO_KEY", ""),
            type="password",
            placeholder="sk-... / fal-... (opcional)",
        )
        ai_video_model = st.text_input(
            "Modelo de Video" if lang_option == "es" else "Video Model",
            value=os.getenv("AI_VIDEO_MODEL", ""),
            placeholder="ej. fal-ai/kling-video/v2.6/pro/text-to-video",
            help=(
                "ID del modelo. Déjalo vacío para usar el modelo por defecto del proveedor."
                if lang_option == "es" else
                "Model ID. Leave blank to use the provider's default model."
            ),
        )
        api_saved  = st.form_submit_button(T["save_api"], use_container_width=True)

    if api_saved:
        set_key(ENV_PATH, "AI_PROVIDER",    provider)
        set_key(ENV_PATH, "AI_API_KEY",     ai_key)
        set_key(ENV_PATH, "AI_MODEL",       model)
        set_key(ENV_PATH, "PEXELS_API_KEY", pexels_key)
        if google_tts_key:
            set_key(ENV_PATH, "GOOGLE_TTS_KEY", google_tts_key)
        set_key(ENV_PATH, "AI_VIDEO_PROVIDER", ai_video_provider)
        if ai_video_key:
            set_key(ENV_PATH, "AI_VIDEO_KEY",  ai_video_key)
        set_key(ENV_PATH, "AI_VIDEO_MODEL",    ai_video_model)
        load_dotenv(ENV_PATH, override=True)
        st.success(T["api_saved"])

    # ── Diagnóstico de Conexiones ─────────────────────────
    st.divider()
    _is_es_diag = lang_option == "es"
    with st.expander(
        "🔧 " + ("Diagnóstico de conexiones" if _is_es_diag else "Connection diagnostics"),
        expanded=False,
    ):
        st.caption(
            "Prueba cada servicio con una petición real sin generar contenido."
            if _is_es_diag else
            "Test each service with a real request without generating content."
        )

        # ── helper: fila de servicio ─────────────────────────
        def _diag_row(icon, label, detail, key, btn_disabled=False):
            """Renderiza una fila horizontal: icono+label+detalle | botón"""
            _ra, _rb = st.columns([3, 1])
            with _ra:
                st.markdown(
                    f"<div style='display:flex;align-items:center;gap:8px;padding:4px 0'>"
                    f"<span style='font-size:1.2rem'>{icon}</span>"
                    f"<div><span style='font-weight:700;font-size:0.85rem'>{label}</span>"
                    f"<br><span style='font-size:0.72rem;color:#6b7280'>{detail}</span></div>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
            with _rb:
                clicked = st.button(
                    "🔌 " + ("Probar" if _is_es_diag else "Test"),
                    key=key,
                    use_container_width=True,
                    disabled=btn_disabled,
                )
            result_slot = st.empty()
            return clicked, result_slot

        # ──────────────── LLM ────────────────────────────
        _diag_llm_key   = os.getenv("AI_API_KEY", "")
        _diag_llm_model = os.getenv("AI_MODEL", "") or "gemini-2.0-flash-exp"
        _diag_llm_prov  = os.getenv("AI_PROVIDER", "gemini").lower()
        _diag_llm_btn, _diag_llm_out = _diag_row(
            "🧠", "LLM", f"{_diag_llm_prov} · {_diag_llm_model[:24]}",
            "diag_llm_btn", btn_disabled=not _diag_llm_key,
        )
        if _diag_llm_btn:
            with st.spinner("Consultando LLM..."):
                try:
                    if _diag_llm_prov == "openrouter":
                        from openai import OpenAI as _OAI
                        _oc = _OAI(base_url="https://openrouter.ai/api/v1", api_key=_diag_llm_key)
                        _or = _oc.chat.completions.create(
                            model=_diag_llm_model,
                            messages=[{"role": "user", "content": "Reply with the single word: OK"}],
                            max_tokens=8,
                        )
                        _ans = _or.choices[0].message.content.strip()
                    else:
                        from google import genai as _gai
                        _gc = _gai.Client(api_key=_diag_llm_key)
                        _gr2 = _gc.models.generate_content(model=_diag_llm_model, contents="Reply with the single word: OK")
                        _ans = _gr2.text.strip()
                    _diag_llm_out.success(f"✅ Conectado · respuesta: {_ans[:20]}")
                except Exception as _de:
                    _diag_llm_out.error(f"❌ {str(_de)[:80]}")

        # ──────────────── Video IA ───────────────────────
        _diag_vid_key  = os.getenv("AI_VIDEO_KEY", "")
        _diag_vid_prov = os.getenv("AI_VIDEO_PROVIDER", "fal").lower()
        _diag_vid_mdl  = os.getenv("AI_VIDEO_MODEL", "") or "fal-ai/kling-video/v2.6/pro/text-to-video"
        _diag_vid_btn, _diag_vid_out = _diag_row(
            "🎬", "Video IA", f"{_diag_vid_prov.upper()} · {_diag_vid_mdl[:26]}",
            "diag_vid_btn", btn_disabled=not _diag_vid_key,
        )
        if _diag_vid_btn:
            with st.spinner("Enviando petición de prueba..."):
                try:
                    import requests as _rq_v
                    if _diag_vid_prov == "kling":
                        # Kling direct: GET a endpoint inexistente — 404 = auth OK
                        _vh = {"Authorization": f"Bearer {_diag_vid_key}", "Content-Type": "application/json"}
                        _vr = _rq_v.get("https://api.klingai.com/v1/videos/text2video/__diag__", headers=_vh, timeout=12)
                        if _vr.status_code in (200, 404, 400):
                            _diag_vid_out.success(f"✅ Auth OK (HTTP {_vr.status_code})")
                        elif _vr.status_code in (401, 403):
                            _diag_vid_out.error(f"❌ Key inválida (HTTP {_vr.status_code})")
                        else:
                            _diag_vid_out.warning(f"⚠️ HTTP {_vr.status_code}")
                    else:
                        # FAL: GET con request_id falso — 404 = auth OK, 401/403 = key inválida
                        # Esta técnica NO genera ningún job ni consume créditos.
                        _vh = {"Authorization": f"Key {_diag_vid_key}"}
                        _fake_id = "diag-test-000000000000"
                        _vr = _rq_v.get(
                            f"https://queue.fal.run/{_diag_vid_mdl}/requests/{_fake_id}/status",
                            headers=_vh, timeout=12,
                        )
                        _http = _vr.status_code
                        try:
                            _body = _vr.json()
                            _detail = _body.get("detail") or _body.get("message") or _body.get("error") or ""
                        except Exception:
                            _detail = _vr.text[:120]

                        if _http in (200, 404, 422):
                            # 404 = key válida pero request no existe (esperado)
                            _diag_vid_out.success(
                                f"✅ Key válida · modelo accesible  "
                                f"(HTTP {_http} — sin créditos gastados)\n"
                                f"Para verificar el clip real usa **🧪 Test IA**"
                            )
                        elif _http in (401, 403):
                            _hint = ""
                            if "credit" in str(_detail).lower() or "quota" in str(_detail).lower():
                                _hint = " — Sin créditos o cuota agotada"
                            elif "model" in str(_detail).lower() or "access" in str(_detail).lower():
                                _hint = " — Modelo no disponible en tu plan"
                            elif "invalid" in str(_detail).lower() or "key" in str(_detail).lower():
                                _hint = " — API Key inválida"
                            else:
                                _hint = " — Revisa la key o el plan de FAL"
                            _diag_vid_out.error(f"❌ {_http} Forbidden{_hint}: {str(_detail)[:100]}")
                        else:
                            _diag_vid_out.warning(f"⚠️ HTTP {_http}: {str(_detail)[:80]}")
                except Exception as _de:
                    _diag_vid_out.error(f"❌ {str(_de)[:120]}")

        # ──────────────── Audio TTS ──────────────────────
        _diag_tts = st.session_state.get("tts_engine", "edge_tts")
        _diag_tts_label = {"edge_tts": "Edge TTS", "google_tts": "Google TTS", "voxcpm": "VoxCPM"}.get(_diag_tts, _diag_tts)
        _diag_tts_btn, _diag_tts_out = _diag_row(
            "🎙️", "Audio TTS", _diag_tts_label,
            "diag_tts_btn",
        )
        if _diag_tts_btn:
            with st.spinner("Probando síntesis..."):
                try:
                    import tempfile, os as _os2
                    _tmp = tempfile.mktemp(suffix=".mp3")
                    if _diag_tts == "edge_tts":
                        import edge_tts as _ett, asyncio as _aio2
                        _ev = st.session_state.get("voice", "es-MX-DaliaNeural")
                        async def _edge_diag():
                            c = _ett.Communicate("ok", _ev)
                            await c.save(_tmp)
                        _aio2.run(_edge_diag())
                        _size = _os2.path.getsize(_tmp) if _os2.path.exists(_tmp) else 0
                        _diag_tts_out.success("✅ Edge TTS OK") if _size > 100 else _diag_tts_out.error("❌ Audio vacío")
                    elif _diag_tts == "google_tts":
                        _gk = os.getenv("GOOGLE_TTS_KEY", "")
                        if not _gk:
                            _diag_tts_out.error("❌ Sin API Key de Google TTS")
                        else:
                            import requests as _rq_t
                            _tr = _rq_t.post(
                                "https://texttospeech.googleapis.com/v1/text:synthesize",
                                params={"key": _gk},
                                json={"input": {"text": "ok"}, "voice": {"languageCode": "es-US", "name": "es-US-Neural2-B"}, "audioConfig": {"audioEncoding": "MP3"}},
                                timeout=10,
                            )
                            if _tr.status_code == 200:
                                _diag_tts_out.success("✅ Google TTS OK")
                            else:
                                _em = _tr.json().get("error", {}).get("message", str(_tr.status_code))
                                _diag_tts_out.error(f"❌ {_em[:70]}")
                    elif _diag_tts == "voxcpm":
                        try:
                            from modelscope.pipelines import pipeline as _ms_pipe  # noqa
                            _diag_tts_out.success("✅ VoxCPM disponible")
                        except ImportError:
                            _diag_tts_out.error("❌ modelscope no instalado")
                    if _os2.path.exists(_tmp):
                        _os2.remove(_tmp)
                except Exception as _de:
                    _diag_tts_out.error(f"❌ {str(_de)[:80]}")

        # ──────────────── Pexels ─────────────────────────
        _diag_px_key = os.getenv("PEXELS_API_KEY", "")
        _diag_px_btn, _diag_px_out = _diag_row(
            "📷", "Pexels", "configurada ✓" if _diag_px_key else "sin configurar",
            "diag_px_btn", btn_disabled=not _diag_px_key,
        )
        if _diag_px_btn:
            with st.spinner("..."):
                try:
                    import requests as _rq_px
                    _pr = _rq_px.get(
                        "https://api.pexels.com/videos/search",
                        params={"query": "nature", "per_page": 1},
                        headers={"Authorization": _diag_px_key},
                        timeout=10,
                    )
                    if _pr.status_code == 200:
                        _total = _pr.json().get("total_results", "?")
                        _diag_px_out.success(f"✅ Pexels OK · {_total} resultados")
                    else:
                        _diag_px_out.error(f"❌ Error {_pr.status_code}")
                except Exception as _de:
                    _diag_px_out.error(f"❌ {str(_de)[:60]}")

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
        "AI_PROVIDER":       cfg["AI_PROVIDER"],
        "AI_API_KEY":        cfg["AI_API_KEY"],
        "AI_MODEL":          cfg["AI_MODEL"],
        "PEXELS_API_KEY":    cfg["PEXELS_API_KEY"],
        "GOOGLE_TTS_KEY":    os.getenv("GOOGLE_TTS_KEY", ""),
        "AI_VIDEO_PROVIDER": os.getenv("AI_VIDEO_PROVIDER", ""),
        "AI_VIDEO_KEY":      os.getenv("AI_VIDEO_KEY", ""),
        "AI_VIDEO_MODEL":    os.getenv("AI_VIDEO_MODEL", ""),
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
            if imported.get("GOOGLE_TTS_KEY"):
                set_key(ENV_PATH, "GOOGLE_TTS_KEY",    imported.get("GOOGLE_TTS_KEY", ""))
            if imported.get("AI_VIDEO_PROVIDER"):
                set_key(ENV_PATH, "AI_VIDEO_PROVIDER", imported.get("AI_VIDEO_PROVIDER", ""))
            if imported.get("AI_VIDEO_KEY"):
                set_key(ENV_PATH, "AI_VIDEO_KEY",      imported.get("AI_VIDEO_KEY", ""))
            if imported.get("AI_VIDEO_MODEL"):
                set_key(ENV_PATH, "AI_VIDEO_MODEL",    imported.get("AI_VIDEO_MODEL", ""))
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

# ── Barra superior: fuente de video + idioma ──────────────────────────────────
_cur_vsrc  = st.session_state.get("video_source", "pexels")
_has_ai_vid = bool(os.getenv("AI_VIDEO_KEY", ""))

_top_left, _top_right = st.columns([3, 1])

with _top_left:
    T = UI[lang_option]
    st.markdown(
        f"<div class='hero-title'>{T['page_title']}</div>"
        f"<p class='hero-sub'>{T['page_caption']}</p>",
        unsafe_allow_html=True,
    )

with _top_right:
    # ── Toggle de idioma ──────────────────────────────────────────────────
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

# ── Selector de fuente de video (3 opciones) ─────────────────────────────────
_vs_label = "🎬 Fuente de video" if lang_option == "es" else "🎬 Video source"
st.caption(_vs_label)
_vsrc_c1, _vsrc_c2, _vsrc_c3 = st.columns(3, gap="small")

_vsrc_pexels_active  = (_cur_vsrc == "pexels")
_vsrc_ai_active      = (_cur_vsrc == "ai_video")
_vsrc_test_active    = (_cur_vsrc == "ai_video_test")
_ai_vid_provider     = os.getenv("AI_VIDEO_PROVIDER", "fal").upper()

def _vsrc_card(active):
    return {
        "bg":     "#6366f1" if active else "#f3f4f6",
        "color":  "#fff"    if active else "#374151",
        "weight": "700"     if active else "500",
        "border": "#6366f1" if active else "#e5e7eb",
        "op":     "1"       if active else "0.6",
    }

# Card 1 — Pexels
with _vsrc_c1:
    _s = _vsrc_card(_vsrc_pexels_active)
    st.markdown(
        f"""<div style="background:{_s['bg']};color:{_s['color']};border-radius:10px;
            padding:10px 8px;text-align:center;font-size:0.83rem;font-weight:{_s['weight']};
            border:2px solid {_s['border']};line-height:1.3;">
            🎥 Pexels<br>
            <span style="font-size:0.7rem;opacity:{_s['op']}">
            {'Stock video' if lang_option == 'en' else 'Stock video'}
            </span></div>""",
        unsafe_allow_html=True,
    )
    if st.button("✓" if _vsrc_pexels_active else ("Elegir" if lang_option == "es" else "Select"),
                 key="vsrc_pexels_btn", use_container_width=True,
                 type="primary" if _vsrc_pexels_active else "secondary"):
        st.session_state["video_source"] = "pexels"
        st.rerun()

# Card 2 — AI Video
with _vsrc_c2:
    _s = _vsrc_card(_vsrc_ai_active)
    _ai_sub = f"{_ai_vid_provider} · {'listo' if _has_ai_vid else 'config →'}" \
              if lang_option == "es" else \
              f"{_ai_vid_provider} · {'ready' if _has_ai_vid else 'set API →'}"
    st.markdown(
        f"""<div style="background:{_s['bg']};color:{_s['color']};border-radius:10px;
            padding:10px 8px;text-align:center;font-size:0.83rem;font-weight:{_s['weight']};
            border:2px solid {_s['border']};line-height:1.3;">
            🤖 {'Video IA' if lang_option == 'es' else 'AI Video'}<br>
            <span style="font-size:0.7rem;opacity:{_s['op']}">{_ai_sub}</span>
            </div>""",
        unsafe_allow_html=True,
    )
    if st.button("✓" if _vsrc_ai_active else ("Elegir" if lang_option == "es" else "Select"),
                 key="vsrc_ai_btn", use_container_width=True,
                 type="primary" if _vsrc_ai_active else "secondary"):
        st.session_state["video_source"] = "ai_video"
        st.rerun()

# Card 3 — Test IA (1 escena / 5s)
with _vsrc_c3:
    _s = _vsrc_card(_vsrc_test_active)
    # override: test card uses amber when active
    if _vsrc_test_active:
        _s["bg"] = "#ca8a04"; _s["border"] = "#ca8a04"
    st.markdown(
        f"""<div style="background:{_s['bg']};color:{_s['color']};border-radius:10px;
            padding:10px 8px;text-align:center;font-size:0.83rem;font-weight:{_s['weight']};
            border:2px solid {_s['border']};line-height:1.3;">
            🧪 Test IA<br>
            <span style="font-size:0.7rem;opacity:{_s['op']}">
            {'1 clip · verifica modelo' if lang_option == 'es' else '1 clip · verify model'}
            </span></div>""",
        unsafe_allow_html=True,
    )
    if st.button("✓" if _vsrc_test_active else ("Elegir" if lang_option == "es" else "Select"),
                 key="vsrc_test_btn", use_container_width=True,
                 type="primary" if _vsrc_test_active else "secondary"):
        st.session_state["video_source"] = "ai_video_test"
        st.rerun()

# Info banners bajo las tarjetas
if (_vsrc_ai_active or _vsrc_test_active) and not _has_ai_vid:
    st.warning("⚠️ " + ("Configura tu API Key de Video IA en el panel lateral."
               if lang_option == "es" else "Set your AI Video API Key in the sidebar."))
elif _vsrc_ai_active and _has_ai_vid:
    _ai_model_display = os.getenv("AI_VIDEO_MODEL", "") or "fal-ai/kling-video/v2.6/pro/text-to-video"
    st.info(f"🤖 **{_ai_vid_provider}** — `{_ai_model_display}`")
elif _vsrc_test_active and _has_ai_vid:
    _ai_model_display = os.getenv("AI_VIDEO_MODEL", "") or "fal-ai/kling-video/v2.6/pro/text-to-video"
    st.warning(
        f"🧪 **Test Mode** — genera **1 escena de 5s** con `{_ai_model_display}`. "
        + ("Verifica que el clip llegue correcto antes de producir el video completo."
           if lang_option == "es" else
           "Verify the clip arrives correctly before producing the full video.")
    )

st.divider()

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

# Aplicar voz recomendada pendiente ANTES de que el selectbox se dibuje
_pending_vs = st.session_state.pop("_next_voice_select", None)
if _pending_vs:
    st.session_state["voice_select"] = _pending_vs

# ── Estilo de Video IA (visible si video_source es ai_video o ai_video_test) ──
if st.session_state.get("video_source", "pexels") in ("ai_video", "ai_video_test"):
    from modules.ai_video import VIDEO_STYLES
    _vs_exp_label = "🎨 Estilo de Video IA" if lang_option == "es" else "🎨 AI Video Style"
    with st.expander(_vs_exp_label, expanded=False):
        _style_keys = list(VIDEO_STYLES.keys())
        _style_labels_map = {k: (v["label"] if lang_option == "es" else v["label_en"]) for k, v in VIDEO_STYLES.items()}
        _cur_style = st.session_state.get("ai_video_style", "cinematic")
        _style_cols = st.columns(2, gap="small")
        for _sci, _sk in enumerate(_style_keys):
            with _style_cols[_sci % 2]:
                _sactive = (_cur_style == _sk)
                st.markdown(
                    f"""<div style="background:{'#6366f1' if _sactive else '#f3f4f6'};
                    color:{'#fff' if _sactive else '#374151'};border-radius:8px;
                    padding:8px;text-align:center;font-size:0.8rem;
                    font-weight:{'700' if _sactive else '500'};
                    border:2px solid {'#6366f1' if _sactive else '#e5e7eb'};
                    margin-bottom:4px">{_style_labels_map[_sk]}</div>""",
                    unsafe_allow_html=True,
                )
                if st.button("✓" if _sactive else ("Elegir" if lang_option == "es" else "Select"),
                             key=f"vstyle_{_sk}", use_container_width=True,
                             type="primary" if _sactive else "secondary"):
                    st.session_state["ai_video_style"] = _sk
                    st.rerun()
        st.caption(
            f"🎬 Estilo activo: **{_style_labels_map.get(_cur_style, _cur_style)}** · {VIDEO_STYLES.get(_cur_style, {}).get('suffix', '')[:60]}..."
            if lang_option == "es" else
            f"🎬 Active style: **{_style_labels_map.get(_cur_style, _cur_style)}** · {VIDEO_STYLES.get(_cur_style, {}).get('suffix', '')[:60]}..."
        )

        # ── Duración del video y cortes ───────────────────────────────────
        st.markdown("---")
        st.markdown(
            "**⏱️ Duración y estructura del video**" if lang_option == "es"
            else "**⏱️ Video duration & structure**"
        )

        _dur_c1, _dur_c2 = st.columns(2, gap="medium")

        with _dur_c1:
            # Duración total deseada
            _total_options = [15, 30, 45, 60, 90]
            _cur_total = st.session_state.get("ai_video_total_duration", 30)
            ai_video_total = st.select_slider(
                "Duración total" if lang_option == "es" else "Total duration",
                options=_total_options,
                value=_cur_total if _cur_total in _total_options else 30,
                format_func=lambda x: f"{x}s",
                key="ai_video_total_slider",
            )
            st.session_state["ai_video_total_duration"] = ai_video_total

        with _dur_c2:
            # Duración por clip (lo que pide al modelo)
            # Detectar duraciones soportadas por el modelo configurado
            _active_vid_model = os.getenv("AI_VIDEO_MODEL", "") or "fal-ai/kling-video/v2.6/pro/text-to-video"
            try:
                from modules.ai_video import _MODEL_DURATIONS as _MVD
                _clip_options = sorted(_MVD.get(_active_vid_model, [5, 10]))
            except Exception:
                _clip_options = [5, 10]
            _cur_clip = st.session_state.get("ai_video_clip_duration", 5)
            ai_video_clip = st.select_slider(
                "Duración por clip" if lang_option == "es" else "Clip duration",
                options=_clip_options,
                value=_cur_clip if _cur_clip in _clip_options else 5,
                format_func=lambda x: f"{x}s",
                key="ai_video_clip_slider",
                help=(
                    "Duración que solicitas al modelo de IA por cada clip."
                    if lang_option == "es" else
                    "Duration requested from the AI model per clip."
                ),
            )
            st.session_state["ai_video_clip_duration"] = ai_video_clip

        # Cálculo automático de escenas
        _computed_scenes = max(1, round(ai_video_total / ai_video_clip))
        st.session_state["ai_video_num_scenes"] = _computed_scenes

        st.markdown(
            f"""<div style="background:#ede9fe;border-radius:10px;padding:12px 16px;
            text-align:center;margin-top:4px">
            <span style="font-size:1.1rem;font-weight:700;color:#5b21b6">
            {ai_video_total}s ÷ {ai_video_clip}s = <span style="font-size:1.4rem">{_computed_scenes}</span> escenas
            </span><br>
            <span style="font-size:0.75rem;color:#7c3aed">
            {'El guión se adaptará a ' if lang_option == 'es' else 'Script will adapt to '}
            {_computed_scenes} {'escenas de' if lang_option == 'es' else 'scenes of'} {ai_video_clip}s
            {'cada una' if lang_option == 'es' else 'each'}
            </span></div>""",
            unsafe_allow_html=True,
        )
        st.caption(
            "💡 FFmpeg recorta cada clip al largo exacto del audio TTS — el tiempo total real puede variar ±2s."
            if lang_option == "es" else
            "💡 FFmpeg trims each clip to the exact TTS audio length — actual total may vary ±2s."
        )

        st.caption(
            "💡 " + ("Para probar el modelo sin gastar créditos, selecciona '🧪 Test IA' en la fuente de video."
                     if lang_option == "es" else
                     "To test the model without spending credits, select '🧪 Test IA' as video source.")
        )

# ── Expander: Duración y escenas ─────────────────────────────────────────────
_dur_label = "📐 Duración y escenas" if lang_option == "es" else "📐 Duration & scenes"
with st.expander(_dur_label, expanded=False):
    _dur_opts   = [15, 30, 45, 60, 90, 120, 150, 180]
    _dur_labels = {15: "15s", 30: "30s", 45: "45s", 60: "1 min",
                   90: "1:30 min", 120: "2 min", 150: "2:30 min", 180: "3 min"}
    _cur_dur = st.session_state.get("target_total_secs", 60)
    if _cur_dur not in _dur_opts:
        _cur_dur = 60
    target_total_secs = st.select_slider(
        "⏱️ " + ("Duración total del video" if lang_option == "es" else "Total video duration"),
        options=_dur_opts,
        value=_cur_dur,
        format_func=lambda v: _dur_labels[v],
        key="target_total_secs",
    )
    global_num_scenes = st.slider(
        "🎬 " + ("Número de escenas" if lang_option == "es" else "Number of scenes"),
        min_value=2, max_value=15,
        value=st.session_state.get("global_num_scenes", 9),
        key="global_num_scenes",
    )
    _wps = round(target_total_secs / global_num_scenes * 2.3)
    st.caption(
        f"≈ {round(target_total_secs / global_num_scenes, 1)}s por escena · "
        f"≈ {_wps} palabras por escena · "
        f"≈ {round(target_total_secs / 60, 1)} min total"
        if lang_option == "es" else
        f"≈ {round(target_total_secs / global_num_scenes, 1)}s per scene · "
        f"≈ {_wps} words per scene · "
        f"≈ {round(target_total_secs / 60, 1)} min total"
    )

# ── Efectos visuales ─────────────────────────────────────────────────────────
_fx_label = "🎬 Efectos visuales" if lang_option == "es" else "🎬 Visual effects"
with st.expander(_fx_label, expanded=False):
    # ── Hook card ────────────────────────────────────────────────────────────
    _hkc1, _hkc2 = st.columns([1, 3])
    with _hkc1:
        st.toggle(
            "Hook card" if lang_option == "es" else "Hook card",
            value=st.session_state.get("fx_hook_card", False),
            key="fx_hook_card",
            help=("Muestra texto grande al inicio del video para enganchar al espectador."
                  if lang_option == "es" else
                  "Shows large text at video start to hook the viewer."),
        )
    with _hkc2:
        st.text_input(
            "Texto" if lang_option == "es" else "Text",
            value=st.session_state.get("fx_hook_text", ""),
            key="fx_hook_text",
            max_chars=60,
            placeholder="Ej: Lo que nadie te contó sobre esto..." if lang_option == "es" else "E.g.: What nobody told you about this...",
            disabled=not st.session_state.get("fx_hook_card", False),
            help=("Deja vacío para usar la primera oración del guion automáticamente."
                  if lang_option == "es" else
                  "Leave blank to auto-use the first sentence of the script."),
        )
    st.divider()
    # ── Otros efectos ────────────────────────────────────────────────────────
    col_fx1, col_fx2 = st.columns(2)
    with col_fx1:
        st.toggle(
            "🎥 Ken Burns (zoom/pan)" if lang_option == "es" else "🎥 Ken Burns (zoom/pan)",
            value=st.session_state.get("fx_ken_burns", False),
            key="fx_ken_burns",
            help=("Aplica un zoom o paneo suave a cada clip de stock. "
                  "Hace el video más dinámico. Aumenta el tiempo de render."
                  if lang_option == "es" else
                  "Applies a slow zoom or pan to each stock clip. "
                  "Makes the video feel more alive. Increases render time."),
        )
        st.toggle(
            "🎨 Color grading automático" if lang_option == "es" else "🎨 Auto color grading",
            value=st.session_state.get("fx_color_grade", True),
            key="fx_color_grade",
            help=("Ajusta saturación, contraste y brillo según el modo del video: "
                  "bíblico=cálido, viral=vibrante, misterio=oscuro y frío."
                  if lang_option == "es" else
                  "Adjusts saturation, contrast and brightness based on the video mode."),
        )
    with col_fx2:
        st.toggle(
            "📊 Barra de progreso" if lang_option == "es" else "📊 Progress bar",
            value=st.session_state.get("fx_progress_bar", False),
            key="fx_progress_bar",
            help=("Muestra una barra delgada en la parte superior que avanza "
                  "mientras el video progresa. Aumenta retención."
                  if lang_option == "es" else
                  "Shows a thin bar at the top that fills as the video plays. Boosts retention."),
        )
        if st.session_state.get("fx_progress_bar", False):
            st.color_picker(
                "Color barra" if lang_option == "es" else "Bar color",
                value=st.session_state.get("fx_progress_bar_color", "#FFFFFF"),
                key="fx_progress_bar_color",
            )


# ── Historial de temas usados ─────────────────────────────────────────────────
_hist_stats  = _topic_history.get_stats()
_hist_total  = _hist_stats["total"]
_hist_lang   = _hist_stats.get("es" if lang_option == "es" else "en", 0)
_hist_label  = (
    f"📋 Historial de temas ({_hist_total} generados)"
    if lang_option == "es" else
    f"📋 Topic history ({_hist_total} generated)"
)
with st.expander(_hist_label, expanded=False):
    if _hist_total == 0:
        st.caption(
            "Aún no hay temas registrados. Cada video generado se guardará aquí automáticamente."
            if lang_option == "es" else
            "No topics recorded yet. Every generated video will be saved here automatically."
        )
    else:
        _c1, _c2 = st.columns(2)
        with _c1:
            st.metric(
                "🌐 " + ("Total" if lang_option == "es" else "Total"),
                _hist_total,
            )
        with _c2:
            st.metric(
                ("🌍 Este idioma" if lang_option == "es" else "🌍 This language"),
                _hist_lang,
            )
        st.caption(
            "El LLM recibe esta lista automáticamente y tiene PROHIBIDO repetir esos temas."
            if lang_option == "es" else
            "The LLM receives this list automatically and is FORBIDDEN from repeating those topics."
        )
        _hcol1, _hcol2 = st.columns(2)
        with _hcol1:
            if st.button(
                ("🗑️ Borrar todo" if lang_option == "es" else "🗑️ Clear all"),
                use_container_width=True,
            ):
                _topic_history.clear_history()
                st.rerun()
        with _hcol2:
            if st.button(
                (f"🗑️ Borrar solo {'ES' if lang_option == 'es' else 'EN'}"
                 if lang_option == "es" else
                 f"🗑️ Clear only {'ES' if lang_option == 'es' else 'EN'}"),
                use_container_width=True,
            ):
                _topic_history.clear_history(lang=lang_option)
                st.rerun()

voice_label_hint = "🎙️ Voz y velocidad" if lang_option == "es" else "🎙️ Voice & speed"
with st.expander(voice_label_hint, expanded=False):

    # ── Motor TTS — botones en cuadrícula (responsive, sin corte en móvil) ──
    _tts_buttons = [
        ("edge_tts",   "☁️ Edge TTS",    "Nube · rápido"    if lang_option == "es" else "Cloud · fast"),
        ("google_tts", "🔵 Google TTS",  "Neural2 / Studio"),
        ("voxcpm",     "🤖 VoxCPM 2B",   "Local · GPU"),
    ]
    _cur_tts = st.session_state.get("tts_engine", "edge_tts")

    st.caption("Motor TTS" if lang_option == "es" else "TTS Engine")
    _tc1, _tc2, _tc3 = st.columns(3, gap="small")
    for _col, (_key, _label, _sub) in zip([_tc1, _tc2, _tc3], _tts_buttons):
        _active = (_cur_tts == _key)
        with _col:
            st.markdown(
                f"""<div style="
                    background:{'#6366f1' if _active else '#f3f4f6'};
                    color:{'#fff' if _active else '#374151'};
                    border-radius:10px;
                    padding:10px 6px;
                    text-align:center;
                    font-size:0.82rem;
                    font-weight:{'700' if _active else '500'};
                    border:2px solid {'#6366f1' if _active else '#e5e7eb'};
                    line-height:1.3;
                    cursor:pointer;
                ">
                {_label}<br>
                <span style="font-size:0.7rem;opacity:{'1' if _active else '0.65'}">{_sub}</span>
                </div>""",
                unsafe_allow_html=True,
            )
            if st.button("✓" if _active else "Seleccionar" if lang_option == "es" else "Select",
                         key=f"tts_btn_{_key}",
                         use_container_width=True,
                         type="primary" if _active else "secondary"):
                st.session_state["tts_engine"] = _key
                st.rerun()

    tts_engine = st.session_state.get("tts_engine", "edge_tts")

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

    elif tts_engine == "google_tts":
        # ── Google TTS controls ───────────────────────────────────────────
        selected_voice = ""   # not used by Google TTS
        rate_str       = "+0%"

        from modules.audio import GoogleTTSAudioEngine as _GTTS

        # API key leída del .env (se guarda en Configuración de API → sidebar)
        gtts_api_key = os.getenv("GOOGLE_TTS_KEY", "")

        # ── Two-column layout: left = API status + test  |  right = voice settings ──
        _gl, _gr = st.columns([3, 2], gap="medium")

        with _gl:
            if gtts_api_key:
                st.success("✅ API Key configurada" if lang_option == "es" else "✅ API Key configured")
            else:
                st.warning(
                    "⚠️ API Key no configurada. Agrégala en **Configuración de API** (panel izquierdo)."
                    if lang_option == "es" else
                    "⚠️ API Key not set. Add it in **API Settings** (left panel)."
                )

            # API Test button + status
            _atc1, _atc2 = st.columns([1, 2])
            with _atc1:
                _api_test_btn = st.button(
                    "🔍 Probar API" if lang_option == "es" else "🔍 Test API",
                    disabled=not bool(gtts_api_key),
                    use_container_width=True,
                    key="gtts_test_api_btn",
                )
            with _atc2:
                _api_status = st.empty()

            if _api_test_btn and gtts_api_key:
                with st.spinner("Verificando..." if lang_option == "es" else "Verifying..."):
                    try:
                        import requests as _req_test
                        _tr = _req_test.post(
                            _GTTS._URL,
                            params={"key": gtts_api_key},
                            headers={"Referer": "https://digency.streamlit.app/"},
                            json={
                                "input": {"text": "ok"},
                                "voice": {"languageCode": "es-US", "name": "es-US-Neural2-B"},
                                "audioConfig": {"audioEncoding": "MP3"},
                            },
                            timeout=10,
                        )
                        if _tr.status_code == 200:
                            _api_status.success("✅ API válida" if lang_option == "es" else "✅ API valid")
                        else:
                            _err_msg = _tr.json().get("error", {}).get("message", str(_tr.status_code))
                            _api_status.error(f"❌ {_err_msg}")
                    except Exception as _te:
                        _api_status.error(f"❌ {_te}")

            st.caption(
                "💡 **Neural2**: 1M chars/mes gratis · **Studio**: 100K chars/mes gratis"
                if lang_option == "es" else
                "💡 **Neural2**: 1M chars/month free · **Studio**: 100K chars/month free"
            )

        with _gr:
            # Voice selection
            _gv_map = _GTTS.VOICES_ES if lang_option == "es" else _GTTS.VOICES_EN
            _gv_opts = list(_gv_map.keys())
            _gv_default_key = "gtts_voice_es" if lang_option == "es" else "gtts_voice_en"
            # Apply pending recommended Google TTS voice BEFORE selectbox renders
            _pending_gtts_vs = st.session_state.pop("_next_gtts_voice_select", None)
            if _pending_gtts_vs and _pending_gtts_vs in _gv_opts:
                st.session_state["gtts_voice_select"] = _pending_gtts_vs
                st.session_state[_gv_default_key] = _pending_gtts_vs
            _gv_saved = st.session_state.get(_gv_default_key, _gv_opts[0])
            _gv_idx   = _gv_opts.index(_gv_saved) if _gv_saved in _gv_opts else 0
            gtts_voice_label = st.selectbox(
                "Voz" if lang_option == "es" else "Voice",
                options=_gv_opts,
                index=_gv_idx,
                key="gtts_voice_select",
            )
            st.session_state[_gv_default_key] = gtts_voice_label
            _gtts_lang_code, _gtts_voice_name = _gv_map[gtts_voice_label]
            st.session_state["gtts_lang_code"]  = _gtts_lang_code
            st.session_state["gtts_voice_name"] = _gtts_voice_name

            gtts_rate = st.slider(
                "Velocidad" if lang_option == "es" else "Rate",
                min_value=0.5, max_value=2.0,
                value=st.session_state.get("gtts_rate", 1.0),
                step=0.05, format="%.2f×",
                key="gtts_rate_slider",
            )
            st.session_state["gtts_rate"] = gtts_rate

            gtts_pitch = st.slider(
                "Tono" if lang_option == "es" else "Pitch",
                min_value=-10.0, max_value=10.0,
                value=st.session_state.get("gtts_pitch", 0.0),
                step=0.5, format="%.1f st",
                key="gtts_pitch_slider",
            )
            st.session_state["gtts_pitch"] = gtts_pitch

            # Preview current voice (synchronous — REST call is ~1-2s)
            _prev_btn = st.button(
                "▶ Previsualizar" if lang_option == "es" else "▶ Preview",
                use_container_width=True,
                disabled=not bool(gtts_api_key),
                key="gtts_preview_btn",
            )
            if _prev_btn and gtts_api_key:
                _prev_txt_g = (
                    "Hola, esta es mi voz de Google. Perfecta para narrar tu video."
                    if lang_option == "es" else
                    "Hello, this is my Google voice. Perfect for narrating your video."
                )
                _prev_path_g = os.path.join(os.path.dirname(__file__), "assets", "temp", "gtts_preview.mp3")
                os.makedirs(os.path.dirname(_prev_path_g), exist_ok=True)
                with st.spinner("Generando..." if lang_option == "es" else "Generating..."):
                    try:
                        _peng = _GTTS(api_key=gtts_api_key, voice_name=_gtts_voice_name,
                                      lang_code=_gtts_lang_code, speaking_rate=gtts_rate,
                                      pitch=gtts_pitch)
                        _peng._synthesize(_prev_txt_g, _prev_path_g)
                    except Exception as _pe:
                        st.error(str(_pe))
                if os.path.exists(_prev_path_g) and os.path.getsize(_prev_path_g) > 500:
                    st.audio(_prev_path_g, format="audio/mp3")

        # ── Voice Explorer ────────────────────────────────────────────────
        st.markdown("<br>", unsafe_allow_html=True)
        with st.expander(
            "🎧 Explorador de Voces — prueba cada voz" if lang_option == "es"
            else "🎧 Voice Explorer — try each voice",
            expanded=False,
        ):
            _exp_map  = _GTTS.VOICES_ES if lang_option == "es" else _GTTS.VOICES_EN
            _exp_text = (
                "Este es un ejemplo de cómo suena esta voz. ¿Te gusta para tu video?"
                if lang_option == "es" else
                "This is a sample of how this voice sounds. Is it good for your video?"
            )
            if not gtts_api_key:
                st.warning(
                    "Ingresa tu API Key arriba para probar las voces."
                    if lang_option == "es" else
                    "Enter your API Key above to test voices."
                )
            else:
                st.caption(
                    "Haz clic en ▶ para escuchar cada voz. La voz activa está marcada con ✓"
                    if lang_option == "es" else
                    "Click ▶ to hear each voice. The active voice is marked with ✓"
                )
                for _ve_label, (_ve_lang, _ve_name) in _exp_map.items():
                    _ve_c1, _ve_c2 = st.columns([5, 1])
                    with _ve_c1:
                        _is_active = (_ve_name == _gtts_voice_name)
                        st.markdown(
                            f"{'**✓** ' if _is_active else ''}`{_ve_name}` · _{_ve_lang}_"
                        )
                    with _ve_c2:
                        _ve_btn = st.button(
                            "▶",
                            key=f"ve_{_ve_name}",
                            use_container_width=True,
                        )
                    if _ve_btn:
                        _ve_out = os.path.join(
                            os.path.dirname(__file__), "assets", "temp", f"ve_{_ve_name}.mp3"
                        )
                        os.makedirs(os.path.dirname(_ve_out), exist_ok=True)
                        with st.spinner(f"{_ve_name}..."):
                            try:
                                _ve_eng = _GTTS(
                                    api_key=gtts_api_key, voice_name=_ve_name,
                                    lang_code=_ve_lang, speaking_rate=gtts_rate, pitch=0.0,
                                )
                                _ve_eng._synthesize(_exp_text, _ve_out)
                                st.audio(_ve_out, format="audio/mp3")
                            except Exception as _vee:
                                st.error(str(_vee))

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

# ── Expander: Subtítulos ──────────────────────────────────────────────────────
def _hex_to_ffmpeg(h: str) -> str:
    return "0x" + h.lstrip("#").upper()

_sub_label = "💬 Subtítulos" if lang_option == "es" else "💬 Subtitles"
with st.expander(_sub_label, expanded=False):
    use_subtitles = st.toggle(
        "Activar subtítulos" if lang_option == "es" else "Enable subtitles",
        value=st.session_state.get("use_subtitles", False),
        key="use_subtitles",
    )
    if use_subtitles:
        _sc1, _sc2 = st.columns(2)
        with _sc1:
            _sub_pos = st.select_slider(
                "📍 " + ("Posición" if lang_option == "es" else "Position"),
                options=["top", "center", "bottom"],
                value=st.session_state.get("sub_position", "bottom"),
                key="sub_position",
            )
            _sub_fs = st.slider(
                "🔤 " + ("Tamaño fuente" if lang_option == "es" else "Font size"),
                min_value=20, max_value=72, step=2,
                value=st.session_state.get("sub_fontsize", 44),
                key="sub_fontsize",
            )
            _sub_mc = st.slider(
                "📏 " + ("Chars por línea" if lang_option == "es" else "Chars per line"),
                min_value=15, max_value=45, step=1,
                value=st.session_state.get("sub_max_chars", 28),
                key="sub_max_chars",
            )
        with _sc2:
            _sub_fc = st.color_picker(
                "🎨 " + ("Color texto" if lang_option == "es" else "Text color"),
                value=st.session_state.get("sub_fontcolor", "#FFFFFF"),
                key="sub_fontcolor",
            )
            _sub_bw = st.slider(
                "✏️ " + ("Borde (px)" if lang_option == "es" else "Border (px)"),
                min_value=0, max_value=8, step=1,
                value=st.session_state.get("sub_borderw", 3),
                key="sub_borderw",
            )
            _sub_bc = st.color_picker(
                "🖊️ " + ("Color borde" if lang_option == "es" else "Border color"),
                value=st.session_state.get("sub_bordercolor", "#000000"),
                key="sub_bordercolor",
            )
        # ── Highlight ──
        _sub_hl = st.toggle(
            "✨ " + ("Highlight (caja de color)" if lang_option == "es" else "Highlight box"),
            value=st.session_state.get("sub_highlight", False),
            key="sub_highlight",
        )
        if _sub_hl:
            _shl1, _shl2 = st.columns(2)
            with _shl1:
                _sub_hlc = st.color_picker(
                    "🎨 " + ("Color highlight" if lang_option == "es" else "Highlight color"),
                    value=st.session_state.get("sub_highlight_color", "#FFD700"),
                    key="sub_highlight_color",
                )
            with _shl2:
                _sub_hlfc = st.color_picker(
                    "🔤 " + ("Color texto (highlight)" if lang_option == "es" else "Text color (highlight)"),
                    value=st.session_state.get("sub_highlight_fontcolor", "#000000"),
                    key="sub_highlight_fontcolor",
                )
        else:
            _sub_hlc  = st.session_state.get("sub_highlight_color", "#FFD700")
            _sub_hlfc = st.session_state.get("sub_highlight_fontcolor", "#000000")

        _sub_box = st.toggle(
            "🟦 " + ("Fondo detrás del texto" if lang_option == "es" else "Background box"),
            value=st.session_state.get("sub_box", False),
            key="sub_box",
        )
        if _sub_box:
            _sbc1, _sbc2 = st.columns(2)
            with _sbc1:
                _sub_boxc = st.color_picker(
                    "Color fondo" if lang_option == "es" else "Box color",
                    value=st.session_state.get("sub_boxcolor", "#000000"),
                    key="sub_boxcolor",
                )
            with _sbc2:
                _sub_box_op = st.slider(
                    "Opacidad" if lang_option == "es" else "Opacity",
                    min_value=0.0, max_value=1.0, step=0.05,
                    value=st.session_state.get("sub_box_opacity", 0.4),
                    key="sub_box_opacity",
                )
        else:
            _sub_boxc   = st.session_state.get("sub_boxcolor", "#000000")
            _sub_box_op = st.session_state.get("sub_box_opacity", 0.4)

        _pos_map = {"top": "h*0.08", "center": "h*0.45", "bottom": "h*0.82"}
        subtitle_style = {
            "fontsize":             st.session_state.get("sub_fontsize", 44),
            "fontcolor":            _hex_to_ffmpeg(st.session_state.get("sub_fontcolor", "#FFFFFF")),
            "y":                    _pos_map.get(st.session_state.get("sub_position", "bottom"), "h*0.82"),
            "borderw":              st.session_state.get("sub_borderw", 3),
            "bordercolor":          _hex_to_ffmpeg(st.session_state.get("sub_bordercolor", "#000000")),
            "box":                  1 if st.session_state.get("sub_box", False) else 0,
            "boxcolor":             _hex_to_ffmpeg(st.session_state.get("sub_boxcolor", "#000000"))
                                    + f"@{st.session_state.get('sub_box_opacity', 0.4):.2f}",
            "max_chars":            st.session_state.get("sub_max_chars", 28),
            "highlight_color":      _hex_to_ffmpeg(_sub_hlc) if st.session_state.get("sub_highlight", False) else "",
            "highlight_opacity":    0.9,
            "highlight_fontcolor":  _sub_hlfc,
        }
    else:
        subtitle_style = {}

# ── Expander: Música de fondo ─────────────────────────────────────────────────
_mus_label = "🎵 Música de fondo" if lang_option == "es" else "🎵 Background music"
with st.expander(_mus_label, expanded=False):
    use_music = st.toggle(
        "Activar música de fondo" if lang_option == "es" else "Enable background music",
        value=st.session_state.get("use_music", False),
        key="use_music",
    )
    if use_music:
        _mu_file = st.file_uploader(
            "🎶 " + ("Archivo de música (MP3 / WAV / M4A)" if lang_option == "es" else "Music file (MP3 / WAV / M4A)"),
            type=["mp3", "wav", "m4a", "ogg"],
            key="music_uploader",
        )
        if _mu_file:
            _mu_save_dir = os.path.join(os.path.dirname(__file__), "assets", "temp")
            os.makedirs(_mu_save_dir, exist_ok=True)
            _mu_save_path = os.path.join(_mu_save_dir, "bgm_upload" + os.path.splitext(_mu_file.name)[1])
            with open(_mu_save_path, "wb") as _mf:
                _mf.write(_mu_file.read())
            st.session_state["music_file_path"] = _mu_save_path
            st.caption(f"✅ {_mu_file.name}")

        _mu1, _mu2 = st.columns(2)
        with _mu1:
            _mu_vol = st.slider(
                "🔊 " + ("Volumen música %" if lang_option == "es" else "Music volume %"),
                min_value=0, max_value=100, step=5,
                value=st.session_state.get("music_volume", 15),
                key="music_volume",
            )
            _mu_fi = st.slider(
                "⬆️ Fade in (s)",
                min_value=0.0, max_value=5.0, step=0.5,
                value=st.session_state.get("music_fade_in", 1.0),
                key="music_fade_in",
            )
        with _mu2:
            _mu_fo = st.slider(
                "⬇️ Fade out (s)",
                min_value=0.0, max_value=5.0, step=0.5,
                value=st.session_state.get("music_fade_out", 2.0),
                key="music_fade_out",
            )
            _mu_loop = st.toggle(
                "🔁 " + ("Repetir si es corta" if lang_option == "es" else "Loop if too short"),
                value=st.session_state.get("music_loop", True),
                key="music_loop",
            )
        if not st.session_state.get("music_file_path", ""):
            st.caption("⚠️ " + ("Sube un archivo de música para activar esta función." if lang_option == "es" else "Upload a music file to enable this feature."))

# ── Selector de modo (grid 2×N de botones) ───────────────────────────────────

_mode_buttons = (
    [
        ("auto",             "⚡ Auto"),
        ("category",         "🗂️ Categorías"),
        ("viral",            "🔥 Viral"),
        ("testimonio",       "👁️ Misterio"),
        ("misterio_biblico", "📖 Mist. Bíblico"),
        ("libro",            "📚 Libro"),
        ("biblia",           "✝️ Biblia"),
        ("empleo",           "💼 Empleo"),
        ("guion",            "✍️ Guión"),
        ("novela",           "🎬 Mininovela"),
        ("podcast",          "🎙️ Podcast"),
    ]
    if lang_option == "es"
    else [
        ("auto",             "⚡ Auto"),
        ("category",         "🗂️ Category"),
        ("viral",            "🔥 Viral"),
        ("testimonio",       "👁️ Mystery"),
        ("misterio_biblico", "📖 Bible Mystery"),
        ("libro",            "📚 Book"),
        ("biblia",           "✝️ Bible"),
        ("empleo",           "💼 Job Ad"),
        ("guion",            "✍️ Script"),
        ("novela",           "🎬 Miniseries"),
        ("podcast",          "🎙️ Podcast"),
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

    num_scenes     = st.session_state.get("global_num_scenes", 9)
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

    num_scenes     = st.session_state.get("global_num_scenes", 9)
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
    num_scenes    = st.session_state.get("global_num_scenes", 9)

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
    num_scenes     = st.session_state.get("global_num_scenes", 9)

# ══════════════════════════════════════════════════════════════════════════════
# MODO MISTERIO BÍBLICO
# ══════════════════════════════════════════════════════════════════════════════

elif mode == "misterio_biblico":

    st.markdown(f"<div class='auto-info'>{T['misterio_biblico_info']}</div>", unsafe_allow_html=True)

    st.markdown(f"<div class='step-header'>🎯 {T['misterio_biblico_cat']}</div>", unsafe_allow_html=True)
    _mb_cats = MISTERIO_BIBLICO_CATEGORIES if lang_option == "es" else MISTERIO_BIBLICO_CATEGORIES_EN
    mb_category = st.selectbox(
        "mbcat", options=[""] + _mb_cats,
        format_func=lambda x: T["category_placeholder"] if x == "" else x,
        label_visibility="collapsed",
        key="mb_cat_select",
    )

    st.markdown(f"<div class='step-header'>✍️ {T['misterio_biblico_topic']}</div>", unsafe_allow_html=True)
    mb_topic_input = st.text_input(
        "mbtopic",
        key="mb_topic_input",
        placeholder=T["misterio_biblico_topic_ph"],
        label_visibility="collapsed",
    )

    final_topic    = mb_topic_input.strip()
    final_category = mb_category
    num_scenes     = st.session_state.get("global_num_scenes", 9)

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
    num_scenes     = st.session_state.get("global_num_scenes", 9)

# ══════════════════════════════════════════════════════════════════════════════
# MODO BIBLIA
# ══════════════════════════════════════════════════════════════════════════════

elif mode == "biblia":

    st.markdown(f"<div class='auto-info'>{T['biblia_info']}</div>", unsafe_allow_html=True)

    _bible_cats = BIBLE_CATEGORIES if lang_option == "es" else BIBLE_CATEGORIES_EN
    st.markdown(f"<div class='step-header'>✝️ {T['biblia_cat']}</div>", unsafe_allow_html=True)
    biblia_category = st.selectbox(
        "bcat", options=[""] + _bible_cats,
        format_func=lambda x: T["category_placeholder"] if x == "" else x,
        label_visibility="collapsed",
        key="biblia_cat_select",
    )

    st.markdown(f"<div class='step-header'>✍️ {T['biblia_topic']}</div>", unsafe_allow_html=True)
    biblia_topic_input = st.text_input(
        "btopic",
        key="biblia_topic_input",
        placeholder=T["biblia_topic_ph"],
        label_visibility="collapsed",
    )

    final_topic    = biblia_topic_input.strip()
    final_category = biblia_category
    num_scenes     = st.session_state.get("global_num_scenes", 9)

# ══════════════════════════════════════════════════════════════════════════════
# MODO OFERTA DE EMPLEO
# ══════════════════════════════════════════════════════════════════════════════

elif mode == "empleo":

    st.markdown(f"<div class='auto-info'>{T['empleo_info']}</div>", unsafe_allow_html=True)

    # Badge fijo: 6 escenas / 30 seg / energético
    st.markdown(
        "<div style='display:flex;gap:8px;margin-bottom:12px'>"
        "<span style='background:#fef3c7;color:#92400e;padding:4px 10px;border-radius:20px;font-size:0.78rem;font-weight:600'>⚡ 6 escenas</span>"
        "<span style='background:#fef3c7;color:#92400e;padding:4px 10px;border-radius:20px;font-size:0.78rem;font-weight:600'>⏱️ ~30 segundos</span>"
        "<span style='background:#fef3c7;color:#92400e;padding:4px 10px;border-radius:20px;font-size:0.78rem;font-weight:600'>🔥 Estilo energético</span>"
        "</div>"
        if lang_option == "es" else
        "<div style='display:flex;gap:8px;margin-bottom:12px'>"
        "<span style='background:#fef3c7;color:#92400e;padding:4px 10px;border-radius:20px;font-size:0.78rem;font-weight:600'>⚡ 6 scenes</span>"
        "<span style='background:#fef3c7;color:#92400e;padding:4px 10px;border-radius:20px;font-size:0.78rem;font-weight:600'>⏱️ ~30 seconds</span>"
        "<span style='background:#fef3c7;color:#92400e;padding:4px 10px;border-radius:20px;font-size:0.78rem;font-weight:600'>🔥 Energetic style</span>"
        "</div>",
        unsafe_allow_html=True,
    )

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
    num_scenes     = 6   # fijo: 6 escenas ≈ 30 segundos, siempre energético

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
    num_scenes     = st.session_state.get("global_num_scenes", 9)

# ══════════════════════════════════════════════════════════════════════════════
# MODO MININOVELA (solo con AI Video)
# ══════════════════════════════════════════════════════════════════════════════

elif mode == "novela":
    _is_ai = st.session_state.get("video_source", "pexels") in ("ai_video", "ai_video_test")
    if not _is_ai:
        st.warning(
            "🎬 El modo Mininovela requiere **Video con IA** como fuente de video. "
            "Selecciona **🤖 Video con IA** arriba para activarlo."
            if lang_option == "es" else
            "🎬 Miniseries mode requires **AI Video** as video source. "
            "Select **🤖 AI Video** above to enable it."
        )
        final_topic    = ""
        final_category = ""
        num_scenes     = 8
    else:
        st.markdown(
            "<div class='auto-info'>"
            + ("🎬 Describe el tema de tu mini historia y la IA crea personajes, escenario, guión y video completo. Solo funciona con Video IA."
               if lang_option == "es" else
               "🎬 Describe your mini story theme and the AI creates characters, setting, full script and video. AI Video only.")
            + "</div>",
            unsafe_allow_html=True,
        )

        # Badges
        _nov_style = st.session_state.get("ai_video_style", "cinematic")
        st.markdown(
            "<div style='display:flex;gap:8px;margin-bottom:12px;flex-wrap:wrap'>"
            f"<span style='background:#ede9fe;color:#5b21b6;padding:4px 10px;border-radius:20px;font-size:0.78rem;font-weight:600'>🎬 8 escenas</span>"
            f"<span style='background:#ede9fe;color:#5b21b6;padding:4px 10px;border-radius:20px;font-size:0.78rem;font-weight:600'>⏱️ ~60-90 segundos</span>"
            f"<span style='background:#ede9fe;color:#5b21b6;padding:4px 10px;border-radius:20px;font-size:0.78rem;font-weight:600'>🤖 Video IA</span>"
            f"<span style='background:#ede9fe;color:#5b21b6;padding:4px 10px;border-radius:20px;font-size:0.78rem;font-weight:600'>🎨 {_nov_style.title()}</span>"
            "</div>",
            unsafe_allow_html=True,
        )

        st.markdown(
            f"<div class='step-header'>🎭 {'Tema o concepto de la historia' if lang_option == 'es' else 'Story theme or concept'}</div>",
            unsafe_allow_html=True,
        )
        novela_theme = st.text_area(
            "novela_theme_area",
            key="novela_theme_input",
            placeholder=(
                "ej. Una doctora descubre que su hospital oculta experimentos ilegales en pacientes comatosos..."
                if lang_option == "es" else
                "e.g. A doctor discovers her hospital is running illegal experiments on comatose patients..."
            ),
            height=120,
            label_visibility="collapsed",
        )

        final_topic    = novela_theme.strip()[:100] if novela_theme.strip() else ""
        final_category = ""
        num_scenes     = 8

# ══════════════════════════════════════════════════════════════════════════════
# MODO PODCAST / DIÁLOGO
# ══════════════════════════════════════════════════════════════════════════════

elif mode == "podcast":

    _pod_info = (
        "🎙️ Genera un corto estilo podcast con dos voces TTS alternando. Host y Invitado hablan de forma natural sobre el tema elegido."
        if lang_option == "es"
        else
        "🎙️ Generate a podcast-style Short with two alternating TTS voices. Host and Guest talk naturally about the chosen topic."
    )
    st.markdown(f"<div class='auto-info'>{_pod_info}</div>", unsafe_allow_html=True)

    podcast_topic = st.text_input(
        "Tema del episodio" if lang_option == "es" else "Episode topic",
        key="podcast_topic_input",
        placeholder=(
            "ej. Los secretos del sueño que nadie te cuenta"
            if lang_option == "es"
            else "e.g. The sleep secrets nobody tells you"
        ),
    )

    col_host, col_guest = st.columns(2)
    with col_host:
        st.markdown("**🎤 Host**")
        host_name = st.text_input(
            "Nombre del Host" if lang_option == "es" else "Host name",
            value="Carlos",
            key="podcast_host_name",
        )
        _voice_keys = list(VOICES.keys())
        _default_voice_key = T["default_voice"]
        _default_idx_a = _voice_keys.index(_default_voice_key) if _default_voice_key in _voice_keys else 0
        voice_a_label = st.selectbox(
            "Voz del Host" if lang_option == "es" else "Host voice",
            options=_voice_keys,
            index=_default_idx_a,
            key="podcast_voice_a",
        )
    with col_guest:
        st.markdown("**🎧 Invitado**" if lang_option == "es" else "**🎧 Guest**")
        guest_name = st.text_input(
            "Nombre del Invitado" if lang_option == "es" else "Guest name",
            value="Ana",
            key="podcast_guest_name",
        )
        _default_idx_b = 1 if len(_voice_keys) > 1 else 0
        voice_b_label = st.selectbox(
            "Voz del Invitado" if lang_option == "es" else "Guest voice",
            options=_voice_keys,
            index=_default_idx_b,
            key="podcast_voice_b",
        )

    num_exchanges = st.slider(
        "Número de intercambios" if lang_option == "es" else "Number of exchanges",
        min_value=4, max_value=12, value=6,
        key="podcast_num_exchanges",
    )

    final_topic    = podcast_topic.strip()
    final_category = ""
    num_scenes     = num_exchanges

# ── Generar / Hook flow ───────────────────────────────────────────────────────
# Modos donde el hook se inyecta en la Escena 1 del guion
_HOOK_MODES = {"auto", "category", "viral", "testimonio", "misterio_biblico", "libro", "biblia"}
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
        "use_avatar": use_avatar,
        "use_subtitles": use_subtitles,
        "subtitle_style": subtitle_style,
        "use_music":      st.session_state.get("use_music", False),
        "music_file_path":st.session_state.get("music_file_path", ""),
        "music_volume":   st.session_state.get("music_volume", 15) / 100.0,
        "music_fade_in":  st.session_state.get("music_fade_in", 1.0),
        "music_fade_out": st.session_state.get("music_fade_out", 2.0),
        "music_loop":     st.session_state.get("music_loop", True),
        "lang": lang_option, "mode": mode,
        "category": final_category,
        "webhook_url": _wh_url,
        "chosen_hook": st.session_state.get("chosen_hook", ""),
        "job_offer_text": st.session_state.get("job_offer_input", ""),
        "guion_raw_text": st.session_state.get("guion_raw_input", ""),
        "tts_engine":       st.session_state.get("tts_engine", "edge_tts"),
        "vox_voice_desc":   st.session_state.get("vox_voice_desc", ""),
        "vox_mood_enabled": st.session_state.get("vox_mood_enabled", True),
        "vox_clone_ref":    st.session_state.get("vox_clone_ref", ""),
        "gtts_api_key":     os.getenv("GOOGLE_TTS_KEY", ""),
        "gtts_voice_name":  st.session_state.get("gtts_voice_name", "es-US-Neural2-B"),
        "gtts_lang_code":   st.session_state.get("gtts_lang_code", "es-US"),
        "gtts_rate":        st.session_state.get("gtts_rate", 1.0),
        "gtts_pitch":       st.session_state.get("gtts_pitch", 0.0),
        "video_source":     st.session_state.get("video_source", "pexels"),
        "ai_video_provider":os.getenv("AI_VIDEO_PROVIDER", "fal"),
        "ai_video_key":     os.getenv("AI_VIDEO_KEY", ""),
        "ai_video_model":   os.getenv("AI_VIDEO_MODEL", ""),
        "ai_video_style":       st.session_state.get("ai_video_style", "cinematic"),
        "ai_video_num_scenes":  st.session_state.get("ai_video_num_scenes", 6),
        "ai_video_clip_duration": st.session_state.get("ai_video_clip_duration", 5),
        "target_total_secs":    st.session_state.get("target_total_secs", 60),
        # ── Efectos visuales ──
        "fx_ken_burns":         st.session_state.get("fx_ken_burns", False),
        "fx_color_grade":       st.session_state.get("fx_color_grade", True),
        "fx_progress_bar":      st.session_state.get("fx_progress_bar", False),
        "fx_progress_bar_color":st.session_state.get("fx_progress_bar_color", "#FFFFFF"),
        "fx_hook_card":         st.session_state.get("fx_hook_card", False),
        "fx_hook_text":         st.session_state.get("fx_hook_text", ""),
        "fx_hook_duration":     st.session_state.get("fx_hook_duration", 2.5),
        "video_mode":           mode,
        "novela_theme":         st.session_state.get("novela_theme_input", ""),
        "podcast_topic":        st.session_state.get("podcast_topic_input", ""),
        "host_name":            st.session_state.get("podcast_host_name", "Host"),
        "guest_name":           st.session_state.get("podcast_guest_name", "Invitado"),
        "podcast_voice_a":      VOICES.get(st.session_state.get("podcast_voice_a", ""), ""),
        "podcast_voice_b":      VOICES.get(st.session_state.get("podcast_voice_b", ""), ""),
        "num_exchanges":        st.session_state.get("podcast_num_exchanges", 6),
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
                    # Para modo libro/biblia: pasar lista de temas ya vistos para evitar repetición
                    if mode == "libro":
                        _excl_books = st.session_state.get("libro_used_books", [])
                    elif mode == "biblia":
                        _excl_books = st.session_state.get("biblia_used_topics", [])
                    else:
                        _excl_books = []
                    _td = _brain_h.get_topic_and_description(_ht, _hc, mode, lang_option,
                                                              exclude_books=_excl_books)
                    _resolved_topic = _td["topic"]
                    _topic_desc     = _td["description"]
                    # Registrar el tema usado para no repetirlo en la próxima llamada
                    if mode == "libro" and _resolved_topic:
                        _used = st.session_state.get("libro_used_books", [])
                        if _resolved_topic not in _used:
                            _used.append(_resolved_topic)
                            st.session_state["libro_used_books"] = _used[-20:]
                    elif mode == "biblia" and _resolved_topic:
                        _used = st.session_state.get("biblia_used_topics", [])
                        if _resolved_topic not in _used:
                            _used.append(_resolved_topic)
                            st.session_state["biblia_used_topics"] = _used[-20:]
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

                # Paso 3: recomendar voz + generar preview
                with st.spinner("🎙️ " + ("Recomendando voz para este video..." if _is_es_hook else "Recommending voice for this video...")):
                    _cur_tts_r = st.session_state.get("tts_engine", "edge_tts")
                    if _cur_tts_r == "google_tts":
                        from modules.audio import GoogleTTSAudioEngine as _GTTS_r
                        _v_map_r = _GTTS_r.VOICES_ES if lang_option == "es" else _GTTS_r.VOICES_EN
                    elif _cur_tts_r == "edge_tts":
                        _v_map_r = VOICES_ES if lang_option == "es" else VOICES_EN
                    else:
                        _v_map_r = None

                    if _v_map_r:
                        _voice_opts_r = list(_v_map_r.keys())
                        _rec_label = _brain_h.recommend_voice(
                            _resolved_topic, _hc, mode, lang_option, _cur_tts_r, _voice_opts_r
                        )
                        # Guardar el valor real resuelto (no sólo el label) para evitar fallos de lookup al aplicar
                        _rec_resolved_val = _v_map_r.get(_rec_label, list(_v_map_r.values())[0])
                        import json as _json_rv
                        if isinstance(_rec_resolved_val, tuple):
                            st.session_state["recommended_voice_value"] = _json_rv.dumps(list(_rec_resolved_val))
                        else:
                            st.session_state["recommended_voice_value"] = _rec_resolved_val
                        st.session_state["recommended_voice_engine"] = _cur_tts_r
                        st.session_state["recommended_voice_label"]  = _rec_label

                        # Texto del preview: primer hook + descripción (max 220 chars)
                        _prev_text_r = ((_hooks[0] + ". " + _topic_desc) if _hooks else _topic_desc).strip()[:220]
                        _prev_rec_path = os.path.join(os.path.dirname(__file__), "assets", "temp", "rec_voice_preview.mp3")
                        os.makedirs(os.path.dirname(_prev_rec_path), exist_ok=True)
                        try:
                            if _cur_tts_r == "google_tts":
                                _gtts_key_r = os.getenv("GOOGLE_TTS_KEY", "")
                                _rec_val = _v_map_r.get(_rec_label, list(_v_map_r.values())[0])
                                _prev_eng_r = _GTTS_r(api_key=_gtts_key_r, voice_name=_rec_val[1],
                                                      lang_code=_rec_val[0], speaking_rate=1.0, pitch=0.0)
                                _prev_eng_r._synthesize(_prev_text_r, _prev_rec_path)
                            elif _cur_tts_r == "edge_tts":
                                import asyncio as _asyncio_r, edge_tts as _et_r
                                _rec_voice_str = _v_map_r.get(_rec_label, list(_v_map_r.values())[0])
                                async def _gen_rec_prev(t, v, p):
                                    await _et_r.Communicate(t, v).save(p)
                                _asyncio_r.run(_gen_rec_prev(_prev_text_r, _rec_voice_str, _prev_rec_path))
                            st.session_state["rec_voice_preview_path"] = _prev_rec_path
                        except Exception as _pe:
                            st.session_state["rec_voice_preview_path"] = ""
                            print(f"⚠️ Voice preview failed: {_pe}")
                    else:
                        st.session_state["recommended_voice_label"] = ""
                        st.session_state["rec_voice_preview_path"]  = ""

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

    # ── Voz recomendada por IA ────────────────────────────────────────────────
    _rec_label_show  = st.session_state.get("recommended_voice_label", "")
    _rec_prev_path   = st.session_state.get("rec_voice_preview_path", "")
    _cur_tts_show    = st.session_state.get("tts_engine", "edge_tts")

    if _rec_label_show and _cur_tts_show != "voxcpm":
        _display_label = _rec_label_show.split("(")[0].split("[")[0].strip()
        st.markdown(
            f"<div style='background:#f0fdf4;border:1px solid #bbf7d0;border-left:4px solid #16a34a;"
            f"border-radius:8px;padding:12px 16px;margin-bottom:14px;'>"
            f"<div style='font-size:0.75rem;font-weight:700;color:#16a34a;text-transform:uppercase;"
            f"letter-spacing:.06em;margin-bottom:4px;'>{'🎙️ Voz recomendada para este video' if _is_es else '🎙️ Recommended voice for this video'}</div>"
            f"<div style='font-size:0.95rem;font-weight:600;color:#14532d;'>{_display_label}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )
        if _rec_prev_path and os.path.exists(_rec_prev_path) and os.path.getsize(_rec_prev_path) > 500:
            st.audio(_rec_prev_path, format="audio/mp3")
        _col_rv1, _col_rv2 = st.columns(2)
        with _col_rv1:
            if st.button("✅ " + ("Usar esta voz" if _is_es else "Use this voice"),
                         key="apply_rec_voice", type="secondary", use_container_width=True):
                import json as _json_apply
                _saved_val   = st.session_state.get("recommended_voice_value", "")
                _saved_eng   = st.session_state.get("recommended_voice_engine", _cur_tts_show)
                if _saved_eng == "google_tts" and _saved_val:
                    try:
                        _gtts_tuple = _json_apply.loads(_saved_val)
                        # Guardar voz para que el selectbox la tome en el próximo render
                        # (no podemos escribir en gtts_voice_select aquí — ya fue renderizado)
                        st.session_state["_next_gtts_voice_select"] = _rec_label_show
                        _gv_key = "gtts_voice_es" if lang_option == "es" else "gtts_voice_en"
                        st.session_state[_gv_key] = _rec_label_show
                    except Exception:
                        pass
                elif _saved_eng == "edge_tts" and _saved_val:
                    st.session_state["_next_voice_select"] = _rec_label_show
                st.session_state["recommended_voice_label"] = ""
                st.session_state["rec_voice_preview_path"]  = ""
                st.success("✅ " + ("Voz aplicada." if _is_es else "Voice applied."))
                st.rerun()
        with _col_rv2:
            if st.button("✕ " + ("Ignorar" if _is_es else "Ignore"),
                         key="dismiss_rec_voice", type="secondary", use_container_width=True):
                st.session_state["recommended_voice_label"] = ""
                st.session_state["rec_voice_preview_path"]  = ""
                st.rerun()

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
            st.session_state["hook_step"]               = "idle"
            st.session_state["hook_options"]            = []
            st.session_state["chosen_hook"]             = ""
            st.session_state["_pending_topic_desc"]     = ""
            st.session_state["recommended_voice_label"]  = ""
            st.session_state["recommended_voice_value"]  = ""
            st.session_state["recommended_voice_engine"] = ""
            st.session_state["rec_voice_preview_path"]   = ""

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
                "use_avatar": use_avatar,
                "use_subtitles": use_subtitles,
                "subtitle_style": subtitle_style,
                "use_music":      st.session_state.get("use_music", False),
                "music_file_path":st.session_state.get("music_file_path", ""),
                "music_volume":   st.session_state.get("music_volume", 15) / 100.0,
                "music_fade_in":  st.session_state.get("music_fade_in", 1.0),
                "music_fade_out": st.session_state.get("music_fade_out", 2.0),
                "music_loop":     st.session_state.get("music_loop", True),
                "lang": lang_option, "mode": mode,
                "category": _fc,
                "webhook_url": _wh_url,
                "chosen_hook": _chosen_hook_val,
                "job_offer_text": st.session_state.get("job_offer_input", ""),
                "tts_engine":       st.session_state.get("tts_engine", "edge_tts"),
                "vox_voice_desc":   st.session_state.get("vox_voice_desc", ""),
                "vox_mood_enabled": st.session_state.get("vox_mood_enabled", True),
                "vox_clone_ref":    st.session_state.get("vox_clone_ref", ""),
                "gtts_api_key":     os.getenv("GOOGLE_TTS_KEY", ""),
                "gtts_voice_name":  st.session_state.get("gtts_voice_name", "es-US-Neural2-B"),
                "gtts_lang_code":   st.session_state.get("gtts_lang_code", "es-US"),
                "gtts_rate":        st.session_state.get("gtts_rate", 1.0),
                "gtts_pitch":       st.session_state.get("gtts_pitch", 0.0),
                "ai_video_style":        st.session_state.get("ai_video_style", "cinematic"),
                "video_source":          st.session_state.get("video_source", "pexels"),
                "ai_video_provider":     os.getenv("AI_VIDEO_PROVIDER", "fal"),
                "ai_video_key":          os.getenv("AI_VIDEO_KEY", ""),
                "ai_video_model":        os.getenv("AI_VIDEO_MODEL", ""),
                "ai_video_num_scenes":   st.session_state.get("ai_video_num_scenes", 6),
                "ai_video_clip_duration":st.session_state.get("ai_video_clip_duration", 5),
                "target_total_secs":     st.session_state.get("target_total_secs", 60),
                # ── Efectos visuales ──
                "fx_ken_burns":          st.session_state.get("fx_ken_burns", False),
                "fx_color_grade":        st.session_state.get("fx_color_grade", True),
                "fx_progress_bar":       st.session_state.get("fx_progress_bar", False),
                "fx_progress_bar_color": st.session_state.get("fx_progress_bar_color", "#FFFFFF"),
                "fx_hook_card":          st.session_state.get("fx_hook_card", False),
                "fx_hook_text":          st.session_state.get("fx_hook_text", ""),
                "fx_hook_duration":      st.session_state.get("fx_hook_duration", 2.5),
                "video_mode":            mode,
                "novela_theme":          st.session_state.get("novela_theme_input", ""),
                "podcast_topic":         st.session_state.get("podcast_topic_input", ""),
                "host_name":             st.session_state.get("podcast_host_name", "Host"),
                "guest_name":            st.session_state.get("podcast_guest_name", "Invitado"),
                "podcast_voice_a":       VOICES.get(st.session_state.get("podcast_voice_a", ""), ""),
                "podcast_voice_b":       VOICES.get(st.session_state.get("podcast_voice_b", ""), ""),
                "num_exchanges":         st.session_state.get("podcast_num_exchanges", 6),
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

# ══════════════════════════════════════════════════════════════════════════════
# 💬 GENERADOR DE FRASES VIRALES — siempre visible, independiente del pipeline
# ══════════════════════════════════════════════════════════════════════════════

st.markdown("---")
_is_es_q = lang_option == "es"

with st.expander(
    "💬 " + ("Generador de Frases Virales" if _is_es_q else "Viral Quote Card Generator"),
    expanded=False,
):
    st.caption(
        "Genera prompts listos para Midjourney · DALL·E · Flux · Ideogram en los 3 formatos clave."
        if _is_es_q else
        "Generate ready-to-use prompts for Midjourney · DALL·E · Flux · Ideogram in all 3 key formats."
    )

    # ── Categorías disponibles ─────────────────────────────────────────────
    _quote_categories_es = [
        "Auto (IA elige)",
        "Motivación y éxito",
        "Filosofía y vida",
        "Amor y relaciones",
        "Liderazgo y negocios",
        "Estoicismo",
        "Psicología y mente",
        "Espiritualidad",
        "Historia y guerreros",
        "Humor e ironía",
        "Resiliencia y superación",
        "Dinero e inversión",
        "Ciencia y tecnología",
        "Arte y creatividad",
        "Política y poder",
    ]
    _quote_categories_en = [
        "Auto (AI chooses)",
        "Motivation & success",
        "Philosophy & life",
        "Love & relationships",
        "Leadership & business",
        "Stoicism",
        "Psychology & mindset",
        "Spirituality",
        "History & warriors",
        "Humor & irony",
        "Resilience & growth",
        "Money & investing",
        "Science & technology",
        "Art & creativity",
        "Politics & power",
    ]
    _qcats = _quote_categories_es if _is_es_q else _quote_categories_en

    _qcol1, _qcol2 = st.columns([2, 1])
    with _qcol1:
        _qcustom = st.text_area(
            "✍️ " + ("Escribe la frase (opcional — vacío = IA elige)" if _is_es_q else "Type the quote (optional — empty = AI picks)"),
            placeholder=(
                'ej. "El único modo de hacer un gran trabajo es amar lo que haces." — Steve Jobs'
                if _is_es_q else
                'e.g. "The only way to do great work is to love what you do." — Steve Jobs'
            ),
            height=90,
            key="qcard_custom_quote",
        )
    with _qcol2:
        _qcat_sel = st.selectbox(
            "🏷️ " + ("Categoría" if _is_es_q else "Category"),
            options=_qcats,
            key="qcard_category",
        )
        # Normalize "Auto" selection → empty string for brain
        _qcat_for_brain = (
            "" if _qcat_sel in ("Auto (IA elige)", "Auto (AI chooses)") else _qcat_sel
        )

    # ── Botón generar ─────────────────────────────────────────────────────
    if st.button(
        "🎨 " + ("Generar prompts de imagen" if _is_es_q else "Generate image prompts"),
        key="qcard_generate_btn",
        type="primary",
        use_container_width=True,
    ):
        with st.spinner("✨ " + ("Generando prompts para los 3 formatos..." if _is_es_q else "Generating prompts for all 3 formats...")):
            try:
                from modules.brain import ContentBrain as _ContentBrain
                _qbrain = _ContentBrain()
                _qresult = _qbrain.generate_quote_card_prompts(
                    quote    = _qcustom.strip(),
                    category = _qcat_for_brain,
                    lang     = "es" if _is_es_q else "en",
                )
                st.session_state["qcard_result"] = _qresult
            except Exception as _qe:
                st.error(f"❌ {_qe}")

    # ── Mostrar resultados ─────────────────────────────────────────────────
    _qdata = st.session_state.get("qcard_result")
    if _qdata:
        _used_q = _qdata.get("quote_used", "")
        if _used_q:
            st.markdown(
                f"<div style='background:#f0fdf4;border-left:4px solid #10b981;padding:10px 14px;"
                f"border-radius:8px;margin:12px 0;font-style:italic;color:#065f46;font-size:0.92rem'>"
                f"💬 {_used_q}</div>",
                unsafe_allow_html=True,
            )

        # ── Copy por plataforma ────────────────────────────────────────────
        st.markdown(
            "**📣 " + ("Copy para redes sociales" if _is_es_q else "Social media captions") + "**"
        )
        _qct, _qci, _qcfb, _qcx = st.tabs(["🎵 TikTok", "📸 Instagram", "👥 Facebook", "🐦 Twitter / X"])

        with _qct:
            _c_tt = _qdata.get("copy_tiktok", "")
            if _c_tt:
                st.caption("✅ #fyp #viral fijos + 2 de nicho — máx 4 hashtags" if _is_es_q else "✅ #fyp #viral fixed + 2 niche — max 4 hashtags")
                st.code(_c_tt, language=None)
            else:
                st.info("—")

        with _qci:
            _c_ig = _qdata.get("copy_instagram", "")
            if _c_ig:
                st.caption("✅ 4 hashtags: 1 amplio + 1 mediano + 2 nicho — estrategia de 3 capas" if _is_es_q else "✅ 4 hashtags: 1 broad + 1 medium + 2 niche — 3-layer strategy")
                st.code(_c_ig, language=None)
            else:
                st.info("—")

        with _qcfb:
            _c_fb = _qdata.get("copy_facebook", "")
            if _c_fb:
                st.caption("✅ Pregunta al final para generar comentarios — máx 3 hashtags" if _is_es_q else "✅ Question at the end to spark comments — max 3 hashtags")
                st.code(_c_fb, language=None)
            else:
                st.info("—")

        with _qcx:
            _c_tw = _qdata.get("copy_twitter", "")
            if _c_tw:
                st.caption("✅ Frase directa + máx 2 hashtags trending — menos es más en X" if _is_es_q else "✅ Direct line + max 2 trending hashtags — less is more on X")
                st.code(_c_tw, language=None)
            else:
                st.info("—")

        st.markdown("---")
        _qt1, _qt2, _qt3 = st.tabs([
            "📱 9:16 — Reels / Stories",
            "⬛ 1:1 — Instagram Post",
            "🖥️ 16:9 — YouTube / LinkedIn",
        ])

        with _qt1:
            _p916 = _qdata.get("prompt_9_16", "")
            if _p916:
                st.caption("📋 " + ("Copia y pega en Midjourney, DALL·E, Flux o Ideogram" if _is_es_q else "Copy and paste into Midjourney, DALL·E, Flux or Ideogram"))
                st.code(_p916, language=None)
            else:
                st.info("No disponible.")

        with _qt2:
            _p11 = _qdata.get("prompt_1_1", "")
            if _p11:
                st.caption("📋 " + ("Copia y pega en Midjourney, DALL·E, Flux o Ideogram" if _is_es_q else "Copy and paste into Midjourney, DALL·E, Flux or Ideogram"))
                st.code(_p11, language=None)
            else:
                st.info("No disponible.")

        with _qt3:
            _p169 = _qdata.get("prompt_16_9", "")
            if _p169:
                st.caption("📋 " + ("Copia y pega en Midjourney, DALL·E, Flux o Ideogram" if _is_es_q else "Copy and paste into Midjourney, DALL·E, Flux or Ideogram"))
                st.code(_p169, language=None)
            else:
                st.info("No disponible.")
