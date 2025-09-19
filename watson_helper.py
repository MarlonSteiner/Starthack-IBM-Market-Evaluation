# watson_helper.py
# ---------------------------------------------------------------------
# IBM watsonx.ai helper: lightweight, fast, and hackathon-friendly.
# - Uses ModelInference (no deprecation warnings)
# - Separate models for classify vs summarize (override via env)
# - Small max_new_tokens for speed; greedy decoding for determinism
# - Model instance cache (avoid re-init on every call)
# - Safe fallbacks: returns "" on any failure
# ---------------------------------------------------------------------

from __future__ import annotations
import os
from typing import Optional, Dict

try:
    from ibm_watsonx_ai import Credentials
    from ibm_watsonx_ai.foundation_models import ModelInference
except Exception as e:  # SDK not installed or import problem
    Credentials = None  # type: ignore
    ModelInference = None  # type: ignore
    _IMPORT_ERR = e
else:
    _IMPORT_ERR = None

# ---- Environment (set these in your shell; do NOT hard-code secrets) ----
WATSONX_API_KEY    = os.getenv("WATSONX_API_KEY", "")
WATSONX_BASE_URL   = os.getenv("WATSONX_BASE_URL", "https://us-south.ml.cloud.ibm.com")

# Use ONE of these contexts:
WATSONX_PROJECT_ID = os.getenv("WATSONX_PROJECT_ID", "")  # for ad-hoc foundation inference
WATSONX_SPACE_ID   = os.getenv("WATSONX_SPACE_ID", "")    # if calling a deployed model in a Space

# Model choices (can be overridden per environment)
# Suggested defaults for speed/quality tradeoff:
DEFAULT_CLASSIFY_MODEL  = "ibm/granite-3-2b-instruct"
DEFAULT_SUMMARIZE_MODEL = "ibm/granite-3-8b-instruct"

CLASSIFY_MODEL_ID  = os.getenv("WATSONX_MODEL_ID_CLASSIFY",  DEFAULT_CLASSIFY_MODEL)
SUMMARIZE_MODEL_ID = os.getenv("WATSONX_MODEL_ID_SUMMARIZE", DEFAULT_SUMMARIZE_MODEL)

# Generation params (keep small for snappy UX)
CLASSIFY_PARAMS  = {"decoding_method": "greedy", "max_new_tokens": 64, "temperature": 0.1}
SUMMARIZE_PARAMS = {"decoding_method": "greedy", "max_new_tokens": 96, "temperature": 0.2}

# Internal cache
_models: Dict[str, "ModelInference"] = {}
_last_error: Optional[str] = None


def _ctx_ok() -> bool:
    """True if we have enough env to initialize the SDK context."""
    if _IMPORT_ERR is not None:
        return False
    if not (WATSONX_API_KEY and WATSONX_BASE_URL):
        return False
    # require exactly one context: project OR space
    if bool(WATSONX_PROJECT_ID) == bool(WATSONX_SPACE_ID):
        # either both set or both empty → invalid
        return False
    return True


def _get_model(model_id: str, *, for_classify: bool = False) -> Optional["ModelInference"]:
    """
    Lazily initialize and cache a ModelInference for a given model_id.
    Uses PROJECT context by default; falls back to SPACE if provided.
    """
    global _last_error
    if not _ctx_ok():
        _last_error = (
            "Missing/invalid environment. Need WATSONX_API_KEY, WATSONX_BASE_URL, and exactly "
            "one of WATSONX_PROJECT_ID or WATSONX_SPACE_ID set."
        )
        return None

    if model_id in _models:
        return _models[model_id]

    try:
        creds = Credentials(api_key=WATSONX_API_KEY, url=WATSONX_BASE_URL)
        params = CLASSIFY_PARAMS if for_classify else SUMMARIZE_PARAMS

        kwargs = dict(
            model_id=model_id,
            credentials=creds,
            params=params,
        )
        if WATSONX_PROJECT_ID:
            kwargs["project_id"] = WATSONX_PROJECT_ID
        else:
            kwargs["space_id"] = WATSONX_SPACE_ID  # using a Space / deployment context

        m = ModelInference(**kwargs)  # type: ignore[arg-type]
        _models[model_id] = m
        return m
    except Exception as e:
        _last_error = f"Model init failed for '{model_id}': {type(e).__name__}({e})"
        return None


def _wx_gen(prompt: str, *, model_key: str = "summarize", model_id: Optional[str] = None) -> str:
    """
    Generate text with watsonx.ai.
    - model_key: "classify" or "summarize" to pick the default model
    - model_id: explicit override (takes precedence over model_key)
    Returns "" on failure (your pipeline should have safe fallbacks).
    """
    global _last_error

    # choose model id
    mid = model_id
    if not mid:
        mid = CLASSIFY_MODEL_ID if model_key == "classify" else SUMMARIZE_MODEL_ID

    # fetch cached model or init a new one
    m = _get_model(mid, for_classify=(model_key == "classify"))
    if m is None:
        return ""

    # call generate
    try:
        # ModelInference API
        return m.generate_text(prompt=prompt) or ""
    except Exception as e:
        _last_error = f"generate_text failed: {type(e).__name__}({e})"
        return ""


def wx_healthcheck() -> dict:
    """Quick diagnostics for your CLI."""
    # try to init both defaults so we can report properly
    cm = _get_model(CLASSIFY_MODEL_ID, for_classify=True)
    sm = _get_model(SUMMARIZE_MODEL_ID, for_classify=False)
    return {
        "sdk_import_ok": _IMPORT_ERR is None,
        "base_url": WATSONX_BASE_URL,
        "project_id_set": bool(WATSONX_PROJECT_ID),
        "space_id_set": bool(WATSONX_SPACE_ID),
        "classify_model_id": CLASSIFY_MODEL_ID,
        "summarize_model_id": SUMMARIZE_MODEL_ID,
        "classify_model_inited": cm is not None,
        "summarize_model_inited": sm is not None,
        "last_error": _last_error,
    }


# ---------------- Optional helpers ----------------

def wx_set_params(*, classify_params: dict | None = None, summarize_params: dict | None = None) -> None:
    """
    Update generation parameters at runtime (e.g., to tweak token caps without restarting).
    Clears model cache so new params stick.
    """
    global CLASSIFY_PARAMS, SUMMARIZE_PARAMS, _models
    if classify_params:
        CLASSIFY_PARAMS = dict(CLASSIFY_PARAMS, **classify_params)
    if summarize_params:
        SUMMARIZE_PARAMS = dict(SUMMARIZE_PARAMS, **summarize_params)
    _models.clear()  # force re-init with new params


def wx_set_models(*, classify_model_id: Optional[str] = None, summarize_model_id: Optional[str] = None) -> None:
    """
    Swap default model IDs at runtime (handy for A/B testing).
    Clears model cache so new models load.
    """
    global CLASSIFY_MODEL_ID, SUMMARIZE_MODEL_ID, _models
    if classify_model_id:
        CLASSIFY_MODEL_ID = classify_model_id
    if summarize_model_id:
        SUMMARIZE_MODEL_ID = summarize_model_id
    _models.clear()
