"""
title: Think (vLLM / Qwen 3.8)
author: ryan + claude (llm-lab)
version: 2.0
description: Claude-Code-style Think button in the chat input bar (toggle filter).
  Click it on -> the request thinks (chat_template_kwargs the way vLLM honors),
  with Qwen's official thinking sampler applied. Off -> server default (fast mode).
  Effort level set in Chat Controls -> Valves.
required_open_webui_version: 0.9.0
"""

from pydantic import BaseModel, Field
from typing import Optional, Literal


class Filter:
    class Valves(BaseModel):
        priority: int = Field(default=0, description="Filter execution order")
        apply_official_thinking_sampler: bool = Field(
            default=True,
            description="Apply Qwen's thinking-mode sampler (temp 1.0 / top_p 0.95 / "
            "presence 0) when thinking, unless the request sets its own.",
        )
        block_thinking_on_tasks: bool = Field(
            default=True,
            description="Keep background task calls (title/tags/follow-ups) instant.",
        )

    class UserValves(BaseModel):
        effort: Literal["low", "medium", "xhigh"] = Field(
            default="medium",
            description="Reasoning effort when the Think button is on",
        )

    def __init__(self):
        self.valves = self.Valves()
        # toggle=True => renders as a click-on/off button in the chat input bar;
        # inlet only runs when the button is active.
        self.toggle = True
        self.icon = (
            "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' "
            "viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' "
            "stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M9 18h6M10 "
            "22h4M12 2a7 7 0 0 0-4 12.7c.6.5 1 1.2 1 2V17h6v-.3c0-.8.4-1.5 1-2A7 7 "
            "0 0 0 12 2z'/%3E%3C/svg%3E"
        )

    def inlet(
        self,
        body: dict,
        __user__: Optional[dict] = None,
        __metadata__: Optional[dict] = None,
    ) -> dict:
        # Button is ON if we're here at all (toggle filter).
        thinking = True
        if self.valves.block_thinking_on_tasks and (__metadata__ or {}).get("task"):
            thinking = False

        uv = (__user__ or {}).get("valves")
        effort = str(getattr(uv, "effort", "medium"))

        kwargs = {"enable_thinking": thinking}
        if thinking:
            kwargs["reasoning_effort"] = effort
        body["chat_template_kwargs"] = kwargs
        body.pop("enable_thinking", None)  # strip OWUI's own no-op flag

        if thinking and self.valves.apply_official_thinking_sampler:
            body.setdefault("temperature", 1.0)
            body.setdefault("top_p", 0.95)
            body.setdefault("presence_penalty", 0.0)
        return body
