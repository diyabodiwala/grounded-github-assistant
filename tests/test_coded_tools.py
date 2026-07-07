"""
Unit tests for the deterministic coded tools. No LLM or API key required --
these exercise the grounded retrieval/lookup layer directly.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from coded_tools.github_assistant.code_search_tool import (
    ListRelatedFilesTool,
    ReadFileTool,
    SearchCodeTool,
)
from coded_tools.github_assistant.document_search_tool import SearchDocsTool
from coded_tools.github_assistant.github_tools import (
    GetCommitHistoryTool,
    GetIssueTool,
    GetPullRequestTool,
)


def test_get_issue_known_issue():
    result = GetIssueTool().invoke({"issue_number": 15}, {})
    assert "error" not in result
    assert "OAuth" in result["title"]
    assert "auth.py" in result["related_files"]


def test_get_issue_unknown_issue_reports_not_found():
    result = GetIssueTool().invoke({"issue_number": 9999}, {})
    assert result["error"] == "not_found"


def test_get_issue_missing_arg_is_error():
    assert "error" in GetIssueTool().invoke({}, {})


def test_get_commit_history_known_issue():
    result = GetCommitHistoryTool().invoke({"issue_number": 15}, {})
    assert "error" not in result
    shas = [c["sha"] for c in result["commits"]]
    assert "a1b2c3d" in shas


def test_get_pull_request_known_pr():
    result = GetPullRequestTool().invoke({"pr_number": 44}, {})
    assert result["status"] == "merged"
    assert "auth.py" in result["files_changed"]


def test_get_pull_request_unknown_pr_reports_not_found():
    result = GetPullRequestTool().invoke({"pr_number": 999}, {})
    assert result["error"] == "not_found"


def test_search_code_finds_oauth_state_files():
    result = SearchCodeTool().invoke({"query": "oauth state validation callback"}, {})
    files = [r["file"] for r in result["results"]]
    assert "auth.py" in files
    assert "oauth.py" in files


def test_search_code_unrelated_query_does_not_match_unrelated_files():
    result = SearchCodeTool().invoke({"query": "oauth state validation callback"}, {})
    files = [r["file"] for r in result["results"]]
    assert "database.py" not in files


def test_search_code_missing_query_is_error():
    assert "error" in SearchCodeTool().invoke({}, {})


def test_search_docs_finds_authentication_flow():
    result = SearchDocsTool().invoke({"query": "oauth state validation csrf"}, {})
    files = [r["file"] for r in result["results"]]
    assert "authentication_flow.md" in files


def test_list_related_files_returns_all_indexed_files():
    result = ListRelatedFilesTool().invoke({}, {})
    assert set(result["files"]) == {"auth.py", "database.py", "oauth.py", "utils.py"}


def test_read_file_returns_full_contents():
    result = ReadFileTool().invoke({"path": "oauth.py"}, {})
    assert "is_state_valid" in result["content"]


def test_read_file_unknown_file_reports_not_found():
    result = ReadFileTool().invoke({"path": "does_not_exist.py"}, {})
    assert result["error"] == "not_found"


def test_read_file_blocks_path_traversal():
    result = ReadFileTool().invoke({"path": "../../etc/passwd"}, {})
    assert result["error"] == "not_found"
