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


def is_duplicate(topic: str, lang: str = None, threshold: float = 0.68) -> bool:
    """Check if a topic is too similar to any already-used topic.
    Uses SequenceMatcher ratio (pure Python, zero tokens).
    threshold=0.68 catches near-identical titles while allowing related-but-distinct topics."""
    from difflib import SequenceMatcher
    if not topic or not topic.strip():
        return False
    topic_lower = topic.lower().strip()
    for used in get_used_topics(lang):
        ratio = SequenceMatcher(None, topic_lower, used.lower().strip()).ratio()
        if ratio >= threshold:
            return True
    return False


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
