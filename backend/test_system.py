"""
test_system.py — Universal E2E + LLM health check
Run: python3 test_system.py
"""
import asyncio, httpx, time, os, json
from dotenv import load_dotenv

load_dotenv()

BASE_URL        = "http://127.0.0.1:8000/api"
TEST_GITHUB_URL = "https://github.com/tiangolo/fastapi"
GROQ_MODEL      = "llama-3.3-70b-versatile"
GEMINI_MODEL    = "models/gemini-2.5-flash-lite"

PASS = "✅"; FAIL = "❌"; WARN = "⚠️ "; INFO = "→"

results: list[dict] = []

def log(label: str, passed: bool, detail: str = ""):
    icon = PASS if passed else FAIL
    line = f"  {icon} {label}"
    if detail:
        line += f"  |  {detail}"
    print(line)
    results.append({"label": label, "passed": passed})

def section(title: str):
    print(f"\n{'═'*68}")
    print(f"  {title}")
    print(f"{'═'*68}")


# ══════════════════════════════════════════════════════════════════════
# PHASE 1 — LLM HEALTH  (direct API, no server needed)
# ══════════════════════════════════════════════════════════════════════

def llm_ask_groq(prompt: str, max_tokens=200) -> tuple[str, int]:
    from groq import Groq
    c     = Groq(api_key=os.getenv("GROQ_API_KEY"))
    start = time.time()
    r     = c.chat.completions.create(
        model=GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens, temperature=0.1,
    )
    return r.choices[0].message.content.strip(), round((time.time()-start)*1000)

def llm_ask_gemini(prompt: str) -> tuple[str, int]:
    from google import genai
    c     = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    start = time.time()
    r     = c.models.generate_content(model=GEMINI_MODEL, contents=prompt)
    return r.text.strip(), round((time.time()-start)*1000)

def phase_llm_health():
    section("PHASE 1 — LLM DIRECT HEALTH")

    # Groq
    try:
        res, ms = llm_ask_groq("Reply with exactly: GROQ_OK")
        ok = "GROQ_OK" in res
        log(f"Groq  [{GROQ_MODEL}]", ok, f"{ms}ms | reply='{res[:30]}'")
    except Exception as e:
        log("Groq  direct", False, str(e)[:80])

    # Gemini
    try:
        res, ms = llm_ask_gemini("Reply with exactly: GEMINI_OK")
        ok = "GEMINI_OK" in res
        log(f"Gemini [{GEMINI_MODEL}]", ok, f"{ms}ms | reply='{res[:30]}'")
    except Exception as e:
        log("Gemini direct", False, str(e)[:80])

    # Groq structured JSON
    try:
        raw, ms = llm_ask_groq(
            'Return ONLY JSON: {"confirmed":true,"severity":"CRITICAL",'
            '"fix":"use parameterized queries"}', max_tokens=100
        )
        parsed = json.loads(raw[raw.find("{"):raw.rfind("}")+1])
        ok = "confirmed" in parsed and "severity" in parsed
        log("Groq  JSON output", ok, f"{ms}ms | severity={parsed.get('severity')}")
    except Exception as e:
        log("Groq  JSON output", False, str(e)[:80])

    # Gemini structured JSON
    try:
        raw, ms = llm_ask_gemini(
            'Return ONLY JSON: {"project_type":"FastAPI Backend",'
            '"tech_stack":["Python","FastAPI"]}'
        )
        parsed = json.loads(raw[raw.find("{"):raw.rfind("}")+1])
        ok = "project_type" in parsed
        log("Gemini JSON output", ok, f"{ms}ms | type={parsed.get('project_type','?')[:30]}")
    except Exception as e:
        log("Gemini JSON output", False, str(e)[:80])


# ══════════════════════════════════════════════════════════════════════
# PHASE 2 — SERVER HEALTH
# ══════════════════════════════════════════════════════════════════════

async def phase_server_health(client: httpx.AsyncClient):
    section("PHASE 2 — SERVER HEALTH")

    # /health
    try:
        r = await client.get(f"{BASE_URL}/health")
        log("GET /health", r.status_code == 200, f"status={r.status_code}")
    except Exception as e:
        log("GET /health", False, str(e)[:80])
        return False

    # /system-status
    try:
        r  = await client.get(f"{BASE_URL}/system-status")
        d  = r.json()
        ok = r.status_code == 200 and "ai_available" in d
        log("GET /system-status", ok,
            f"ai={d.get('ai_available')} | model={d.get('active_model','?')} | db={d.get('database','?')}")
        if ok:
            svcs = d.get("services", {})
            for svc, mode in svcs.items():
                print(f"       {INFO} {svc:<12} → {mode}")
    except Exception as e:
        log("GET /system-status", False, str(e)[:80])

    return True


# ══════════════════════════════════════════════════════════════════════
# PHASE 3 — PIPELINE (upload → scan → summarize → embed → workflow)
# ══════════════════════════════════════════════════════════════════════

async def phase_pipeline(client: httpx.AsyncClient) -> str | None:
    section("PHASE 3 — PIPELINE  (uploads FastAPI repo, ~2–4 min)")

    # Upload
    try:
        r  = await client.post(f"{BASE_URL}/upload", data={"github_url": TEST_GITHUB_URL})
        d  = r.json()
        pid = d.get("project_id")
        log("POST /upload", r.status_code == 200 and bool(pid),
            f"project_id={pid} | files={d.get('total_files')}")
        if not pid:
            return None
    except Exception as e:
        log("POST /upload", False, str(e)[:80])
        return None

    # Poll status
    print(f"\n  {INFO} Polling pipeline  (max 6 min)...")
    last_pct  = -1
    last_step = ""
    s         = {}
    for attempt in range(90):
        try:
            r = await client.get(f"{BASE_URL}/status/{pid}")
            if r.status_code == 404:
                await asyncio.sleep(4); continue
            s    = r.json()
            pct  = s.get("percent", 0)
            step = s.get("current_step_name", "")
            if pct != last_pct or step != last_step:
                print(f"     [{pct:>3}%] {step}")
                last_pct, last_step = pct, step
            if s.get("status") == "completed" or pct >= 100:
                log("Pipeline completed", True, f"steps polled={attempt+1}")
                break
            if s.get("status") == "error":
                log("Pipeline completed", False, s.get("error","unknown"))
                return None
        except Exception as e:
            print(f"     poll error: {e}")
        await asyncio.sleep(4)
    else:
        log("Pipeline completed", False, "timeout after 6 min")
        return None

    return pid


# ══════════════════════════════════════════════════════════════════════
# PHASE 4 — ANALYSIS QUALITY
# ══════════════════════════════════════════════════════════════════════

async def phase_analysis(client: httpx.AsyncClient, pid: str):
    section("PHASE 4 — ANALYSIS QUALITY")
    try:
        r = await client.get(f"{BASE_URL}/analysis/{pid}")
        a = r.json()
    except Exception as e:
        log("GET /analysis", False, str(e)[:80]); return

    summary = a.get("summary", {})
    log("GET /analysis",          r.status_code == 200)
    log("Project type detected",  bool(summary.get("project_type")),
        summary.get("project_type", "—"))
    log("Tech stack detected",    bool(summary.get("tech_stack")),
        str(summary.get("tech_stack", [])[:4]))
    log("Security score present", summary.get("security_score") is not None,
        f"score={summary.get('security_score')}/100")

    issues = a.get("issues") or a.get("security_issues", [])
    log("Issues detected",        len(issues) > 0,
        f"{len(issues)} issues  "
        f"C:{summary.get('critical_count',0)} "
        f"H:{summary.get('high_count',0)} "
        f"M:{summary.get('medium_count',0)}")

    if issues:
        top = issues[0]
        sev  = top.get("severity") or top.get("type_label","?")
        file = top.get("file_path") or top.get("file","?")
        fix  = (top.get("fix_suggestion") or top.get("fix","N/A"))[:100]
        print(f"\n     Top issue  →  [{sev}]  {file}")
        print(f"     Fix        →  {fix}")


# ══════════════════════════════════════════════════════════════════════
# PHASE 5 — CHAT
# ══════════════════════════════════════════════════════════════════════

async def phase_chat(client: httpx.AsyncClient, pid: str):
    section("PHASE 5 — CHAT  (dev + pm + investor)")

    tests = [
        ("Where is authentication handled?",       "dev"),
        ("Which file defines the main application?","dev"),
        ("Is this project ready for production?",   "pm"),
        ("What is the investment risk level?",       "investor"),
    ]

    for question, role in tests:
        try:
            r = await client.post(f"{BASE_URL}/chat", json={
                "project_id": pid, "question": question, "role": role
            })
            d       = r.json()
            answer  = d.get("answer", "")
            sources = d.get("sources", [])
            mode    = d.get("mode", "?")
            grounded = len(sources) > 0
            log(f"Chat [{role:<8}] grounded",  grounded,
                f"mode={mode} | sources={len(sources)} | answer={answer[:80]}...")
            if not grounded:
                print(f"     {WARN} No sources — answer may be hallucinated")
        except Exception as e:
            log(f"Chat [{role}]", False, str(e)[:80])


# ══════════════════════════════════════════════════════════════════════
# PHASE 6 — WORKFLOW + ROLE VIEWS
# ══════════════════════════════════════════════════════════════════════

async def phase_workflow(client: httpx.AsyncClient, pid: str):
    section("PHASE 6 — WORKFLOW + ROLE VIEWS")

    try:
        r  = await client.get(f"{BASE_URL}/workflow/{pid}")
        wf = r.json()
        log("GET /workflow",   r.status_code == 200,
            f"stage={wf.get('stage')} | risk={wf.get('risk_level') or wf.get('risk')} "
            f"| action={wf.get('recommended_action')}")
    except Exception as e:
        log("GET /workflow", False, str(e)[:80])

    for role in ["dev", "pm", "investor"]:
        try:
            r    = await client.get(f"{BASE_URL}/workflow/{pid}/view/{role}")
            view = r.json().get("view", {})
            ok   = r.status_code == 200 and bool(view)

            if role == "dev":
                detail = f"blockers={len(view.get('blockers',[]))} | issues={len(view.get('issues_to_fix',[]))}"
            elif role == "pm":
                detail = f"status={view.get('project_status','?')[:50]} | delay={view.get('estimated_release_delay','?')}"
            else:
                detail = f"health={view.get('project_health_score')}/100 | signal={view.get('investment_signal','?')[:40]}"

            log(f"Workflow view [{role}]", ok, detail)
        except Exception as e:
            log(f"Workflow view [{role}]", False, str(e)[:80])


# ══════════════════════════════════════════════════════════════════════
# PHASE 7 — MOCK DATA
# ══════════════════════════════════════════════════════════════════════

async def phase_mock(client: httpx.AsyncClient, pid: str):
    section("PHASE 7 — MOCK DATA")
    try:
        r = await client.get(f"{BASE_URL}/mock/{pid}")
        m = r.json()
        emails = m.get("PII_EMAIL", [])
        users  = m.get("sample_users", [])
        pii    = m.get("total_pii_fields_found", 0)
        log("GET /mock",        r.status_code == 200)
        log("Mock emails exist", len(emails) > 0,  f"sample={emails[:2]}")
        log("Sample users exist",len(users)  > 0,  f"{len(users)} users generated")
        log("PII fields replaced",pii > 0,         f"{pii} fields replaced")
    except Exception as e:
        log("GET /mock", False, str(e)[:80])


# ══════════════════════════════════════════════════════════════════════
# FINAL SCORECARD
# ══════════════════════════════════════════════════════════════════════

def print_scorecard(pid: str | None):
    section("FINAL SCORECARD")
    passed = sum(1 for r in results if r["passed"])
    total  = len(results)
    pct    = int(passed / total * 100) if total else 0

    # group failures
    failed = [r["label"] for r in results if not r["passed"]]

    print(f"\n  Score  :  {passed}/{total}  ({pct}%)")

    if failed:
        print(f"\n  {FAIL} Failed checks:")
        for f in failed:
            print(f"       • {f}")
    else:
        print(f"\n  {PASS} All checks passed!")

    if pct == 100:
        print("\n  🚀 SYSTEM FULLY OPERATIONAL — ship it!")
    elif pct >= 80:
        print("\n  ✅ SYSTEM HEALTHY — minor issues above")
    elif pct >= 50:
        print(f"\n  {WARN} SYSTEM PARTIAL — check failures above")
    else:
        print("\n  🔴 SYSTEM DEGRADED — multiple failures, review logs")

    if pid:
        print(f"\n  Project ID  :  {pid}")
        print(f"  Analysis    :  {BASE_URL}/analysis/{pid}")
        print(f"  Workflow    :  {BASE_URL}/workflow/{pid}")
        print(f"  Dev view    :  {BASE_URL}/workflow/{pid}/view/dev")
        print(f"  PM view     :  {BASE_URL}/workflow/{pid}/view/pm")
        print(f"  Investor    :  {BASE_URL}/workflow/{pid}/view/investor")
    print()


# ══════════════════════════════════════════════════════════════════════
# ENTRYPOINT
# ══════════════════════════════════════════════════════════════════════

async def main():
    print("\n" + "█"*68)
    print("  AI PROJECT INTELLIGENCE PLATFORM — UNIVERSAL SYSTEM TEST")
    print("█"*68)
    print(f"  Server  : {BASE_URL}")
    print(f"  Repo    : {TEST_GITHUB_URL}")
    print(f"  Groq    : {GROQ_MODEL}")
    print(f"  Gemini  : {GEMINI_MODEL}")

    # Phase 1 — LLM direct (no server)
    phase_llm_health()

    pid = None
    async with httpx.AsyncClient(timeout=360) as client:

        # Phase 2 — server alive?
        server_ok = await phase_server_health(client)
        if not server_ok:
            print(f"\n  {FAIL} Server not reachable at {BASE_URL}")
            print("  Start it with:  uvicorn main:app --reload --port 8000")
            print_scorecard(None)
            return

        # Phase 3 — full pipeline
        pid = await phase_pipeline(client)
        if not pid:
            print(f"\n  {FAIL} Pipeline failed — skipping downstream tests")
            print_scorecard(None)
            return

        # Phases 4-7 — all require a valid project_id
        await phase_analysis(client, pid)
        await phase_chat(client, pid)
        await phase_workflow(client, pid)
        await phase_mock(client, pid)

    print_scorecard(pid)


if __name__ == "__main__":
    asyncio.run(main())