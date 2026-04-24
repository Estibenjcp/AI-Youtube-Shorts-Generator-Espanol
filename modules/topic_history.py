"""
Persistent topic history — prevents the LLM from repeating already-used topics.
Stores history in assets/used_topics.json (survives server restarts on Streamlit Cloud).
"""
import json
import os
from datetime import datetime

_PATH       = os.path.join(os.getcwd(), "assets", "used_topics.json")
_MAX_STORED = 2000   # keep last N entries on disk
_MAX_TO_LLM = 150    # max topics injected into a single LLM prompt (token budget)


# ── Internal helpers ──────────────────────────────────────────────────────────

def _load() -> list:
    try:
        if os.path.exists(_PATH):
            with open(_PATH, 'r', encoding='utf-8') as f:
                return json.load(f).get("topics", [])
    except Exception:
        pass
    return []


def _save(topics: list):
    os.makedirs(os.path.dirname(_PATH), exist_ok=True)
    topics = topics[-_MAX_STORED:]
    try:
        with open(_PATH, 'w', encoding='utf-8') as f:
            json.dump({"topics": topics}, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


# ── Public API ────────────────────────────────────────────────────────────────

def add_topic(topic: str, mode: str = "", lang: str = "es", category: str = ""):
    """Register a topic as used after a successful generation."""
    if not topic or not topic.strip():
        return
    topics = _load()
    topics.append({
        "topic":     topic.strip(),
        "mode":      mode,
        "lang":      lang,
        "category":  category,
        "timestamp": datetime.now().isoformat(),
    })
    _save(topics)


def get_used_topics(lang: str = None) -> list:
    """Return list of used topic strings, optionally filtered by lang."""
    topics = _load()
    if lang:
        topics = [t for t in topics if t.get("lang", "") == lang]
    return [t["topic"] for t in topics]


def topics_for_prompt(lang: str = None) -> list:
    """Return the most-recent topics suitable for injecting into an LLM prompt.
    Most recent first, capped at _MAX_TO_LLM to stay within token budget."""
    return list(reversed(get_used_topics(lang)))[:_MAX_TO_LLM]


def get_stats() -> dict:
    """Return stats for display in the UI."""
    topics = _load()
    return {
        "total": len(topics),
        "es":    sum(1 for t in topics if t.get("lang") == "es"),
        "en":    sum(1 for t in topics if t.get("lang") == "en"),
    }


def clear_history(lang: str = None):
    """Clear all history, or only for a specific language."""
    if lang is None:
        _save([])
    else:
        topics = _load()
        _save([t for t in topics if t.get("lang", "") != lang])
