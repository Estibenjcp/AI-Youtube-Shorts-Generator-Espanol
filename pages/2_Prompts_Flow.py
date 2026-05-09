import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="Prompts Flow / Veo 3",
    page_icon="🎬",
    layout="centered",
    initial_sidebar_state="expanded",
)

# Ocultar header nativo de Streamlit en esta página
st.markdown("""
<style>
#MainMenu, footer, header,
[data-testid="stDecoration"],
[data-testid="stStatusWidget"],
[data-testid="stToolbar"],
[data-testid="stAppDeployButton"],
.viewerBadge_container__1QSob { display: none !important; }
.block-container { padding: 0 !important; max-width: 100% !important; }
iframe { border: none !important; }
</style>
""", unsafe_allow_html=True)

HTML = r"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Generador de Prompts Multi-Modo v4</title>
<style>
*{box-sizing:border-box;}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#faf9f5;color:#1a1a1a;margin:0;padding:20px;line-height:1.5;}
.container{max-width:800px;margin:0 auto;}
.header-row{display:flex;justify-content:space-between;align-items:flex-start;gap:16px;margin-bottom:20px;flex-wrap:wrap;}
h1{font-size:22px;margin:0 0 4px;font-weight:500;}
.subtitle{color:#666;font-size:13px;margin:0;}
.lang-switch{display:flex;background:#fff;border:0.5px solid rgba(0,0,0,0.15);border-radius:8px;padding:3px;flex-shrink:0;}
.lang-btn{height:28px;padding:0 12px;border:none;background:transparent;border-radius:5px;font-size:13px;cursor:pointer;font-family:inherit;color:#666;font-weight:500;}
.lang-btn.active{background:#1a1a1a;color:#fff;}
.mode-selector-wrap{margin-bottom:14px;}
.mode-cat-label{font-size:10px;font-weight:700;color:#888;text-transform:uppercase;letter-spacing:0.5px;margin:0 0 5px;}
.mode-selector{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:6px;}
.mode-pill{display:flex;align-items:center;gap:5px;padding:6px 11px;background:#fff;border:0.5px solid rgba(0,0,0,0.15);border-radius:20px;cursor:pointer;transition:all 0.15s;white-space:nowrap;}
.mode-pill:hover{background:#f5f4ed;}
.mode-pill.active{background:#1a1a1a;border-color:#1a1a1a;}
.mode-pill.active .mode-title{color:#fff;}
.mode-icon{font-size:14px;}
.mode-title{font-size:12px;font-weight:500;color:#1a1a1a;}
.mode-desc{display:none;}
.format-row{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:16px;}
.format-block{background:#fff;border:0.5px solid rgba(0,0,0,0.12);border-radius:12px;padding:14px;}
.format-block h4{font-size:12px;color:#666;text-transform:uppercase;letter-spacing:0.5px;margin:0 0 10px;font-weight:500;}
.format-pills{display:flex;gap:6px;flex-wrap:wrap;}
.fpill{padding:5px 12px;background:#f0ede2;border:none;border-radius:20px;font-size:12px;cursor:pointer;font-family:inherit;color:#1a1a1a;font-weight:500;transition:all 0.15s;}
.fpill:hover{background:#e0ddd2;}
.fpill.active{background:#1a1a1a;color:#fff;}
#highlight-subtypes{margin-top:10px;display:none;}
.sub-pills{display:flex;gap:5px;flex-wrap:wrap;margin-top:6px;}
.spill{padding:4px 10px;background:#f0ede2;border:none;border-radius:20px;font-size:11px;cursor:pointer;font-family:inherit;color:#555;transition:all 0.15s;}
.spill:hover{background:#e0ddd2;}
.spill.active{background:#555;color:#fff;}
.dur-pills{display:flex;gap:6px;flex-wrap:wrap;}
.dpill{padding:5px 12px;background:#f0ede2;border:none;border-radius:20px;font-size:12px;cursor:pointer;font-family:inherit;color:#1a1a1a;font-weight:500;transition:all 0.15s;}
.dpill:hover{background:#e0ddd2;}
.dpill.active{background:#185fa5;color:#fff;}
.dur-info{font-size:11px;color:#888;margin-top:6px;}
.npill{padding:5px 14px;background:#f0ede2;border:none;border-radius:20px;font-size:12px;cursor:pointer;font-family:inherit;color:#1a1a1a;font-weight:600;transition:all 0.15s;}
.npill:hover{background:#e0ddd2;}
.npill.active{background:#7c3aed;color:#fff;}
.card{background:#fff;border:0.5px solid rgba(0,0,0,0.12);border-radius:12px;padding:14px;margin-bottom:14px;}
.card h3{font-size:12px;font-weight:500;margin:0 0 10px;color:#666;text-transform:uppercase;letter-spacing:0.5px;display:flex;align-items:center;gap:8px;}
.tag{display:inline-block;padding:1px 7px;background:#e6f1fb;color:#0c447c;border-radius:4px;font-size:11px;font-weight:500;}
.tag.rnd{background:#fbeaf0;color:#72243e;}
.grid2{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:10px;}
label{display:block;font-size:12px;color:#666;margin-bottom:5px;font-weight:500;}
select,input{width:100%;height:34px;padding:0 10px;border:0.5px solid rgba(0,0,0,0.2);border-radius:6px;font-size:13px;background:#fff;font-family:inherit;}
select:focus,input:focus{outline:2px solid #185fa5;outline-offset:-1px;}
.row{display:flex;gap:8px;align-items:center;}
.row>input{flex:1;}
.actions{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin:16px 0;}
.actions button{width:100%;height:40px;padding:0 8px;font-size:12px;font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
button{height:36px;padding:0 14px;border:0.5px solid rgba(0,0,0,0.25);background:#fff;border-radius:6px;font-size:13px;cursor:pointer;font-family:inherit;transition:all 0.15s;white-space:nowrap;}
button:hover{background:#f5f4ed;}
button:active{transform:scale(0.98);}
button.primary{background:#1a1a1a;color:#fff;border-color:#1a1a1a;font-weight:500;}
button.primary:hover{background:#333;}
#output-area{display:none;margin-top:16px;}
.config-box{background:#f0ede2;border-left:3px solid #1a1a1a;padding:10px 14px;border-radius:0 8px 8px 0;font-family:'SF Mono',Monaco,monospace;font-size:11px;line-height:1.7;white-space:pre-wrap;margin-bottom:14px;}
details{background:#fff;border:0.5px solid rgba(0,0,0,0.12);border-radius:12px;padding:10px 14px;margin-bottom:8px;}
summary{cursor:pointer;font-size:13px;font-weight:500;padding:3px 0;user-select:none;}
details[open] summary{margin-bottom:8px;}
.out-header{display:flex;justify-content:space-between;align-items:center;margin:6px 0;gap:10px;}
.out-hint{font-size:11px;color:#888;flex:1;}
.cbtn{height:26px;padding:0 10px;font-size:11px;}
.output{background:#faf9f5;border:0.5px solid rgba(0,0,0,0.1);border-radius:6px;padding:10px;font-family:'SF Mono',Monaco,'Courier New',monospace;font-size:11px;line-height:1.6;white-space:pre-wrap;word-break:break-word;max-height:400px;overflow-y:auto;color:#2a2a2a;}
.clip-card{background:#fff;border:0.5px solid rgba(0,0,0,0.1);border-radius:8px;padding:10px 12px;margin-bottom:8px;}
.clip-header{font-size:11px;font-weight:600;color:#185fa5;margin-bottom:6px;}
.clip-section{font-size:11px;margin-bottom:4px;}
.clip-voice{background:#f8f5e8;border-radius:5px;padding:8px;font-family:'SF Mono',Monaco,monospace;font-size:10.5px;line-height:1.5;margin-top:4px;white-space:pre-wrap;word-break:break-word;}
.clip-copy{height:22px;padding:0 8px;font-size:10px;margin-top:6px;}
/* API PANEL */
.api-panel{background:#fff;border:0.5px solid rgba(0,0,0,0.15);border-radius:12px;padding:12px 14px;margin-bottom:16px;}
.api-panel-header{display:flex;justify-content:space-between;align-items:center;cursor:pointer;user-select:none;}
.api-panel-header h4{margin:0;font-size:13px;font-weight:600;color:#1a1a1a;}
.api-body{display:none;margin-top:12px;flex-wrap:wrap;gap:10px;align-items:flex-end;}
.api-body.open{display:flex;}
.api-field{flex:1;min-width:180px;}
.api-field label{display:block;font-size:11px;color:#666;margin-bottom:4px;font-weight:500;}
.api-field input,.api-field select{width:100%;height:32px;padding:0 8px;border:0.5px solid rgba(0,0,0,0.2);border-radius:6px;font-size:12px;font-family:inherit;background:#fff;}
.api-badge{display:inline-block;padding:2px 9px;border-radius:20px;font-size:10px;font-weight:600;cursor:pointer;}
.badge-ok{background:#f0fdf4;color:#166534;}
.badge-off{background:#f3f4f6;color:#6b7280;}
.badge-err{background:#fff1f2;color:#9f1239;}
button.btn-ai{background:#185fa5;color:#fff;border-color:#185fa5;font-weight:500;}
button.btn-ai:hover{background:#1251a3;}
button.btn-ai:disabled{background:#93c5fd;border-color:#93c5fd;cursor:not-allowed;}
.ai-out{background:#fff;border:0.5px solid rgba(0,0,0,0.12);border-radius:12px;padding:14px;margin-top:16px;}
.ai-seg{background:#f9fafb;border-radius:8px;padding:10px;margin-bottom:8px;font-size:12px;}
.ai-seg-label{font-size:10px;font-weight:600;color:#185fa5;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:4px;}
.spinner{display:inline-block;width:12px;height:12px;border:2px solid #fff;border-top-color:transparent;border-radius:50%;animation:spin 0.7s linear infinite;margin-right:6px;vertical-align:middle;}
@keyframes spin{to{transform:rotate(360deg)}}
.footer{text-align:center;color:#999;font-size:11px;margin-top:24px;padding-top:16px;border-top:0.5px solid rgba(0,0,0,0.1);}
@media(max-width:600px){.grid2{grid-template-columns:1fr;}.format-row{grid-template-columns:1fr;}.mode-pill{min-width:100%;}}
.toast{position:fixed;bottom:24px;left:50%;transform:translateX(-50%);background:#1a1a1a;color:#fff;padding:8px 20px;border-radius:20px;font-size:12px;font-weight:600;z-index:9999;pointer-events:none;opacity:1;transition:opacity 0.5s;}
.copy-overlay{position:fixed;inset:0;background:rgba(0,0,0,0.55);z-index:9990;display:flex;align-items:center;justify-content:center;padding:16px;}
.copy-box{background:#fff;border-radius:14px;padding:16px;width:100%;max-width:640px;max-height:85vh;display:flex;flex-direction:column;gap:10px;box-shadow:0 20px 60px rgba(0,0,0,0.3);}
.copy-box-header{display:flex;justify-content:space-between;align-items:center;}
.copy-box-header span{font-size:13px;font-weight:600;color:#1a1a1a;}
.copy-box-header button{background:none;border:none;font-size:20px;cursor:pointer;color:#666;line-height:1;padding:0 4px;}
.copy-box textarea{width:100%;flex:1;min-height:220px;max-height:55vh;font-size:11px;font-family:'SF Mono',Monaco,monospace;padding:10px;border:1px solid #ddd;border-radius:8px;resize:vertical;color:#1a1a1a;line-height:1.5;}
.copy-box-hint{font-size:11px;color:#666;text-align:center;}
.copy-box-hint kbd{background:#f0ede2;border:1px solid #ccc;border-radius:4px;padding:1px 5px;font-size:10px;font-family:monospace;}
</style>
</head>
<body>
<div class="container">

<!-- API PANEL -->
<div class="api-panel">
  <div class="api-panel-header" onclick="toggleApi()">
    <h4>🔑 OpenRouter API &nbsp;<span class="api-badge badge-off" id="api-badge">sin configurar — clic para abrir</span></h4>
    <span id="api-arrow">▼</span>
  </div>
  <div class="api-body" id="api-body">
    <div class="api-field" style="flex:2;">
      <label>API Key</label>
      <input type="password" id="or-key" placeholder="sk-or-v1-..." autocomplete="off">
    </div>
    <div class="api-field" style="flex:2;">
      <label>Modelo</label>
      <select id="or-model" onchange="onModelChange()">
        <optgroup label="✦ Mejores para guiones (2026)">
          <option value="anthropic/claude-3.7-sonnet">Claude 3.7 Sonnet 🏆 mejor escritura</option>
          <option value="anthropic/claude-3.5-sonnet">Claude 3.5 Sonnet ✨ creativo</option>
          <option value="openai/gpt-4.1">GPT-4.1 💎 nuevo 2025</option>
          <option value="google/gemini-2.5-pro-preview-03-25">Gemini 2.5 Pro 🔥 largo contexto</option>
        </optgroup>
        <optgroup label="⚡ Rápido / Económico">
          <option value="anthropic/claude-3.5-haiku">Claude 3.5 Haiku ⚡ rápido</option>
          <option value="openai/gpt-4.1-mini">GPT-4.1 Mini ⚡ económico</option>
          <option value="google/gemini-2.5-flash-preview">Gemini 2.5 Flash ⚡</option>
          <option value="google/gemini-2.0-flash-001">Gemini 2.0 Flash ⚡</option>
        </optgroup>
        <optgroup label="🆓 Gratis">
          <option value="meta-llama/llama-4-scout:free">Llama 4 Scout 🆓</option>
          <option value="google/gemini-2.0-flash-exp:free">Gemini 2.0 Flash 🆓</option>
          <option value="mistralai/mistral-7b-instruct:free">Mistral 7B 🆓</option>
        </optgroup>
        <optgroup label="🧠 Reasoning">
          <option value="openai/o4-mini">OpenAI o4-mini 🧠</option>
          <option value="openai/o3-mini">OpenAI o3-mini 🧠</option>
        </optgroup>
        <optgroup label="🦙 Meta Llama">
          <option value="meta-llama/llama-4-maverick">Llama 4 Maverick</option>
        </optgroup>
        <option value="__custom__">✏️ Escribir modelo manualmente...</option>
      </select>
    </div>
    <div class="api-field" id="custom-model-field" style="flex:2;display:none;">
      <label>Modelo personalizado (slug exacto de OpenRouter)</label>
      <input type="text" id="or-model-custom" placeholder="ej. anthropic/claude-opus-4">
    </div>
    <div style="display:flex;gap:8px;padding-bottom:1px;">
      <button onclick="saveApi()" style="height:32px;padding:0 14px;font-size:12px;">💾 Guardar</button>
      <button onclick="testApi()" style="height:32px;padding:0 14px;font-size:12px;">🔌 Probar</button>
    </div>
  </div>
</div>

<div class="header-row">
  <div>
    <h1>🎬 Generador de prompts</h1>
    <p class="subtitle">Multi-modo · ChatGPT + Google Flow / Veo 3 + CapCut</p>
  </div>
  <div class="lang-switch">
    <button class="lang-btn active" data-lang="es">ES</button>
    <button class="lang-btn" data-lang="en">EN</button>
  </div>
</div>

<div class="mode-selector-wrap">
  <div class="mode-cat-label" data-i18n="podcastCat">🎙️ Podcast</div>
  <div class="mode-selector" id="mode-selector-podcast"></div>
  <div class="mode-cat-label" style="margin-top:8px;" data-i18n="narratorCat">📺 Narrador / Canal</div>
  <div class="mode-selector" id="mode-selector-narrator"></div>
</div>

<div class="format-row" style="grid-template-columns:1fr 1fr 1fr;">
  <div class="format-block">
    <h4 data-i18n="formatLabel">Formato del video</h4>
    <div class="format-pills">
      <button class="fpill active" data-format="lineal" data-i18n="fmtLineal">📖 Lineal</button>
      <button class="fpill" data-format="highlight" data-i18n="fmtHighlight">⚡ Highlight</button>
    </div>
    <div id="highlight-subtypes">
      <div style="font-size:11px;color:#888;margin-top:8px;" data-i18n="highlightSubLabel">Sub-tipo:</div>
      <div class="sub-pills" id="sub-pills-container"></div>
    </div>
  </div>
  <div class="format-block">
    <h4 data-i18n="durationLabel">Duración del video</h4>
    <div class="dur-pills">
      <button class="dpill active" data-dur="1">1 min</button>
      <button class="dpill" data-dur="2">2 min</button>
      <button class="dpill" data-dur="3">3 min</button>
      <button class="dpill" data-dur="5">5 min</button>
    </div>
    <div class="dur-info" id="dur-info"></div>
  </div>
  <div class="format-block">
    <h4 data-i18n="setStyleLabel">Estilo de set</h4>
    <div class="format-pills" style="flex-direction:column;gap:5px;">
      <button class="spill active" data-set="oscuro" style="text-align:left;padding:5px 12px;">🕯️ Oscuro / Edison</button>
      <button class="spill" data-set="moderno" style="text-align:left;padding:5px 12px;">💡 Moderno / Softbox</button>
      <button class="spill" data-set="natural" style="text-align:left;padding:5px 12px;">🌿 Natural / Madera</button>
      <button class="spill" data-set="neon" style="text-align:left;padding:5px 12px;">🎨 Neon / Urbano</button>
      <button class="spill" data-set="biblioteca" style="text-align:left;padding:5px 12px;">📚 Biblioteca / Clásico</button>
      <button class="spill" data-set="mistico" style="text-align:left;padding:5px 12px;">🔮 Místico / Velas</button>
    </div>
  </div>
</div>

<div id="narrator-count-row" style="display:none;margin-bottom:14px;">
  <div style="background:#fff;border:0.5px solid rgba(0,0,0,0.12);border-radius:12px;padding:12px 14px;">
    <h4 style="font-size:12px;color:#666;text-transform:uppercase;letter-spacing:0.5px;margin:0 0 12px;font-weight:500;" data-i18n="nCountLabel">Personajes en escena</h4>
    <div style="display:flex;gap:20px;flex-wrap:wrap;">
      <div style="flex:1;min-width:160px;">
        <div style="font-size:11px;font-weight:700;color:#7c3aed;margin-bottom:6px;display:flex;align-items:center;gap:4px;">🎙️ HOST(S)</div>
        <div style="display:flex;gap:5px;">
          <button class="npill host-pill active" data-n="1">1</button>
          <button class="npill host-pill" data-n="2">2</button>
          <button class="npill host-pill" data-n="3">3</button>
          <button class="npill host-pill" data-n="4">4</button>
        </div>
      </div>
      <div style="flex:1;min-width:160px;">
        <div style="font-size:11px;font-weight:700;color:#e11d48;margin-bottom:6px;display:flex;align-items:center;gap:4px;">🎤 GUEST(S)</div>
        <div style="display:flex;gap:5px;">
          <button class="npill guest-pill active" data-n="0">0</button>
          <button class="npill guest-pill" data-n="1">1</button>
          <button class="npill guest-pill" data-n="2">2</button>
          <button class="npill guest-pill" data-n="3">3</button>
        </div>
      </div>
    </div>
    <div style="font-size:11px;color:#888;margin-top:8px;" id="ncount-info">Un solo narrador en escena.</div>
  </div>
</div>

<div id="config-blocks"></div>

<div class="card">
  <h3 data-i18n="topicSection">Tema y estilo</h3>
  <div style="margin-bottom:10px;">
    <label data-i18n="topicLabel">Tema del episodio</label>
    <div class="row">
      <input type="text" id="topic" data-i18n-placeholder="topicPH">
      <button id="roll-topic">🎲</button>
    </div>
  </div>
  <div class="grid2">
    <div><label data-i18n="styleLabel">Estilo</label><select id="style"></select></div>
    <div><label data-i18n="toneLabel">Tono</label><select id="tone"></select></div>
  </div>
</div>

<div class="actions">
  <button id="btn-clear" onclick="clearFields()" style="background:#fff;border-color:rgba(0,0,0,0.2);">🗑️ Limpiar campos</button>
  <button id="recommend-combo" onclick="recommendCombo()" disabled style="background:#7c3aed;border-color:#7c3aed;color:#fff;">🎯 Recomendar combo</button>
  <button id="generate-ai" onclick="generateWithAI()" disabled style="background:#185fa5;border-color:#185fa5;color:#fff;">👁️ Vista previa</button>
  <button id="generate" class="primary" onclick="generate()">⚡ Generar prompts</button>
</div>

<div id="ai-output-area"></div>

<div id="output-area">
  <div class="config-box" id="config-out"></div>
  <div id="output-blocks"></div>
</div>

<div class="footer">Sistema multi-modo v4 · 1MinutoDirecto</div>
</div>

<script>
// ── i18n ──────────────────────────────────────────────────────────────────────
const T={
  es:{title:"Generador de prompts",subtitle:"Multi-modo · ChatGPT + Google Flow / Veo 3 + CapCut",formatLabel:"Formato del video",fmtLineal:"📖 Lineal",fmtHighlight:"⚡ Highlight",highlightSubLabel:"Sub-tipo de highlight:",durationLabel:"Duración del video",setStyleLabel:"Estilo de set",topicSection:"Tema y estilo",topicLabel:"Tema del episodio",topicPH:"Escribe un tema o usa 🎲",styleLabel:"Estilo",toneLabel:"Tono",randomizeAll:"🎲 Aleatorizar todo",generateBtn:"⚡ Generar prompts Flow",copyBtn:"Copiar",copied:"✓ Copiado",manual:"manual",rnd:"aleatorio",podcastCat:"🎙️ Podcast",narratorCat:"📺 Narrador / Canal",nCountLabel:"Personajes en escena",backToTop:"⬆️ Volver arriba",
    durInfo:(n,clips,sec)=>`~${clips} clips de ${sec}s = ${n} minuto${n>1?'s':''}`,
    hlTypes:{rapida:"🌶️ Preguntas picantes",bestof:"🏆 Best-of / momentos pico",datos:"💡 Datos encadenados",comparacion:"⚔️ Comparaciones"},
    clipLabel:(i,total)=>`CLIP ${i} de ${total}`,
    outputTitles:{image1:"1️⃣ Prompt imagen del host (Image A)",image2:"2️⃣ Prompt imagen del invitado (Image A → reemplazo)",clips:"3️⃣ Prompts Flow completos por clip",meta:"4️⃣ Metadata publicación",imgNarrator:"1️⃣ Prompt imagen / escena",voiceNarrator:"2️⃣ Voice prompt narrador",clips2:"3️⃣ Prompts Flow completos por clip",meta2:"4️⃣ Metadata publicación"},
    hints:{image1:"Sin imagen de referencia — ChatGPT / Nano Banana",image2:"Sube Image A del host + pega esto",clips:"Cada bloque = 1 prompt para Google Flow.",meta:"TikTok / Reels / YouTube Shorts"}
  },
  en:{title:"Prompt generator",subtitle:"Multi-mode · ChatGPT + Google Flow / Veo 3 + CapCut",formatLabel:"Video format",fmtLineal:"📖 Linear",fmtHighlight:"⚡ Highlight",highlightSubLabel:"Highlight sub-type:",durationLabel:"Video duration",setStyleLabel:"Set style",topicSection:"Topic & style",topicLabel:"Episode topic",topicPH:"Write a topic or use 🎲",styleLabel:"Style",toneLabel:"Tone",randomizeAll:"🎲 Randomize all",generateBtn:"⚡ Generate Flow prompts",copyBtn:"Copy",copied:"✓ Copied",manual:"manual",rnd:"random",podcastCat:"🎙️ Podcast",narratorCat:"📺 Narrator / Channel",nCountLabel:"Characters on screen",backToTop:"⬆️ Back to top",
    durInfo:(n,clips,sec)=>`~${clips} clips of ${sec}s = ${n} minute${n>1?'s':''}`,
    hlTypes:{rapida:"🌶️ Hot questions",bestof:"🏆 Best-of / peak moments",datos:"💡 Chained facts",comparacion:"⚔️ Comparisons"},
    clipLabel:(i,total)=>`CLIP ${i} of ${total}`,
    outputTitles:{image1:"1️⃣ Host image prompt (Image A)",image2:"2️⃣ Guest image prompt",clips:"3️⃣ Full Flow prompts per clip",meta:"4️⃣ Publication metadata",imgNarrator:"1️⃣ Image / scene prompt",voiceNarrator:"2️⃣ Narrator voice prompt",clips2:"3️⃣ Full Flow prompts per clip",meta2:"4️⃣ Publication metadata"},
    hints:{image1:"No reference image — ChatGPT / Nano Banana",image2:"Upload host Image A + paste this",clips:"Each block = 1 prompt for Google Flow.",meta:"TikTok / Reels / YouTube Shorts"}
  }
};

const DUR_CLIPS={1:{clips:8,sec:8},2:{clips:15,sec:8},3:{clips:22,sec:8},5:{clips:37,sec:8}};

const MODES={
  'ficticio-viral':{icon:'🎙️',title:{es:'Podcast ficticio viral',en:'Fake viral podcast'},desc:{es:'Testimonios oscuros, conspirativo, humor negro',en:'Dark testimonies, conspiracy, dark humor'}},
  'misterio-biblico':{icon:'📜',title:{es:'Misterio bíblico / apócrifo',en:'Biblical / apocryphal mystery'},desc:{es:'Pergaminos, ángeles caídos, profecías ocultas',en:'Scrolls, fallen angels, hidden prophecies'}},
  'libro-rapido':{icon:'📚',title:{es:'Podcast de libro (rápido)',en:'Quick book podcast'},desc:{es:'Un narrador, un libro, 5 segmentos virales',en:'One narrator, one book, 5 viral segments'}},
  'documental-narrado':{icon:'🎬',title:{es:'Documental narrado',en:'Narrated documentary'},desc:{es:'Voz en off tipo NatGeo — historia oscura, catástrofes, secretos',en:'NatGeo-style voice-over — dark history, disasters, secrets'}},
  'testimonio-real':{icon:'😱',title:{es:'Testimonio real',en:'Real testimony'},desc:{es:'Primera persona, confesión dramatizada, tono perturbador',en:'First person, dramatized confession, disturbing tone'}},
  'reflexion-biblica':{icon:'🙏',title:{es:'Reflexión bíblica',en:'Biblical reflection'},desc:{es:'Devocional corto, voz calmada, versículo y reflexión',en:'Short devotional, calm voice, verse and reflection'}},
  'ciencia-misterio':{icon:'🌌',title:{es:'Ciencia y misterio',en:'Science & mystery'},desc:{es:'Narrador científico, datos impactantes, preguntas abiertas',en:'Scientific narrator, shocking facts, open questions'}},
  'true-crime':{icon:'🔍',title:{es:'True Crime',en:'True Crime'},desc:{es:'Detective + testigo — caso criminal oscuro y adictivo',en:'Detective + witness — dark addictive criminal case'}},
  'psicologia-oscura':{icon:'🧠',title:{es:'Psicología oscura',en:'Dark psychology'},desc:{es:'Experto + sobreviviente — manipulación, narcisismo, mente tóxica',en:'Expert + survivor — manipulation, narcissism, toxic mind'}},
  'conspiracion-moderna':{icon:'👁️',title:{es:'Conspiración moderna',en:'Modern conspiracy'},desc:{es:'Periodista + informante — IA, élites, tecnología y poder',en:'Journalist + whistleblower — AI, elites, tech and power'}},
  'finanzas-libertad':{icon:'💰',title:{es:'Finanzas & libertad',en:'Finance & freedom'},desc:{es:'Educación financiera viral, mentalidad de riqueza, libertad',en:'Viral financial education, wealth mindset, freedom'}},
  'mentalidad-disciplina':{icon:'💪',title:{es:'Mentalidad & disciplina',en:'Mindset & discipline'},desc:{es:'Motivación, hábitos, resiliencia — voz directa al espectador',en:'Motivation, habits, resilience — direct voice to viewer'}},
  'historia-epica':{icon:'⚔️',title:{es:'Historia épica',en:'Epic history'},desc:{es:'Batallas, imperios, héroes — narración cinematográfica épica',en:'Battles, empires, heroes — epic cinematic narration'}},
  'psicologia-positiva':{icon:'🌸',title:{es:'Psicología positiva',en:'Positive psychology'},desc:{es:'Autoestima, sanación emocional, límites, apego — contenido que sana',en:'Self-esteem, healing, boundaries, attachment — content that heals'}},
  'mente-masculina':{icon:'💎',title:{es:'Mente masculina',en:'Masculine mindset'},desc:{es:'Reflexiones profundas para hombres — emociones, amor propio, relaciones, propósito',en:'Deep reflections for men — emotions, self-love, relationships, purpose'}},
  'mujer-consciente':{icon:'🌺',title:{es:'Mujer consciente',en:'Conscious woman'},desc:{es:'Empoderamiento femenino — autoestima, sanación, relaciones, propósito y esencia propia',en:'Feminine empowerment — self-worth, healing, relationships, purpose and true self'}}
};

const MODE_SELECTS={
'ficticio-viral':{
  'host-type':{es:[['random','🎲 Aleatorio (IA elige)'],['clasico','Clásico carismático (35-45)'],['joven-energico','Joven enérgico (22-30)'],['intelectual','Intelectual / académico'],['periodista-investigador','Periodista investigador'],['conspirativo','Conspirativo / analista'],['espiritual','Espiritual / esotérico'],['comico-oscuro','Cómico con humor negro']],en:[['random','🎲 Random (AI chooses)'],['clasico','Classic charismatic (35-45)'],['joven-energico','Young & energetic (22-30)'],['intelectual','Intellectual / academic'],['periodista-investigador','Investigative journalist'],['conspirativo','Conspiracy analyst'],['espiritual','Spiritual / esoteric'],['comico-oscuro','Dark humor comedian']]},
  'host-gender':{es:[['random','🎲 Aleatorio'],['male','Masculino'],['female','Femenino']],en:[['random','🎲 Random'],['male','Male'],['female','Female']]},
  'host-region':{es:[['random','🎲 Aleatorio'],['latam-neutro','Latinoamérica (neutro)'],['mexico-centroam','México / Centroamérica'],['caribe','Caribe (RD, Cuba, PR)'],['sudamerica','Sudamérica (Col, Ven, Arg)'],['espana','España / Europa'],['ingles-neutro','Inglés neutro'],['bilingue','Bilingüe (mezcla)']],en:[['random','🎲 Random'],['latam-neutro','Latin America (neutral)'],['mexico-centroam','Mexico / Central America'],['caribe','Caribbean (DR, Cuba, PR)'],['sudamerica','South America (Col, Ven, Arg)'],['espana','Spain / Europe'],['ingles-neutro','Neutral English'],['bilingue','Bilingual (mixed)']]},
  'guest-type':{es:[['random','🎲 Aleatorio (IA elige)'],['sobreviviente','Sobreviviente / testigo directo'],['profesional-secreto','Profesional con secreto oscuro'],['artista-perturbado','Artista / creativo perturbado'],['ex-agente','Ex agente / infiltrado'],['victima-sistema','Víctima del sistema'],['figura-esoterica','Figura esotérica / espiritual'],['joven-trauma','Joven con trauma profundo'],['anciano-revelacion','Anciano con revelación'],['foraneo-misterioso','Foráneo / extranjero misterioso']],en:[['random','🎲 Random (AI chooses)'],['sobreviviente','Survivor / direct witness'],['profesional-secreto','Professional with dark secret'],['artista-perturbado','Disturbed artist / creative'],['ex-agente','Ex-agent / informant'],['victima-sistema','System victim'],['figura-esoterica','Esoteric / spiritual figure'],['joven-trauma','Youth with deep trauma'],['anciano-revelacion','Elder with revelation'],['foraneo-misterioso','Foreign / mysterious outsider']]},
  'guest-gender':{es:[['random','🎲 Aleatorio'],['female','Femenino'],['male','Masculino']],en:[['random','🎲 Random'],['female','Female'],['male','Male']]},
  'guest-region':{es:[['random','🎲 Aleatorio'],['latam-general','Latinoamérica (general)'],['mexico-centroam','México / Centroamérica'],['caribe','Caribe'],['sudamerica','Sudamérica'],['eeuu-hispano','EE.UU. / comunidad hispana'],['espana-europa','España / Europa'],['internacional','Internacional / sin especificar']],en:[['random','🎲 Random'],['latam-general','Latin America (general)'],['mexico-centroam','Mexico / Central America'],['caribe','Caribbean'],['sudamerica','South America'],['eeuu-hispano','US / Hispanic community'],['espana-europa','Spain / Europe'],['internacional','International / unspecified']]},
  'guest-age':{es:[['random','🎲 Aleatorio'],['18-25','Muy joven (18-25)'],['25-35','Joven adulto (25-35)'],['35-50','Adulto (35-50)'],['50-70','Mayor (50-70)'],['no-especificar','Sin especificar']],en:[['random','🎲 Random'],['18-25','Very young (18-25)'],['25-35','Young adult (25-35)'],['35-50','Adult (35-50)'],['50-70','Senior (50-70)'],['no-especificar','Unspecified']]},
  'style':{es:[['random','🎲 Aleatorio'],['conspirativo','Conspirativo / misterio'],['criminal','Testimonio oscuro / criminal'],['humor-negro','Humor negro'],['absurdo','Entrevista absurda'],['paranormal','Paranormal']],en:[['random','🎲 Random'],['conspirativo','Conspiracy / mystery'],['criminal','Dark / criminal testimony'],['humor-negro','Dark humor'],['absurdo','Absurd interview'],['paranormal','Paranormal']]},
  'tone':{es:[['random','🎲 Aleatorio'],['tenso','Tenso / intenso'],['frio','Frío / desapegado'],['erratico','Errático / inestable'],['ironico','Irónico / amargo']],en:[['random','🎲 Random'],['tenso','Tense / intense'],['frio','Cold / detached'],['erratico','Erratic / unstable'],['ironico','Ironic / bitter']]}
},
'misterio-biblico':{
  'narrator-type':{es:[['random','🎲 Aleatorio'],['erudito','Erudito anciano'],['monje','Monje encapuchado'],['profesor','Profesor académico'],['arqueologo','Arqueólogo'],['narrador-oculto','Solo voz (sin rostro)'],['profeta','Profeta moderno']],en:[['random','🎲 Random'],['erudito','Ancient scholar'],['monje','Hooded monk'],['profesor','Academic professor'],['arqueologo','Archaeologist'],['narrador-oculto','Voice only (no face)'],['profeta','Modern prophet']]},
  'narrator-gender':{es:[['random','🎲 Aleatorio'],['male','Masculino'],['female','Femenino']],en:[['random','🎲 Random'],['male','Male'],['female','Female']]},
  'narrator-lang':{es:[['random','🎲 Aleatorio'],['espanol-neutro','Español neutro'],['espanol-mexicano','Español mexicano'],['ingles-neutro','Inglés neutro'],['ingles-britanico','Inglés británico']],en:[['random','🎲 Random'],['espanol-neutro','Neutral Spanish'],['espanol-mexicano','Mexican Spanish'],['ingles-neutro','Neutral English'],['ingles-britanico','British English']]},
  'scene-type':{es:[['random','🎲 Aleatorio'],['biblioteca','Biblioteca antigua'],['caverna','Caverna Qumrán'],['ruinas','Ruinas de templo'],['scriptorium','Scriptorium medieval'],['desierto','Desierto al amanecer'],['podcast-oscuro','Studio oscuro con velas'],['cripta','Cripta con velas']],en:[['random','🎲 Random'],['biblioteca','Ancient library'],['caverna','Qumran cave'],['ruinas','Temple ruins'],['scriptorium','Medieval scriptorium'],['desierto','Desert at dawn'],['podcast-oscuro','Dark studio with candles'],['cripta','Candle-lit crypt']]},
  'subtopic':{es:[['random','🎲 Aleatorio'],['apocrifos','Libros apócrifos (Enoc, Jubileos)'],['mar-muerto','Manuscritos del Mar Muerto'],['profecias','Profecías ocultas'],['nefilim','Nefilim y ángeles caídos'],['reyes','Misterios de los reyes'],['geografia','Geografía bíblica perdida'],['simbolos','Símbolos y números ocultos'],['gnosticismo','Gnosticismo y evangelios alternativos']],en:[['random','🎲 Random'],['apocrifos','Apocryphal books'],['mar-muerto','Dead Sea Scrolls'],['profecias','Hidden prophecies'],['nefilim','Nephilim and fallen angels'],['reyes','Kings mysteries'],['geografia','Lost biblical geography'],['simbolos','Hidden symbols and numbers'],['gnosticismo','Gnosticism and alternative gospels']]},
  'style':{es:[['random','🎲 Aleatorio'],['documental','Documental serio'],['misterio','Misterioso / revelaciones ocultas'],['educativo','Educativo / divulgativo'],['profetico','Profético / apocalíptico']],en:[['random','🎲 Random'],['documental','Serious documentary'],['misterio','Mysterious / hidden revelations'],['educativo','Educational'],['profetico','Prophetic / apocalyptic']]},
  'tone':{es:[['random','🎲 Aleatorio'],['solemne','Solemne / grave'],['revelador','Revelador / enigmático'],['ominoso','Ominoso / amenazante'],['contemplativo','Contemplativo / espiritual']],en:[['random','🎲 Random'],['solemne','Solemn / grave'],['revelador','Revealing / enigmatic'],['ominoso','Ominous / menacing'],['contemplativo','Contemplative / spiritual']]}
},
'libro-rapido':{
  'narrator-type':{es:[['random','🎲 Aleatorio'],['joven-curioso','Joven curioso (25-32)'],['intelectual-moderno','Intelectual moderno (35-45)'],['motivador','Motivador energético (30-40)'],['filosofico','Filosófico tranquilo (40-55)'],['cinico-amigable','Cínico amigable (28-38)']],en:[['random','🎲 Random'],['joven-curioso','Curious youth (25-32)'],['intelectual-moderno','Modern intellectual (35-45)'],['motivador','Energetic motivator (30-40)'],['filosofico','Quiet philosopher (40-55)'],['cinico-amigable','Friendly cynic (28-38)']]},
  'narrator-gender':{es:[['random','🎲 Aleatorio'],['male','Masculino'],['female','Femenino']],en:[['random','🎲 Random'],['male','Male'],['female','Female']]},
  'book-genre':{es:[['random','🎲 Aleatorio'],['autoayuda','Autoayuda / desarrollo personal'],['negocios','Negocios / emprendimiento'],['psicologia','Psicología / comportamiento'],['filosofia','Filosofía / estoicismo'],['ciencia','Ciencia popular'],['historia','Historia / biografía'],['productividad','Productividad / hábitos']],en:[['random','🎲 Random'],['autoayuda','Self-help / personal growth'],['negocios','Business / entrepreneurship'],['psicologia','Psychology / behavior'],['filosofia','Philosophy / stoicism'],['ciencia','Popular science'],['historia','History / biography'],['productividad','Productivity / habits']]},
  'style':{es:[['random','🎲 Aleatorio'],['inspirador','Inspirador / motivacional'],['revelador','Revelador / sorprendente'],['practico','Práctico / accionable'],['filosofico','Filosófico / reflexivo']],en:[['random','🎲 Random'],['inspirador','Inspiring / motivational'],['revelador','Revealing / surprising'],['practico','Practical / actionable'],['filosofico','Philosophical / reflective']]},
  'tone':{es:[['random','🎲 Aleatorio'],['amigo-inteligente','Como hablarle a un amigo inteligente'],['profesor-cool','Profesor cool que simplifica'],['conversacional','Conversacional y directo'],['intenso','Intenso y urgente']],en:[['random','🎲 Random'],['amigo-inteligente','Like talking to a smart friend'],['profesor-cool','Cool teacher who simplifies'],['conversacional','Conversational and direct'],['intenso','Intense and urgent']]}
},
'documental-narrado':{
  'narrator-type':{es:[['random','🎲 Aleatorio'],['periodista','Periodista investigador'],['historiador','Historiador académico'],['sobreviviente','Sobreviviente testigo'],['militar-retirado','Ex militar retirado'],['cientifico','Científico forense']],en:[['random','🎲 Random'],['periodista','Investigative journalist'],['historiador','Academic historian'],['sobreviviente','Surviving witness'],['militar-retirado','Retired ex-military'],['cientifico','Forensic scientist']]},
  'narrator-gender':{es:[['random','🎲 Aleatorio'],['male','Masculino'],['female','Femenino']],en:[['random','🎲 Random'],['male','Male'],['female','Female']]},
  'category':{es:[['random','🎲 Aleatorio'],['historia-oscura','Historia oscura y olvidada'],['catastrofes','Catástrofes y desastres'],['guerras-secretas','Secretos de guerras'],['experimentos','Experimentos gubernamentales'],['civilizaciones','Civilizaciones perdidas'],['nucleares','Hechos nucleares impactantes'],['mortandades','Mortandades históricas']],en:[['random','🎲 Random'],['historia-oscura','Dark forgotten history'],['catastrofes','Catastrophes and disasters'],['guerras-secretas','War secrets'],['experimentos','Government experiments'],['civilizaciones','Lost civilizations'],['nucleares','Shocking nuclear facts'],['mortandades','Historic mass deaths']]},
  'style':{es:[['random','🎲 Aleatorio'],['revelador','Revelador / impactante'],['ominoso','Ominoso / tenso'],['epico','Épico / grandioso'],['frio','Frío / periodístico']],en:[['random','🎲 Random'],['revelador','Revealing / shocking'],['ominoso','Ominous / tense'],['epico','Epic / grandiose'],['frio','Cold / journalistic']]},
  'tone':{es:[['random','🎲 Aleatorio'],['grave','Grave / solemne'],['urgente','Urgente / alarmante'],['nostalgico','Nostálgico / reflexivo'],['suspenso','Suspenso creciente']],en:[['random','🎲 Random'],['grave','Grave / solemn'],['urgente','Urgent / alarming'],['nostalgico','Nostalgic / reflective'],['suspenso','Rising suspense']]}
},
'testimonio-real':{
  'narrator-type':{es:[['random','🎲 Aleatorio'],['anonimo','Voz anónima protegida'],['superviviente','Superviviente de trauma'],['ex-agente','Ex agente o infiltrado'],['victima','Víctima directa'],['testigo','Testigo ocular']],en:[['random','🎲 Random'],['anonimo','Protected anonymous voice'],['superviviente','Trauma survivor'],['ex-agente','Ex-agent or informant'],['victima','Direct victim'],['testigo','Eyewitness']]},
  'narrator-gender':{es:[['random','🎲 Aleatorio'],['male','Masculino'],['female','Femenino']],en:[['random','🎲 Random'],['male','Male'],['female','Female']]},
  'category':{es:[['random','🎲 Aleatorio'],['misterioso','Testimonio misterioso'],['paranormal','Experiencia paranormal'],['criminal','Testimonio criminal / oscuro'],['conspiracion','Conspiración revelada'],['secta','Escape de secta o culto'],['sobrenatural','Evento sobrenatural']],en:[['random','🎲 Random'],['misterioso','Mysterious testimony'],['paranormal','Paranormal experience'],['criminal','Dark / criminal testimony'],['conspiracion','Revealed conspiracy'],['secta','Cult or sect escape'],['sobrenatural','Supernatural event']]},
  'style':{es:[['random','🎲 Aleatorio'],['confesional','Confesional / íntimo'],['perturbador','Perturbador / oscuro'],['emocional','Emocional / cargado'],['fragmentado','Fragmentado / disociado']],en:[['random','🎲 Random'],['confesional','Confessional / intimate'],['perturbador','Disturbing / dark'],['emocional','Emotional / heavy'],['fragmentado','Fragmented / dissociated']]},
  'tone':{es:[['random','🎲 Aleatorio'],['tembloroso','Tembloroso / asustado'],['frio','Frío / distante'],['desesperado','Desesperado / urgente'],['cauteloso','Cauteloso / susurrado']],en:[['random','🎲 Random'],['tembloroso','Trembling / scared'],['frio','Cold / distant'],['desesperado','Desperate / urgent'],['cauteloso','Cautious / whispered']]}
},
'reflexion-biblica':{
  'narrator-type':{es:[['random','🎲 Aleatorio'],['pastor','Pastor cercano'],['narrador-sereno','Narrador sereno'],['predicador','Predicador inspirador'],['anciano-sabio','Anciano sabio'],['voz-suave','Voz suave femenina']],en:[['random','🎲 Random'],['pastor','Warm pastor'],['narrador-sereno','Serene narrator'],['predicador','Inspiring preacher'],['anciano-sabio','Wise elder'],['voz-suave','Soft female voice']]},
  'narrator-gender':{es:[['random','🎲 Aleatorio'],['male','Masculino'],['female','Femenino']],en:[['random','🎲 Random'],['male','Male'],['female','Female']]},
  'category':{es:[['random','🎲 Aleatorio'],['fe-esperanza','Fe y esperanza'],['palabras-aliento','Palabras de aliento'],['promesas-dios','Promesas de Dios'],['fortaleza','Fortaleza y perseverancia'],['amor-compasion','Amor y compasión'],['sanacion','Sanación y restauración'],['proposito','Propósito y llamado']],en:[['random','🎲 Random'],['fe-esperanza','Faith and hope'],['palabras-aliento','Words of encouragement'],['promesas-dios','God\'s promises'],['fortaleza','Strength and perseverance'],['amor-compasion','Love and compassion'],['sanacion','Healing and restoration'],['proposito','Purpose and calling']]},
  'style':{es:[['random','🎲 Aleatorio'],['devocional','Devocional / íntimo'],['inspirador','Inspirador / motivacional'],['reflexivo','Reflexivo / contemplativo'],['esperanzador','Esperanzador / luminoso']],en:[['random','🎲 Random'],['devocional','Devotional / intimate'],['inspirador','Inspiring / motivational'],['reflexivo','Reflective / contemplative'],['esperanzador','Hopeful / luminous']]},
  'tone':{es:[['random','🎲 Aleatorio'],['sereno','Sereno / calmado'],['amoroso','Amoroso / cálido'],['solemne','Solemne / reverente'],['alentador','Alentador / energizante']],en:[['random','🎲 Random'],['sereno','Serene / calm'],['amoroso','Loving / warm'],['solemne','Solemn / reverent'],['alentador','Encouraging / energizing']]}
},
'ciencia-misterio':{
  'narrator-type':{es:[['random','🎲 Aleatorio'],['divulgador','Divulgador científico'],['astronomo','Astrónomo apasionado'],['biologo','Biólogo marino'],['fisico','Físico cuántico'],['explorador','Explorador de lo desconocido']],en:[['random','🎲 Random'],['divulgador','Science communicator'],['astronomo','Passionate astronomer'],['biologo','Marine biologist'],['fisico','Quantum physicist'],['explorador','Explorer of the unknown']]},
  'narrator-gender':{es:[['random','🎲 Aleatorio'],['male','Masculino'],['female','Femenino']],en:[['random','🎲 Random'],['male','Male'],['female','Female']]},
  'category':{es:[['random','🎲 Aleatorio'],['universo','Misterios del universo y astronomía'],['oceano','Secretos del océano profundo'],['fisica-cuantica','Física cuántica y realidad'],['evolucion','Evolución y animales extraordinarios'],['fenomenos','Fenómenos naturales extremos'],['cerebro','Psicología y el cerebro humano'],['tiempo','Tiempo, física y realidad']],en:[['random','🎲 Random'],['universo','Universe mysteries and astronomy'],['oceano','Deep ocean secrets'],['fisica-cuantica','Quantum physics and reality'],['evolucion','Evolution and extraordinary animals'],['fenomenos','Extreme natural phenomena'],['cerebro','Psychology and the human brain'],['tiempo','Time, physics and reality']]},
  'style':{es:[['random','🎲 Aleatorio'],['revelador','Revelador / asombroso'],['educativo','Educativo / divulgativo'],['reflexivo','Reflexivo / filosófico'],['impactante','Impactante / viral']],en:[['random','🎲 Random'],['revelador','Revealing / amazing'],['educativo','Educational'],['reflexivo','Reflective / philosophical'],['impactante','Shocking / viral']]},
  'tone':{es:[['random','🎲 Aleatorio'],['fascinado','Fascinado / maravillado'],['analitico','Analítico / preciso'],['filosofico','Filosófico / profundo'],['dramatico','Dramático / cinematográfico']],en:[['random','🎲 Random'],['fascinado','Fascinated / amazed'],['analitico','Analytical / precise'],['filosofico','Philosophical / deep'],['dramatico','Dramatic / cinematic']]}
},
'true-crime':{
  'host-type':{es:[['random','🎲 Aleatorio'],['detective-retirado','Detective retirado'],['periodista-crimen','Periodista de crimen'],['fiscal-investigador','Fiscal investigador'],['profiler','Profiler / perfilador criminal'],['investigador-privado','Investigador privado']],en:[['random','🎲 Random'],['detective-retirado','Retired detective'],['periodista-crimen','Crime journalist'],['fiscal-investigador','Investigative prosecutor'],['profiler','Criminal profiler'],['investigador-privado','Private investigator']]},
  'host-gender':{es:[['random','🎲 Aleatorio'],['male','Masculino'],['female','Femenino']],en:[['random','🎲 Random'],['male','Male'],['female','Female']]},
  'host-region':{es:[['random','🎲 Aleatorio'],['latam-neutro','Latinoamérica (neutro)'],['mexico-centroam','México / Centroamérica'],['caribe','Caribe'],['sudamerica','Sudamérica'],['espana','España']],en:[['random','🎲 Random'],['latam-neutro','Latin America (neutral)'],['mexico-centroam','Mexico / Central America'],['caribe','Caribbean'],['sudamerica','South America'],['espana','Spain']]},
  'guest-type':{es:[['random','🎲 Aleatorio'],['testigo-ocular','Testigo ocular directo'],['familiar-victima','Familiar de la víctima'],['sospechoso-absuelto','Sospechoso absuelto'],['sobreviviente','Sobreviviente del crimen'],['complice-arrepentido','Cómplice arrepentido'],['exrecluso','Exrecluso con secreto']],en:[['random','🎲 Random'],['testigo-ocular','Direct eyewitness'],['familiar-victima','Victim\'s family member'],['sospechoso-absuelto','Acquitted suspect'],['sobreviviente','Crime survivor'],['complice-arrepentido','Repentant accomplice'],['exrecluso','Ex-convict with a secret']]},
  'guest-gender':{es:[['random','🎲 Aleatorio'],['female','Femenino'],['male','Masculino']],en:[['random','🎲 Random'],['female','Female'],['male','Male']]},
  'guest-region':{es:[['random','🎲 Aleatorio'],['latam-general','Latinoamérica'],['mexico-centroam','México / Centroamérica'],['caribe','Caribe'],['sudamerica','Sudamérica'],['espana-europa','España / Europa'],['internacional','Internacional']],en:[['random','🎲 Random'],['latam-general','Latin America'],['mexico-centroam','Mexico / Central America'],['caribe','Caribbean'],['sudamerica','South America'],['espana-europa','Spain / Europe'],['internacional','International']]},
  'guest-age':{es:[['random','🎲 Aleatorio'],['18-25','18-25'],['25-35','25-35'],['35-50','35-50'],['50-70','50-70']],en:[['random','🎲 Random'],['18-25','18-25'],['25-35','25-35'],['35-50','35-50'],['50-70','50-70']]},
  'style':{es:[['random','🎲 Aleatorio'],['interrogatorio','Interrogatorio frío'],['revelador','Revelación escalofriante'],['procesal','Procesal / periodístico'],['psicologico','Análisis psicológico']],en:[['random','🎲 Random'],['interrogatorio','Cold interrogation'],['revelador','Chilling revelation'],['procesal','Procedural / journalistic'],['psicologico','Psychological analysis']]},
  'tone':{es:[['random','🎲 Aleatorio'],['tenso-frio','Tenso / frío'],['urgente','Urgente / alarmante'],['calculado','Calculado / preciso'],['emocional','Emocional / pesado']],en:[['random','🎲 Random'],['tenso-frio','Tense / cold'],['urgente','Urgent / alarming'],['calculado','Calculated / precise'],['emocional','Emotional / heavy']]}
},
'psicologia-oscura':{
  'host-type':{es:[['random','🎲 Aleatorio'],['psicologo-clinico','Psicólogo clínico'],['coach-recuperacion','Coach de recuperación'],['terapeuta-trauma','Terapeuta de trauma'],['investigador-forense','Investigador forense'],['divulgador-psico','Divulgador de psicología']],en:[['random','🎲 Random'],['psicologo-clinico','Clinical psychologist'],['coach-recuperacion','Recovery coach'],['terapeuta-trauma','Trauma therapist'],['investigador-forense','Forensic researcher'],['divulgador-psico','Psychology communicator']]},
  'host-gender':{es:[['random','🎲 Aleatorio'],['male','Masculino'],['female','Femenino']],en:[['random','🎲 Random'],['male','Male'],['female','Female']]},
  'host-region':{es:[['random','🎲 Aleatorio'],['latam-neutro','Latinoamérica (neutro)'],['mexico-centroam','México / Centroamérica'],['sudamerica','Sudamérica'],['espana','España']],en:[['random','🎲 Random'],['latam-neutro','Latin America (neutral)'],['mexico-centroam','Mexico / Central America'],['sudamerica','South America'],['espana','Spain']]},
  'guest-type':{es:[['random','🎲 Aleatorio'],['sobreviviente-narcisista','Sobreviviente de narcisista'],['expareja-toxica','Expareja de relación tóxica'],['victima-manipulacion','Víctima de manipulación'],['exmanipulador','Ex manipulador / narcisista'],['recuperado-secta','Recuperado de secta o culto']],en:[['random','🎲 Random'],['sobreviviente-narcisista','Narcissist survivor'],['expareja-toxica','Toxic relationship ex-partner'],['victima-manipulacion','Manipulation victim'],['exmanipulador','Ex manipulator / narcissist'],['recuperado-secta','Cult recovery survivor']]},
  'guest-gender':{es:[['random','🎲 Aleatorio'],['female','Femenino'],['male','Masculino']],en:[['random','🎲 Random'],['female','Female'],['male','Male']]},
  'guest-region':{es:[['random','🎲 Aleatorio'],['latam-general','Latinoamérica'],['mexico-centroam','México / Centroamérica'],['caribe','Caribe'],['sudamerica','Sudamérica'],['espana-europa','España / Europa'],['internacional','Internacional']],en:[['random','🎲 Random'],['latam-general','Latin America'],['mexico-centroam','Mexico / Central America'],['caribe','Caribbean'],['sudamerica','South America'],['espana-europa','Spain / Europe'],['internacional','International']]},
  'guest-age':{es:[['random','🎲 Aleatorio'],['18-25','18-25'],['25-35','25-35'],['35-50','35-50'],['50-70','50-70']],en:[['random','🎲 Random'],['18-25','18-25'],['25-35','25-35'],['35-50','35-50'],['50-70','50-70']]},
  'style':{es:[['random','🎲 Aleatorio'],['revelador','Revelador / perturbador'],['educativo-oscuro','Educativo / oscuro'],['confesional','Confesional íntimo'],['analitico','Analítico clínico']],en:[['random','🎲 Random'],['revelador','Revealing / disturbing'],['educativo-oscuro','Educational / dark'],['confesional','Intimate confessional'],['analitico','Clinical analytical']]},
  'tone':{es:[['random','🎲 Aleatorio'],['intenso','Intenso / perturbador'],['frio-analitico','Frío / analítico'],['empatico-pesado','Empático / pesado'],['calculado','Calculado / controlado']],en:[['random','🎲 Random'],['intenso','Intense / disturbing'],['frio-analitico','Cold / analytical'],['empatico-pesado','Empathetic / heavy'],['calculado','Calculated / controlled']]}
},
'conspiracion-moderna':{
  'host-type':{es:[['random','🎲 Aleatorio'],['periodista-investigador','Periodista investigador'],['analista-datos','Analista de datos'],['investigador-independiente','Investigador independiente'],['activista-digital','Activista digital'],['youtuber-critico','Creador de contenido crítico']],en:[['random','🎲 Random'],['periodista-investigador','Investigative journalist'],['analista-datos','Data analyst'],['investigador-independiente','Independent researcher'],['activista-digital','Digital activist'],['youtuber-critico','Critical content creator']]},
  'host-gender':{es:[['random','🎲 Aleatorio'],['male','Masculino'],['female','Femenino']],en:[['random','🎲 Random'],['male','Male'],['female','Female']]},
  'host-region':{es:[['random','🎲 Aleatorio'],['latam-neutro','Latinoamérica (neutro)'],['mexico-centroam','México / Centroamérica'],['sudamerica','Sudamérica'],['espana','España'],['eeuu-hispano','EE.UU. hispano']],en:[['random','🎲 Random'],['latam-neutro','Latin America (neutral)'],['mexico-centroam','Mexico / Central America'],['sudamerica','South America'],['espana','Spain'],['eeuu-hispano','US Hispanic']]},
  'guest-type':{es:[['random','🎲 Aleatorio'],['informante-tech','Informante tecnológico'],['ex-empleado-faang','Ex empleado de Google/Meta/Apple'],['hacker-etico','Hacker ético'],['analista-inteligencia','Analista de inteligencia retirado'],['experto-vigilancia','Experto en vigilancia digital'],['denunciante','Denunciante / whistleblower']],en:[['random','🎲 Random'],['informante-tech','Tech whistleblower'],['ex-empleado-faang','Ex Google/Meta/Apple employee'],['hacker-etico','Ethical hacker'],['analista-inteligencia','Retired intelligence analyst'],['experto-vigilancia','Digital surveillance expert'],['denunciante','Whistleblower']]},
  'guest-gender':{es:[['random','🎲 Aleatorio'],['male','Masculino'],['female','Femenino']],en:[['random','🎲 Random'],['male','Male'],['female','Female']]},
  'guest-region':{es:[['random','🎲 Aleatorio'],['latam-general','Latinoamérica'],['eeuu-hispano','EE.UU. hispano'],['espana-europa','España / Europa'],['internacional','Internacional / anónimo']],en:[['random','🎲 Random'],['latam-general','Latin America'],['eeuu-hispano','US Hispanic'],['espana-europa','Spain / Europe'],['internacional','International / anonymous']]},
  'guest-age':{es:[['random','🎲 Aleatorio'],['25-35','25-35'],['35-50','35-50'],['50-70','50-70']],en:[['random','🎲 Random'],['25-35','25-35'],['35-50','35-50'],['50-70','50-70']]},
  'style':{es:[['random','🎲 Aleatorio'],['paranoico-urgente','Paranoico / urgente'],['analitico-preciso','Analítico / preciso'],['revelador-impactante','Revelador / impactante'],['periodistico','Periodístico / frío']],en:[['random','🎲 Random'],['paranoico-urgente','Paranoid / urgent'],['analitico-preciso','Analytical / precise'],['revelador-impactante','Revealing / shocking'],['periodistico','Journalistic / cold']]},
  'tone':{es:[['random','🎲 Aleatorio'],['tenso','Tenso / presionado'],['urgente','Urgente / alarmante'],['calculado','Calculado / susurrado'],['conspirativo','Conspirativo / desconfiado']],en:[['random','🎲 Random'],['tenso','Tense / pressured'],['urgente','Urgent / alarming'],['calculado','Calculated / whispered'],['conspirativo','Conspiratorial / suspicious']]}
},
'finanzas-libertad':{
  'narrator-type':{es:[['random','🎲 Aleatorio'],['coach-financiero','Coach financiero'],['inversor-exitoso','Inversor exitoso autodidacta'],['economista-viral','Economista divulgador'],['emprendedor','Emprendedor millonario'],['ex-endeudado','Persona que salió de deudas']],en:[['random','🎲 Random'],['coach-financiero','Financial coach'],['inversor-exitoso','Self-taught successful investor'],['economista-viral','Viral economist'],['emprendedor','Millionaire entrepreneur'],['ex-endeudado','Debt-free success story']]},
  'narrator-gender':{es:[['random','🎲 Aleatorio'],['male','Masculino'],['female','Femenino']],en:[['random','🎲 Random'],['male','Male'],['female','Female']]},
  'category':{es:[['random','🎲 Aleatorio'],['inversion','Inversión y bolsa'],['ahorro','Ahorro e independencia'],['mentalidad-riqueza','Mentalidad de riqueza'],['ingresos-pasivos','Ingresos pasivos'],['deudas','Salir de deudas'],['emprendimiento','Emprendimiento viral']],en:[['random','🎲 Random'],['inversion','Investment and stocks'],['ahorro','Savings and independence'],['mentalidad-riqueza','Wealth mindset'],['ingresos-pasivos','Passive income'],['deudas','Getting out of debt'],['emprendimiento','Viral entrepreneurship']]},
  'style':{es:[['random','🎲 Aleatorio'],['revelador','Revelador / sorprendente'],['practico','Práctico / accionable'],['motivacional','Motivacional / inspirador'],['directo','Directo / sin filtros']],en:[['random','🎲 Random'],['revelador','Revealing / surprising'],['practico','Practical / actionable'],['motivacional','Motivational / inspiring'],['directo','Direct / no filter']]},
  'tone':{es:[['random','🎲 Aleatorio'],['urgente','Urgente / despertador'],['amigable','Amigable / cercano'],['intenso','Intenso / enérgico'],['sereno','Sereno / sabio']],en:[['random','🎲 Random'],['urgente','Urgent / wake-up call'],['amigable','Friendly / relatable'],['intenso','Intense / energetic'],['sereno','Calm / wise']]}
},
'mentalidad-disciplina':{
  'narrator-type':{es:[['random','🎲 Aleatorio'],['coach-motivacional','Coach motivacional'],['atleta-elite','Atleta de élite'],['emprendedor-resiliente','Emprendedor resiliente'],['filosofo-moderno','Filósofo moderno'],['militar-liderazgo','Ex militar / liderazgo']],en:[['random','🎲 Random'],['coach-motivacional','Motivational coach'],['atleta-elite','Elite athlete'],['emprendedor-resiliente','Resilient entrepreneur'],['filosofo-moderno','Modern philosopher'],['militar-liderazgo','Ex military / leadership']]},
  'narrator-gender':{es:[['random','🎲 Aleatorio'],['male','Masculino'],['female','Femenino']],en:[['random','🎲 Random'],['male','Male'],['female','Female']]},
  'category':{es:[['random','🎲 Aleatorio'],['disciplina','Disciplina y constancia'],['habitos','Hábitos que transforman'],['resiliencia','Resiliencia y adversidad'],['mentalidad-ganadora','Mentalidad ganadora'],['zona-confort','Salir de la zona de confort'],['proposito','Propósito y dirección']],en:[['random','🎲 Random'],['disciplina','Discipline and consistency'],['habitos','Life-changing habits'],['resiliencia','Resilience and adversity'],['mentalidad-ganadora','Winner mindset'],['zona-confort','Leaving the comfort zone'],['proposito','Purpose and direction']]},
  'style':{es:[['random','🎲 Aleatorio'],['brutal-honesto','Brutal y honesto'],['inspirador','Inspirador / épico'],['narrativo','Historia real de superación'],['filosofico','Filosófico / reflexivo']],en:[['random','🎲 Random'],['brutal-honesto','Brutally honest'],['inspirador','Inspiring / epic'],['narrativo','Real overcoming story'],['filosofico','Philosophical / reflective']]},
  'tone':{es:[['random','🎲 Aleatorio'],['fuego','De fuego / urgente'],['sereno-poderoso','Sereno pero poderoso'],['directo','Directo al alma'],['epico','Épico / cinematográfico']],en:[['random','🎲 Random'],['fuego','On fire / urgent'],['sereno-poderoso','Calm but powerful'],['directo','Direct to the soul'],['epico','Epic / cinematic']]}
},
'historia-epica':{
  'narrator-type':{es:[['random','🎲 Aleatorio'],['historiador-apasionado','Historiador apasionado'],['narrador-cinematografico','Narrador cinematográfico'],['cronista-epico','Cronista épico'],['arqueólogo','Arqueólogo aventurero']],en:[['random','🎲 Random'],['historiador-apasionado','Passionate historian'],['narrador-cinematografico','Cinematic narrator'],['cronista-epico','Epic chronicler'],['arqueólogo','Adventure archaeologist']]},
  'narrator-gender':{es:[['random','🎲 Aleatorio'],['male','Masculino'],['female','Femenino']],en:[['random','🎲 Random'],['male','Male'],['female','Female']]},
  'category':{es:[['random','🎲 Aleatorio'],['batallas','Batallas épicas históricas'],['imperios','Imperios y su caída'],['heroes-olvidados','Héroes olvidados'],['revoluciones','Revoluciones que cambiaron el mundo'],['figuras-extraordinarias','Figuras extraordinarias'],['civilizaciones','Civilizaciones asombrosas']],en:[['random','🎲 Random'],['batallas','Epic historical battles'],['imperios','Empires and their fall'],['heroes-olvidados','Forgotten heroes'],['revoluciones','World-changing revolutions'],['figuras-extraordinarias','Extraordinary figures'],['civilizaciones','Amazing civilizations']]},
  'style':{es:[['random','🎲 Aleatorio'],['epico','Épico / grandioso'],['revelador','Revelador / sorprendente'],['dramatico','Dramático / cinematográfico'],['educativo','Educativo / fascinante']],en:[['random','🎲 Random'],['epico','Epic / grandiose'],['revelador','Revealing / surprising'],['dramatico','Dramatic / cinematic'],['educativo','Educational / fascinating']]},
  'tone':{es:[['random','🎲 Aleatorio'],['apasionado','Apasionado / encendido'],['solemne','Solemne / grandioso'],['urgente','Urgente / impactante'],['narrativo','Narrativo / íntimo']],en:[['random','🎲 Random'],['apasionado','Passionate / fired up'],['solemne','Solemn / grand'],['urgente','Urgent / impactful'],['narrativo','Narrative / intimate']]}
},
'psicologia-positiva':{
  'narrator-type':{es:[['random','🎲 Aleatorio'],['psicologa-empatica','Psicóloga empática'],['terapeuta-cercana','Terapeuta cercana'],['coach-bienestar','Coach de bienestar'],['voz-amiga','Voz de amiga que sana'],['experto-apego','Experto en apego y vínculos']],en:[['random','🎲 Random'],['psicologa-empatica','Empathetic psychologist'],['terapeuta-cercana','Warm therapist'],['coach-bienestar','Wellness coach'],['voz-amiga','Healing friend voice'],['experto-apego','Attachment & bonding expert']]},
  'narrator-gender':{es:[['random','🎲 Aleatorio'],['female','Femenino'],['male','Masculino']],en:[['random','🎲 Random'],['female','Female'],['male','Male']]},
  'category':{es:[['random','🎲 Aleatorio'],['autoestima','Autoestima y amor propio'],['sanacion-emocional','Sanación emocional'],['limites','Límites y autorespeto'],['apego','Estilos de apego y relaciones'],['ansiedad','Ansiedad y regulación emocional'],['duelo','Duelo y cierre emocional'],['autocuidado','Autocuidado y bienestar']],en:[['random','🎲 Random'],['autoestima','Self-esteem and self-love'],['sanacion-emocional','Emotional healing'],['limites','Boundaries and self-respect'],['apego','Attachment styles and relationships'],['ansiedad','Anxiety and emotional regulation'],['duelo','Grief and emotional closure'],['autocuidado','Self-care and well-being']]},
  'style':{es:[['random','🎲 Aleatorio'],['reconfortante','Reconfortante / sanador'],['revelador','Revelador / que abre los ojos'],['practico','Práctico / con pasos concretos'],['narrativo','Narrativo / historia personal']],en:[['random','🎲 Random'],['reconfortante','Comforting / healing'],['revelador','Eye-opening / revealing'],['practico','Practical / with concrete steps'],['narrativo','Narrative / personal story']]},
  'tone':{es:[['random','🎲 Aleatorio'],['calido-cercano','Cálido / cercano'],['suave-poderoso','Suave pero poderoso'],['esperanzador','Esperanzador / luminoso'],['directo-amoroso','Directo y amoroso']],en:[['random','🎲 Random'],['calido-cercano','Warm / close'],['suave-poderoso','Soft but powerful'],['esperanzador','Hopeful / luminous'],['directo-amoroso','Direct and loving']]}
},
'mente-masculina':{
  'narrator-type':{es:[['random','🎲 Aleatorio'],['coach-masculino','Coach de vida masculino'],['mentor-emocional','Mentor emocional'],['psicologo-masculino','Psicólogo / terapeuta'],['hombre-vivencia','Hombre con vivencia propia'],['voz-reflexiva','Voz reflexiva anónima']],en:[['random','🎲 Random'],['coach-masculino','Masculine life coach'],['mentor-emocional','Emotional mentor'],['psicologo-masculino','Psychologist / therapist'],['hombre-vivencia','Man sharing personal experience'],['voz-reflexiva','Anonymous reflective voice']]},
  'narrator-gender':{es:[['male','Masculino'],['random','🎲 Aleatorio'],['female','Femenino']],en:[['male','Male'],['random','🎲 Random'],['female','Female']]},
  'category':{es:[['random','🎲 Aleatorio'],['emociones-masculinas','Emociones & vulnerabilidad masculina'],['amor-propio','Amor propio & autoestima'],['relaciones','Relaciones & pareja'],['proposito-identidad','Propósito & identidad'],['sanacion','Sanación & heridas del pasado'],['soledad','Soledad & conexión'],['fuerza-interior','Fuerza interior & resiliencia']],en:[['random','🎲 Random'],['emociones-masculinas','Emotions & male vulnerability'],['amor-propio','Self-love & self-esteem'],['relaciones','Relationships & romantic life'],['proposito-identidad','Purpose & identity'],['sanacion','Healing & past wounds'],['soledad','Loneliness & connection'],['fuerza-interior','Inner strength & resilience']]},
  'style':{es:[['random','🎲 Aleatorio'],['reflexivo-profundo','Reflexivo / profundo'],['directo-al-alma','Directo al alma'],['cinematografico','Cinematográfico / poético'],['confesional','Confesional / íntimo'],['motivacional','Motivacional / que activa']],en:[['random','🎲 Random'],['reflexivo-profundo','Reflective / deep'],['directo-al-alma','Direct to the soul'],['cinematografico','Cinematic / poetic'],['confesional','Confessional / intimate'],['motivacional','Motivational / activating']]},
  'tone':{es:[['random','🎲 Aleatorio'],['sereno-poderoso','Sereno pero poderoso'],['vulnerable-honesto','Vulnerable y honesto'],['directo-firme','Directo y firme'],['epico-profundo','Épico / profundo'],['calido-masculino','Cálido / masculino']],en:[['random','🎲 Random'],['sereno-poderoso','Calm but powerful'],['vulnerable-honesto','Vulnerable and honest'],['directo-firme','Direct and firm'],['epico-profundo','Epic / deep'],['calido-masculino','Warm / masculine']]}
},
'mujer-consciente':{
  'narrator-type':{es:[['random','🎲 Aleatorio'],['coach-femenina','Coach de vida femenina'],['mentora-emocional','Mentora emocional'],['psicologa','Psicóloga / terapeuta'],['mujer-vivencia','Mujer con vivencia propia'],['voz-reflexiva','Voz reflexiva anónima']],en:[['random','🎲 Random'],['coach-femenina','Feminine life coach'],['mentora-emocional','Emotional mentor'],['psicologa','Psychologist / therapist'],['mujer-vivencia','Woman sharing personal experience'],['voz-reflexiva','Anonymous reflective voice']]},
  'narrator-gender':{es:[['female','Femenino'],['random','🎲 Aleatorio'],['male','Masculino']],en:[['female','Female'],['random','🎲 Random'],['male','Male']]},
  'category':{es:[['random','🎲 Aleatorio'],['empoderamiento','Empoderamiento & fuerza femenina'],['amor-propio','Amor propio & autoestima'],['relaciones','Relaciones & pareja'],['sanacion','Sanación & heridas del pasado'],['limites','Límites & independencia'],['maternidad-identidad','Maternidad & identidad'],['proposito','Propósito & esencia propia']],en:[['random','🎲 Random'],['empoderamiento','Empowerment & feminine strength'],['amor-propio','Self-love & self-worth'],['relaciones','Relationships & romantic life'],['sanacion','Healing & past wounds'],['limites','Boundaries & independence'],['maternidad-identidad','Motherhood & identity'],['proposito','Purpose & true self']]},
  'style':{es:[['random','🎲 Aleatorio'],['reflexivo-profundo','Reflexivo / profundo'],['directo-al-alma','Directo al alma'],['poetico-cinematografico','Poético / cinematográfico'],['confesional','Confesional / íntimo'],['empoderador','Empoderador / que activa']],en:[['random','🎲 Random'],['reflexivo-profundo','Reflective / deep'],['directo-al-alma','Direct to the soul'],['poetico-cinematografico','Poetic / cinematic'],['confesional','Confessional / intimate'],['empoderador','Empowering / activating']]},
  'tone':{es:[['random','🎲 Aleatorio'],['calido-poderoso','Cálido pero poderoso'],['vulnerable-honesto','Vulnerable y honesto'],['empoderador-firme','Empoderador y firme'],['poetico-suave','Poético / suave'],['directo-amoroso','Directo y amoroso']],en:[['random','🎲 Random'],['calido-poderoso','Warm but powerful'],['vulnerable-honesto','Vulnerable and honest'],['empoderador-firme','Empowering and firm'],['poetico-suave','Poetic / gentle'],['directo-amoroso','Direct and loving']]}
}
};

const MODE_BLOCKS={
'ficticio-viral':[
  {id:'host-block',title:{es:'Host del podcast',en:'Podcast host'},fields:[{id:'host-type',label:{es:'Perfil',en:'Profile'}},{id:'host-gender',label:{es:'Género',en:'Gender'}},{id:'host-region',label:{es:'Región / acento',en:'Region / accent'}}]},
  {id:'guest-block',title:{es:'Invitado',en:'Guest'},fields:[{id:'guest-type',label:{es:'Arquetipo',en:'Archetype'}},{id:'guest-gender',label:{es:'Género',en:'Gender'}},{id:'guest-region',label:{es:'Región de origen',en:'Region of origin'}},{id:'guest-age',label:{es:'Rango de edad',en:'Age range'}}]}
],
'misterio-biblico':[
  {id:'narrator-block',title:{es:'Narrador / Erudito',en:'Narrator / Scholar'},fields:[{id:'narrator-type',label:{es:'Tipo',en:'Type'}},{id:'narrator-gender',label:{es:'Género',en:'Gender'}},{id:'narrator-lang',label:{es:'Idioma audio',en:'Audio language'}}]},
  {id:'scene-block',title:{es:'Escena y sub-tema',en:'Scene & sub-topic'},fields:[{id:'scene-type',label:{es:'Escenario visual',en:'Visual scene'}},{id:'subtopic',label:{es:'Sub-tema',en:'Sub-topic'}}]}
],
'libro-rapido':[
  {id:'book-narrator-block',title:{es:'Narrador',en:'Narrator'},fields:[{id:'narrator-type',label:{es:'Tipo de narrador',en:'Narrator type'}},{id:'narrator-gender',label:{es:'Género',en:'Gender'}}]},
  {id:'book-block',title:{es:'El libro',en:'The book'},fields:[{id:'book-genre',label:{es:'Género del libro',en:'Book genre'}}]}
],
'documental-narrado':[
  {id:'doc-narrator-block',title:{es:'Narrador',en:'Narrator'},fields:[{id:'narrator-type',label:{es:'Tipo',en:'Type'}},{id:'narrator-gender',label:{es:'Género',en:'Gender'}}]},
  {id:'doc-theme-block',title:{es:'Temática y estilo',en:'Theme & style'},fields:[{id:'category',label:{es:'Categoría',en:'Category'}},{id:'style',label:{es:'Estilo',en:'Style'}},{id:'tone',label:{es:'Tono',en:'Tone'}}]}
],
'testimonio-real':[
  {id:'test-narrator-block',title:{es:'Narrador / Testigo',en:'Narrator / Witness'},fields:[{id:'narrator-type',label:{es:'Tipo de voz',en:'Voice type'}},{id:'narrator-gender',label:{es:'Género',en:'Gender'}}]},
  {id:'test-theme-block',title:{es:'Tipo de testimonio',en:'Testimony type'},fields:[{id:'category',label:{es:'Categoría',en:'Category'}},{id:'style',label:{es:'Estilo',en:'Style'}},{id:'tone',label:{es:'Tono',en:'Tone'}}]}
],
'reflexion-biblica':[
  {id:'ref-narrator-block',title:{es:'Narrador',en:'Narrator'},fields:[{id:'narrator-type',label:{es:'Tipo de voz',en:'Voice type'}},{id:'narrator-gender',label:{es:'Género',en:'Gender'}}]},
  {id:'ref-theme-block',title:{es:'Temática',en:'Theme'},fields:[{id:'category',label:{es:'Categoría',en:'Category'}},{id:'style',label:{es:'Estilo',en:'Style'}},{id:'tone',label:{es:'Tono',en:'Tone'}}]}
],
'ciencia-misterio':[
  {id:'sci-narrator-block',title:{es:'Narrador científico',en:'Scientific narrator'},fields:[{id:'narrator-type',label:{es:'Tipo',en:'Type'}},{id:'narrator-gender',label:{es:'Género',en:'Gender'}}]},
  {id:'sci-theme-block',title:{es:'Temática científica',en:'Science theme'},fields:[{id:'category',label:{es:'Categoría',en:'Category'}},{id:'style',label:{es:'Estilo',en:'Style'}},{id:'tone',label:{es:'Tono',en:'Tone'}}]}
],
'true-crime':[
  {id:'tc-host-block',title:{es:'Investigador / Host',en:'Investigator / Host'},fields:[{id:'host-type',label:{es:'Perfil',en:'Profile'}},{id:'host-gender',label:{es:'Género',en:'Gender'}},{id:'host-region',label:{es:'Región',en:'Region'}}]},
  {id:'tc-guest-block',title:{es:'Testigo / Involucrado',en:'Witness / Involved'},fields:[{id:'guest-type',label:{es:'Rol',en:'Role'}},{id:'guest-gender',label:{es:'Género',en:'Gender'}},{id:'guest-region',label:{es:'Región de origen',en:'Region of origin'}},{id:'guest-age',label:{es:'Edad',en:'Age'}}]}
],
'psicologia-oscura':[
  {id:'ps-host-block',title:{es:'Experto / Host',en:'Expert / Host'},fields:[{id:'host-type',label:{es:'Perfil',en:'Profile'}},{id:'host-gender',label:{es:'Género',en:'Gender'}},{id:'host-region',label:{es:'Región',en:'Region'}}]},
  {id:'ps-guest-block',title:{es:'Sobreviviente / Invitado',en:'Survivor / Guest'},fields:[{id:'guest-type',label:{es:'Perfil',en:'Profile'}},{id:'guest-gender',label:{es:'Género',en:'Gender'}},{id:'guest-region',label:{es:'Región',en:'Region'}},{id:'guest-age',label:{es:'Edad',en:'Age'}}]}
],
'conspiracion-moderna':[
  {id:'cm-host-block',title:{es:'Periodista / Host',en:'Journalist / Host'},fields:[{id:'host-type',label:{es:'Perfil',en:'Profile'}},{id:'host-gender',label:{es:'Género',en:'Gender'}},{id:'host-region',label:{es:'Región',en:'Region'}}]},
  {id:'cm-guest-block',title:{es:'Informante / Invitado',en:'Whistleblower / Guest'},fields:[{id:'guest-type',label:{es:'Rol',en:'Role'}},{id:'guest-gender',label:{es:'Género',en:'Gender'}},{id:'guest-region',label:{es:'Región / anonimato',en:'Region / anonymity'}},{id:'guest-age',label:{es:'Edad',en:'Age'}}]}
],
'finanzas-libertad':[
  {id:'fin-narrator-block',title:{es:'Narrador',en:'Narrator'},fields:[{id:'narrator-type',label:{es:'Perfil',en:'Profile'}},{id:'narrator-gender',label:{es:'Género',en:'Gender'}}]},
  {id:'fin-theme-block',title:{es:'Temática financiera',en:'Financial theme'},fields:[{id:'category',label:{es:'Categoría',en:'Category'}},{id:'style',label:{es:'Estilo',en:'Style'}},{id:'tone',label:{es:'Tono',en:'Tone'}}]}
],
'mentalidad-disciplina':[
  {id:'men-narrator-block',title:{es:'Narrador / Coach',en:'Narrator / Coach'},fields:[{id:'narrator-type',label:{es:'Perfil',en:'Profile'}},{id:'narrator-gender',label:{es:'Género',en:'Gender'}}]},
  {id:'men-theme-block',title:{es:'Temática',en:'Theme'},fields:[{id:'category',label:{es:'Categoría',en:'Category'}},{id:'style',label:{es:'Estilo',en:'Style'}},{id:'tone',label:{es:'Tono',en:'Tone'}}]}
],
'historia-epica':[
  {id:'his-narrator-block',title:{es:'Narrador épico',en:'Epic narrator'},fields:[{id:'narrator-type',label:{es:'Perfil',en:'Profile'}},{id:'narrator-gender',label:{es:'Género',en:'Gender'}}]},
  {id:'his-theme-block',title:{es:'Temática histórica',en:'Historic theme'},fields:[{id:'category',label:{es:'Categoría',en:'Category'}},{id:'style',label:{es:'Estilo',en:'Style'}},{id:'tone',label:{es:'Tono',en:'Tone'}}]}
],
'psicologia-positiva':[
  {id:'pp-narrator-block',title:{es:'Narrador / Terapeuta',en:'Narrator / Therapist'},fields:[{id:'narrator-type',label:{es:'Perfil',en:'Profile'}},{id:'narrator-gender',label:{es:'Género',en:'Gender'}}]},
  {id:'pp-theme-block',title:{es:'Temática',en:'Theme'},fields:[{id:'category',label:{es:'Categoría',en:'Category'}},{id:'style',label:{es:'Estilo',en:'Style'}},{id:'tone',label:{es:'Tono',en:'Tone'}}]}
],
'mente-masculina':[
  {id:'mm-narrator-block',title:{es:'Narrador / Mentor',en:'Narrator / Mentor'},fields:[{id:'narrator-type',label:{es:'Perfil',en:'Profile'}},{id:'narrator-gender',label:{es:'Género',en:'Gender'}}]},
  {id:'mm-theme-block',title:{es:'Temática masculina',en:'Masculine theme'},fields:[{id:'category',label:{es:'Categoría',en:'Category'}},{id:'style',label:{es:'Estilo',en:'Style'}},{id:'tone',label:{es:'Tono',en:'Tone'}}]}
],
'mujer-consciente':[
  {id:'mc-narrator-block',title:{es:'Narradora / Mentora',en:'Narrator / Mentor'},fields:[{id:'narrator-type',label:{es:'Perfil',en:'Profile'}},{id:'narrator-gender',label:{es:'Género',en:'Gender'}}]},
  {id:'mc-theme-block',title:{es:'Temática femenina',en:'Feminine theme'},fields:[{id:'category',label:{es:'Categoría',en:'Category'}},{id:'style',label:{es:'Estilo',en:'Style'}},{id:'tone',label:{es:'Tono',en:'Tone'}}]}
]
};

const RAND_TOPICS={
  'ficticio-viral':{
    es:['Una enfermera que vio a un paciente morir y revivir 7 veces en una noche','Un ex militar con recuerdos de un experimento secreto en los 90','Una mujer que escapó de una secta después de 12 años','Un rockero que dice que sus canciones se las dicta un fantasma'],
    en:['A nurse who watched a patient die and revive 7 times','An ex-military man who remembers a secret 90s experiment','A woman who escaped a cult after 12 years','A rocker whose songs are dictated by a ghost']
  },
  'misterio-biblico':{
    es:['El Libro de Enoc y los 200 Vigilantes que descendieron al Monte Hermón','Los gigantes nefilim según los manuscritos del Mar Muerto','Salomón y los 72 demonios sellados en una vasija de bronce','El Evangelio de Tomás: 114 enseñanzas secretas de Jesús'],
    en:['The Book of Enoch and the 200 Watchers who descended to Mount Hermon','The Nephilim giants per the Dead Sea Scrolls','Solomon and the 72 demons sealed in a bronze vessel','The Gospel of Thomas: 114 secret teachings of Jesus']
  },
  'documental-narrado':{
    es:['El experimento MKUltra y las mentes que la CIA destruyó en secreto','La catástrofe nuclear de Kyshtym de 1957 que el mundo casi nunca supo','Los 300,000 soldados japoneses que nadie se atrevió a rendirse','La masacre de Katyn y 80 años de silencio soviético'],
    en:['MKUltra and the minds the CIA secretly destroyed','The 1957 Kyshtym nuclear disaster the world almost never knew about','The 300,000 Japanese soldiers nobody dared to surrender','The Katyn massacre and 80 years of Soviet silence']
  },
  'testimonio-real':{
    es:['La noche que vi algo en el bosque que nadie me creyó','Trabajé 3 años para una organización que no debía conocer','Sobreviví algo que no debería haber sobrevivido y nadie sabe por qué','Me pasó algo en ese hospital que no puedo explicar con lógica'],
    en:['The night I saw something in the woods nobody believed me','I worked 3 years for an organization I was never supposed to know about','I survived something I shouldn\'t have and nobody knows why','Something happened to me in that hospital I can\'t explain with logic']
  },
  'reflexion-biblica':{
    es:['Cuando Dios permite el dolor, no es señal de abandono sino de confianza','La promesa de Isaías 41:10 para los que sienten que ya no pueden más','Cuando todo colapsa a tu alrededor, hay una paz que no entiende la mente','Lo que Jesús dijo sobre el miedo que la mayoría nunca escucha'],
    en:['When God allows pain, it\'s not abandonment but trust','The promise of Isaiah 41:10 for those who feel they can\'t go on','When everything collapses around you, there\'s a peace the mind can\'t grasp','What Jesus said about fear that most people never hear']
  },
  'ciencia-misterio':{
    es:['El 95% del universo es materia oscura y energía oscura que no podemos ver ni tocar','En el océano profundo hay criaturas que producen su propia luz sin ninguna fuente externa','El efecto túnel cuántico hace que los átomos atraviesen paredes sólidas todos los días','El cerebro humano tarda 80 milisegundos en procesar la realidad — vivimos en el pasado'],
    en:['95% of the universe is dark matter and energy we can\'t see or touch','In the deep ocean there are creatures that produce their own light with no external source','Quantum tunneling makes atoms pass through solid walls every day','The human brain takes 80ms to process reality — we live in the past']
  },
  'true-crime':{
    es:['Un detective descubrió que el culpable había estado frente a él desde el primer día','La mujer que vivió 3 años con su asesino sin saber quién era realmente','El caso que la policía cerró como accidente y un periodista reabrió 20 años después','Un jurado que condenó al hombre equivocado — y lo supo el mismo día del veredicto'],
    en:['A detective discovered the culprit had been right in front of him from day one','The woman who lived 3 years with her killer without knowing who he really was','The case the police closed as an accident that a journalist reopened 20 years later','A jury that convicted the wrong man — and knew it the very day of the verdict']
  },
  'psicologia-oscura':{
    es:['Cómo un narcisista te hace sentir loco hasta que ya no confías en ti mismo','Las 7 tácticas que usa un manipulador para controlarte sin que lo notes','Por qué las víctimas de abuso defienden a su agresor — la ciencia lo explica','El patrón exacto que sigue cada relación tóxica y que nadie te enseñó a ver'],
    en:['How a narcissist makes you feel crazy until you no longer trust yourself','The 7 tactics a manipulator uses to control you without you noticing','Why abuse victims defend their abuser — science explains it','The exact pattern every toxic relationship follows that nobody taught you to see']
  },
  'conspiracion-moderna':{
    es:['Un gigante tecnológico sabe en qué piensas antes de que tú mismo lo sepas','Las redes sociales fueron diseñadas para crear adicción, no conexión — hay documentos internos filtrados','Un ex empleado de una gran plataforma digital reveló lo que nunca debías saber del algoritmo','Por qué tu teléfono te escucha aunque el micrófono esté desactivado según un experto en seguridad'],
    en:['A tech giant knows what you\'re thinking before you do','Social media was designed to create addiction, not connection — there are leaked internal documents','A former employee of a major digital platform revealed what you were never supposed to know about the algorithm','Why your phone listens to you even when the microphone is off according to a security expert']
  },
  'finanzas-libertad':{
    es:['El error financiero que el 95% comete antes de los 30 y que los hunde para siempre','Por qué trabajar más horas nunca te hará rico — y qué hacen diferente los que sí lo son','El hábito de 10 minutos al día que separa a los que tienen dinero de los que no','Warren Buffett compró su primera acción a los 11 años — lo que nadie te cuenta de eso'],
    en:['The financial mistake 95% of people make before 30 that sinks them forever','Why working more hours will never make you rich — and what wealthy people do differently','The 10-minute daily habit that separates those who have money from those who don\'t','Warren Buffett bought his first stock at 11 — what nobody tells you about that']
  },
  'mentalidad-disciplina':{
    es:['La única razón por la que no logras lo que quieres — y no es lo que crees','David Goggins corrió 100 millas con el pie roto porque nadie le dijo que podía parar','El hábito de 5 minutos que cambia la química de tu cerebro según la neurociencia','Por qué tu zona de confort literalmente te mata — y cómo salir de ella hoy'],
    en:['The only reason you\'re not achieving what you want — and it\'s not what you think','David Goggins ran 100 miles with a broken foot because no one told him he could stop','The 5-minute habit that changes your brain chemistry according to neuroscience','Why your comfort zone is literally killing you — and how to leave it today']
  },
  'historia-epica':{
    es:['El hombre que detuvo solo a un ejército de 3000 soldados en el año 480 a.C.','Espartaco: el esclavo que hizo temblar al Imperio Romano durante 3 años','La civilización más avanzada de la historia antigua que desapareció en menos de 100 años','Alejandro Magno conquistó medio mundo conocido antes de cumplir 30 años'],
    en:['The man who alone stopped an army of 3000 soldiers in 480 BC','Spartacus: the slave who made the Roman Empire tremble for 3 years','The most advanced ancient civilization that disappeared in less than 100 years','Alexander the Great conquered half the known world before turning 30']
  },
  'psicologia-positiva':{
    es:['La razón por la que no puedes parar de pensar en esa persona y cómo sanar de verdad','Cuando alguien te dice "estás exagerando" — eso se llama invalidación emocional y tiene consecuencias','El tipo de apego que tienes determina cómo amas — y cómo te lastimas','Poner límites no es ser egoísta — es respetarte y enseñar a otros cómo tratarte'],
    en:['The reason you can\'t stop thinking about that person and how to truly heal','When someone tells you "you\'re overreacting" — that\'s called emotional invalidation and it has consequences','Your attachment style determines how you love — and how you get hurt','Setting boundaries isn\'t being selfish — it\'s respecting yourself and teaching others how to treat you']
  },
  'mente-masculina':{
    es:['Nadie te enseñó a ser hombre — te enseñaron a no sentir','El hombre que más te hará daño eres tú cuando nadie te ve','La soledad masculina: por qué los hombres mueren solos y el mundo calla','Amar sin perder tu identidad — la trampa más silenciosa de las relaciones','No es debilidad llorar — es que te enseñaron a llamarle debilidad a tu humanidad','El día que dejé de buscar su aprobación fue el día que me encontré a mí mismo','Un hombre que no conoce sus heridas, las convierte en armas contra los que ama'],
    en:['Nobody taught you to be a man — they taught you not to feel','The man who will hurt you most is who you are when no one is watching','Male loneliness: why men die alone and the world stays silent','Loving without losing your identity — the most silent trap in relationships','It\'s not weakness to cry — they just taught you to call your humanity weakness','The day I stopped seeking her approval was the day I found myself','A man who doesn\'t know his wounds turns them into weapons against those he loves']
  },
  'mujer-consciente':{
    es:['Nadie te enseñó a amarte — te enseñaron a necesitar que te amaran','El día que dejé de pedir perdón por ser demasiado fue el día que empecé a vivir','No eres difícil de amar — estuviste rodeada de personas que no sabían amar','Seguiste dando amor a quien nunca supo recibirlo y lo llamaste tu culpa','La mujer que más te costará soltar eres tú misma de hace 5 años','Poner límites no te hace cruel — te hace honesta contigo misma','Una mujer que sana su relación consigo misma cambia todo lo que toca'],
    en:['Nobody taught you to love yourself — they taught you to need to be loved','The day I stopped apologizing for being too much was the day I started living','You\'re not hard to love — you were surrounded by people who didn\'t know how to love','You kept giving love to someone who couldn\'t receive it and called it your fault','The woman who will be hardest to let go of is who you were 5 years ago','Setting boundaries doesn\'t make you cruel — it makes you honest with yourself','A woman who heals her relationship with herself changes everything she touches']
  }
};

const RAND_TOPICS_LIBRO={
  es:['El Poder del Ahora — Eckhart Tolle','Pensar Rapido Pensar Despacio — Kahneman','Sapiens — Yuval Noah Harari','Los 7 Habitos — Stephen Covey','Deep Work — Cal Newport'],
  en:['The Power of Now — Eckhart Tolle','Thinking Fast and Slow — Kahneman','Sapiens — Yuval Noah Harari','The 7 Habits — Stephen Covey','Deep Work — Cal Newport']
};

const LIBRO_SEGMENTS={
  es:[
    {id:'gancho',label:'🎣 Gancho',dur:8,instruction:'Verdad incómoda o dato sorprendente del libro. Sin presentar el título todavía. Máximo 20 palabras.'},
    {id:'libro',label:'📖 El Libro',dur:8,instruction:'Presenta título y autor de forma natural, como recomendación a un amigo. Máximo 22 palabras.'},
    {id:'ideas',label:'💡 Ideas + Giro',dur:10,instruction:'Premisa principal + la idea más contraintuitiva del libro. Máximo 28 palabras.'},
    {id:'vida',label:'🔥 En tu vida',dur:10,instruction:'Cómo aplicar la idea mañana mismo, ejemplo concreto. Máximo 28 palabras.'},
    {id:'cierre',label:'🚀 Cierre+CTA',dur:8,instruction:'Frase memorable que resuene + invitación a leer el libro. Máximo 22 palabras.'}
  ],
  en:[
    {id:'gancho',label:'🎣 Hook',dur:8,instruction:'Uncomfortable truth or surprising fact. No book title yet. Max 20 words.'},
    {id:'libro',label:'📖 The Book',dur:8,instruction:'Present title and author naturally, like recommending to a friend. Max 22 words.'},
    {id:'ideas',label:'💡 Ideas + Twist',dur:10,instruction:'Main premise + the most counterintuitive idea. Max 28 words.'},
    {id:'vida',label:'🔥 In your life',dur:10,instruction:'How to apply it tomorrow, concrete example. Max 28 words.'},
    {id:'cierre',label:'🚀 Close+CTA',dur:8,instruction:'Memorable line + invitation to read. Max 22 words.'}
  ]
};

let lang='es', mode='ficticio-viral', format='lineal', hlType='rapida', dur=1, setStyle='oscuro', numHosts=1, numGuests=0;

function t(key){return T[lang][key]||key;}
function pick(arr){return arr[Math.floor(Math.random()*arr.length)];}
function gv(id){const el=document.getElementById(id);return el?el.value:'';}
function res(id,opts){const v=gv(id);return v==='random'?pick(opts):v;}

// ── API OpenRouter ─────────────────────────────────────────────────────────────
let _orKey  = localStorage.getItem('or_key')   || '';
let _orModel= localStorage.getItem('or_model') || 'anthropic/claude-3.7-sonnet';

(function initApi(){
  const ki=document.getElementById('or-key');
  const mi=document.getElementById('or-model');
  if(ki&&_orKey) ki.value=_orKey;
  if(mi){
    const savedModel=_orModel;
    const match=[...mi.options].some(o=>o.value===savedModel);
    if(match){ mi.value=savedModel; }
    else if(savedModel&&savedModel!=='__custom__'){
      // modelo guardado no está en la lista → mostrar campo custom
      mi.value='__custom__';
      const cf=document.getElementById('custom-model-field');
      const cm=document.getElementById('or-model-custom');
      if(cf) cf.style.display='block';
      if(cm) cm.value=savedModel;
    }
  }
  updateBadge();
})();

function onModelChange(){
  const sel=document.getElementById('or-model');
  const cf=document.getElementById('custom-model-field');
  if(cf) cf.style.display=(sel.value==='__custom__')?'block':'none';
}

function getActiveModel(){
  const sel=document.getElementById('or-model');
  if(sel&&sel.value==='__custom__'){
    return (document.getElementById('or-model-custom').value||'').trim()||_orModel;
  }
  return sel?sel.value:_orModel;
}

function toggleApi(){
  const body=document.getElementById('api-body');
  const arrow=document.getElementById('api-arrow');
  const open=body.classList.toggle('open');
  arrow.textContent=open?'▲':'▼';
}

function updateBadge(){
  const badge=document.getElementById('api-badge');
  const btn=document.getElementById('generate-ai');
  const rcBtn=document.getElementById('recommend-combo');
  if(_orKey){
    badge.textContent='✅ '+getActiveModel().split('/').pop();
    badge.className='api-badge badge-ok';
    if(btn)btn.disabled=false;
    if(rcBtn)rcBtn.disabled=false;
  } else {
    badge.textContent='sin configurar — clic para abrir';
    badge.className='api-badge badge-off';
    if(btn)btn.disabled=true;
    if(rcBtn)rcBtn.disabled=true;
  }
}

function saveApi(){
  _orKey  =(document.getElementById('or-key').value||'').trim();
  _orModel=getActiveModel();
  localStorage.setItem('or_key',  _orKey);
  localStorage.setItem('or_model',_orModel);
  updateBadge();
  const badge=document.getElementById('api-badge');
  badge.textContent=_orKey?'💾 Guardado':'⚠️ Sin API key';
  setTimeout(updateBadge,1500);
}

async function testApi(){
  if(!_orKey){alert('Agrega tu API key y guarda primero.');return;}
  const badge=document.getElementById('api-badge');
  badge.textContent='⏳ Probando...';badge.className='api-badge';
  try{
    const r=await _callOR('Reply with the single word: OK','ping',10);
    badge.textContent='✅ Conectado';badge.className='api-badge badge-ok';
  }catch(e){
    badge.textContent='❌ '+e.message.slice(0,35);badge.className='api-badge badge-err';
  }
}

const _SAFETY=`\n\nSAFETY RULES (mandatory):\n- Never mention real brand names, company names, or registered trademarks. Use generics: "cadena de comida rápida / fast food chain", "gigante tecnológico / tech giant", "plataforma social / social media platform", "farmacéutica / pharma company", "aerolínea / airline", "banco multinacional / multinational bank".\n- Do not present fictional or speculative content as verified facts. Use narrative or hypothetical framing.\n- No defamatory statements about real, identifiable individuals.\n- Content must comply with TikTok, YouTube Shorts, and Facebook community guidelines.`;

async function _callOR(sys,user,maxTok=1000){
  const r=await fetch('https://openrouter.ai/api/v1/chat/completions',{
    method:'POST',
    headers:{'Authorization':'Bearer '+_orKey,'Content-Type':'application/json','HTTP-Referer':'https://generador-prompts.local','X-Title':'Generador Multi-Modo'},
    body:JSON.stringify({model:getActiveModel(),messages:[{role:'system',content:sys+_SAFETY},{role:'user',content:user}],max_tokens:maxTok,temperature:0.88})
  });
  if(!r.ok){const e=await r.json().catch(()=>({}));throw new Error(e.error?.message||'HTTP '+r.status);}
  const d=await r.json();
  return (d.choices[0].message.content||'').trim();
}

async function generateWithAI(skipBtnUI=false){
  if(!_orKey){alert('Configura tu API key primero.');return;}
  const btn=document.getElementById('generate-ai');
  const area=document.getElementById('ai-output-area');
  if(!skipBtnUI){btn.innerHTML='<span class="spinner"></span>Generando...';btn.disabled=true;}
  area.innerHTML='';

  const topic=gv('topic').trim()||(mode==='libro-rapido'?pick(RAND_TOPICS_LIBRO[lang]):pick(RAND_TOPICS[mode]?.[lang]||[]));
  const styleV=gv('style')||'random';
  const toneV=gv('tone')||'random';

  let sys='', usr='';

  const PODCAST_PREVIEW_SYS={
    'ficticio-viral':{es:'Eres el guionista de un podcast ficticio viral de misterio. Responde SOLO con JSON array de objetos {"host":"...","guest":"..."} sin texto extra.',en:'You are the scriptwriter of a viral fictional mystery podcast. Reply ONLY with a JSON array of {"host":"...","guest":"..."} objects.'},
    'true-crime':{es:'Eres el guionista de un podcast de true crime. El host investiga, el invitado revela. Responde SOLO con JSON array de objetos {"host":"...","guest":"..."} sin texto extra.',en:'You are the scriptwriter of a true crime podcast. Host investigates, guest reveals. Reply ONLY with a JSON array of {"host":"...","guest":"..."} objects.'},
    'psicologia-oscura':{es:'Eres el guionista de un podcast de psicología oscura. El experto expone patrones, el invitado los reconoce en su experiencia. Responde SOLO con JSON array de objetos {"host":"...","guest":"..."} sin texto extra.',en:'You are the scriptwriter of a dark psychology podcast. Expert exposes patterns, guest recognizes them from experience. Reply ONLY with a JSON array of {"host":"...","guest":"..."} objects.'},
    'conspiracion-moderna':{es:'Eres el guionista de un podcast de conspiración moderna. El periodista presiona, el informante revela datos perturbadores. Responde SOLO con JSON array de objetos {"host":"...","guest":"..."} sin texto extra.',en:'You are the scriptwriter of a modern conspiracy podcast. Journalist presses, whistleblower reveals disturbing data. Reply ONLY with a JSON array of {"host":"...","guest":"..."} objects.'}
  };
  const PODCAST_PREVIEW_USR={
    'ficticio-viral':{es:`Tema: "${topic}" | Estilo: ${styleV} | Tono: ${toneV}\n\nGenera 8 intercambios HOST/GUEST (máx 20 palabras cada uno). El host presiona, el invitado revela algo perturbador.\n\nJSON:\n[{"host":"...","guest":"..."}]`,en:`Topic: "${topic}" | Style: ${styleV} | Tone: ${toneV}\n\nGenerate 8 HOST/GUEST exchanges (max 20 words each).\n\nJSON:\n[{"host":"...","guest":"..."}]`},
    'true-crime':{es:`Caso: "${topic}" | Estilo: ${styleV} | Tono: ${toneV}\n\nGenera 8 intercambios INVESTIGADOR/TESTIGO (máx 22 palabras cada uno). El investigador interroga, el testigo revela detalles perturbadores. Escala la tensión.\n\nJSON:\n[{"host":"...","guest":"..."}]`,en:`Case: "${topic}" | Style: ${styleV} | Tone: ${toneV}\n\nGenerate 8 INVESTIGATOR/WITNESS exchanges (max 22 words each). Investigator interrogates, witness reveals disturbing details. Escalate tension.\n\nJSON:\n[{"host":"...","guest":"..."}]`},
    'psicologia-oscura':{es:`Tema: "${topic}" | Estilo: ${styleV} | Tono: ${toneV}\n\nGenera 8 intercambios EXPERTO/SOBREVIVIENTE (máx 22 palabras cada uno). El experto expone tácticas, el sobreviviente las reconoce con horror.\n\nJSON:\n[{"host":"...","guest":"..."}]`,en:`Topic: "${topic}" | Style: ${styleV} | Tone: ${toneV}\n\nGenerate 8 EXPERT/SURVIVOR exchanges (max 22 words each). Expert exposes tactics, survivor recognizes them with horror.\n\nJSON:\n[{"host":"...","guest":"..."}]`},
    'conspiracion-moderna':{es:`Tema: "${topic}" | Estilo: ${styleV} | Tono: ${toneV}\n\nGenera 8 intercambios PERIODISTA/INFORMANTE (máx 22 palabras cada uno). El periodista cuestiona, el informante revela datos que no debería saber nadie.\n\nJSON:\n[{"host":"...","guest":"..."}]`,en:`Topic: "${topic}" | Style: ${styleV} | Tone: ${toneV}\n\nGenerate 8 JOURNALIST/WHISTLEBLOWER exchanges (max 22 words each). Journalist questions, whistleblower reveals data nobody should know.\n\nJSON:\n[{"host":"...","guest":"..."}]`}
  };

  if(PODCAST_PREVIEW_SYS[mode]){
    sys=PODCAST_PREVIEW_SYS[mode][lang]||PODCAST_PREVIEW_SYS[mode].es;
    usr=PODCAST_PREVIEW_USR[mode][lang]||PODCAST_PREVIEW_USR[mode].es;
  } else if(mode==='misterio-biblico'){
    sys=lang==='es'
      ?'Eres un narrador experto en misterios bíblicos y textos apócrifos. Generas revelaciones cinematográficas y oscuras. Responde SOLO con JSON array de strings.'
      :'You are a narrator expert in biblical mysteries and apocryphal texts. Generate cinematic dark revelations. Reply ONLY with a JSON array of strings.';
    usr=lang==='es'
      ?`Tema: "${topic}" | Estilo: ${styleV} | Tono: ${toneV}\n\nGenera 8 frases de narración (máximo 25 palabras cada una). Escala la tensión y revela el misterio progresivamente.\n\nJSON:\n["frase1","frase2",...]`
      :`Topic: "${topic}" | Style: ${styleV} | Tone: ${toneV}\n\nGenerate 8 narration lines (max 25 words each). Escalate tension, reveal the mystery progressively.\n\nJSON:\n["line1","line2",...]`;
  } else if(mode==='libro-rapido'){
    const segs=LIBRO_SEGMENTS[lang];
    sys=lang==='es'
      ?'Eres un narrador viral de resúmenes de libros. Hablas directo al oído del espectador. Responde SOLO con JSON array de 5 strings.'
      :'You are a viral book summary narrator. You speak directly into the viewer\'s ear. Reply ONLY with a JSON array of 5 strings.';
    usr=lang==='es'
      ?`Libro: "${topic}"\n\nGenera exactamente 5 segmentos:\n1. GANCHO (18 palabras máx): verdad incómoda del libro\n2. EL LIBRO (20 palabras máx): presenta título y autor\n3. IDEA+GIRO (25 palabras máx): premisa + idea contraintuitiva\n4. EN TU VIDA (25 palabras máx): aplicación práctica mañana\n5. CIERRE+CTA (20 palabras máx): frase memorable + invita a leer\n\nJSON:\n["gancho","libro","ideas","vida","cierre"]`
      :`Book: "${topic}"\n\nGenerate exactly 5 segments:\n1. HOOK (max 18 words): uncomfortable truth from book\n2. THE BOOK (max 20 words): introduce title and author\n3. IDEA+TWIST (max 25 words): premise + counterintuitive idea\n4. IN YOUR LIFE (max 25 words): practical application tomorrow\n5. CLOSE+CTA (max 20 words): memorable line + invite to read\n\nJSON:\n["hook","book","ideas","life","close"]`;
  } else if(mode==='documental-narrado'){
    sys=lang==='es'
      ?'Eres el narrador de un documental histórico impactante, estilo National Geographic / BBC. Voz grave, hechos reales, escalas la tensión. Responde SOLO con JSON array de strings.'
      :'You are the narrator of a shocking historical documentary, National Geographic / BBC style. Deep voice, real facts, escalating tension. Reply ONLY with a JSON array of strings.';
    usr=lang==='es'
      ?`Tema: "${topic}" | Categoría: ${gv('category')||'random'} | Estilo: ${styleV} | Tono: ${toneV}\n\nGenera 8 frases de narración documental (máx 28 palabras cada una). Inicia con un dato impactante, escala la tensión, termina con una revelación.\n\nJSON:\n["frase1","frase2",...]`
      :`Topic: "${topic}" | Category: ${gv('category')||'random'} | Style: ${styleV} | Tone: ${toneV}\n\nGenerate 8 documentary narration lines (max 28 words each). Start with a shocking fact, escalate tension, end with a revelation.\n\nJSON:\n["line1","line2",...]`;
  } else if(mode==='testimonio-real'){
    sys=lang==='es'
      ?'Eres el escritor de testimonios dramáticos en primera persona para YouTube Shorts. Voz temblorosa, confesional, íntima. Responde SOLO con JSON array de strings.'
      :'You write dramatic first-person testimonies for YouTube Shorts. Trembling, confessional, intimate voice. Reply ONLY with a JSON array of strings.';
    usr=lang==='es'
      ?`Tema: "${topic}" | Tipo: ${gv('narrator-type')||'random'} | Categoría: ${gv('category')||'random'} | Estilo: ${styleV} | Tono: ${toneV}\n\nGenera 8 frases de testimonio en primera persona (máx 22 palabras cada una). Usa "yo", "me", "mi". Inicia in media res, genera intriga, revela algo perturbador al final.\n\nJSON:\n["frase1","frase2",...]`
      :`Topic: "${topic}" | Type: ${gv('narrator-type')||'random'} | Category: ${gv('category')||'random'} | Style: ${styleV} | Tone: ${toneV}\n\nGenerate 8 first-person testimony lines (max 22 words each). Use "I", "me", "my". Start in media res, build intrigue, reveal something disturbing at the end.\n\nJSON:\n["line1","line2",...]`;
  } else if(mode==='reflexion-biblica'){
    sys=lang==='es'
      ?'Eres un pastor o narrador bíblico que crea devocionales cortos y profundos para YouTube Shorts. Responde SOLO con JSON de exactamente 5 strings.'
      :'You are a pastor or biblical narrator creating short, deep devotionals for YouTube Shorts. Reply ONLY with a JSON of exactly 5 strings.';
    usr=lang==='es'
      ?`Tema: "${topic}" | Categoría: ${gv('category')||'fe-esperanza'} | Estilo: ${styleV} | Tono: ${toneV}\n\nGenera exactamente 5 segmentos:\n1. GANCHO (15 palabras máx): pregunta o verdad que golpea el alma\n2. VERSO (20 palabras máx): cita bíblica relevante con referencia\n3. CONTEXTO (25 palabras máx): qué significa ese verso hoy\n4. APLICACION (25 palabras máx): cómo aplicarlo en tu vida esta semana\n5. CIERRE+ORACIóN (22 palabras máx): oración breve o frase de fe\n\nJSON:\n["gancho","verso","contexto","aplicacion","cierre"]`
      :`Topic: "${topic}" | Category: ${gv('category')||'faith-hope'} | Style: ${styleV} | Tone: ${toneV}\n\nGenerate exactly 5 segments:\n1. HOOK (max 15 words): question or soul-piercing truth\n2. VERSE (max 20 words): relevant Bible quote with reference\n3. CONTEXT (max 25 words): what that verse means today\n4. APPLICATION (max 25 words): how to apply it this week\n5. CLOSE+PRAYER (max 22 words): brief prayer or faith statement\n\nJSON:\n["hook","verse","context","application","close"]`;
  } else if(mode==='ciencia-misterio'){
    sys=lang==='es'
      ?'Eres un divulgador científico viral que explica misterios del universo de forma asombrosa. Responde SOLO con JSON array de strings.'
      :'You are a viral science communicator explaining universe mysteries in an amazing way. Reply ONLY with a JSON array of strings.';
    usr=lang==='es'
      ?`Tema: "${topic}" | Categoría: ${gv('category')||'random'} | Estilo: ${styleV} | Tono: ${toneV}\n\nGenera 8 frases de divulgación científica (máx 26 palabras cada una). Usa datos reales, analogías visuales, termina con una pregunta que expande la mente.\n\nJSON:\n["frase1","frase2",...]`
      :`Topic: "${topic}" | Category: ${gv('category')||'random'} | Style: ${styleV} | Tone: ${toneV}\n\nGenerate 8 science communication lines (max 26 words each). Use real facts, visual analogies, end with a mind-expanding question.\n\nJSON:\n["line1","line2",...]`;
  } else if(mode==='psicologia-positiva'){
    sys=lang==='es'
      ?'Eres una psicóloga empática y divulgadora de bienestar emocional para YouTube Shorts. Hablas con calidez, claridad y amor. Responde SOLO con JSON array de strings.'
      :'You are an empathetic psychologist and emotional wellness communicator for YouTube Shorts. Speak with warmth, clarity and love. Reply ONLY with a JSON array of strings.';
    usr=lang==='es'
      ?`Tema: "${topic}" | Categoría: ${gv('category')||'autoestima'} | Estilo: ${styleV} | Tono: ${toneV}\n\nGenera 8 frases de psicología positiva (máx 24 palabras cada una). Habla directo al espectador ("tú", "te"), inicia con algo que resuene emocionalmente, da validación y un paso de acción concreto al final.\n\nJSON:\n["frase1","frase2",...]`
      :`Topic: "${topic}" | Category: ${gv('category')||'self-esteem'} | Style: ${styleV} | Tone: ${toneV}\n\nGenerate 8 positive psychology lines (max 24 words each). Speak directly to the viewer ("you"), start with something emotionally resonant, give validation and one concrete action step at the end.\n\nJSON:\n["line1","line2",...]`;
  } else if(mode==='finanzas-libertad'){
    sys=lang==='es'
      ?'Eres un educador financiero viral. Hablas directo, con datos reales, sin jerga aburrida. Sacudes creencias y das pasos concretos. Responde SOLO con JSON array de strings.'
      :'You are a viral financial educator. Direct, real data, no boring jargon. You shake beliefs and give concrete steps. Reply ONLY with a JSON array of strings.';
    usr=lang==='es'
      ?`Tema: "${topic}" | Categoría: ${gv('category')||'random'} | Estilo: ${styleV} | Tono: ${toneV}\n\nGenera 8 frases de educación financiera (máx 26 palabras cada una). Inicia con un dato que sacuda, escala con pasos reales, cierra con una frase que cambie la mentalidad.\n\nJSON:\n["frase1","frase2",...]`
      :`Topic: "${topic}" | Category: ${gv('category')||'random'} | Style: ${styleV} | Tone: ${toneV}\n\nGenerate 8 financial education lines (max 26 words each). Start with a mind-shaking fact, escalate with real steps, close with a mindset-shifting line.\n\nJSON:\n["line1","line2",...]`;
  } else if(mode==='mentalidad-disciplina'){
    sys=lang==='es'
      ?'Eres un coach de mentalidad y disciplina extremadamente viral. Hablas con fuego, datos y verdades incómodas. Responde SOLO con JSON array de strings.'
      :'You are an extremely viral mindset and discipline coach. You speak with fire, data, and uncomfortable truths. Reply ONLY with a JSON array of strings.';
    usr=lang==='es'
      ?`Tema: "${topic}" | Categoría: ${gv('category')||'random'} | Estilo: ${styleV} | Tono: ${toneV}\n\nGenera 8 frases de mentalidad / motivación (máx 24 palabras cada una). Habla directo al espectador, usa "tú", inicia con una verdad incómoda, escala hacia la acción.\n\nJSON:\n["frase1","frase2",...]`
      :`Topic: "${topic}" | Category: ${gv('category')||'random'} | Style: ${styleV} | Tone: ${toneV}\n\nGenerate 8 mindset / motivation lines (max 24 words each). Speak directly to the viewer, use "you", start with an uncomfortable truth, escalate toward action.\n\nJSON:\n["line1","line2",...]`;
  } else if(mode==='historia-epica'){
    sys=lang==='es'
      ?'Eres un narrador épico de historia, estilo documental cinematográfico de Hollywood. Voz poderosa, datos impactantes, tensión crescente. Responde SOLO con JSON array de strings.'
      :'You are an epic history narrator, Hollywood cinematic documentary style. Powerful voice, shocking facts, rising tension. Reply ONLY with a JSON array of strings.';
    usr=lang==='es'
      ?`Tema: "${topic}" | Categoría: ${gv('category')||'random'} | Estilo: ${styleV} | Tono: ${toneV}\n\nGenera 8 frases de narración épica histórica (máx 28 palabras cada una). Inicia con un hecho impactante, escala la tensión dramática, termina con una frase legendaria.\n\nJSON:\n["frase1","frase2",...]`
      :`Topic: "${topic}" | Category: ${gv('category')||'random'} | Style: ${styleV} | Tone: ${toneV}\n\nGenerate 8 epic historical narration lines (max 28 words each). Start with a shocking fact, escalate dramatic tension, end with a legendary line.\n\nJSON:\n["line1","line2",...]`;
  }

  try{
    const raw=await _callOR(sys,usr,1200);
    const m=raw.match(/\[[\s\S]*\]/);
    if(!m) throw new Error(lang==='es'?'La IA no devolvió JSON válido':'AI did not return valid JSON');
    const data=JSON.parse(m[0]);
    renderAI(data,topic);
    // ── Paquete redes sociales (segunda llamada ligera) ────────────────
    try{
      const soc=await _callOR(
        'You are a viral social media expert for YouTube Shorts, TikTok and Facebook. Reply ONLY with valid JSON, no markdown.',
        `Content mode: ${mode} | Topic: "${topic}" | Language: ${lang==='es'?'Spanish':'English'}\n\nReturn ONLY this JSON:\n{\n  "hook":"Viral hook max 130 chars — curiosity, ends on suspense",\n  "copy":"Caption 2-3 short lines",\n  "tags_tiktok":["#tag1","#tag2","#tag3","#tag4","#tag5"],\n  "tags_facebook":["#tag1","#tag2","#tag3","#tag4","#tag5","#tag6","#tag7","#tag8"],\n  "tags_youtube":["#tag1","#tag2","#tag3","#tag4"],\n  "thumbnail_prompt":"Vertical 9:16 ChatGPT/DALL-E prompt for thumbnail — dramatic, high contrast, text space top 20%"\n}\nAll text in ${lang==='es'?'Spanish':'English'}. No brand names — use generics.`,
        600
      );
      const sm=soc.match(/\{[\s\S]*\}/);
      if(sm){
        const sd=JSON.parse(sm[0]);
        const tagRow=(tags,color,label)=>tags&&tags.length?`<div style="margin-bottom:6px;"><span style="font-size:9px;font-weight:700;color:${color};text-transform:uppercase;letter-spacing:0.5px;">${label}</span><br><span style="font-size:11px;color:#444;">${tags.join(' ')}</span><button class="clip-copy" style="margin-left:8px;" onclick="copyTxt(${JSON.stringify(tags.join(' '))})">📋</button></div>`:'';
        const socHtml=`${sd.hook?`<div style="background:#f0f9ff;border-radius:8px;padding:10px;margin-bottom:8px;"><div style="font-size:10px;font-weight:700;color:#0369a1;margin-bottom:4px;">🪝 HOOK / CAPTION</div><div style="font-size:12px;color:#1a1a1a;font-weight:500;">${sd.hook}</div>${sd.copy?`<div style="font-size:11px;color:#555;margin-top:4px;white-space:pre-line;">${sd.copy}</div>`:''}<button class="clip-copy" onclick="copyTxt(${JSON.stringify((sd.hook||'')+(sd.copy?'\n\n'+sd.copy:''))})">📋 Copiar copy</button></div>`:''}
        ${(sd.tags_tiktok||sd.tags_facebook||sd.tags_youtube)?`<div style="background:#fafafa;border:0.5px solid rgba(0,0,0,0.1);border-radius:8px;padding:10px;margin-bottom:8px;">${tagRow(sd.tags_tiktok,'#000','TikTok (máx 5)')}${tagRow(sd.tags_facebook,'#1877f2','Facebook (máx 8)')}${tagRow(sd.tags_youtube,'#ff0000','YouTube (máx 4)')}</div>`:''}
        ${sd.thumbnail_prompt?`<div style="background:#fff8f0;border-radius:8px;padding:10px;"><div style="font-size:10px;font-weight:700;color:#d97706;margin-bottom:4px;">🖼️ PROMPT PORTADA — ChatGPT / DALL-E</div><div class="clip-voice">${sd.thumbnail_prompt}</div><button class="clip-copy" onclick="copyTxt(${JSON.stringify(sd.thumbnail_prompt)})">📋 Copiar prompt portada</button></div>`:''}`;
        const existingArea=document.getElementById('ai-output-area');
        existingArea.insertAdjacentHTML('beforeend',`<div class="ai-out" style="border-left:3px solid #0ea5e9;padding-left:14px;"><div style="font-size:11px;font-weight:700;color:#0369a1;margin-bottom:10px;">📱 Paquete redes sociales</div>${socHtml}</div>`);
      }
    }catch(e2){/* no bloquear si la segunda call falla */}
  }catch(e){
    area.innerHTML=`<div style="background:#fff1f2;border-radius:8px;padding:12px;font-size:12px;color:#9f1239;">❌ ${e.message}</div>`;
  }finally{
    if(!skipBtnUI){btn.innerHTML='🤖 Generar con IA';btn.disabled=false;}
  }
}

function renderAI(data,topic){
  const area=document.getElementById('ai-output-area');
  const model=_orModel.split('/').pop();
  let html=`<div class="ai-out"><div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;gap:8px;flex-wrap:wrap;">
    <strong style="font-size:13px;color:#185fa5;">🤖 Generado con IA · ${model}</strong>
    <div style="display:flex;gap:5px;"><button onclick="window.scrollTo({top:0,behavior:'smooth'})" style="height:26px;padding:0 8px;font-size:11px;background:#f0ede2;border:none;border-radius:5px;cursor:pointer;">⬆️</button><button onclick="copyAI()" style="height:26px;padding:0 10px;font-size:11px;">📋 Copiar todo</button></div>
  </div><div style="font-size:11px;color:#666;margin-bottom:10px;">Tema: <strong>${topic}</strong></div>`;

  // Modos con formato host/guest (podcast de 2 personas)
  const PODCAST_PREVIEW_MODES=['ficticio-viral','true-crime','psicologia-oscura','conspiracion-moderna'];
  if(PODCAST_PREVIEW_MODES.includes(mode)){
    const hostLabel=mode==='true-crime'?(lang==='es'?'INVESTIGADOR':'INVESTIGATOR'):mode==='psicologia-oscura'?(lang==='es'?'EXPERTO':'EXPERT'):mode==='conspiracion-moderna'?(lang==='es'?'PERIODISTA':'JOURNALIST'):'HOST';
    const guestLabel=mode==='true-crime'?(lang==='es'?'TESTIGO':'WITNESS'):mode==='psicologia-oscura'?(lang==='es'?'SOBREVIVIENTE':'SURVIVOR'):mode==='conspiracion-moderna'?(lang==='es'?'INFORMANTE':'WHISTLEBLOWER'):(lang==='es'?'INVITADO':'GUEST');
    data.forEach((p,i)=>{
      html+=`<div class="ai-seg"><div class="ai-seg-label">${lang==='es'?'Intercambio':'Exchange'} ${i+1}</div>
        <div style="margin-bottom:5px;"><span style="font-size:10px;font-weight:600;color:#7c3aed;">${hostLabel}</span><br>${p.host||''}</div>
        <div><span style="font-size:10px;font-weight:600;color:#e11d48;">${guestLabel}</span><br>${p.guest||''}</div></div>`;
    });
    area._copy=data.map((p,i)=>`[${i+1}]\n${hostLabel}: ${p.host||''}\n${guestLabel}: ${p.guest||''}`).join('\n\n');
  } else if(mode==='libro-rapido'){
    const labels=lang==='es'
      ?['🎣 Gancho','📖 El Libro','💡 Ideas + Giro','🔥 En tu vida','🚀 Cierre + CTA']
      :['🎣 Hook','📖 The Book','💡 Ideas + Twist','🔥 In your life','🚀 Close + CTA'];
    data.forEach((s,i)=>{html+=`<div class="ai-seg"><div class="ai-seg-label">${labels[i]||'Seg '+(i+1)}</div>${s}</div>`;});
    area._copy=labels.map((l,i)=>`${l}:\n${data[i]||''}`).join('\n\n');
  } else if(mode==='reflexion-biblica'){
    const labels=lang==='es'
      ?['🎣 Gancho','📖 Verso bíblico','💡 Contexto','🔥 Aplicación','🙏 Cierre / Oración']
      :['🎣 Hook','📖 Bible verse','💡 Context','🔥 Application','🙏 Close / Prayer'];
    data.forEach((s,i)=>{html+=`<div class="ai-seg"><div class="ai-seg-label">${labels[i]||'Seg '+(i+1)}</div>${s}</div>`;});
    area._copy=labels.map((l,i)=>`${l}:\n${data[i]||''}`).join('\n\n');
  } else {
    // Todos los modos narradores: misterio-biblico, documental-narrado, testimonio-real,
    // ciencia-misterio, finanzas-libertad, mentalidad-disciplina, historia-epica,
    // psicologia-positiva, psicologia-oscura (narrator preview), etc.
    data.forEach((l,i)=>{html+=`<div class="ai-seg"><div class="ai-seg-label">${lang==='es'?'Clip':'Clip'} ${i+1}</div>${l}</div>`;});
    area._copy=data.map((l,i)=>`[${i+1}] ${l}`).join('\n\n');
  }

  html+='</div>';
  area.innerHTML=html;
}

function copyAI(){
  const area=document.getElementById('ai-output-area');
  if(!area||!area._copy) return;
  copyTxt(area._copy);
}

// ── UI Render ──────────────────────────────────────────────────────────────────
function renderModes(){
  const cPod=document.getElementById('mode-selector-podcast');
  const cNar=document.getElementById('mode-selector-narrator');
  if(cPod) cPod.innerHTML='';
  if(cNar) cNar.innerHTML='';
  const podcastSet=new Set(['ficticio-viral','true-crime','psicologia-oscura','conspiracion-moderna']);
  Object.entries(MODES).forEach(([id,m])=>{
    const p=document.createElement('div');
    p.className='mode-pill'+(id===mode?' active':'');
    p.title=m.desc[lang];
    p.innerHTML=`<span class="mode-icon">${m.icon}</span><span class="mode-title">${m.title[lang]}</span>`;
    p.onclick=()=>setMode(id);
    const target=podcastSet.has(id)?cPod:cNar;
    if(target) target.appendChild(p);
  });
}

function renderBlocks(){
  const c=document.getElementById('config-blocks');c.innerHTML='';
  MODE_BLOCKS[mode].forEach(block=>{
    const card=document.createElement('div');card.className='card';
    let html=`<h3>${block.title[lang]} <span class="tag" id="${block.id}-tag">${t('manual')}</span></h3><div class="grid2">`;
    block.fields.forEach(f=>{html+=`<div><label>${f.label[lang]}</label><select id="${f.id}"></select></div>`;});
    html+='</div>';card.innerHTML=html;c.appendChild(card);
  });
}

function renderSelects(){
  const ms=MODE_SELECTS[mode];
  Object.entries(ms).forEach(([id,lo])=>{
    const el=document.getElementById(id);if(!el)return;
    const prev=el.value;el.innerHTML='';
    lo[lang].forEach(([v,l])=>{const o=document.createElement('option');o.value=v;o.textContent=l;el.appendChild(o);});
    if(prev&&[...el.options].some(o=>o.value===prev))el.value=prev;
  });
}

function renderHighlightSubs(){
  const cont=document.getElementById('highlight-subtypes');
  const pc=document.getElementById('sub-pills-container');
  if(format==='highlight'){
    cont.style.display='block';pc.innerHTML='';
    Object.entries(T[lang].hlTypes).forEach(([k,label])=>{
      const b=document.createElement('button');b.className='spill'+(k===hlType?' active':'');b.textContent=label;
      b.onclick=()=>{hlType=k;renderHighlightSubs();};pc.appendChild(b);
    });
  } else {cont.style.display='none';}
}

function updateDurInfo(){
  const {clips,sec}=DUR_CLIPS[dur];
  document.getElementById('dur-info').textContent=T[lang].durInfo(dur,clips,sec);
}

function updateTags(){
  MODE_BLOCKS[mode].forEach(block=>{
    const tag=document.getElementById(`${block.id}-tag`);if(!tag)return;
    const isRnd=block.fields.some(f=>gv(f.id)==='random');
    tag.textContent=isRnd?t('rnd'):t('manual');tag.className=isRnd?'tag rnd':'tag';
  });
}

function applyI18n(){
  document.querySelectorAll('[data-i18n]').forEach(el=>{const k=el.getAttribute('data-i18n');if(T[lang][k])el.textContent=T[lang][k];});
  document.querySelectorAll('[data-i18n-placeholder]').forEach(el=>{const k=el.getAttribute('data-i18n-placeholder');if(T[lang][k])el.placeholder=T[lang][k];});
}

function updateNarratorCountRow(){
  const row=document.getElementById('narrator-count-row');
  if(!row) return;
  const isNarrator=NARRATOR_MODES.includes(mode);
  row.style.display=isNarrator?'block':'none';
  updateNarratorCountInfo();
}
function updateNarratorCountInfo(){
  const info=document.getElementById('ncount-info');
  if(!info) return;
  const total=numHosts+numGuests;
  let msg;
  if(total===1){msg=lang==='es'?'1 narrador único — solo en escena.':'1 solo narrator on screen.';}
  else if(total===2){msg=lang==='es'?`${numHosts} host + ${numGuests} guest — formato entrevista o debate.`:`${numHosts} host + ${numGuests} guest — interview or debate format.`;}
  else{msg=lang==='es'?`Mesa redonda con ${total} personas (${numHosts} host${numHosts>1?'s':''} + ${numGuests} guest${numGuests>1?'s':''}) — panel de conversación natural.`:`Round table with ${total} people (${numHosts} host${numHosts>1?'s':''} + ${numGuests} guest${numGuests>1?'s':''}) — natural conversation panel.`;}
  info.textContent=msg;
}
function fullRender(){renderModes();renderBlocks();renderSelects();renderHighlightSubs();updateDurInfo();applyI18n();updateTags();updateRecommendBtn();updateNarratorCountRow();}
function updateRecommendBtn(){
  // El botón siempre está visible; solo cambia su label según el modo
  const btn=document.getElementById('recommend-combo');
  if(!btn) return;
  const labels={es:'🎯 Recomendar combo',en:'🎯 Recommend combo'};
  btn.textContent=labels[lang]||labels.es;
}

function clearFields(){
  document.getElementById('topic').value='';
  if(MODE_BLOCKS[mode]) MODE_BLOCKS[mode].forEach(b=>b.fields.forEach(f=>{const el=document.getElementById(f.id);if(el)el.value='random';}));
  document.getElementById('output-area').style.display='none';
  document.getElementById('ai-output-area').innerHTML='';
  updateTags();
}
function setMode(m){mode=m;numHosts=1;numGuests=0;document.querySelectorAll('.host-pill').forEach((p,i)=>p.classList.toggle('active',i===0));document.querySelectorAll('.guest-pill').forEach((p,i)=>p.classList.toggle('active',i===0));document.getElementById('topic').value='';document.getElementById('output-area').style.display='none';document.getElementById('ai-output-area').innerHTML='';fullRender();}

async function recommendCombo(){
  if(!_orKey){alert('Configura tu API key primero.');return;}
  const currentTopic=(document.getElementById('topic').value||'').trim();
  const btn=document.getElementById('recommend-combo');
  const area=document.getElementById('ai-output-area');
  btn.innerHTML='<span class="spinner"></span>'+(lang==='es'?'Analizando...':'Analyzing...');
  btn.disabled=true;
  area.innerHTML='';

  // Campos disponibles por modo para incluir en el prompt
  const modeFields={
    'ficticio-viral':['host-type','host-gender','host-region','guest-type','guest-gender','guest-region','guest-age','style','tone'],
    'true-crime':['host-type','host-gender','host-region','guest-type','guest-gender','guest-region','guest-age','style','tone'],
    'psicologia-oscura':['host-type','host-gender','host-region','guest-type','guest-gender','guest-region','guest-age','style','tone'],
    'conspiracion-moderna':['host-type','host-gender','host-region','guest-type','guest-gender','guest-region','guest-age','style','tone'],
    'documental-narrado':['narrator-type','narrator-gender','category','style','tone'],
    'testimonio-real':['narrator-type','narrator-gender','category','style','tone'],
    'reflexion-biblica':['narrator-type','narrator-gender','category','style','tone'],
    'ciencia-misterio':['narrator-type','narrator-gender','category','style','tone'],
    'finanzas-libertad':['narrator-type','narrator-gender','category','style','tone'],
    'mentalidad-disciplina':['narrator-type','narrator-gender','category','style','tone'],
    'historia-epica':['narrator-type','narrator-gender','category','style','tone'],
    'psicologia-positiva':['narrator-type','narrator-gender','category','style','tone'],
    'mente-masculina':['narrator-type','narrator-gender','category','style','tone'],
    'mujer-consciente':['narrator-type','narrator-gender','category','style','tone'],
    'misterio-biblico':['narrator-type','narrator-gender','narrator-lang','scene-type','subtopic','style','tone'],
    'libro-rapido':['narrator-type','narrator-gender','book-genre','style','tone'],
  };
  const fields=modeFields[mode]||['style','tone'];
  const allFields=[...fields,'set-style'];

  // Construir lista de valores válidos para el modo actual
  const ms=MODE_SELECTS[mode]||{};
  const validVals=fields.map(id=>{
    const opts=(ms[id]||{es:[],en:[]})[lang]||[];
    const vals=opts.filter(([v])=>v!=='random').map(([v])=>v).join('|');
    return `${id}: ${vals}`;
  }).join('\n')+'\nset-style: oscuro|moderno|natural|neon|biblioteca|mistico';

  const sys=lang==='es'
    ?'Eres experto en viralidad de YouTube Shorts. Dado el modo de podcast y un tema, sugieres la mejor configuración Y un tema viral específico si no se proporcionó. Responde SOLO con JSON.'
    :'You are a YouTube Shorts virality expert. Given the podcast mode and a topic, you suggest the best configuration AND a viral specific topic if not provided. Reply ONLY with JSON.';

  const topicInstruction=currentTopic
    ?`Tema actual: "${currentTopic}" (úsalo tal cual o mejóralo ligeramente)`
    :`No hay tema — sugiere un tema viral específico para el modo "${mode}" (campo "tema", máx 15 palabras)`;

  const usr=lang==='es'
    ?`Modo: ${mode}\n${topicInstruction}\n\nDevuelve SOLO este JSON:\n{"tema":"","razon":"","${allFields.join('":"","')}":""}\n\nValores válidos por campo:\n${validVals}\ntema: tema concreto y viral (máx 15 palabras)\nrazon: por qué esta combinación es viral (máx 18 palabras)`
    :`Mode: ${mode}\n${topicInstruction.replace('Tema actual','Current topic').replace('No hay tema','No topic')}\n\nReturn ONLY this JSON:\n{"tema":"","reason":"","${allFields.join('":"","')}":""}\n\nValid values per field:\n${validVals}\ntema: specific viral topic (max 15 words)\nreason: why this combination is viral (max 18 words)`;

  try{
    const raw=await _callOR(sys,usr,500);
    const m=raw.match(/\{[\s\S]*\}/);
    if(!m) throw new Error('JSON inválido');
    const rec=JSON.parse(m[0]);

    // Llenar el tema si vino o se sugirió
    const topicEl=document.getElementById('topic');
    if(topicEl&&rec.tema&&!currentTopic) topicEl.value=rec.tema;

    // Llenar los selects del modo
    fields.forEach(id=>{
      const el=document.getElementById(id);
      if(el&&rec[id]){const match=[...el.options].some(o=>o.value===rec[id]);if(match)el.value=rec[id];}
    });

    // Aplicar set-style recomendado
    const validSetStyles=['oscuro','moderno','natural','neon','biblioteca','mistico'];
    if(rec['set-style']&&validSetStyles.includes(rec['set-style'])){
      setStyle=rec['set-style'];
      document.querySelectorAll('[data-set]').forEach(b=>b.classList.toggle('active',b.dataset.set===setStyle));
    }

    const razon=rec.razon||rec.reason||'';
    const temaMsg=(!currentTopic&&rec.tema)?`<br><span style="color:#7c3aed;">📌 Tema sugerido: <strong>${rec.tema}</strong></span>`:'';
    const setNames={oscuro:'🕯️ Oscuro/Edison',moderno:'💡 Moderno/Softbox',natural:'🌿 Natural/Madera',neon:'🎨 Neon/Urbano',biblioteca:'📚 Biblioteca/Clásico',mistico:'🔮 Místico/Velas'};
    const setMsg=rec['set-style']&&validSetStyles.includes(rec['set-style'])?`<br><span style="color:#185fa5;">🎬 Set: <strong>${setNames[rec['set-style']]||rec['set-style']}</strong></span>`:'';
    area.innerHTML=`<div style="background:#f5f3ff;border:1px solid #c4b5fd;border-radius:8px;padding:10px 14px;font-size:12px;color:#4c1d95;margin-bottom:8px;">🎯 <strong>${lang==='es'?'Combo recomendado':'Recommended combo'}:</strong> ${razon}${temaMsg}${setMsg}</div>`;
    updateTags();
  }catch(e){
    area.innerHTML=`<div style="background:#fff1f2;border-radius:8px;padding:10px;font-size:12px;color:#9f1239;">❌ ${e.message}</div>`;
  }finally{
    btn.innerHTML='🎯 '+(lang==='es'?'Recomendar combo':'Recommend combo');
    btn.disabled=false;
  }
}
function setLang(l){lang=l;document.querySelectorAll('.lang-btn').forEach(b=>b.classList.toggle('active',b.dataset.lang===l));fullRender();}

// ── Templates fijos de producción ─────────────────────────────────────────────
const SET_SCENES={
  oscuro:{
    setup:`SCENE SETUP: Sitting at a moody dark podcast studio. Round wooden table in the foreground. Background: dark walls with vintage wooden shelves and crates, warm Edison bulb lanterns on both sides creating amber ambient glow. Dark defocused background with subtle warm bokeh.
MICROPHONE: professional desktop podcast microphone (Shure SM7B-style condenser, no logo) on a short desktop stand on the table surface — UPRIGHT, NO boom arm, NO diagonal arm. Positioned directly in front of the character on the table.`,
    lighting:(s)=>{const r=s==='host'?'camera-LEFT':'camera-RIGHT',d=s==='host'?'right':'left';return `LIGHTING: Warm amber rim light from ${r}. Deep cinematic shadows on ${d} side of face. Dark background with Edison lantern glow. Do NOT increase brightness or add fill light on later clips.`;}
  },
  moderno:{
    setup:`SCENE SETUP: Modern minimalist podcast studio. Clean white desk with light gray walls. Professional softbox lights visible in background. Sleek, neutral, contemporary aesthetic.
MICROPHONE: professional desktop podcast microphone (Shure SM7B-style condenser, no logo) on a short desktop stand on the desk surface — UPRIGHT, NO boom arm, NO diagonal arm.`,
    lighting:(s)=>{const r=s==='host'?'camera-LEFT':'camera-RIGHT';return `LIGHTING: Balanced soft softbox light from ${r}. Even professional fill light. No harsh shadows. Clean, crisp look. Do NOT alter light balance between clips.`;}
  },
  natural:{
    setup:`SCENE SETUP: Warm rustic podcast studio with natural wood and plants. Exposed brick wall, raw wooden table, hanging potted plants in background. Cozy warm incandescent bulbs overhead.
MICROPHONE: professional desktop podcast microphone (Shure SM7B-style condenser, no logo) on a short desktop stand on the table surface — UPRIGHT, NO boom arm, NO diagonal arm.`,
    lighting:(s)=>{const r=s==='host'?'camera-LEFT':'camera-RIGHT',d=s==='host'?'right':'left';return `LIGHTING: Warm golden rim light from ${r}. Soft earthy shadows on ${d} side of face. Warm incandescent glow from background. Do NOT over-brighten or add cool fill light.`;}
  },
  neon:{
    setup:`SCENE SETUP: Dark urban podcast studio with neon accent lighting. Black matte desk, dark walls with out-of-focus neon signs (purple, blue, pink) in background. Edgy modern aesthetic.
MICROPHONE: professional desktop podcast microphone (Shure SM7B-style condenser, no logo) on a short desktop stand on the desk surface — UPRIGHT, NO boom arm, NO diagonal arm.`,
    lighting:(s)=>{const r=s==='host'?'camera-LEFT':'camera-RIGHT',d=s==='host'?'right':'left';return `LIGHTING: Deep purple-blue neon rim light from ${r}. Dark dramatic shadows on ${d} side of face. Colorful neon bokeh in background. Do NOT wash out with white fill light.`;}
  },
  biblioteca:{
    setup:`SCENE SETUP: Classic library podcast setting. Dark mahogany desk, floor-to-ceiling shelves with old leather-bound books in background, warm incandescent reading lamp. Scholarly, timeless atmosphere.
MICROPHONE: professional desktop podcast microphone (Shure SM7B-style condenser, no logo) on a short desktop stand on the desk surface — UPRIGHT, NO boom arm, NO diagonal arm.`,
    lighting:(s)=>{const r=s==='host'?'camera-LEFT':'camera-RIGHT',d=s==='host'?'right':'left';return `LIGHTING: Warm desk lamp amber glow from ${r}. Soft intellectual shadows on ${d} side of face. Classic warm tone. No modern LED fill light. Do NOT alter color temperature between clips.`;}
  },
  mistico:{
    setup:`SCENE SETUP: Mystical dark studio with candle lighting. Stone-textured dark walls, multiple tall white candles burning on and around the table, ancient artifacts, crystals, and dried herbs visible. Atmospheric and mysterious.
MICROPHONE: professional desktop podcast microphone (Shure SM7B-style condenser, no logo) on a short desktop stand on the table surface — UPRIGHT, NO boom arm, NO diagonal arm.`,
    lighting:(s)=>{const r=s==='host'?'camera-LEFT':'camera-RIGHT',d=s==='host'?'right':'left';return `LIGHTING: Flickering orange candle rim light from ${r}. Deep dramatic shadows on ${d} side of face. Warm mysterious candle glow from background. No electric fill light. Do NOT stabilize flicker between clips.`;}
  }
};

function getScene(){return SET_SCENES[setStyle]||SET_SCENES.oscuro;}

function buildHostImagePrompt(charDesc){
  const sc=getScene();
  return `Ultra-realistic cinematic portrait of a podcast host. ${charDesc}

${sc.setup}

POSE — HOST POSITION:
3/4 side-profile facing RIGHT — head and body angled clearly to the RIGHT side of frame.
Looking attentively toward the RIGHT, as if the guest is seated to the right.
Eye line directed clearly to the RIGHT. NOT toward camera.
In the two-shot edit, this character will be placed on the LEFT side of frame — so this rightward gaze points toward the guest on the right.

${sc.lighting('host')}
IMAGE QUALITY: ultra-realistic, 8K detail, sharp focus, visible pores, no beauty filters, no auto-enhancement.
FORMAT: vertical 9:16 aspect ratio, 1024x1792. Black border top 12% for safe area.`;
}

function buildGuestImagePrompt(genderWord, charDetails){
  const sc=getScene();
  return `Ultra-realistic cinematic portrait for a podcast guest. Generate a completely new ${genderWord} character — do NOT reuse any person from previous images.

CHARACTER DETAILS:
${charDetails}

${sc.setup}

POSE — GUEST POSITION:
3/4 side-profile facing LEFT — head and body angled clearly to the LEFT side of frame.
Looking attentively toward the LEFT, as if the host is seated to the left.
Eye line directed clearly to the LEFT. NOT toward camera.
In the two-shot edit, this character will be placed on the RIGHT side of frame — so this leftward gaze will point toward the host on the left.

${sc.lighting('guest')}
IMAGE QUALITY: ultra-realistic, 8K detail, sharp focus, visible pores, no beauty filters.
FORMAT: vertical 9:16, 1024x1792. Keep top black border identical to Image A.`;
}

const VEO3_RESTRICTIONS=`❌ NO SUBTITLES. NO captions. NO burned-in text of any kind. NO watermarks. Clean video only.
❌ NO auto-enhancement. NO sharpness boost. NO extra lighting on face between clips.
❌ NO variation in character appearance from clip to clip — same face, same hair, same skin tone, same lighting ratio, same depth of field.`;

const VEO3_POSE=(facesDir)=>`Strict side-profile (3/4 angle), looking off-camera to the ${facesDir}. Addressing someone seated to their ${facesDir}. Subtle organic micro-movements only: slow blink, slight chest breathing. NO head turns. NO hand gestures. Professional desktop podcast microphone (Shure SM7B-style condenser, no logo) on a short desktop stand on the table surface — UPRIGHT, NO boom arm, NO diagonal arm.`;

const VEO3_CAMERA=`CAMERA: 100% static. No zoom in or out. No pan. Only imperceptible organic micro-shake from breathing.
FORMAT: Vertical 9:16, 1024x1792. No letterboxing, no pillarboxing.`;

const VEO3_LIGHTING=(speaker)=>getScene().lighting(speaker);

function buildClipPrompt(clipNum,total,sec,speaker,spkLabel,visualConsistency,voiceConsistency,dialogue){
  const facesDir=speaker==='host'?'RIGHT':'LEFT';
  const toward  =speaker==='host'?'guest':'host';
  return `=== PROMPT GOOGLE FLOW / VEO 3 — CLIP ${clipNum} / ${total} ===
Duration: ${sec} seconds
Character: ${spkLabel}
${spkLabel.toUpperCase()} POSITION: faces ${facesDir} — toward ${toward}.

${VEO3_RESTRICTIONS}

⚠️ VISUAL CONSISTENCY — paste this IDENTICALLY in every clip of this character:
${visualConsistency}
Lighting ratio: unchanged from clip to clip. No sharpness increase on last clips. Hair style and volume: identical to clip 1. Skin texture: same natural imperfections, no smoothing. Depth of field: same blur radius on background. NO auto-beautification between clips.

POSE & ACTION:
${VEO3_POSE(facesDir)}

⚠️ VOICE CONSISTENCY — paste this IDENTICALLY in every clip of this character:
${voiceConsistency}

DIALOGUE (spoken aloud — lip-sync required, character's lips must match every word):
"${dialogue}"

${VEO3_LIGHTING(speaker)}
${VEO3_CAMERA}`;
}

const PODCAST_MODES=['ficticio-viral','true-crime','psicologia-oscura','conspiracion-moderna'];
const NARRATOR_MODES=['documental-narrado','ciencia-misterio','finanzas-libertad','mentalidad-disciplina','historia-epica','psicologia-positiva','testimonio-real','misterio-biblico','mente-masculina','mujer-consciente','libro-rapido','reflexion-biblica'];

function buildNarratorImagePrompt(charDesc,setting,sceneType='solo',lightingRole='host',charLabel=''){
  const sc=getScene();
  const roleWord=charLabel||(lightingRole==='host'?'host':'guest');
  let poseBlock;
  if(sceneType==='panel'){
    poseBlock=`POSE — PANEL PARTICIPANT (${roleWord.toUpperCase()}):
Seated at a round table. Slight 3/4 turn toward camera. Other participants slightly visible/blurred in background. Natural panel discussion posture.
Engaged expression, leaning slightly forward, hands resting naturally on table.`;
  } else if(sceneType==='duo'){
    poseBlock=`POSE — ${roleWord.toUpperCase()}:
Slight profile (3/4 angle) facing conversation partner. Natural engaged expression, open body language, subtle lean toward partner.
Relaxed shoulders, natural breathing stance.`;
  } else {
    poseBlock=`POSE — ${roleWord.toUpperCase()}:
Faces camera directly or slight 3/4 angle toward camera.
Natural confident expression, engaging energy, slight lean forward.
Subtle organic posture: natural breathing stance, relaxed shoulders.`;
  }
  const lightingDirective=sceneType==='panel'
    ?sc.lighting('host').replace('camera-LEFT','camera-FRONT-LEFT').replace('toward the guest on the right','toward other participants')
    :sc.lighting(lightingRole);
  return `Ultra-realistic cinematic portrait of a video ${roleWord}. ${charDesc}

SCENE: ${setting}
${sc.setup.split('MICROPHONE:')[0].trim()}

${poseBlock}

${lightingDirective}
IMAGE QUALITY: ultra-realistic, 8K detail, sharp focus, visible pores, no beauty filters, no auto-enhancement.
FORMAT: vertical 9:16 aspect ratio, 1024x1792. Clean space at top 15% for text overlay.`;
}

function buildNarratorClipPrompt(clipNum,total,sec,visual,voice,setting,dialogue,lightingRole='host',charLabel='Narrator'){
  const sc=getScene();
  const lightingDirective=sc.lighting(lightingRole);
  return `=== PROMPT GOOGLE FLOW / VEO 3 — CLIP ${clipNum} / ${total} ===
Duration: ${sec} seconds
Character: ${charLabel}

${VEO3_RESTRICTIONS}

⚠️ VISUAL CONSISTENCY — paste this IDENTICALLY in every clip of ${charLabel}:
${visual}
Lighting ratio: unchanged clip to clip. Hair style and volume: identical to clip 1. Skin texture: same natural imperfections, no smoothing. Depth of field: same blur radius on background. NO auto-beautification between clips.

POSE & ACTION:
${charLabel} faces camera directly (slight 3/4 angle). Engaged, confident energy. Subtle organic micro-movements: slow blink, slight chest breathing. NO sudden gestures. NO abrupt head turns. Eye contact with camera maintained throughout.

SCENE / BACKGROUND (keep identical across all clips):
${setting}

⚠️ VOICE CONSISTENCY — paste this IDENTICALLY in every clip of ${charLabel}:
${voice}

DIALOGUE (spoken aloud — lip-sync required, ${charLabel}'s lips must match every word):
"${dialogue}"

${lightingDirective}
${VEO3_CAMERA}`;
}

async function generateNarratorPackage(){
  const btn=document.getElementById('generate');
  const area=document.getElementById('output-area');
  const blocksEl=document.getElementById('output-blocks');
  btn.innerHTML='<span class="spinner"></span>'+(lang==='es'?'Generando...':'Generating...');
  btn.disabled=true;
  area.style.display='block';
  blocksEl.innerHTML=`<div style="text-align:center;padding:24px;color:#888;font-size:12px;">🎬 ${lang==='es'?'Generando paquete completo...':'Generating full package...'}</div>`;

  const topic=(gv('topic')||'').trim()||(mode==='libro-rapido'?pick(RAND_TOPICS_LIBRO[lang]):pick(RAND_TOPICS[mode]?.[lang]||[]))||'tema general';
  const {clips,sec}=DUR_CLIPS[dur]||{clips:8,sec:8};
  const narratorType=gv('narrator-type')||'random';
  const narratorGender=gv('narrator-gender')||'male';
  const category=gv('category')||'random';
  const styleV=gv('style')||'random';
  const toneV=gv('tone')||'random';

  const MODE_CTX={
    'documental-narrado':{es:'documental narrado estilo NatGeo/BBC con narrador de voz en off',en:'NatGeo/BBC style narrated documentary with voice-over narrator'},
    'ciencia-misterio':{es:'canal de divulgación científica y misterios del universo',en:'science mystery and universe exploration channel'},
    'finanzas-libertad':{es:'canal de educación financiera viral y mentalidad de riqueza',en:'viral financial education and wealth mindset channel'},
    'mentalidad-disciplina':{es:'canal motivacional de mentalidad, hábitos y disciplina extrema',en:'motivational mindset, habits and extreme discipline channel'},
    'historia-epica':{es:'canal de historia épica cinematográfica — batallas, imperios, héroes',en:'cinematic epic history channel — battles, empires, heroes'},
    'psicologia-positiva':{es:'canal de psicología positiva y bienestar emocional',en:'positive psychology and emotional wellness channel'},
    'testimonio-real':{es:'canal de testimonios reales en primera persona, confesional',en:'real first-person confessional testimony channel'},
    'misterio-biblico':{es:'canal de misterios bíblicos y textos apócrifos',en:'biblical mysteries and apocryphal texts channel'},
    'mente-masculina':{es:'canal de reflexiones profundas sobre masculinidad consciente, emociones, amor propio y propósito — especialmente dirigido a hombres',en:'deep reflections channel on conscious masculinity, emotions, self-love and purpose — especially aimed at men'},
    'mujer-consciente':{es:'canal de empoderamiento femenino consciente — autoestima, sanación, relaciones, límites y propósito — especialmente dirigido a mujeres',en:'conscious feminine empowerment channel — self-worth, healing, relationships, boundaries and purpose — especially aimed at women'},
    'libro-rapido':{es:'canal de resúmenes virales de libros — un narrador presenta ideas clave de un libro de forma emocionante y directa al espectador',en:'viral book summary channel — a narrator presents key ideas from a book in an exciting, direct-to-viewer style'},
    'reflexion-biblica':{es:'canal de devocionales bíblicos cortos y profundos — un narrador o pastor presenta reflexiones espirituales con versículos y aplicación práctica',en:'short deep biblical devotional channel — a narrator or pastor shares spiritual reflections with verses and practical application'}
  };
  const MODE_SETTING={
    'documental-narrado':'Documentary studio or relevant environmental backdrop, dramatic lighting, cinematic atmosphere',
    'ciencia-misterio':'Dark minimal science environment — subtle galaxy bokeh or abstract cosmic background, cool blue/purple tones',
    'finanzas-libertad':'Modern minimal home office, warm neutral tones, soft bokeh with books or a plant in background',
    'mentalidad-disciplina':'Dark industrial loft or gym environment, dramatic side lighting, high-contrast shadows, motivated energy',
    'historia-epica':'Ancient stone architecture or dramatic cinematic landscape, warm torch-like amber lighting, epic atmosphere',
    'psicologia-positiva':'Warm cozy interior, soft golden natural light, plants or flowers in background, calm healing atmosphere',
    'testimonio-real':'Dimly lit intimate room, single warm practical light source from one side, raw confessional atmosphere',
    'misterio-biblico':'Candlelit stone room, ancient scrolls or artifacts on table, mysterious dramatic shadows, mystical atmosphere',
    'mente-masculina':'Dark minimal masculine space — leather chair or raw wooden desk, warm amber side light, dramatic shadows, books and a single plant, serious contemplative atmosphere',
    'mujer-consciente':'Warm feminine minimal space — soft cream or blush tones, natural window light, fresh flowers or greenery in background, candles, elegant and intimate healing atmosphere',
    'libro-rapido':'Modern minimal home studio — book shelf with colorful spines in background, warm neutral desk lamp, clean professional setup, intellectual and inviting atmosphere',
    'reflexion-biblica':'Peaceful warm interior — soft candlelight or window light, open Bible on desk, subtle cross or neutral spiritual decor, calm and reverent atmosphere'
  };

  const ctx=(MODE_CTX[mode]||{})[lang]||MODE_CTX[mode]?.es||mode;
  const settingHint=MODE_SETTING[mode]||'Clean minimal studio with relevant thematic background';

  // ── Paleta de colores por narrador ──────────────────────────────────────────
  const NARRATOR_COLORS=['#185fa5','#7c3aed','#e11d48','#d97706'];

  // ── Prompt de IA (unified multi-narrator format) ─────────────────────────────
  const numH=numHosts;
  const numG=numGuests;
  const n=numH+numG;  // total characters
  const isMulti=n>1;

  // Genera labels según rol: Host / Invitado (o Host 1, Host 2… si hay varios)
  function getNarratorLabel(i){
    const isHost=i<numH;
    if(isHost){
      return numH>1?(lang==='es'?`Host ${i+1}`:`Host ${i+1}`):(lang==='es'?'Host':'Host');
    } else {
      const gi=i-numH+1;
      return numG>1?(lang==='es'?`Invitado ${gi}`:`Guest ${gi}`):(lang==='es'?'Invitado':'Guest');
    }
  }
  const isPanel=n>=3;  // 3+ = round table setup

  const sceneDesc=n===1?'featuring a single narrator':n===2?'featuring a host and a guest in an interview format':`featuring a panel of ${n} participants around a round table`;
  const sys=`You are a creative director for YouTube Shorts ${ctx} videos ${sceneDesc}. Reply ONLY with valid JSON — no markdown, no extra text.`;

  // Override settingHint for panel scenes
  const PANEL_SETTINGS={
    'finanzas-libertad':'Round table financial discussion studio — participants seated around a modern circular table, professional broadcast lighting, warm neutral tones, books and financial props',
    'mentalidad-disciplina':'Round table motivation studio — participants seated around a modern circular table, dramatic side lighting, high-contrast industrial atmosphere',
    'historia-epica':'Round table historian panel — participants seated around an ancient stone circular table, warm amber torch-like lighting, epic cinematic atmosphere',
    'ciencia-misterio':'Round table science panel — participants seated around a sleek circular table, cool blue/purple cosmic lighting, abstract cosmic background',
    'documental-narrado':'Round table documentary studio — participants seated around a modern circular broadcast table, dramatic cinematic lighting',
    'testimonio-real':'Round table intimate discussion — participants seated around a dim circular table, single warm practical light, raw confessional atmosphere',
    'misterio-biblico':'Round table ancient study — participants seated around a stone circular table, candlelit mystical atmosphere, ancient scrolls visible',
    'psicologia-positiva':'Round table wellness panel — participants seated around a light circular table, soft golden natural light, plants and flowers in background',
    'mente-masculina':'Round table masculine panel — participants seated around a dark minimal circular table, warm amber dramatic side lighting, leather chairs, raw honest contemplative atmosphere',
    'mujer-consciente':'Round table feminine panel — participants seated around a light circular table with fresh flowers, soft warm natural light, cream and blush tones, intimate empowering atmosphere',
    'libro-rapido':'Round table book club — participants seated around a modern circular table with books visible, warm professional lighting, intellectual discussion atmosphere',
    'reflexion-biblica':'Round table spiritual discussion — participants seated around a calm circular table, soft candlelit atmosphere, open Bibles or spiritual texts visible, peaceful and reverent'
  };
  const STYLE_ATMOSPHERE={
    oscuro:'Dark moody atmosphere — single warm Edison rim light, deep dramatic shadows, very dark walls, intimate',
    moderno:'Modern bright studio — clean white LED softbox panels, minimal background, crisp professional lighting',
    natural:'Natural warm tones — wooden desk, indoor plants, soft diffused window light, warm earth tones',
    neon:'Dark studio with colorful neon accent lighting — purple/blue/pink neon bokeh in background, dramatic dark shadows',
    biblioteca:'Classic library — warm amber desk lamp, floor-to-ceiling bookshelves, scholarly warm tones',
    mistico:'Mystical candlelit — multiple tall white candles, stone textures, ancient artifacts, flickering orange light'
  };
  const styleAtm=STYLE_ATMOSPHERE[setStyle]||'';
  const baseHint=isPanel?(PANEL_SETTINGS[mode]||`Round table panel studio — ${n} participants seated around a modern circular table, thematic background`):settingHint;
  const effectiveSettingHint=styleAtm?`${baseHint}. Lighting/atmosphere: ${styleAtm}`:baseHint;

  // Build narrator entries for the prompt with proper roles
  const narratorEntries=Array.from({length:n},(_,i)=>{
    const isHost=i<numH;
    const roleLabel=isHost?(numH>1?`Host ${i+1}`:'Host'):(numG>1?`Guest ${i+1-numH}`:'Guest');
    const role=isHost?'host':'guest';
    return `    {
      "id": ${i+1},
      "role": "${role}",
      "char_desc": "[gender word], [age range], [hair], [clothing — no logos], [distinctive feature], [expression]. Example: Adult woman, 30-40, wavy auburn hair, dark blazer, warm confident smile.",
      "visual": "Key visual traits identical across all clips for ${roleLabel}: gender, age, hair, clothing, marks.",
      "voice": "Voice profile ${roleLabel}: [age]-year-old, [voice texture], [delivery style]. Temperament: [baseline]. CRITICAL: keep EXACT across all clips.",
      "image_scene": "One-line ChatGPT scene: ${roleLabel} in setting, mood."
    }`;
  }).join(',\n');

  const clipPattern=isMulti
    ?`{"narrator_id":[1-${n} rotating],"dialogue":"[max 26 words]"}`
    :`{"dialogue":"[max 28 words]"}`;

  const usr=`Topic: "${topic}" | Mode: ${mode} | Category: ${category} | Style: ${styleV} | Tone: ${toneV}
Narrators: ${n} (${numH} host${numH>1?'s':''} + ${numG} guest${numG>1?'s':''}) | Primary gender: ${narratorGender}, type: ${narratorType}
Clips: ${clips} × ${sec}s | Setting hint: ${effectiveSettingHint}

Return ONLY this JSON (no markdown):
{
  "narrators": [
${narratorEntries}
  ],
  "shared_setting": "Detailed Veo 3 scene shared by all narrators: background, lighting, mood, key props. Keep identical across all clips.",
  "clips": [
    ${clipPattern}
  ],
  "hook": "Viral hook — max 130 chars",
  "copy": "Social caption — 2-3 short lines",
  "tags_tiktok": ["#tag1","#tag2","#tag3","#tag4","#tag5"],
  "tags_facebook": ["#tag1","#tag2","#tag3","#tag4","#tag5","#tag6","#tag7","#tag8"],
  "tags_youtube": ["#tag1","#tag2","#tag3","#tag4"],
  "thumbnail_prompt": "Vertical 9:16 ChatGPT/DALL-E thumbnail — dramatic, high contrast, text space top 20%"
}
Rules:
- narrators: exactly ${n} objects with unique distinct appearances and assigned roles (host/guest)
- clips: exactly ${clips} items${isMulti?`, rotate narrator_id 1-${n} evenly across all ${n} characters, escalate tension progressively`:', escalate progressively'}
- All dialogue in ${lang==='es'?'Spanish':'English'}
- hook and copy in ${lang==='es'?'Spanish':'English'}
- hashtags lowercase, no spaces`;

  try{
    window._pStore=[];
    const raw=await _callOR(sys,usr,4500);
    const m=raw.match(/\{[\s\S]*\}/);
    if(!m) throw new Error(lang==='es'?'La IA no devolvió JSON válido':'AI did not return valid JSON');
    const data=JSON.parse(m[0]);

    const narratorsArr=Array.isArray(data.narrators)?data.narrators:[];
    // Fallback: si la IA devolvió formato antiguo (single narrator fields)
    if(narratorsArr.length===0 && data.narrator_char_desc){
      narratorsArr.push({id:1,char_desc:data.narrator_char_desc,visual:data.narrator_visual||'',voice:data.narrator_voice||'',image_scene:data.narrator_image_scene||''});
    }
    const sharedSetting=data.shared_setting||data.narrator_setting||'';
    const clipsArr=Array.isArray(data.clips)?data.clips:[];
    const socialHook=data.hook||'';
    const socialCopy=data.copy||'';
    const tagsTT=Array.isArray(data.tags_tiktok)?data.tags_tiktok:[];
    const tagsFB=Array.isArray(data.tags_facebook)?data.tags_facebook:[];
    const tagsYT=Array.isArray(data.tags_youtube)?data.tags_youtube:[];
    const thumbP=data.thumbnail_prompt||'';

    const castDesc=numG===0?(lang==='es'?`${numH} narrador${numH>1?'es':''}`:`${numH} narrator${numH>1?'s':''}`): (lang==='es'?`${numH} host${numH>1?'s':''} + ${numG} invitado${numG>1?'s':''}`:`${numH} host${numH>1?'s':''} + ${numG} guest${numG>1?'s':''}`);
    document.getElementById('config-out').textContent=
      `MODO: ${MODES[mode].title[lang].toUpperCase()} | ${dur} min · ${clips} clips × ${sec}s | ${castDesc} | MODELO: ${getActiveModel()}\nTEMA: ${topic}`;

    window._allPrompts=[];

    // ── Header ────────────────────────────────────────────────────────────────
    let html=`<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px;gap:8px;flex-wrap:wrap;">
      <strong style="font-size:13px;color:#1a1a1a;">🎬 Paquete completo · ${castDesc}</strong>
      <div style="display:flex;gap:6px;">
        <button onclick="window.scrollTo({top:0,behavior:'smooth'})" style="height:28px;padding:0 10px;font-size:11px;background:#f0ede2;color:#1a1a1a;border:none;border-radius:6px;cursor:pointer;" data-i18n="backToTop">⬆️ Volver arriba</button>
        <button onclick="copyAllPrompts()" style="height:28px;padding:0 12px;font-size:11px;background:#1a1a1a;color:#fff;border:none;border-radius:6px;cursor:pointer;">📋 Copiar todo</button>
      </div>
    </div>`;

    // ── Prompts de imagen por narrador ────────────────────────────────────────
    const imgSceneType=isPanel?'panel':isMulti?'duo':'solo';
    narratorsArr.forEach((nr,i)=>{
      const color=NARRATOR_COLORS[i]||'#185fa5';
      const label=getNarratorLabel(i);
      const imgLightRole=isPanel?'host':(i===0?'host':'guest');
      const imgP=buildNarratorImagePrompt(nr.char_desc||'',nr.image_scene||sharedSetting,imgSceneType,imgLightRole,label);
      if(imgP) window._allPrompts.push(`=== PROMPT ${label.toUpperCase()} (ChatGPT) ===\n${imgP}`);
      window._pStore.push(imgP);
      const imgIdx=window._pStore.length-1;
      html+=`<div class="clip-card" style="border-left:3px solid ${color};">
        <div class="clip-header" style="color:${color};">📸 ${label.toUpperCase()} — ChatGPT (genera imagen)</div>
        <div style="font-size:10.5px;color:#666;margin-bottom:6px;">Pega en ChatGPT con tu foto base para generar al ${label.toLowerCase()}.</div>
        <div class="clip-voice">${imgP}</div>
        <button class="clip-copy" onclick="copyTxt(window._pStore[${imgIdx}])">📋 Copiar</button>
      </div>`;
    });

    // ── Clips Veo 3 ───────────────────────────────────────────────────────────
    if(clipsArr.length){
      html+=`<div style="font-size:11px;font-weight:700;color:#444;text-transform:uppercase;letter-spacing:0.5px;margin:16px 0 8px;">📹 ${clipsArr.length} clips · Google Veo 3 / Flow</div>`;
      clipsArr.forEach((c,i)=>{
        const nIdx=isMulti?((c.narrator_id||1)-1):0;
        const nr=narratorsArr[nIdx]||narratorsArr[0]||{};
        const color=NARRATOR_COLORS[nIdx]||'#185fa5';
        const label=getNarratorLabel(nIdx);
        const dialogue=c.dialogue||'';
        const clipLightRole=isPanel?'host':(nIdx===0?'host':'guest');
        const fullPrompt=buildNarratorClipPrompt(i+1,clipsArr.length,sec,nr.visual||'',nr.voice||'',sharedSetting,dialogue,clipLightRole,label);
        window._allPrompts.push(fullPrompt);
        window._pStore.push(fullPrompt);
        const clipIdx=window._pStore.length-1;
        html+=`<div class="clip-card">
          <div class="clip-header" style="display:flex;justify-content:space-between;align-items:center;">
            <span>📹 CLIP ${i+1} / ${clipsArr.length} &nbsp;·&nbsp; ${sec}s</span>
            <span style="font-size:10px;font-weight:700;color:${color};background:${color}18;padding:2px 8px;border-radius:20px;">${label.toUpperCase()}</span>
          </div>
          <div class="clip-section">
            <strong style="font-size:10px;color:${color};">PROMPT COMPLETO → Google Veo 3 / Flow</strong>
            <div class="clip-voice">${fullPrompt}</div>
          </div>
          <button class="clip-copy" onclick="copyTxt(window._pStore[${clipIdx}])">📋 Copiar clip ${i+1}</button>
        </div>`;
      });
    }

    // ── Paquete redes sociales ────────────────────────────────────────────────
    const tagRow=(tags,tColor,tLabel)=>{
      if(!tags||!tags.length) return '';
      const tagStr=tags.join(' ');
      window._pStore.push(tagStr);
      const tIdx=window._pStore.length-1;
      return `<div style="margin-bottom:6px;"><span style="font-size:9px;font-weight:700;color:${tColor};text-transform:uppercase;letter-spacing:0.5px;">${tLabel}</span><br><span style="font-size:11px;color:#444;">${tagStr}</span><button class="clip-copy" style="margin-left:8px;" onclick="copyTxt(window._pStore[${tIdx}])">📋</button></div>`;
    };
    if(socialHook||socialCopy||tagsTT.length||tagsFB.length||tagsYT.length||thumbP){
      let socContent='';
      if(socialHook){
        const hookCopy=socialHook+(socialCopy?'\n\n'+socialCopy:'');
        window._pStore.push(hookCopy);
        const hookIdx=window._pStore.length-1;
        socContent+=`<div style="background:#f0f9ff;border-radius:8px;padding:10px;margin-bottom:8px;"><div style="font-size:10px;font-weight:700;color:#0369a1;margin-bottom:4px;">🪝 HOOK / CAPTION</div><div style="font-size:12px;color:#1a1a1a;font-weight:500;">${socialHook}</div>${socialCopy?`<div style="font-size:11px;color:#555;margin-top:4px;white-space:pre-line;">${socialCopy}</div>`:''}<button class="clip-copy" onclick="copyTxt(window._pStore[${hookIdx}])">📋 Copiar copy</button></div>`;
      }
      if(tagsTT.length||tagsFB.length||tagsYT.length){
        socContent+=`<div style="background:#fafafa;border:0.5px solid rgba(0,0,0,0.1);border-radius:8px;padding:10px;margin-bottom:8px;">${tagRow(tagsTT,'#000','TikTok (máx 5)')}${tagRow(tagsFB,'#1877f2','Facebook (máx 8)')}${tagRow(tagsYT,'#ff0000','YouTube (máx 4)')}</div>`;
      }
      if(thumbP){
        window._pStore.push(thumbP);
        const thumbIdx=window._pStore.length-1;
        socContent+=`<div style="background:#fff8f0;border-radius:8px;padding:10px;"><div style="font-size:10px;font-weight:700;color:#d97706;margin-bottom:4px;">🖼️ PROMPT PORTADA — ChatGPT / DALL-E</div><div class="clip-voice">${thumbP}</div><button class="clip-copy" onclick="copyTxt(window._pStore[${thumbIdx}])">📋 Copiar prompt portada</button></div>`;
      }
      html+=`<div class="clip-card" style="border-left:3px solid #0ea5e9;">
        <div class="clip-header" style="color:#0369a1;">📱 Paquete redes sociales</div>
        ${socContent}
      </div>`;
    }

    blocksEl.innerHTML=html;
    area.scrollIntoView({behavior:'smooth',block:'start'});
  }catch(e){
    blocksEl.innerHTML=`<div style="background:#fff1f2;border-radius:8px;padding:12px;font-size:12px;color:#9f1239;">❌ ${e.message}</div>`;
  }finally{
    btn.innerHTML='⚡ '+(lang==='es'?'Generar prompts':'Generate prompts');
    btn.disabled=false;
  }
}

async function generate(){
  if(!_orKey){alert(lang==='es'?'Configura tu API key primero.':'Configure your API key first.');return;}
  if(NARRATOR_MODES.includes(mode)){
    await generateNarratorPackage();
    return;
  }
  if(!PODCAST_MODES.includes(mode)){
    const genBtn=document.getElementById('generate');
    genBtn.innerHTML='<span class="spinner"></span>'+(lang==='es'?'Generando...':'Generating...');
    genBtn.disabled=true;
    try{await generateWithAI(true);}finally{
      genBtn.innerHTML='⚡ '+(lang==='es'?'Generar prompts':'Generate prompts');
      genBtn.disabled=false;
    }
    const outEl=document.getElementById('ai-output-area');
    if(outEl)outEl.scrollIntoView({behavior:'smooth',block:'start'});
    return;
  }
  const btn=document.getElementById('generate');
  const area=document.getElementById('output-area');
  const blocksEl=document.getElementById('output-blocks');
  btn.innerHTML='<span class="spinner"></span>'+(lang==='es'?'Generando...':'Generating...');
  btn.disabled=true;
  area.style.display='block';
  blocksEl.innerHTML=`<div style="text-align:center;padding:24px;color:#888;font-size:12px;">🎬 ${lang==='es'?'Generando paquete completo...':'Generating full package...'}</div>`;

  const topic=(gv('topic')||'').trim()||(mode==='libro-rapido'?pick(RAND_TOPICS_LIBRO[lang]):pick(RAND_TOPICS[mode]?.[lang]||[]));
  const {clips,sec}=DUR_CLIPS[dur];
  const styleV=gv('style')||'conspirativo';
  const toneV =gv('tone')||'tenso';
  const numClips=clips;

  const hostGender =gv('host-gender')||'male';
  const hostType   =gv('host-type')||'periodista-investigador';
  const hostRegion =gv('host-region')||'latam-neutro';
  const guestGender=gv('guest-gender')||'female';
  const guestType  =gv('guest-type')||'sobreviviente';
  const guestRegion=gv('guest-region')||'latam-neutro';
  const guestAge   =gv('guest-age')||'25-35';

  const MODE_CONTEXT={
    'ficticio-viral':'dark mystery fictional podcast — host presses, guest reveals something disturbing',
    'true-crime':'true crime investigation podcast — a detective/journalist interrogates a witness, suspect, or survivor of a real or fictional criminal case',
    'psicologia-oscura':'dark psychology podcast — an expert exposes manipulation tactics, narcissism, or toxic behaviors while a survivor shares their experience',
    'conspiracion-moderna':'modern conspiracy podcast — a journalist interviews a whistleblower or tech expert about surveillance, AI, elites, or hidden power structures'
  };
  const sys=`You are a creative director for YouTube Shorts ${MODE_CONTEXT[mode]||'dark podcast'} videos.
You write character descriptions and dialogue. Reply ONLY with valid JSON — no markdown, no extra text.`;

  const usr=`Topic: "${topic}" | Mode: ${mode} | Style: ${styleV} | Tone: ${toneV}
HOST: ${hostGender}, ${hostType}, region: ${hostRegion}
GUEST: ${guestGender}, ${guestType}, region: ${guestRegion}, age: ${guestAge}
Clips: ${numClips} × ${sec}s

Return ONLY this JSON (no markdown):
{
  "host_char_desc": "One line: [gender word], [age range], [hair], [key clothing — no logos], [distinctive physical feature], [expression/gaze]. Example: Adult woman, 40-50, long dark hair, visible tattoos, black leather jacket, dark eye makeup. Worn intense gaze.",
  "guest_char_details": "Multi-line block:\\n[gender word], [age from ${guestAge}], [region] origin. [clothing — no logos, no text]. [distinctive feature]. [expression].",
  "host_visual": "One sentence of key visual traits to keep identical across all host clips: gender, age, hair, clothing, distinctive marks.",
  "host_voice": "Voice profile: [age]-year-old [region] ${hostGender}, [voice texture: gravelly/smooth/breathy/raspy], [accent description], [delivery: slow/fast, pauses, bursts]. Temperament: [baseline]. CRITICAL: maintain this EXACT voice profile across all clips of this character without variation.",
  "guest_visual": "One sentence of key visual traits to keep identical across all guest clips: gender, age, hair, clothing, distinctive marks.",
  "guest_voice": "Voice profile: [age]-year-old [region] ${guestGender}, [voice texture], [accent], [delivery style]. Temperament: [baseline]. CRITICAL: maintain this EXACT voice profile across all clips of this character without variation.",
  "clips": [
    {"speaker":"host","dialogue":"[max 22 words — impactful opening]"},
    {"speaker":"guest","dialogue":"[max 22 words]"}
  ],
  "hook": "Viral hook for the caption — max 130 chars, creates curiosity, ends on suspense",
  "copy": "Full social caption — 2-3 short impactful lines, no emojis spam",
  "tags_tiktok": ["#tag1","#tag2","#tag3","#tag4","#tag5"],
  "tags_facebook": ["#tag1","#tag2","#tag3","#tag4","#tag5","#tag6","#tag7","#tag8"],
  "tags_youtube": ["#tag1","#tag2","#tag3","#tag4"],
  "thumbnail_prompt": "Ultra-realistic vertical 9:16 thumbnail prompt for ChatGPT/DALL-E — dramatic scene, high contrast, space for text overlay at top 20%"
}
Rules:
- clips: exactly ${numClips} items, alternate host/guest, escalate tension toward a dark revelation
- All dialogue must be written in ${lang==='es'?'Spanish':'English'} only
- hook and copy must be in ${lang==='es'?'Spanish':'English'}
- hashtags: relevant, no spaces, lowercase, trending for the topic
- host_char_desc: single line like the example
- guest_char_details: 2-3 lines with line breaks`;

  try{
    const raw=await _callOR(sys,usr,4000);
    const m=raw.match(/\{[\s\S]*\}/);
    if(!m) throw new Error('JSON inválido');
    const data=JSON.parse(m[0]);

    const hostImageP =buildHostImagePrompt(data.host_char_desc||'');
    const guestGenderWord=guestGender==='female'?'female':'male';
    const guestImageP=buildGuestImagePrompt(guestGenderWord, data.guest_char_details||'');
    const hostVisual =data.host_visual||'';
    const hostVoice  =data.host_voice||'';
    const guestVisual=data.guest_visual||'';
    const guestVoice =data.guest_voice||'';
    const clipsArr   =Array.isArray(data.clips)?data.clips:[];
    const socialHook =data.hook||'';
    const socialCopy =data.copy||'';
    const tagsTT     =Array.isArray(data.tags_tiktok)?data.tags_tiktok:[];
    const tagsFB     =Array.isArray(data.tags_facebook)?data.tags_facebook:[];
    const tagsYT     =Array.isArray(data.tags_youtube)?data.tags_youtube:[];
    const thumbP     =data.thumbnail_prompt||'';

    document.getElementById('config-out').textContent=
      `MODO: ${MODES[mode].title[lang].toUpperCase()} | ${dur} min · ${numClips} clips × ${sec}s | MODELO: ${getActiveModel()}\nTEMA: ${topic}`;

    window._allPrompts=[];
    if(hostImageP)  window._allPrompts.push(`=== PROMPT HOST (ChatGPT) ===\n${hostImageP}`);
    if(guestImageP) window._allPrompts.push(`=== PROMPT GUEST (ChatGPT) ===\n${guestImageP}`);

    let html=`<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px;gap:8px;flex-wrap:wrap;">
      <strong style="font-size:13px;color:#1a1a1a;">🎬 Paquete de producción completo</strong>
      <div style="display:flex;gap:6px;">
        <button onclick="window.scrollTo({top:0,behavior:'smooth'})" style="height:28px;padding:0 10px;font-size:11px;background:#f0ede2;color:#1a1a1a;border:none;border-radius:6px;cursor:pointer;">⬆️ Volver arriba</button>
        <button onclick="copyAllPrompts()" style="height:28px;padding:0 12px;font-size:11px;background:#1a1a1a;color:#fff;border:none;border-radius:6px;cursor:pointer;">📋 Copiar todo</button>
      </div>
    </div>`;

    // ── PROMPT HOST (ChatGPT) ─────────────────────────────────────────
    if(hostImageP){
      html+=`<div class="clip-card" style="border-left:3px solid #7c3aed;">
        <div class="clip-header" style="color:#7c3aed;">📸 PROMPT HOST — ChatGPT (Image A → Host)</div>
        <div style="font-size:10.5px;color:#666;margin-bottom:6px;">Pega en ChatGPT con tu foto base de estudio para generar el <strong>host</strong>.</div>
        <div class="clip-voice">${hostImageP}</div>
        <button class="clip-copy" onclick="copyTxt(${JSON.stringify(hostImageP)})">📋 Copiar</button>
      </div>`;
    }

    // ── PROMPT GUEST (ChatGPT) ────────────────────────────────────────
    if(guestImageP){
      html+=`<div class="clip-card" style="border-left:3px solid #e11d48;">
        <div class="clip-header" style="color:#e11d48;">📸 PROMPT GUEST — ChatGPT (Image A → Guest)</div>
        <div style="font-size:10.5px;color:#666;margin-bottom:6px;">Pega en ChatGPT con la misma foto base para generar el <strong>invitado</strong>.</div>
        <div class="clip-voice">${guestImageP}</div>
        <button class="clip-copy" onclick="copyTxt(${JSON.stringify(guestImageP)})">📋 Copiar</button>
      </div>`;
    }

    // ── CLIPS VEO 3 ───────────────────────────────────────────────────
    if(clipsArr.length){
      html+=`<div style="font-size:11px;font-weight:700;color:#444;text-transform:uppercase;letter-spacing:0.5px;margin:16px 0 8px;">📹 ${clipsArr.length} clips · Google Veo 3 / Flow</div>`;
      clipsArr.forEach((c,i)=>{
        const spk=c.speaker||'host';
        const isHost=spk==='host';
        const spkColor=isHost?'#7c3aed':'#e11d48';
        const spkLabel=isHost?'Host':'Guest';
        const visual  =isHost?hostVisual:guestVisual;
        const voice   =isHost?hostVoice:guestVoice;
        const dialogue=c.dialogue||'';
        const fullPrompt=buildClipPrompt(i+1,clipsArr.length,sec,spk,spkLabel,visual,voice,dialogue);
        window._allPrompts.push(fullPrompt);
        html+=`<div class="clip-card">
          <div class="clip-header" style="display:flex;justify-content:space-between;align-items:center;">
            <span>📹 CLIP ${i+1} / ${clipsArr.length} &nbsp;·&nbsp; ${sec}s</span>
            <span style="font-size:10px;font-weight:700;color:${spkColor};background:${spkColor}18;padding:2px 8px;border-radius:20px;">${spkLabel.toUpperCase()}</span>
          </div>
          <div class="clip-section">
            <strong style="font-size:10px;color:#185fa5;">PROMPT COMPLETO → Google Veo 3 / Flow</strong>
            <div class="clip-voice" style="white-space:pre-wrap;">${fullPrompt}</div>
            <button class="clip-copy" onclick="copyTxt(${JSON.stringify(fullPrompt)})">📋 Copiar clip completo</button>
          </div>
        </div>`;
      });
    }

    // ── REDES SOCIALES ────────────────────────────────────────────────
    if(socialHook||tagsTT.length){
      const tagRow=(tags,color,label)=>tags.length?`<div style="margin-bottom:6px;"><span style="font-size:9px;font-weight:700;color:${color};text-transform:uppercase;letter-spacing:0.5px;">${label}</span><br><span style="font-size:11px;color:#444;">${tags.join(' ')}</span><button class="clip-copy" style="margin-left:8px;" onclick="copyTxt(${JSON.stringify(tags.join(' '))})">📋</button></div>`:'';
      const socialBlock=`${socialHook?`<div style="background:#f0f9ff;border-radius:8px;padding:10px;margin-bottom:8px;"><div style="font-size:10px;font-weight:700;color:#0369a1;margin-bottom:4px;">🪝 HOOK / CAPTION</div><div style="font-size:12px;color:#1a1a1a;font-weight:500;">${socialHook}</div>${socialCopy?`<div style="font-size:11px;color:#555;margin-top:4px;white-space:pre-line;">${socialCopy}</div>`:''}<button class="clip-copy" onclick="copyTxt(${JSON.stringify(socialHook+(socialCopy?'\n\n'+socialCopy:''))})">📋 Copiar copy</button></div>`:''}
      ${tagsTT.length||tagsFB.length||tagsYT.length?`<div style="background:#fafafa;border:0.5px solid rgba(0,0,0,0.1);border-radius:8px;padding:10px;margin-bottom:8px;">${tagRow(tagsTT,'#000','TikTok (máx 5)')}${tagRow(tagsFB,'#1877f2','Facebook (máx 8)')}${tagRow(tagsYT,'#ff0000','YouTube (máx 4)')}</div>`:''}
      ${thumbP?`<div style="background:#fff8f0;border-radius:8px;padding:10px;"><div style="font-size:10px;font-weight:700;color:#d97706;margin-bottom:4px;">🖼️ PROMPT PORTADA — ChatGPT / DALL-E</div><div class="clip-voice">${thumbP}</div><button class="clip-copy" onclick="copyTxt(${JSON.stringify(thumbP)})">📋 Copiar prompt portada</button></div>`:''}`;
      html+=`<div class="clip-card" style="border-left:3px solid #0ea5e9;"><div class="clip-header" style="color:#0369a1;">📱 Paquete redes sociales</div>${socialBlock}</div>`;
      window._allPrompts.push(`=== REDES SOCIALES ===\nHOOK: ${socialHook}\n\n${socialCopy}\n\nTikTok: ${tagsTT.join(' ')}\nFacebook: ${tagsFB.join(' ')}\nYouTube: ${tagsYT.join(' ')}\n\n=== PORTADA ===\n${thumbP}`);
    }

    blocksEl.innerHTML=html;
  }catch(e){
    blocksEl.innerHTML=`<div style="background:#fff1f2;border-radius:8px;padding:12px;font-size:12px;color:#9f1239;">❌ ${e.message}</div>`;
  }finally{
    btn.innerHTML='⚡ '+(lang==='es'?'Generar prompts':'Generate prompts');
    btn.disabled=false;
  }
}

function showToast(msg){
  const el=document.createElement('div');el.className='toast';el.textContent=msg;
  document.body.appendChild(el);
  setTimeout(()=>{el.style.opacity='0';setTimeout(()=>el.remove(),500);},1800);
}

function copyTxt(text){
  // Primero intentar clipboard API (funciona en algunos browsers incluso en iframe)
  const tryClipboard=()=>{
    if(navigator.clipboard&&navigator.clipboard.writeText){
      return navigator.clipboard.writeText(text).then(()=>{showToast(lang==='es'?'¡Copiado ✓':'Copied ✓');return true;}).catch(()=>false);
    }
    return Promise.resolve(false);
  };
  tryClipboard().then(ok=>{if(!ok)showCopyModal(text);});
}

function showCopyModal(text){
  document.getElementById('copy-modal-overlay')?.remove();
  const overlay=document.createElement('div');
  overlay.id='copy-modal-overlay';overlay.className='copy-overlay';
  const isEs=lang==='es';
  overlay.innerHTML=`<div class="copy-box">
    <div class="copy-box-header">
      <span>📋 ${isEs?'Selecciona todo y copia':'Select all and copy'}</span>
      <button onclick="document.getElementById('copy-modal-overlay').remove()">✕</button>
    </div>
    <textarea id="copy-modal-ta" readonly></textarea>
    <div class="copy-box-hint">${isEs?'Haz clic en el texto →':'Click inside the text →'} <kbd>${isEs?'Ctrl':'Ctrl'}+A</kbd> ${isEs?'para seleccionar todo, luego':'to select all, then'} <kbd>Ctrl+C</kbd> ${isEs?'para copiar':'to copy'}</div>
  </div>`;
  document.body.appendChild(overlay);
  const ta=document.getElementById('copy-modal-ta');
  ta.value=text;
  ta.focus();ta.select();
  // Cerrar al clic fuera del box
  overlay.addEventListener('click',e=>{if(e.target===overlay)overlay.remove();});
}

function copyAllPrompts(){
  copyTxt((window._allPrompts||[]).join('\n\n---\n\n'));
}

document.querySelectorAll('.lang-btn').forEach(b=>b.addEventListener('click',()=>setLang(b.dataset.lang)));
document.querySelectorAll('[data-set]').forEach(b=>b.addEventListener('click',()=>{setStyle=b.dataset.set;document.querySelectorAll('[data-set]').forEach(p=>p.classList.remove('active'));b.classList.add('active');}));
document.querySelectorAll('.fpill[data-format]').forEach(b=>b.addEventListener('click',()=>{format=b.dataset.format;document.querySelectorAll('.fpill[data-format]').forEach(p=>p.classList.remove('active'));b.classList.add('active');renderHighlightSubs();}));
document.querySelectorAll('.dpill').forEach(b=>b.addEventListener('click',()=>{dur=parseInt(b.dataset.dur);document.querySelectorAll('.dpill').forEach(p=>p.classList.remove('active'));b.classList.add('active');updateDurInfo();}));
document.getElementById('roll-topic').addEventListener('click',()=>{document.getElementById('topic').value=mode==='libro-rapido'?pick(RAND_TOPICS_LIBRO[lang]):pick(RAND_TOPICS[mode]?.[lang]||[]);});
document.addEventListener('change',e=>{if(e.target.tagName==='SELECT'||e.target.tagName==='INPUT')updateTags();});
document.querySelectorAll('.host-pill').forEach(b=>b.addEventListener('click',()=>{numHosts=parseInt(b.dataset.n);document.querySelectorAll('.host-pill').forEach(p=>p.classList.remove('active'));b.classList.add('active');updateNarratorCountInfo();}));
document.querySelectorAll('.guest-pill').forEach(b=>b.addEventListener('click',()=>{numGuests=parseInt(b.dataset.n);document.querySelectorAll('.guest-pill').forEach(p=>p.classList.remove('active'));b.classList.add('active');updateNarratorCountInfo();}));

fullRender();
</script>
</body>
</html>"""

components.html(HTML, height=2800, scrolling=True)
