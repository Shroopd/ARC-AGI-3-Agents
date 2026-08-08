# ARC-AGI-3-Agents: Clean up pre-commit + devcontainer (no codebase restart)

## Goal

Get the current repo into a clean, GPU-ready state for writing and running torch/ARC code in a devcontainer, **without** restarting onto current upstream `main`. Keep the current fork-based `main` (at `6544461`) as-is and apply all cleanups in place.

## Unified vision (north star — why the pieces fit together)

This repo exists to be a place where **you write and run your own non-LLM torch/ARC game agents** in a GPU-capable devcontainer. Turning that into one coherent end-state means every task below serves one of five pillars:

1. **Keep a lean base, don't restart** — the LLM templates are already deleted and merged into your `main`; re-basing on upstream adds only merge-drag, not value.
2. **Product is non-LLM, but dev tooling may be LLM** — strip every LLM artifact from the *game-agent* code/docs/env; keep the *development* loop's LLM infrastructure (spark1 host, `.config/kilo`) because that's how *you* develop. This tension is intentional, not a contradiction.
3. **Right tooling for the work** — pyright (same engine as Pylance) + ruff + pre-commit, so the editor, the commit gate, and the type-checker agree on how you write code.
4. **GPU-ready devcontainer** — Debian/CUDA-13 torch matching your host driver, `--gpus all`, cached UV, so running torch locally "just works."
5. **A working regression guard** — pytest kept and fixed against the real `arc_agi`/`arcengine` API, so removing the LLM cruft doesn't silently break things.

If a given edit doesn't advance at least one of these pillars, it's out of scope (see "Out of scope"). Every task in this plan maps to one or more of the five.

## Why no restart (context)

- The prior plan assumed a restart onto current upstream was needed, hinging on "your branch is 11 commits that delete upstream's ~5,700 LLM template lines."
- Those deletions are **already committed and merged into current `main`** (`60ad314`, `70fb485`). `pyproject.toml` already matches the target runtime set (`arc-agi, dotenv, numpy, pillow, pydantic, requests, torch, torchvision`). LLM deps are already pruned.
- Therefore the restart buys only: (a) future `git merge upstream/main` ergonomics (avoiding re-fighting LLM-template deletions on every sync), and (b) cosmetic history rewriting. For a repo whose product is "own agents + torch + GPU," upstream merges will be rare and low-value.
- **Accepted tradeoff:** future upstream syncs will re-introduce the LLM template deletions and their deps, requiring re-resolution. This is a conscious acceptance; upstream template code is not wanted.
- `main` currently shows uncommitted/untracked items to reconcile (see Task 1).

## Preserve first (do not lose)

- `AI_experiments` submodule (shows "new commits" — decide whether to bump the pinned SHA).
- Any `.kilo/plans` notes.
- Do **not** preserve `agents/templates/random_agent_copy.py` in its current form: it is byte-for-byte identical to the tracked `agents/templates/random_agent.py` (verified by SHA-256). It is scratch; **delete** it in Task 1 rather than commit it as a duplicate.

## Facts from current tree

- `pre-commit-config.yaml`: ruff + ruff-format (keep) and a mypy hook (remove).
- `pyproject.toml`: `[tool.mypy]` strict block exists; dev group has `mypy, pre-commit, pytest, pytest-asyncio, requests-mock, ruff`; **no** pyright; **no** `[project.optional-dependencies]` (extras). `arcengine` is imported directly by app code but only declared transitively via `arc-agi`.
- Kept tests use **no `async`/`asyncio` and no `requests_mock`** (verified by grep across `tests/`) — `pytest-asyncio` and `requests-mock` are unused dev deps and should be dropped.
- **App code migrated to the `arc_agi`/`arcengine` packages** (`arc_agi` depends on `arcengine` transitively). `agents/agent.py`, `agents/swarm.py`, `agents/templates/random_agent.py`, `agents/templates/_game_utils/vision.py`, and `tests/conftest.py` all import from `arcengine`/`arc_agi`.
- **`agents/structs.py` was deleted** in commit `b06c432` ("Updating to use the new arg-agi toolkit"). Its symbols moved: `ActionInput`, `FrameData`, `FrameDataRaw`, `GameAction`, `GameState` are in `arcengine`; `Card`, `Scorecard` are in `arc_agi.scorecard` (probed). `Card`'s field set changed (`scores`/`score`/`high_score`/`idx` removed/replaced), which affects `test_core.py`.
- **Tests are currently BROKEN as committed:** `tests/unit/test_core.py:3` and `tests/unit/test_swarm.py:6` still `import` from `agents.structs`, which no longer exists — the suite fails at collection. `tests/unit/test_recorder.py` imports only `agents.recorder` and is unaffected. This is a deciding factor for the pytest/dependency question (see Task 2 and Task 4).
- **AgentOps tracing is dead weight.** `agentops` is **not** a dependency, so `agents/tracing.py` always falls into `NoOpAgentOps`. Still wired into: `agents/agent.py:14,38-39,68` (`trace_agent_session`, `trace: Any`, decorator on `main`), `main.py:21,179-180` (`init_agentops`), plus `agents/tracing.py` itself (~143 lines). README "Observability" section and `.env.example` `AGENTOPS_API_KEY`/`OPENAI_API_KEY`/`OPENCLAW_*` vars serve the removed LLM agents.
- **Confirmed discard:** `agents/templates/_game_utils/schema.py` and `prompts.py` are LLM-only utilities (nothing imports them; `prompts.py` imports `schema.Observation`). Keep `_game_utils/vision.py` (intentionally preserved for non-LLM agents; imports `numpy`/`PIL`/`arcengine`).
- `tests/conftest.py:64-65` still sets an `OPENAI_API_KEY` test env var (LLM remnant).
- Devcontainer base: **Rocky 9** with EPEL/CRB + `python3.13` ensurepip hacks — replace with Debian-family.
- Stale `__pycache__` artifacts remain from deleted modules.

## Policy notes (from user)

- **No LLM usage except dev agents.** LLM ecosystem (agentops, openai, langchain/langgraph, smolagents, openclaw) is permanently removed; remove all dead tails, docs, and env vars referencing them.
- **spark is for development agents, not game agents.** Keep the `--add-host spark1:...` runtime arg in the devcontainer — the dev-agent loop needs it. Do not conflate it with the outbound game server (`three.arcprize.org`, resolved from `.env`). It is not needed by game agents.
- **`.config/kilo` bind mount = dev-agent loop.** Keep it (optionally narrow to just the kilo subtree).

## Execution: ordered stages + handoff

The host (this environment) **cannot interact with the inside of the devcontainer**, and `uv` is not installed on the host. Execution is therefore a three-stage pipeline. **Handoff vehicle:** all host edits live in the repo working tree, which the container sees via the bind mount — **no `git commit` is required** for handoff (only commit if the user explicitly asks).

### Stage A — Host: file edits (Tasks 1, 1b, 2-edits, 3, 4)
- Perform all source/config edits listed in Tasks 1-4. Do **not** run `uv`/`pytest`/GPU commands on the host (no in-container access; Windows has no Linux-NVIDIA runtime).
- **Exception — do NOT touch `uv.lock` on the host.** Task 2's "regenerate `uv lock`" and Task 4's "run `uv lock`/`uv sync --frozen`" are **in-container steps only**. Editing `pyproject.toml` without regenerating the lock is expected and correct at this stage.
- **Test edits are best-effort here.** Use the probed mapping to write the corrected imports and `TestCard`/`TestScorecard` assertions, but treat them as provisional. Stage C is the authority that validates and finalizes them against the locked arcengine/arc_agi API.
- **Stage A done when:** all Task 1-4 edits are made; static checks in Task 5(A) pass; no `uv.lock` touch.

### Stage B — Rebuild the container from `.devcontainer/`
- User/facilitator rebuilds the devcontainer (host sidebar, "Rebuild Container"). Not an agent code step; it surfaces the Stage A edits into the container.

### Stage C — In-container agent: validation + finalize (Task 5)
- A **separate agent launched from inside the container** executes the runbook below. It must open `.kilo/plans/1785988849331-cleanup-precommit-devcontainer.md` for context.
- **Stage C done when:** every runbook item succeeds and reported. Failing items must be fixed in place and re-run before reporting done — a red/failing-collection suite or a hidden GPU is a blocking defect, not a stopping point.

### Stage C runbook (copy in order)
```bash
# 1. Reconcile the host's pyproject.toml edits into the lockfile (host could not run uv).
uv lock
# 2. Sync frozen from the regenerated lock (validates arcengine direct dep, mypy removed, pytest-asyncio/requests-mock dropped).
uv sync --frozen
# 3. Verify no stray LLM/tracing imports remain.
uv run python -c "import main; import agents, agents.agent, agents.swarm, agents.templates.random_agent"
# 4. Confirm locked arcengine/arc_agi API; adjust test_core.py/test_swarm.py to locked reality if the host probe drifted.
uv run python -c "from arcengine import ActionInput, FrameData, GameAction, GameState; from arc_agi.scorecard import Card, Scorecard"
# 5. Install + run the commit gate.
uv run pre-commit install
uv run pre-commit run --all-files
# 6. Run the suite (recordings auto-cleaned by conftest).
uv run pytest
# 7. GPU checks as the non-root user.
nvidia-smi
uv run python -c "import torch; print(torch.cuda.is_available(), torch.version.cuda)"
# 8. Dev-agent loop still reads kilo config; spark1 reachable.
getent hosts spark1
```
- `uv lock` runs first (not `--frozen`) to bring `uv.lock` in line with the edited `pyproject.toml`; only then does `uv sync --frozen` apply.

### Verified test-rewrite API mapping (probed via pip install of `arcengine`/`arc-agi`)

- `arcengine` exports: `ActionInput`, `FrameData`, `FrameDataRaw`, `GameAction`, `GameState` (plus others). These are the import targets for most of `test_core.py`.
- `arc_agi.scorecard` exports: `Card`, `Scorecard`, `EnvironmentScorecard`. **`Card` and `Scorecard` do NOT live in `arcengine`.**
- **Not a pure 1:1 name swap — `Card`'s API changed.** New `Card` fields are `game_id, total_plays, guids, levels_completed, states, actions, actions_by_level, resets` with a computed `total_actions`. It no longer has old-structs fields like `score`/`high_score`/`idx`/`scores`. `Scorecard` gained many methods; `get`, `get_json_for`, `won`, `played` still exist. `ActionInput(id, data, reasoning)` and `GameState(NOT_PLAYED, NOT_FINISHED, WIN, GAME_OVER)` are unchanged.
- Consequence: fixing the test suite is **more than an import-line swap** for `TestCard`/`TestScorecard` in `test_core.py` — assertions on removed fields (`score`, `high_score`, `idx`) must be rewritten against the real `Card`/`Scorecard` API, verified at runtime. See Task 2.
- Note: the host pip probe resolved newest versions (arc-agi 0.9.9 / arcengine 0.9.3). The repo lock pins arc-agi 0.9.1 / arcengine 0.9.3. Exact field names may drift slightly between these; treat the probe as strong guidance and re-confirm field names against the **locked** versions in-container during Task 2/5.

---

## Task list

### 1. Tidy current working tree (git hygiene)

- **Delete** `agents/templates/random_agent_copy.py` (verified identical to tracked `random_agent.py`; scratch, no unique content). Do not commit it.
- Reconcile `AI_experiments` submodule "new commits": either bump the pinned commit in `main`, or leave and note the drift. Do not silently discard.
- Sweep stale `__pycache__` for deleted modules under `agents/` and `agents/templates/`: `langgraph_functional_agent`, `llm_agents`, `multimodal`, `smolagents`, `reasoning_agent`, `structs` `.pyc` files. Confirm `__pycache__` is gitignored; these are only a filesystem-cleanliness matter, not tracked content.

### 1b. Remove LLM-ecosystem dead tails (AgentOps, docs, env, utils)

- **Delete `agents/tracing.py`** (~143 lines, AgentOps-only; always a no-op now).
- **Strip AgentOps from `agents/agent.py`:** remove `from .tracing import trace_agent_session`, the `@trace_agent_session` decorator on `main()` (line 68), the `# AgentOps tracing attributes` comment + `trace: Any = None` (38-39), and the now-unneeded `from typing import ... Any`/`Optional` imports if they become unused.
- **Strip AgentOps from `main.py`:** remove `from agents.tracing import initialize as init_agentops` (line 21), the `# Initialize AgentOps client` comment, and the `init_agentops(...)` call (179-180). Nothing else in `main.py` references AgentOps.
- **Delete LLM-only game utils:** `agents/templates/_game_utils/schema.py` and `agents/templates/_game_utils/prompts.py` (user-confirmed discard). Keep `_game_utils/vision.py`.
- **`.env.example`:** remove `OPENAI_API_KEY` (23-24), `AGENTOPS_API_KEY` (29-30), and the entire `OPENCLAW_*` block (32-48). Delete now-unreached blank lines.
- **`README.md`:** delete the "Observability" section (lines 57-103, AgentOps/OpenClaw/custom-agent tracing). It references `uv sync --extra agentops`, which has no extras target. Fix Quickstart/contributing wording only as needed to stay accurate.
- **`llms.md` (tracked, stale):** it duplicates README but its "Agent System" section names the deleted `agents/structs.py` (line 99), its "Observability" section (36-54) documents the non-existent `agentops` extra, and its "Agent Templates" section (107-108) lists removed LLM templates. Remove the agentops/LLM/structs content and align the rest with the retained random-agent-only tree. (Do not replace the whole README; this is the agent-context doc.)
- **`tests/conftest.py`:** remove the `OPENAI_API_KEY` monkeypatch (lines 64-65); keep the other env defaults (ARC_API_KEY, SCHEME, HOST, PORT).

### 2. Tooling: replace mypy with pyright (editor/commit parity)

`pyproject.toml`:
- Remove from `[dependency-groups].dev`: `mypy`.
- Add `pyright` (latest).
- Delete the `[tool.mypy]` block.
- Add `[tool.pyright]`:
  - `pythonVersion = "3.13"`
  - point at the real `.venv` (e.g. `venvPath`/`venv`) so pre-commit resolves the true environment
  - `typeCheckingMode = "standard"` (start standard; ratchet to strict only if the torch/numpy code tolerates it).
- **Do NOT run `uv lock` here (host can't).** Lock re-resolution happens in Stage C runbook step 1.

**Decision: Option A — fix the broken tests, keep pytest.** Because `test_core.py:3` and `test_swarm.py:6` import the deleted `agents.structs`, the suite currently fails at collection. Rewriting these imports is in scope; pytest is retained.

- Only the two test files touch `agents.structs`; no app code does (verified by grep).
- Rewrite the import lines using the **probed mapping** (see "Verified test-rewrite API mapping"):
  - `test_core.py:3` — `ActionInput, FrameData, GameAction, GameState` from `arcengine`; `Card, Scorecard` from `arc_agi.scorecard`.
  - `test_swarm.py:6` — `GameState` from `arcengine`; `Card, Scorecard` from `arc_agi.scorecard`.
- **`TestCard` / `TestScorecard` assertions must be rewritten, not just imports.** Re-confirm `Card`'s current fields against the **locked** arcengine 0.9.3 (probe says `levels_completed`, `actions_by_level` replaced `scores`/`score`; `high_score`/`idx` are gone). Map each assertion to the real API; if a behavior genuinely no longer exists, assert against `arcengine`/`arc_agi`'s actual semantics (e.g. use `total_actions` computed field) rather than re-creating `agents.structs`.
- **Other cases are near-1:1:** `ActionInput(id, data, reasoning)`, `GameState`, `FrameData`, `GameAction` were probed as unchanged; `Scorecard.get/get_json_for/won/played` still exist.
- **Ownership:** the host (Stage A) writes a best-effort probe-based version of these test edits. The **Stage C in-container agent is the authority** — it must re-verify against the locked arcengine/arc_agi (the host probe used possibly-newer arc-agi 0.9.9; the lock pins 0.9.1) and adjust `test_core.py`/`test_swarm.py` before `pytest` counts as green. There is no conflict: Stage A edits are provisional input; Stage C finalizes.
- Do not re-add `agents/structs.py`; the goal is to align tests with the migrated packages.
- Keep `pytest` and `conftest`'s recordings fixtures in the dev group; `pytest-asyncio`/`requests-mock` are dropped (unused by tests).

`.pre-commit-config.yaml`:
- Keep `ruff` + `ruff-format` hooks as-is.
- **Remove** the `mirrors-mypy` hook block.
- **Add** a `pyright` hook (e.g. `RobertCraigie/pyright-pre-commit`). Configure the same venv/python-version settings as `[tool.pyright]` so the isolated pre-commit env does not emit false stub errors.

### 3. Devcontainer base image → Debian-family + GPU

`.devcontainer/Dockerfile`:
- Replace `FROM rockylinux:9` with a Debian-family Python 3.13 base image.
- Delete the EPEL/CRB enable, `dnf` `--allowerasing` install of `python3.13`, and the `ensurepip` bootstrap.
- Keep: non-root `vscode` user + sudo, `uv` install, `ENV UV_LINK_MODE=copy`, `WORKDIR`.

`.devcontainer/devcontainer.json`:
- Add `--gpus all` to `runArgs`; keep `SYS_PTRACE` + `seccomp=unconfined`.
- Add the `nvidia-cuda` devcontainer feature at **CUDA 13** — this matches the locked torch 2.13.0 (which resolves CUDA-13 wheels from the default PyPI index: `cuda-toolkit`, `nvidia-cudnn-cu13`, `nvidia-nccl-cu13`, etc.) and the host NVIDIA driver (CUDA 13.1.1 on the Windows host).
- **Do NOT switch torch to a `cu126`/`cu128` index** — the default PyPI torch build is already CUDA 13-aligned with the host, so no `uv.toml` index override and no `uv.lock` re-resolution are needed. Confirm this only if the host driver were older (it is not, per user: CUDA 13.1.1).
- Python 3.13 + torch 2.13.0: verified compatible in the lock (`cp313` manylinux wheels exist for torch 2.13.0 and torchvision 0.28.0).
- Add a named **cache volume** (e.g. `devcontainer-uv-cache`) mounted at uv's cache dir so torch is not re-downloaded on rebuild.
- `postCreateCommand`: `uv sync --frozen` + `pre-commit install`.
- **Remove** `ms-python.pylint` from extensions (ruff + pyright supersede it).
- **Keep `--add-host spark1:10.13.54.178`** — it is required for the **development agent** loop, not game agents (per user policy). Do not remove it.
- **Keep the `.config` bind mount** — it serves the dev-agent loop. Optionally narrow it to just the kilo subtree (`${HOME}/.config/kilo`) rather than the whole `${HOME}/.config`; do not delete outright. **Note the existing source is `"${env:HOME}${env:USERPROFILE}/.config"`** — a concatenation of the shell `HOME` and `USERPROFILE` that is malformed in-container; correct it to point at the real host path (e.g. `${env:USERPROFILE}/.config` or the WSL home) while implementing. Confirm with a live rebuild that the dev-agent loop still reads kilo config.
- The outbound game server (`three.arcprize.org`) is configured via `.env`, not the devcontainer; no `--add-host` needed for it.
- Review any `forwardPorts`; likely unnecessary since the app is outbound.

### 4. Dependency cleanup

- Runtime deps are final: `arc-agi, dotenv, numpy, pillow, pydantic, requests, torch, torchvision`. **Declare `arcengine` as a direct dependency** (pinned/constrained to match `arc-agi`'s own `arcengine` requirement, currently 0.9.3) — app code imports it first-class in `agents/agent.py`, `agents/templates/random_agent.py`, `agents/templates/_game_utils/vision.py`, and `tests/conftest.py`, so relying on it only transitively is fragile under pyright/ruff and future resolves. Do not add `openai/anthropic/langchain/langgraph/langsmith/smolagents/agentops`.
- Ensure stale LLM-ecosystem packages (`openai/anthropic/langchain/langgraph/langsmith/smolagents/agentops`) are absent from `uv.lock`; run `uv lock`/`uv sync --frozen` to verify a clean resolve (happens automatically once tests are fixed — see Task 2).
- Dev group after cleanup: `pyright`, `ruff`, `pre-commit`, `pytest`. **Drop `pytest-asyncio` and `requests-mock`** — verified unused by the kept tests (no `async`, no `asyncio`, no `requests_mock` usage anywhere in `tests/`). Keep `pytest` per the Option A decision.
- **`.gitignore` updates:** remove `.mypy_cache/` (mypy eliminated); add `.venv/`, `.pytest_cache/`, `.pyright/` (or `.pyright` cache) to match the new toolchain. Keep `.ruff_cache/`, `*.env`, etc.
- Keep `uv.lock` tracked.

### 5. Validation

**Stage A — host-side (static only; do not attempt container/runtime commands here):**
- Confirm the `.devcontainer/devcontainer.json` edits are syntactically valid JSON (e.g. `python -m json.tool`) and that `pyproject.toml`/`.pre-commit-config.yaml` are well-formed (parse at least).
- Confirm no remaining references to `agents.tracing`, `agentops`, `agents.structs`, `schema`, `prompts`, `pytest_asyncio`, or `requests_mock` across `agents/`, `main.py`, and `tests/` (grep).
- Confirm no tracked file references the deleted `agents/templates/random_agent_copy.py`.
- **Do NOT run `uv`, `pytest`, or GPU checks on the host.**

**Stage C — in-container agent (acceptance gate; execute the Stage C runbook in "Execution: ordered stages + handoff"):**
- Runbook steps 1-8 (reproduced above) all succeed: `uv lock` → `uv sync --frozen` → import check → API re-verify → `pre-commit run --all-files` (ruff + pyright only, no false stub errors) → `uv run pytest` green → `nvidia-smi` + `torch.cuda.is_available()` + `torch.version.cuda` = CUDA 13.x → `spark1` reachable / kilo config read.
- The rewritten `TestCard`/`TestScorecard` assertions match the **locked** arcengine/arc_agi API (fix any drift from the host probe).
- A failing-collection suite is a blocking defect; the agent must fix and re-run before reporting done.

## Risks / notes

- **Pyright standard-vs-strict:** start at standard. Mypy-strict ≠ pyright-strict; strict pyright is harsher on torch/numpy. Ratchet only if code tolerates it.
- **Pyright pre-commit gotcha:** must be given the real `.venv` + Python version or it fails on stubs Pylance never reports.
- **CUDA alignment is already correct** (torch 2.13.0 = cu13 from PyPI; host driver = CUDA 13.1.1), reducing GPU risk. Still verify `nvidia-smi` + `torch.cuda.is_available()` + `torch.version.cuda` as non-root before assuming GPU works — the main remaining risk is the Docker Desktop / NVIDIA Container Toolkit plumbing, not a version mismatch.
- **Future upstream merges** will re-introduce LLM template deletions/deps (accepted cost of not restarting).

## Out of scope

- Restarting/reset onto upstream `main`.
- Rewriting git history of the 11 deletion commits.
- Any functional changes to `agents/` or `main.py` beyond the AgentOps/hook cleanup specified above (no new agent logic, no game behavior changes).
- Deleting `_game_utils/vision.py` (kept intentionally for non-LLM agents).
- Removing the spark1 `--add-host` or the `.config/kilo` mount (both needed for the dev-agent loop).
- Re-adding `forwardPorts`/host-IP config unless later needed.

## Resolved decisions

- **No codebase restart.** Apply cleanups in place on current `main` (`6544461`).
- **Broken tests → Option A (fix them, keep pytest).** `test_core.py` and `test_swarm.py` get their `agents.structs` imports rewritten (`arcengine` for frames/actions/state + `ActionInput`; `arc_agi.scorecard` for `Card`/`Scorecard`); `TestCard`/`TestScorecard` assertions rewritten to the real API. pytest and friends stay in the dev group.
- **Execution = 3 ordered stages (A host edits → B rebuild → C in-container validate/finalize),** with a copy-paste Stage C runbook in "Execution: ordered stages + handoff." `uv lock` is in-container only (host can't run uv). Test edits: host provisional → in-container authority. No commit required for handoff.
- **`random_agent_copy.py` is scratch** (byte-identical to `random_agent.py`) → delete, don't commit.
- **mypy → pyright**, `typeCheckingMode = "standard"`; **pylint** extension dropped.
- **Remove AgentOps tracing entirely (Option A).** Delete `agents/tracing.py`; strip `trace_agent_session`/`trace`/`init_agentops` from `agent.py` + `main.py`; remove AgentOps docs, env vars, and the `OPENAI_API_KEY`/`OPENCLAW` leftovers. LLM is never returning except for dev work.
- **Delete LLM-only game utils** `schema.py` + `prompts.py`; keep `vision.py`.
- **Keep spark1 `--add-host` and the `.config/kilo` mount** — both serve the development-agent loop, not game agents.
- **Dependency shrinks:** `arcengine` promoted from transitive to direct runtime dep; `pytest-asyncio` + `requests-mock` dropped from dev group (unused by kept tests); `mypy` removed.
- **GPU/CUDA = CUDA 13, keep default PyPI torch.** Locked torch 2.13.0 resolves cu13 wheels; host driver supports CUDA 13.1.1. `nvidia-cuda` feature at CUDA 13. No `download.pytorch.org` index override, no lock re-resolution.

## Open questions for implementation

1. **Pyright `typeCheckingMode`:** start at **standard** (recommended). Only escalate to strict if pyright-standard passes clean and a maintained strict bar is wanted. **CUDA/torch flavor is resolved (CUDA 13, default PyPI)** and needs no further decision.
2. **Mypy-specific `# type: ignore` comments** in `random_agent.py`, `agent.py`, and `swarm.py` (e.g. `type: ignore[attr-defined,unused-ignore]`, `no-any-return`): these reference mypy error codes that pyright/ruff don't use. After the tooling swap, verify they don't become stray/false-ignore comments and clean them up if so.
3. **`Card`/`Scorecard` field drift between probe (arc-agi 0.9.9 / arcengine 0.9.3) and locked (arc-agi 0.9.1 / arcengine 0.9.3).** The in-container agent must re-verify the exact `Card`/`Scorecard` fields against the locked 0.9.x before finalizing `test_core.py` edits. Use `git show b06c432~1:agents/structs.py` as the behavior reference; do not resurrect `agents.structs`.
4. **`.config` bind mount source path:** the current `"${env:HOME}${env:USERPROFILE}/.config"` concatenation is malformed in-container. Correct the host path and optionally narrow to the kilo subtree. Default: fix the path, keep the full `.config` unless narrowing is trivial and safe (the dev-agent loop must keep working).

> Handoff is now fully specified in "Execution: ordered stages + handoff" (Stages A/B/C + the Stage C runbook); it is no longer an open question.
