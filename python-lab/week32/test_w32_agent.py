"""Tests for week 32. Do not edit. Run:  pytest week32

Every test uses FakeLLM (a scripted model), tmp_path files and an injected clock.
Nothing here touches the network, a real model or the real time.
"""
import json

import pytest
from pydantic import BaseModel, Field

from w32_agent import (
    AgentResult,
    ApprovalExpired,
    ApprovalState,
    ApprovalStore,
    AuditLog,
    FakeLLM,
    IllegalTransition,
    SelfApproval,
    ToolRegistry,
    final_msg,
    redact,
    run_agent,
    run_tool,
    tool_call_msg,
)


# ---------------------------------------------------------------- fixtures


class LookupTicketArgs(BaseModel):
    ticket_id: str = Field(pattern=r"^T-\d+$")


class GrantArgs(BaseModel):
    employee_id: str
    site_id: str
    days: int = Field(default=1, ge=1, le=30)


class Clock:
    """An injectable clock: tests move time by hand."""

    def __init__(self, now=1000.0):
        self.now = now

    def __call__(self):
        return self.now


def make_registry(grants=None):
    grants = grants if grants is not None else []
    reg = ToolRegistry()
    reg.register("lookup_ticket", "Read one ticket.", LookupTicketArgs,
                 lambda ticket_id: {"id": ticket_id, "status": "open"})
    reg.register("grant_access", "Grant site access.", GrantArgs,
                 lambda employee_id, site_id, days: grants.append((employee_id, site_id, days)) or "granted",
                 writes=True)

    def boom():
        raise RuntimeError("vendor down")

    class NoArgs(BaseModel):
        pass

    reg.register("flaky", "Always fails.", NoArgs, boom)
    return reg


# ---------------------------------------------------------------- registry


def test_registry_names_are_sorted_and_get_returns_none_for_unknown():
    reg = make_registry()
    assert reg.names() == ["flaky", "grant_access", "lookup_ticket"]
    assert reg.get("nope") is None
    assert reg.get("lookup_ticket").writes is False
    assert reg.get("grant_access").writes is True


def test_registry_rejects_duplicate_names():
    reg = make_registry()
    with pytest.raises(ValueError):
        reg.register("lookup_ticket", "again", LookupTicketArgs, lambda ticket_id: None)


def test_schemas_are_json_schema_with_name_description_parameters():
    schemas = make_registry().schemas()
    assert [s["name"] for s in schemas] == ["flaky", "grant_access", "lookup_ticket"]
    grant = schemas[1]
    assert grant["description"] == "Grant site access."
    assert grant["parameters"]["type"] == "object"
    assert set(grant["parameters"]["properties"]) == {"employee_id", "site_id", "days"}
    assert sorted(grant["parameters"]["required"]) == ["employee_id", "site_id"]
    json.dumps(schemas)  # must be serialisable as-is


# ---------------------------------------------------------------- run_tool


def test_run_tool_success_wraps_result():
    out = run_tool(make_registry(), "lookup_ticket", {"ticket_id": "T-101"})
    assert out == {"ok": True, "result": {"id": "T-101", "status": "open"}}


def test_run_tool_accepts_arguments_as_json_string():
    out = run_tool(make_registry(), "lookup_ticket", '{"ticket_id": "T-7"}')
    assert out["ok"] is True and out["result"]["id"] == "T-7"


def test_unknown_tool_is_a_structured_error_not_an_exception():
    out = run_tool(make_registry(), "delete_everything", {})
    assert out["ok"] is False
    assert out["error"]["type"] == "unknown_tool"
    assert out["error"]["available"] == ["flaky", "grant_access", "lookup_ticket"]


def test_invalid_arguments_never_reach_the_function():
    grants = []
    reg = make_registry(grants)
    out = run_tool(reg, "grant_access", {"employee_id": "e-902", "site_id": "BLR-01", "days": 400})
    assert out["ok"] is False
    assert out["error"]["type"] == "invalid_arguments"
    assert out["error"]["details"][0]["field"] == "days"
    assert grants == []  # the write tool never ran


def test_function_receives_the_validated_values_with_defaults_filled_in():
    grants = []
    reg = make_registry(grants)
    out = run_tool(reg, "grant_access", {"employee_id": "e-902", "site_id": "BLR-01"})
    assert out == {"ok": True, "result": "granted"}
    assert grants == [("e-902", "BLR-01", 1)]  # days was omitted: the model's default arrived
    run_tool(reg, "grant_access", {"employee_id": "e-1", "site_id": "HYD-01", "days": "3"})
    assert grants[-1] == ("e-1", "HYD-01", 3)  # "3" was coerced to the int 3 by validation


def test_missing_required_field_is_reported_by_name():
    out = run_tool(make_registry(), "grant_access", {"employee_id": "e-902"})
    fields = {d["field"] for d in out["error"]["details"]}
    assert fields == {"site_id"}


def test_bad_json_string_and_non_object_are_invalid_arguments():
    reg = make_registry()
    assert run_tool(reg, "lookup_ticket", "{not json")["error"]["type"] == "invalid_arguments"
    assert run_tool(reg, "lookup_ticket", "[1, 2]")["error"]["type"] == "invalid_arguments"
    assert run_tool(reg, "lookup_ticket", None)["error"]["type"] == "invalid_arguments"


def test_tool_exception_becomes_tool_failed_without_traceback():
    out = run_tool(make_registry(), "flaky", {})
    assert out["ok"] is False
    assert out["error"]["type"] == "tool_failed"
    assert out["error"]["message"] == "vendor down"
    assert "Traceback" not in json.dumps(out)


# ---------------------------------------------------------------- agent loop


def test_agent_calls_tool_then_returns_final_answer():
    llm = FakeLLM([tool_call_msg("c1", "lookup_ticket", ticket_id="T-101"),
                   final_msg("T-101 is open.")])
    res = run_agent(llm, make_registry(), "status of T-101?")
    assert isinstance(res, AgentResult)
    assert res.final == "T-101 is open."
    assert res.stop_reason == "final"
    assert res.iterations == 2
    assert res.calls == [{"name": "lookup_ticket", "arguments": {"ticket_id": "T-101"}, "ok": True}]


def test_history_has_user_assistant_tool_assistant_in_order_with_matching_ids():
    llm = FakeLLM([tool_call_msg("c1", "lookup_ticket", ticket_id="T-101"), final_msg("done")])
    res = run_agent(llm, make_registry(), "hi")
    roles = [m["role"] for m in res.messages]
    assert roles == ["user", "assistant", "tool", "assistant"]
    tool_msg = res.messages[2]
    assert tool_msg["tool_call_id"] == "c1"
    assert tool_msg["name"] == "lookup_ticket"
    assert json.loads(tool_msg["content"])["ok"] is True


def test_model_sees_the_tool_result_on_its_second_call():
    llm = FakeLLM([tool_call_msg("c1", "lookup_ticket", ticket_id="T-5"), final_msg("ok")])
    run_agent(llm, make_registry(), "go")
    second_call_messages = llm.calls[1]
    assert second_call_messages[-1]["role"] == "tool"


def test_no_tool_calls_means_immediate_final_answer():
    llm = FakeLLM([final_msg("hello")])
    res = run_agent(llm, make_registry(), "hi")
    assert (res.final, res.stop_reason, res.iterations, res.calls) == ("hello", "final", 1, [])


def test_max_iterations_stops_a_model_that_never_finishes():
    llm = FakeLLM([tool_call_msg("c1", "lookup_ticket", ticket_id="T-1")])  # repeats forever
    res = run_agent(llm, make_registry(), "loop", max_iterations=3, max_tool_calls=99)
    assert res.stop_reason == "max_iterations"
    assert res.final is None
    assert len(llm.calls) == 3
    assert res.iterations == 3


def test_max_tool_calls_stops_before_executing_the_extra_call():
    grants = []
    llm = FakeLLM([tool_call_msg("c1", "grant_access", employee_id="e-1", site_id="BLR-01", days=1)])
    res = run_agent(llm, make_registry(grants), "spam", max_iterations=50, max_tool_calls=2)
    assert res.stop_reason == "max_tool_calls"
    assert len(grants) == 2
    assert len(res.calls) == 2


def test_unknown_tool_in_loop_is_returned_to_the_model_and_loop_continues():
    llm = FakeLLM([tool_call_msg("c1", "rm_rf", path="/"), final_msg("sorry, cannot")])
    res = run_agent(llm, make_registry(), "x")
    assert res.stop_reason == "final"
    assert res.calls == [{"name": "rm_rf", "arguments": {"path": "/"}, "ok": False}]
    fed_back = json.loads(res.messages[2]["content"])
    assert fed_back["error"]["type"] == "unknown_tool"


def test_invalid_arguments_in_loop_are_fed_back_so_the_model_can_correct():
    llm = FakeLLM([
        tool_call_msg("c1", "lookup_ticket", ticket_id="101"),     # wrong shape
        tool_call_msg("c2", "lookup_ticket", ticket_id="T-101"),   # corrected
        final_msg("fixed"),
    ])
    res = run_agent(llm, make_registry(), "x")
    assert [c["ok"] for c in res.calls] == [False, True]
    assert res.final == "fixed"


def test_tool_failure_does_not_crash_the_loop():
    llm = FakeLLM([tool_call_msg("c1", "flaky"), final_msg("could not reach vendor")])
    res = run_agent(llm, make_registry(), "x")
    assert res.final == "could not reach vendor"
    assert json.loads(res.messages[2]["content"])["error"]["type"] == "tool_failed"


def test_agent_writes_one_audit_event_per_tool_call_with_redaction(tmp_path):
    audit = AuditLog(tmp_path / "audit.jsonl", clock=Clock())
    llm = FakeLLM([tool_call_msg("c1", "lookup_ticket", ticket_id="T-1", api_key="sk-live-123"),
                   final_msg("done")])
    run_agent(llm, make_registry(), "x", audit=audit)
    events = audit.events()
    assert len(events) == 1
    assert events[0]["event"] == "tool_call" and events[0]["name"] == "lookup_ticket"
    assert events[0]["arguments"]["api_key"] == "[REDACTED]"
    assert "sk-live-123" not in (tmp_path / "audit.jsonl").read_text(encoding="utf-8")


# ---------------------------------------------------------------- approval store


def make_store(tmp_path, clock):
    return ApprovalStore(tmp_path / "approvals.json", clock=clock)


def test_new_request_is_pending_with_expiry(tmp_path):
    clock = Clock(1000)
    store = make_store(tmp_path, clock)
    rec = store.create("ap-1", {"tool": "grant_access"}, requested_by="agent", ttl_seconds=60)
    assert rec["state"] == "pending"
    assert rec["expires_at"] == 1060
    assert store.state("ap-1") is ApprovalState.PENDING


def test_create_is_written_to_disk_immediately(tmp_path):
    store = make_store(tmp_path, Clock())
    store.create("ap-1", {"tool": "grant_access"}, "agent", 60)
    assert make_store(tmp_path, Clock()).state("ap-1") is ApprovalState.PENDING


def test_duplicate_id_and_unknown_id(tmp_path):
    store = make_store(tmp_path, Clock())
    store.create("ap-1", {}, "agent", 60)
    with pytest.raises(ValueError):
        store.create("ap-1", {}, "agent", 60)
    with pytest.raises(KeyError):
        store.state("ap-404")


def test_approve_then_execute_happy_path_records_who_and_when(tmp_path):
    clock = Clock(1000)
    store = make_store(tmp_path, clock)
    store.create("ap-1", {"tool": "grant_access"}, "agent", 600)
    clock.now = 1010
    store.approve("ap-1", "mgr-7")
    assert store.state("ap-1") is ApprovalState.APPROVED
    clock.now = 1020
    store.mark_executed("ap-1")
    rec = store.get("ap-1")
    assert rec["state"] == "executed"
    assert [(h["state"], h["by"], h["at"]) for h in rec["history"]] == [
        ("pending", "agent", 1000), ("approved", "mgr-7", 1010), ("executed", "system", 1020)]


def test_cannot_execute_without_approval(tmp_path):
    store = make_store(tmp_path, Clock())
    store.create("ap-1", {}, "agent", 60)
    with pytest.raises(IllegalTransition):
        store.mark_executed("ap-1")
    assert store.state("ap-1") is ApprovalState.PENDING


def test_self_approval_is_rejected_and_state_unchanged(tmp_path):
    store = make_store(tmp_path, Clock())
    store.create("ap-1", {}, requested_by="e-902", ttl_seconds=60)
    with pytest.raises(SelfApproval):
        store.approve("ap-1", "e-902")
    assert store.state("ap-1") is ApprovalState.PENDING
    store.approve("ap-1", "mgr-7")  # a different person can
    assert store.state("ap-1") is ApprovalState.APPROVED


def test_illegal_transitions_are_rejected(tmp_path):
    store = make_store(tmp_path, Clock())
    store.create("ap-1", {}, "agent", 60)
    store.reject("ap-1", "mgr-7")
    with pytest.raises(IllegalTransition):
        store.approve("ap-1", "mgr-8")          # rejected is terminal
    store.create("ap-2", {}, "agent", 60)
    store.approve("ap-2", "mgr-7")
    with pytest.raises(IllegalTransition):
        store.approve("ap-2", "mgr-8")          # cannot approve twice
    with pytest.raises(IllegalTransition):
        store.reject("ap-2", "mgr-8")           # cannot reject after approval
    store.mark_executed("ap-2")
    with pytest.raises(IllegalTransition):
        store.mark_executed("ap-2")             # cannot execute twice


def test_pending_request_expires_and_cannot_be_approved(tmp_path):
    clock = Clock(1000)
    store = make_store(tmp_path, clock)
    store.create("ap-1", {}, "agent", ttl_seconds=60)
    clock.now = 1059
    assert store.state("ap-1") is ApprovalState.PENDING   # still valid one second before
    clock.now = 1060
    with pytest.raises(ApprovalExpired):
        store.approve("ap-1", "mgr-7")
    assert store.state("ap-1") is ApprovalState.EXPIRED
    assert issubclass(ApprovalExpired, IllegalTransition)


def test_approved_but_unexecuted_request_also_expires(tmp_path):
    clock = Clock(1000)
    store = make_store(tmp_path, clock)
    store.create("ap-1", {}, "agent", ttl_seconds=60)
    store.approve("ap-1", "mgr-7")
    clock.now = 2000
    with pytest.raises(ApprovalExpired):
        store.mark_executed("ap-1")
    assert store.state("ap-1") is ApprovalState.EXPIRED


def test_state_survives_a_restart(tmp_path):
    clock = Clock(1000)
    store = make_store(tmp_path, clock)
    store.create("ap-1", {"tool": "grant_access", "site": "BLR-01"}, "agent", 600)
    store.approve("ap-1", "mgr-7")
    reopened = make_store(tmp_path, clock)          # a new object reading the same file
    assert reopened.state("ap-1") is ApprovalState.APPROVED
    assert reopened.get("ap-1")["action"]["site"] == "BLR-01"
    with pytest.raises(IllegalTransition):
        reopened.approve("ap-1", "mgr-8")


def test_expiry_is_persisted_not_only_computed(tmp_path):
    clock = Clock(1000)
    store = make_store(tmp_path, clock)
    store.create("ap-1", {}, "agent", 10)
    clock.now = 5000
    assert store.state("ap-1") is ApprovalState.EXPIRED
    clock.now = 0  # time going backwards must not resurrect it
    assert make_store(tmp_path, clock).state("ap-1") is ApprovalState.EXPIRED


def test_get_returns_a_copy(tmp_path):
    store = make_store(tmp_path, Clock())
    store.create("ap-1", {"n": 1}, "agent", 60)
    rec = store.get("ap-1")
    rec["state"] = "executed"
    rec["action"]["n"] = 99
    assert store.state("ap-1") is ApprovalState.PENDING
    assert store.get("ap-1")["action"]["n"] == 1


# ---------------------------------------------------------------- redaction and audit


def test_redact_masks_sensitive_keys_at_any_depth_case_insensitively():
    out = redact({"user": "e-902", "API_Key": "sk-1", "nested": {"Password": "x", "ok": 1},
                  "items": [{"token": "t"}, "plain"]})
    assert out == {"user": "e-902", "API_Key": "[REDACTED]",
                   "nested": {"Password": "[REDACTED]", "ok": 1},
                   "items": [{"token": "[REDACTED]"}, "plain"]}


def test_redact_keeps_cost_counters_whose_name_merely_contains_token():
    out = redact({"tokens_used": 512, "token": "abc"})
    assert out == {"tokens_used": 512, "token": "[REDACTED]"}


def test_redact_masks_email_addresses_inside_strings():
    out = redact({"note": "contact asha.k+vip@example.com today", "n": 3, "flag": True, "none": None})
    assert out == {"note": "contact [EMAIL] today", "n": 3, "flag": True, "none": None}


def test_redact_does_not_mutate_its_input():
    original = {"password": "p", "inner": {"secret": "s"}, "list": [{"token": "t"}]}
    snapshot = json.loads(json.dumps(original))
    redact(original)
    assert original == snapshot


def test_audit_log_appends_json_lines_with_sequence_and_time(tmp_path):
    clock = Clock(50)
    log = AuditLog(tmp_path / "a.jsonl", clock=clock)
    first = log.record({"event": "propose", "authorization": "Bearer abc"})
    clock.now = 60
    log.record({"event": "approve", "by": "mgr-7"})
    events = log.events()
    assert [e["seq"] for e in events] == [1, 2]
    assert [e["at"] for e in events] == [50, 60]
    assert first["authorization"] == "[REDACTED]"
    lines = (tmp_path / "a.jsonl").read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2 and json.loads(lines[0])["event"] == "propose"
    assert "Bearer abc" not in "".join(lines)


def test_audit_log_continues_sequence_after_reopen_and_is_empty_when_new(tmp_path):
    path = tmp_path / "a.jsonl"
    assert AuditLog(path).events() == []
    log = AuditLog(path, clock=Clock())
    log.record({"event": "one"})
    log.record({"event": "two"})
    again = AuditLog(path, clock=Clock())
    rec = again.record({"event": "three"})
    assert rec["seq"] == 3
    assert [e["event"] for e in again.events()] == ["one", "two", "three"]
