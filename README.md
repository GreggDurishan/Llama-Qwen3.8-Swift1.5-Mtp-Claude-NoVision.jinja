# Llama-Qwen3.8-Swift1.5-Mtp-Claude-NoVision.jinja

A streamlined Jinja chat template for running **Claude Code** against **Swift 1.5** or **Qwen 3.8 MTP** GGUFs in `llama-server` (without vision projectors).

Adapted from [froggeric/Qwen-Fixed-Chat-Templates](https://huggingface.co/froggeric/Qwen-Fixed-Chat-Templates) (incorporating Anthropic content-block handling from [PR #110](https://huggingface.co/froggeric/Qwen-Fixed-Chat-Templates/discussions/110/files)).

---

## Example Tuned `llama-server` Setup

**Hardware:** Ryzen 5 9600X · 32 GB DDR5 · RX 9060 XT 16 GB  
**Performance:** ~136k context · 300–800 t/s prompt processing · 15–40 t/s generation (with MTP speculative decoding)

```bash
llama-server -m Swift-1.5-Qwen3.8-27B-GSQ-RCO-IQ3_XXS-mtp.gguf \
  --threads 6 --parallel 1 --load-mode none --flash-attn on \
  --reasoning-effort medium --temp 0.7 --top-k 20 --top-p 0.95 --min-p 0.0 \
  --spec-type draft-mtp --spec-draft-n-max 9 --spec-draft-p-min 0.72 \
  --jinja --chat-template-file Llama-Qwen3.8-Swift1.5-Mtp-Claude-NoVision.jinja \
  --cache-type-k q5_0 --cache-type-v q4_1 \
  --batch-size 1024 --ubatch-size 512 --fit-target 512
```

> **VRAM Tip:** Disabling hardware/graphics acceleration in your browser (and terminal) keeps desktop DWM/browser surfaces from eating into your 16 GB discrete VRAM without needing to plug your monitor into motherboard graphics.

---

## What Changed from Upstream (`froggeric` v22.5 + PR #110)

### Fixed & Adapted
* **Anthropic / Claude Code Multi-Part Blocks ([PR #110](https://huggingface.co/froggeric/Qwen-Fixed-Chat-Templates/discussions/110/files)):** Gracefully renders `thinking`, `redacted_thinking`, `tool_use`, `server_tool_use`, `mcp_tool_use`, `tool_result`, `web_search_tool_result`, `code_execution_tool_result`, `tool_reference`, and `document` blocks instead of throwing `Unexpected item type` errors.
* **No Blank `<think>` Blocks in History:** Only emits `<think>...</think>` on past assistant turns when `reasoning_content` is non-empty, preventing blank `<think>\n\n</think>` blocks from polluting chat history.
* **Context-Saving Thinking Retention (`preserve_thinking = false` by default):** Drops `<think>` blocks from prior user turns to conserve KV cache during long Claude Code sessions while still retaining reasoning across active multi-step tool calls (override with `--reasoning-preserve` or `preserve_thinking=true`).
* **Explicit `medium` Reasoning Steering:** Tracks inline `<|think_medium|>` overrides and injects balanced reasoning guidance when explicitly switched back from `low` or `xhigh`.

### Removed (Streamlined for XML + `NoVision`)
* **JSON Tool-Call Branch & Payload Truncation:** Removed `tool_call_format="json"` (Hermes) code paths and `max_tool_arg_chars` / `max_tool_response_chars` slicers, keeping strictly Qwen's native XML `<tool_call><function=...>` format for faster Jinja evaluation.
* **Heuristic Tool Error Warnings (`⚠️ SYSTEM WARNING`):** Removed the `consecutive_failures` string-matching scanner so Claude Code's native tool-error recovery loops are not altered by injected warnings.
* **Video & Audio Content Parsing:** Removed `video`, `video_url`, and `audio` handling for text-only (`NoVision`) local setups.

### Refactored
* **Unified `parse_and_strip()` Macro:** Consolidated repeated `<|think_*|>` tag detection and stripping blocks into a single reusable Jinja macro.
