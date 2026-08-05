import os
from dotenv import load_dotenv, set_key

ENV_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")

PROVIDER_DEFAULTS = {
    "gemini": {
        "label": "Google Gemini",
        "model": "gemini-2.0-flash-exp",
    },
    "openrouter": {
        "label": "OpenRouter",
        "model": "google/gemini-2.0-flash-lite-001",
    },
}


_dotenv_cargado = False


def get_secret(key: str, default: str = "") -> str:
    """Lee una clave del entorno y, si no esta, de st.secrets.

    En local los valores viven en .env; en Streamlit Cloud, en st.secrets. Sin
    esta funcion, cualquier clave leida solo con os.getenv queda vacia en el
    despliegue y la app pide credenciales que el usuario ya habia configurado.

    Carga el .env por su cuenta la primera vez: si dependiera de que alguien
    llamase antes a load_config(), devolveria vacio segun el orden de ejecucion.
    """
    global _dotenv_cargado
    if not _dotenv_cargado:
        try:
            load_dotenv(ENV_PATH)
        except Exception:
            pass
        _dotenv_cargado = True

    val = os.getenv(key, "")
    if val:
        return val
    try:
        import streamlit as st
        return st.secrets.get(key, default)
    except Exception:
        return default


def _streamlit_secrets() -> dict:
    """Lee st.secrets si estamos en Streamlit Cloud."""
    try:
        import streamlit as st
        return {
            "AI_PROVIDER":    st.secrets.get("AI_PROVIDER", ""),
            "AI_API_KEY":     st.secrets.get("AI_API_KEY", ""),
            "AI_MODEL":       st.secrets.get("AI_MODEL", ""),
            "PEXELS_API_KEY": st.secrets.get("PEXELS_API_KEY", ""),
        }
    except Exception:
        return {}


def load_config():
    load_dotenv(ENV_PATH)  # sin override=True para no pisar st.secrets
    env_cfg = {
        "AI_PROVIDER":    os.getenv("AI_PROVIDER", ""),
        "AI_API_KEY":     os.getenv("AI_API_KEY", ""),
        "AI_MODEL":       os.getenv("AI_MODEL", ""),
        "PEXELS_API_KEY": os.getenv("PEXELS_API_KEY", ""),
    }
    # Prioridad: .env local → st.secrets (Streamlit Cloud)
    st_cfg = _streamlit_secrets()
    return {k: env_cfg[k] or st_cfg.get(k, "") for k in env_cfg}


def _save(key, value):
    set_key(ENV_PATH, key, value)


def _mask(value):
    if not value:
        return "(not set)"
    return f"...{value[-6:]}" if len(value) > 6 else "***"


def run_setup():
    print()
    print("=" * 52)
    print("   ⚙️   AutoShorts AI — API Configuration")
    print("=" * 52)

    current = load_config()

    # ── 1. AI Provider ──────────────────────────────────
    print()
    print("📡  AI Provider")
    print("    [1] Google Gemini  (direct API)")
    print("    [2] OpenRouter     (supports many models)")
    current_provider = current["AI_PROVIDER"] or "gemini"
    current_label = PROVIDER_DEFAULTS.get(current_provider, {}).get("label", current_provider)
    print(f"    Current: {current_label}")

    choice = input("    Select provider (1/2, blank = keep): ").strip()
    if choice == "2":
        provider = "openrouter"
    elif choice == "1":
        provider = "gemini"
    else:
        provider = current_provider

    info = PROVIDER_DEFAULTS[provider]

    # ── 2. API Key ───────────────────────────────────────
    print()
    print(f"🔑  {info['label']} API Key")
    print(f"    Current: {_mask(current['AI_API_KEY'])}")
    api_key = input("    Enter API key (blank = keep current): ").strip()
    if not api_key:
        api_key = current["AI_API_KEY"]

    # ── 3. Model ─────────────────────────────────────────
    print()
    print("🤖  Model")
    print(f"    Default for {info['label']}: {info['model']}")
    current_model = current["AI_MODEL"] or info["model"]
    print(f"    Current: {current_model}")
    model = input("    Enter model name (blank = keep current): ").strip()
    if not model:
        model = current_model

    # ── 4. Pexels API Key ────────────────────────────────
    print()
    print("🎥  Pexels API Key")
    print(f"    Current: {_mask(current['PEXELS_API_KEY'])}")
    pexels_key = input("    Enter Pexels API key (blank = keep current): ").strip()
    if not pexels_key:
        pexels_key = current["PEXELS_API_KEY"]

    # ── Save ─────────────────────────────────────────────
    _save("AI_PROVIDER",   provider)
    _save("AI_API_KEY",    api_key)
    _save("AI_MODEL",      model)
    _save("PEXELS_API_KEY", pexels_key)

    print()
    print("✅  Configuration saved to .env")
    print("=" * 52)
    print()

    return load_config()


def check_config():
    """Returns True if all required keys are present."""
    cfg = load_config()
    return bool(cfg["AI_PROVIDER"] and cfg["AI_API_KEY"] and cfg["PEXELS_API_KEY"])


# Run as standalone: python -m modules.config
if __name__ == "__main__":
    run_setup()
