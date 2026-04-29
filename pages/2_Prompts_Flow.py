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
.mode-selector{display:flex;gap:8px;margin-bottom:16px;flex-wrap:wrap;}
.mode-pill{flex:1;min-width:180px;padding:12px 14px;background:#fff;border:0.5px solid rgba(0,0,0,0.15);border-radius:12px;cursor:pointer;transition:all 0.15s;text-align:left;}
.mode-pill:hover{background:#f5f4ed;}
.mode-pill.active{background:#1a1a1a;border-color:#1a1a1a;}
.mode-pill.active .mode-title,.mode-pill.active .mode-desc{color:#fff;}
.mode-icon{font-size:20px;margin-bottom:3px;}
.mode-title{font-size:13px;font-weight:500;color:#1a1a1a;margin-bottom:1px;}
.mode-desc{font-size:11px;color:#666;}
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

<div class="mode-selector" id="mode-selector"></div>

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
    <h4>Estilo de set</h4>
    <div class="format-pills" style="flex-direction:column;gap:5px;">
      <button class="spill active" data-set="oscuro" style="text-align:left;padding:5px 12px;">🕯️ Oscuro / Edison</button>
      <button class="spill" data-set="moderno" style="text-align:left;padding:5px 12px;">💡 Moderno / Softbox</button>
    </div>
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
  es:{title:"Generador de prompts",subtitle:"Multi-modo · ChatGPT + Google Flow / Veo 3 + CapCut",formatLabel:"Formato del video",fmtLineal:"📖 Lineal",fmtHighlight:"⚡ Highlight",highlightSubLabel:"Sub-tipo de highlight:",durationLabel:"Duración del video",topicSection:"Tema y estilo",topicLabel:"Tema del episodio",topicPH:"Escribe un tema o usa 🎲",styleLabel:"Estilo",toneLabel:"Tono",randomizeAll:"🎲 Aleatorizar todo",generateBtn:"⚡ Generar prompts Flow",copyBtn:"Copiar",copied:"✓ Copiado",manual:"manual",rnd:"aleatorio",
    durInfo:(n,clips,sec)=>`~${clips} clips de ${sec}s = ${n} minuto${n>1?'s':''}`,
    hlTypes:{rapida:"🌶️ Preguntas picantes",bestof:"🏆 Best-of / momentos pico",datos:"💡 Datos encadenados",comparacion:"⚔️ Comparaciones"},
    clipLabel:(i,total)=>`CLIP ${i} de ${total}`,
    outputTitles:{image1:"1️⃣ Prompt imagen del host (Image A)",image2:"2️⃣ Prompt imagen del invitado (Image A → reemplazo)",clips:"3️⃣ Prompts Flow completos por clip",meta:"4️⃣ Metadata publicación",imgNarrator:"1️⃣ Prompt imagen / escena",voiceNarrator:"2️⃣ Voice prompt narrador",clips2:"3️⃣ Prompts Flow completos por clip",meta2:"4️⃣ Metadata publicación"},
    hints:{image1:"Sin imagen de referencia — ChatGPT / Nano Banana",image2:"Sube Image A del host + pega esto",clips:"Cada bloque = 1 prompt para Google Flow.",meta:"TikTok / Reels / YouTube Shorts"}
  },
  en:{title:"Prompt generator",subtitle:"Multi-mode · ChatGPT + Google Flow / Veo 3 + CapCut",formatLabel:"Video format",fmtLineal:"📖 Linear",fmtHighlight:"⚡ Highlight",highlightSubLabel:"Highlight sub-type:",durationLabel:"Video duration",topicSection:"Topic & style",topicLabel:"Episode topic",topicPH:"Write a topic or use 🎲",styleLabel:"Style",toneLabel:"Tone",randomizeAll:"🎲 Randomize all",generateBtn:"⚡ Generate Flow prompts",copyBtn:"Copy",copied:"✓ Copied",manual:"manual",rnd:"random",
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
  'ciencia-misterio':{icon:'🌌',title:{es:'Ciencia y misterio',en:'Science & mystery'},desc:{es:'Narrador científico, datos impactantes, preguntas abiertas',en:'Scientific narrator, shocking facts, open questions'}}
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

let lang='es', mode='ficticio-viral', format='lineal', hlType='rapida', dur=1, setStyle='oscuro';

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

async function _callOR(sys,user,maxTok=1000){
  const r=await fetch('https://openrouter.ai/api/v1/chat/completions',{
    method:'POST',
    headers:{'Authorization':'Bearer '+_orKey,'Content-Type':'application/json','HTTP-Referer':'https://generador-prompts.local','X-Title':'Generador Multi-Modo'},
    body:JSON.stringify({model:getActiveModel(),messages:[{role:'system',content:sys},{role:'user',content:user}],max_tokens:maxTok,temperature:0.88})
  });
  if(!r.ok){const e=await r.json().catch(()=>({}));throw new Error(e.error?.message||'HTTP '+r.status);}
  const d=await r.json();
  return (d.choices[0].message.content||'').trim();
}

async function generateWithAI(){
  if(!_orKey){alert('Configura tu API key primero.');return;}
  const btn=document.getElementById('generate-ai');
  const area=document.getElementById('ai-output-area');
  btn.innerHTML='<span class="spinner"></span>Generando...';
  btn.disabled=true;
  area.innerHTML='';

  const topic=gv('topic').trim()||(mode==='libro-rapido'?pick(RAND_TOPICS_LIBRO[lang]):pick(RAND_TOPICS[mode]?.[lang]||[]));
  const styleV=gv('style')||'random';
  const toneV=gv('tone')||'random';

  let sys='', usr='';

  if(mode==='ficticio-viral'){
    sys=lang==='es'
      ?'Eres el guionista de un podcast ficticio viral de misterio. Generas diálogos cortos, impactantes y adictivos. Responde SOLO con JSON array de objetos {"host":"...","guest":"..."} sin texto extra.'
      :'You are the scriptwriter of a viral fictional mystery podcast. Generate short, impactful dialogues. Reply ONLY with a JSON array of {"host":"...","guest":"..."} objects, no extra text.';
    usr=lang==='es'
      ?`Tema: "${topic}" | Estilo: ${styleV} | Tono: ${toneV} | Formato: ${format}\n\nGenera 8 intercambios HOST/GUEST (máximo 20 palabras cada uno). El host presiona, el invitado revela algo perturbador.\n\nJSON:\n[{"host":"...","guest":"..."}]`
      :`Topic: "${topic}" | Style: ${styleV} | Tone: ${toneV} | Format: ${format}\n\nGenerate 8 HOST/GUEST exchanges (max 20 words each). Host presses, guest reveals something disturbing.\n\nJSON:\n[{"host":"...","guest":"..."}]`;
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
  }

  try{
    const raw=await _callOR(sys,usr,1200);
    const m=raw.match(/\[[\s\S]*\]/);
    if(!m) throw new Error(lang==='es'?'La IA no devolvió JSON válido':'AI did not return valid JSON');
    const data=JSON.parse(m[0]);
    renderAI(data,topic);
  }catch(e){
    area.innerHTML=`<div style="background:#fff1f2;border-radius:8px;padding:12px;font-size:12px;color:#9f1239;">❌ ${e.message}</div>`;
  }finally{
    btn.innerHTML='🤖 Generar con IA';
    btn.disabled=false;
  }
}

function renderAI(data,topic){
  const area=document.getElementById('ai-output-area');
  const model=_orModel.split('/').pop();
  let html=`<div class="ai-out"><div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
    <strong style="font-size:13px;color:#185fa5;">🤖 Generado con IA · ${model}</strong>
    <button onclick="copyAI()" style="height:26px;padding:0 10px;font-size:11px;">📋 Copiar todo</button>
  </div><div style="font-size:11px;color:#666;margin-bottom:10px;">Tema: <strong>${topic}</strong></div>`;

  if(mode==='ficticio-viral'){
    data.forEach((p,i)=>{
      html+=`<div class="ai-seg"><div class="ai-seg-label">Intercambio ${i+1}</div>
        <div style="margin-bottom:5px;"><span style="font-size:10px;font-weight:600;color:#666;">HOST</span><br>${p.host||''}</div>
        <div><span style="font-size:10px;font-weight:600;color:#666;">INVITADO</span><br>${p.guest||''}</div></div>`;
    });
    area._copy=data.map((p,i)=>`[${i+1}]\nHost: ${p.host||''}\nInvitado: ${p.guest||''}`).join('\n\n');
  } else if(mode==='misterio-biblico'){
    data.forEach((l,i)=>{html+=`<div class="ai-seg"><div class="ai-seg-label">Clip ${i+1}</div>${l}</div>`;});
    area._copy=data.join('\n\n');
  } else if(mode==='libro-rapido'){
    const labels=lang==='es'
      ?['🎣 Gancho','📖 El Libro','💡 Ideas + Giro','🔥 En tu vida','🚀 Cierre + CTA']
      :['🎣 Hook','📖 The Book','💡 Ideas + Twist','🔥 In your life','🚀 Close + CTA'];
    data.forEach((s,i)=>{html+=`<div class="ai-seg"><div class="ai-seg-label">${labels[i]||'Seg '+(i+1)}</div>${s}</div>`;});
    area._copy=labels.map((l,i)=>`${l}:\n${data[i]||''}`).join('\n\n');
  } else if(mode==='documental-narrado'||mode==='testimonio-real'||mode==='ciencia-misterio'){
    data.forEach((l,i)=>{html+=`<div class="ai-seg"><div class="ai-seg-label">Clip ${i+1}</div>${l}</div>`;});
    area._copy=data.map((l,i)=>`[${i+1}] ${l}`).join('\n\n');
  } else if(mode==='reflexion-biblica'){
    const labels=lang==='es'
      ?['🎣 Gancho','📖 Verso bíblico','💡 Contexto','🔥 Aplicación','🙏 Cierre / Oración']
      :['🎣 Hook','📖 Bible verse','💡 Context','🔥 Application','🙏 Close / Prayer'];
    data.forEach((s,i)=>{html+=`<div class="ai-seg"><div class="ai-seg-label">${labels[i]||'Seg '+(i+1)}</div>${s}</div>`;});
    area._copy=labels.map((l,i)=>`${l}:\n${data[i]||''}`).join('\n\n');
  }

  html+='</div>';
  area.innerHTML=html;
}

async function copyAI(){
  const area=document.getElementById('ai-output-area');
  if(!area||!area._copy) return;
  try{await navigator.clipboard.writeText(area._copy);}catch(e){const ta=document.createElement('textarea');ta.value=area._copy;document.body.appendChild(ta);ta.select();document.execCommand('copy');document.body.removeChild(ta);}
}

// ── UI Render ──────────────────────────────────────────────────────────────────
function renderModes(){
  const c=document.getElementById('mode-selector');c.innerHTML='';
  Object.entries(MODES).forEach(([id,m])=>{
    const p=document.createElement('div');
    p.className='mode-pill'+(id===mode?' active':'');
    p.innerHTML=`<div class="mode-icon">${m.icon}</div><div class="mode-title">${m.title[lang]}</div><div class="mode-desc">${m.desc[lang]}</div>`;
    p.onclick=()=>setMode(id);c.appendChild(p);
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

function fullRender(){renderModes();renderBlocks();renderSelects();renderHighlightSubs();updateDurInfo();applyI18n();updateTags();updateRecommendBtn();}
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
function setMode(m){mode=m;document.getElementById('topic').value='';document.getElementById('output-area').style.display='none';document.getElementById('ai-output-area').innerHTML='';fullRender();}

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
    'documental-narrado':['narrator-type','narrator-gender','category','style','tone'],
    'testimonio-real':['narrator-type','narrator-gender','category','style','tone'],
    'reflexion-biblica':['narrator-type','narrator-gender','category','style','tone'],
    'ciencia-misterio':['narrator-type','narrator-gender','category','style','tone'],
    'misterio-biblico':['narrator-type','narrator-gender','narrator-lang','scene-type','subtopic','style','tone'],
    'libro-rapido':['narrator-type','narrator-gender','book-genre','style','tone'],
  };
  const fields=modeFields[mode]||['style','tone'];

  // Construir lista de valores válidos para el modo actual
  const ms=MODE_SELECTS[mode]||{};
  const validVals=fields.map(id=>{
    const opts=(ms[id]||{es:[],en:[]})[lang]||[];
    const vals=opts.filter(([v])=>v!=='random').map(([v])=>v).join('|');
    return `${id}: ${vals}`;
  }).join('\n');

  const sys=lang==='es'
    ?'Eres experto en viralidad de YouTube Shorts. Dado el modo de podcast y un tema, sugieres la mejor configuración Y un tema viral específico si no se proporcionó. Responde SOLO con JSON.'
    :'You are a YouTube Shorts virality expert. Given the podcast mode and a topic, you suggest the best configuration AND a viral specific topic if not provided. Reply ONLY with JSON.';

  const topicInstruction=currentTopic
    ?`Tema actual: "${currentTopic}" (úsalo tal cual o mejóralo ligeramente)`
    :`No hay tema — sugiere un tema viral específico para el modo "${mode}" (campo "tema", máx 15 palabras)`;

  const usr=lang==='es'
    ?`Modo: ${mode}\n${topicInstruction}\n\nDevuelve SOLO este JSON:\n{"tema":"","razon":"","${fields.join('":"","')}":""}\n\nValores válidos por campo:\n${validVals}\ntema: tema concreto y viral (máx 15 palabras)\nrazon: por qué esta combinación es viral (máx 18 palabras)`
    :`Mode: ${mode}\n${topicInstruction.replace('Tema actual','Current topic').replace('No hay tema','No topic')}\n\nReturn ONLY this JSON:\n{"tema":"","reason":"","${fields.join('":"","')}":""}\n\nValid values per field:\n${validVals}\ntema: specific viral topic (max 15 words)\nreason: why this combination is viral (max 18 words)`;

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

    const razon=rec.razon||rec.reason||'';
    const temaMsg=(!currentTopic&&rec.tema)?`<br><span style="color:#7c3aed;">📌 Tema sugerido: <strong>${rec.tema}</strong></span>`:'';
    area.innerHTML=`<div style="background:#f5f3ff;border:1px solid #c4b5fd;border-radius:8px;padding:10px 14px;font-size:12px;color:#4c1d95;margin-bottom:8px;">🎯 <strong>${lang==='es'?'Combo recomendado':'Recommended combo'}:</strong> ${razon}${temaMsg}</div>`;
    updateTags();
  }catch(e){
    area.innerHTML=`<div style="background:#fff1f2;border-radius:8px;padding:10px;font-size:12px;color:#9f1239;">❌ ${e.message}</div>`;
  }finally{
    btn.innerHTML='🎯 '+(lang==='es'?'Recomendar combo':'Recommend combo');
    btn.disabled=false;
  }
}
function setLang(l){lang=l;document.querySelectorAll('.lang-btn').forEach(b=>b.classList.toggle('active',b.dataset.lang===l));fullRender();}

function generate(){
  document.getElementById('output-area').style.display='block';
  document.getElementById('config-out').textContent=
    `MODO: ${MODES[mode].title[lang]} | FORMATO: ${format} | ${dur} min\nMODELO IA: ${_orModel}\nTEMA: ${gv('topic')||'(aleatorio)'} | ESTILO: ${gv('style')} | TONO: ${gv('tone')}`;
  document.getElementById('output-blocks').innerHTML=
    `<div style="background:#f0ede2;border-radius:8px;padding:14px;font-size:12px;color:#555;">
      ℹ️ Para los prompts completos de Google Flow/Veo 3 (imagen del host, clips de video, metadata) abre el archivo HTML original.<br><br>
      Para generar el <strong>guión real con IA</strong>, usa el botón <strong>🤖 Generar con IA</strong> de arriba.
    </div>`;
}

document.querySelectorAll('.lang-btn').forEach(b=>b.addEventListener('click',()=>setLang(b.dataset.lang)));
document.querySelectorAll('[data-set]').forEach(b=>b.addEventListener('click',()=>{setStyle=b.dataset.set;document.querySelectorAll('[data-set]').forEach(p=>p.classList.remove('active'));b.classList.add('active');}));
document.querySelectorAll('.fpill[data-format]').forEach(b=>b.addEventListener('click',()=>{format=b.dataset.format;document.querySelectorAll('.fpill[data-format]').forEach(p=>p.classList.remove('active'));b.classList.add('active');renderHighlightSubs();}));
document.querySelectorAll('.dpill').forEach(b=>b.addEventListener('click',()=>{dur=parseInt(b.dataset.dur);document.querySelectorAll('.dpill').forEach(p=>p.classList.remove('active'));b.classList.add('active');updateDurInfo();}));
document.getElementById('roll-topic').addEventListener('click',()=>{document.getElementById('topic').value=mode==='libro-rapido'?pick(RAND_TOPICS_LIBRO[lang]):pick(RAND_TOPICS[mode]?.[lang]||[]);});
document.addEventListener('change',e=>{if(e.target.tagName==='SELECT'||e.target.tagName==='INPUT')updateTags();});

fullRender();
</script>
</body>
</html>"""

components.html(HTML, height=2200, scrolling=True)
