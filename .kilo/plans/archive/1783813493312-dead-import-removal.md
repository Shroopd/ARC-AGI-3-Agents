# Remove All LLM-Based Agents

## Goal
Remove every agent class that depends on an LLM. Keep only `Random` and `Playback` as available agents. Preserve independent utility functions into `_game_utils/vision.py`.

---

## Files to Remove Entirely (5 files, 1 directory)

| # | Path | Reason |
|---|------|--------|
| 1 | `agents/templates/llm_agents.py` | `LLM`, `FastLLM`, `GuidedLLM`, `ReasoningLLM`. All use OpenAI. |
| 2 | `agents/templates/multimodal.py` | `MultiModalLLM`. Uses OpenAI. Contains independent utilities (extracted first — see below). |
| 3 | `agents/templates/reasoning_agent.py` | `ReasoningAgent` extends `ReasoningLLM`. Uses OpenAI. `generate_grid_image_with_zone()` extracted first. |
| 4 | `agents/templates/smolagents.py` | `SmolCodingAgent`, `SmolVisionAgent`. Uses smolagents + OpenAI via `LLM`. `SmolVisionAgent.grid_to_image()` extracted first. |
| 5 | `agents/templates/openclaw_agent/` (directory) | `OpenClaw`. Uses OpenAI gateway. No independent content worth extracting — all helpers (`_parse_blob`, `_action_from_blob`, `_extract_reasoning`, `_enforce_size`) are tied to the OpenClaw JSON-in-text protocol. |

## Test Files to Remove Entirely (2 files)

| # | Path | Reason |
|---|------|--------|
| 6 | `tests/unit/test_openclaw_parser.py` | Tests `OpenClaw._parse_blob` / `_extract_reasoning`. |
| 7 | `tests/unit/test_openclaw_model_override.py` | Tests OpenClaw model override header. |

---

## Files to Edit (2 files)

| # | File | Changes |
|---|------|---------|
| 8 | `agents/__init__.py` | Remove imports of all removed agents. Rebuild `__all__` to: `Swarm`, `Random`, `Agent`, `Recorder`, `Playback`, `AVAILABLE_AGENTS`. Remove the `AVAILABLE_AGENTS["reasoningagent"] = ReasoningAgent` manual override line. |
| 9 | `pyproject.toml` | Remove `openai`, `smolagents`, `agentops` from `[project]` dependencies. |

---

## Files to Edit — Preserve Independent Utilities (1 file)

### `agents/templates/_game_utils/vision.py`

Append the following extracted functions. The file already has: `base64`, `json`, `BytesIO`, `numpy`, `FrameData` from arcengine, `PIL.Image/ImageDraw/ImageFont`, `COLOR_PALETTE`, `SCALE_FACTOR`, `extract_rect_from_render`, `render_frame`, `add_highlight`, `g2im`, `format_frame`.

#### Import change
Add `GameAction` to the arcengine import:
```diff
-from arcengine import FrameData
+from arcengine import FrameData, GameAction
```

#### Appended functions (in order)

**From `multimodal.py` (6 items):**

1. `_RGBA_PALETTE` — 16 RGBA color tuples (0–15), same mapping as `COLOR_PALETTE` but RGBA format. Renamed from `_PALETTE` to avoid clash with `COLOR_PALETTE`.

2. `_validate_grid_64(grid: list[list[int]]) -> None` — validates a grid is 64×64 with values 0–15. Renamed from `_validate_grid` to be more specific.

3. `grid_2d_to_pil(grid: list[list[int]]) -> Image.Image` — converts a 2D 64×64 grid to a 256×256 RGBA PIL Image using `_RGBA_PALETTE`. Renamed from `grid_to_image` to avoid naming collision.

4. `pil_to_base64(img: Image.Image) -> str` — PIL Image → base64 PNG. Renamed from `image_to_base64` for clarity.

5. `image_diff(img_a: Image.Image, img_b: Image.Image, highlight_rgb: tuple[int, int, int] = (255, 0, 0)) -> Image.Image` — visual diff of two PIL Images, changed pixels tinted `highlight_rgb` on black background. Returns pure black Image if identical. Uses numpy. Unchanged.

6. `human_actions: dict[GameAction, str]` — maps `GameAction` enum values to human-readable descriptions. Original name preserved.

7. `get_human_inputs_from(available_actions: list[GameAction]) -> str` — formats available actions into a human-readable string using `human_actions` map. Original name preserved.

**NOT preserved from multimodal.py:**
- `make_image_block` — OpenAI-specific image_url dict format, no remaining consumers
- `extract_json` — signature tied to `ChatCompletion` (openai type), no remaining consumers

**From `smolagents.py` (1 item, converted):**

8. `def grids_to_pil(grid: list[list[list[int]]]) -> Image.Image` — converts a 3D grid to a PIL Image, stacking layers horizontally with 5-pixel separators. Extracted from `SmolVisionAgent.grid_to_image()` — the method didn't use `self` so conversion is trivial (drop `self`, rename). Uses PIL only.

**From `reasoning_agent.py` (1 item, converted):**

9. `def render_grid_with_zones(grid: list[list[int]], cell_size: int = 40, zone_size: int = 16) -> bytes` — renders a 2D grid with colored cells, zone coordinate labels, gold zone borders. Extracted from `ReasoningAgent.generate_grid_image_with_zone()` — the instance method used `self.ZONE_SIZE`; converted to standalone function by adding `zone_size: int = 16` parameter. Uses `ImageDraw`, `ImageFont`. Returns PNG bytes.

**NOT preserved from reasoning_agent.py:**
- `ReasoningActionResponse(BaseModel)` — Pydantic schema specific to the agent's structured output

---

## Dead Import — Categorization

### A. Fully Dependent — Mark for Removal (8 items)
| File | Dead imports |
|------|-------------|
| `smolagents.py` | `from smolagents import ...` (L8–15), `from .llm_agents import LLM` (L17) |
| `llm_agents.py` | `import openai` (L7), `from openai import OpenAI` (L9) |
| `multimodal.py` | `import openai` (L14), `from openai import OpenAI` (L16), `from openai.types.chat import ChatCompletion` (L17) |
| `reasoning_agent.py` | `from openai import OpenAI` (L9), `from .llm_agents import ReasoningLLM` (L13) |
| `openclaw_agent/openclaw_agent.py` | `import openai` (L18), `from openai import OpenAI` (L20) |
| `openclaw_agent/__init__.py` | `from .openclaw_agent import OpenClaw` (L1) |
| `test_openclaw_parser.py` | `from ...openclaw_agent import OpenClaw` (L12) |
| `test_openclaw_model_override.py` | `from ...openclaw_agent import OpenClaw` (L16) |

### B. Fully Independent — Preserved (9 items → `vision.py`)
| Source | Preserved as | In destination |
|--------|-------------|---------------|
| `multimodal.py:_PALETTE` | `_RGBA_PALETTE` | `_game_utils/vision.py` |
| `multimodal.py:_validate_grid` | `_validate_grid_64` | `_game_utils/vision.py` |
| `multimodal.py:grid_to_image` | `grid_2d_to_pil` | `_game_utils/vision.py` |
| `multimodal.py:image_to_base64` | `pil_to_base64` | `_game_utils/vision.py` |
| `multimodal.py:image_diff` | `image_diff` (unchanged) | `_game_utils/vision.py` |
| `multimodal.py:human_actions` | `human_actions` (unchanged) | `_game_utils/vision.py` |
| `multimodal.py:get_human_inputs_from` | `get_human_inputs_from` (unchanged) | `_game_utils/vision.py` |
| `smolagents.py:SmolVisionAgent.grid_to_image` | `grids_to_pil` (standalone) | `_game_utils/vision.py` |
| `reasoning_agent.py:ReasoningAgent.generate_grid_image_with_zone` | `render_grid_with_zones` (standalone) | `_game_utils/vision.py` |

### C. Partially Dependent — Edit/Strip
| File | Action |
|------|--------|
| `agents/__init__.py` | Strip dead imports and `__all__` entries. Remove `reasoningagent` manual override. |
| `pyproject.toml` | Remove `openai`, `smolagents`, `agentops` lines. |

---

## Depth 2 — Knock-on Effects
Same as before — all cascading dead imports are contained in `agents/__init__.py` and handled by its edit.

**Depth 3**: No further effects. Remaining files (`main.py`, `swarm.py`, `agent.py`, `recorder.py`, `tracing.py`, `_game_utils/*`, `random_agent.py`, `conftest.py`, remaining test files) have zero imports from removed packages or agent classes.

---

## Pre-Existing Test Breakage (unchanged)
- `tests/unit/test_core.py` and `tests/unit/test_swarm.py` import from non-existent `agents.structs`. Not in scope.

---

## Execution Order

1. **Edit `_game_utils/vision.py`** — add `GameAction` to arcengine import, append the 9 preserved functions
2. **Remove 5 template files + 1 directory** — `llm_agents.py`, `multimodal.py`, `reasoning_agent.py`, `smolagents.py`, `openclaw_agent/`
3. **Remove 2 test files** — `test_openclaw_parser.py`, `test_openclaw_model_override.py`
4. **Edit `agents/__init__.py`** — strip dead imports, rebuild `__all__`, remove `reasoningagent` override
5. **Edit `pyproject.toml`** — remove `openai`, `smolagents`, `agentops` lines
6. `pip install -e .` (update installed packages after pyproject.toml changes)
7. Run validation: `git grep` for all removed agent/package names → zero matches
8. Run validation: `python -c "from agents import AVAILABLE_AGENTS; print(AVAILABLE_AGENTS.keys())"` → only `random` and playback recordings
9. `ruff check && mypy`
10. Commit

## Validation Commands
```bash
# No dead imports remain
git grep -c "openai\|smolagents\|agentops\|llm_agents\|ReasoningAgent\|MultiModalLLM\|OpenClaw\|SmolCodingAgent\|SmolVisionAgent" -- "*.py" "*.toml"

# Only Random + playback recorders available
python -c "from agents import AVAILABLE_AGENTS; print( sorted(k for k in AVAILABLE_AGENTS if not k.endswith('.recording.jsonl')))"
# Expected: ['random']

# Lint passes
ruff check agents/ tests/ main.py
mypy agents/ main.py
```
