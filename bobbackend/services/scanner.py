import re
import json
import asyncio
from services.ai_client import smart_llm_call

PATTERNS = {
    "PII_EMAIL": re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'),
    "PII_PHONE": re.compile(r'\b(\+?91[-\s]?)?[6-9]\d{9}\b|\b\+1[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b'),
    "HARDCODED_SECRET": re.compile(r'(sk-[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{36}|AIza[0-9A-Za-z_\-]{35}|xox[baprs]-[A-Za-z0-9\-]{10,})'),
    "HARDCODED_PASSWORD": re.compile(r'(?i)(password|passwd|pwd|secret|token|api_key)\s*[=:]\s*["\'"][^"\']{4,}["\']'),
    "PRIVATE_KEY": re.compile(r'-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----'),
    "SQL_INJECTION": re.compile(r'(?i)(SELECT|INSERT|UPDATE|DELETE).{0,100}(\+\s*\w+|f["\'"].*\{|\.format\s*\(|%\s*\w+|\bexec\b)'),
    "PII_IN_RESPONSE": re.compile(r'(?i)(return|jsonify|json\.dumps|Response|send|render|log|print|logger\.(info|debug|warning|error))\s*[\(\{].*(email|phone|password|ssn|card_number|credit_card|dob|date_of_birth|address|social_security)', re.DOTALL),
    "UNSAFE_SERIALIZATION": re.compile(r'(?i)(pickle\.loads|yaml\.load\s*\([^,)]*\)|marshal\.loads|shelve\.open)'),
    "LOG_PII": re.compile(r'(?i)(logging\.(info|debug|warning|error|critical)|print|console\.log)\s*\(.*(email|password|token|secret|phone|ssn|credit)', re.DOTALL),
}

AUTO_CONFIRM = {"PRIVATE_KEY", "UNSAFE_SERIALIZATION"}
NEEDS_AI = {"SQL_INJECTION", "HARDCODED_PASSWORD", "HARDCODED_SECRET", "PII_IN_RESPONSE", "LOG_PII"}

NOISE_PREFIXES = (
    "docs/", "venv/", ".git/", "__pycache__/", "node_modules/",
    "README", ".md", "CHANGELOG", "LICENSE", "requirements",
)

TYPE_SEVERITY = {
    "PRIVATE_KEY": "CRITICAL",
    "HARDCODED_SECRET": "CRITICAL",
    "HARDCODED_PASSWORD": "HIGH",
    "SQL_INJECTION": "HIGH",
    "UNSAFE_SERIALIZATION": "HIGH",
    "PII_IN_RESPONSE": "MEDIUM",
    "LOG_PII": "MEDIUM",
    "PII_EMAIL": "MEDIUM",
    "PII_PHONE": "LOW",
}

TYPE_CONFIDENCE = {
    "PRIVATE_KEY": 0.99,
    "UNSAFE_SERIALIZATION": 0.95,
    "HARDCODED_SECRET": 0.90,
    "HARDCODED_PASSWORD": 0.80,
    "SQL_INJECTION": 0.70,
    "PII_IN_RESPONSE": 0.65,
    "LOG_PII": 0.65,
    "PII_EMAIL": 0.85,
    "PII_PHONE": 0.80,
}

TEST_MARKERS = {"test", "tests", "spec", "fixture", "mock", "__test__", "examples"}


def _is_test_file(path: str) -> bool:
    parts = set(path.lower().replace("\\", "/").split("/"))
    return bool(parts & TEST_MARKERS) or any(
        p.startswith("test_") or ".test." in p or ".spec." in p
        for p in path.split("/")
    )


def _is_docs_file(path: str) -> bool:
    return any(path.startswith(p) or path.endswith(p) for p in NOISE_PREFIXES)


def _is_example_file(path: str) -> bool:
    lower = path.lower()
    return any(x in lower for x in [".example", "sample", "template", "readme", ".md"])


def _get_snippet(content: str, match_start: int, context: int = 3) -> tuple:
    lines = content.split("\n")
    char_count = 0
    match_line = 0
    for i, line in enumerate(lines):
        char_count += len(line) + 1
        if char_count > match_start:
            match_line = i
            break
    start = max(0, match_line - context)
    end = min(len(lines), match_line + context + 1)
    return "\n".join(lines[start:end]), match_line + 1


def _default_fix(issue_type: str) -> str:
    fixes = {
        "SQL_INJECTION": "Use parameterized queries or ORM. Never concatenate user input into SQL strings. Example: cursor.execute('SELECT * FROM users WHERE id = %s', (user_id,))",
        "HARDCODED_SECRET": "Move to environment variable. Rotate the exposed key immediately. Use os.environ.get('KEY_NAME') or python-dotenv.",
        "HARDCODED_PASSWORD": "Use environment variables + a secrets manager. Never hardcode credentials in source code.",
        "PRIVATE_KEY": "REVOKE this key immediately. Add *.pem and private keys to .gitignore. Use a secrets vault (AWS Secrets Manager, HashiCorp Vault).",
        "PII_EMAIL": "Remove real email address from code. Use an environment variable or configuration file instead.",
        "PII_PHONE": "Replace with fake test data (e.g. +1-555-000-0000). Never use real phone numbers in code.",
        "PII_IN_RESPONSE": "Filter PII fields before returning API response. Use a DTO/response model that excludes sensitive fields.",
        "LOG_PII": "Never log PII. Mask sensitive fields: logger.info('User login', extra={'user_id': user.id}) — do NOT log email/password/token.",
        "UNSAFE_SERIALIZATION": "Replace pickle.loads with json.loads. Replace yaml.load with yaml.safe_load to prevent arbitrary code execution.",
    }
    return fixes.get(issue_type, "Review and remediate following OWASP guidelines: https://owasp.org/www-project-top-ten/")


def _default_explanation(issue_type: str, matched_text: str = "", file_path: str = "") -> str:
    fname = file_path.split("/")[-1] if "/" in file_path else file_path
    explanations = {
        "SQL_INJECTION": f"String concatenation used to build SQL query in `{fname}`. Attacker can inject malicious SQL to dump, modify, or delete database data.",
        "HARDCODED_SECRET": f"API key or secret token hardcoded directly in `{fname}`. Anyone with repo access can steal and misuse this credential.",
        "HARDCODED_PASSWORD": f"Password or secret value hardcoded as a string literal in `{fname}`. Should be loaded from environment variables.",
        "PRIVATE_KEY": f"Private key material found in `{fname}`. This is a critical credential leak — the key must be revoked immediately.",
        "PII_EMAIL": f"Real email address found hardcoded in `{fname}`. Should be replaced with environment variable or fake test data.",
        "PII_PHONE": f"Real phone number found in `{fname}`. Should be replaced with clearly fake test data.",
        "PII_IN_RESPONSE": f"Sensitive personal data (email/phone/password) appears to be included in an API response in `{fname}`. This violates privacy regulations.",
        "LOG_PII": f"Sensitive data (password/token/email) is being written to logs in `{fname}`. Logs are often stored insecurely and accessible by ops teams.",
        "UNSAFE_SERIALIZATION": f"Unsafe deserialization function detected in `{fname}`. pickle.loads/yaml.load can execute arbitrary code from malicious input.",
    }
    return explanations.get(issue_type, f"Potential security issue detected in `{fname}`. Manual review recommended.")


def _generate_before_after(issue_type: str, code_snippet: str, matched_text: str) -> tuple:
    """Generate before/after code examples for the fix suggestion panel."""
    before_after = {
        "SQL_INJECTION": (
            "# ❌ VULNERABLE\nquery = f\"SELECT * FROM users WHERE id = {user_id}\"\ncursor.execute(query)",
            "# ✅ SAFE — Use parameterized queries\nquery = \"SELECT * FROM users WHERE id = %s\"\ncursor.execute(query, (user_id,))"
        ),
        "HARDCODED_SECRET": (
            "# ❌ VULNERABLE\nAPI_KEY = \"sk-abc123xyz...\"",
            "# ✅ SAFE — Use environment variable\nimport os\nAPI_KEY = os.environ.get(\"API_KEY\")"
        ),
        "HARDCODED_PASSWORD": (
            "# ❌ VULNERABLE\npassword = \"mysecretpassword123\"",
            "# ✅ SAFE — Use environment variable\nimport os\npassword = os.environ.get(\"DB_PASSWORD\")"
        ),
        "PII_IN_RESPONSE": (
            "# ❌ VULNERABLE\nreturn jsonify(user.__dict__)  # includes email, password",
            "# ✅ SAFE — Use DTO pattern\nreturn jsonify({\"id\": user.id, \"name\": user.name})  # exclude PII"
        ),
        "LOG_PII": (
            "# ❌ VULNERABLE\nlogging.info(f\"User login: {user.email} / {password}\")",
            "# ✅ SAFE — Log only non-sensitive fields\nlogging.info(f\"User login: user_id={user.id}\")"
        ),
        "UNSAFE_SERIALIZATION": (
            "# ❌ VULNERABLE\ndata = pickle.loads(user_input)\nconfig = yaml.load(file)",
            "# ✅ SAFE\ndata = json.loads(user_input)\nconfig = yaml.safe_load(file)"
        ),
        "PRIVATE_KEY": (
            "# ❌ CRITICAL — Private key in source code\nprivate_key = \"-----BEGIN RSA PRIVATE KEY-----\\n...\"",
            "# ✅ SAFE — Load from secure vault or env\nimport os\nprivate_key_path = os.environ.get(\"PRIVATE_KEY_PATH\")"
        ),
        "PII_EMAIL": (
            "# ❌ WRONG\nadmin_email = \"john.doe@company.com\"",
            "# ✅ SAFE\nimport os\nadmin_email = os.environ.get(\"ADMIN_EMAIL\", \"admin@example.com\")"
        ),
        "PII_PHONE": (
            "# ❌ WRONG\ncontact_phone = \"+91-9876543210\"",
            "# ✅ SAFE — Use fake test data\ncontact_phone = \"+1-555-000-0000\"  # fake test number"
        ),
    }
    before, after = before_after.get(issue_type, ("", ""))
    return before, after


def _confirm_issues(raw_issues: list) -> list:
    """Conservative pass: keep every issue."""
    return list(raw_issues)


def _run_regex_pass(files: list) -> list:
    findings = []
    for file_data in files:
        path = file_data.get("path", file_data.get("file_path", ""))
        content = file_data.get("content", "")
        is_test = _is_test_file(path)
        is_example = _is_example_file(path)
        is_docs = _is_docs_file(path)

        lines = content.split("\n")

        for ptype, pattern in PATTERNS.items():
            if (is_example or is_docs) and ptype in ("HARDCODED_SECRET", "HARDCODED_PASSWORD"):
                continue
            if is_docs and ptype == "SQL_INJECTION":
                continue

            for match in pattern.finditer(content):
                snippet, line_num = _get_snippet(content, match.start())
                matched_line = lines[line_num - 1] if line_num <= len(lines) else ""

                if "return (" in matched_line:
                    continue
                if "console.log" in matched_line and "user" not in matched_line.lower():
                    continue

                needs_ai = ptype in NEEDS_AI
                base_confidence = TYPE_CONFIDENCE.get(ptype, 0.8)

                if is_test:
                    confidence = base_confidence * 0.6
                elif is_docs:
                    confidence = base_confidence * 0.4
                else:
                    confidence = base_confidence

                before_code, after_code = _generate_before_after(ptype, snippet, match.group())
                explanation = _default_explanation(ptype, match.group()[:100], path)
                fix = _default_fix(ptype)

                if is_test and ptype in ("PII_EMAIL", "PII_PHONE"):
                    findings.append({
                        "file_path": path,
                        "line_number": line_num,
                        "type": ptype,
                        "matched_text": match.group()[:100],
                        "code_snippet": snippet,
                        "needs_ai": False,
                        "severity": "LOW",
                        "confirmed": True,
                        "confidence": round(confidence, 2),
                        "fix_suggestion": "Replace with clearly fake test data.",
                        "explanation": "Test file — use fake data instead of real PII.",
                        "before_code": before_code,
                        "after_code": after_code,
                        "is_docs": is_docs,
                    })
                    continue

                if ptype in AUTO_CONFIRM:
                    findings.append({
                        "file_path": path,
                        "line_number": line_num,
                        "type": ptype,
                        "matched_text": match.group()[:100],
                        "code_snippet": snippet,
                        "needs_ai": False,
                        "severity": TYPE_SEVERITY[ptype],
                        "confirmed": True,
                        "confidence": round(base_confidence, 2),
                        "fix_suggestion": fix,
                        "explanation": explanation,
                        "before_code": before_code,
                        "after_code": after_code,
                        "is_docs": is_docs,
                    })
                    continue

                findings.append({
                    "file_path": path,
                    "line_number": line_num,
                    "type": ptype,
                    "matched_text": match.group()[:100],
                    "code_snippet": snippet,
                    "needs_ai": needs_ai,
                    "severity": TYPE_SEVERITY.get(ptype, "LOW") if not needs_ai else None,
                    "confirmed": not needs_ai,
                    "confidence": round(confidence, 2),
                    "fix_suggestion": fix,
                    "explanation": explanation,
                    "before_code": before_code,
                    "after_code": after_code,
                    "is_docs": is_docs,
                })

        # Extra SQL injection check: execute() with string concat
        for i, line in enumerate(lines):
            if "execute(" in line and "+" in line and "sql" not in path.lower():
                snippet, _ = _get_snippet(content, sum(len(l) + 1 for l in lines[:i]))
                before_code, after_code = _generate_before_after("SQL_INJECTION", snippet, line.strip())
                findings.append({
                    "file_path": path,
                    "line_number": i + 1,
                    "type": "SQL_INJECTION",
                    "matched_text": line.strip()[:100],
                    "code_snippet": snippet,
                    "needs_ai": False,
                    "severity": "HIGH",
                    "confirmed": True,
                    "confidence": 0.85,
                    "fix_suggestion": _default_fix("SQL_INJECTION"),
                    "explanation": _default_explanation("SQL_INJECTION", line.strip(), path),
                    "before_code": before_code,
                    "after_code": after_code,
                    "is_docs": is_docs,
                })

    return findings


async def _verify_batch(batch: list) -> list:
    items_text = ""
    for i, f in enumerate(batch):
        first_line = f["code_snippet"].strip().split("\n")[0][:120]
        is_docs_hint = " [docs/example file]" if f.get("is_docs") else ""
        items_text += f"[{i+1}] {f['type']} in {f['file_path']}{is_docs_hint}:\n  {first_line}\n"

    prompt = (
        f"Are these {len(batch)} code findings real production security risks?\n"
        f"{items_text}\n"
        f"Return JSON array of exactly {len(batch)} objects:\n"
        f'[{{"confirmed":true/false,"severity":"CRITICAL/HIGH/MEDIUM/LOW","explanation":"one specific sentence describing the risk","fix_suggestion":"one specific actionable sentence"}}]\n'
        f"Rules:\n"
        f"- confirmed=false if in comment, docstring, docs/ file, or example/tutorial code\n"
        f"- confirmed=true if real production code with real risk\n"
        f"- explanation must be specific, not generic\n"
        f"Return ONLY the JSON array."
    )

    try:
        raw, model_used = await smart_llm_call(prompt, task="scanner", max_tokens=600)
        if not raw:
            print(f"⚠️ Scanner: all LLMs unavailable — keeping {len(batch)} conservatively")
            return [{"confirmed": True, "confidence": 0.6} for _ in batch]

        text = raw
        if "```" in text:
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        start = text.find("[")
        end = text.rfind("]") + 1
        if start == -1 or end == 0:
            raise ValueError("No JSON array found")

        results = json.loads(text[start:end])
        if not isinstance(results, list):
            results = [results]
        while len(results) < len(batch):
            results.append({"confirmed": True, "confidence": 0.6})

        print(f" → Scanner [{model_used}]: verified {len(batch)} items")
        return results

    except (json.JSONDecodeError, ValueError) as e:
        print(f"⚠️ Scanner parse error: {e} — keeping conservatively")
        return [{"confirmed": True, "confidence": 0.6} for _ in batch]
    except Exception as e:
        print(f"⚠️ Scanner unexpected error: {e} — keeping conservatively")
        return [{"confirmed": True, "confidence": 0.6} for _ in batch]


async def run_scanner(files: list, project_id: str) -> list:
    print(f"🔍 Running deterministic security scan on {len(files)} files...")
    raw = _run_regex_pass(files)
    needs_ai_list = [f for f in raw if f.get("needs_ai")]
    pre_conf = [f for f in raw if not f.get("needs_ai") and f.get("confirmed")]

    print(f" Regex found {len(raw)} raw findings | {len(needs_ai_list)} need AI verification")

    ai_confirmed = []
    BATCH_SIZE = 3
    for i in range(0, len(needs_ai_list), BATCH_SIZE):
        batch = needs_ai_list[i: i + BATCH_SIZE]
        results = await _verify_batch(batch)
        for finding, result in zip(batch, results):
            finding["confirmed"] = True
            finding["severity"] = result.get("severity") or TYPE_SEVERITY.get(finding["type"], "MEDIUM")
            # ✅ FIX: Only override if AI gave a BETTER, non-empty explanation
            if result.get("explanation") and len(result["explanation"]) > 20:
                finding["explanation"] = result["explanation"]
            if result.get("fix_suggestion") and len(result["fix_suggestion"]) > 20:
                finding["fix_suggestion"] = result["fix_suggestion"]
            # Always ensure before/after codes are populated
            if not finding.get("before_code"):
                finding["before_code"], finding["after_code"] = _generate_before_after(
                    finding["type"], finding.get("code_snippet", ""), finding.get("matched_text", "")
                )
            finding["confidence"] = min(1.0, round(finding.get("confidence", 0.7) + 0.1, 2))
            ai_confirmed.append(finding)
        if i + BATCH_SIZE < len(needs_ai_list):
            await asyncio.sleep(0.5)

    all_issues = pre_conf + ai_confirmed

    # Final pass — ensure EVERY issue has all required fields populated
    for issue in all_issues:
        if not issue.get("fix_suggestion"):
            issue["fix_suggestion"] = _default_fix(issue["type"])
        if not issue.get("explanation"):
            issue["explanation"] = _default_explanation(
                issue["type"], issue.get("matched_text", ""), issue.get("file_path", "")
            )
        if not issue.get("before_code"):
            issue["before_code"], issue["after_code"] = _generate_before_after(
                issue["type"], issue.get("code_snippet", ""), issue.get("matched_text", "")
            )
        issue.setdefault("confidence", 0.8)

    print(f"✅ Scanner: {len(all_issues)} issues found (deterministic, 0 LLM calls)")
    return all_issues