"""
Code-retrieval coded tools, operating over data/sample_repo/ and, for
ReadFileTool/ListRelatedFilesTool, data/docs/ as well -- validation_agent in
particular needs to be able to read back a documentation file the planner
named, not just source files.
"""

import os
from typing import Any, Dict

from neuro_san.interfaces.coded_tool import CodedTool

from coded_tools.github_assistant.data_access import (
    docs_dir,
    keyword_search,
    list_files,
    sample_repo_dir,
)


class SearchCodeTool(CodedTool):
    """search_code(query): keyword-search the sample repo's source files."""

    def invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> Dict[str, Any]:
        query = (args.get("query") or "").strip()
        if not query:
            return {"error": "query is required."}

        results = keyword_search(query, sample_repo_dir(), max_results=5)
        return {
            "query": query,
            "results": results,
            "source": "data/sample_repo/ (local indexed codebase)",
        }


class ListRelatedFilesTool(CodedTool):
    """list_related_files(): list every file currently indexed, code and docs."""

    def invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "code_files": list_files(sample_repo_dir()),
            "doc_files": list_files(docs_dir()),
            "source": "data/sample_repo/ and data/docs/ (local indexed codebase + docs)",
        }


class ReadFileTool(CodedTool):
    """read_file(path): read the full contents of an indexed code or doc file."""

    def invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> Dict[str, Any]:
        path = (args.get("path") or "").strip()
        if not path:
            return {"error": "path is required."}

        # Guard against path traversal by only ever looking at the basename,
        # then check both indexed locations -- source files live in
        # sample_repo/, documentation lives in docs/.
        safe_name = os.path.basename(path)

        for directory, source_label in (
            (sample_repo_dir(), "data/sample_repo/ (local indexed codebase)"),
            (docs_dir(), "data/docs/ (local indexed documentation)"),
        ):
            full_path = os.path.join(directory, safe_name)
            if os.path.isfile(full_path):
                with open(full_path, "r", encoding="utf-8") as f:
                    content = f.read()
                return {
                    "path": safe_name,
                    "content": content,
                    "source": source_label,
                }

        return {
            "error": "not_found",
            "message": (
                f"'{safe_name}' is not a file in the indexed codebase (data/sample_repo/) "
                "or the indexed documentation (data/docs/)."
            ),
        }

