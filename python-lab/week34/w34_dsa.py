"""Week 34 (Sheet 34, ai-dsa.html): classic interview functions, one per pattern.

Replace every `raise NotImplementedError` with your own code.
Run:  pytest week34            (from the python-lab folder)
      pytest week34 -k two_sum -x

ListNode and TreeNode are given to you. Read the docstring of each function: it is the specification.
Several tests feed large inputs and have a time budget. A correct but O(n^2) answer will FAIL them on
purpose: the point of this week is the complexity, not only the output.

Some tests also use inputs deep enough that recursion hits Python's default limit of 1000 frames.
Where a docstring says "iterative", it means it.
"""
from __future__ import annotations

from typing import Optional


class ListNode:
    """Given. A singly linked list node."""

    def __init__(self, val: int = 0, next: "Optional[ListNode]" = None):
        self.val = val
        self.next = next


class TreeNode:
    """Given. A binary tree node."""

    def __init__(self, val: int = 0, left: "Optional[TreeNode]" = None, right: "Optional[TreeNode]" = None):
        self.val = val
        self.left = left
        self.right = right


# ---------------------------------------------------------------- hash maps, arrays, strings
def two_sum(nums: list[int], target: int) -> Optional[list[int]]:
    """Return [i, j] with i < j and nums[i] + nums[j] == target, or None if there is no such pair.
    The input is NOT sorted and may contain duplicates and negatives. Must run in O(n) on average."""
    raise NotImplementedError


def group_anagrams(words: list[str]) -> list[list[str]]:
    """Group words that are anagrams of each other, e.g. ["eat","tea","tan","ate","nat","bat"] ->
    [["eat","tea","ate"],["tan","nat"],["bat"]]. Group order and order inside a group do not matter.
    Words are lowercase. The empty string is a valid word (it forms its own group)."""
    raise NotImplementedError


def top_k_frequent(nums: list[int], k: int) -> list[int]:
    """Return the k most frequent values, most frequent first. The tests never contain ties that
    would make the answer ambiguous. Must beat O(n * distinct): the big test has about 120,000 numbers and 40,000 distinct values."""
    raise NotImplementedError


def subarray_sum_equals_k(nums: list[int], k: int) -> int:
    """Count the contiguous, non-empty subarrays whose sum equals k. nums may contain negatives and
    zeros (so a sliding window does not work: use prefix sums and a dict). Must be O(n)."""
    raise NotImplementedError


# ---------------------------------------------------------------- two pointers, sliding window
def pair_sum_sorted(nums: list[int], target: int) -> Optional[list[int]]:
    """nums is sorted ascending. Return [i, j] with i < j and nums[i] + nums[j] == target, or None.
    Use two pointers: O(n) time, O(1) extra space."""
    raise NotImplementedError


def longest_unique_substring(s: str) -> int:
    """Length of the longest substring of s with no repeated character. "" -> 0.
    Sliding window, O(n). The tests include a 40,000-character string of distinct characters."""
    raise NotImplementedError


def max_sum_window(nums: list[int], k: int) -> int:
    """Largest sum of any k consecutive elements. Raise ValueError if k <= 0 or k > len(nums).
    Slide the window; do not re-add k numbers each step. O(n)."""
    raise NotImplementedError


# ---------------------------------------------------------------- stack
def valid_parentheses(s: str) -> bool:
    """True if every ( [ { is closed by the matching ) ] } in the right order. "" is valid.
    Characters other than brackets do not appear in the tests."""
    raise NotImplementedError


# ---------------------------------------------------------------- binary search, sorting
def binary_search(nums: list[int], target: int) -> int:
    """nums is sorted ascending with distinct values. Return the index of target, or -1. O(log n).
    Do not use list.index or `in`: the tests run 2,000 searches over 1,000,000 numbers."""
    raise NotImplementedError


def first_last_position(nums: list[int], target: int) -> list[int]:
    """nums is sorted ascending and MAY contain duplicates. Return [first_index, last_index] of target,
    or [-1, -1]. Two binary searches, O(log n)."""
    raise NotImplementedError


def merge_intervals(intervals: list[list[int]]) -> list[list[int]]:
    """Merge overlapping intervals. [[1,3],[2,6],[8,10]] -> [[1,6],[8,10]]. Intervals that merely touch
    ([1,4],[4,5]) DO merge. The input is not sorted and must not be modified. O(n log n)."""
    raise NotImplementedError


# ---------------------------------------------------------------- linked lists
def reverse_list(head: Optional[ListNode]) -> Optional[ListNode]:
    """Reverse a singly linked list and return the new head. Iterative: the tests use 100,000 nodes."""
    raise NotImplementedError


def has_cycle(head: Optional[ListNode]) -> bool:
    """True if following .next from head ever revisits a node. Floyd's tortoise and hare: O(1) space.
    The tests include a 200,000-node list."""
    raise NotImplementedError


def merge_two_sorted(a: Optional[ListNode], b: Optional[ListNode]) -> Optional[ListNode]:
    """Merge two sorted linked lists into one sorted list by relinking nodes. Return the head.
    Either input may be None. When values are equal, take from `a` first (stable)."""
    raise NotImplementedError


# ---------------------------------------------------------------- trees
def level_order(root: Optional[TreeNode]) -> list[list[int]]:
    """Breadth-first traversal: a list of levels, each a list of values left to right. None -> []."""
    raise NotImplementedError


def max_depth(root: Optional[TreeNode]) -> int:
    """Number of nodes on the longest root-to-leaf path. None -> 0."""
    raise NotImplementedError


def is_valid_bst(root: Optional[TreeNode]) -> bool:
    """True if the tree is a valid binary search tree: for EVERY node, all values in its left subtree are
    smaller and all values in its right subtree are larger (strictly; duplicates make it invalid).
    Checking only each node against its direct children is the classic wrong answer."""
    raise NotImplementedError


# ---------------------------------------------------------------- graphs
def num_islands(grid: list[list[str]]) -> int:
    """grid holds "1" (land) and "0" (water). Count 4-connected groups of land. Do not modify the input.
    Iterative traversal only: the tests include a 200 x 200 grid that is all land (a recursive DFS would
    be 40,000 frames deep and crash)."""
    raise NotImplementedError


def topo_sort(n: int, edges: list[tuple[int, int]]) -> list[int]:
    """Nodes are 0..n-1. An edge (a, b) means a must come before b. Return any valid order, or an
    EMPTY list if the graph has a cycle. Kahn's algorithm (indegrees + queue), O(n + e).
    The tests include a 100,000-node chain."""
    raise NotImplementedError


# ---------------------------------------------------------------- dynamic programming
def climb_stairs(n: int) -> int:
    """Ways to climb n stairs taking 1 or 2 steps at a time. climb_stairs(1) == 1, (2) == 2, (3) == 3.
    n >= 1. The test calls n = 35 under a time budget: plain recursion without a cache is too slow."""
    raise NotImplementedError


def rob(nums: list[int]) -> int:
    """House robber: maximum sum of non-adjacent elements (all values >= 0). [] -> 0.
    The tests use 100,000 houses, deeper than the recursion limit: tabulate (bottom-up)."""
    raise NotImplementedError


def coin_change(coins: list[int], amount: int) -> int:
    """Fewest coins (unlimited supply of each) that make `amount`, or -1 if impossible. amount 0 -> 0.
    WARNING: plain recursion with no memo is exponential. If the big test seems to hang, press Ctrl+C
    and add a cache or a table."""
    raise NotImplementedError
