import os
import sys
import json
import traceback

try:
    from jinja2 import Environment, FileSystemLoader, StrictUndefined
except ImportError:
    print("Error: jinja2 is required to run tests. Please install it using 'pip install jinja2'")
    sys.exit(1)

TEMPLATE_FILE = 'chat_template.jinja'
TEMPLATE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

env = Environment(
    loader=FileSystemLoader(TEMPLATE_DIR),
    undefined=StrictUndefined,
    keep_trailing_newline=True,
    lstrip_blocks=True,
    trim_blocks=True
)

def raise_exception(msg):
    raise Exception(msg)

env.globals['raise_exception'] = raise_exception

try:
    template = env.get_template(TEMPLATE_FILE)
except Exception as e:
    print(f"Error loading template: {e}")
    sys.exit(1)

def run_test(name, messages, tools=None, kwargs=None, expected_in=None, expected_not_in=None, expect_error=False):
    if kwargs is None:
        kwargs = {}
    
    print(f"\n--- Running Test: {name} ---")
    
    try:
        render_kwargs = {'messages': messages, 'add_generation_prompt': True}
        if tools is not None:
            render_kwargs['tools'] = tools
        render_kwargs.update(kwargs)
        
        rendered = template.render(**render_kwargs)
        
        if expect_error:
            print("❌ FAILED: Expected an exception but got none.")
            return False
            
        success = True
        
        if expected_in:
            for ex in expected_in:
                if ex not in rendered:
                    print(f"❌ FAILED: Missing expected string:\n'''{ex}'''")
                    print(f"Rendered:\n{rendered}")
                    success = False
        
        if expected_not_in:
            for n_ex in expected_not_in:
                if n_ex in rendered:
                    print(f"❌ FAILED: Found string that should NOT be present:\n'''{n_ex}'''")
                    print(f"Rendered:\n{rendered}")
                    success = False
                    
        if success:
            print("✅ PASSED")
            return True
        return False
        
    except Exception as e:
        if expect_error:
            print(f"✅ PASSED (Caught expected error: {e})")
            return True
        print(f"❌ FAILED with exception:\n{traceback.format_exc()}")
        return False

tests_passed = 0
tests_total = 0

def execute_test(*args, **kwargs):
    global tests_passed, tests_total
    tests_total += 1
    if run_test(*args, **kwargs):
        tests_passed += 1

# ==========================================
# 1. Qwen 3.8 Reasoning Effort Controls (v22.1 Default: medium)
# ==========================================

# 1. Default reasoning_effort="medium" (no system message -> zero system message emitted)
execute_test(
    "1. reasoning_effort='medium' (v22.1 default, no system message)",
    messages=[{"role": "user", "content": "Hello!"}],
    expected_in=[
        "<|im_start|>user\nHello!<|im_end|>\n<|im_start|>assistant\n<think>\n"
    ],
    expected_not_in=[
        "<|im_start|>system\n"
    ]
)

# 2. Explicit reasoning_effort="xhigh"
execute_test(
    "2. reasoning_effort='xhigh'",
    messages=[{"role": "user", "content": "Hello!"}],
    kwargs={"reasoning_effort": "xhigh"},
    expected_in=[
        "<|im_start|>system\nReasoning effort is set to xhigh. Please think carefully through the task, validate key assumptions, consider plausible alternatives, and prioritize correctness, consistency, and clarity in the final answer.<|im_end|>\n",
        "<|im_start|>user\nHello!<|im_end|>\n",
        "<|im_start|>assistant\n<think>\n"
    ]
)

# 3. Explicit reasoning_effort="high" (OpenAI alias -> xhigh)
execute_test(
    "3. reasoning_effort='high' (OpenAI alias)",
    messages=[{"role": "user", "content": "Hello!"}],
    kwargs={"reasoning_effort": "high"},
    expected_in=[
        "<|im_start|>system\nReasoning effort is set to xhigh. Please think carefully through the task, validate key assumptions, consider plausible alternatives, and prioritize correctness, consistency, and clarity in the final answer.<|im_end|>\n"
    ]
)

# 4. Explicit reasoning_effort="max" (API max alias -> xhigh)
execute_test(
    "4. reasoning_effort='max' (API alias)",
    messages=[{"role": "user", "content": "Hello!"}],
    kwargs={"reasoning_effort": "max"},
    expected_in=[
        "<|im_start|>system\nReasoning effort is set to xhigh. Please think carefully through the task, validate key assumptions, consider plausible alternatives, and prioritize correctness, consistency, and clarity in the final answer.<|im_end|>\n"
    ]
)

# 5. Explicit reasoning_effort="low"
execute_test(
    "5. reasoning_effort='low'",
    messages=[{"role": "user", "content": "Hello!"}],
    kwargs={"reasoning_effort": "low"},
    expected_in=[
        "<|im_start|>system\nReasoning effort is set to low. Keep your thinking brief and focused, moving directly to the conclusion without unnecessary elaboration.<|im_end|>\n",
        "<|im_start|>user\nHello!<|im_end|>\n"
    ]
)

# 6. Explicit reasoning_effort="minimal" (API minimal alias -> low)
execute_test(
    "6. reasoning_effort='minimal' (API alias)",
    messages=[{"role": "user", "content": "Hello!"}],
    kwargs={"reasoning_effort": "minimal"},
    expected_in=[
        "<|im_start|>system\nReasoning effort is set to low. Keep your thinking brief and focused, moving directly to the conclusion without unnecessary elaboration.<|im_end|>\n"
    ]
)

# 7. Explicit reasoning_effort="none" (disables thinking)
execute_test(
    "7. reasoning_effort='none' (disables thinking)",
    messages=[{"role": "user", "content": "Hello!"}],
    kwargs={"reasoning_effort": "none"},
    expected_in=[
        "<|im_start|>user\nHello!<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n"
    ],
    expected_not_in=[
        "Reasoning effort is set to"
    ]
)

# 8. Explicit reasoning_effort="unknown_val" (safe fallback to medium)
execute_test(
    "8. reasoning_effort='unknown_val' (safe fallback to medium)",
    messages=[{"role": "user", "content": "Hello!"}],
    kwargs={"reasoning_effort": "unrecognized_str"},
    expected_in=[
        "<|im_start|>user\nHello!<|im_end|>\n<|im_start|>assistant\n<think>\n"
    ],
    expected_not_in=[
        "Reasoning effort is set to"
    ]
)

# 9. reasoning_effort='xhigh' with user system prompt
execute_test(
    "9. reasoning_effort='xhigh' with user system prompt",
    messages=[
        {"role": "system", "content": "You are an expert coder."},
        {"role": "user", "content": "Write quicksort in C++"}
    ],
    kwargs={"reasoning_effort": "xhigh"},
    expected_in=[
        "<|im_start|>system\nReasoning effort is set to xhigh. Please think carefully through the task, validate key assumptions, consider plausible alternatives, and prioritize correctness, consistency, and clarity in the final answer.\n\nYou are an expert coder.<|im_end|>\n",
        "<|im_start|>user\nWrite quicksort in C++<|im_end|>\n"
    ]
)

# 10. reasoning_effort='xhigh' with tools
tools_sample = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get weather for city",
            "parameters": {
                "type": "object",
                "properties": {"city": {"type": "string"}},
                "required": ["city"]
            }
        }
    }
]

execute_test(
    "10. reasoning_effort='xhigh' with tools",
    messages=[{"role": "user", "content": "What's the weather in Tokyo?"}],
    tools=tools_sample,
    kwargs={"reasoning_effort": "xhigh"},
    expected_in=[
        "<|im_start|>system\nReasoning effort is set to xhigh. Please think carefully through the task, validate key assumptions, consider plausible alternatives, and prioritize correctness, consistency, and clarity in the final answer.\n\n# Tools\n\nYou have access to the following functions:\n\n<tools>\n"
    ]
)

# ==========================================
# 2. Inline Chat Tags for Reasoning Effort Steering (v22.1)
# ==========================================

# 11. Inline <|think_low|> in user message
execute_test(
    "11. Inline <|think_low|> in user string",
    messages=[{"role": "user", "content": "What is 2+2? <|think_low|>"}],
    expected_in=[
        "<|im_start|>system\nReasoning effort is set to low. Keep your thinking brief and focused, moving directly to the conclusion without unnecessary elaboration.<|im_end|>\n",
        "<|im_start|>user\nWhat is 2+2?<|im_end|>\n",
        "<|im_start|>assistant\n<think>\n"
    ],
    expected_not_in=[
        "<|think_low|>"
    ]
)

# 12. Inline <|think_xhigh|> in user message
execute_test(
    "12. Inline <|think_xhigh|> in user string",
    messages=[{"role": "user", "content": "Prove Fermat's Last Theorem <|think_xhigh|>"}],
    expected_in=[
        "<|im_start|>system\nReasoning effort is set to xhigh. Please think carefully through the task, validate key assumptions, consider plausible alternatives, and prioritize correctness, consistency, and clarity in the final answer.<|im_end|>\n",
        "<|im_start|>user\nProve Fermat's Last Theorem<|im_end|>\n",
        "<|im_start|>assistant\n<think>\n"
    ],
    expected_not_in=[
        "<|think_xhigh|>"
    ]
)

# 13. Inline <|think_medium|> in user message
execute_test(
    "13. Inline <|think_medium|> in user string",
    messages=[{"role": "user", "content": "Hello <|think_medium|>"}],
    expected_in=[
        "<|im_start|>user\nHello<|im_end|>\n",
        "<|im_start|>assistant\n<think>\n"
    ],
    expected_not_in=[
        "<|think_medium|>",
        "<|im_start|>system\n"
    ]
)

# 14. Inline <|think_off|> in user message
execute_test(
    "14. Inline <|think_off|> in user string",
    messages=[{"role": "user", "content": "Quick answer: what is capital of France? <|think_off|>"}],
    expected_in=[
        "<|im_start|>user\nQuick answer: what is capital of France?<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n"
    ],
    expected_not_in=[
        "<|think_off|>",
        "Reasoning effort is set to"
    ]
)

# 15. Inline <|think_low|> in multi-part list[dict]
execute_test(
    "15. Inline <|think_low|> in multi-part list[dict]",
    messages=[
        {"role": "user", "content": [{"type": "text", "text": "Solve this riddle <|think_low|>"}]}
    ],
    expected_in=[
        "<|im_start|>system\nReasoning effort is set to low. Keep your thinking brief and focused, moving directly to the conclusion without unnecessary elaboration.<|im_end|>\n",
        "<|im_start|>user\nSolve this riddle<|im_end|>\n"
    ],
    expected_not_in=[
        "<|think_low|>"
    ]
)

# 16. Inline <|think_xhigh|> in multi-part list[str]
execute_test(
    "16. Inline <|think_xhigh|> in multi-part list[str]",
    messages=[
        {"role": "user", "content": ["Solve this deeply", "<|think_xhigh|>"]}
    ],
    expected_in=[
        "<|im_start|>system\nReasoning effort is set to xhigh. Please think carefully through the task, validate key assumptions, consider plausible alternatives, and prioritize correctness, consistency, and clarity in the final answer.<|im_end|>\n",
        "<|im_start|>user\nSolve this deeply<|im_end|>\n"
    ],
    expected_not_in=[
        "<|think_xhigh|>"
    ]
)

# 17. Clean tag stripping across multiple tags in same string
execute_test(
    "17. Clean tag stripping across multiple tags in same string",
    messages=[
        {"role": "user", "content": "Hello <|think_on|> <|think_minimal|> world"}
    ],
    expected_in=[
        "<|im_start|>user\nHello   world<|im_end|>\n"
    ],
    expected_not_in=[
        "<|think_on|>",
        "<|think_minimal|>"
    ]
)

# ==========================================
# 3. Thinking Toggles & Preserves
# ==========================================

# 18. enable_thinking=false kwarg
execute_test(
    "18. enable_thinking=false kwarg",
    messages=[{"role": "user", "content": "Hello!"}],
    kwargs={"enable_thinking": False},
    expected_in=[
        "<|im_start|>user\nHello!<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n"
    ]
)

# 19. auto_disable_thinking_with_tools=true
execute_test(
    "19. auto_disable_thinking_with_tools=true",
    messages=[{"role": "user", "content": "What's the weather?"}],
    tools=tools_sample,
    kwargs={"auto_disable_thinking_with_tools": True},
    expected_in=[
        "<|im_start|>assistant\n<think>\n\n</think>\n\n"
    ]
)

# 20. preserve_reasoning=True preserves thinking
execute_test(
    "20. preserve_reasoning=True preserves thinking",
    messages=[
        {"role": "user", "content": "Question 1"},
        {"role": "assistant", "content": "<think>\nThinking 1\n</think>\n\nAnswer 1"},
        {"role": "user", "content": "Question 2"}
    ],
    kwargs={"preserve_reasoning": True},
    expected_in=[
        "<|im_start|>assistant\n<think>\nThinking 1\n</think>\n\nAnswer 1<|im_end|>\n"
    ]
)

# 21. preserve_reasoning=False strips past thinking
execute_test(
    "21. preserve_reasoning=False strips past thinking",
    messages=[
        {"role": "user", "content": "Question 1"},
        {"role": "assistant", "content": "<think>\nThinking 1\n</think>\n\nAnswer 1"},
        {"role": "user", "content": "Question 2"}
    ],
    kwargs={"preserve_reasoning": False},
    expected_in=[
        "<|im_start|>assistant\nAnswer 1<|im_end|>\n"
    ],
    expected_not_in=[
        "Thinking 1"
    ]
)

# 22. In-content <think> parsing (Curing official 3.8 empty think poisoning)
execute_test(
    "22. In-content <think> parsing (Curing official 3.8 empty think poisoning)",
    messages=[
        {"role": "user", "content": "Solve 1+1"},
        {"role": "assistant", "content": "<think>\n1+1 is 2\n</think>\n\nResult is 2"},
        {"role": "user", "content": "Now 2+2"}
    ],
    kwargs={"preserve_thinking": True},
    expected_in=[
        "<|im_start|>assistant\n<think>\n1+1 is 2\n</think>\n\nResult is 2<|im_end|>\n"
    ],
    expected_not_in=[
        "<think>\n\n</think>\n\n<think>"
    ]
)

# 23. OpenAI reasoning_content field
execute_test(
    "23. OpenAI reasoning_content field",
    messages=[
        {"role": "user", "content": "Question 1"},
        {"role": "assistant", "content": "Answer 1", "reasoning_content": "Deep thought 1"},
        {"role": "user", "content": "Question 2"}
    ],
    kwargs={"preserve_thinking": True},
    expected_in=[
        "<|im_start|>assistant\n<think>\nDeep thought 1\n</think>\n\nAnswer 1<|im_end|>\n"
    ]
)

# 24. Anthropic message.thinking field
execute_test(
    "24. Anthropic message.thinking field",
    messages=[
        {"role": "user", "content": "Question 1"},
        {"role": "assistant", "content": "Answer 1", "thinking": "Anthropic thought 1"},
        {"role": "user", "content": "Question 2"}
    ],
    kwargs={"preserve_thinking": True},
    expected_in=[
        "<|im_start|>assistant\n<think>\nAnthropic thought 1\n</think>\n\nAnswer 1<|im_end|>\n"
    ]
)

# ==========================================
# 4. Tool Calling (XML & JSON)
# ==========================================

# 25. Tool calling with dict arguments (XML)
execute_test(
    "25. Tool calling with dict arguments (XML)",
    messages=[
        {"role": "user", "content": "Weather in Paris?"},
        {
            "role": "assistant",
            "content": "",
            "tool_calls": [
                {
                    "type": "function",
                    "function": {
                        "name": "get_weather",
                        "arguments": {"city": "Paris"}
                    }
                }
            ]
        }
    ],
    expected_in=[
        "<|im_start|>assistant\n<tool_call>\n<function=get_weather>\n<parameter=city>\nParis\n</parameter>\n</function>\n</tool_call><|im_end|>\n"
    ]
)

# 26. Tool calling with JSON string arguments (XML)
execute_test(
    "26. Tool calling with JSON string arguments (XML)",
    messages=[
        {"role": "user", "content": "Weather in Paris?"},
        {
            "role": "assistant",
            "content": "",
            "tool_calls": [
                {
                    "type": "function",
                    "function": {
                        "name": "get_weather",
                        "arguments": '{"city": "Paris"}'
                    }
                }
            ]
        }
    ],
    kwargs={"tool_call_format": "xml"},
    expected_in=[
        "<|im_start|>assistant\n<tool_call>\n<function=get_weather>\n{\"city\": \"Paris\"}</function>\n</tool_call><|im_end|>\n"
    ]
)

# 27. Tool calling with dict arguments (JSON format)
execute_test(
    "27. Tool calling with dict arguments (JSON format)",
    messages=[
        {"role": "user", "content": "Weather in Paris?"},
        {
            "role": "assistant",
            "content": "",
            "tool_calls": [
                {
                    "type": "function",
                    "function": {
                        "name": "get_weather",
                        "arguments": {"city": "Paris"}
                    }
                }
            ]
        }
    ],
    kwargs={"tool_call_format": "json"},
    expected_in=[
        '<|im_start|>assistant\n<tool_call>\n{"name": "get_weather", "arguments": {"city": "Paris"}}\n</tool_call><|im_end|>\n'
    ]
)

# 28. Tool calling with JSON string arguments (JSON format)
execute_test(
    "28. Tool calling with JSON string arguments (JSON format)",
    messages=[
        {"role": "user", "content": "Weather in Paris?"},
        {
            "role": "assistant",
            "content": "",
            "tool_calls": [
                {
                    "type": "function",
                    "function": {
                        "name": "get_weather",
                        "arguments": '{"city": "Paris"}'
                    }
                }
            ]
        }
    ],
    kwargs={"tool_call_format": "json"},
    expected_in=[
        '<|im_start|>assistant\n<tool_call>\n{"name": "get_weather", "arguments": {"city": "Paris"}}\n</tool_call><|im_end|>\n'
    ]
)

# 29. Tool calling with empty arguments string
execute_test(
    "29. Tool calling with empty arguments string",
    messages=[
        {"role": "user", "content": "Call tool without args"},
        {
            "role": "assistant",
            "content": "",
            "tool_calls": [
                {
                    "type": "function",
                    "function": {
                        "name": "no_arg_tool",
                        "arguments": ""
                    }
                }
            ]
        }
    ],
    expected_in=[
        "<|im_start|>assistant\n<tool_call>\n<function=no_arg_tool>\n</function>\n</tool_call><|im_end|>\n"
    ]
)

# ==========================================
# 5. Payload Truncation & Error Escalation
# ==========================================

# 30. Dynamic parameter truncation (max_tool_arg_chars)
execute_test(
    "30. Dynamic parameter truncation (max_tool_arg_chars)",
    messages=[
        {"role": "user", "content": "Execute SQL"},
        {
            "role": "assistant",
            "content": "",
            "tool_calls": [
                {
                    "type": "function",
                    "function": {
                        "name": "run_sql",
                        "arguments": {"query": "SELECT * FROM users WHERE id = 1234567890 AND active = true"}
                    }
                }
            ]
        }
    ],
    kwargs={"max_tool_arg_chars": 20},
    expected_in=[
        "[TRUNCATED - original length"
    ]
)

# 31. Dynamic response truncation (max_tool_response_chars)
execute_test(
    "31. Dynamic response truncation (max_tool_response_chars)",
    messages=[
        {"role": "user", "content": "Search files"},
        {"role": "assistant", "content": "", "tool_calls": [{"type": "function", "function": {"name": "search", "arguments": {}}}]},
        {"role": "tool", "content": "A" * 200}
    ],
    kwargs={"max_tool_response_chars": 50},
    expected_in=[
        "[TRUNCATED - original length 200 chars]"
    ]
)

# 32. Consecutive tool error warning 1
execute_test(
    "32. Consecutive tool error warning 1",
    messages=[
        {"role": "user", "content": "Run tool"},
        {"role": "assistant", "content": "", "tool_calls": [{"type": "function", "function": {"name": "run", "arguments": {}}}]},
        {"role": "tool", "content": '{"error": "file not found"}'}
    ],
    expected_in=[
        "⚠️ SYSTEM WARNING: The previous tool call returned an error. Diagnose the failure and retry with completely corrected arguments."
    ]
)

# 33. Consecutive tool error warning 2 (retaining reasoning for error correction)
execute_test(
    "33. Consecutive tool error warning 2 (retaining reasoning for error correction)",
    messages=[
        {"role": "user", "content": "Run tool"},
        {"role": "assistant", "content": "", "tool_calls": [{"type": "function", "function": {"name": "run", "arguments": {}}}]},
        {"role": "tool", "content": '{"error": "file not found"}'},
        {"role": "assistant", "content": "", "tool_calls": [{"type": "function", "function": {"name": "run", "arguments": {}}}]},
        {"role": "tool", "content": '{"error": "permission denied"}'}
    ],
    expected_in=[
        "⚠️ SYSTEM WARNING: 2 consecutive tool errors detected. Your previous approach is incorrect. You MUST use a fundamentally different approach or corrected arguments.",
        "<|im_start|>assistant\n<think>\n"
    ]
)

# 34. Mid-conversation system & developer messages
execute_test(
    "34. Mid-conversation system & developer messages",
    messages=[
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi"},
        {"role": "developer", "content": "Mid-conversation update: user changed context."},
        {"role": "user", "content": "Continue"}
    ],
    expected_in=[
        "<|im_start|>system\nMid-conversation update: user changed context.<|im_end|>\n",
        "<|im_start|>user\nContinue<|im_end|>\n"
    ]
)

# ==========================================
# 3. v22.2 Enhancements & Community Fixes
# ==========================================

# 35. reasoning_effort='ultracode' (Discussion #78)
execute_test(
    "35. reasoning_effort='ultracode'",
    messages=[{"role": "user", "content": "Analyze algorithm"}],
    kwargs={"reasoning_effort": "ultracode"},
    expected_in=[
        "<|im_start|>system\nReasoning effort is set to xhigh. Please think carefully through the task, validate key assumptions, consider plausible alternatives, and prioritize correctness, consistency, and clarity in the final answer.<|im_end|>\n"
    ]
)

# 36. reasoning_effort='extreme'
execute_test(
    "36. reasoning_effort='extreme'",
    messages=[{"role": "user", "content": "Analyze algorithm"}],
    kwargs={"reasoning_effort": "extreme"},
    expected_in=[
        "<|im_start|>system\nReasoning effort is set to xhigh. Please think carefully through the task, validate key assumptions, consider plausible alternatives, and prioritize correctness, consistency, and clarity in the final answer.<|im_end|>\n"
    ]
)

# 37. Inline <|think_ultracode|> in user message
execute_test(
    "37. Inline <|think_ultracode|> in user message",
    messages=[{"role": "user", "content": "Optimize this shader <|think_ultracode|>"}],
    expected_in=[
        "<|im_start|>system\nReasoning effort is set to xhigh. Please think carefully through the task, validate key assumptions, consider plausible alternatives, and prioritize correctness, consistency, and clarity in the final answer.<|im_end|>\n",
        "<|im_start|>user\nOptimize this shader<|im_end|>\n"
    ],
    expected_not_in=[
        "<|think_ultracode|>"
    ]
)

# 38. Multiple leading system and developer messages merging
execute_test(
    "38. Multiple leading system and developer messages merging",
    messages=[
        {"role": "system", "content": "Base instructions."},
        {"role": "developer", "content": "Developer constraints."},
        {"role": "system", "content": "Additional guidelines."},
        {"role": "user", "content": "Hello"}
    ],
    expected_in=[
        "<|im_start|>system\nBase instructions.\n\nDeveloper constraints.\n\nAdditional guidelines.<|im_end|>\n",
        "<|im_start|>user\nHello<|im_end|>\n"
    ]
)

# 39. Grep code search with throw Error not false-positiving on tool error (Discussion #66)
execute_test(
    "39. Grep code search with throw Error not false-positiving on tool error (Discussion #66)",
    messages=[
        {"role": "user", "content": "Search for error handlers"},
        {"role": "assistant", "content": "", "tool_calls": [{"type": "function", "function": {"name": "grep", "arguments": {"pattern": "failed to"}}}]},
        {"role": "tool", "content": "src/lib/api.ts:42: throw new Error('failed to fetch');"},
        {"role": "assistant", "content": "", "tool_calls": [{"type": "function", "function": {"name": "grep", "arguments": {"pattern": "failed to"}}}]},
        {"role": "tool", "content": "src/lib/auth.ts:18: throw new Error('failed to authenticate');"}
    ],
    expected_not_in=[
        "⚠️ SYSTEM WARNING"
    ]
)

# 40. Grep code search with console.error not false-positiving
execute_test(
    "40. Grep code search with console.error not false-positiving",
    messages=[
        {"role": "user", "content": "Search for error logging"},
        {"role": "assistant", "content": "", "tool_calls": [{"type": "function", "function": {"name": "grep", "arguments": {"pattern": "console.error"}}}]},
        {"role": "tool", "content": "src/utils.js:5: console.error('failed to load config');"}
    ],
    expected_not_in=[
        "⚠️ SYSTEM WARNING"
    ]
)

# 41. Python Traceback legitimately triggers tool error warning
execute_test(
    "41. Python Traceback legitimately triggers tool error warning",
    messages=[
        {"role": "user", "content": "Run script"},
        {"role": "assistant", "content": "", "tool_calls": [{"type": "function", "function": {"name": "python", "arguments": {"code": "1/0"}}}]},
        {"role": "tool", "content": "Traceback (most recent call last):\n  File 'test.py', line 1\nZeroDivisionError: division by zero"}
    ],
    expected_in=[
        "⚠️ SYSTEM WARNING: The previous tool call returned an error. Diagnose the failure and retry with completely corrected arguments."
    ]
)

# 42. Safe XML parameter formatting for booleans, nulls, and numbers
execute_test(
    "42. Safe XML parameter formatting for booleans, nulls, and numbers",
    messages=[
        {"role": "user", "content": "Call config tool"},
        {"role": "assistant", "content": "", "tool_calls": [{
            "type": "function",
            "function": {
                "name": "set_config",
                "arguments": {
                    "is_active": True,
                    "is_debug": False,
                    "retries": 5,
                    "metadata": None
                }
            }
        }]}
    ],
    expected_in=[
        "<parameter=is_active>\ntrue\n</parameter>",
        "<parameter=is_debug>\nfalse\n</parameter>",
        "<parameter=retries>\n5\n</parameter>",
        "<parameter=metadata>\nnull\n</parameter>"
    ]
)

# 43. KV Cache Stability: History with JSON string arguments preserves canonical XML system prompt
execute_test(
    "43. KV Cache Stability: History with JSON string arguments preserves canonical XML system prompt",
    messages=[
        {"role": "user", "content": "What's the weather?"},
        {"role": "assistant", "content": "", "tool_calls": [{
            "type": "function",
            "function": {
                "name": "get_weather",
                "arguments": '{"city": "Paris", "unit": "celsius"}'
            }
        }]},
        {"role": "tool", "content": '{"temp": 22}'}
    ],
    tools=tools_sample,
    expected_in=[
        "<function=example_function_name>",
        "<tool_call>\n<function=get_weather>\n{\"city\": \"Paris\", \"unit\": \"celsius\"}</function>\n</tool_call>"
    ]
)

# 44. Empty think poisoning prevention regression test
execute_test(
    "44. Empty think poisoning prevention regression test",
    messages=[
        {"role": "user", "content": "Call tool"},
        {"role": "assistant", "content": "", "reasoning_content": "", "tool_calls": [{
            "type": "function",
            "function": {"name": "fetch", "arguments": {"id": 1}}
        }]},
        {"role": "tool", "content": "result data"},
        {"role": "assistant", "content": "Done!"}
    ],
    expected_not_in=[
        "<think>\n\n</think>"
    ]
)

print("\n==========================================")
print(f"Results: {tests_passed} / {tests_total} tests passed ({tests_passed/tests_total*100:.1f}%)")
print("==========================================")

if tests_passed != tests_total:
    sys.exit(1)
