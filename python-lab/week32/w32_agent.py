"""Week 32: a tool registry, a hand-written agent loop, an approval state machine, an audit log.

Replace each stub with your own code. FakeLLM, tool_call_msg and final_msg are GIVEN: read them first.
Run:  pytest week32          (from the python-lab folder, with requirements-week32.txt installed)

Message format used everywhere (provider-neutral; a real adapter converts to and from it):
    user message       {"role": "user", "content": "..."}
    assistant, final   {"role": "assistant", "content": "text"}
    assistant, calling {"role": "assistant", "content": None,
                        "tool_calls": [{"id": "c1", "name": "lookup_ticket", "arguments": {"ticket_id": "T-101"}}]}
    tool result        {"role": "tool", "tool_call_id": "c1", "name": "lookup_ticket", "content": "<JSON string>"}
"""
from __future__ import annotations

import json  # noqa: F401  (you will need these)
import os  # noqa: F401
import re  # noqa: F401
import tempfile  # noqa: F401
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable

from pydantic import BaseModel, ValidationError  # noqa: F401


# --------------------------------------------------------------------------- GIVEN: the scripted model


class FakeLLM:
    """GIVEN. A scripted stand-in for a model. complete() returns the next scripted assistant message.

    When the script runs out it repeats the LAST message forever: that is how a test makes a model that
    never stops calling tools. `calls` records a copy of the message list passed to each complete().
    """

    def __init__(self, script):
        self._script = list(script)
        self.calls = []

    def complete(self, messages):
        self.calls.append(list(messages))
        index = min(len(self.calls) - 1, len(self._script) - 1)
        return self._script[index]


def tool_call_msg(call_id, name, **arguments):
    """GIVEN. An assistant message that asks for one tool call."""
    return {"role": "assistant", "content": None,
            "tool_calls": [{"id": call_id, "name": name, "arguments": arguments}]}


def final_msg(text):
    """GIVEN. An assistant message with a final answer and no tool calls."""
    return {"role": "assistant", "content": text}


# --------------------------------------------------------------------------- 1. tool registry


@dataclass
class Tool:
    """GIVEN. One registered tool. `writes` is True for tools that change something."""

    name: str
    description: str
    args_model: type  # a pydantic BaseModel subclass describing the arguments
    func: Callable[..., Any]
    writes: bool = False


class ToolRegistry:
    """Holds tools by name.

    register(name, description, args_model, func, writes=False)
        Add a tool. A name that is already registered raises ValueError.
    get(name) -> Tool | None
        None for an unknown name (do not raise).
    names() -> list[str]
        All names, sorted alphabetically.
    schemas() -> list[dict]
        One dict per tool, sorted by name, shaped
        {"name": ..., "description": ..., "parameters": <args_model.model_json_schema()>}
        This is what you would send to a model so it knows what it may call.
    """

    def __init__(self):
        raise NotImplementedError

    def register(self, name, description, args_model, func, writes=False):
        raise NotImplementedError

    def get(self, name):
        raise NotImplementedError

    def names(self):
        raise NotImplementedError

    def schemas(self):
        raise NotImplementedError


def run_tool(registry, name, raw_args):
    """Run one tool call the model proposed. NEVER raises for model mistakes or tool failures.

    Returns {"ok": True, "result": <whatever the function returned>} on success, otherwise
    {"ok": False, "error": {"type": ..., "message": ..., ...}} where type is one of:

      "unknown_tool"       name not in the registry. Add "available": registry.names() to the error.
      "invalid_arguments"  raw_args is a str that is not valid JSON, or is not a JSON object (dict) after
                           parsing, or fails the tool's pydantic model. For a pydantic failure add
                           "details": [{"field": "days", "problem": "<pydantic message>"}, ...]
                           (field = the dotted location, one entry per problem).
      "tool_failed"        the function raised any Exception. message = str(exception). Never include a
                           traceback.

    raw_args may arrive as a dict or as a JSON string (providers differ): accept both.
    The function is called ONLY after validation succeeds, as func(**validated_model.model_dump()).
    """
    raise NotImplementedError


# --------------------------------------------------------------------------- 2. the agent loop


@dataclass
class AgentResult:
    """GIVEN. final: the answer text or None; stop_reason: "final" | "max_iterations" | "max_tool_calls";
    messages: the full history; calls: one dict per executed tool call; iterations: model calls made."""

    final: str | None
    stop_reason: str
    messages: list
    calls: list = field(default_factory=list)
    iterations: int = 0


def run_agent(llm, registry, user_message, *, max_iterations=6, max_tool_calls=10, audit=None):
    """The agent loop, by hand.

    Start with messages = [{"role": "user", "content": user_message}]. Then repeat, at most
    max_iterations times (one iteration = one llm.complete(messages) call):

      1. reply = llm.complete(messages); append reply to messages.
      2. No "tool_calls" (missing or empty)? Stop: AgentResult(reply["content"], "final", messages, calls, n).
      3. For each requested call, in order:
           - if len(calls) is already max_tool_calls: stop WITHOUT running it:
             AgentResult(None, "max_tool_calls", messages, calls, n)
           - result = run_tool(registry, call["name"], call["arguments"])
           - record {"name", "arguments", "ok": result["ok"]} in calls
           - if audit is not None: audit.record({"event": "tool_call", "name", "arguments", "ok"})
           - append {"role": "tool", "tool_call_id": call["id"], "name": call["name"],
                     "content": json.dumps(result)} to messages
      4. After the last allowed iteration: AgentResult(None, "max_iterations", messages, calls, max_iterations).

    Errors from run_tool are NOT special: they go back to the model as ordinary tool messages so it can
    correct itself.
    """
    raise NotImplementedError


# --------------------------------------------------------------------------- 3. approval state machine


class ApprovalState(str, Enum):
    """GIVEN."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    EXECUTED = "executed"


class IllegalTransition(Exception):
    """GIVEN. Raised when a state change is not allowed from the current state."""


class ApprovalExpired(IllegalTransition):
    """GIVEN. Raised when you try to act on a request whose time ran out."""


class SelfApproval(Exception):
    """GIVEN. Raised when the person who requested an action tries to approve it."""


class ApprovalStore:
    """Approvals persisted in ONE JSON file, so state survives a restart. Time comes from `clock`
    (a function returning seconds as a float) so tests can move it by hand.

    ApprovalStore(path, clock=time.time)
        Load the file if it exists, otherwise start empty. A fresh object on the same file sees the same data.

    create(request_id, action, requested_by, ttl_seconds) -> dict
        New record in state "pending". Duplicate id raises ValueError. Returns a COPY of the record:
        {"id", "action", "requested_by", "state", "created_at", "expires_at", "history"}
        expires_at = now + ttl_seconds. history = [{"state": "pending", "at": now, "by": requested_by}].

    get(request_id) -> dict            a COPY of the record (changing it must not change the store). KeyError if unknown.
    state(request_id) -> ApprovalState KeyError if unknown.

    Expiry: whenever a record is read or acted on, if its state is "pending" or "approved" and
    clock() >= expires_at, it becomes "expired" (append a history entry by "system") and that is SAVED.
    Expired is terminal; moving the clock backwards later does not bring it back.

    approve(request_id, approver)
        Checks in this order: expired -> raise ApprovalExpired; not pending -> raise IllegalTransition;
        approver == requested_by -> raise SelfApproval (state unchanged). Otherwise state "approved",
        history entry by the approver.
    reject(request_id, approver)
        expired -> ApprovalExpired; not pending -> IllegalTransition; else "rejected". (Rejecting your own
        request is allowed: it is a cancel.)
    mark_executed(request_id)
        expired -> ApprovalExpired; not approved -> IllegalTransition; else "executed", history entry by "system".

    Every change is written to disk immediately. Write to a temp file in the same folder and os.replace() it
    over the real one, so a crash never leaves half a file.
    """

    def __init__(self, path, clock=time.time):
        raise NotImplementedError

    def create(self, request_id, action, requested_by, ttl_seconds):
        raise NotImplementedError

    def get(self, request_id):
        raise NotImplementedError

    def state(self, request_id):
        raise NotImplementedError

    def approve(self, request_id, approver):
        raise NotImplementedError

    def reject(self, request_id, approver):
        raise NotImplementedError

    def mark_executed(self, request_id):
        raise NotImplementedError


# --------------------------------------------------------------------------- 4. audit log with redaction

REDACT_KEYS = {"password", "passwd", "secret", "token", "api_key", "apikey", "authorization",
               "access_token", "refresh_token", "client_secret"}
"""GIVEN. A dict key is sensitive when key.lower() is EXACTLY one of these. Exact, not 'contains':
a counter called tokens_used must survive, because cost tracking needs it."""


def redact(value):
    """Return a redacted DEEP COPY. Never mutate the input.

    - dict: every value whose key is sensitive (case-insensitive, see REDACT_KEYS) becomes "[REDACTED]";
      other values are redacted recursively.
    - list / tuple: a list of redacted items.
    - str: every email address replaced by "[EMAIL]" (a regex such as r"[\\w.+-]+@[\\w-]+\\.[\\w.-]+" is fine).
    - anything else (int, float, bool, None): returned unchanged.
    """
    raise NotImplementedError


class AuditLog:
    """Append-only JSON-lines audit file.

    AuditLog(path, clock=time.time)
        The next sequence number continues after any lines already in the file (a new file starts at 1).

    record(event: dict) -> dict
        Build {"seq": n, "at": clock(), **redact(event)}, append it as ONE json line (json.dumps), and
        return it. The file must never contain the raw secret.

    events() -> list[dict]
        Every record in the file, in order. [] if the file does not exist yet.
    """

    def __init__(self, path, clock=time.time):
        raise NotImplementedError

    def record(self, event):
        raise NotImplementedError

    def events(self):
        raise NotImplementedError
