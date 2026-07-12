# Dead Import Removal Plan — Dead Import Chase Results

## Removed Packages
- `langchain[openai]` → imports: `langchain_core.*`, `langchain_openai.*`
- `langgraph>=0.6.3` + `langgraph-checkpoint-sqlite` → imports: `langgraph.*` (submodules: graph, pregel, store.sqlite, config, checkpoint.memory, func)
- `langsmith` → imports: `langsmith`, `langsmith.schemas.Attachment` (removed before last commit, but dead imports remain)

---

## Depth 1 — Direct Dead Imports

### Affected Files and Dead Imports

| # | File | Dead Imports |
|---|------|-------------|
| 1 | `agents/__init__.py` | L8: `from .templates.langgraph_functional_agent import LangGraphFunc, LangGraphTextOnly`; L9: `from .templates.langgraph_random_agent import LangGraphRandom`; L10: `from .templates.langgraph_thinking import LangGraphThinking`; L36-39: `__all__` entries for these 4 classes |
| 2 | `agents/templates/langgraph_thinking/__init__.py` | L1: `from .agent import LangGraphThinking` (re-export) |
| 3 | `agents/templates/langgraph_thinking/agent.py` | L5: `from langgraph.graph import END, START, StateGraph`; L6: `from langgraph.pregel import Pregel`; L7: `from langgraph.store.sqlite import SqliteStore` |
| 4 | `agents/templates/langgraph_thinking/llm.py` | L1: `from langchain_core.language_models import BaseChatModel`; L2: `from langchain_openai import ChatOpenAI` |
| 5 | `agents/templates/langgraph_thinking/nodes.py` | L8: `from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage`; L9: `from langgraph.config import get_store` |
| 6 | `agents/templates/langgraph_thinking/schema.py` | L5: `from langchain_core.messages import BaseMessage` |
| 7 | `agents/templates/langgraph_thinking/tools.py` | L6: `from langchain_core.tools import tool`; L7: `from langgraph.config import get_store` |
| 8 | `agents/templates/langgraph_random_agent.py` | L6: `from langgraph.graph import END, START, StateGraph`; L7: `from langgraph.pregel import Pregel` |
| 9 | `agents/templates/langgraph_functional_agent.py` | L10: `import langsmith as ls`; L13: `from langgraph.checkpoint.memory import InMemorySaver`; L14: `from langgraph.func import entrypoint`; L15: `from langgraph.pregel import Pregel`; L16: `from langsmith.schemas import Attachment` |
| 10 | `tests/unit/test_core.py` | L11: `from agents.templates.langgraph_random_agent import LangGraphRandom`; L249: `assert "langgraphrandom" in name.lower()` within `TestLangGraphRandomAgent` class |

### Categorization (Depth 1)

#### A. Fully Dependent — Mark for Removal (no salvageable code)
1. **`agents/templates/langgraph_thinking/__init__.py`** — Re-export shim. Remove entirely.
2. **`agents/templates/langgraph_thinking/llm.py`** — Factory returning langchain types. Remove entirely.
3. **`agents/templates/langgraph_thinking/tools.py`** — All 4 tools use `@tool` + `get_store()`. Remove entirely.
4. **`agents/templates/langgraph_thinking/agent.py`** — Entire `LangGraphThinking` class uses `StateGraph`, `Pregel`, `SqliteStore`. Remove entirely.
5. **`agents/templates/langgraph_thinking/nodes.py`** — All 5 node functions use `langchain_core.messages` and `get_store()`. Remove entirely.
6. **`agents/templates/langgraph_random_agent.py`** — Entire `LangGraphRandom` class uses `StateGraph`, `Pregel`. Remove entirely.

#### B. Fully Independent — Mark for Preservation (no changes needed)
7. **`agents/templates/langgraph_thinking/prompts.py`** — Pure string-building functions. Imports `Observation` from `.schema` (preserved). No dead imports.
8. **`agents/templates/langgraph_thinking/vision.py`** — Frame rendering utilities (PIL + numpy). No dead imports.

#### C. Partially Dependent — Mark for Investigation
9. **`agents/templates/langgraph_thinking/schema.py`** — Dead import `BaseMessage` (L5) used only in `AgentState.context` type annotation (L17). The `LLM` enum, `KeyCheck`, and `Observation` TypedDicts are independent. **Action**: Remove `BaseMessage` import, change `context: list[BaseMessage]` to `context: list[Any]` (add `Any` to typing imports).

10. **`agents/templates/langgraph_functional_agent.py`** — Mixed content:
    - **Dead/remove**: `build_agent()` (L47-120), `LangGraphFunc` class (L126-173), `LangGraphTextOnly` class (L176-177), imports L10+L13-16, docstring L1
    - **Independent/preserve**: `g2im()` (L225-261)
    - **Needs stripping**: `format_frame()` (L180-222) — else branch (L190-195) uses `ls.get_current_run_tree()` and `Attachment`. Strip those lines.
    - **Action**: Strip dead imports and code. Keep `format_frame()` and `g2im()`. Remove the `from agents.templates.llm_agents import LLM` line since only `LangGraphFunc` used it. The remaining imports (`base64`, `io`, `json`, `Any` from typing, `FrameData` from arcengine, `ChatCompletionMessage` from openai) are all alive.

11. **`agents/__init__.py`** — Lines 8-10 import from removed modules. Lines 36-39 are dead `__all__` entries. **Action**: Remove L8-10 and the 4 `__all__` strings. `AVAILABLE_AGENTS` dict uses `Agent.__subclasses__()` which auto-discovers — no change needed.

12. **`tests/unit/test_core.py`** — Line 11 imports `LangGraphRandom`. `TestLangGraphRandomAgent` class (L229-281). **Action**: Remove L11 and the entire test class (L229-281).

---

## Depth 2 — Knock-on Effects from Depth 1 Removals

After removing files marked A and applying changes to C files in Depth 1:

### New Dead Imports (from now-removed modules)

| # | File | Dead Import | Reason |
|---|------|-------------|--------|
| 1 | `agents/__init__.py` | L8-10: imports from `.templates.langgraph_*` | Those modules removed in Depth 1 |
| 2 | `tests/unit/test_core.py` | L11: `from agents.templates.langgraph_random_agent import LangGraphRandom` | Module removed in Depth 1 |

**Status**: Already handled in Depth 1 Category C actions. No new files surface.

### Categorization (Depth 2)

#### A. Fully Dependent — Mark for Removal
*(none new)*

#### B. Fully Independent — Mark for Preservation
*(none new)*

#### C. Partially Dependent — Mark for Investigation
*(none new)*

---

## Depth 3 — Knock-on Effects from Depth 2 Removals

No knock-on effects remain. All cascading dead imports are contained.

---

## Resolved Design Decisions

1. **Preserved functions location**: `format_frame()` and `g2im()` → merge into `agents/templates/_game_utils/vision.py`. After merge, delete `agents/templates/langgraph_functional_agent.py` entirely (no remaining content).
2. **Directory rename**: `agents/templates/langgraph_thinking/` → `agents/templates/_game_utils/` (underscore prefix signals internal/private utilities). Move `prompts.py`, `schema.py`, and the now-merged `vision.py` into the new directory.
3. **Pre-existing `agents.structs` issue**: leave alone in `test_core.py`. Only remove the dead LangGraphRandom import and test class.

---

## Open Design Decisions

### Decision 1: Where to place preserved `format_frame()` and `g2im()` functions
After stripping `langgraph_functional_agent.py`, `format_frame()` and `g2im()` are game-frame-to-image utilities. `vision.py` already has similar utilities (`render_frame()`).

**Options:**
- **A**: Append `g2im()` and `format_frame()` to `vision.py` — consolidates all frame-rendering utilities in one place.
- **B**: Keep them in a renamed file (e.g., `agents/templates/_frame_utils.py`) — keeps concerns separate.
- **C**: Leave them in `langgraph_functional_agent.py` stripped of dead code — name becomes misleading.

**Recommendation**: **Option A** — `vision.py` is the natural home for frame-rendering utilities. Both functions are general-purpose grid-to-image converters.

### Decision 2: What to do with `langgraph_thinking/` directory after removing 5 of 7 files
After removals, the directory contains `prompts.py`, `vision.py`, and `schema.py`. No `__init__.py` (removed). The name "langgraph_thinking" is now misleading.

**Options:**
- **A**: Keep directory as implicit namespace package (no `__init__.py`), rename to something like `_game_utils/`.
- **B**: Keep directory as-is without `__init__.py` — Python 3.3+ implicit namespace packages allow `from agents.templates.langgraph_thinking.prompts import ...` to still work.
- **C**: Keep directory, add a minimal `__init__.py` that exports preserved public API.

**Recommendation**: **Option B** — simplest. No `__init__.py` needed; implicit namespace packages work. The name is cosmetic; the user can rename later. If they prefer, **Option A** (rename to `_game_utils/`) is also clean.

### Decision 3: Pre-existing `agents.structs` test breakage
Both `tests/unit/test_core.py` (L3-10) and `tests/unit/test_swarm.py` (L6) import from the non-existent `agents.structs` module. This is a pre-existing issue unrelated to the langchain/langgraph removal. The `structs.py` file was removed when the codebase migrated to `arcengine` (see git history: commit `b06c432`). The tests were not updated.

**Options:**
- **In scope**: Fix the structs imports in the test files being modified (test_core.py) — update to import from `arcengine`/`arc_agi`.
- **Out of scope**: Leave test_swarm.py structs issue for another pass.

**Recommendation**: Since we're already editing `tests/unit/test_core.py` for the LangGraphRandom removal, fix the structs imports there too. The imports should come from `arcengine` (for `FrameData`, `GameAction`, `GameState`) and `arc_agi.scorecard` (for `Scorecard`/`EnvironmentScorecard`). Leave `test_swarm.py` as-is (separate concern).

However — check whether `ActionInput`, `Card`, `Scorecard` are defined in `arcengine` or `arc_agi`. If they exist there, the fix is straightforward. If not (which seems likely given the `EnvironmentScorecard` usage in `agent.py`), then the test file has a deeper pre-existing problem that's beyond the scope of this task.

**Confirmed**: `agents.agent.py` line 10 imports `FrameData, FrameDataRaw, GameAction, GameState` from `arcengine`. Line 9 imports `EnvironmentWrapper` from `arc_agi`. Line `from arc_agi.scorecard import EnvironmentScorecard`. So the structs types are now in `arcengine` and `arc_agi`. The specific types `ActionInput`, `Card`, `Scorecard` — check if they exist in `arcengine`.

---

## Summary of Changes Required

### Files to Remove Entirely (7 files)
1. `agents/templates/langgraph_thinking/__init__.py`
2. `agents/templates/langgraph_thinking/llm.py`
3. `agents/templates/langgraph_thinking/tools.py`
4. `agents/templates/langgraph_thinking/agent.py`
5. `agents/templates/langgraph_thinking/nodes.py`
6. `agents/templates/langgraph_random_agent.py`
7. `agents/templates/langgraph_functional_agent.py` — After extracting `format_frame()` and `g2im()` into vision.py, this file has no remaining content.

### Files to Create (1 file — new renamed directory)
8. `agents/templates/_game_utils/` — rename from `langgraph_thinking/`. Contains `prompts.py`, `schema.py` (modified), `vision.py` (with format_frame/g2im appended).

### Files to Remove Content From (2 files)
9. `agents/__init__.py` — Remove L8-10 (3 import lines), remove L36-39 (4 `__all__` strings)
10. `tests/unit/test_core.py` — Remove L11 (import), remove `TestLangGraphRandomAgent` class (L229-281)

### Files to Edit/Strip Dead References (1 file)
11. `agents/templates/_game_utils/schema.py` (moved from `agents/templates/langgraph_thinking/schema.py`) — Remove `BaseMessage` import (L5), change `context: list[BaseMessage]` to `context: list[Any]` (add `Any` to typing imports)

### Files to Preserve Unchanged (3 files, moved to new directory)
12. `agents/templates/_game_utils/prompts.py` (moved from `agents/templates/langgraph_thinking/prompts.py`)
13. `agents/templates/_game_utils/vision.py` (moved from `agents/templates/langgraph_thinking/vision.py` — `format_frame()` and `g2im()` appended at end)
14. `agents/templates/_game_utils/schema.py` (moved from `agents/templates/langgraph_thinking/schema.py`, with edit applied)

---

## Dead Import Inventory (by package)

### `langchain_core` (3 files, 4 import lines — after removing tools.py and nodes.py as entire files)
| File | Import |
|------|--------|
| `langgraph_thinking/llm.py:1` | `from langchain_core.language_models import BaseChatModel` |
| `langgraph_thinking/schema.py:5` | `from langchain_core.messages import BaseMessage` |
| `langgraph_thinking/nodes.py:8` | `from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage` |
| `langgraph_thinking/tools.py:6` | `from langchain_core.tools import tool` |

### `langchain_openai` (1 file, 1 import line)
| File | Import |
|------|--------|
| `langgraph_thinking/llm.py:2` | `from langchain_openai import ChatOpenAI` |

### `langgraph` (4 files, 10 import lines)
| File | Import |
|------|--------|
| `langgraph_thinking/agent.py:5` | `from langgraph.graph import END, START, StateGraph` |
| `langgraph_thinking/agent.py:6` | `from langgraph.pregel import Pregel` |
| `langgraph_thinking/agent.py:7` | `from langgraph.store.sqlite import SqliteStore` |
| `langgraph_thinking/nodes.py:9` | `from langgraph.config import get_store` |
| `langgraph_thinking/tools.py:7` | `from langgraph.config import get_store` |
| `langgraph_random_agent.py:6` | `from langgraph.graph import END, START, StateGraph` |
| `langgraph_random_agent.py:7` | `from langgraph.pregel import Pregel` |
| `langgraph_functional_agent.py:13` | `from langgraph.checkpoint.memory import InMemorySaver` |
| `langgraph_functional_agent.py:14` | `from langgraph.func import entrypoint` |
| `langgraph_functional_agent.py:15` | `from langgraph.pregel import Pregel` |

### `langsmith` (1 file, 2 import lines)
| File | Import |
|------|--------|
| `langgraph_functional_agent.py:10` | `import langsmith as ls` |
| `langgraph_functional_agent.py:16` | `from langsmith.schemas import Attachment` |

---

## Pre-existing Issues Discovered (out of scope but noted)

1. **`tests/unit/test_core.py`** imports from `agents.structs` (L3-10) which does not exist. Same issue in `tests/unit/test_swarm.py` (L6). This predates the langchain removal.
2. **`tests/unit/test_openclaw_parser.py`** and **`tests/unit/test_openclaw_model_override.py`** exist — not checked for import issues, but unlikely to be affected.

---

## Execution Order

1. **Edit `schema.py`** — change `BaseMessage` to `Any` first (no dependency on other steps)
2. **Append `format_frame()` and `g2im()` to `vision.py`** — take cleaned versions from `langgraph_functional_agent.py` (strip langsmith refs from `format_frame()` L190-195 first)
3. **Create `agents/templates/_game_utils/` directory** and move `prompts.py`, `schema.py`, `vision.py` into it
4. **Remove the 7 fully-dependent files** — the 6 original files plus `langgraph_functional_agent.py`
5. **Edit `agents/__init__.py`** — strip dead imports (L8-10) and `__all__` entries (L36-39 relevant strings)
6. **Edit `tests/unit/test_core.py`** — strip dead import (L11) and `TestLangGraphRandomAgent` class (L229-281)
7. Verify no dangling references remain (`git grep` for `langchain`, `langgraph`, `langsmith`, `langchain_core`, `langchain_openai`)
8. Run `pytest` to confirm tests pass (expect `test_swarm.py` structs failures — pre-existing)
9. Run `ruff check` and `mypy` to confirm no new issues
