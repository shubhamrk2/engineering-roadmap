"""Week 4: classes, dataclasses, enums, validation.

Replace each stub with your own code.
Run:  pytest week04
"""
from dataclasses import dataclass, field  # noqa: F401  (you will need these)
from datetime import date  # noqa: F401
from enum import Enum


class Status(str, Enum):
    """Given to you: the allowed states of an access request."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class AccessRequest:
    """ex01 + ex02. Replace this whole class with a @dataclass.

    Fields, in this order:
        id: str
        employee_id: str
        site_id: str
        starts_on: date
        ends_on: date
        status: Status = Status.PENDING
        reasons: list[str]   (each request gets its OWN empty list by default)

    Rules:
        - ends_on before starts_on -> raise ValueError when the object is created.
        - duration_days (a property, not a method): days from starts_on to ends_on, inclusive.
          starts 2 Nov, ends 6 Nov -> 5.
        - approve(): only a PENDING request can be approved; it becomes APPROVED.
          Approving any other state raises RuntimeError.
    """

    def __init__(self, *args, **kwargs):
        raise NotImplementedError("Replace this class with a @dataclass")


class Stack:
    """ex03. A last-in, first-out stack, written as a plain class.

    Methods:
        push(item)    add to the top
        pop()         remove and return the top item; IndexError on an empty stack
        peek()        return the top item without removing it; IndexError on an empty stack
        is_empty()    True when there are no items
        size()        number of items
    """

    def __init__(self):
        raise NotImplementedError
