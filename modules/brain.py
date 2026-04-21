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
                           category_hint: str = "", mode: str = "auto",
                           exclude_books: list = None) -> str:
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

        import time as _time
        # Seed compuesto: nanosegundos + aleatorio → prácticamente único cada llamada
        seed = (int(_time.time_ns()) % 999983) ^ int(_random.random() * 999979)

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
            # Lista negra de libros ya usados en esta sesión
            _excl = exclude_books or []
            _excl_es = (
                (f"- ESTRICTAMENTE PROHIBIDO elegir cualquiera de estos libros ya vistos: {', '.join(_excl)}.\n")
                if _excl else ""
            )
            _excl_en = (
                (f"- STRICTLY FORBIDDEN to choose any of these already-seen books: {', '.join(_excl)}.\n")
                if _excl else ""
            )
            prompt = (
                f"Eres un curador literario experto. Necesito el título de UN libro real de la categoría: {category}.\n"
                f"Semilla de aleatoriedad: {seed} — este número cambia en cada llamada, úsalo para explorar el catálogo en orden diferente.\n"
                f"REGLAS ESTRICTAS:\n"
                f"- PROHIBIDO: 'Hábitos Atómicos', 'El Poder del Ahora', 'Padre Rico Padre Pobre', 'El Monje que Vendió su Ferrari', 'Piense y Hágase Rico'.\n"
                f"{_excl_es}"
                f"- Elige un libro real, valioso pero NO el más obvio de la categoría.\n"
                f"- Rota entre: clásicos del siglo XX, libros modernos (2010-2024), autores latinoamericanos, europeos, asiáticos.\n"
                f"- Formato exacto: 'Título del Libro — Autor'\n"
                f"- Responde ÚNICAMENTE con el título y autor. Nada más."
            ) if lang == "es" else (
                f"You are an expert literary curator. Give me the title of ONE real book from the category: {category}.\n"
                f"Randomness seed: {seed} — this number changes each call, use it to explore the catalog in a different order.\n"
                f"STRICT RULES:\n"
                f"- FORBIDDEN: 'Atomic Habits', 'The Power of Now', 'Rich Dad Poor Dad', 'The 7 Habits of Highly Effective People', 'Think and Grow Rich'.\n"
                f"{_excl_en}"
                f"- Choose a real, valuable book that is NOT the most obvious one in the category.\n"
                f"- Rotate between: 20th-century classics, modern books (2010-2024), authors from different continents.\n"
                f"- Exact format: 'Book Title — Author'\n"
                f"- Return ONLY the title and author. Nothing else."
            )
        elif mode == "biblia":
            _excl = exclude_books or []
            _excl_es = (f"- PROHIBIDO repetir estos pasajes/temas ya vistos: {', '.join(_excl)}.\n") if _excl else ""
            _excl_en = (f"- FORBIDDEN to repeat these already-seen passages/themes: {', '.join(_excl)}.\n") if _excl else ""
            prompt = (
                f"Eres un experto en contenido bíblico y espiritual. Sugiere UN pasaje bíblico o tema espiritual de la categoría: {category}.\n"
                f"Semilla: {seed} — úsala para variar entre versículos, parábolas, temas y libros bíblicos.\n"
                f"REGLAS:\n"
                f"{_excl_es}"
                f"- Puede ser: un versículo específico (ej. 'Juan 3:16'), una parábola, un tema bíblico (ej. 'La fe que mueve montañas').\n"
                f"- Formato: 'Tema o versículo — referencia bíblica (si aplica)'\n"
                f"- Responde ÚNICAMENTE con el tema/versículo. Nada más."
            ) if lang == "es" else (
                f"You are an expert in biblical and spiritual content. Suggest ONE Bible passage or spiritual theme from the category: {category}.\n"
                f"Seed: {seed} — use it to vary between verses, parables, themes, and biblical books.\n"
                f"RULES:\n"
                f"{_excl_en}"
                f"- It can be: a specific verse (e.g. 'John 3:16'), a parable, a biblical theme (e.g. 'Faith that moves mountains').\n"
                f"- Format: 'Theme or verse — biblical reference (if applicable)'\n"
                f"- Return ONLY the theme/verse. Nothing else."
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

    def get_topic_and_description(self, manual_topic: str = "", category: str = "",
                                   mode: str = "auto", lang: str = "es",
                                   exclude_books: list = None) -> dict:
        """Resuelve el tema final y genera una descripción breve de 1-2 oraciones.
        Retorna {"topic": str, "description": str}"""
        # Step 1: resolve topic (uses existing logic with category/mode fallback)
        topic = self.get_trending_topic(manual_topic, lang=lang,
                                        category_hint=category, mode=mode,
                                        exclude_books=exclude_books or [])

        # Step 2: generate a 1-2 sentence teaser about the video
        _tone_hint = {
            "viral":      ("oscuro, impactante, histórico" if lang == "es" else "dark, shocking, historical"),
            "testimonio": ("misterioso, perturbador, cinematográfico" if lang == "es" else "mysterious, disturbing, cinematic"),
            "libro":      ("inspirador, revelador, educativo" if lang == "es" else "inspiring, revealing, educational"),
            "biblia":     ("espiritual, esperanzador, edificante" if lang == "es" else "spiritual, hopeful, uplifting"),
            "auto":       ("viral, curioso, impactante" if lang == "es" else "viral, curious, shocking"),
            "category":   ("viral, curioso, impactante" if lang == "es" else "viral, curious, shocking"),
        }.get(mode, ("interesante, impactante" if lang == "es" else "interesting, impactful"))

        if lang == "es":
            prompt = (
                f"Tema del video: \"{topic}\"\n\n"
                f"Escribe exactamente 2 oraciones cortas (maximo 35 palabras en total) que describan:\n"
                f"1. El hecho o dato central que revelara el video.\n"
                f"2. Por que es impactante o fascinante para el espectador.\n\n"
                f"Tono: {_tone_hint}.\n"
                f"PROHIBIDO: preguntas retorica, emojis, spoilers completos, caracteres especiales.\n"
                f"Responde SOLO las 2 oraciones, sin introduccion ni explicacion."
            )
        else:
            prompt = (
                f"Video topic: \"{topic}\"\n\n"
                f"Write exactly 2 short sentences (maximum 35 words total) describing:\n"
                f"1. The central fact or revelation the video will uncover.\n"
                f"2. Why it's shocking or fascinating for the viewer.\n\n"
                f"Tone: {_tone_hint}.\n"
                f"FORBIDDEN: rhetorical questions, emojis, complete spoilers, special characters.\n"
                f"Respond ONLY with the 2 sentences, no intro or explanation."
            )

        description = self._sanitize(self._generate(prompt).strip())
        print(f"🎯 Topic resolved: {topic}")
        print(f"📝 Description: {description}")
        return {"topic": topic, "description": description}

    def recommend_voice(self, topic: str, category: str, mode: str, lang: str,
                        tts_engine: str, voice_options: list) -> str:
        """Picks the most suitable voice label from voice_options for the given topic/mode."""
        if not voice_options:
            return ""
        mood_es = {
            "testimonio": "voz masculina profunda, misteriosa, que genere suspenso",
            "libro":      "voz cálida, clara e inspiradora",
            "biblia":     "voz cálida, tranquila y espiritual",
            "viral":      "voz enérgica e impactante",
            "novela":     "voz dramática y expresiva",
            "podcast":    "voz natural y conversacional",
        }.get(mode, "voz clara y atractiva")
        mood_en = {
            "testimonio": "deep, mysterious, suspenseful male voice",
            "libro":      "warm, clear, inspiring voice",
            "biblia":     "warm, calm, spiritual voice",
            "viral":      "energetic, impactful voice",
            "novela":     "dramatic, expressive voice",
            "podcast":    "natural, conversational voice",
        }.get(mode, "clear, engaging voice")
        opts_text = "\n".join(f"- {v}" for v in voice_options[:25])
        if lang == "es":
            prompt = (
                f"Eres un director de casting de voz para videos de redes sociales.\n"
                f"Contexto del video:\n"
                f"- Tema: {topic}\n"
                f"- Categoría: {category}\n"
                f"- Modo: {mode}\n"
                f"- Personalidad ideal: {mood_es}\n\n"
                f"Elige UNA voz de esta lista que mejor encaje:\n{opts_text}\n\n"
                f"Responde ÚNICAMENTE con el nombre EXACTO de la voz tal como aparece en la lista. Nada más."
            )
        else:
            prompt = (
                f"You are a voice casting director for social media videos.\n"
                f"Video context:\n"
                f"- Topic: {topic}\n"
                f"- Category: {category}\n"
                f"- Mode: {mode}\n"
                f"- Ideal personality: {mood_en}\n\n"
                f"Choose ONE voice from this list that fits best:\n{opts_text}\n\n"
                f"Respond ONLY with the EXACT voice name as it appears in the list. Nothing else."
            )
        raw = self._generate(prompt).strip()
        for opt in voice_options:
            if raw == opt:
                return opt
        for opt in voice_options:
            if raw[:30] in opt or opt[:30] in raw:
                return opt
        return voice_options[0]

    def get_hook_options(self, topic: str, category: str, mode: str = "auto", lang: str = "es", n: int = 3) -> list:
        """Genera N opciones de gancho viral para un tema dado.
        Si topic está vacío, usa la categoría como contexto principal."""

        # Construir el contexto de forma robusta — nunca dejar vacío
        topic   = (topic   or "").strip()
        category = (category or "").strip()

        if topic and category:
            ctx = f"{topic} (categoría: {category})" if lang == "es" else f"{topic} (category: {category})"
        elif topic:
            ctx = topic
        elif category:
            ctx = category
        else:
            ctx = "contenido viral misterioso" if lang == "es" else "viral mystery content"

        # Tipos de hook por modo
        if mode == "testimonio":
            types_es = (
                "- TIPO A: cifra impactante + hecho perturbador ('17 personas desaparecieron la misma noche. Nadie explica como.')\n"
                "- TIPO B: revelacion del testigo ('Lo que este ex-miembro revelo sobre [X] cambio todo.')\n"
                "- TIPO C: secreto oculto ('Nadie habla de lo que paso realmente en [X].')\n"
            )
            types_en = (
                "- TYPE A: shocking number + disturbing fact ('17 people vanished the same night. No one explains how.')\n"
                "- TYPE B: witness reveal ('What this ex-member revealed about [X] changed everything.')\n"
                "- TYPE C: hidden secret ('Nobody talks about what really happened at [X].')\n"
            )
            tone_es = "oscuro y perturbador, estilo testimonio real de horror"
            tone_en = "dark and disturbing, real horror testimony style"
        elif mode == "libro":
            types_es = (
                "- TIPO A: verdad incomoda del libro ('La mayoria trabaja mas duro pero gana menos. Este libro explica por que.')\n"
                "- TIPO B: creencia que el libro destruye ('Todo lo que te ensenaron sobre [X] esta equivocado, segun este libro.')\n"
                "- TIPO C: dato que el libro revela ('Lo que nadie te cuenta sobre [X] esta en este libro.')\n"
            )
            types_en = (
                "- TYPE A: uncomfortable truth from the book ('Most people work harder but earn less. This book explains why.')\n"
                "- TYPE B: belief the book destroys ('Everything you were taught about [X] is wrong, according to this book.')\n"
                "- TYPE C: what the book reveals ('What nobody tells you about [X] is in this book.')\n"
            )
            tone_es = "inspirador e intrigante, que motive a leer el libro"
            tone_en = "inspiring and intriguing, motivating to read the book"
        elif mode == "biblia":
            types_es = (
                "- TIPO A: promesa poderosa ('Dios prometio que nunca te abandonaria. Y hay un versiculo que lo prueba.')\n"
                "- TIPO B: verdad que transforma ('La mayoria no conoce este versiculo. Pero cambia todo.')\n"
                "- TIPO C: pregunta espiritual ('¿Que hace Dios cuando sientes que ya no puedes mas?')\n"
            )
            types_en = (
                "- TYPE A: powerful promise ('God promised He would never leave you. And there is a verse that proves it.')\n"
                "- TYPE B: transforming truth ('Most people don't know this verse. But it changes everything.')\n"
                "- TYPE C: spiritual question ('What does God do when you feel like you can't go on?')\n"
            )
            tone_es = "espiritual, esperanzador y edificante, que toque el corazon"
            tone_en = "spiritual, hopeful and uplifting, touching the heart"
        else:  # auto, category, viral
            types_es = (
                "- TIPO A (Numero shockeante): cifra + consecuencia brutal ('40.000 personas murieron en 48 horas. Nadie lo investigo.')\n"
                "- TIPO B (Controversia): 'Todo lo que sabes sobre [X] esta completamente equivocado.'\n"
                "- TIPO C (Curiosidad): 'Nadie habla de lo que paso realmente con [X].'\n"
            )
            types_en = (
                "- TYPE A (Shocking number): stat + brutal consequence ('40,000 people died in 48 hours. Nobody investigated.')\n"
                "- TYPE B (Controversy): 'Everything you know about [X] is completely wrong.'\n"
                "- TYPE C (Curiosity): 'Nobody is talking about what really happened with [X].'\n"
            )
            tone_es = "viral e impactante, estilo MrBeast + Dark History"
            tone_en = "viral and impactful, MrBeast + Dark History style"

        if lang == "es":
            prompt = f"""Eres experto en ganchos virales para YouTube Shorts. El espectador decide si sigue viendo en 1.7 segundos.

Contexto del video: "{ctx}"
Tono requerido: {tone_es}

TAREA: Genera exactamente {n} hooks distintos para la Escena 1. Cada uno de un tipo diferente:
{types_es}
REGLAS ABSOLUTAS:
- Maximo 12 palabras por hook
- Sin emojis, sin caracteres especiales, sin comillas rizadas
- Concreto y especifico al contexto — PROHIBIDO ser generico
- Cada hook debe crear curiosidad INMEDIATA e IRRESISTIBLE
- PROHIBIDO responder con explicaciones, solo el JSON

FORMATO (JSON estricto, sin markdown, sin texto extra):
["hook A aqui", "hook B aqui", "hook C aqui"]"""
        else:
            prompt = f"""You are an expert in viral hooks for YouTube Shorts. The viewer decides in 1.7 seconds.

Video context: "{ctx}"
Required tone: {tone_en}

TASK: Generate exactly {n} distinct hooks for Scene 1. Each a different type:
{types_en}
ABSOLUTE RULES:
- Maximum 12 words per hook
- No emojis, no special characters, no curly quotes
- Concrete and specific to the context — GENERIC hooks are FORBIDDEN
- Each hook must create IMMEDIATE and IRRESISTIBLE curiosity
- FORBIDDEN to respond with explanations, only the JSON

FORMAT (strict JSON, no markdown, no extra text):
["hook A here", "hook B here", "hook C here"]"""

        raw   = self._generate(prompt)
        clean = raw.replace('```json', '').replace('```', '').strip()
        # Strip any leading text before the JSON array
        bracket = clean.find('[')
        if bracket > 0:
            clean = clean[bracket:]
        try:
            hooks = json.loads(clean)
            if isinstance(hooks, list):
                result = [self._sanitize(h.strip()) for h in hooks if isinstance(h, str) and len(h.strip()) > 5]
                if result:
                    return result[:n]
        except Exception:
            pass
        # Fallback: extract quoted strings
        import re as _re
        quoted = _re.findall(r'"([^"]{10,})"', raw)
        if quoted:
            return [self._sanitize(q) for q in quoted[:n]]
        lines = [l.strip().strip('"').strip("'").strip('-').strip() for l in raw.splitlines() if len(l.strip()) > 10]
        return [self._sanitize(l) for l in lines if len(l) > 10][:n] or [ctx[:60]]

    def generate_viral_script(self, topic: str, category: str, lang: str = "es", chosen_hook: str = "", num_scenes: int = 9, max_words_per_scene: int = 999) -> list:
        """Genera un guion viral ultra-retención (45-60 seg) con estructura MrBeast/Dark History.
        Single-call: produce JSON scenes directly — no second AI call, no text modification."""
        import re as _re
        label = "Generando guion viral" if lang == "es" else "Generating viral script"
        print(f"🔥 {label}: {topic}...")

        if lang == "es":
            prompt = f"""Eres el mejor guionista de YouTube Shorts especializado en hechos historicos impactantes, near misses, catastrofes evitadas, mortandades misteriosas y misterios sin resolver.

Tu objetivo es crear Shorts que generen maxima retencion y shares (estilo MrBeast + The Why Files + Dark History).

REGLAS OBLIGATORIAS:
- Duracion total: ~{num_scenes * 5} segundos (maximo {num_scenes * 17} palabras en total sumando todos los campos "text").
- MAXIMO {max_words_per_scene} palabras por escena en el campo "text" — es critico para sincronizar con el clip de video.
- EXACTAMENTE {num_scenes} escenas — ni una mas, ni una menos.
- Estructura EXACTA en el orden de las escenas:
  Escena 1: HOOK VIRAL (CRITICO - maximo 12 palabras, el espectador decide en 1.7 seg):
    Elige OBLIGATORIAMENTE uno de estos 4 tipos:
    TIPO A-NUMERO: "[CIFRA] [personas/dias/años] [consecuencia brutal]." Ej: "40.000 personas murieron en 48 horas. Nadie lo investigo."
    TIPO B-CONTROVERSIA: "Todo lo que sabes sobre [ELEMENTO ESPECIFICO DEL TEMA] esta completamente equivocado."
    TIPO C-CURIOSIDAD: "Nadie esta hablando de lo que paso realmente con [ELEMENTO DEL TEMA]."
    TIPO D-PREGUNTA TRAMPA: "¿Que harias si descubrieras que [AFIRMACION IMPACTANTE Y ESPECIFICA]?"
    El hook debe ser IMPOSIBLE de ignorar.
  Escenas 2-{max(3, num_scenes - 3)}: CONTEXTO + DESARROLLO - Situacion historica, detalles brutales, datos desconocidos.
  Escena {num_scenes - 1}: TWIST FINAL - Revelacion impactante, ironia o "lo que paso despues".
  Escena {num_scenes}: CTA - "Comenta QUE MAS si queres la parte 2. Sigueme para mas historia oscura."
- Lenguaje dramatico, conversacional y adictivo. Usa MAYUSCULAS para enfasis.
- PROHIBIDO: emojis, caracteres especiales Unicode (guiones largos, comillas rizadas, puntos suspensivos especiales).
- USA SOLO: letras, numeros, comas, puntos, signos de exclamacion, signos de interrogacion y apostrofes simples.
- En espanol neutro latino. Nunca digas "hoy te voy a contar" ni "vamos a hablar de".

Tema: {topic}
Categoria: {category}{f'{chr(10)}HOOK PRE-SELECCIONADO (OBLIGATORIO usar este texto EXACTO en Escena 1): "{chosen_hook}"' if chosen_hook else ""}

FORMATO DE SALIDA: JSON estricto, sin markdown, sin texto fuera del JSON:
[
  {{"id":1,"text":"texto de la escena aqui","visual_1":"english pexels term","visual_2":"english pexels term","mood":"dramatic"}},
  {{"id":2,"text":"texto de la escena aqui","visual_1":"english pexels term","visual_2":"english pexels term","mood":"dramatic"}}
]

REGLAS DEL JSON:
- EXACTAMENTE {num_scenes} entradas — no mas, no menos.
- "text": el texto narrado de esa escena. Sin emojis. Sin caracteres especiales.
- "visual_1" y "visual_2": terminos de busqueda en INGLES para Pexels (2-4 palabras), que coincidan con el contenido.
- "mood": siempre "dramatic"."""
        else:
            prompt = f"""You are the best YouTube Shorts scriptwriter specialized in shocking historical facts, near misses, avoided catastrophes, mysterious deaths and unsolved mysteries.

Your goal: maximum retention and shares (MrBeast + The Why Files + Dark History style).

MANDATORY RULES:
- LANGUAGE: ENGLISH ONLY. Every single word must be in English. No Spanish words whatsoever.
- Total duration: ~{num_scenes * 5} seconds (maximum {num_scenes * 17} words total across all "text" fields).
- MAXIMUM {max_words_per_scene} words per scene in the "text" field — critical for video clip sync.
- EXACTLY {num_scenes} scenes — no more, no fewer.
- EXACT scene structure:
  Scene 1: VIRAL HOOK (CRITICAL - max 12 words, viewer decides in 1.7 sec):
    MANDATORY — pick ONE of these 4 hook types:
    TYPE A-NUMBER: "[SHOCKING NUMBER] [people/days/years] [brutal consequence]." E.g.: "40,000 people died in 48 hours. Nobody investigated."
    TYPE B-CONTROVERSY: "Everything you know about [SPECIFIC TOPIC ELEMENT] is completely wrong."
    TYPE C-CURIOSITY: "Nobody is talking about what really happened with [SPECIFIC ELEMENT]."
    TYPE D-TRAP QUESTION: "What would you do if you found out that [SHOCKING SPECIFIC STATEMENT]?"
    The hook must be IMPOSSIBLE to scroll past.
  Scenes 2-{max(3, num_scenes - 3)}: QUICK CONTEXT + DEVELOPMENT - Historical situation, brutal details, unknown facts.
  Scene {num_scenes - 1}: FINAL TWIST - Shocking revelation, irony or "what happened after".
  Scene {num_scenes}: CTA - "Comment WHAT ELSE if you want part 2. Follow for more dark history."
- Dramatic, conversational and addictive language. Use CAPS for emphasis.
- FORBIDDEN: emojis, special Unicode characters (em-dashes, curly quotes, special ellipsis).
- USE ONLY: letters, numbers, commas, periods, exclamation marks, question marks, plain apostrophes.
- Never say "today I'm going to tell you" or "we're going to talk about".

Topic: {topic}
Category: {category}{f'{chr(10)}PRE-SELECTED HOOK (MANDATORY — use this EXACT text in Scene 1): "{chosen_hook}"' if chosen_hook else ""}

OUTPUT FORMAT: Strict JSON, no markdown, no text outside the JSON:
[
  {{"id":1,"text":"scene text here","visual_1":"pexels search term","visual_2":"pexels search term","mood":"dramatic"}},
  {{"id":2,"text":"scene text here","visual_1":"pexels search term","visual_2":"pexels search term","mood":"dramatic"}}
]

JSON RULES:
- EXACTLY {num_scenes} entries — no more, no fewer.
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
            if len(scenes) > num_scenes:
                print(f"⚠️ AI returned {len(scenes)} viral scenes, trimming to {num_scenes}.")
                scenes = scenes[:num_scenes]
            elif len(scenes) < num_scenes:
                print(f"⚠️ AI returned only {len(scenes)} viral scenes (requested {num_scenes}).")
            print(f"✅ {len(scenes)} viral scenes ready")
            return scenes
        except Exception:
            sentences = [s.strip() for s in _re.split(r'(?<=[.!?])\s+', clean) if len(s.strip()) > 8][:num_scenes]
            return [
                {"id": i+1, "text": self._sanitize(s), "visual_1": "dramatic cinematic footage", "visual_2": "historical documentary", "mood": "dramatic"}
                for i, s in enumerate(sentences)
            ]

    def generate_testimonio_script(self, topic: str, category: str, lang: str = "es", chosen_hook: str = "", num_scenes: int = 9, max_words_per_scene: int = 999) -> list:
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

Estructura exacta (~{num_scenes * 5} segundos / EXACTAMENTE {num_scenes} escenas / MAXIMO {max_words_per_scene} palabras por escena):
  Escena 1 - HOOK PERTURBADOR (maximo 12 palabras, el espectador decide en 1.7 seg):
    OBLIGATORIO — uno de estos tipos:
    TIPO A: "[CIFRA] personas/casos [hecho perturbador]." Ej: "17 miembros de una secta murieron la misma noche. Nadie explica como."
    TIPO B: "Lo que [testigo/ex-miembro] revelo sobre [ELEMENTO ESPECIFICO] cambio todo."
    TIPO C: "Nadie habla de lo que paso realmente en [LUGAR/EVENTO ESPECIFICO DEL TEMA]."
    TIPO D: "¿Que harias si descubrieras que [HECHO PERTURBADOR CONCRETO]?"
  Escenas 2-{max(3, num_scenes - 3)} - TESTIGO + DESARROLLO: Presentacion del testimoniante y detalles escalofriantes.
  Escena {num_scenes - 1} - CLIMAX: La parte mas fuerte y perturbadora.
  Escena {num_scenes} - CIERRE: Consecuencia + CTA ("Vos crees en esto? Comenta SI o NO").

Reglas de estilo:
- Lenguaje conversacional, misterioso y dramatico.
- Frases como: "me conto que...", "revelo que...", "nadie se atreve a decir...", "lo mas aterrador fue...".
- PROHIBIDO: emojis, caracteres especiales Unicode (guiones largos, comillas rizadas, puntos suspensivos especiales).
- USA SOLO: letras, numeros, comas, puntos, signos de exclamacion, signos de interrogacion y apostrofes simples.
- En espanol neutro latino.

Tema: {topic}
Categoria: {category}{f'{chr(10)}HOOK PRE-SELECCIONADO (OBLIGATORIO usar este texto EXACTO en Escena 1): "{chosen_hook}"' if chosen_hook else ""}

FORMATO DE SALIDA: JSON estricto, sin markdown, sin texto fuera del JSON:
[
  {{"id":1,"text":"texto de la escena","visual_1":"dark forest night","visual_2":"candle ritual","visual_3":"mysterious shadow","mood":"horror"}},
  {{"id":2,"text":"texto de la escena","visual_1":"foggy cemetery","visual_2":"abandoned church","visual_3":"eerie fog","mood":"horror"}}
]

REGLAS DEL JSON:
- EXACTAMENTE {num_scenes} entradas — no mas, no menos.
- "text": el texto narrado de esa escena. Sin emojis. Sin caracteres especiales.
- "visual_1", "visual_2", "visual_3": terminos en INGLES para Pexels (2-4 palabras). Deben ser oscuros, atmosfericos: dark forest, candles, fog, shadow, cemetery, abandoned, storm, etc.
- "mood": siempre "horror"."""
        else:
            prompt = f"""You are an expert at creating horror and mystery stories in YouTube/TikTok Shorts format, Archimosfera style.

Tell the story as if it were a real testimony from a real person (ex-satanist, witness, priest, victim, etc.).

Exact structure (~{num_scenes * 5} seconds / EXACTLY {num_scenes} scenes / MAX {max_words_per_scene} words per scene):
  Scene 1 - DISTURBING HOOK (max 12 words, viewer decides in 1.7 sec):
    MANDATORY — one of these types:
    TYPE A: "[NUMBER] people/cases [disturbing fact]." E.g.: "17 cult members died the same night. Nobody explains how."
    TYPE B: "What [witness/ex-member/priest] revealed about [SPECIFIC ELEMENT] changed everything."
    TYPE C: "Nobody is talking about what really happened at [SPECIFIC PLACE/EVENT]."
    TYPE D: "What would you do if you found out that [DISTURBING CONCRETE FACT]?"
  Scenes 2-{max(3, num_scenes - 3)} - WITNESS + DEVELOPMENT: Introduce testimony person and chilling details gradually.
  Scene {num_scenes - 1} - CLIMAX: The strongest and most disturbing part.
  Scene {num_scenes} - CLOSING: Consequence + CTA ("Do you believe this? Comment YES or NO").

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
- EXACTLY {num_scenes} entries — no more, no fewer.
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
            if len(scenes) > num_scenes:
                print(f"⚠️ AI returned {len(scenes)} testimonio scenes, trimming to {num_scenes}.")
                scenes = scenes[:num_scenes]
            elif len(scenes) < num_scenes:
                print(f"⚠️ AI returned only {len(scenes)} testimonio scenes (requested {num_scenes}).")
            print(f"✅ {len(scenes)} testimonio scenes ready")
            return scenes
        except Exception:
            sentences = [s.strip() for s in _re.split(r'(?<=[.!?])\s+', clean) if len(s.strip()) > 8][:num_scenes]
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

    def generate_book_summary_script(self, book: str, category: str, lang: str = "es", chosen_hook: str = "", num_scenes: int = 9, max_words_per_scene: int = 999) -> list:
        """Resumen de libro de 60 seg — enseña, aplica y motiva a leer.
        Single-call: produce JSON scenes directly — no second AI call, no text modification."""
        import re as _re
        label = "Generando resumen del libro" if lang == "es" else "Generating book summary"
        print(f"📚 {label}: {book}...")

        if lang == "es":
            prompt = f"""Eres un narrador conversacional que habla directamente al oido del espectador. Tu voz sera leida por un sistema de texto a voz, por eso CADA FRASE debe sonar natural al ser pronunciada en voz alta.

Estructura (EXACTAMENTE {num_scenes} escenas / {num_scenes * 15}-{num_scenes * 18} palabras en total / MAXIMO {max_words_per_scene} palabras por escena):
  Escena 1 - GANCHO: Una verdad incomoda o dato sorprendente que el libro revela. Directo, sin rodeos.
  Escena 2 - EL LIBRO: Presenta el titulo y autor de forma natural, como si lo recomendaras a un amigo.
  Escenas 3-{max(4, num_scenes - 3)} - IDEAS + GIRO: La premisa principal y la idea mas inesperada del libro.
  Escena {num_scenes - 1} - EN TU VIDA: Como aplicar esto manana mismo, con un ejemplo concreto.
  Escena {num_scenes} - CIERRE + CTA: Una frase que quede resonando y llamada a la accion.

REGLAS CRITICAS PARA SONAR HUMANO:
- Cada escena: maximo 15 palabras. Frases cortas. Una idea por escena.
- Usa comas donde harias una pausa al hablar.
- Usa "..." solo para pausas dramaticas intencionales (maximo 2 veces en todo el guion).
- Habla en 2da persona: "tu", "te", "tu vida".
- Tono: como si le hablaras a un amigo inteligente, no como un libro de texto.
- Varía el ritmo: alterna frases muy cortas con frases medianas.
- PROHIBIDO: emojis, palabras rebuscadas, frases subordinadas largas, lenguaje de vendedor.
- PROHIBIDO: caracteres especiales Unicode. Solo letras, numeros, comas, puntos, signos de exclamacion, signos de interrogacion.

Libro: {book}
Categoria: {category}{f'{chr(10)}HOOK PRE-SELECCIONADO (OBLIGATORIO usar este texto EXACTO en Escena 1): "{chosen_hook}"' if chosen_hook else ""}

FORMATO DE SALIDA: JSON estricto, sin markdown, sin texto fuera del JSON:
[
  {{"id":1,"text":"texto corto y natural aqui","visual_1":"person reading book","visual_2":"open notebook writing","mood":"inspiring"}},
  {{"id":2,"text":"texto corto y natural aqui","visual_1":"city skyline sunrise","visual_2":"person thinking window","mood":"inspiring"}}
]

REGLAS DEL JSON:
- "text": el texto narrado. Maximo 15 palabras por escena. Sin caracteres especiales.
- "visual_1" y "visual_2": terminos en INGLES para Pexels (2-4 palabras). Inspiradores: personas leyendo, escribiendo, pensando, naturaleza, ciudad, exito. EVITAR visuals oscuros.
- "mood": siempre "inspiring"."""
        else:
            prompt = f"""You are a conversational narrator speaking directly into the viewer's ear. Your voice will be read by a text-to-speech system, so EVERY SENTENCE must sound natural when spoken out loud.

Structure (EXACTLY {num_scenes} scenes / {num_scenes * 15}-{num_scenes * 18} words total / MAX {max_words_per_scene} words per scene):
  Scene 1 - HOOK: An uncomfortable truth or surprising fact the book reveals. Direct, no fluff.
  Scene 2 - THE BOOK: Introduce the title and author naturally, like recommending it to a friend.
  Scenes 3-{max(4, num_scenes - 3)} - CORE IDEAS + TWIST: Main premise and most unexpected idea of the book.
  Scene {num_scenes - 1} - IN YOUR LIFE: How to apply this tomorrow, with a concrete example.
  Scene {num_scenes} - CLOSE + CTA: A line that keeps echoing and a simple call to action.

CRITICAL RULES FOR SOUNDING HUMAN:
- Each scene: maximum 15 words. Short sentences. One idea per scene.
- Use commas where you would pause when speaking.
- Use "..." only for intentional dramatic pauses (maximum 2 times in the whole script).
- Speak in 2nd person: "you", "your", "your life".
- Tone: like talking to a smart friend, not writing a textbook.
- Vary the rhythm: alternate very short sentences with medium ones.
- FORBIDDEN: emojis, complex vocabulary, long subordinate clauses, salesy language.
- FORBIDDEN: special Unicode characters. Only letters, numbers, commas, periods, exclamation marks, question marks.
- LANGUAGE: ENGLISH ONLY. No Spanish words.

Book: {book}
Category: {category}

OUTPUT FORMAT: Strict JSON, no markdown, no text outside the JSON:
[
  {{"id":1,"text":"short natural text here","visual_1":"person reading book","visual_2":"open notebook writing","mood":"inspiring"}},
  {{"id":2,"text":"short natural text here","visual_1":"city skyline sunrise","visual_2":"person thinking window","mood":"inspiring"}}
]

JSON RULES:
- "text": narrated text. Maximum 15 words per scene. No special characters.
- "visual_1" and "visual_2": English Pexels search terms (2-4 words). Inspiring: people reading, writing, thinking, nature, city, success. AVOID dark visuals.
- "mood": always "inspiring"."""

        raw   = self._generate(prompt)
        clean = raw.replace('```json', '').replace('```', '').strip()

        try:
            scenes = json.loads(clean)
            for i, s in enumerate(scenes):
                s['id']   = i + 1
                s['text'] = self._sanitize(s.get('text', ''))
                s.setdefault('mood', 'inspiring')
            if len(scenes) > num_scenes:
                print(f"⚠️ AI returned {len(scenes)} book scenes, trimming to {num_scenes}.")
                scenes = scenes[:num_scenes]
            elif len(scenes) < num_scenes:
                print(f"⚠️ AI returned only {len(scenes)} book scenes (requested {num_scenes}).")
            print(f"✅ {len(scenes)} book summary scenes ready")
            return scenes
        except Exception:
            sentences = [s.strip() for s in _re.split(r'(?<=[.!?])\s+', clean) if len(s.strip()) > 8][:num_scenes]
            return [
                {"id": i+1, "text": self._sanitize(s), "visual_1": "person reading book", "visual_2": "open notebook inspiring", "mood": "inspiring"}
                for i, s in enumerate(sentences)
            ]

    def generate_bible_script(self, verse: str, category: str, lang: str = "es", chosen_hook: str = "", num_scenes: int = 9, max_words_per_scene: int = 999) -> list:
        """Reflexión bíblica de 60 seg centrada en UN versículo como fuente de toda la narración."""
        import re as _re
        print(f"✝️ Generando reflexión bíblica: {verse}...")

        if lang == "es":
            prompt = f"""Eres un narrador espiritual que habla directamente al corazon del espectador. Tu voz sera leida por texto a voz, cada frase debe sonar natural al pronunciarse.

VERSÍCULO FUENTE: "{verse}"
Este versículo es el UNICO fundamento de todo el guion. Todo gira en torno a el.

Estructura (EXACTAMENTE {num_scenes} escenas / {num_scenes * 15}-{num_scenes * 18} palabras en total / MAXIMO {max_words_per_scene} palabras por escena):
  Escena 1 - GANCHO: Una pregunta o verdad poderosa que conecta con la vida del espectador. Directo al corazon.
  Escena 2 - EL VERSICULO: Cita el texto EXACTO del versiculo y su referencia biblica. Claro y solemne.
  Escenas 3-{max(4, num_scenes - 3)} - REFLEXION + GIRO: Que significa este versiculo, la idea mas profunda e inesperada que encierra.
  Escena {num_scenes - 1} - EN TU VIDA: Como aplicar este versiculo hoy mismo, con un ejemplo concreto y practico.
  Escena {num_scenes} - CIERRE + CTA: Una frase que quede resonando y llamada a la accion (guardar, compartir, reflexionar).

REGLAS CRITICAS:
- Cada escena: maximo 15 palabras. Frases cortas. Una idea por escena.
- Usa comas donde harias una pausa al hablar.
- Habla en 2da persona: "tu", "te", "tu vida".
- Tono: espiritual, esperanzador, como un pastor que le habla a un amigo.
- PROHIBIDO: emojis, palabras rebuscadas, lenguaje religioso forzado o fanático.
- PROHIBIDO: caracteres especiales Unicode. Solo letras, numeros, comas, puntos, signos de exclamacion, signos de interrogacion.
- NO inventes versiculos. Usa solo el versiculo fuente indicado.
{f'HOOK PRE-SELECCIONADO (OBLIGATORIO usar este texto EXACTO en Escena 1): "{chosen_hook}"' if chosen_hook else ""}

Categoria: {category}

FORMATO DE SALIDA: JSON estricto, sin markdown, sin texto fuera del JSON:
[
  {{"id":1,"text":"texto corto y natural aqui","visual_1":"person praying sunrise","visual_2":"open bible candle light","mood":"inspiring"}},
  {{"id":2,"text":"texto corto y natural aqui","visual_1":"peaceful nature light","visual_2":"person meditating calm","mood":"inspiring"}}
]

REGLAS DEL JSON:
- "text": el texto narrado. Maximo 15 palabras. Sin caracteres especiales.
- "visual_1" y "visual_2": terminos en INGLES para Pexels (2-4 palabras). Espirituales y luminosos: persona orando, biblia abierta, naturaleza tranquila, luz solar, familia unida, esperanza. EVITAR visuals oscuros.
- "mood": siempre "inspiring"."""
        else:
            prompt = f"""You are a spiritual narrator speaking directly into the viewer's heart. Your voice will be read by text-to-speech, every sentence must sound natural when spoken.

SOURCE VERSE: "{verse}"
This verse is the ONLY foundation of the entire script. Everything revolves around it.

Structure (EXACTLY {num_scenes} scenes / {num_scenes * 15}-{num_scenes * 18} words total / MAX {max_words_per_scene} words per scene):
  Scene 1 - HOOK: A powerful question or truth that connects with the viewer's life. Straight to the heart.
  Scene 2 - THE VERSE: Quote the EXACT text of the verse and its biblical reference. Clear and solemn.
  Scenes 3-{max(4, num_scenes - 3)} - REFLECTION + TWIST: What this verse means, the deepest and most unexpected idea it holds.
  Scene {num_scenes - 1} - IN YOUR LIFE: How to apply this verse today, with a concrete practical example.
  Scene {num_scenes} - CLOSE + CTA: A line that keeps echoing and a call to action (save, share, reflect).

CRITICAL RULES:
- Each scene: maximum 15 words. Short sentences. One idea per scene.
- Use commas where you would pause when speaking.
- Speak in 2nd person: "you", "your", "your life".
- Tone: spiritual, hopeful, like a pastor talking to a friend.
- FORBIDDEN: emojis, complex vocabulary, forced or fanatical religious language.
- FORBIDDEN: special Unicode characters. Only letters, numbers, commas, periods, exclamation marks, question marks.
- Do NOT invent verses. Use only the source verse provided.
- LANGUAGE: ENGLISH ONLY.
{f'PRE-SELECTED HOOK (MANDATORY use this EXACT text in Scene 1): "{chosen_hook}"' if chosen_hook else ""}

Category: {category}

OUTPUT FORMAT: Strict JSON, no markdown, no text outside the JSON:
[
  {{"id":1,"text":"short natural text here","visual_1":"person praying sunrise","visual_2":"open bible candle light","mood":"inspiring"}},
  {{"id":2,"text":"short natural text here","visual_1":"peaceful nature light","visual_2":"person meditating calm","mood":"inspiring"}}
]

JSON RULES:
- "text": narrated text. Maximum 15 words. No special characters.
- "visual_1" and "visual_2": English Pexels search terms (2-4 words). Spiritual and luminous: person praying, open bible, peaceful nature, sunlight, united family, hope. AVOID dark visuals.
- "mood": always "inspiring"."""

        raw   = self._generate(prompt)
        clean = raw.replace('```json', '').replace('```', '').strip()

        try:
            scenes = json.loads(clean)
            for i, s in enumerate(scenes):
                s['id']   = i + 1
                s['text'] = self._sanitize(s.get('text', ''))
                s.setdefault('mood', 'inspiring')
            if len(scenes) > num_scenes:
                scenes = scenes[:num_scenes]
            print(f"✅ {len(scenes)} bible scenes ready")
            return scenes
        except Exception:
            sentences = [s.strip() for s in _re.split(r'(?<=[.!?])\s+', clean) if len(s.strip()) > 8][:num_scenes]
            return [
                {"id": i+1, "text": self._sanitize(s), "visual_1": "person praying sunrise", "visual_2": "open bible light", "mood": "inspiring"}
                for i, s in enumerate(sentences)
            ]

    def generate_job_offer_script(self, offer_text: str, lang: str = "es") -> list:
        """Convierte una oferta de empleo en un guion de video promocional.
        Preserva TODA la información original — solo la presenta de forma atractiva."""
        import re as _re
        label = "Convirtiendo oferta de empleo en guion" if lang == "es" else "Converting job offer to script"
        print(f"💼 {label}...")

        if lang == "es":
            prompt = f"""Eres el director creativo de anuncios de empleo más energicos y virales de TikTok y YouTube Shorts.

OFERTA DE EMPLEO (texto original del cliente):
---
{offer_text}
---

TAREA: Crea exactamente 6 escenas — video de 30 SEGUNDOS EXACTOS — estilo anuncio de TV de alto impacto.

REGLAS ABSOLUTAS:
- PROHIBIDO inventar, exagerar o añadir información que NO esté en el texto original.
- Presenta la información de forma EXPLOSIVA y ENERGICA, pero 100% fiel al original.
- Si el salario está en la oferta, DEBES mencionarlo — es el gancho mas poderoso.
- Tono: directo, urgente, habla en 2da persona ("tu", "tu carrera", "si buscas").
- Cada escena: MAXIMO 10 PALABRAS. Frases cortas, poderosas, sin relleno.
- PROHIBIDO: emojis, caracteres especiales Unicode, palabras en ingles (excepto nombre de empresa).
- TODO el mood debe ser "energetic" — rapido, dinamico, sin pausa.

ESTRUCTURA (6 escenas exactas — ~5 seg cada una):
  Escena 1 — GANCHO EXPLOSIVO: El beneficio mas impactante. Impresiona en 3 segundos.
  Escena 2 — EMPRESA + PUESTO: Quien contrata y que rol. Ultra corto.
  Escena 3 — REQUISITO CLAVE: El mas importante, presentado como "si tienes X, es para ti".
  Escena 4 — BENEFICIO ESTRELLA: Salario, modalidad, crecimiento — lo mas atractivo.
  Escena 5 — URGENCIA: Por que aplicar YA. Plazas limitadas, oportunidad unica, etc.
  Escena 6 — CTA DIRECTO: Aplica ya. Link en descripcion. Accion inmediata.

FORMATO DE SALIDA (JSON estricto, sin markdown, exactamente 6 elementos):
[
  {{"id":1,"text":"texto aqui maximo 10 palabras","visual_1":"energetic job interview success","visual_2":"modern office team celebrating","mood":"energetic"}},
  {{"id":2,"text":"texto aqui","visual_1":"company brand building","visual_2":"professional team working","mood":"energetic"}}
]

REGLAS DEL JSON:
- "text": MAXIMO 10 PALABRAS por escena. Frases de impacto. Sin puntos finales innecesarios.
- "visual_1" y "visual_2": terminos EN INGLES para Pexels (2-4 palabras). Dinamicos: success celebration, career growth, job interview, modern workspace, team achievement, business success.
- "mood": SIEMPRE "energetic" en todas las escenas."""
        else:
            prompt = f"""You are the creative director of the most energetic and viral job ad videos on TikTok and YouTube Shorts.

JOB OFFER (original client text):
---
{offer_text}
---

TASK: Create exactly 6 scenes — a 30-SECOND video — high-impact TV ad style.

ABSOLUTE RULES:
- FORBIDDEN to invent, exaggerate or add information NOT in the original text.
- Present information in an EXPLOSIVE, ENERGETIC way — 100% faithful to the original.
- If salary is in the offer, you MUST mention it — it's the most powerful hook.
- Tone: direct, urgent, speak in 2nd person ("you", "your career", "if you're looking").
- Each scene: MAXIMUM 10 WORDS. Short, powerful phrases. Zero filler.
- FORBIDDEN: emojis, special Unicode characters. ENGLISH ONLY.
- ALL moods must be "energetic" — fast, dynamic, no pauses.

STRUCTURE (exactly 6 scenes — ~5 sec each):
  Scene 1 — EXPLOSIVE HOOK: The most impactful benefit. Wow in 3 seconds.
  Scene 2 — COMPANY + ROLE: Who's hiring and what role. Ultra short.
  Scene 3 — KEY REQUIREMENT: The most important one, framed as "if you have X, this is for you".
  Scene 4 — STAR BENEFIT: Salary, work model, growth — the most attractive detail.
  Scene 5 — URGENCY: Why apply NOW. Limited spots, unique opportunity, etc.
  Scene 6 — DIRECT CTA: Apply now. Link in description. Immediate action.

OUTPUT FORMAT (strict JSON, no markdown, exactly 6 items):
[
  {{"id":1,"text":"max 10 words here","visual_1":"energetic job interview success","visual_2":"modern office team celebrating","mood":"energetic"}},
  {{"id":2,"text":"text here","visual_1":"company brand building","visual_2":"professional team working","mood":"energetic"}}
]

JSON RULES:
- "text": MAXIMUM 10 WORDS per scene. Impact phrases. No unnecessary punctuation.
- "visual_1" and "visual_2": English Pexels search terms (2-4 words). Dynamic: success celebration, career growth, job interview, modern workspace, team achievement, business success.
- "mood": ALWAYS "energetic" for ALL scenes."""

        raw   = self._generate(prompt)
        clean = raw.replace('```json', '').replace('```', '').strip()

        try:
            scenes = json.loads(clean)
            for i, s in enumerate(scenes):
                s['id']   = i + 1
                s['text'] = self._sanitize(s.get('text', ''))
                s['mood'] = 'energetic'   # siempre energético para empleo
            print(f"✅ {len(scenes)} job offer scenes ready (~30s)")
            return scenes
        except Exception:
            sentences = [s.strip() for s in _re.split(r'(?<=[.!?])\s+', clean) if len(s.strip()) > 8][:6]
            return [
                {"id": i+1, "text": self._sanitize(s), "visual_1": "job interview success", "visual_2": "career growth celebration", "mood": "energetic"}
                for i, s in enumerate(sentences)
            ]

    def generate_freeform_script(self, raw_text: str, lang: str = "es") -> list:
        """Convierte texto libre (noticias, chismes, reflexiones, curiosidades) en un
        guion de YouTube Shorts adaptado al tono del texto original."""
        import re as _re
        label = "Adaptando texto libre a guion viral" if lang == "es" else "Adapting freeform text to viral script"
        print(f"✍️ {label}...")

        if lang == "es":
            prompt = f"""Eres un experto creador de contenido viral para YouTube Shorts en español latino.

TEXTO DEL USUARIO:
---
{raw_text[:4000]}
---

TAREA:
1. Detecta el TONO del texto (noticia, chisme/entretenimiento, reflexion personal, dato curioso, opinion, humor, otro).
2. Adapta ese contenido para YouTube Shorts — dinamico, rapido, viral — SIN inventar informacion nueva.
3. Preserva todos los hechos, nombres y datos clave del texto original.
4. Adapta el estilo de narracion al tono detectado:
   - Noticia: voz de reportero, datos precisos, urgencia ("Segun reportes...", "Esto acaba de ocurrir...")
   - Chisme/entretenimiento: conversacional, emocionante, ganchos ("Y lo que nadie sabe es...", "Pero aqui lo interesante...")
   - Reflexion/opinion: cercana, emotiva, pausada ("Piensalo asi...", "Esto me hizo pensar...")
   - Dato curioso: asombro, impacto, revelacion ("Lo que pocos saben es...", "Resulta que...")
   - Humor: ligero, ganchos, ritmo rapido
5. Genera entre 7 y 10 escenas cortas y dinamicas.
6. La primera escena SIEMPRE debe ser el GANCHO mas poderoso del texto.
7. PROHIBIDO: emojis, caracteres Unicode especiales, inventar informacion.
8. Maximo 20 palabras por escena.

FORMATO JSON (sin markdown):
[
  {{"id":1,"text":"texto narrado aqui","visual_1":"english pexels search","visual_2":"alternative english search","mood":"exciting|dramatic|calm|mysterious|informative|fun"}},
  ...
]

Reglas del JSON:
- "text": espanol latino neutro, maximo 20 palabras, sin simbolos especiales.
- "visual_1" y "visual_2": terminos de busqueda EN INGLES para Pexels (2-4 palabras).
- "mood": segun el tono de cada escena.

Responde SOLO el JSON, sin explicaciones."""
        else:
            prompt = f"""You are an expert viral content creator for YouTube Shorts.

USER TEXT:
---
{raw_text[:4000]}
---

TASK:
1. Detect the TONE of the text (news, gossip/entertainment, personal reflection, fun fact, opinion, humor, other).
2. Adapt the content for YouTube Shorts — dynamic, fast, viral — WITHOUT inventing new information.
3. Preserve all facts, names and key data from the original text.
4. Adapt narration style to the detected tone:
   - News: reporter voice, precise data, urgency ("According to reports...", "This just happened...")
   - Gossip/entertainment: conversational, exciting, hooks ("And what nobody knows is...", "But here's the interesting part...")
   - Reflection/opinion: close, emotional, paced ("Think about it this way...", "This made me realize...")
   - Fun fact: amazement, impact, revelation ("What few people know is...", "It turns out that...")
   - Humor: light, hooks, fast pace
5. Generate between 7 and 10 short dynamic scenes.
6. The first scene MUST always be the most powerful HOOK from the text.
7. FORBIDDEN: emojis, special Unicode characters, inventing information.
8. Maximum 20 words per scene.

JSON FORMAT (no markdown):
[
  {{"id":1,"text":"narrated text here","visual_1":"english pexels search","visual_2":"alternative english search","mood":"exciting|dramatic|calm|mysterious|informative|fun"}},
  ...
]

Rules:
- "text": English, maximum 20 words, no special characters.
- "visual_1" and "visual_2": English Pexels search terms (2-4 words).
- "mood": matching the tone of each scene.

Respond ONLY with the JSON, no explanations."""

        raw   = self._generate(prompt)
        clean = raw.replace('```json', '').replace('```', '').strip()

        try:
            scenes = json.loads(clean)
            for i, s in enumerate(scenes):
                s['id']   = i + 1
                s['text'] = self._sanitize(s.get('text', ''))
                s.setdefault('mood', 'informative')
            print(f"✅ {len(scenes)} freeform scenes ready")
            return scenes
        except Exception:
            sentences = [s.strip() for s in _re.split(r'(?<=[.!?])\s+', clean) if len(s.strip()) > 8][:10]
            return [
                {"id": i+1, "text": self._sanitize(s), "visual_1": "people talking news", "visual_2": "interesting facts world", "mood": "informative"}
                for i, s in enumerate(sentences)
            ]

    def generate_script(self, topic: str, num_scenes: int = 9, lang: str = "es", chosen_hook: str = "") -> list:
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
- **Flujo:** Gancho -> Contexto -> Mecanismo -> Giro inesperado -> Cierre memorable.
- **HOOK CRITICO (Escena 1, maximo 12 palabras):** OBLIGATORIO uno de: (A) Numero shockeante + consecuencia brutal, (B) "Todo lo que sabes sobre X esta mal", (C) "Nadie habla de lo que paso con X", (D) Pregunta trampa imposible de ignorar.{f' HOOK PRE-SELECCIONADO (usar EXACTO): "{chosen_hook}"' if chosen_hook else ""}

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
- **Flow:** Hook -> Context -> Mechanism -> Twist -> Memorable Outro.
- **CRITICAL HOOK (Scene 1, max 12 words):** MANDATORY one of: (A) Shocking number + brutal consequence, (B) "Everything you know about X is wrong", (C) "Nobody is talking about what happened with X", (D) Impossible-to-ignore trap question.{f' PRE-SELECTED HOOK (use EXACT text): "{chosen_hook}"' if chosen_hook else ""}

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

    def generate_podcast_script(self, topic: str, host_name: str = "Host",
                                guest_name: str = "Invitado", lang: str = "es",
                                num_exchanges: int = 6, max_words_per_scene: int = 999) -> list:
        """Genera un diálogo estilo podcast entre dos personas para YouTube Shorts."""
        import re as _re
        print(f"🎙️ Generando diálogo podcast: {topic}...")

        if lang == "es":
            prompt = f"""Eres el guionista de un canal de podcast viral para YouTube Shorts en español latino.

Genera un diálogo natural y fluido entre dos personas:
- Host: {host_name} — hace preguntas, presenta el tema, conduce la conversación
- Invitado: {guest_name} — responde con datos fascinantes, revela información impactante

Tema: {topic}

ESTRUCTURA (EXACTAMENTE {num_exchanges} intercambios / MAXIMO {max_words_per_scene} palabras por turno):
- Turno 1 (Host): Hook viral — pregunta o dato impactante que engancha en 1.7 segundos
- Turnos 2-{num_exchanges - 1}: Diálogo natural alternado con revelaciones progresivas
- Turno {num_exchanges} (Host o Guest): Conclusión + CTA ("Comenta qué opinas y síguenos")

REGLAS:
- Lenguaje conversacional, como si hablaran de verdad, no como narración
- Frases cortas y directas — máximo {max_words_per_scene} palabras por turno
- Datos reales y verificables
- PROHIBIDO: emojis, caracteres Unicode especiales
- Solo letras, números, comas, puntos, signos de exclamación e interrogación

FORMATO JSON estricto, sin markdown:
[
  {{"id":1,"speaker":"host","text":"¿Sabías que...?","visual_1":"podcast studio microphone","visual_2":"two people talking","mood":"informative"}},
  {{"id":2,"speaker":"guest","text":"Sí, y lo más increíble es...","visual_1":"person explaining animated","visual_2":"podcast closeup face","mood":"informative"}}
]

REGLAS DEL JSON:
- "speaker": "host" o "guest" (alternando, empezar con host)
- "text": el diálogo de ese turno. MAX {max_words_per_scene} palabras. Sin caracteres especiales.
- "visual_1" y "visual_2": términos EN INGLÉS para Pexels (2-4 palabras). Podcast: studio, microphone, conversation, talking, discussion.
- "mood": "informative", "fun", "exciting" o "professional"
- EXACTAMENTE {num_exchanges} entradas"""
        else:
            prompt = f"""You are the scriptwriter of a viral podcast channel for YouTube Shorts.

Generate a natural and fluid dialogue between two people:
- Host: {host_name} — asks questions, introduces the topic, leads the conversation
- Guest: {guest_name} — responds with fascinating data, reveals impactful information

Topic: {topic}

STRUCTURE (EXACTLY {num_exchanges} exchanges / MAX {max_words_per_scene} words per turn):
- Turn 1 (Host): Viral hook — impactful question or fact that hooks in 1.7 seconds
- Turns 2-{num_exchanges - 1}: Natural alternating dialogue with progressive revelations
- Turn {num_exchanges} (Host or Guest): Conclusion + CTA ("Comment what you think and follow us")

RULES:
- Conversational language, as if they are really talking, not narrating
- Short and direct phrases — maximum {max_words_per_scene} words per turn
- Real and verifiable data
- FORBIDDEN: emojis, special Unicode characters
- Only letters, numbers, commas, periods, exclamation and question marks

Strict JSON format, no markdown:
[
  {{"id":1,"speaker":"host","text":"Did you know that...?","visual_1":"podcast studio microphone","visual_2":"two people talking","mood":"informative"}},
  {{"id":2,"speaker":"guest","text":"Yes, and the most incredible thing is...","visual_1":"person explaining animated","visual_2":"podcast closeup face","mood":"informative"}}
]

JSON RULES:
- "speaker": "host" or "guest" (alternating, start with host)
- "text": the dialogue for that turn. MAX {max_words_per_scene} words. No special characters.
- "visual_1" and "visual_2": English Pexels search terms (2-4 words). Podcast: studio, microphone, conversation, talking, discussion.
- "mood": "informative", "fun", "exciting" or "professional"
- EXACTLY {num_exchanges} entries"""

        raw   = self._generate(prompt)
        clean = raw.replace('```json', '').replace('```', '').strip()

        try:
            scenes = json.loads(clean)
            for i, s in enumerate(scenes):
                s['id']   = i + 1
                s['text'] = self._sanitize(s.get('text', ''))
                s.setdefault('mood', 'informative')
                s.setdefault('speaker', 'host' if i % 2 == 0 else 'guest')
            if len(scenes) > num_exchanges:
                print(f"⚠️ AI returned {len(scenes)} podcast scenes, trimming to {num_exchanges}.")
                scenes = scenes[:num_exchanges]
            elif len(scenes) < num_exchanges:
                print(f"⚠️ AI returned only {len(scenes)} podcast scenes (requested {num_exchanges}).")
            print(f"✅ {len(scenes)} podcast scenes ready")
            return scenes
        except Exception:
            sentences = [s.strip() for s in _re.split(r'(?<=[.!?])\s+', clean) if len(s.strip()) > 8][:num_exchanges]
            return [
                {
                    "id": i + 1,
                    "text": self._sanitize(s),
                    "speaker": "host" if i % 2 == 0 else "guest",
                    "visual_1": "podcast studio microphone",
                    "visual_2": "two people talking",
                    "mood": "informative",
                }
                for i, s in enumerate(sentences)
            ]

    def generate_quote_card_prompts(
        self,
        quote: str = "",
        category: str = "",
        lang: str = "es",
    ) -> dict:
        """
        Genera prompts de imagen para una frase célebre o viral en 3 formatos:
        9:16 (Reels/Stories), 1:1 (Instagram post), 16:9 (YouTube/LinkedIn).

        Si no se provee frase, la IA elige una viral/célebre de la categoría dada.
        Retorna dict con keys: quote_used, prompt_9_16, prompt_1_1, prompt_16_9
        """
        print(f"💬 Generando prompts de frase viral [{category or 'auto'}]...")

        # ── Step 1: resolve quote ─────────────────────────────────────────────
        if not quote.strip() and category.strip():
            if lang == "es":
                _qprompt = (
                    f"Dame UNA frase célebre, viral o motivacional de la categoría: {category}.\n"
                    f"Debe ser impactante, compartible y no demasiado larga (máximo 20 palabras).\n"
                    f"Puede ser de un personaje famoso o una frase anónima que haya viralizado.\n"
                    f"Responde SOLO con la frase y el autor si lo hay (formato: 'Frase.' — Autor). Nada más."
                )
            else:
                _qprompt = (
                    f"Give me ONE famous, viral or motivational quote from the category: {category}.\n"
                    f"Must be impactful, shareable, not too long (max 20 words).\n"
                    f"Can be from a famous person or an anonymous viral phrase.\n"
                    f"Respond ONLY with the quote and author if known (format: 'Quote.' — Author). Nothing else."
                )
            quote = self._sanitize(self._generate(_qprompt).strip())
        elif not quote.strip():
            if lang == "es":
                _qprompt = (
                    f"Dame UNA frase célebre o viral de cualquier categoría que esté generando "
                    f"mucha interacción en redes sociales actualmente. "
                    f"Máximo 20 palabras. Formato: 'Frase.' — Autor (o 'Anónimo'). Solo la frase."
                )
            else:
                _qprompt = (
                    f"Give me ONE famous or viral quote from any category that's generating "
                    f"high social media engagement right now. "
                    f"Max 20 words. Format: 'Quote.' — Author (or 'Anonymous'). Just the quote."
                )
            quote = self._sanitize(self._generate(_qprompt).strip())

        print(f"💬 Frase: {quote[:80]}")

        # ── Step 2: common context for all 3 formats ──────────────────────────
        _ctx = f"Quote / frase: \"{quote}\"\nCategory / categoría: {category or 'general'}"

        _style_ref = (
            "Visual style rules:\n"
            "- Cinematic, dramatic, high-contrast\n"
            "- The quote text MUST appear as an overlay on the image (specify exact text)\n"
            "- Background: rich, atmospheric, relevant to the quote's theme\n"
            "- Lighting: dramatic volumetric light (god rays, rim light, or neon glow)\n"
            "- Color palette: deep moody tones OR vibrant energetic tones — match the quote's emotion\n"
            "- Photorealistic or painterly — NO flat design, NO plain backgrounds\n"
            "- PROHIBIDO: bordes blancos, fondos lisos, diseño minimalista sin textura\n"
            "- The quote text overlay must be bold, legible, high contrast, in the quote's original language\n"
            "- Do NOT add any text beyond the quote and optional author credit\n"
        )

        # ── Step 3: generate 3 format prompts in one LLM call ─────────────────
        if lang == "es":
            _main_prompt = f"""Eres un experto en diseño de contenido viral para redes sociales y un maestro generando prompts para IA de imagen (Midjourney, DALL-E, Flux, Ideogram).

{_ctx}

TAREA: Genera EXACTAMENTE 3 prompts de imagen — uno por formato — para una "quote card" (tarjeta con frase) de alto impacto visual que genere interacción masiva en redes sociales.

{_style_ref}

INSTRUCCIONES POR FORMATO:

**FORMATO 9:16 (Reels / Stories / TikTok — VERTICAL)**
- Composición vertical dominante
- La frase ocupa el centro o la mitad inferior
- Fondo: escena atmosférica vertical que no compite con el texto
- Estilo: dramático, editorial, para capturar scroll en 0.5 segundos

**FORMATO 1:1 (Instagram Post / Facebook — CUADRADO)**
- Composición equilibrada y centrada
- La frase puede estar arriba, centro o abajo con margen igual en todos lados
- Fondo: equilibrado, no muy ocupado en los bordes
- Estilo: limpio pero poderoso, optimizado para engagement de post

**FORMATO 16:9 (YouTube / LinkedIn / Twitter — HORIZONTAL)**
- La frase en el tercio izquierdo o centrada
- Background dramático en el tercio derecho o detrás
- Espacio visual izquierdo para texto, lado derecho con escena
- Estilo: thumbnail cinematográfico, click-worthy

FORMATO DE SALIDA (JSON estricto, sin markdown):
{{
  "quote_used": "la frase exacta que usarás",
  "prompt_9_16": "prompt completo en inglés listo para pegar en Midjourney/DALL-E — incluye la frase como texto overlay especificado, composición vertical, iluminación, estilo",
  "prompt_1_1":  "prompt completo en inglés — composición cuadrada, misma frase como texto overlay",
  "prompt_16_9": "prompt completo en inglés — composición horizontal 16:9, misma frase como texto overlay",
  "copy_tiktok": "1-2 líneas gancho + salto de línea + hashtags TikTok: SIEMPRE incluir #fyp #viral al inicio + 2 hashtags de nicho específicos. MAXIMO 4 hashtags en total. En español.",
  "copy_instagram": "2-3 líneas reflexivas que inviten a guardar o compartir + doble salto de línea + EXACTAMENTE 4 hashtags: 1 amplio (1M+ posts) + 1 mediano (100K-1M) + 2 de nicho específico (<100K). MAXIMO 4 hashtags. En español.",
  "copy_facebook": "2-3 líneas conversacionales que generen comentarios (pregunta al final) + MAXIMO 3 hashtags del nicho. Facebook penaliza el exceso de hashtags — menos es más. En español.",
  "copy_twitter": "1 frase directa e impactante + MAXIMO 2 hashtags trending. Máximo 280 caracteres total. En español."
}}

REGLAS CRÍTICAS:
- Los prompts van en INGLÉS (para compatibilidad con los modelos de imagen)
- El texto de la frase que aparece en la imagen va en el IDIOMA ORIGINAL de la frase
- Cada prompt debe tener mínimo 80 palabras y máximo 200 palabras
- Cada prompt debe especificar: sujeto/escena, composición, iluminación, estilo, texto overlay, ratio
- NO repitas el mismo background en los 3 formatos — adapta el encuadre
- Los copies van en español neutro, directos y optimizados para máxima viralidad en cada plataforma
- Los hashtags deben ser REALES y específicos del nicho — PROHIBIDO hashtags genéricos vacíos"""
        else:
            _main_prompt = f"""You are an expert in viral social media content design and a master at generating prompts for AI image generation (Midjourney, DALL-E, Flux, Ideogram).

{_ctx}

TASK: Generate EXACTLY 3 image prompts — one per format — for a high-impact "quote card" that drives massive engagement on social media.

{_style_ref}

FORMAT INSTRUCTIONS:

**FORMAT 9:16 (Reels / Stories / TikTok — VERTICAL)**
- Vertical dominant composition
- Quote occupies center or lower half
- Background: atmospheric vertical scene that doesn't compete with text
- Style: dramatic, editorial, designed to stop scrolling in 0.5 seconds

**FORMAT 1:1 (Instagram Post / Facebook — SQUARE)**
- Balanced, centered composition
- Quote can be top, center or bottom with equal margins on all sides
- Background: balanced, not too busy at edges
- Style: clean but powerful, optimized for post engagement

**FORMAT 16:9 (YouTube / LinkedIn / Twitter — HORIZONTAL)**
- Quote in left third or centered
- Dramatic background in right third or behind
- Left visual space for text, right side with scene
- Style: cinematic thumbnail, click-worthy

OUTPUT FORMAT (strict JSON, no markdown):
{{
  "quote_used": "the exact quote you're using",
  "prompt_9_16": "complete English prompt ready to paste in Midjourney/DALL-E — includes the quote as specified text overlay, vertical composition, lighting, style",
  "prompt_1_1":  "complete English prompt — square composition, same quote as text overlay",
  "prompt_16_9": "complete English prompt — horizontal 16:9 composition, same quote as text overlay",
  "copy_tiktok": "1-2 hook lines + line break + TikTok hashtags: ALWAYS start with #fyp #viral + 2 niche-specific hashtags. MAXIMUM 4 hashtags total. In English.",
  "copy_instagram": "2-3 reflective lines inviting saves or shares + double line break + EXACTLY 4 hashtags: 1 broad (1M+ posts) + 1 medium (100K-1M) + 2 niche-specific (<100K). MAXIMUM 4 hashtags. In English.",
  "copy_facebook": "2-3 conversational lines that spark comments (end with a question) + MAXIMUM 3 niche hashtags. Facebook penalizes hashtag overload — less is more. In English.",
  "copy_twitter": "1 direct impactful sentence + MAXIMUM 2 trending hashtags. Max 280 characters total. In English."
}}

CRITICAL RULES:
- Prompts in ENGLISH (for AI image model compatibility)
- The quote text that appears in the image stays in its original language
- Each prompt: minimum 80 words, maximum 200 words
- Each prompt must specify: subject/scene, composition, lighting, style, text overlay, ratio
- Do NOT reuse the same background for all 3 formats — adapt the framing
- Copies must be punchy and optimized for maximum virality on each platform
- Hashtags must be REAL and niche-specific — FORBIDDEN generic empty hashtags"""

        raw   = self._generate(_main_prompt)
        clean = raw.replace("```json", "").replace("```", "").strip()
        bracket = clean.find("{")
        if bracket > 0:
            clean = clean[bracket:]
        try:
            import json as _j
            result = _j.loads(clean)
            return {
                "quote_used":     result.get("quote_used", quote),
                "prompt_9_16":    self._sanitize(result.get("prompt_9_16", "")),
                "prompt_1_1":     self._sanitize(result.get("prompt_1_1", "")),
                "prompt_16_9":    self._sanitize(result.get("prompt_16_9", "")),
                "copy_tiktok":    self._sanitize(result.get("copy_tiktok", "")),
                "copy_instagram": self._sanitize(result.get("copy_instagram", "")),
                "copy_facebook":  self._sanitize(result.get("copy_facebook", "")),
                "copy_twitter":   self._sanitize(result.get("copy_twitter", "")),
            }
        except Exception:
            return {
                "quote_used":     quote,
                "prompt_9_16":    clean[:800],
                "prompt_1_1":     "",
                "prompt_16_9":    "",
                "copy_tiktok":    "",
                "copy_instagram": "",
                "copy_facebook":  "",
                "copy_twitter":   "",
            }

    def generate_thumbnail_prompt(self, topic: str, script: list, lang: str = "es",
                                   mode: str = "auto", offer_text: str = "") -> str:
        print("🖼️ Generating thumbnail prompt...")
        hook = script[0]['text'] if script else ""

        # ── MODO EMPLEO: prompt especializado de reclutamiento ─────────────────
        if mode == "empleo":
            # Extraer datos clave del guion para no inventar nada
            script_lines = " | ".join(s.get("text", "") for s in script[:6])
            source_ctx   = offer_text.strip()[:1200] if offer_text.strip() else script_lines

            prompt = f"""You are an expert in visual marketing, performance ads and viral recruitment thumbnail design.

JOB OFFER SOURCE (use ONLY this — do NOT invent anything):
---
{source_ctx}
---

EXTRACTED SCRIPT SCENES (reference for copy):
{script_lines}

YOUR TASK: Generate ONE complete image prompt (ready for DALL-E / Midjourney) for a job offer thumbnail.

MANDATORY RULES:
1. RECRUITMENT FOCUS — transmit opportunity, growth and money. Positive and energetic.
2. 70% positive visual dominance. If using contrast (duality), positive side must dominate.
3. COPY INSIDE THE IMAGE (extract ONLY from the offer, no invention):
   - Top title: what the job is (e.g. "REPARTIDOR", "VENDEDOR", "DISEÑADOR")
   - Main headline: the economic or emotional main benefit
   - Secondary badge: specific earning or key advantage (salary if mentioned)
   - Call to action: "EMPIEZA HOY" or "APLICA YA"
4. VISUAL STYLE:
   - Viral thumbnail, cinematic, optimistic and energetic
   - Dramatic but positive lighting: golden glow, neon energy, bright highlights
   - Progress elements: money, apps, metrics, action, celebration, success
   - Vertical composition 9:16, centered, mobile-optimized
   - Photorealistic, 8K, maximum detail
5. ADAPT to job type detected:
   - Delivery/field: outdoor energy, vehicle, city, motion blur
   - Office/remote: modern workspace, laptop, skyline, professional glow
   - Sales: handshake, money rain, targets hit, celebration
   - Technical: tools, precision, expertise glow
6. TEXT ON IMAGE: ALL IN SPANISH (Spanish-speaking audience)
7. PROMPT LANGUAGE: English (for AI image generation compatibility)

OUTPUT FORMAT — return exactly this structure, no markdown, no explanations:

[ONE LINE: brief creative concept]
---
[FULL PROMPT ready for DALL-E/Midjourney, in English, with Spanish overlay texts specified]
"""
            return self._generate(prompt).strip()

        # ── RESTO DE MODOS: prompt cinematográfico estándar ──────────────────
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

    def generate_copy(self, topic: str, script: list, lang: str = "es", mode: str = "auto") -> dict:
        label = "Generando copy para redes sociales" if lang == "es" else "Generating social media copy"
        print(f"✍️ {label}...")
        hook = script[0]['text'] if script else ""
        last = script[-1]['text'] if script else ""

        # Hashtag pools para TikTok: #fyp + #viral fijos + 3 del nicho = 5 exactos
        # Para Facebook/YouTube se usan solo los 3 del nicho (sin fyp/viral)
        _ht = {
            "viral":      ("#HistoriaOscura #HechosImpactantes #DarkHistory",
                           "#DarkHistory #MysteryFacts #DidYouKnow"),
            "testimonio": ("#Misterio #TerrorReal #HistoriaOculta",
                           "#Mystery #Horror #TrueStory"),
            "libro":      ("#ResumenDeLibro #Lectura #DesarrolloPersonal",
                           "#BookSummary #SelfImprovement #LearnSomethingNew"),
            "empleo":     ("#OfertaDeEmpleo #BuscandoEmpleo #OportunidadLaboral",
                           "#JobOffer #NowHiring #JobOpportunity"),
            "guion":      ("#NoticiasVirales #LoCurioso #SabiaQue",
                           "#ViralNews #DidYouKnow #InterestingFacts"),
        }
        _niche_es, _niche_en = _ht.get(mode, ("#HechosCuriosos #CienciaYMisterio #DatosImpactantes",
                                               "#DidYouKnow #MindBlowing #FunFacts"))
        # TikTok: siempre #fyp #viral + 3 del nicho (total 5)
        hashtags_tiktok_es = f"#fyp #viral {_niche_es}"
        hashtags_tiktok_en = f"#fyp #viral {_niche_en}"
        # Facebook / YouTube: solo los 3 del nicho
        hashtags_es = _niche_es
        hashtags_en = _niche_en

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
- LÍNEA 3: CTA — pregunta directa que invite a comentar (ej: "¿Lo sabías? Comenta abajo 👇").
- HASHTAGS: Usa EXACTAMENTE estos (ya optimizados para el nicho): {hashtags_tiktok_es}

### 4. CAPTION DE FACEBOOK REELS:
- LÍNEA 1: afirmación impactante con la palabra clave principal (sin preguntas).
- LÍNEA 2: 1 oración conversacional de contexto.
- LÍNEA 3: CTA — pregunta que invite a comentar (ej: "¿Tú lo sabías? Comenta SÍ o NO").
- HASHTAGS: Usa 3 de estos (ya optimizados): {hashtags_es}

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
- LINE 3: CTA — direct question inviting engagement (e.g. "Did you know this? Comment below 👇").
- HASHTAGS: Use EXACTLY these (already optimized for the niche): {hashtags_tiktok_en}

### 4. FACEBOOK REELS CAPTION:
- LINE 1: strongest hook — shocking statement with main keyword (no questions).
- LINE 2: 1 natural conversational sentence adding context.
- LINE 3: CTA — question inviting comment (e.g. "Did you know? Comment YES or NO").
- HASHTAGS: Use 3 of these (already optimized): {hashtags_en}

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

    # ------------------------------------------------------------------
    # MININOVELA METHODS
    # ------------------------------------------------------------------

    def generate_miniseries_bible(self, theme: str, lang: str = "es") -> dict:
        """Generate the creative bible (story foundation) for a mini-series."""
        if lang == "es":
            prompt = f"""Eres el director creativo de una mini serie viral para YouTube Shorts en español latino.

TEMA DEL USUARIO: "{theme}"

TAREA: Crea la biblia creativa completa para una mini historia de 8 escenas (~60-90 segundos).

REGLAS:
- El tema del usuario es el punto de partida. Desarrolla una historia original pero fiel al tema.
- 2-3 personajes máximo (más es confuso en 60 segundos).
- Escenario concreto y específico (no vago).
- Descripción física de personajes OPTIMIZADA para prompts de video IA (en inglés, detallada).
- Arco narrativo completo: setup → conflicto → clímax → resolución.
- Tono que maximice retención: drama, giro inesperado, emoción fuerte.
- Idioma de la narración: español latino neutro.
- Las descripciones físicas de personajes DEBEN estar en INGLÉS (para los prompts de video IA).

FORMATO DE SALIDA (JSON estricto, sin markdown):
{{
  "title": "título impactante en español",
  "genre": "thriller | drama | romance | comedia | suspenso | horror",
  "setting": "descripción concreta del lugar y época (ej: mansión colonial, Santo Domingo, noche de tormenta, 2024)",
  "setting_visual": "english visual description of the setting for AI video prompts",
  "characters": [
    {{
      "name": "Nombre del personaje",
      "role": "protagonist | antagonist | supporting",
      "age": 35,
      "physical": "detailed english description for AI video: Hispanic female, 35 years old, long dark curly hair, red dress, intense brown eyes, elegant posture",
      "personality": "descripción breve en español de su personalidad y motivación"
    }}
  ],
  "arc": {{
    "setup": "situación inicial en 1-2 oraciones",
    "conflict": "el conflicto principal en 1-2 oraciones",
    "climax": "el momento de máxima tensión en 1-2 oraciones",
    "resolution": "cómo termina en 1-2 oraciones"
  }},
  "narrator_style": "tercera persona omnisciente, tono dramático y urgente"
}}"""
        else:
            prompt = f"""You are the creative director of a viral mini-series for YouTube Shorts.

USER THEME: "{theme}"

TASK: Create the complete creative bible for an 8-scene mini-story (~60-90 seconds).

RULES:
- The user's theme is the starting point. Develop an original story faithful to the theme.
- Maximum 2-3 characters (more is confusing in 60 seconds).
- Concrete and specific setting (not vague).
- Character physical descriptions OPTIMIZED for AI video prompts (in English, detailed).
- Complete narrative arc: setup → conflict → climax → resolution.
- Tone that maximizes retention: drama, unexpected twist, strong emotion.
- Narration language: English.
- Character physical descriptions MUST be in ENGLISH (for AI video prompts).

OUTPUT FORMAT (strict JSON, no markdown):
{{
  "title": "impactful title in English",
  "genre": "thriller | drama | romance | comedy | suspense | horror",
  "setting": "concrete description of place and era (e.g., colonial mansion, New York, stormy night, 2024)",
  "setting_visual": "english visual description of the setting for AI video prompts",
  "characters": [
    {{
      "name": "Character Name",
      "role": "protagonist | antagonist | supporting",
      "age": 35,
      "physical": "detailed english description for AI video: Hispanic female, 35 years old, long dark curly hair, red dress, intense brown eyes, elegant posture",
      "personality": "brief description of their personality and motivation"
    }}
  ],
  "arc": {{
    "setup": "initial situation in 1-2 sentences",
    "conflict": "the main conflict in 1-2 sentences",
    "climax": "the moment of maximum tension in 1-2 sentences",
    "resolution": "how it ends in 1-2 sentences"
  }},
  "narrator_style": "third person omniscient, dramatic and urgent tone"
}}"""

        raw = self._generate(prompt)
        clean = raw.replace('```json', '').replace('```', '').strip()
        try:
            import json as _j
            result = _j.loads(clean)
        except Exception:
            result = {
                "title": theme,
                "genre": "drama",
                "setting": "",
                "setting_visual": "",
                "characters": [],
                "arc": {
                    "setup": "",
                    "conflict": "",
                    "climax": "",
                    "resolution": "",
                },
                "narrator_style": "tercera persona omnisciente, tono dramático y urgente",
            }

        print(f"🎬 [Mininovela] Biblia creativa generada: {result.get('title', 'Sin título')}")
        return result

    def generate_miniseries_script(self, bible: dict, lang: str = "es", num_scenes: int = 8) -> list:
        """Generate the scene-by-scene script for the mini-series using its bible."""
        title = bible.get("title", "")
        genre = bible.get("genre", "")
        setting = bible.get("setting", "")
        setting_visual = bible.get("setting_visual", setting)
        arc = bible.get("arc", {})

        char_list = "\n".join(
            f"- {c['name']} ({c['role']}): {c['physical']} | Personalidad: {c['personality']}"
            for c in bible.get("characters", [])
        )

        if lang == "es":
            prompt = f"""Eres el guionista de la mini serie "{title}" ({genre}).

BIBLIA DE LA HISTORIA:
Escenario: {setting}
Descripción visual del escenario: {setting_visual}

PERSONAJES:
{char_list}

ARCO NARRATIVO:
- Setup: {arc.get('setup', '')}
- Conflicto: {arc.get('conflict', '')}
- Clímax: {arc.get('climax', '')}
- Resolución: {arc.get('resolution', '')}

TAREA: Escribe exactamente {num_scenes} escenas para YouTube Shorts.

REGLAS DE NARRACIÓN:
- Idioma: español latino neutro, 3ra persona.
- Cada "text" es la NARRACIÓN en voz en off (lo que dice el narrador). Máximo 15 palabras.
- Sin diálogos en el "text" — solo narración descriptiva y dramática.
- Cada escena: una sola idea poderosa. Sin relleno.
- Flujo: Escena 1 (gancho explosivo) → Escenas 2-3 (setup y personajes) → Escenas 4-6 (conflicto escalando) → Escena 7 (clímax) → Escena 8 (resolución o giro final).

REGLAS DE VIDEO (MUY IMPORTANTE para IA):
- "visual_1": término de búsqueda EN INGLÉS (Pexels fallback), 3-4 palabras.
- "visual_2": segundo término EN INGLÉS, 3-4 palabras.
- "video_prompt": prompt COMPLETO en INGLÉS para generación de video IA.
  FORMATO del video_prompt: "[Acción visual]. [Personajes presentes con descripción física completa si hay]. [Escenario visual]. [Atmósfera/iluminación]. Cinematic, 9:16 vertical, no text overlays."
  CRÍTICO: Si hay personajes en la escena, SIEMPRE incluye su descripción física completa del personaje de la biblia.
- "characters_in_scene": array con nombres de personajes presentes (puede ser vacío []).
- "mood": energetic | dramatic | mysterious | calm | inspiring | professional | exciting

ESTRUCTURA OBLIGATORIA:
- Escena 1 — GANCHO: La imagen o situación más impactante de la historia. Hook visual puro.
- Escenas 2-3 — INTRODUCCIÓN: Presenta el escenario y los personajes clave.
- Escenas 4-6 — DESARROLLO Y CONFLICTO: La situación escala, tensión crece.
- Escena 7 — CLÍMAX: El momento de máxima tensión o el giro.
- Escena 8 — RESOLUCIÓN / GANCHO FINAL: Cierre impactante o pregunta que enganche.

FORMATO DE SALIDA (JSON estricto, sin markdown, exactamente {num_scenes} elementos):
[
  {{
    "id": 1,
    "text": "narración aquí, máximo 15 palabras",
    "visual_1": "english pexels search term",
    "visual_2": "english pexels search term 2",
    "video_prompt": "Complete english AI video generation prompt with character descriptions if present. Setting description. Atmosphere. Cinematic, 9:16 vertical, no text.",
    "characters_in_scene": ["Nombre1"],
    "mood": "dramatic"
  }}
]"""
        else:
            prompt = f"""You are the screenwriter for the mini-series "{title}" ({genre}).

STORY BIBLE:
Setting: {setting}
Visual setting description: {setting_visual}

CHARACTERS:
{char_list}

NARRATIVE ARC:
- Setup: {arc.get('setup', '')}
- Conflict: {arc.get('conflict', '')}
- Climax: {arc.get('climax', '')}
- Resolution: {arc.get('resolution', '')}

TASK: Write exactly {num_scenes} scenes for YouTube Shorts.

NARRATION RULES:
- Language: English, third person.
- Each "text" is the VOICE-OVER NARRATION (what the narrator says). Maximum 15 words.
- No dialogue in "text" — only descriptive and dramatic narration.
- Each scene: one powerful idea. No filler.
- Flow: Scene 1 (explosive hook) → Scenes 2-3 (setup and characters) → Scenes 4-6 (escalating conflict) → Scene 7 (climax) → Scene 8 (resolution or final twist).

VIDEO RULES (VERY IMPORTANT for AI):
- "visual_1": English search term (Pexels fallback), 3-4 words.
- "visual_2": second English term, 3-4 words.
- "video_prompt": COMPLETE English prompt for AI video generation.
  FORMAT: "[Visual action]. [Characters present with full physical description if any]. [Visual setting]. [Atmosphere/lighting]. Cinematic, 9:16 vertical, no text overlays."
  CRITICAL: If characters are in the scene, ALWAYS include their full physical description from the bible.
- "characters_in_scene": array with names of characters present (can be empty []).
- "mood": energetic | dramatic | mysterious | calm | inspiring | professional | exciting

MANDATORY STRUCTURE:
- Scene 1 — HOOK: The most impactful image or situation of the story. Pure visual hook.
- Scenes 2-3 — INTRODUCTION: Introduce the setting and key characters.
- Scenes 4-6 — DEVELOPMENT & CONFLICT: The situation escalates, tension grows.
- Scene 7 — CLIMAX: The moment of maximum tension or the twist.
- Scene 8 — RESOLUTION / FINAL HOOK: Impactful close or engaging question.

OUTPUT FORMAT (strict JSON, no markdown, exactly {num_scenes} elements):
[
  {{
    "id": 1,
    "text": "narration here, maximum 15 words",
    "visual_1": "english pexels search term",
    "visual_2": "english pexels search term 2",
    "video_prompt": "Complete english AI video generation prompt with character descriptions if present. Setting description. Atmosphere. Cinematic, 9:16 vertical, no text.",
    "characters_in_scene": ["Character1"],
    "mood": "dramatic"
  }}
]"""

        raw = self._generate(prompt)
        clean = raw.replace('```json', '').replace('```', '').strip()
        try:
            import json as _j
            scenes = _j.loads(clean)
            if not isinstance(scenes, list):
                raise ValueError("Response is not a JSON array")
        except Exception:
            # Fallback: build minimal scenes from the arc
            arc_texts = [
                arc.get("setup", ""),
                arc.get("conflict", ""),
                arc.get("climax", ""),
                arc.get("resolution", ""),
            ]
            scenes = []
            for i in range(num_scenes):
                arc_text = arc_texts[min(i, len(arc_texts) - 1)] if arc_texts else ""
                scenes.append({
                    "id": i + 1,
                    "text": arc_text if arc_text else f"Scene {i + 1}",
                    "visual_1": "cinematic drama",
                    "visual_2": "dramatic scene",
                    "video_prompt": f"{setting_visual}. Cinematic, 9:16 vertical, no text.",
                    "characters_in_scene": [],
                    "mood": "dramatic",
                })

        # Sanitize text, fill missing fields, cap at num_scenes
        default_mood = "dramatic"
        sanitized = []
        for scene in scenes[:num_scenes]:
            if not isinstance(scene, dict):
                continue
            scene["text"] = self._sanitize(scene.get("text", ""))
            scene.setdefault("id", len(sanitized) + 1)
            scene.setdefault("visual_1", "cinematic drama")
            scene.setdefault("visual_2", "dramatic scene")
            scene.setdefault("video_prompt", f"{setting_visual}. Cinematic, 9:16 vertical, no text.")
            scene.setdefault("characters_in_scene", [])
            scene.setdefault("mood", default_mood)
            sanitized.append(scene)

        print(f"✅ [Mininovela] {len(sanitized)} escenas generadas para \"{title}\"")
        return sanitized


if __name__ == "__main__":
    brain = ContentBrain()
    topic = brain.get_trending_topic(lang="es")
    script = brain.generate_script(topic, lang="es")
    with open("script.json", "w", encoding="utf-8") as f:
        json.dump(script, f, indent=4, ensure_ascii=False)
        print("✅ Script saved to script.json")
