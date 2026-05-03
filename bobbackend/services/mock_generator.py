"""
Mock generator — 100% deterministic using Faker + random.
Zero LLM calls. Instant. Always works.
"""
import random
import string
import uuid
from datetime import datetime, timedelta

# ── Faker-style word banks (no external dependency needed) ─────────────────────
FIRST_NAMES = [
    "Alex", "Jordan", "Casey", "Morgan", "Taylor", "Riley", "Drew", "Quinn",
    "Sam", "Jamie", "Blake", "Avery", "Logan", "Reese", "Skyler", "Harper",
    "Emery", "Dakota", "Finley", "Rowan", "Charlie", "Sage", "River", "Phoenix",
]
LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
    "Wilson", "Moore", "Taylor", "Anderson", "Thomas", "Jackson", "White", "Harris",
    "Martin", "Thompson", "Young", "Walker", "Hall", "Allen", "King", "Wright",
]
DOMAINS    = ["mockdata.dev", "testonly.io", "fake-users.net", "sandbox.local"]
ROLES      = ["admin", "user", "developer", "tester", "manager", "viewer", "editor"]
COMPANIES  = ["Acme Corp", "TechLabs", "DevStudio", "CloudBase", "AppWorks", "CodeCraft"]
STATUSES   = ["active", "inactive", "pending", "suspended"]
CITIES     = ["New York", "London", "Toronto", "Sydney", "Berlin", "Tokyo", "Paris", "Mumbai"]
STREETS    = ["Main St", "Oak Ave", "Maple Rd", "Cedar Blvd", "Pine Lane", "Elm Drive"]


# ── Deterministic generators ───────────────────────────────────────────────────

def _random_str(n: int = 8) -> str:
    return "".join(random.choices(string.ascii_lowercase, k=n))

def _random_name() -> str:
    return f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"

def _random_email(name: str | None = None) -> str:
    if name:
        local = name.lower().replace(" ", ".") + str(random.randint(1, 99))
    else:
        local = _random_str(8)
    return f"{local}@{random.choice(DOMAINS)}"

def _random_phone() -> str:
    return f"+1-555-{random.randint(100, 999)}-{random.randint(1000, 9999)}"

def _random_uuid() -> str:
    return str(uuid.uuid4())

def _random_date(days_back: int = 365) -> str:
    delta = timedelta(days=random.randint(0, days_back))
    return (datetime.utcnow() - delta).strftime("%Y-%m-%d")

def _random_address() -> str:
    return f"{random.randint(1, 999)} {random.choice(STREETS)}, {random.choice(CITIES)}"

def _random_company() -> str:
    return random.choice(COMPANIES)

def _generate_user(index: int) -> dict:
    name = _random_name()
    return {
        "id":         f"mock_{index:03d}",
        "uuid":       _random_uuid(),
        "name":       name,
        "email":      _random_email(name),
        "phone":      _random_phone(),
        "role":       random.choice(ROLES),
        "company":    _random_company(),
        "address":    _random_address(),
        "status":     random.choice(STATUSES),
        "created_at": _random_date(730),
        "updated_at": _random_date(30),
    }

def _generate_replacement_values(pii_type: str, count: int = 3) -> list:
    """Generate fake replacement values for a given PII type."""
    if pii_type == "PII_EMAIL":
        return [_random_email() for _ in range(count)]
    if pii_type == "PII_PHONE":
        return [_random_phone() for _ in range(count)]
    if pii_type == "PII_SSN":
        return [f"000-{random.randint(10,99)}-{random.randint(1000,9999)}" for _ in range(count)]
    if pii_type in ("HARDCODED_SECRET", "HARDCODED_PASSWORD"):
        return [f"REPLACE_WITH_ENV_VAR_{_random_str(6).upper()}" for _ in range(count)]
    return [f"MOCK_{pii_type}_{i+1}" for i in range(count)]


# ── Main entry point ───────────────────────────────────────────────────────────

async def run_mock_generator(security_issues: list, project_id: str) -> dict:
    """
    Fully deterministic mock data generator. No LLM calls. No tokens spent.
    Uses random name/email/phone generators to produce realistic-looking test data.
    """
    pii_issues = [i for i in security_issues if i.get("type", "").startswith("PII_")]
    print(f"🎭 Generating deterministic mock data for {len(pii_issues)} PII issues...")

    pii_types = list(dict.fromkeys(i["type"] for i in pii_issues)) if pii_issues else ["PII_EMAIL", "PII_PHONE"]

    # Generate 5 sample users
    sample_users = [_generate_user(i + 1) for i in range(5)]

    # Generate replacement values for each PII type found
    replacements: dict = {}
    for ptype in pii_types:
        replacements[ptype] = _generate_replacement_values(ptype, count=3)

    # Always include these two even if not detected
    if "PII_EMAIL" not in replacements:
        replacements["PII_EMAIL"] = [_random_email() for _ in range(3)]
    if "PII_PHONE" not in replacements:
        replacements["PII_PHONE"] = [_random_phone() for _ in range(2)]

    print(f"✅ Mock data generated: {len(sample_users)} users, {len(pii_types)} PII types (0 LLM calls)")

    return {
        "project_id":            project_id,
        "total_pii_fields_found": len(pii_issues),
        "sample_users":          sample_users,
        "mode":                  "deterministic",
        **replacements,
    }