import pytest

from w01_basics import count_vowels, greeting, is_working_hours, request_cost, sum_to


def test_ex01_greeting_basic():
    assert greeting("Shubham", 3) == "Shubham has 3 years of experience"


def test_ex01_greeting_other_values():
    assert greeting("Asha", 10) == "Asha has 10 years of experience"


def test_ex01_greeting_returns_a_string_not_none():
    assert isinstance(greeting("Asha", 1), str)


@pytest.mark.parametrize("hour, expected", [
    (8, False), (9, True), (12, True), (17, True), (18, False), (0, False), (23, False),
])
def test_ex02_is_working_hours(hour, expected):
    assert is_working_hours(hour) is expected


@pytest.mark.parametrize("n, expected", [(0, 0), (1, 1), (3, 6), (10, 55), (100, 5050)])
def test_ex03_sum_to(n, expected):
    assert sum_to(n) == expected


def test_ex04_count_vowels_basic():
    assert count_vowels("Badge Desk") == 3


def test_ex04_count_vowels_ignores_case():
    assert count_vowels("AEIOU") == 5


def test_ex04_count_vowels_none_and_empty():
    assert count_vowels("rhythm") == 0
    assert count_vowels("") == 0


@pytest.mark.parametrize("days, kwargs, expected", [
    (3, {}, 300),
    (4, {}, 400),
    (5, {}, 450),
    (5, {"rate": 200}, 900),
    (10, {}, 900),
    (0, {}, 0),
    (2, {"rate": 50}, 100),
])
def test_ex05_request_cost(days, kwargs, expected):
    assert request_cost(days, **kwargs) == pytest.approx(expected)
