"""
Documentation-retrieval coded tool, operating over data/docs/.
"""

from typing import Any, Dict

from neuro_san.interfaces.coded_tool import CodedTool

from coded_tools.github_assistant.data_access import docs_dir, keyword_search


class SearchDocsTool(CodedTool):
    """search_docs(query): keyword-search the project's markdown documentation."""

    def invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> Dict[str, Any]:
        query = (args.get("query") or "").strip()
        if not query:
            return {"error": "query is required."}

        results = keyword_search(query, docs_dir(), max_results=5)
        return {
            "query": query,
            "results": results,
            "source": "data/docs/ (local indexed documentation)",
        }
