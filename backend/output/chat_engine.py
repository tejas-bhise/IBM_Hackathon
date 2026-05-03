"""
Chat engine — Universal conversational AI + RAG over repo.
Gemini PRIMARY → Groq fallback → smart structured fallback.


Fixes applied:
  Fix 1: REMOVED _validate_answer blocking — LLM answer always used if non-empty
  Fix 2: _boost_important_code() — SQL/route/function sections get higher scores
  Fix 3: _is_general_question() — tighter detection, code keywords always = RAG mode
  Fix 4: top_k raised to 12 for better context coverage
"""
import numpy as np
import logging
from services.ai_client import smart_llm_call_messages


logger = logging.getLogger(__name__)


NOISE_PREFIXES = (
    "docs/", "venv/", ".git/", "__pycache__/", "node_modules/",
    "README", "CHANGELOG", "LICENSE", ".md",
)


SOURCE_BOOST_PATTERNS = (
    "service", "route", "model", "schema", "auth", "api",
    "handler", "engine", "controller", "middleware",
)


ROLE_PROMPTS = {
    "dev": (
        "You are a senior software engineer. Focus on: exact file paths, function names, line numbers, "
        "code architecture, bugs, security issues, database queries, API design, and technical debt. "
        "Give specific, actionable technical answers. Cite exact file names and line numbers from context."
    ),
    "pm": (
        "You are a project manager focused on delivery and risk. Focus on: feature completeness, "
        "release blockers, timeline estimates, open issues that affect users, missing features, "
        "test coverage gaps, and deployment readiness. Do NOT give low-level code details. "
        "Give a high-level status: what's done, what's blocking, and when can we ship."
    ),
    "investor": (
        "You are a technical due-diligence analyst evaluating investment risk. Focus on: "
        "security posture (score and grade), architecture quality (scalability, maintainability), "
        "tech debt indicators, compliance risks (PII, data handling), team velocity signals, "
        "and overall release readiness. Give a clear GREEN/YELLOW/RED signal with reasoning. "
        "Be concise and executive-level — no code snippets unless critical."
    ),
    "lead": (
        "You are a technical lead reviewing code quality and architecture. Focus on: "
        "module structure, code smells, coupling issues, missing abstractions, security vulnerabilities, "
        "performance bottlenecks, and what needs refactoring before the next release. "
        "Give prioritized recommendations."
    ),
    "finance": (
        "You are a financial/business analyst. Focus on: infrastructure cost implications, "
        "technical risk to business continuity, compliance exposure, and resource requirements. "
        "Translate technical issues into business impact (risk, cost, delay)."
    ),
}


# Role normalization — covers all values frontend might send
def _normalize_role(role: str) -> str:
    r = str(role).lower().strip()
    r = r.replace("roleenum.", "").replace("role.", "")
    mapping = {
        "dev": "dev", "developer": "dev", "technical": "dev",
        "pm": "pm", "projectmanager": "pm", "project_manager": "pm", "manager": "pm",
        "investor": "investor", "finance": "finance", "financial": "finance",
        "lead": "lead", "techlead": "lead", "tech_lead": "lead",
    }
    return mapping.get(r, "dev")



def _is_noise(path: str) -> bool:
    return any(path.startswith(p) or path.endswith(p) for p in NOISE_PREFIXES)



def _is_source(path: str) -> bool:
    lower = path.lower()
    return any(p in lower for p in SOURCE_BOOST_PATTERNS)



def _cosine(a: list, b: list) -> float:
    arr_a = np.array(a, dtype=np.float32)
    arr_b = np.array(b, dtype=np.float32)
    na, nb = np.linalg.norm(arr_a), np.linalg.norm(arr_b)
    if na == 0 or nb == 0:
        return 0.0
    return float(np.dot(arr_a, arr_b) / (na * nb))



# ✅ Fix 2: Boost important code sections inside chunks
def _boost_important_code(chunk: dict, score: float) -> float:
    """
    Boost score for chunks containing high-signal code patterns.
    Targets: SQL queries, route definitions, function/class definitions.
    This ensures we retrieve the RIGHT part of a file, not just the top chunk.
    """
    content = chunk.get("raw_content", "").lower()


    # SQL / database logic
    if any(x in content for x in ["select ", "insert ", "update ", "delete ", "sql", "query", "cursor"]):
        score *= 1.5


    # Route / endpoint definitions
    if any(x in content for x in ["@app.", "@router.", "route(", "endpoint", "app.get(", "app.post("]):
        score *= 1.4


    # Function / class definitions (meaningful code, not imports or comments)
    if any(x in content for x in ["def ", "async def ", "function ", "class ", "const ", "export default"]):
        score *= 1.2


    # Auth / security logic
    if any(x in content for x in ["jwt", "token", "password", "hash", "auth", "login", "bearer"]):
        score *= 1.3


    # PII / sensitive data patterns
    if any(x in content for x in ["email", "phone", "ssn", "credit_card", "secret", "api_key"]):
        score *= 1.2


    return score



# ✅ Fix 3: Tighter general question detection
def _is_general_question(query: str) -> bool:
    """
    Returns True ONLY if the query is clearly a general question with zero
    codebase intent. Any code-related keyword → RAG mode.
    """
    q = query.lower()


    # These keywords always mean "look in the codebase"
    code_keywords = (
        "where", "find", "file", "function", "class", "method",
        "endpoint", "api", "route", "auth", "sql", "database",
        "code", "module", "service", "handler", "model", "schema",
        "this project", "this repo", "the project", "our code",
        "security", "issue", "bug", "error", "fix", "how does",
        "what does", "explain the", "show me", "list all", "list the",
        "what is the", "what are the", "where is", "where are",
        "how is", "which file", "what file",
    )
    for kw in code_keywords:
        if kw in q:
            return False


    # Only treat as general if it's clearly a standalone question
    return True



def _retrieve_chunks(q_emb: list, stored_chunks: list, top_k: int = 12) -> list:
    """
    ✅ Fix 3 (retrieval): Soft scoring only — no hard type filtering.
    ✅ Fix 2: Applies _boost_important_code to every chunk.
    ✅ Fix 4: top_k=12 for better coverage.
    Returns top_k unique-file chunks by boosted score.
    """
    scored = []
    for chunk in stored_chunks:
        emb = chunk.get("embedding")
        if not emb:
            continue
        path = str(chunk.get("file_path", ""))


        sim = _cosine(q_emb, emb)


        # Path-level scoring (soft, no hard exclusion)
        if _is_noise(path):
            sim *= 0.1
        elif "test" in path.lower():
            sim *= 0.5
        elif _is_source(path):
            sim *= 1.3


        # ✅ Fix 2: Content-level boost — finds the RIGHT chunk inside a file
        sim = _boost_important_code(chunk, sim)


        scored.append((sim, chunk))


    scored.sort(key=lambda x: x[0], reverse=True)


    # Deduplicate by file — keep the best-scoring chunk per file
    seen_files: set = set()
    results: list = []
    for sim, chunk in scored:
        fp = str(chunk.get("file_path", ""))
        if fp not in seen_files:
            seen_files.add(fp)
            results.append(chunk)
        if len(results) >= top_k:
            break


    return results



def _build_context(chunks: list) -> tuple:
    sources: list = []
    ctx_parts: list = []
    seen_files: set = set()


    for chunk in chunks:
        fp = str(chunk.get("file_path", "unknown"))
        start = chunk.get("chunk_start_line", chunk.get("line_start", 0))
        end = chunk.get("chunk_end_line", chunk.get("line_end", start + 60))
        code = str(chunk.get("raw_content", chunk.get("content", "")))[:600]
        funcs = chunk.get("file_functions", chunk.get("functions", []))
        clss = chunk.get("file_classes", chunk.get("classes", []))


        header = f"# {fp} (lines {start}–{end})"
        if funcs:
            header += f" | functions: {', '.join(str(x) for x in funcs[:4])}"
        if clss:
            header += f" | classes: {', '.join(str(x) for x in clss[:3])}"


        ctx_parts.append(f"{header}
{code}")


        if fp not in seen_files:
            seen_files.add(fp)
            sources.append({
                "file": fp,
                "content": code[:200],
                "lines": f"{fp}, lines {start}-{end}",
                "start_line": start,
                "end_line": end,
            })


    return "

".join(ctx_parts), sources



def _smart_fallback_answer(question: str, chunks: list, role: str = "dev") -> dict:
    """
    Only used when ALL LLMs are fully unavailable.
    Builds a structured meaningful answer from retrieved chunks.
    Never returns an empty answer.
    """
    if not chunks:
        return {
            "answer": (
                "I'm operating in offline mode right now (LLM unavailable). "
                "No relevant code chunks were found for your question. "
                "Try asking about a specific file, function, or feature in your project."
            ),
            "sources": [],
            "role": role,
            "mode": "fallback",
            "confidence": "low",
        }


    top = chunks[:8]
    seen_files: set = set()
    sources: list = []
    explanation_parts: list = []


    for chunk in top:
        fp = str(chunk.get("file_path", "unknown"))
        start = chunk.get("line_start", chunk.get("chunk_start_line", 0))
        end = chunk.get("line_end", chunk.get("chunk_end_line", start + 60))
        content = str(chunk.get("raw_content", chunk.get("content", "")))[:300]
        funcs = chunk.get("file_functions", chunk.get("functions", []))[:3]
        clss = chunk.get("file_classes", chunk.get("classes", []))[:2]


        file_name = fp.split("/")[-1] if "/" in fp else fp


        part = f"**`{file_name}`** (lines {start}–{end})"
        if funcs:
            part += f"
→ functions: `{'`, `'.join(str(f) for f in funcs)}`"
        if clss:
            part += f"
→ classes: `{'`, `'.join(str(c) for c in clss)}`"
        if content.strip():
            part += f"
```
{content.strip()[:200]}
```"
        explanation_parts.append(part)


        if fp not in seen_files:
            seen_files.add(fp)
            sources.append({
                "file": fp,
                "content": content[:200],
                "lines": f"{fp}, lines {start}-{end}",
                "start_line": start,
                "end_line": end,
            })


    answer = (
        f"Found relevant logic in {len(top)} file(s):

"
        + "

".join(explanation_parts)
        + "

*(LLM temporarily unavailable — showing top semantic matches)*"
    )


    return {
        "answer": answer,
        "sources": sources,
        "role": role,
        "mode": "fallback",
        "confidence": "medium",
    }



async def run_chat(
    question: str,
    role: str,
    project_summary: dict,
    stored_chunks: list,
    chat_history: list,
    project_id: str,
) -> dict:
    # ✅ Fixed: use _normalize_role() — covers all frontend values including "Lead", "Finance", etc.
    role = _normalize_role(role)


    has_project = bool(stored_chunks) and bool(project_id)


    # Universal conversational mode: no project OR clearly general question
    if not has_project or _is_general_question(question):
        return await _run_general_chat(question, role, chat_history, project_summary)


    # ── RAG mode: project loaded, question is about the codebase ──


    # Embed the question using local model
    q_emb: list = []
    try:
        from services.embedder import get_embedding_model
        embed_model = get_embedding_model()
        q_emb = embed_model.encode(question).tolist()
    except Exception as e:
        logger.warning(f"⚠️ Chat embed failed: {e}")


    # ✅ Fix 4: top_k=12
    top_chunks = _retrieve_chunks(q_emb, stored_chunks, top_k=12) if q_emb else []


    # If retrieval found nothing, fall back to general LLM
    if not top_chunks:
        return await _run_general_chat(question, role, chat_history, project_summary, no_chunks=True)


    context, sources = _build_context(top_chunks)


    summary_line = (
        f"Project: {project_summary.get('project_type', 'Unknown')} | "
        f"Score: {project_summary.get('security_score', '?')}/100 | "
        f"Issues: {project_summary.get('total_issues', 0)} "
        f"(Critical:{project_summary.get('critical_count', 0)} High:{project_summary.get('high_count', 0)}) | "
        f"Architecture: {project_summary.get('architecture', 'unknown')}"
    )


    system_msg = f"""You are an expert AI code assistant with full access to this project's codebase.


Project context: {summary_line}


RELEVANT CODE CONTEXT (from semantic search):
{context}


ROLE: {ROLE_PROMPTS[role]}


RULES:
- Answer from the code context above when the question is about this project
- Be specific: cite exact file names, function names, line numbers from the context
- If the exact answer is not in the context, say so briefly then answer generally
- NEVER refuse to answer — always provide something useful
- Keep answers concise and actionable"""


    messages = [{"role": "system", "content": system_msg}]
    if chat_history:
        for h in chat_history[-4:]:
            messages.append({
                "role": "user" if h.get("role") == "user" else "assistant",
                "content": str(h.get("content", "")),
            })
    messages.append({"role": "user", "content": question})


    try:
        raw, model_used = await smart_llm_call_messages(messages, task="chat", max_tokens=700)
    except Exception as e:
        logger.warning(f"⚠️ LLM call exception: {e}")
        return _smart_fallback_answer(question, top_chunks, role)


    # ✅ Fix 1: REMOVED _validate_answer blocking — if LLM gave any answer, use it directly
    if raw:
        return {
            "answer": raw,
            "sources": sources,
            "role": role,
            "mode": model_used,
            "confidence": "high" if top_chunks else "medium",
        }


    # Only reach fallback if LLM returned empty/None (both providers down)
    logger.warning("⚠️ All LLMs returned empty — using smart fallback")
    return _smart_fallback_answer(question, top_chunks, role)



async def _run_general_chat(
    question: str,
    role: str,
    chat_history: list,
    project_summary: dict,
    no_chunks: bool = False,
) -> dict:
    """
    Universal conversational mode — works like GPT/Gemini.
    Handles: general programming questions, greetings, general doubts,
    questions when no project is loaded, when RAG finds nothing.
    """
    project_context = ""
    if project_summary and project_summary.get("project_type"):
        project_context = (
            f"
Loaded project context (use if relevant): {project_summary.get('project_type', '')} project, "
            f"security score {project_summary.get('security_score', '?')}/100."
        )


    note = ""
    if no_chunks:
        note = "
(Note: Semantic search found no matching code chunks for this question in the uploaded project — answering generally.)"


    system_msg = (
        "You are a highly capable AI assistant — like GPT or Gemini — that specializes in software development. "
        "You help developers, PMs, and investors understand code, answer programming questions, explain concepts, "
        "debug issues, and have natural conversations. Be helpful, clear, and thorough."
        f"{project_context}{note}

"
        f"Role style: {ROLE_PROMPTS.get(role, ROLE_PROMPTS['dev'])}"
    )


    messages = [{"role": "system", "content": system_msg}]
    if chat_history:
        for h in chat_history[-6:]:
            messages.append({
                "role": "user" if h.get("role") == "user" else "assistant",
                "content": str(h.get("content", "")),
            })
    messages.append({"role": "user", "content": question})


    try:
        raw, model_used = await smart_llm_call_messages(messages, task="chat", max_tokens=700)
    except Exception as e:
        logger.warning(f"⚠️ General chat LLM failed: {e}")
        raw, model_used = None, "fallback"


    # ✅ Fix 1: Use any non-empty LLM answer directly
    if raw:
        return {
            "answer": raw,
            "sources": [],
            "role": role,
            "mode": model_used,
            "confidence": "high",
        }


    return {
        "answer": (
            "I'm having trouble connecting to the AI service right now. "
            "Please try again in a moment. If your question is about the uploaded project, "
            "try asking something specific like 'What does auth.py do?' or 'List all API endpoints'."
        ),
        "sources": [],
        "role": role,
        "mode": "fallback",
        "confidence": "low",
    }



# ── Public backward-compat wrapper ───────────────────────────────────────────


def smart_fallback_answer(question: str, chunks: list) -> dict:
    return _smart_fallback_answer(question, chunks, role="dev")
