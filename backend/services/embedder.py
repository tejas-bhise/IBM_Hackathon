import re
import hashlib
import numpy as np
from sentence_transformers import SentenceTransformer
from typing import Optional

_model: Optional[SentenceTransformer] = None

# 60 lines per chunk — fits all-MiniLM-L6-v2's 256-token limit perfectly
# 500 lines (old) caused silent truncation → bad embedding quality
CHUNK_SIZE = 60
CHUNK_STEP = 40  # 20-line overlap

SKIP_EXTS = {
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico",
    ".woff", ".woff2", ".ttf", ".eot", ".otf",
    ".zip", ".tar", ".gz", ".pdf", ".lock",
    ".pyc", ".pyo", ".pyd", ".so", ".dll", ".exe",
    ".min.js", ".min.css",
}

SKIP_DIRS = {
    "node_modules", ".git", "__pycache__", "venv", ".venv",
    "dist", "build", ".next", "coverage", ".pytest_cache",
}

MAX_FILE_BYTES = 200_000


def get_embedding_model() -> SentenceTransformer:
    global _model
    if _model is None:
        print("📦 Loading embedding model (all-MiniLM-L6-v2)...")
        _model = SentenceTransformer("all-MiniLM-L6-v2")
        print("✅ Embedding model loaded")
    return _model


def extract_imports(text: str) -> list:
    found = set()
    for m in re.finditer(r'^(?:import|from)\s+([\w.]+)', text, re.MULTILINE):
        found.add(m.group(1).split(".")[0])
    for m in re.finditer(r"""(?:import\s+.*?from\s+['"](.+?)['"]|require\s*\(\s*['"](.+?)['"]\s*\))""", text):
        val = m.group(1) or m.group(2)
        if val:
            found.add(val.lstrip("./").split("/")[0])
    return sorted(found)


def extract_functions(text: str) -> list:
    found = set()
    for m in re.finditer(r'^(?:async\s+)?def\s+(\w+)\s*\(', text, re.MULTILINE):
        found.add(m.group(1))
    for m in re.finditer(r'(?:function\s+(\w+)|(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s*)?\()', text):
        val = m.group(1) or m.group(2)
        if val:
            found.add(val)
    return sorted(found)


def extract_classes(text: str) -> list:
    found = set()
    for m in re.finditer(r'^class\s+(\w+)\s*[\(:]', text, re.MULTILINE):
        found.add(m.group(1))
    for m in re.finditer(r'^(?:export\s+)?(?:abstract\s+)?class\s+(\w+)', text, re.MULTILINE):
        found.add(m.group(1))
    return sorted(found)


def extract_routes(text: str) -> list:
    found = set()
    for m in re.finditer(r"""(?:@(?:app|router)\.\w+\s*\(\s*['"]([^'"]+)['"]|route\s*\(\s*['"]([^'"]+)['"]\s*,\s*methods)""", text):
        val = m.group(1) or m.group(2)
        if val:
            found.add(val)
    return sorted(found)


def _should_skip(path: str) -> bool:
    lower = path.lower()
    parts = set(lower.replace("\\", "/").split("/"))
    if parts & SKIP_DIRS:
        return True
    for ext in SKIP_EXTS:
        if lower.endswith(ext):
            return True
    if lower.endswith("requirements.txt") or lower.endswith("package-lock.json"):
        return True
    return False


def _chunk_text(content: str) -> list:
    """
    60-line chunks with 20-line overlap.
    Fits all-MiniLM-L6-v2's 256-token limit for accurate embeddings.
    """
    lines = content.split("\n")
    chunks = []
    i = 0
    while i < len(lines):
        end = min(i + CHUNK_SIZE, len(lines))
        block = "\n".join(lines[i:end]).strip()
        if block:
            chunks.append((block, i + 1, end))
        if end >= len(lines):
            break
        i += CHUNK_STEP
    return chunks


async def run_embedder(files: list, project_id: str) -> list:
    """
    Embeds all source files using local all-MiniLM-L6-v2 model ONLY.
    No Gemini API calls. No network requests. Pure local inference.
    """
    model = get_embedding_model()
    results = []
    skipped = 0

    for file_data in files:
        path = file_data.get("path", "")
        content = file_data.get("content", "")

        if _should_skip(path):
            skipped += 1
            continue
        if not content or not content.strip():
            skipped += 1
            continue
        if len(content.encode()) > MAX_FILE_BYTES:
            content = content[:MAX_FILE_BYTES]

        parts = path.replace("\\", "/").split("/")
        file_name = parts[-1]
        folder = "/".join(parts[:-1]) if len(parts) > 1 else ""

        all_imports = extract_imports(content)
        all_functions = extract_functions(content)
        all_classes = extract_classes(content)
        all_routes = extract_routes(content)

        chunks = _chunk_text(content)
        for raw_content, line_start, line_end in chunks:
            chunk_id = hashlib.md5(f"{project_id}:{path}:{line_start}".encode()).hexdigest()

            embedding = model.encode(raw_content, normalize_embeddings=True).tolist()

            chunk_imports = extract_imports(raw_content)
            chunk_functions = extract_functions(raw_content)
            chunk_classes = extract_classes(raw_content)
            chunk_routes = extract_routes(raw_content)

            results.append({
                "chunk_id": chunk_id,
                "project_id": project_id,
                "file_path": path,
                "file_name": file_name,
                "folder": folder,
                "line_start": line_start,
                "line_end": line_end,
                "raw_content": raw_content,
                "embedding": embedding,
                "file_imports": all_imports,
                "file_functions": all_functions,
                "file_classes": all_classes,
                "file_routes": all_routes,
                "imports": chunk_imports,
                "functions": chunk_functions,
                "classes": chunk_classes,
                "routes": chunk_routes,
            })

    print(f"✅ Embedder: {len(results)} chunks from {len(files) - skipped} files ({skipped} skipped)")
    return results


def _is_source_code(path: str) -> bool:
    path = path.lower()
    return any([
        path.endswith(".py"), path.endswith(".js"),
        path.endswith(".ts"), path.endswith(".tsx"),
        path.endswith(".jsx"), path.endswith(".java"),
        path.endswith(".go"), path.endswith(".rs"),
        path.endswith(".cpp"), path.endswith(".c"),
        path.endswith(".cs"), path.endswith(".rb"),
        path.endswith(".php"), path.endswith(".swift"),
        path.endswith(".kt"),
    ])


def _is_noise_file(path: str) -> bool:
    path = path.lower()
    return any([
        "node_modules" in path, "package-lock.json" in path,
        "yarn.lock" in path, "pnpm-lock.yaml" in path,
        ".git" in path, "dist/" in path,
        "build/" in path, "coverage/" in path,
        ".next/" in path, "__pycache__" in path,
        "venv/" in path, ".venv/" in path,
        path.endswith(".md"), path.endswith(".txt"),
        path.endswith(".log"),
        (path.endswith(".json") and any(x in path for x in ["package-lock", "yarn.lock", "pnpm-lock"])),
    ])


def _adjust_score(path: str, score: float) -> float:
    path = path.lower()
    if _is_source_code(path):
        return score * 1.5
    if path.endswith(".md") or path.endswith(".txt") or "docs/" in path:
        return score * 0.3
    return score


def _boost_important_code(chunk: dict, score: float) -> float:
    """
    Boost score for chunks containing high-signal code patterns.
    Applied during search to surface the RIGHT chunk inside a file.
    """
    content = chunk.get("raw_content", "").lower()

    if any(x in content for x in ["select ", "insert ", "update ", "delete ", "sql", "query", "cursor"]):
        score *= 1.5

    if any(x in content for x in ["@app.", "@router.", "route(", "endpoint", "app.get(", "app.post("]):
        score *= 1.4

    if any(x in content for x in ["def ", "async def ", "function ", "class ", "const ", "export default"]):
        score *= 1.2

    if any(x in content for x in ["jwt", "token", "password", "hash", "auth", "login", "bearer"]):
        score *= 1.3

    if any(x in content for x in ["email", "phone", "ssn", "credit_card", "secret", "api_key"]):
        score *= 1.2

    return score


async def search_chunks_in_memory(
    query: str,
    stored_chunks: list,
    top_k: int = 12,
    min_score: float = 0.15,
) -> list:
    """
    Search stored chunks using local model ONLY. No Gemini.
    Applies both path-level and content-level boosting.
    """
    if not stored_chunks:
        return []

    model = get_embedding_model()
    query_vec = model.encode(query, normalize_embeddings=True)
    scored = []

    for chunk in stored_chunks:
        emb = chunk.get("embedding")
        if not emb:
            continue
        score = float(np.dot(query_vec, np.array(emb)))
        if score >= min_score:
            scored.append((score, chunk))

    scored.sort(key=lambda x: x[0], reverse=True)

    filtered = []
    for score, chunk in scored:
        path = chunk.get("file_path", "")
        if _is_noise_file(path):
            continue
        adjusted_score = _adjust_score(path, score)
        adjusted_score = _boost_important_code(chunk, adjusted_score)
        filtered.append((adjusted_score, chunk))

    filtered.sort(key=lambda x: x[0], reverse=True)
    return [c for _, c in filtered[:top_k]]