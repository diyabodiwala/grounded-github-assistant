"""
Shared, deterministic helpers for the github_assistant coded tools.

Retrieval here is intentionally a plain keyword/line-match search rather
than an embeddings pipeline. For a small, fixed local corpus this is fully
deterministic, needs no model download, and is easy to unit test -- and it
demonstrates the same "retrieve, then ground the LLM in what was retrieved"
pattern that a FAISS/embeddings-based retriever would. Swapping this module
for a real vector-search backend later would not require touching the
agent network or any other tool. See README "Future Improvements".
"""

import json
import os
import re
from typing import Any, Dict, List

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_THIS_DIR, "..", ".."))
_DATA_DIR = os.path.join(_REPO_ROOT, "data")
_SAMPLE_REPO_DIR = os.path.join(_DATA_DIR, "sample_repo")
_DOCS_DIR = os.path.join(_DATA_DIR, "docs")

_CACHE: Dict[str, Any] = {}


def load_json(filename: str) -> Dict[str, Any]:
    """Load (and cache) a JSON data file from the /data directory."""
    if filename not in _CACHE:
        path = os.path.join(_DATA_DIR, filename)
        with open(path, "r", encoding="utf-8") as data_file:
            _CACHE[filename] = json.load(data_file)
    return _CACHE[filename]


def sample_repo_dir() -> str:
    return _SAMPLE_REPO_DIR


def docs_dir() -> str:
    return _DOCS_DIR


def list_files(directory: str) -> List[str]:
    """List file names (not full paths) in a data subdirectory, sorted."""
    return sorted(
        f for f in os.listdir(directory)
        if os.path.isfile(os.path.join(directory, f))
    )


def _tokenize(text: str) -> List[str]:
    return re.findall(r"[a-z0-9_]+", text.lower())


def keyword_search(query: str, directory: str, max_results: int = 5, context_lines: int = 2) -> List[Dict[str, Any]]:
    """
    Deterministic keyword search over every file in `directory`.

    Scores each file by the number of query-token occurrences (whole-word,
    case-insensitive) and returns, for the top-scoring files, the matching
    line numbers plus a small window of surrounding context so the caller
    gets a grounded snippet rather than a bare filename.

    :return: a list of dicts, each with file name, score, and matched snippets
    """
    query_tokens = set(_tokenize(query))
    if not query_tokens:
        return []

    results = []
    for filename in list_files(directory):
        path = os.path.join(directory, filename)
        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        matches = []
        score = 0
        for i, line in enumerate(lines):
            line_tokens = set(_tokenize(line))
            overlap = query_tokens & line_tokens
            if overlap:
                score += len(overlap)
                start = max(0, i - context_lines)
                end = min(len(lines), i + context_lines + 1)
                snippet = "".join(lines[start:end]).rstrip("\n")
                matches.append({"line_number": i + 1, "snippet": snippet})

        if score > 0:
            results.append({
                "file": filename,
                "score": score,
                "matches": matches[:3],  # cap snippets per file to keep responses compact
            })

    results.sort(key=lambda r: r["score"], reverse=True)
    return results[:max_results]
