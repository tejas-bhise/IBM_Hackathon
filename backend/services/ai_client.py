"""
AI Client — Gemini PRIMARY, Groq emergency fallback.
LLM calls are ONLY permitted for: chat
Hard limiter: MAX_CALLS_PER_RUN = 10 per pipeline run.
"""
import time
import asyncio
import logging
from typing import Optional, Any

from groq import AsyncGroq
import google.generativeai as genai

from config import get_settings

settings = get_settings()
logger   = logging.getLogger(__name__)

# ── Retry configuration ────────────────────────────────────────────────────────
MAX_RETRIES      = 2
INITIAL_BACKOFF  = 1.0
TIMEOUT_SECONDS  = 30.0

# ── HARD CALL LIMITER — resets per process lifecycle ──────────────────────────
MAX_CALLS_PER_RUN = 10
_current_calls    = 0

def _check_call_budget(task: str) -> bool:
    """Returns True if call is allowed. False if budget exceeded."""
    global _current_calls
    if _current_calls >= MAX_CALLS_PER_RUN:
        logger.warning(
            f"[LLM] ⛔ Call budget exhausted ({_current_calls}/{MAX_CALLS_PER_RUN}) "
            f"for task={task} → returning fallback"
        )
        return False
    return True

def _increment_call_counter(task: str) -> None:
    global _current_calls
    _current_calls += 1
    logger.info(f"[LLM] call #{_current_calls}/{MAX_CALLS_PER_RUN} for task={task}")

def reset_call_counter() -> None:
    """Call this at the start of each pipeline run to reset per-run budget."""
    global _current_calls
    _current_calls = 0
    logger.info("[LLM] Call counter reset for new pipeline run")

# ── Clients ────────────────────────────────────────────────────────────────────
_groq:          Optional[AsyncGroq] = None
# ✅ FIX: Use Any to prevent Pyright private export errors
_gemini_client: Optional[Any]       = None

if settings.GROQ_API_KEY:
    try:
        _groq = AsyncGroq(api_key=settings.GROQ_API_KEY)
        print("[ai_client] ✅ Groq client initialized")
    except Exception as e:
        print(f"[ai_client] ⚠️ Groq client failed: {e}")
        _groq = None
else:
    print("[ai_client] ⚠️ GROQ_API_KEY not set")

if settings.GEMINI_API_KEY:
    try:
        # ✅ FIX: Added type ignore for strict Pyright export checks
        genai.configure(api_key=settings.GEMINI_API_KEY) # type: ignore
        _gemini_client = genai.GenerativeModel( # type: ignore
            settings.GEMINI_MODEL.strip().replace("models/", "")
        )
        print("[ai_client] ✅ Gemini client initialized")
    except Exception as e:
        print(f"[ai_client] ⚠️ Gemini client failed: {e}")
        _gemini_client = None
else:
    print("[ai_client] ⚠️ GEMINI_API_KEY not set")

GROQ_MODEL   = settings.GROQ_MODEL.strip() if settings.GROQ_MODEL else ""
GEMINI_MODEL = settings.GEMINI_MODEL.strip().replace("models/", "") if settings.GEMINI_MODEL else ""

print(f"[ai_client] GROQ_MODEL={GROQ_MODEL} | GEMINI_MODEL={GEMINI_MODEL}")
print(f"[ai_client] groq={'OK' if _groq else 'NONE'} | gemini={'OK' if _gemini_client else 'NONE'}")

# ── Cooldown tracker ──────────────────────────────────────────────────────────
COOLDOWN_SECONDS   = 65.0
_last_rate_limited: dict[str, float] = {"groq": 0.0, "gemini": 0.0}

# ── STRICT Task → LLM routing ─────────────────────────────────────────────────
# ✅ ONLY chat uses LLM — everything else is rule-based (zero tokens)
TASK_ROUTING: dict[str, list[str]] = {
    "chat":       ["gemini", "groq"],   # ✅ ONLY permitted LLM task
    "scanner":    [],
    "summarizer": [],
    "memory":     [],
    "mock":       [],
    "workflow":   [],
}

# ── Token limits per task ─────────────────────────────────────────────────────
MAX_TOKENS: dict[str, int] = {
    "chat": 600,
}

# ── Prompt size hard caps ─────────────────────────────────────────────────────
MAX_PROMPT_CHARS: dict[str, int] = {
    "chat": 5_000,
}


# ── Helpers ────────────────────────────────────────────────────────────────────

def _is_available(provider: str) -> bool:
    return (time.time() - _last_rate_limited.get(provider, 0.0)) >= COOLDOWN_SECONDS

def _mark_rate_limited(provider: str) -> None:
    _last_rate_limited[provider] = time.time()
    logger.warning(f"⚠️ {provider.capitalize()} rate-limited → cooldown {int(COOLDOWN_SECONDS)}s")

def _is_rate_error(msg: str) -> bool:
    return any(x in msg for x in (
        "429", "rate_limit", "quota", "exhausted",
        "TPD", "TPM", "tokens per", "RESOURCE_EXHAUSTED",
    ))

def _is_unavailable_error(msg: str) -> bool:
    return any(x in msg.lower() for x in (
        "503", "unavailable", "overloaded", "service_unavailable",
    ))

def _truncate(prompt: str, task: str) -> str:
    limit = MAX_PROMPT_CHARS.get(task, 3_000)
    return (prompt[:limit] + "\n[...truncated]") if len(prompt) > limit else prompt


# ── Single-provider call wrappers ─────────────────────────────────────────────

async def _call_groq(prompt: str, max_tokens: int) -> str:
    if not _groq:
        raise ValueError("Groq client not initialized")
    resp = await asyncio.wait_for(
        _groq.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}], # type: ignore
            max_tokens=max_tokens,
            temperature=0.1,
        ),
        timeout=TIMEOUT_SECONDS,
    )
    result = resp.choices[0].message.content
    return result.strip() if result else ""

async def _call_gemini(prompt: str, max_tokens: int) -> str:
    if not _gemini_client:
        raise ValueError("Gemini client not initialized")
    resp = await asyncio.wait_for(
        _gemini_client.generate_content_async(
            prompt,
            generation_config={"max_output_tokens": max_tokens, "temperature": 0.1},
        ),
        timeout=TIMEOUT_SECONDS,
    )
    return resp.text.strip()

async def _call_groq_messages(messages: list[dict], max_tokens: int) -> str:
    if not _groq:
        raise ValueError("Groq client not initialized")
    resp = await asyncio.wait_for(
        _groq.chat.completions.create(
            model=GROQ_MODEL,
            messages=messages, # type: ignore
            max_tokens=max_tokens,
            temperature=0.2,
        ),
        timeout=TIMEOUT_SECONDS,
    )
    result = resp.choices[0].message.content
    return result.strip() if result else ""

async def _call_gemini_messages(messages: list[dict], max_tokens: int) -> str:
    if not _gemini_client:
        raise ValueError("Gemini client not initialized")
    combined = "\n\n".join(
        f"{'SYSTEM' if m['role'] == 'system' else m['role'].upper()}: {m['content']}"
        for m in messages
    )
    resp = await asyncio.wait_for(
        _gemini_client.generate_content_async(
            combined,
            generation_config={"max_output_tokens": max_tokens, "temperature": 0.2},
        ),
        timeout=TIMEOUT_SECONDS,
    )
    return resp.text.strip()


# ── Provider try-wrappers with retry + backoff ────────────────────────────────

async def _try_provider(provider: str, prompt: str, max_tokens: int) -> tuple[str | None, str]:
    if not _is_available(provider):
        remaining = int(COOLDOWN_SECONDS - (time.time() - _last_rate_limited[provider]))
        logger.info(f"[LLM] {provider} in cooldown ({remaining}s) — skipping")
        return None, provider
    if provider == "groq"   and not _groq:          return None, provider
    if provider == "gemini" and not _gemini_client:  return None, provider

    backoff = INITIAL_BACKOFF
    for attempt in range(MAX_RETRIES + 1):
        try:
            result = await (_call_groq(prompt, max_tokens) if provider == "groq"
                            else _call_gemini(prompt, max_tokens))
            return result, provider
        except asyncio.TimeoutError:
            if attempt < MAX_RETRIES:
                await asyncio.sleep(backoff); backoff *= 2; continue
            return None, provider
        except Exception as exc:
            msg = str(exc)
            if _is_rate_error(msg) or _is_unavailable_error(msg):
                if attempt < MAX_RETRIES:
                    await asyncio.sleep(backoff); backoff *= 2; continue
                _mark_rate_limited(provider)
            return None, provider

    return None, provider

async def _try_provider_messages(provider: str, messages: list[dict], max_tokens: int) -> tuple[str | None, str]:
    if not _is_available(provider):
        remaining = int(COOLDOWN_SECONDS - (time.time() - _last_rate_limited[provider]))
        logger.info(f"[LLM] {provider} in cooldown ({remaining}s) — skipping")
        return None, provider
    if provider == "groq"   and not _groq:          return None, provider
    if provider == "gemini" and not _gemini_client:  return None, provider

    backoff = INITIAL_BACKOFF
    for attempt in range(MAX_RETRIES + 1):
        try:
            result = await (_call_groq_messages(messages, max_tokens) if provider == "groq"
                            else _call_gemini_messages(messages, max_tokens))
            return result, provider
        except asyncio.TimeoutError:
            if attempt < MAX_RETRIES:
                await asyncio.sleep(backoff); backoff *= 2; continue
            return None, provider
        except Exception as exc:
            msg = str(exc)
            if _is_rate_error(msg) or _is_unavailable_error(msg):
                if attempt < MAX_RETRIES:
                    await asyncio.sleep(backoff); backoff *= 2; continue
                _mark_rate_limited(provider)
            return None, provider

    return None, provider


# ── Public API ────────────────────────────────────────────────────────────────

async def smart_llm_call(
    prompt: str, task: str = "default", max_tokens: int = 400
) -> tuple[str | None, str]:
    providers = TASK_ROUTING.get(task, [])
    if not providers:
        return None, "fallback"
    if not _check_call_budget(task):
        return None, "fallback"
    prompt = _truncate(prompt, task)
    _increment_call_counter(task)
    for provider in providers:
        text, used = await _try_provider(provider, prompt, max_tokens)
        if text is not None:
            return text, used
    return None, "fallback"

async def smart_llm_call_messages(
    messages: list[dict], task: str = "chat", max_tokens: int = 600
) -> tuple[str | None, str]:
    providers = TASK_ROUTING.get(task, [])
    if not providers:
        return None, "fallback"
    if not _check_call_budget(task):
        return None, "fallback"
    _increment_call_counter(task)
    for provider in providers:
        text, used = await _try_provider_messages(provider, messages, max_tokens)
        if text is not None:
            return text, used
    return None, "fallback"

def get_availability_status() -> dict:
    groq_ok    = (_groq is not None) and _is_available("groq")
    gemini_ok  = (_gemini_client is not None) and _is_available("gemini")
    groq_wait  = max(0, int(COOLDOWN_SECONDS - (time.time() - _last_rate_limited.get("groq", 0.0))))
    gemini_wait = max(0, int(COOLDOWN_SECONDS - (time.time() - _last_rate_limited.get("gemini", 0.0))))
    active     = "gemini" if gemini_ok else ("groq" if groq_ok else "fallback")
    return {
        "groq":          {"available": groq_ok,   "cooldown_remaining_s": groq_wait   if not groq_ok   else 0},
        "gemini":        {"available": gemini_ok, "cooldown_remaining_s": gemini_wait if not gemini_ok else 0},
        "any_available": groq_ok or gemini_ok,
        "active_model":  active,
        "calls_used":    _current_calls,
        "calls_budget":  MAX_CALLS_PER_RUN,
    }

GROQ_AVAILABLE   = True
GEMINI_AVAILABLE = True
AI_AVAILABLE     = True