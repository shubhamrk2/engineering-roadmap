from datetime import date

import pytest

from w04_models import AccessRequest, Stack, Status


def make(**overrides):
    args = dict(
        id="req-1",
        employee_id="e-902",
        site_id="BLR-01",
        starts_on=date(2026, 11, 2),
        ends_on=date(2026, 11, 6),
    )
    args.update(overrides)
    return AccessRequest(**args)


def test_ex01_defaults():
    r = make()
    assert r.status is Status.PENDING
    assert r.reasons == []


def test_ex01_positional_construction_order():
    r = AccessRequest("req-9", "e-1", "HYD-01", date(2026, 11, 2), date(2026, 11, 2))
    assert (r.id, r.employee_id, r.site_id) == ("req-9", "e-1", "HYD-01")


def test_ex01_duration_days_is_inclusive():
    assert make().duration_days == 5
    assert make(ends_on=date(2026, 11, 2)).duration_days == 1


def test_ex01_duration_days_is_a_property_not_a_method():
    assert isinstance(make().duration_days, int)


def test_ex01_end_before_start_is_rejected():
    with pytest.raises(ValueError):
        make(starts_on=date(2026, 11, 6), ends_on=date(2026, 11, 2))


def test_ex01_each_request_gets_its_own_reasons_list():
    a, b = make(), make()
    a.reasons.append("visitor")
    assert b.reasons == []


def test_ex01_equal_when_all_fields_equal():
    assert make() == make()
    assert make() != make(id="req-2")


def test_ex02_approve_from_pending():
    r = make()
    r.approve()
    assert r.status is Status.APPROVED


def test_ex02_approve_twice_is_an_error():
    r = make()
    r.approve()
    with pytest.raises(RuntimeError):
        r.approve()


def test_ex02_cannot_approve_a_rejected_request():
    r = make(status=Status.REJECTED)
    with pytest.raises(RuntimeError):
        r.approve()


def test_ex03_stack_is_last_in_first_out():
    s = Stack()
    s.push(1)
    s.push(2)
    s.push(3)
    assert s.pop() == 3
    assert s.pop() == 2
    assert s.pop() == 1


def test_ex03_stack_peek_does_not_remove():
    s = Stack()
    s.push("a")
    assert s.peek() == "a"
    assert s.size() == 1


def test_ex03_stack_is_empty_and_size():
    s = Stack()
    assert s.is_empty() is True
    assert s.size() == 0
    s.push(1)
    assert s.is_empty() is False
    assert s.size() == 1


def test_ex03_pop_and_peek_on_empty_raise_index_error():
    s = Stack()
    with pytest.raises(IndexError):
        s.pop()
    with pytest.raises(IndexError):
        s.peek()


def test_ex03_two_stacks_do_not_share_items():
    a, b = Stack(), Stack()
    a.push(1)
    assert b.is_empty()
