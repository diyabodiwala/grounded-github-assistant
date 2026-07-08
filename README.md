# Grounded Multi-Agent GitHub Coding Assistant (neuro-san)

A multi-agent network, built on [neuro-san-studio](https://github.com/cognizant-ai-lab/neuro-san-studio),
that helps a developer triage a GitHub issue: "Help me resolve issue #15" in,
and get back a grounded implementation plan with evidence -- not a guess from
model memory.

## Problem statement

Resolving an issue well means pulling together several things that live in
different places: the issue text itself, the relevant source files, the
relevant docs, and prior related PRs/commits -- then reasoning about all of
them together without inventing a file, function, or root cause that isn't
actually there. A single agent doing all of this in one prompt tends to blend
real retrieved context with plausible-sounding invented detail, especially
once the context window fills up with several different kinds of source
material. This project separates that work by domain and adds an
independent verification pass before anything reaches the user.

## Why multi-agent

- **GitHub agent**, **code retrieval agent**, and **docs agent** each own one
  narrow, tool-backed concern, so each only has to be right about one thing.
- **Planner agent** is deliberately tool-less: it only synthesizes from the
  context the other agents already retrieved, which forces it to work from
  grounded material instead of reaching for its own knowledge.
- **Validation agent** doesn't read the planner's summary and trust it -- it
  independently re-calls the retrieval tools itself and diffs the draft plan
  against fresh results, catching anything the planner mis-stated, dropped,
  or invented.
- **Response agent** only formats already-validated content into the final
  answer, so formatting concerns never leak into and dilute the fact-finding
  and validation steps.

## Architecture

```
                                   User
                                     │
                                     ▼
                             orchestrator
                            (front-man agent)
              ┌───────────────┬──────┴───────┬─────────────────┐
              ▼               ▼              ▼                 ▼
      github_agent   code_retrieval_agent  docs_agent    (after gathering
                                                            context, calls
                                                            planner_agent)
              │               │              │
              ▼               ▼              ▼
       GetIssueTool      SearchCodeTool  SearchDocsTool
       GetCommitHistoryTool  ReadFileTool
       GetPullRequestTool    ListRelatedFilesTool
              │               │              │
              ▼               ▼              ▼
     data/issues.json   data/sample_repo/  data/docs/
     data/pull_requests.json

                             planner_agent
                        (drafts plan from context;
                         no tools of its own)
                                     │
                                     ▼
                           validation_agent
                    (independently re-calls GetIssueTool,
                     SearchCodeTool, SearchDocsTool, ReadFileTool
                     to fact-check the draft plan)
                                     │
                                     ▼
                            response_agent
                    (formats the validated plan + evidence
                     into the final answer; no tools)
                                     │
                                     ▼
                                 Final Answer
```

## Agent responsibilities

| Agent | Responsibility | Tools |
|---|---|---|
| `orchestrator` | Front-man. Collects the issue number, delegates to specialists, sends the draft plan through validation, and relays the final formatted answer. | — |
| `github_agent` | Fetches issue text, linked commits, and PR details. | `GetIssueTool`, `GetCommitHistoryTool`, `GetPullRequestTool` |
| `code_retrieval_agent` | Finds relevant source files/snippets; can list all indexed files or read one in full. | `SearchCodeTool`, `ListRelatedFilesTool`, `ReadFileTool` |
| `docs_agent` | Finds relevant documentation sections. | `SearchDocsTool` |
| `planner_agent` | Synthesizes a root-cause + implementation plan **only** from the context it's handed -- no tools of its own, so it can't reach outside the retrieved material. | — |
| `validation_agent` | Independently re-derives the facts and flags any unsupported claim in the draft plan. | `GetIssueTool`, `SearchCodeTool`, `SearchDocsTool`, `ReadFileTool` |
| `response_agent` | Formats the validated plan into the final answer with an evidence section. No new claims allowed. | — |

## Tool descriptions

| Tool | Function | Backed by |
|---|---|---|
| `GetIssueTool` | `get_issue(issue_number)` | `data/issues.json` |
| `GetCommitHistoryTool` | `get_commit_history(issue_number)` | `data/issues.json` (`commits` field per issue) |
| `GetPullRequestTool` | `get_pull_request(pr_number)` | `data/pull_requests.json` |
| `SearchCodeTool` | `search_code(query)` | keyword search over `data/sample_repo/*.py` |
| `ListRelatedFilesTool` | `list_related_files()` | directory listing of `data/sample_repo/` and `data/docs/` |
| `ReadFileTool` | `read_file(path)` | reads one file from `data/sample_repo/` or `data/docs/` (basename-only, blocks path traversal) |
| `SearchDocsTool` | `search_docs(query)` | keyword search over `data/docs/*.md` |

## How grounding works

```
User Query ("issue #15")
      │
      ▼
GetIssueTool ──▶ data/issues.json
      │
      ▼
SearchCodeTool / SearchDocsTool ──▶ data/sample_repo/, data/docs/
      │
      ▼
Relevant snippets (file name + line number + text)
      │
      ▼
planner_agent (LLM, but constrained to the snippets above)
      │
      ▼
validation_agent (independently re-fetches the same sources and
                   diffs the draft plan against them)
      │
      ▼
Grounded, evidence-cited response
```

Every tool that hits a miss (`not_found`) says so explicitly, and every
agent's instructions forbid treating a `not_found`/error result as "no
issue" -- they must relay the gap rather than assume a clean/empty answer.

### A deliberate simplification: keyword search, not embeddings

The JD/plan mentions FAISS + sentence-transformers for `search_code` /
`search_docs`. For a small, fixed local corpus like this one, a plain
keyword/line-match search (see `coded_tools/github_assistant/data_access.py`)
gives the same "retrieve real snippets, then ground the LLM in them"
guarantee, is fully deterministic and unit-testable with zero model
downloads or network calls, and keeps the project scoped to what a 2-day
assessment can actually finish end-to-end. Swapping in a real embeddings
index later is a drop-in replacement for `keyword_search()` -- it wouldn't
require touching the agent network, the HOCON file, or any other tool. See
**Future Improvements** below.

## Example queries and outputs

**Query:** `Help me resolve issue #15`

Expected flow: `github_agent` returns the issue ("OAuth login intermittently
fails after redirect", files `auth.py`/`oauth.py`, linked PR #44);
`code_retrieval_agent` and `docs_agent` surface `auth.py`'s
`handle_oauth_callback` (which accepts `state` but never validates it),
`oauth.py`'s `is_state_valid`, and `authentication_flow.md`'s "Security
requirement: state validation" section; `planner_agent` proposes calling
`is_state_valid(state)` inside `handle_oauth_callback` before issuing a
session; `validation_agent` re-confirms all of that against fresh tool
calls; `response_agent` returns the plan with an evidence list citing issue
#15, `auth.py`, `oauth.py`, and `authentication_flow.md`.

**Query:** `Help me resolve issue #9999` (doesn't exist)

Expected flow: `github_agent`'s `GetIssueTool` returns `"error":
"not_found"`; `orchestrator` stops and tells the user the issue wasn't
found, rather than inventing a plausible-sounding issue.

**Query:** `Help me resolve issue #31` (a real but unrelated, low-context
issue -- unicode support in `slugify()`)

Expected flow: retrieval correctly surfaces `utils.py` and nothing from
`auth.py`/`oauth.py`, demonstrating the retrieval isn't just keyed off issue
number but actually discriminates by content.

### The full local issue set

`data/issues.json` contains 6 mock issues in total, each grounded in a real,
verifiable gap in `data/sample_repo/` -- not invented bugs with no basis in
the actual sample code:

| Issue | Title | Real gap in the code |
|---|---|---|
| #15 | OAuth login intermittently fails after redirect | `auth.py`'s `handle_oauth_callback` accepts `state` but never calls `oauth.py`'s `is_state_valid` |
| #22 | Session tokens never expire under load testing | (scenario issue -- see `auth.py`'s `token_ttl_seconds` handling) |
| #31 | Add slugify support for unicode characters | `utils.py`'s `slugify()` strips non-ASCII characters entirely |
| #47 | No way to log out -- tokens are never invalidated on demand | `auth.py`'s `AuthService` has `login()`/`validate_session()` but no `logout()`/`invalidate_session()` |
| #58 | `InMemoryDatabase` is not thread-safe under concurrent access | `database.py`'s `_store` dict has no locking around `put`/`get`/`delete` |
| #63 | `truncate()` can split a multi-character symbol at the cutoff | `utils.py`'s `truncate()` cuts on a raw character index, not a grapheme boundary |

Every one of these was verified end-to-end before being added: each
issue's `related_files` entry is confirmed to actually surface via
`SearchCodeTool` for a realistic query about that issue (see
`tests/test_coded_tools.py`), not just declared in the JSON and hoped for.

## Project layout

```
.
├── registries/
│   ├── manifest.hocon
│   └── github_assistant.hocon        # the agent network definition
├── coded_tools/
│   └── github_assistant/
│       ├── data_access.py            # shared JSON loading + keyword search
│       ├── github_tools.py           # GetIssueTool, GetCommitHistoryTool, GetPullRequestTool
│       ├── code_search_tool.py       # SearchCodeTool, ListRelatedFilesTool, ReadFileTool
│       └── document_search_tool.py   # SearchDocsTool
├── data/
│   ├── issues.json
│   ├── pull_requests.json
│   ├── docs/
│   │   ├── authentication_flow.md
│   │   ├── architecture.md
│   │   └── api.md
│   └── sample_repo/
│       ├── auth.py
│       ├── oauth.py
│       ├── database.py
│       └── utils.py
├── config/
│   └── llm_config.hocon
├── tests/
│   └── test_coded_tools.py
├── requirements.txt
├── .env.example
└── README.md
```

Note on structure: the assignment's plan sketched a generic
`agents/*.py` + `tools/*.py` layout. Real neuro-san doesn't work that way --
agents are declared as data in the HOCON registry file (instructions +
tool wiring), and only the *coded tools* are Python, living under
`coded_tools/<network_name>/`. This repo follows the actual framework
convention rather than forcing a generic layout onto it.

## Running it

```bash
# 1. Clone neuro-san-studio and drop this project's files into it
git clone https://github.com/cognizant-ai-lab/neuro-san-studio
cd neuro-san-studio
cp /path/to/grounded-github-assistant/registries/github_assistant.hocon registries/
cp -r /path/to/grounded-github-assistant/coded_tools/github_assistant coded_tools/
cp -r /path/to/grounded-github-assistant/data .
# add "github_assistant.hocon": true to registries/manifest.hocon

# 2. Install deps
pip install -r requirements.txt
pip install langchain-mistralai==1.1.2

# 3. Set your key
export MISTRAL_API_KEY="your-key-here"
export AGENT_MANIFEST_FILE="./registries/manifest.hocon"
export AGENT_TOOL_PATH="./coded_tools"

# 4. Run
python -m neuro_san_studio.run
```

Open the nsflow UI (default `http://localhost:4173/`), pick
`github_assistant`, and ask:

> Help me resolve issue #15

## Running the tests (no LLM/API key required)

```bash
pip install pytest
pytest tests/ -v
```

All 14 tests pass without any network access or API key -- they call the
coded tools directly against the local JSON/file data.

## Validation finding from a live run (and the fix)

Running this against a real LLM (Mistral) surfaced a genuine grounding
failure worth documenting rather than hiding:

**What happened:** `validation_agent` correctly re-derived all the facts
independently and returned a short verdict (`"VALIDATED: All claims in the
draft plan are confirmed..."`). `orchestrator` then called `response_agent`
passing *only that one-line verdict* as `validated_plan` -- not the actual
plan content. `response_agent`, given almost nothing to reformat, fabricated
an entirely different, fictional issue (a nonexistent "issue #456" about
database concurrency, citing files and a design doc that don't exist
anywhere in this project) rather than reporting that it had insufficient
input.

**Root cause:** `orchestrator`'s instructions said to send "the validated
plan" to `response_agent` without being explicit that this meant the full
draft plan text *plus* the verdict -- not the verdict alone. The model's
interpretation was reasonable given the ambiguity; the instruction was the
bug, not the model.

**The fix (now in this repo):**
1. `orchestrator`'s instructions now explicitly require passing
   `planner_agent`'s full draft plan text *and* `validation_agent`'s verdict
   together to `response_agent`, and explicitly forbid sending the verdict
   alone.
2. `response_agent` now has an explicit safeguard: if it ever receives a
   `validated_plan` that doesn't actually contain plan content, it must say
   so plainly rather than invent anything to fill the gap.

This is the kind of failure that's easy to miss if you only read the HOCON
and never run a live query -- the instructions looked reasonable on paper.
It's also a good illustration of why `validation_agent` existing isn't
enough on its own: a correct validation step can still be undermined by a
later hop that drops the content it validated. Anyone reviewing this repo
should feel free to try reproducing it by asking a similarly worded query
and checking the Internal Chat tab in nsflow for the exact `validated_plan`
argument passed to `response_agent`.

**A second, smaller finding from the same live-testing pass:** `ListRelatedFilesTool`
takes no real arguments, so its HOCON schema originally declared an empty
`"properties": {}`. Mistral's function-calling API rejected that as an
invalid tool schema at call time. Fixed by adding one harmless, optional,
unused `reason` property so the schema is never empty -- the tool's own
`invoke()` ignores it entirely. Worth knowing if you add more no-argument
tools later.

**A third finding, and the most interesting one:** after the two fixes
above, a live run correctly triggered the `response_agent` safeguard
itself -- it refused to present an answer, saying validation had flagged
"documentation files that do not appear to exist in the indexed codebase."
That sounded like `planner_agent` hallucinating a doc file name, but the
real cause was narrower and more subtle: `ReadFileTool` and
`ListRelatedFilesTool` only ever looked inside `data/sample_repo/` --
they had no way to see `data/docs/` at all. So when `validation_agent`
tried to verify a real, existing documentation file (e.g.
`authentication_flow.md`) that the plan correctly referenced, `ReadFileTool`
reported "not found" purely because it was looking in the wrong directory,
not because the file didn't exist. `validation_agent` correctly flagged
what looked like an unsupported claim, and `response_agent`'s safeguard
correctly refused to present it -- the *system* behaved exactly as
designed given the information it had; the bug was that one tool's scope
was narrower than the domain it was being asked to verify.

**Fix:** `ReadFileTool` now checks both `data/sample_repo/` and
`data/docs/` (trying source code first, then documentation), and
`ListRelatedFilesTool` now returns `code_files` and `doc_files` separately
covering both. This is arguably the most instructive of the three bugs:
it's a reminder that a "no hallucination" safeguard is only as good as the
tools backing it -- if a verification tool can't see the whole relevant
data surface, it will produce false negatives that look identical to real
hallucinations from the outside, and it takes checking the tool's actual
scope (not just the agent's tool list) to tell the difference.

## Future improvements

- Swap `keyword_search()` in `data_access.py` for a real embeddings index
  (FAISS/Chroma + sentence-transformers), for semantic rather than
  literal-keyword matching -- the interface (`query -> ranked file matches
  with snippets`) is already the shape a vector search would return.
- Point `github_tools.py` at the real GitHub REST API (or PyGithub) instead
  of local JSON, gated behind a feature flag so the local-mock path still
  works for offline testing.
- Extend `planner_agent`'s output into an actual patch/diff (still with a
  human-approval gate before anything is applied), rather than stopping at
  a text plan.
- Add a lightweight relevance-score threshold to `keyword_search()` so very
  weak matches (score of 1 on a long file) don't get reported as evidence.
