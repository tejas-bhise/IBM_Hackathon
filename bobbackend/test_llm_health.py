"""
LLM Feature Test — asks real project questions to Groq + Gemini
Run: python3 test_llm_features.py
"""
import os
import time
import json
from dotenv import load_dotenv

load_dotenv()

GROQ_MODEL   = "llama-3.3-70b-versatile"
GEMINI_MODEL = "models/gemini-2.5-flash-lite"

# ── Clients ───────────────────────────────────────────────────────────────────

def get_groq():
    from groq import Groq
    return Groq(api_key=os.getenv("GROQ_API_KEY"))

def get_gemini():
    from google import genai
    return genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def ask_groq(client, prompt: str, max_tokens=500) -> tuple:
    start = time.time()
    resp  = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens,
        temperature=0.1,
    )
    return resp.choices[0].message.content.strip(), round((time.time() - start) * 1000)

def ask_gemini(client, prompt: str) -> tuple:
    start = time.time()
    resp  = client.models.generate_content(model=GEMINI_MODEL, contents=prompt)
    return resp.text.strip(), round((time.time() - start) * 1000)


# ── Feature Tests ─────────────────────────────────────────────────────────────

FEATURE_TESTS = [

    # ── TEST 1: Security Scanner (JSON output) ────────────────────────────────
    {
        "name": "🔍 Security Scanner — SQL Injection Detection",
        "prompt": """Analyze this code finding for a real security vulnerability.

[1] File: routes/users.py | Type: SQL_INJECTION
Code:
    user_id = request.args.get('id')
    query = "SELECT * FROM users WHERE id = " + user_id
    db.execute(query)

Return a JSON object:
{
  "confirmed": true or false,
  "severity": "CRITICAL|HIGH|MEDIUM|LOW",
  "explanation": "one sentence",
  "fix_suggestion": "concrete fix",
  "before_code": "bad code",
  "after_code": "fixed code"
}
Return ONLY the JSON. No markdown.""",
        "expect": "confirmed",
        "check": lambda r: '"confirmed"' in r and '"severity"' in r,
    },

    # ── TEST 2: Summarizer (project understanding) ────────────────────────────
    {
        "name": "🧠 Summarizer — Project Type Detection",
        "prompt": """Analyze this codebase structure and return a JSON summary.

Files detected:
- main.py (FastAPI app, 12 routes)
- services/scanner.py (regex + AI security scanner)
- services/embedder.py (SentenceTransformer, 2309 chunks)
- services/pipeline.py (orchestrates scanner, embedder, summarizer)
- routes/upload.py, analysis.py, chat.py
- db/mongo.py (MongoDB)
- models/schemas.py (Pydantic)

Return JSON:
{
  "project_type": "...",
  "description": "one sentence what this project does",
  "tech_stack": ["list", "of", "tech"],
  "architecture_type": "monolith|microservice|serverless",
  "entry_point": "filename"
}
Return ONLY the JSON. No markdown.""",
        "expect": "project_type",
        "check": lambda r: '"project_type"' in r and '"tech_stack"' in r,
    },

    # ── TEST 3: Chat Engine (conversational) ──────────────────────────────────
    {
        "name": "💬 Chat Engine — Codebase Q&A",
        "prompt": """You are an AI assistant for a codebase called "AI Project Intelligence Platform".

Project context:
- FastAPI backend with MongoDB
- Scans code for PII, SQL injection, hardcoded secrets
- Builds semantic search index using SentenceTransformer
- Has chat endpoint for Q&A about the codebase

User question: "Where is authentication handled in this project?"

Answer in 2-3 sentences based on the context. Be specific and technical.""",
        "expect": "auth",
        "check": lambda r: len(r) > 50,
    },
]


# ── Runner ────────────────────────────────────────────────────────────────────

def run_test_on_model(test: dict, model_name: str, ask_fn) -> dict:
    result = {"passed": False, "latency_ms": None, "response": None, "error": None}
    try:
        raw, ms = ask_fn(test["prompt"])
        result["latency_ms"] = ms
        result["response"]   = raw

        # Try to parse JSON if expected
        if test.get("check"):
            result["passed"] = test["check"](raw)
        else:
            result["passed"] = len(raw) > 10

        # Try JSON parse for scanner/summarizer tests
        if test["name"].startswith("🔍") or test["name"].startswith("🧠"):
            try:
                start = raw.find("{")
                end   = raw.rfind("}") + 1
                if start != -1 and end > 0:
                    parsed = json.loads(raw[start:end])
                    result["parsed"] = parsed
            except Exception:
                result["parsed"] = None

    except Exception as e:
        result["error"] = str(e)
    return result


def print_result(test_name: str, model: str, result: dict):
    status = "✅ PASS" if result["passed"] else ("❌ FAIL" if not result["error"] else "💥 ERROR")
    ms     = f"{result['latency_ms']}ms" if result["latency_ms"] else "—"
    print(f"\n  [{model}] {status} | {ms}")

    if result["error"]:
        print(f"    Error: {result['error']}")
        return

    # Show parsed JSON for scanner/summarizer
    if result.get("parsed"):
        p = result["parsed"]
        for k, v in p.items():
            val = str(v)[:80] + ("..." if len(str(v)) > 80 else "")
            print(f"    {k}: {val}")
    else:
        # Show first 200 chars of raw response
        preview = result["response"][:200].replace("\n", " ")
        print(f"    Response: {preview}{'...' if len(result['response']) > 200 else ''}")


def main():
    print("\n" + "="*60)
    print("  LLM FEATURE TEST — GROQ vs GEMINI")
    print(f"  Groq:   {GROQ_MODEL}")
    print(f"  Gemini: {GEMINI_MODEL}")
    print("="*60)

    try:
        groq_client   = get_groq()
        groq_ask      = lambda p: ask_groq(groq_client, p)
        groq_online   = True
    except Exception as e:
        print(f"\n❌ Groq client init failed: {e}")
        groq_online = False

    try:
        gemini_client = get_gemini()
        gemini_ask    = lambda p: ask_gemini(gemini_client, p)
        gemini_online = True
    except Exception as e:
        print(f"\n❌ Gemini client init failed: {e}")
        gemini_online = False

    groq_score = gemini_score = 0
    total      = len(FEATURE_TESTS)

    for i, test in enumerate(FEATURE_TESTS, 1):
        print(f"\n{'─'*60}")
        print(f"TEST {i}/{total}: {test['name']}")
        print(f"{'─'*60}")

        if groq_online:
            r = run_test_on_model(test, "Groq  ", groq_ask)
            print_result(test["name"], "Groq  ", r)
            if r["passed"]: groq_score += 1
        else:
            print("  [Groq  ] SKIPPED — offline")

        if gemini_online:
            r = run_test_on_model(test, "Gemini", gemini_ask)
            print_result(test["name"], "Gemini", r)
            if r["passed"]: gemini_score += 1
        else:
            print("  [Gemini] SKIPPED — offline")

    print(f"\n{'='*60}")
    print(f"  RESULTS")
    print(f"{'='*60}")
    print(f"  Groq   passed: {groq_score}/{total}")
    print(f"  Gemini passed: {gemini_score}/{total}")

    if groq_score == total and gemini_score == total:
        print("\n  🚀 Both models fully operational — pipeline is rock solid!")
    elif groq_score == total:
        print("\n  ✅ Groq primary path solid | ⚠️  Check Gemini fallback")
    elif gemini_score == total:
        print("\n  ⚠️  Groq has issues | ✅ Gemini fallback solid")
    else:
        print("\n  🔴 Issues detected — check errors above")
    print()


if __name__ == "__main__":
    main()