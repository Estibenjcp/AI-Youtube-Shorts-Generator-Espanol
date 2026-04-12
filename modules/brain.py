import os
import json
from dotenv import load_dotenv

load_dotenv()

from modules.categories import TOPIC_CATEGORIES_ES, TOPIC_CATEGORIES_EN, TOPIC_CATEGORIES


def _get_secret(key: str, default: str = "") -> str:
    """Lee una clave de st.secrets (Streamlit Cloud) o de os.environ."""
    val = os.getenv(key, "")
    if val:
        return val
    try:
        import streamlit as st
        return st.secrets.get(key, default)
    except Exception:
        return default


def _get_client():
    """Inicializa el cliente de IA solo cuando se necesita (lazy init)."""
    provider  = _get_secret("AI_PROVIDER", "gemini").lower()
    api_key   = _get_secret("AI_API_KEY", "")
    model     = _get_secret("AI_MODEL", "")

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

    def get_trending_topic(self, manual_topic: str = "", lang: str = "es",
                           category_hint: str = "", mode: str = "auto") -> str:
        if manual_topic.strip():
            label = "Tema" if lang == "es" else "Topic"
            print(f"🎯 {label}: {manual_topic.strip()}")
            return manual_topic.strip()

        import random as _random
        from modules.categories import VIRAL_CATEGORIES, TESTIMONIO_CATEGORIES, BOOK_CATEGORIES, BOOK_CATEGORIES_EN

        # Pick category from the right pool depending on mode
        if category_hint.strip():
            category = category_hint.strip()
        elif mode == "viral":
            category = _random.choice(VIRAL_CATEGORIES)
        elif mode == "testimonio":
            category = _random.choice(TESTIMONIO_CATEGORIES)
        elif mode == "libro":
            category = _random.choice(BOOK_CATEGORIES if lang == "es" else BOOK_CATEGORIES_EN)
        else:
            categories = TOPIC_CATEGORIES.get(lang, TOPIC_CATEGORIES_ES)
            category   = _random.choice(categories)

        seed = int(_random.random() * 99999)

        # Use mode-specific prompt so the topic matches the content style
        if mode == "viral":
            prompt = (
                f"Dame 1 tema oscuro, impactante y poco conocido para un YouTube Short viral "
                f"en la categoría: {category}. "
                f"Debe ser un hecho histórico real, catástrofe, near miss, mortandad o conspiración documentada. "
                f"Estilo: MrBeast + Dark History. Impacto máximo, dato que shockee. "
                f"Semilla: {seed}. "
                f"Responde ÚNICAMENTE con el nombre del tema, nada más. En español."
            ) if lang == "es" else (
                f"Give me 1 dark, shocking and little-known topic for a viral YouTube Short "
                f"in the category: {category}. "
                f"Must be a real historical fact, catastrophe, near miss, or documented conspiracy. "
                f"MrBeast + Dark History style. Maximum shock value. "
                f"Seed: {seed}. Return ONLY the topic name, nothing else."
            )
        elif mode == "testimonio":
            prompt = (
                f"Dame 1 tema de horror, misterio o testimonio perturbador para un Short cinematográfico "
                f"en la categoría: {category}. "
                f"Debe sonar como un testimonio real: una secta, ritual, aparición, revelación aterradora, ocultismo. "
                f"Estilo Archimosfera — tono oscuro y escalofriante. "
                f"Semilla: {seed}. "
                f"Responde ÚNICAMENTE con el nombre del tema, nada más. En español."
            ) if lang == "es" else (
                f"Give me 1 horror, mystery or disturbing testimony topic for a cinematic Short "
                f"in the category: {category}. "
                f"Must sound like a real testimony: a cult, ritual, apparition, terrifying revelation, occultism. "
                f"Archimosfera style — dark and chilling tone. "
                f"Seed: {seed}. Return ONLY the topic name, nothing else."
            )
        elif mode == "libro":
            prompt = (
                f"Dame el título de 1 libro real, famoso y muy recomendado en la categoría: {category}. "
                f"Debe ser un libro que haya cambiado la vida de muchas personas o que sea muy popular. "
                f"Formato: 'Título del Libro — Autor'. "
                f"Semilla: {seed}. "
                f"Responde ÚNICAMENTE con el título y autor, nada más. En español."
            ) if lang == "es" else (
                f"Give me the title of 1 real, famous and highly recommended book in the category: {category}. "
                f"Must be a book that has changed many people's lives or is very popular. "
                f"Format: 'Book Title — Author'. "
                f"Seed: {seed}. "
                f"Return ONLY the title and author, nothing else."
            )
        else:
            prompt = (
                f"Dame 1 tema específico, viral y fascinante para un Short Documental "
                f"en la categoría: {category}. "
                f"Debe ser un dato sorprendente o un evento real poco conocido. "
                f"Hazlo DIFERENTE e INESPERADO — evita temas comunes. "
                f"Semilla de unicidad: {seed}. "
                f"Responde ÚNICAMENTE con el nombre del tema, nada más. En español."
            ) if lang == "es" else (
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
            prompt = f"""Eres un investigador experto en contenido viral para YouTube Shorts. Tu especialidad es encontrar HECHOS REALES que la gente no conoce.

Categoría: "{category}"

TAREA: Dame exactamente {n} temas REALES de la categoría indicada. Deben provenir de:
- Noticias reales documentadas (pueden ser recientes o históricas)
- Leyendas o mitos populares que circulan en internet y la cultura popular
- Teorías de conspiración conocidas que la gente discute actualmente
- Fábulas o historias tradicionales con trasfondo real o histórico
- Misterios no resueltos reconocidos por la ciencia o la historia
- Experimentos, eventos o descubrimientos científicos reales poco conocidos

REGLAS ABSOLUTAS:
- PROHIBIDO inventar eventos, personas o datos que no existan.
- PROHIBIDO mezclar hechos reales con detalles ficticios.
- Cada tema debe ser algo que realmente ocurrió, que realmente se dice, o que realmente existe como leyenda o teoría en la cultura popular.
- Longitud: máximo 12 palabras por tema.
- Estilo: titular directo, impactante, que genere curiosidad real.
- Idioma: español neutro latino.

FUENTES VÁLIDAS de donde debes extraer (usa tu conocimiento entrenado):
- Historia documentada mundial
- Teorías de conspiración populares (Área 51, Illuminati, reptilianos, etc.)
- Leyendas urbanas conocidas (La Llorona, El Chupacabras, etc.)
- Misterios históricos reales (El Triángulo de las Bermudas, El Arca Perdida, etc.)
- Noticias científicas o sociales reales de los últimos años
- Fábulas con origen histórico verificable

FORMATO DE SALIDA (JSON estricto, sin markdown):
["tema 1", "tema 2", "tema 3", "tema 4", "tema 5", "tema 6"]"""
        else:
            prompt = f"""You are an expert researcher in viral YouTube Shorts content. Your specialty is finding REAL FACTS that most people don't know about.

Category: "{category}"

TASK: Give me exactly {n} REAL topics from the given category. They must come from:
- Real documented news events (recent or historical)
- Popular legends or myths circulating on the internet and in popular culture
- Known conspiracy theories that people actively discuss
- Fables or traditional stories with a real or historical background
- Unsolved mysteries acknowledged by science or history
- Real lesser-known scientific experiments, events, or discoveries

ABSOLUTE RULES:
- FORBIDDEN: inventing events, people, or data that do not exist.
- FORBIDDEN: mixing real facts with fictional details.
- Each topic must be something that actually happened, is actually said, or actually exists as a legend or theory in popular culture.
- Length: maximum 12 words per topic.
- Style: direct, impactful headline that creates genuine curiosity.

VALID SOURCES to draw from (use your trained knowledge):
- Documented world history
- Popular conspiracy theories (Area 51, Illuminati, reptilians, flat earth, etc.)
- Known urban legends (Bigfoot, Loch Ness, Bermuda Triangle, etc.)
- Real historical mysteries (Lost Ark, Atlantis, Stonehenge, etc.)
- Real scientific or social news from recent years
- Fables with verifiable historical origins

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

    @staticmethod
    def _sanitize(text: str) -> str:
        """Remove special Unicode characters that break TTS or JSON parsing."""
        replacements = {
            "\u2014": "-", "\u2013": "-",   # em-dash, en-dash
            "\u2018": "'", "\u2019": "'",   # curly single quotes
            "\u201c": '"', "\u201d": '"',   # curly double quotes
            "\u2026": "...",                # ellipsis character
            "\u00ab": '"', "\u00bb": '"',   # guillemets
            "\u2022": "-",                  # bullet
        }
        for char, rep in replacements.items():
            text = text.replace(char, rep)
        return text

    def generate_viral_script(self, topic: str, category: str, lang: str = "es") -> list:
        """Genera un guion viral ultra-retención (45-60 seg) con estructura MrBeast/Dark History.
        Single-call: produce JSON scenes directly — no second AI call, no text modification."""
        import re as _re
        label = "Generando guion viral" if lang == "es" else "Generating viral script"
        print(f"🔥 {label}: {topic}...")

        if lang == "es":
            prompt = f"""Eres el mejor guionista de YouTube Shorts especializado en hechos historicos impactantes, near misses, catastrofes evitadas, mortandades misteriosas y misterios sin resolver.

Tu objetivo es crear Shorts que generen maxima retencion y shares (estilo MrBeast + The Why Files + Dark History).

REGLAS OBLIGATORIAS:
- Duracion total: 45-60 segundos (maximo 140-160 palabras en total sumando todos los campos "text").
- Estructura EXACTA en el orden de las escenas:
  Escena 1: HOOK - Pregunta impactante, numero shockeante o afirmacion loca.
  Escenas 2-3: CONTEXTO RAPIDO - Situacion historica en 1-2 frases.
  Escenas 4-7: EL GIRO / LA MORTANDAD / EL NEAR MISS - Detalle brutal, dato desconocido, consecuencia terrorifica.
  Escena 8: TWIST FINAL - Revelacion impactante, ironia o "lo que paso despues".
  Escena 9: CTA - "Comenta QUE MAS si queres la parte 2. Sigueme para mas historia oscura."
- Lenguaje dramatico, conversacional y adictivo. Usa MAYUSCULAS para enfasis.
- PROHIBIDO: emojis, caracteres especiales Unicode (guiones largos, comillas rizadas, puntos suspensivos especiales).
- USA SOLO: letras, numeros, comas, puntos, signos de exclamacion, signos de interrogacion y apostrofes simples.
- En espanol neutro latino. Nunca digas "hoy te voy a contar" ni "vamos a hablar de".

Tema: {topic}
Categoria: {category}

FORMATO DE SALIDA: JSON estricto, sin markdown, sin texto fuera del JSON:
[
  {{"id":1,"text":"texto de la escena aqui","visual_1":"english pexels term","visual_2":"english pexels term","mood":"dramatic"}},
  {{"id":2,"text":"texto de la escena aqui","visual_1":"english pexels term","visual_2":"english pexels term","mood":"dramatic"}}
]

REGLAS DEL JSON:
- Entre 8 y 10 escenas.
- "text": el texto narrado de esa escena. Sin emojis. Sin caracteres especiales.
- "visual_1" y "visual_2": terminos de busqueda en INGLES para Pexels (2-4 palabras), que coincidan con el contenido.
- "mood": siempre "dramatic"."""
        else:
            prompt = f"""You are the best YouTube Shorts scriptwriter specialized in shocking historical facts, near misses, avoided catastrophes, mysterious deaths and unsolved mysteries.

Your goal: maximum retention and shares (MrBeast + The Why Files + Dark History style).

MANDATORY RULES:
- LANGUAGE: ENGLISH ONLY. Every single word must be in English. No Spanish words whatsoever.
- Total duration: 45-60 seconds (maximum 140-160 words total across all "text" fields).
- EXACT scene structure:
  Scene 1: HOOK - Shocking question, mind-blowing number or crazy statement.
  Scenes 2-3: QUICK CONTEXT - Historical situation in 1-2 sentences.
  Scenes 4-7: THE TWIST / NEAR MISS - Brutal detail, unknown fact, terrifying consequence.
  Scene 8: FINAL TWIST - Shocking revelation, irony or "what happened after".
  Scene 9: CTA - "Comment WHAT ELSE if you want part 2. Follow for more dark history."
- Dramatic, conversational and addictive language. Use CAPS for emphasis.
- FORBIDDEN: emojis, special Unicode characters (em-dashes, curly quotes, special ellipsis).
- USE ONLY: letters, numbers, commas, periods, exclamation marks, question marks, plain apostrophes.
- Never say "today I'm going to tell you" or "we're going to talk about".

Topic: {topic}
Category: {category}

OUTPUT FORMAT: Strict JSON, no markdown, no text outside the JSON:
[
  {{"id":1,"text":"scene text here","visual_1":"pexels search term","visual_2":"pexels search term","mood":"dramatic"}},
  {{"id":2,"text":"scene text here","visual_1":"pexels search term","visual_2":"pexels search term","mood":"dramatic"}}
]

JSON RULES:
- Between 8 and 10 scenes.
- "text": narrated text for that scene. No emojis. No special characters.
- "visual_1" and "visual_2": English Pexels search terms (2-4 words) matching the content.
- "mood": always "dramatic"."""

        raw   = self._generate(prompt)
        clean = raw.replace('```json', '').replace('```', '').strip()

        try:
            scenes = json.loads(clean)
            for i, s in enumerate(scenes):
                s['id']   = i + 1
                s['text'] = self._sanitize(s.get('text', ''))
                s.setdefault('mood', 'dramatic')
            print(f"✅ {len(scenes)} viral scenes ready")
            return scenes
        except Exception:
            sentences = [s.strip() for s in _re.split(r'(?<=[.!?])\s+', clean) if len(s.strip()) > 8][:10]
            return [
                {"id": i+1, "text": self._sanitize(s), "visual_1": "dramatic cinematic footage", "visual_2": "historical documentary", "mood": "dramatic"}
                for i, s in enumerate(sentences)
            ]

    def generate_testimonio_script(self, topic: str, category: str, lang: str = "es") -> list:
        """Guion estilo testimonio misterioso — narración lenta, cinematográfica, terror.
        Single-call: produce JSON scenes directly — no second AI call, no text modification."""
        import re as _re
        import random as _random
        print(f"👁️ Generando testimonio: {topic}...")

        ATMOSPHERIC_FALLBACKS = [
            "dark forest night fog", "candle ritual dark room",
            "haunted abandoned church", "mysterious silhouette shadow",
            "foggy cemetery night", "stormy dark night lightning",
            "eerie fog forest", "candlelit room dark",
        ]

        if lang == "es":
            prompt = f"""Eres un experto en crear historias de terror y misterio en formato YouTube/TikTok Shorts, estilo Archimosfera.

Debes contar la historia como si fuera un testimonio real de una persona (ex satanica, testigo, sacerdote, victima, etc.).

Estructura exacta (50-70 segundos en total):
  Escena 1 - HOOK: Afirmacion o pregunta muy fuerte que paralice al espectador.
  Escenas 2-3 - TESTIGO: Presentacion del testimoniante ("Segun una mujer que estuvo anos en el satanismo...").
  Escenas 4-7 - DESARROLLO: Detalles escalofriantes contados poco a poco.
  Escena 8 - CLIMAX: La parte mas fuerte y perturbadora.
  Escena 9 - CIERRE: Consecuencia + CTA ("Vos crees en esto? Comenta SI o NO").

Reglas de estilo:
- Lenguaje conversacional, misterioso y dramatico.
- Frases como: "me conto que...", "revelo que...", "nadie se atreve a decir...", "lo mas aterrador fue...".
- PROHIBIDO: emojis, caracteres especiales Unicode (guiones largos, comillas rizadas, puntos suspensivos especiales).
- USA SOLO: letras, numeros, comas, puntos, signos de exclamacion, signos de interrogacion y apostrofes simples.
- En espanol neutro latino.

Tema: {topic}
Categoria: {category}

FORMATO DE SALIDA: JSON estricto, sin markdown, sin texto fuera del JSON:
[
  {{"id":1,"text":"texto de la escena","visual_1":"dark forest night","visual_2":"candle ritual","visual_3":"mysterious shadow","mood":"horror"}},
  {{"id":2,"text":"texto de la escena","visual_1":"foggy cemetery","visual_2":"abandoned church","visual_3":"eerie fog","mood":"horror"}}
]

REGLAS DEL JSON:
- Entre 8 y 10 escenas.
- "text": el texto narrado de esa escena. Sin emojis. Sin caracteres especiales.
- "visual_1", "visual_2", "visual_3": terminos en INGLES para Pexels (2-4 palabras). Deben ser oscuros, atmosfericos: dark forest, candles, fog, shadow, cemetery, abandoned, storm, etc.
- "mood": siempre "horror"."""
        else:
            prompt = f"""You are an expert at creating horror and mystery stories in YouTube/TikTok Shorts format, Archimosfera style.

Tell the story as if it were a real testimony from a real person (ex-satanist, witness, priest, victim, etc.).

Exact structure (50-70 seconds total):
  Scene 1 - HOOK: Very strong statement or question that freezes the viewer.
  Scenes 2-3 - WITNESS: Introduce the person giving testimony ("According to a woman who spent years in satanism...").
  Scenes 4-7 - DEVELOPMENT: Tell the chilling details gradually.
  Scene 8 - CLIMAX: The strongest and most disturbing part.
  Scene 9 - CLOSING: Consequence + CTA ("Do you believe this? Comment YES or NO").

Style rules:
- LANGUAGE: ENGLISH ONLY. No Spanish words.
- Conversational, mysterious and dramatic language.
- Use phrases like: "she told me that...", "revealed that...", "nobody dares to say...", "the scariest part was...".
- FORBIDDEN: emojis, special Unicode characters (em-dashes, curly quotes, special ellipsis).
- USE ONLY: letters, numbers, commas, periods, exclamation marks, question marks, plain apostrophes.

Topic: {topic}
Category: {category}

OUTPUT FORMAT: Strict JSON, no markdown, no text outside the JSON:
[
  {{"id":1,"text":"scene text here","visual_1":"dark forest night","visual_2":"candle ritual","visual_3":"mysterious shadow","mood":"horror"}},
  {{"id":2,"text":"scene text here","visual_1":"foggy cemetery","visual_2":"abandoned church","visual_3":"eerie fog","mood":"horror"}}
]

JSON RULES:
- Between 8 and 10 scenes.
- "text": narrated text for that scene. No emojis. No special characters.
- "visual_1", "visual_2", "visual_3": English Pexels search terms (2-4 words). Must be dark and atmospheric: dark forest, candles, fog, shadow, cemetery, abandoned, storm, etc.
- "mood": always "horror"."""

        raw   = self._generate(prompt)
        clean = raw.replace('```json', '').replace('```', '').strip()

        try:
            scenes = json.loads(clean)
            for i, s in enumerate(scenes):
                s['id']   = i + 1
                s['text'] = self._sanitize(s.get('text', ''))
                s.setdefault('mood', 'horror')
                if not s.get('visual_3'):
                    s['visual_3'] = _random.choice(ATMOSPHERIC_FALLBACKS)
            print(f"✅ {len(scenes)} testimonio scenes ready")
            return scenes
        except Exception:
            sentences = [s.strip() for s in _re.split(r'(?<=[.!?])\s+', clean) if len(s.strip()) > 8][:10]
            return [
                {
                    "id": i+1, "text": self._sanitize(s),
                    "visual_1": _random.choice(ATMOSPHERIC_FALLBACKS),
                    "visual_2": _random.choice(ATMOSPHERIC_FALLBACKS),
                    "visual_3": _random.choice(ATMOSPHERIC_FALLBACKS),
                    "mood": "horror"
                }
                for i, s in enumerate(sentences)
            ]

    def generate_book_summary_script(self, book: str, category: str, lang: str = "es") -> list:
        """Resumen de libro de 60 seg — enseña, aplica y motiva a leer.
        Single-call: produce JSON scenes directly — no second AI call, no text modification."""
        import re as _re
        label = "Generando resumen del libro" if lang == "es" else "Generating book summary"
        print(f"📚 {label}: {book}...")

        if lang == "es":
            prompt = f"""Actua como un narrador de historias experto y analista literario con un estilo minimalista, profundo y misterioso, similar al de los mejores curadores de contenido en TikTok. Tu objetivo no es resumir un libro, sino revelar su esencia de forma que parezca un descubrimiento necesario para el espectador.

Estructura del Guion (55-65 segundos / 150-170 palabras en total):
  Escena 1 - EL MISTERIO (5 seg): No empieces con una pregunta de autoayuda. Empieza con una observacion contraintuitiva o una verdad incomoda que el libro aborda.
  Escena 2 - LA REVELACION (5 seg): Introduce el titulo y autor como si fuera la pieza que falta en el rompecabezas. Sin introducciones innecesarias.
  Escenas 3-4 - EL DESCUBRIMIENTO (15 seg): Explica la premisa central no como una leccion, sino como una "regla del juego" que el autor descubrio.
  Escenas 5-6 - EL GIRO (15 seg): Presenta la idea mas sorprendente o radical del libro. La que te hace detener el scroll.
  Escena 7 - LA APLICACION INVISIBLE (10 seg): Como cambia este libro la forma en que el espectador vera el mundo.
  Escenas 8-9 - EL IMPACTO FINAL (10 seg): Una frase de cierre que deje un silencio reflexivo. CTA minimalista, sin sonar a vendedor.

REGLAS CRITICAS:
- PROHIBIDO: Emojis, saludos iniciales, despedidas genericas o lenguaje de vendedor.
- PROHIBIDO: caracteres especiales Unicode (guiones largos, comillas rizadas, puntos suspensivos especiales).
- USA SOLO: letras, numeros, comas, puntos, signos de exclamacion, signos de interrogacion y apostrofes simples.
- PERSPECTIVA: 2da persona constante. Habla directamente a la mente del espectador.
- TONO: Cinematografico, pausado, intelectual pero accesible.
- LENGUAJE: Espanol Latino neutro, elegante y preciso.

Libro: {book}
Categoria: {category}

FORMATO DE SALIDA: JSON estricto, sin markdown, sin texto fuera del JSON:
[
  {{"id":1,"text":"texto de la escena","visual_1":"person reading book","visual_2":"open notebook writing","mood":"inspiring"}},
  {{"id":2,"text":"texto de la escena","visual_1":"city skyline sunrise","visual_2":"person thinking window","mood":"inspiring"}}
]

REGLAS DEL JSON:
- Entre 8 y 10 escenas.
- "text": el texto narrado de esa escena. Sin emojis. Sin caracteres especiales.
- "visual_1" y "visual_2": terminos en INGLES para Pexels (2-4 palabras). Inspiradores, educativos: personas leyendo, escribiendo, pensando, naturaleza, ciudad, exito, crecimiento. EVITAR visuals oscuros.
- "mood": siempre "inspiring"."""
        else:
            prompt = f"""Act as an expert storyteller and literary analyst with a minimalist, deep and mysterious style, similar to the best content curators on TikTok. Your goal is not to summarize a book, but to reveal its essence in a way that feels like a necessary discovery for the viewer.

Script Structure (55-65 seconds / 150-170 words total):
  Scene 1 - THE MYSTERY (5 sec): Don't start with a self-help question. Start with a counterintuitive observation or an uncomfortable truth the book addresses.
  Scene 2 - THE REVELATION (5 sec): Introduce the title and author as if it were the missing piece of the puzzle. No unnecessary introductions.
  Scenes 3-4 - THE DISCOVERY (15 sec): Explain the core premise not as a lesson, but as a "rule of the game" the author uncovered.
  Scenes 5-6 - THE TWIST (15 sec): Present the most surprising or radical idea in the book. The one that makes you stop scrolling.
  Scene 7 - THE INVISIBLE APPLICATION (10 sec): How this book changes the way the viewer will see the world.
  Scenes 8-9 - THE FINAL IMPACT (10 sec): A closing line that leaves a reflective silence. Minimalist CTA, never salesy.

CRITICAL RULES:
- FORBIDDEN: Emojis, opening greetings, generic farewells or salesy language.
- FORBIDDEN: Special Unicode characters (em-dashes, curly quotes, special ellipsis characters).
- USE ONLY: letters, numbers, commas, periods, exclamation marks, question marks, plain apostrophes.
- LANGUAGE: ENGLISH ONLY. No Spanish words.
- PERSPECTIVE: Constant 2nd person. Speak directly to the viewer's mind.
- TONE: Cinematic, unhurried, intellectual yet accessible.

Book: {book}
Category: {category}

OUTPUT FORMAT: Strict JSON, no markdown, no text outside the JSON:
[
  {{"id":1,"text":"scene text here","visual_1":"person reading book","visual_2":"open notebook writing","mood":"inspiring"}},
  {{"id":2,"text":"scene text here","visual_1":"city skyline sunrise","visual_2":"person thinking window","mood":"inspiring"}}
]

JSON RULES:
- Between 8 and 10 scenes.
- "text": narrated text for that scene. No emojis. No special characters.
- "visual_1" and "visual_2": English Pexels search terms (2-4 words). Inspiring and educational: people reading, writing, thinking, nature, city, success, growth. AVOID dark visuals.
- "mood": always "inspiring"."""

        raw   = self._generate(prompt)
        clean = raw.replace('```json', '').replace('```', '').strip()

        try:
            scenes = json.loads(clean)
            for i, s in enumerate(scenes):
                s['id']   = i + 1
                s['text'] = self._sanitize(s.get('text', ''))
                s.setdefault('mood', 'inspiring')
            print(f"✅ {len(scenes)} book summary scenes ready")
            return scenes
        except Exception:
            sentences = [s.strip() for s in _re.split(r'(?<=[.!?])\s+', clean) if len(s.strip()) > 8][:10]
            return [
                {"id": i+1, "text": self._sanitize(s), "visual_1": "person reading book", "visual_2": "open notebook inspiring", "mood": "inspiring"}
                for i, s in enumerate(sentences)
            ]

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
- **Emojis:** PROHIBIDO usar emojis. Solo texto puro narrado.
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
- **Language:** ENGLISH ONLY. Every single word must be in English. No Spanish words whatsoever.
- **Emojis:** NO emojis. Pure narration text only.
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
                scene['id']   = i + 1
                scene['text'] = self._sanitize(scene.get('text', ''))
            return scenes
        except json.JSONDecodeError:
            print("❌ Error parsing JSON. Raw output:")
            print(clean_text)
            return None

    def generate_thumbnail_prompt(self, topic: str, script: list, lang: str = "es") -> str:
        print("🖼️ Generating thumbnail prompt...")
        hook = script[0]['text'] if script else ""

        if lang == "es":
            word_lang_instruction = (
                "- El prompt de imagen va en INGLÉS (para compatibilidad con Midjourney/DALL-E).\n"
                "- EXCEPCIÓN IMPORTANTE: Las palabras del título, badge y headline superpuestos en la imagen "
                "DEBEN estar en ESPAÑOL. Ejemplo: en vez de 'ETERNITY' usa 'ETERNIDAD', "
                "en vez de 'LOST REALM' usa 'REINO PERDIDO', en vez de 'MYTH' usa 'MITO'.\n"
                "- El subtítulo contextual final también debe ir en ESPAÑOL."
            )
        else:
            word_lang_instruction = (
                "- Every single word in the entire prompt — including title, badge, headline, and subtitle — "
                "MUST be in ENGLISH. Absolutely no other language."
            )

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
Title overlaid in the upper center, one dominant word: '[WORD]' with a rugged,
glowing stone texture. Below it, a short secondary badge: '[SHORT_LABEL]' like a label.
Main headline below that, a large powerful word: '[WORD_2]' with a bright crystalline texture.
Finally, a short contextual subtitle relevant to the topic."

### LANGUAGE RULES:
{word_lang_instruction}
- Title and Headline must be single dramatic words in ALL CAPS.
- Badge and subtitle must be short punchy phrases.

### OTHER RULES:
- Keep the same structural format and length as the reference.
- Replace every placeholder with elements specific to "{topic}".
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
