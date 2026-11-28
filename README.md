# Llama-Qwen3.8-Swift1.5-Mtp-Claude-NoVision.jinja

A streamlined Jinja2 chat template for running Claude Code on [Qwen 3.8](https://github.com/QwenLM/Qwen3.8) Family (ie: Swift 1.5) GGUFs in llama-server without vision projectors, adapted from [froggeric/Qwen-Fixed-Chat-Templates](https://huggingface.co/froggeric/Qwen-Fixed-Chat-Templates/discussions/110/files).

* Bridges Claude’s Anthropic API format and Qwen3.8’s native ChatML + XML tool-calling syntax so local `llama-server` setups stay fast, accurate, and within tight VRAM limits.
* Protects KV-cache prefix by stripping dynamic `x-anthropic-*` headers and merging leading `system`/`developer` blocks into a single static header.
* Translates Claude-specific `tool_use`, `tool_result`, and `thinking` blocks into strict Qwen XML tags that a quantized 27B model can reliably parse.
* Replaces image inputs with text placeholders so text-only GGUFs don't crash without an `mmproj` file.
* Detects the boundary of your current user turn—retaining `<think>` blocks across intermediate tool calls so Qwen keeps its reasoning intact mid-task, while collapsing older turns' thinking into empty `<think></think>` stubs once finished to save tens of thousands of context tokens—and supports inline `<|think_*|>` tags to dynamically adjust reasoning effort on the fly.

---

# Example Tuned Setup & Config Tips

**Environment:** Ryzen 5 9600X · 32 GB DDR5-6000 · RX 9060 XT 16 GB · Llama.cpp v1.1.0 (Windows x64 Vulkan)  
**1h Parent/Child Agent Diagnose/Coding Task:** 430 t/s PreFill · 31 t/s Gen · 82.5% Draft Acceptance · 6.34 Mean Len  
**llm-bench.io:** [Results](https://llm-bench.io/benchmarks/cmx05enua034w01lmhxc88kdi)
 T/S 31.4 · QUALITY 89.3 · Agent 91.3 · Code 84.8 · RP 93.8 · Research 87.1  

## `llama-server` Invocation

```bat
llama-server ^
  -m Swift-1.5-Qwen3.8-27B-GSQ-RCO-IQ3_XXS-mtp.gguf -ngl all -c 114688 ^
  --fit off --threads 6 --parallel 1 --load-mode none --flash-attn on ^
  --temp 1 --top-k 20 --top-p 0.95 --min-p 0.0 --batch-size 1024 --ubatch-size 512 ^
  --cache-type-k q4_0 --cache-type-v q4_1 --cache-ram 18432 --checkpoint-min-step 16384 ^
  --spec-type draft-mtp --spec-draft-n-max 9 --spec-draft-p-min 0.72 --timeout 900 ^
  --reasoning-format deepseek --reasoning-effort xhigh --no-reasoning-preserve --reasoning-budget 12288 ^
  --reasoning-budget-message "Thinking budget reached. Proceed with the best action or response now." ^
  --jinja --chat-template-file Llama-Qwen3.8-Swift1.5-Mtp-Claude-NoVision.jinja --metrics
```

> [!IMPORTANT]
> Use `--reasoning-format deepseek` and `--no-reasoning-preserve`  
> `--reasoning-format deepseek` prevents raw thinking tokens from leaking into the text stream and stopping tool calls midway. Passing `--no-reasoning-preserve` frees 15–30% more usable context and matches Qwen 3.8's native training format by pruning older `<think>` traces on each new user prompt.

<sub>Running Claude smoothly on a local GPU comes down to four transferable rules rather than copying exact numbers. <strong>1. Pack the largest single-slot KV cache your VRAM can hold without spilling:</strong> Claude is context-hungry, so dedicate 100% of your GPU memory to one active sequence (<code>--parallel 1</code>), disable automatic memory guesswork (<code>--fit off</code>), enable <code>--flash-attn on</code>, and quantize the KV cache (<code>--cache-type-k q4_0 --cache-type-v q4_1</code>) to stretch your context window (<code>-c</code>) as far as your dedicated VRAM allows—if you have 24 GB+ VRAM, raise <code>-c</code> or step up to <code>q8_0</code> KV cache; if you have 8–12 GB, lower <code>-c</code> until the entire model + cache fits in dedicated VRAM with zero shared-RAM spillover. <strong>2. Match host RAM caching and checkpoint spacing to your system RAM:</strong> Size <code>--cache-ram</code> to roughly 25–50% of your free system RAM so inactive conversation prefixes warm-reload instead of re-evaluating from scratch, and keep <code>--checkpoint-min-step</code> large enough (e.g., <code>8192</code>–<code>16384</code>) that recurrent state snapshots don't eat into your VRAM headroom. <strong>3. Use zero-VRAM speculative decoding for speed:</strong> Models with built-in Multi-Token Prediction heads (<code>--spec-type draft-mtp</code>) boost generation speed by 30–50% without loading a separate draft model into VRAM—tune <code>--spec-draft-n-max</code> and <code>--spec-draft-p-min</code> to keep acceptance around 70%+. <strong>4. Guard context and timeouts against agentic loops:</strong> Use a Claude-compatible Jinja template (<code>--jinja</code>), strip stale thinking blocks from prior turns (<code>--no-reasoning-preserve</code>) so history doesn't balloon, cap runaway thinking with <code>--reasoning-budget</code>, and set <code>--timeout</code> high enough to cover your slowest full-budget generation turn.</sub>

---

## Claude `settings.json`

<details open>
<summary><strong>View <code>settings.json</code></strong> (click to collapse)</summary>

```json
{
  "includeGitInstructions": false,
  "env": {
    "ANTHROPIC_BASE_URL": "http://localhost:9931",
    "ANTHROPIC_AUTH_TOKEN": "apikey",
    "ANTHROPIC_MODEL": "Swift-1.5-Qwen3.8-27B-GSQ-RCO-IQ3_XXS-mtp",
    "ANTHROPIC_DEFAULT_HAIKU_MODEL": "Swift-1.5-Qwen3.8-27B-GSQ-RCO-IQ3_XXS-mtp",
    "CLAUDE_CODE_SUBAGENT_MODEL": "Swift-1.5-Qwen3.8-27B-GSQ-RCO-IQ3_XXS-mtp",
    "CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS": "1",
    "CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH": "1",
    "CLAUDE_CODE_ATTRIBUTION_HEADER": "0",
    "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1",
    "CLAUDE_CODE_DISABLE_BACKGROUND_TASKS": "1",
    "DISABLE_NON_ESSENTIAL_MODEL_CALLS": "1",
    "CLAUDE_CODE_DISABLE_1M_CONTEXT": "1",
    "CLAUDE_AUTOCOMPACT_PCT_OVERRIDE": "79",
    "API_TIMEOUT_MS": "900000",
    "CLAUDE_STREAM_IDLE_TIMEOUT_MS": "300000"
  },
  "showClearContextOnPlanAccept": true,
  "permissions": {
    "deny": [
      "WebSearch",
      "WebFetch"
    ]
  },
  "modelSettings": {
    "Swift-1.5-Qwen3.8-27B-GSQ-RCO-IQ3_XXS-mtp": {
      "autoCompactWindow": 114688
    }
  },
  "autoCompactEnabled": true,
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Read",
        "hooks": [
          {
            "type": "command",
            "command": "python \$USERPROFILE/.claude/hooks/read_guard.py"
          }
        ]
      }
    ],
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python \$USERPROFILE/.claude/hooks/read_guard.py"
          }
        ]
      }
    ]
  }
}
```

</details>

> [!IMPORTANT]
> Use `"CLAUDE_CODE_ATTRIBUTION_HEADER": "0"` and `"CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1"`  
> Without these, Claude injects a dynamic attribution/session header that causes constant KV-cache eviction and 40–100+ second prompt re-evaluation stalls between turns. This jinja template strips these headers automatically, but this is the canonical solution and good practice.


<sub>Claude assumes cloud API speeds, 1M-token context windows, and parallel multi-slot concurrency—all of which stall or crash a single-GPU setup unless you align the client to your server's physical limits. <strong>1. Match compaction to your real VRAM context ceiling:</strong> Disable the 1M cloud assumption (<code>CLAUDE_CODE_DISABLE_1M_CONTEXT: "1"</code>), set <code>autoCompactWindow</code> to your exact <code>llama-server -c</code> value, and trigger compaction at 75–80% (<code>CLAUDE_AUTOCOMPACT_PCT_OVERRIDE: "79"</code>) so Claude summarizes history before quantized attention degrades or hits truncation; pair this with <code>showClearContextOnPlanAccept: true</code> to wipe planning chatter before coding begins. <strong>2. Keep a single, unbreakable KV prefix:</strong> Point <code>ANTHROPIC_MODEL</code>, <code>ANTHROPIC_DEFAULT_HAIKU_MODEL</code>, and <code>CLAUDE_CODE_SUBAGENT_MODEL</code> to your exact same model string, set <code>CLAUDE_CODE_ATTRIBUTION_HEADER: "0"</code> to strip dynamic per-session headers, and block background traffic (<code>CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC: "1", "CLAUDE_CODE_DISABLE_BACKGROUND_TASKS": "1", "DISABLE_NON_ESSENTIAL_MODEL_CALLS": "1"</code> ) so every turn hits your cached prefix instead of triggering full prompt re-evaluations. <strong>3. Serialize subagents to match single-slot VRAM:</strong> Unless you have 48 GB+ VRAM to run multiple <code>--parallel</code> slots, cap <code>CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS: "1"</code> and <code>CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH: "1"</code> so child agents execute one at a time instead of ping-ponging Slot 0 and wiping each other's KV cache. <strong>4. Scale timeouts to your local tokens-per-second:</strong> Calculate your worst-case turn time (<code>[context size / prompt eval t/s] + [max output / generation t/s]</code>) and set <code>API_TIMEOUT_MS</code> above that total and <code>CLAUDE_STREAM_IDLE_TIMEOUT_MS</code> above your slowest full-prompt evaluation so Claude never aborts valid long generations mid-stream. <strong>5. Strip cloud tools and guard context bloat:</strong> Deny cloud-only <code>WebSearch</code>/<code>WebFetch</code> tools, replace Claude's ~1,200-token built-in git manual (<code>includeGitInstructions: false</code>) with concise rules in <code>CLAUDE.md</code>, and use a <code>PreToolUse</code> hook (<code>read_guard.py</code>) to prevent smaller local models from dumping huge files into their own window. (Have Claude write you one)</sub>


---

## 3. `CLAUDE.md`

<details open>
<summary><strong>View <code>CLAUDE.md</code></strong> (click to collapse)</summary>

```markdown
# Environment
Local LLM via llama-server (http://localhost:9931/, API only). 112K context (compacts at ~91K).

# File Reading Rules
- **Locate first:** Use `Glob`/`Grep` to find exact files and line numbers before calling `Read`.
- **Slice sizes (`read_guard.py`):** Whole-read files ≤300L / ≤15KB at most **once** per session (resets on `/compact`/`/clear`). Always read files >300L / >15KB and follow-ups in **100–150 line slices** (`offset`/`limit`).
- **Diffs & confirmations:** Use `git diff --stat` then `git diff <file> | head -80`. Never `Read` a file back after a successful `Edit`/`Write` — the tool result is the confirmation.
- **No binary images** (`.png`, `.jpg`, `.webp`, etc.; `.svg` is allowed).

# Web
- Use `playwright-cli` (unique sessions, load the skill) instead of WebSearch/WebFetch.
- Web content: extract, don't dump — pull only the facts you need (in-page eval, targeted slices).

# Git
- Work on feature branches (`feat/`, `fix/`, `chore/`), not `main`/`master`.
- Commit only when asked; stage specific files, never `git add -A`.
- Conventional Commits, imperative subject ≤72 chars, explain *why*.
- No `--force`, `reset --hard`, rebasing shared branches, or amending published commits without explicit OK. No interactive git.

# Sub-agents
- **Architect (main session):** Stays grounded in the codebase by reading code/design docs directly, may use `Explore` subagents for broad searches to keep main context lean.
- **Delegation (main session only):** Spawn a child when a unit needs >~1500 lines, >3 big files, or ≥3 independent context-heavy units. Subagents must never spawn subagents.
- **Scope to fit the window:** Split large tasks into an appropriate number of smaller agents so no agent exceeds ~91K context.
- **Disk checkpoints & short finals:** Write each unit's results to a file on disk immediately; summarize + point at the disk report. Scripts go to files, not inline.
- **Strict serialization:** After launching a background Agent, output 1 short line and end your turn immediately—never poll while waiting for its completion notification.
- **Recovery:** If a notified Agent stopped incomplete or stalled, resume it via SendMessage instead of spawning a new one.
```

</details>

<sub>State your true auto-compact ceiling in <code># Environment</code> and <code># Sub-agents</code> - adjust this number to match your own <code>-c * CLAUDE_AUTOCOMPACT_PCT_OVERRIDE</code> so the model splits work cleanly instead of triggering mid-task compactions. <code># File Reading Rules</code> sits at the top for peak transformer attention, forcing targeted <code>Glob</code>/<code>Grep</code> lookups, 100–150 line read slices, truncated diffs, and zero post-edit re-reads to preserve KV cache and 27B reasoning focus. <code># Web</code> routes browsing through [playwright-cli](https://github.com/microsoft/playwright-cli) with targeted extraction so raw web pages never bloat the context window, while <code># Git</code> provides essential branch and commit guardrails in ~95 tokens to replace the ~1,200-token prompt stripped in <code>settings.json</code>. <code># Sub-agents</code> keeps the main Architect grounded while using <code>Explore</code> subagents selectively, scopes child tasks with disk checkpoints and short summaries so parent context stays lean, keeps the parent completely silent while a child owns Slot 0, and recovers stalled agents via <code>SendMessage</code> instead of spawning cache-wiping replacements.</sub>
