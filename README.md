# Think Toggle for Open WebUI (vLLM / Qwen 3.8)

A Claude-Code-style **Think button** for [Open WebUI](https://github.com/open-webui/open-webui) (or as close as I could get it) click it on in the chat input bar and your next message gets full reasoning (rendered as the collapsible *"Thought for N seconds"* block); leave it off and responses stay instant. Reasoning effort (`low` / `medium` / `xhigh`) is selectable per user.

Built for **hybrid thinking models served by vLLM** — Qwen 3.8 in particular — where the server default is thinking *off* and you want thinking on demand.

## Why this exists

Open WebUI's own thinking toggle sends `enable_thinking` as a **top-level request field, which vLLM silently ignores**. vLLM expects it inside `chat_template_kwargs`. So the built-in toggle does nothing against a vLLM backend. This filter injects the flag where it actually works, and strips the no-op top-level field so there's one source of truth.

## What it does

When the Think button is active, the filter's `inlet` rewrites the request:

```python
body["chat_template_kwargs"] = {"enable_thinking": True, "reasoning_effort": effort}
```

plus three quality-of-life behaviors:

- **Official thinking sampler** — Qwen's recommended thinking-mode sampling (`temperature 1.0 / top_p 0.95 / presence_penalty 0`) is applied automatically while thinking, unless the request already sets its own values. Without this you'd be thinking with instruct-mode sampling, which is off-spec.
- **Background tasks never think** — title, tag, and follow-up generation calls are forced to fast mode, so flipping Think on doesn't give you 30-second chat titles.
- **Effort control** — `low` / `medium` / `xhigh` via a per-user valve (Chat Controls → Valves). These map to Qwen 3.8's native `reasoning_effort`.

## Requirements

- Open WebUI **≥ 0.9.0** (toggle filters)
- A vLLM server (tested on v0.24) running a hybrid thinking model, launched with:
  - `--reasoning-parser qwen3` — so reasoning arrives in `reasoning_content` and Open WebUI renders the collapsed block (without it, raw `<think>` tags land in the message text)
  - recommended: `--default-chat-template-kwargs '{"enable_thinking": false}'` so fast mode is the default and the button is the opt-in 
- A model whose chat template understands `enable_thinking` (Qwen 3.8 / 3.6 family; `reasoning_effort` is 3.8+ and harmlessly ignored elsewhere). Recent llama.cpp `llama-server` also accepts per-request `chat_template_kwargs`, so this largely works there too.

## Install

1. Admin Panel → **Functions** → **+** (New Function)
2. Paste `thinking-toggle.py`, save, **enable** it
3. Make it **Global** (⋮ menu on the function row), or attach it to specific models via Workspace → Models → *edit model* → Filters

The 💡 button appears in the chat input bar's toggle row. Effort lives in Chat Controls (sliders icon) → **Valves**.

## Admin valves

| Valve | Default | What it does |
|---|---|---|
| `apply_official_thinking_sampler` | on | Thinking-mode sampling while the button is active |
| `block_thinking_on_tasks` | on | Keeps title/tag/follow-up generation instant |
| `priority` | 0 | Filter execution order |

## Troubleshooting

- **No button visible** → the function isn't enabled, or isn't Global/attached to the model you're chatting with. Hard-refresh after enabling.
- **Thinking shows as raw `<think>` text** → your vLLM is missing `--reasoning-parser qwen3`.
- **Empty responses while thinking** → a tight `max_tokens` cap ate the whole budget mid-reasoning. Raise or remove the cap for thinking requests.
- **Effort seems to do nothing** → your model's template predates `reasoning_effort` (it's a Qwen 3.8+ feature); on/off still works.

## License

MIT
