# Llama-Qwen3.8-Swift1.5-Mtp-Claude-NoVision.jinja

A streamlined Jinja chat template for running **Claude Code** against **Swift 1.5** or **Qwen 3.8 MTP** GGUFs in `llama-server` (without vision projectors).

Adapted from [froggeric/Qwen-Fixed-Chat-Templates](https://huggingface.co) (incorporating Anthropic content-block handling from [PR #110](https://huggingface.co/discussions/110/files)).

---

## 🚨 Important: Use `--reasoning-format deepseek` and `--no-reasoning-preserve`

This template follows `llama-server`'s native reasoning-preservation behavior, which defaults to **`--reasoning-preserve` (`on`)**. For agentic coding workflows like Claude Code, we strongly recommend passing **`--no-reasoning-preserve`**:

* `--reasoning-format deepseek` extracts <think> blocks into the dedicated reasoning_content API response field. This prevents raw thinking tokens from leaking into the text stream and stopping tool calls midway.
* **Reasoning Preservation (`--no-reasoning-preserve` vs. Default):** Passing `--no-reasoning-preserve` frees **15–30% more usable context** and matches Qwen 3.8's native training format by pruning older `<think>` traces on each new user prompt (trading a ~1–3s checkpoint re-prefill per human turn), whereas leaving `llama-server`'s default `--reasoning-preserve` enabled preserves **99.9% instant prefix-cache hits** across every turn at the cost of earlier context compaction.

---

## Example Tuned `llama-server` Setup

**Environment:** Ryzen 5 9600X · 32 GB DDR5 · RX 9060 XT 16 GB · Llama.cpp 1.0 (Windows x64 Vulkan)  
**Performance:** ~136k context · 300–800 t/s prompt processing · 15–40 t/s generation (with MTP speculative decoding)

```text
llama-server
  -m Swift-1.5-Qwen3.8-27B-GSQ-RCO-IQ3_XXS-mtp.gguf
  --threads 6 --parallel 1 --load-mode none --fit-target 512 --flash-attn on
  --batch-size 1024 --ubatch-size 512 --cache-type-k q5_0 --cache-type-v q4_1
  --cache-ram 14336 --checkpoint-min-step 4096
  --reasoning-format deepseek --reasoning-effort medium --no-reasoning-preserve --reasoning-budget 8192
  --reasoning-budget-message "Thinking budget reached. Proceed with the best action or response now."
  --temp 0.7 --top-k 20 --top-p 0.95 --min-p 0.0
  --spec-type draft-mtp --spec-draft-n-max 9 --spec-draft-p-min 0.72
  --jinja --chat-template-file Llama-Qwen3.8-Swift1.5-Mtp-Claude-NoVision.jinja
  --metrics
```

* **VRAM Tip:** Disabling hardware/graphics acceleration in your browser (and terminal) keeps desktop DWM/browser surfaces from eating into discrete VRAM without needing to plug your monitor into motherboard graphics.

---

## What Changed from Upstream (`froggeric` v22.5 + PR #110)

### Fixed & Adapted
* **Anthropic / Claude Code Multi-Part Blocks ([PR #110](https://huggingface.co/discussions/110/files)):** Gracefully renders `thinking`, `redacted_thinking`, `tool_use`, `server_tool_use`, `mcp_tool_use`, `tool_result`, `web_search_tool_result`, `code_execution_tool_result`, `tool_reference`, and `document` blocks instead of throwing `Unexpected item type` errors.
* **Uniform `<think>` Boundaries in History:** Emits `<think>\n\n</think>` on past assistant turns once reasoning is pruned so multi-turn tool history matches Qwen 3.8's native training format and `add_generation_prompt` boundaries.
* **Native Thinking Retention (`--no-reasoning-preserve` Recommended):** Uses standard `preserve_thinking` / `preserve_reasoning` template flags so `llama-server` controls reasoning retention directly via CLI flags, pruning older `<think>` blocks when `--no-reasoning-preserve` is passed while retaining reasoning across active multi-step tool loops.
* **Explicit `medium` Reasoning Steering:** Tracks inline `<|think_medium|>` overrides in leading system blocks and injects balanced reasoning guidance when explicitly switched back from `low` or `xhigh`.

### Removed (Streamlined for XML + `NoVision`)
* **JSON Tool-Call Branch & Payload Truncation:** Removed `tool_call_format="json"` (Hermes) code paths and `max_tool_arg_chars` / `max_tool_response_chars` slicers, keeping strictly Qwen's native XML `<tool_call><function=...>` format for faster Jinja evaluation.
* **Heuristic Tool Error Warnings (`⚠️ SYSTEM WARNING`):** Removed the `consecutive_failures` string-matching scanner so Claude Code's native tool-error recovery loops are not altered by injected warnings.
* **Video, Audio & Vision Counter Overhead:** Removed `video`, `video_url`, `audio`, and unused vision-ID tracking (`add_vision_id`, `image_count`) for text-only (`NoVision`) local setups.

### Refactored
* **Unified `parse_and_strip()` Macro:** Consolidated `<|think_*|>` tag detection/stripping and `x-anthropic-*` header scrubbing into a single reusable Jinja macro.

---

## What's Changed in v1.1

* **Native `<tool_response>` Wrapping for Anthropic Tool Results:** Renders `tool_result`, `web_search_tool_result`, and `code_execution_tool_result` blocks inside Qwen's native `<tool_response>...</tool_response>` tags (with newline separation between parallel tool results) so multi-step Claude Code tool loops preserve active `<think>` reasoning until the next user turn.
* **Safe `NoVision` Image Placeholder:** Replaces `<|vision_start|><|image_pad|><|vision_end|>` special tokens with `[Image omitted - NoVision template]` so accidental image blocks in chat history don't trip up `llama-server` when running without `--mmproj`.

---

## What's Changed in v1.2

* **Aligned Defaults with `llama-server` (`--reasoning-preserve`):** Retained standard `preserve_thinking` / `preserve_reasoning` variable handling so the template follows `llama-server`'s native reasoning-preservation default (`on`) out of the box and responds directly to `--no-reasoning-preserve` / `--reasoning-preserve` CLI flags (unlike `v1.1` documentation that implied `preserve_thinking = false` overrode `llama-server`'s default).
* **Prefix Cache Protection (`x-anthropic-*` Scrubbing):** Automatically strips dynamic Anthropic billing and routing headers (such as `x-anthropic-billing-header:`) from system messages before tokenization, preventing token-0 cache misses in `llama-server`.
* **Claude Code `<system-reminder>` Compatibility:** Updated active-turn boundary detection to recognize standalone and bundled `<tool_response>` / `<system-reminder>` blocks without prematurely pruning current-turn reasoning, and added newline separation when text blocks follow tool results.
* **Single-Pass System Parsing & Empty-Turn Guards:** Consolidated leading system aggregation and `<|think_*|>` override detection into one pass (preventing mid-chat override tags from invalidating the system prefix), skipped blank turns left after stripping, and normalized historical assistant `<think>\n\n</think>` blocks.
* **Template Cleanup:** Removed unused upstream vision-ID tracking variables (`add_vision_id`, `image_count`, and `count_vision`).
