import os
import json
from dotenv import load_dotenv

load_dotenv()

from modules.categories import TOPIC_CATEGORIES_ES, TOPIC_CATEGORIES_EN, TOPIC_CATEGORIES


def _get_client():
    """Inicializa el cliente de IA solo cuando se necesita (lazy init)."""
    provider  = os.getenv("AI_PROVIDER", "gemini").lower()
    api_key   = os.getenv("AI_API_KEY", "")
    model     = os.getenv("AI_MODEL", "")

    if provider == "openrouter":
        from openai import OpenAI
        client        = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key)
        default_model = "google/gemini-flash-1.5"
    else:
        from google import genai
        client        = genai.Client(api_key=api_key)
        default_model = "gemini-2.0-flash-exp"

    return client, provider, model or default_model


class ContentBrain:

    def _generate(self, prompt: str) -> str:
        client, provider, model = _get_client()
        if provider == "openrouter":
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.choices[0].message.content
        else:
            response = client.models.generate_content(model=model, contents=prompt)
            return response.text

    def get_trending_topic(self, manual_topic: str = "", lang: str = "es") -> str:
        if manual_topic.strip():
            label = "Tema" if lang == "es" else "Topic"
            print(f"🎯 {label}: {manual_topic.strip()}")
            return manual_topic.strip()

        import random as _random

        categories = TOPIC_CATEGORIES.get(lang, TOPIC_CATEGORIES_ES)
        category   = _random.choice(categories)
        seed       = int(_random.random() * 99999)

        if lang == "es":
            prompt = (
                f"Dame 1 tema específico, viral y fascinante para un Short Documental "
                f"en la categoría: {category}. "
                f"Debe ser un dato sorprendente o un evento real poco conocido. "
                f"Hazlo DIFERENTE e INESPERADO — evita temas comunes. "
                f"Semilla de unicidad: {seed}. "
                f"Responde ÚNICAMENTE con el nombre del tema, nada más. En español."
            )
        else:
            prompt = (
                f"Give me 1 specific, viral, and deeply fascinating topic for a Short Documentary "
                f"in the category of: {category}. "
                f"It must be a surprising 'Did you know' fact or a little-known true event. "
                f"Make it DIFFERENT and UNEXPECTED — avoid common topics. "
                f"Seed for uniqueness: {seed}. "
                f"Return ONLY the topic name, nothing else."
            )

        topic = self._generate(prompt).strip()
        print(f"🎯 Auto Topic [{category}]: {topic}")
        return topic

    def get_topic_suggestions(self, category: str, n: int = 6, lang: str = "es") -> list:
        label = "Generando sugerencias para" if lang == "es" else "Generating suggestions for"
        print(f"💡 {label}: {category}...")

        if lang == "es":
            prompt = f"""Eres el estratega de contenido viral más experto de YouTube en español.

Categoría: "{category}"

TAREA: Genera exactamente {n} títulos de temas virales para un canal de YouTube Shorts educativo-entretenimiento en español latino.

REGLAS ESTRICTAS:
- Cada tema debe sonar como un titular de noticias que no puedes ignorar.
- Longitud: máximo 12 palabras por tema.
- Estilo: directo, sin rodeos, sin preguntas. Afirmaciones audaces o datos perturbadores.
- PROHIBIDO: temas genéricos, obvios o que cualquiera ya conoce.
- REQUERIDO: cada tema debe ser 100% verificable (basado en hechos reales).
- Idioma: español neutro latino, sin regionalismos.

EJEMPLOS del estilo correcto (NO los copies, son solo referencia de tono):
- "El ejército soviético entrenó delfines como armas nucleares vivientes"
- "Una ciudad entera desapareció bajo el mar en 1931 y nadie lo reportó"
- "El ser humano tiene un órgano que la ciencia ignoró por 300 años"

FORMATO DE SALIDA (JSON estricto, sin markdown):
["tema 1", "tema 2", "tema 3", "tema 4", "tema 5", "tema 6"]"""
        else:
            prompt = f"""You are the most expert viral content strategist on YouTube in English.

Category: "{category}"

TASK: Generate exactly {n} viral topic titles for an English-language educational-entertainment YouTube Shorts channel.

STRICT RULES:
- Each topic must sound like a headline you cannot ignore.
- Length: maximum 12 words per topic.
- Style: direct, no fluff, no questions. Bold claims or disturbing facts.
- FORBIDDEN: generic, obvious, or already well-known topics.
- REQUIRED: every topic must be 100% verifiable (based on real events).

EXAMPLES of correct style (do NOT copy — for tone reference only):
- "The Soviet Army Trained Dolphins as Living Nuclear Weapons"
- "An Entire City Vanished Under the Sea in 1931 and No One Reported It"
- "The Human Body Has an Organ That Science Ignored for 300 Years"

OUTPUT FORMAT (strict JSON, no markdown):
["topic 1", "topic 2", "topic 3", "topic 4", "topic 5", "topic 6"]"""

        raw = self._generate(prompt)
        clean = raw.replace('```json', '').replace('```', '').strip()
        try:
            suggestions = json.loads(clean)
            if isinstance(suggestions, list) and len(suggestions) > 0:
                return [s.strip() for s in suggestions if isinstance(s, str)][:n]
        except (json.JSONDecodeError, Exception):
            pass
        lines = [
            l.strip().strip('"').strip("'").strip('-').strip()
            for l in clean.splitlines() if l.strip()
        ]
        result = [l for l in lines if len(l) > 10][:n]
        return result or [f"Viral topic about {category}"]

    def generate_script(self, topic: str, num_scenes: int = 9, lang: str = "es") -> list:
        label = "Escribiendo guion" if lang == "es" else "Writing script"
        print(f"📝 {label}: {topic} ({num_scenes} scenes)...")

        if lang == "es":
            prompt = f"""Eres el guionista principal de un canal viral de YouTube Shorts en español latino llamado "Mentes Curiosas".

Tema: {topic}

### OBJETIVO:
Crear un guion donde cada oración tenga un "Cambio Visual" para mantener la retención alta.
Necesitamos DOS videos de stock diferentes por cada escena.

### 1. REQUISITOS DEL GUION (La narración):
- **Idioma:** ESPAÑOL LATINO neutro. Sin regionalismos. Sin palabras en inglés.
- **Perspectiva:** Estrictamente **3ª Persona** ("Los científicos descubrieron...", "El océano esconde...").
- **Tono:** Cautivador, rápido, lógico. Sin relleno. Cada oración debe generar curiosidad.
- **Estructura:** Exactamente {num_scenes} escenas en total.
- **Flujo:** Gancho (hook) -> Contexto -> Mecanismo (cómo funciona) -> Giro inesperado -> Cierre memorable.

### 2. REQUISITOS VISUALES (Doble visual por escena):
- Para CADA escena, proporciona DOS términos de búsqueda distintos:
  - **visual_1:** Corresponde al *inicio* de la oración.
  - **visual_2:** Corresponde al *final* de la oración o proporciona contexto/reacción.
- **CRÍTICO:** Los términos visual_1 y visual_2 deben estar en INGLÉS (para búsqueda en Pexels).

### FORMATO DE SALIDA (JSON estricto, exactamente {num_scenes} entradas):
[
    {{
        "id": 1,
        "text": "En 1995, catorce lobos fueron liberados en el Parque Yellowstone, y cambiaron el curso de los ríos.",
        "visual_1": "wolves running snow aerial",
        "visual_2": "river flowing forest drone",
        "mood": "intriguing"
    }}
]"""
        else:
            prompt = f"""You are the lead scriptwriter for a high-retention "Edutainment" YouTube Shorts channel.

Topic: {topic}

### GOAL:
Create a script where every sentence has a "Visual Switch" to keep retention high.
We need TWO different stock videos for every single scene.

### 1. SCRIPT REQUIREMENTS (The Voiceover):
- **Perspective:** Strictly **3rd Person** ("Scientists found...", "The ocean hides...").
- **Tone:** Engaging, fast-paced, logical. No fluff. Every sentence must build curiosity.
- **Structure:** Exactly {num_scenes} scenes total.
- **Flow:** Hook -> Context -> Mechanism (How it works) -> Twist -> Memorable Outro.

### 2. VISUAL REQUIREMENTS (Dual Visuals):
- For EVERY scene, provide TWO distinct search terms:
  - **visual_1:** Matches the *start* of the sentence.
  - **visual_2:** Matches the *end* of the sentence or provides reaction/context.
- **Strictly Literal:** If the text is "The economy crashed," search "stock market crash red chart".

### OUTPUT FORMAT (Strict JSON, exactly {num_scenes} entries):
[
    {{
        "id": 1,
        "text": "In 1995, fourteen wolves were released into Yellowstone Park, and they changed the rivers.",
        "visual_1": "wolves running snow aerial",
        "visual_2": "river flowing forest drone",
        "mood": "intriguing"
    }}
]"""

        raw = self._generate(prompt)
        clean_text = raw.replace('```json', '').replace('```', '').strip()

        try:
            scenes = json.loads(clean_text)
            if len(scenes) > num_scenes:
                print(f"⚠️ AI returned {len(scenes)} scenes, trimming to {num_scenes}.")
                scenes = scenes[:num_scenes]
            elif len(scenes) < num_scenes:
                print(f"⚠️ AI returned only {len(scenes)} scenes (requested {num_scenes}).")
            for i, scene in enumerate(scenes):
                scene['id'] = i + 1
            return scenes
        except json.JSONDecodeError:
            print("❌ Error parsing JSON. Raw output:")
            print(clean_text)
            return None

    def generate_thumbnail_prompt(self, topic: str, script: list) -> str:
        print("🖼️ Generating thumbnail prompt...")
        hook = script[0]['text'] if script else ""
        prompt = f"""
You are an expert AI image prompt engineer specializing in viral YouTube Shorts thumbnails.

Video topic: "{topic}"
Opening line: "{hook}"

### YOUR TASK:
Write an image generation prompt following EXACTLY this style reference structure.
Adapt every element to match the video topic — do NOT copy the jellyfish example.

### STYLE REFERENCE (adapt — do not copy):
"Viral thumbnail style, cinematic documentary, dramatic high contrast photo, dual nature.
A massive [SUBJECT] is split vertically. Left side: [POSITIVE/ALIVE/BEGINNING aspect],
luminous glow. Right side: [NEGATIVE/DARK/END aspect], dark and decaying counterpart.
The central vertical axis is sharp. Exaggerated visual duality. Iconic [SUBJECT] centered.
Background is [FITTING DARK ENVIRONMENT], with a dramatic volumetric light beam piercing
from the top right, creating hard shadows and bright highlights on the [SUBJECT].
Swirling particles (dust, embers, glowing debris) around the central figure.
Breaking news/historic discovery aesthetic. Maximum detail, photorealistic, 8k,
vertical composition (9:16). Centralized composition, all key elements within the
central 1:1 safe area. Top area is clear of text.
Title overlaid in the upper center, one dominant word: '[ENGLISH_WORD]' with a rugged,
glowing stone texture. Below it, a short secondary badge: '[SHORT_ENGLISH_LABEL]' like a label.
Main headline below that, a large powerful word: '[ENGLISH_WORD_2]' with a bright crystalline texture.
Finally, a short contextual subtitle in English relevant to the topic."

### RULES:
- Keep the same structural format and length as the reference.
- Replace every placeholder with elements specific to "{topic}".
- **CRITICAL: Every single word in the entire prompt — including title, badge, headline, and subtitle — MUST be in ENGLISH. Absolutely no Spanish or any other language.**
- Title and Headline must be single dramatic English words in ALL CAPS.
- Badge and subtitle must be short punchy English phrases.
- Return ONLY the final prompt text. No explanations. No JSON. No markdown.
"""
        return self._generate(prompt).strip()

    def generate_copy(self, topic: str, script: list, lang: str = "es") -> dict:
        label = "Generando copy para redes sociales" if lang == "es" else "Generating social media copy"
        print(f"✍️ {label}...")
        hook = script[0]['text'] if script else ""
        last = script[-1]['text'] if script else ""

        if lang == "es":
            prompt = f"""
Eres un estratega experto en redes sociales especializado en contenido viral en español para YouTube Shorts, TikTok y Facebook Reels en el mercado latinoamericano.

Tema del video: "{topic}"
Línea de apertura: "{hook}"
Línea de cierre: "{last}"

### TAREA:
Genera copy optimizado para cada plataforma en español latino.

### 1. TÍTULO YOUTUBE SHORTS:
- Longitud: estrictamente 40–70 caracteres incluyendo espacios y emojis.
- Formato: usa UNO de estos ganchos: Pregunta ("¿Sabías que...?"), Número ("3 datos..."), Intriga ("El secreto detrás de...").
- Coloca la palabra clave más importante en las primeras 6 palabras.
- Termina exactamente con: #Shorts
- Máximo 1 emoji relevante. SIN mayúsculas completas.

### 2. DESCRIPCIÓN DE YOUTUBE (2–3 oraciones):
- Amplía el tema con palabras clave en español. Incluye CTA. Termina con 3 hashtags (#Shorts + 2 específicos).

### 3. CAPTION DE TIKTOK:
- LÍNEA 1: gancho con la PALABRA CLAVE PRINCIPAL del tema (dato impactante o afirmación sorprendente).
- LÍNEA 2: 1 oración conversacional que amplía la curiosidad.
- LÍNEA 3: CTA — pregunta que invite a interacción o pida la Parte 2.
- HASHTAGS: 3 a 5 hashtags de nicho en español.

### 4. CAPTION DE FACEBOOK REELS:
- LÍNEA 1: afirmación impactante con la palabra clave principal (sin preguntas).
- LÍNEA 2: 1 oración conversacional de contexto.
- LÍNEA 3: CTA — invita a comentar o compartir.
- HASHTAGS: EXACTAMENTE 3 hashtags en español.

### SALIDA (JSON estricto, sin markdown). Usa \\n para saltos de línea:
{{
  "youtube_title": "...",
  "youtube_description": "...",
  "tiktok_caption": "línea gancho\\n\\nlínea contexto\\n\\nCTA\\n\\n#tag1 #tag2 #tag3",
  "facebook_caption": "afirmación gancho\\n\\ncontexto\\n\\nCTA\\n\\n#tag1 #tag2 #tag3"
}}
"""
        else:
            prompt = f"""
You are an expert social media strategist specializing in viral short-form video content in English.

Video topic: "{topic}"
Opening line: "{hook}"
Closing line: "{last}"

### TASK:
Generate platform-optimized copy for YouTube Shorts, TikTok, and Facebook Reels.

### 1. YOUTUBE SHORTS TITLE:
- Length: strictly 40–70 characters including spaces and emojis.
- Format: use ONE of these hooks: Question ("Did you know...?"), Number ("3 facts about..."), Intrigue ("The secret behind...").
- Place the most important keyword in the FIRST 6 words.
- End with exactly: #Shorts
- 1 relevant emoji maximum. NO all-caps spam words.

### 2. YOUTUBE DESCRIPTION (2–3 sentences):
- Expand on the topic with relevant keywords. Include a CTA. End with 3 hashtags (#Shorts + 2 topic-specific).

### 3. TIKTOK CAPTION:
- LINE 1: hook containing the PRIMARY KEYWORD (shocking fact or surprising statement).
- LINE 2: 1 short conversational sentence expanding curiosity.
- LINE 3: CTA — question inviting engagement or asking for Part 2.
- HASHTAGS: 3 to 5 niche hashtags.

### 4. FACEBOOK REELS CAPTION:
- LINE 1: strongest hook — shocking statement with main keyword (no questions).
- LINE 2: 1 natural conversational sentence adding context.
- LINE 3: CTA — invites comment or share.
- HASHTAGS: EXACTLY 3 hashtags.

### OUTPUT (strict JSON, no markdown). Use \\n for line breaks:
{{
  "youtube_title": "...",
  "youtube_description": "...",
  "tiktok_caption": "hook line\\n\\ncontext line\\n\\nCTA\\n\\n#tag1 #tag2 #tag3",
  "facebook_caption": "hook statement\\n\\ncontext line\\n\\nCTA\\n\\n#tag1 #tag2 #tag3"
}}
"""

        raw   = self._generate(prompt)
        clean = raw.replace('```json', '').replace('```', '').strip()
        try:
            import json as _j
            data = _j.loads(clean)
            return {
                "youtube_title":       data.get("youtube_title", ""),
                "youtube_description": data.get("youtube_description", ""),
                "tiktok_caption":      data.get("tiktok_caption", ""),
                "facebook_caption":    data.get("facebook_caption", ""),
            }
        except Exception:
            print("⚠️ Could not parse copy JSON — returning raw.")
            return {
                "youtube_title": topic,
                "youtube_description": clean,
                "tiktok_caption": clean,
                "facebook_caption": clean,
            }


if __name__ == "__main__":
    brain = ContentBrain()
    topic = brain.get_trending_topic(lang="es")
    script = brain.generate_script(topic, lang="es")
    with open("script.json", "w", encoding="utf-8") as f:
        json.dump(script, f, indent=4, ensure_ascii=False)
        print("✅ Script saved to script.json")
