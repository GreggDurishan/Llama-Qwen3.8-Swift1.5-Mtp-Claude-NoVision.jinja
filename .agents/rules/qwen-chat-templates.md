# Qwen Chat Template Architecture & Jinja Invariants

1. **Reasoning Effort Safety:**
   * In Qwen 3.8, `reasoning_effort` is implemented purely via prompt steering (not a sampler-level token budget).
   * Defaulting to `xhigh` causes the model to explore alternate reasoning branches indefinitely on complex tasks until hitting `max_tokens`, returning zero content (`content: ""`).
   * Always default `reasoning_effort` to `medium` (zero injected tokens) to preserve 100% Prefix KV Cache hit rate and prevent token-burn traps.
   * Map standard API strings monotonically (`none` disables thinking, `minimal`/`low` -> `low`, `medium`/unknown -> `medium`, `high`/`xhigh`/`max` -> `xhigh`).

2. **Jinja2 & MiniJinja Block Scoping Invariant:**
   * In Jinja2 and MiniJinja (C++), `{% set x = ... %}` inside a `{% for %}` loop creates a block-local variable that does NOT mutate outer scope.
   * Always encapsulate mutable state evaluated across message loops inside a `namespace` object (e.g. `ns_state = namespace(thinking=..., effort=...)`).

3. **Control Tag Pre-Scanning & Stripping:**
   * Pre-scan only trusted roles (`system`, `developer`, `user`) to prevent prompt injection from third-party tool returns.
   * Handle raw strings (`str`), string lists (`list[str]`), and structured multimodal objects (`list[dict]` with `type="text"`).
   * Strip all control tags sequentially using `.split(tag) | join('')` across system, user, and assistant content to prevent prompt leakage.

4. **Inference Server Flags & Compatibility:**
   * **`llama-server`:** Use `--reasoning-format deepseek` to separate `<think>` into the OpenAI `reasoning_content` field so coding agents (OpenCode, Claude Code, Pi.dev) do not stall on raw tokens.
   * **`vLLM`:** Use `--tool-call-parser qwen3_xml` for native Qwen XML tool calling.
   * **`chat_template_kwargs`:** Parameters intended for custom Jinja templates must be passed inside `chat_template_kwargs` because servers like `llama-server` and `oMLX` consume top-level fields for internal routing.
