"""Shared state & types for all LangGraph agents."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from langchain_core.messages import BaseMessage


class AgentAction(str, Enum):
    CONTINUE = "continue"
    ESCALATE = "escalate"
    COMPLETE = "complete"
    FAIL = "fail"


@dataclass
class AgentState:
    """Mutable state passed through every LangGraph node."""

    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    messages: list[BaseMessage] = field(default_factory=list)
    input_data: dict[str, Any] = field(default_factory=dict)
    output_data: dict[str, Any] = field(default_factory=dict)
    current_step: str = ""
    steps_completed: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    next_action: AgentAction = AgentAction.CONTINUE
    tokens_used: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)
