"""
GitHub-facing coded tools.

These read from local, mocked JSON files (data/issues.json,
data/pull_requests.json) rather than calling the live GitHub API, per the
assignment's guidance to use deterministic data sources. Swapping these for
real GitHub API calls (PyGithub, or the REST API directly) later would not
require changing the agent network -- only these tool implementations.
"""

from typing import Any, Dict

from neuro_san.interfaces.coded_tool import CodedTool

from coded_tools.github_assistant.data_access import load_json


class GetIssueTool(CodedTool):
    """get_issue(issue_number): fetch an issue's full record."""

    def invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> Dict[str, Any]:
        issue_number = str(args.get("issue_number", "")).strip()
        if not issue_number:
            return {"error": "issue_number is required."}

        issues = load_json("issues.json")
        issue = issues.get(issue_number)
        if issue is None:
            return {
                "error": "not_found",
                "message": f"No issue #{issue_number} in the local issue tracker.",
            }

        result = dict(issue)
        result["source"] = "data/issues.json (local issue tracker)"
        return result


class GetCommitHistoryTool(CodedTool):
    """get_commit_history(issue_number): fetch commits linked to an issue."""

    def invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> Dict[str, Any]:
        issue_number = str(args.get("issue_number", "")).strip()
        if not issue_number:
            return {"error": "issue_number is required."}

        issues = load_json("issues.json")
        issue = issues.get(issue_number)
        if issue is None:
            return {
                "error": "not_found",
                "message": f"No issue #{issue_number}, so no linked commits.",
            }

        return {
            "issue_number": issue_number,
            "commits": issue.get("commits", []),
            "source": "data/issues.json (local issue tracker)",
        }


class GetPullRequestTool(CodedTool):
    """get_pull_request(pr_number): fetch a pull request's record."""

    def invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> Dict[str, Any]:
        pr_number = str(args.get("pr_number", "")).strip()
        if not pr_number:
            return {"error": "pr_number is required."}

        prs = load_json("pull_requests.json")
        pr = prs.get(pr_number)
        if pr is None:
            return {
                "error": "not_found",
                "message": f"No pull request #{pr_number} in the local PR tracker.",
            }

        result = dict(pr)
        result["source"] = "data/pull_requests.json (local PR tracker)"
        return result
