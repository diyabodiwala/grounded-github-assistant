"""
Code-retrieval coded tools, operating over data/sample_repo/.
"""

import os
from typing import Any, Dict

from neuro_san.interfaces.coded_tool import CodedTool

from coded_tools.github_assistant.data_access import (
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
    """list_related_files(): list every file currently indexed in the sample repo."""

    def invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "files": list_files(sample_repo_dir()),
            "source": "data/sample_repo/ (local indexed codebase)",
        }


class ReadFileTool(CodedTool):
    """read_file(path): read the full contents of a file in the sample repo."""

    def invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> Dict[str, Any]:
        path = (args.get("path") or "").strip()
        if not path:
            return {"error": "path is required."}

        # Guard against path traversal outside the sample repo directory.
        safe_name = os.path.basename(path)
        full_path = os.path.join(sample_repo_dir(), safe_name)

        if not os.path.isfile(full_path):
            return {
                "error": "not_found",
                "message": f"'{safe_name}' is not a file in the indexed sample repo.",
            }

        with open(full_path, "r", encoding="utf-8") as f:
            content = f.read()

        return {
            "path": safe_name,
            "content": content,
            "source": "data/sample_repo/ (local indexed codebase)",
        }
