"""Tests for week 34. Do not edit.

Three kinds of test:
  * examples and edge cases (empty, one element, duplicates, negatives);
  * small random inputs checked against a slow-but-obviously-correct oracle written in this file;
  * "big" tests with a time budget. The budgets are about 10x what a correct solution needs, so they
    pass on a slow laptop and fail an O(n^2) answer. If one of these fails but the small tests pass,
    your answer is correct and too slow: that is the lesson.
"""
import itertools
import random
import time
from collections import Counter

import pytest

import w34_dsa as m
from w34_dsa import ListNode, TreeNode


# ------------------------------------------------------------------ helpers
def fast(fn, budget, *args):
    """Run fn(*args); fail if it takes longer than `budget` seconds. Returns the result."""
    t0 = time.perf_counter()
    out = fn(*args)
    took = time.perf_counter() - t0
    assert took < budget, f"{fn.__name__} took {took:.2f}s on this input (budget {budget}s): too slow, think O(n) or O(n log n)"
    return out


def make_list(values):
    head = None
    for v in reversed(values):
        head = ListNode(v, head)
    return head


def to_values(head, limit=10**6):
    out = []
    while head is not None and len(out) < limit:
        out.append(head.val)
        head = head.next
    return out


def tree_from_level(values):
    """[3, 9, 20, None, None, 15, 7] -> tree (LeetCode-style level-order encoding)."""
    if not values or values[0] is None:
        return None
    nodes = [TreeNode(v) if v is not None else None for v in values]
    kids = iter(nodes[1:])
    for n in nodes:
        if n is None:
            continue
        n.left = next(kids, None)
        n.right = next(kids, None)
    return nodes[0]


def balanced(depth, counter=None):
    """A full binary tree with 2**depth - 1 nodes, values in BST order (so it is a valid BST)."""
    def build(lo, hi):
        if lo > hi:
            return None
        mid = (lo + hi) // 2
        return TreeNode(mid, build(lo, mid - 1), build(mid + 1, hi))
    return build(0, 2 ** depth - 2)


# ------------------------------------------------------------------ hash maps
def _valid_pair(nums, target, got):
    assert got is not None and len(got) == 2
    i, j = got
    assert 0 <= i < j < len(nums), "need i < j, both valid indices"
    assert nums[i] + nums[j] == target


def test_two_sum_examples():
    _valid_pair([2, 7, 11, 15], 9, m.two_sum([2, 7, 11, 15], 9))
    _valid_pair([3, 2, 4], 6, m.two_sum([3, 2, 4], 6))      # 3 + 3 would reuse index 0: wrong
    _valid_pair([3, 3], 6, m.two_sum([3, 3], 6))            # duplicates
    _valid_pair([-3, 4, 3, 90], 0, m.two_sum([-3, 4, 3, 90], 0))


def test_two_sum_none():
    assert m.two_sum([], 5) is None
    assert m.two_sum([5], 10) is None                       # one element cannot pair with itself
    assert m.two_sum([1, 2, 3], 100) is None


def test_two_sum_random_vs_oracle():
    rnd = random.Random(34)
    for _ in range(200):
        nums = [rnd.randint(-8, 8) for _ in range(rnd.randint(0, 9))]
        target = rnd.randint(-12, 12)
        exists = any(nums[i] + nums[j] == target for i, j in itertools.combinations(range(len(nums)), 2))
        got = m.two_sum(list(nums), target)
        if exists:
            _valid_pair(nums, target, got)
        else:
            assert got is None


def test_two_sum_big():
    n = 200_000
    nums = list(range(n))
    got = fast(m.two_sum, 2.0, nums, (n - 1) + (n - 2))     # the answer is the last two elements
    _valid_pair(nums, (n - 1) + (n - 2), got)


def _norm(groups):
    return sorted(sorted(g) for g in groups)


def test_group_anagrams():
    got = m.group_anagrams(["eat", "tea", "tan", "ate", "nat", "bat"])
    assert _norm(got) == [["ate", "eat", "tea"], ["bat"], ["nat", "tan"]]


def test_group_anagrams_edges():
    assert m.group_anagrams([]) == []
    assert _norm(m.group_anagrams([""])) == [[""]]
    assert _norm(m.group_anagrams(["a", "a", "b"])) == [["a", "a"], ["b"]]   # repeated word stays in its group
    assert _norm(m.group_anagrams(["ab", "abb", "ba"])) == [["ab", "ba"], ["abb"]]  # same letters, different counts


def test_top_k_frequent():
    assert m.top_k_frequent([1, 1, 1, 2, 2, 3], 2) == [1, 2]
    assert m.top_k_frequent([7], 1) == [7]
    assert m.top_k_frequent([4, 4, 4, 4, 5, 5, 5, 6, 6, 7], 3) == [4, 5, 6]
    assert m.top_k_frequent([-1, -1, 2], 1) == [-1]


def test_top_k_frequent_big():
    rnd = random.Random(1)
    distinct = 40_000
    nums = []
    for v in range(distinct):                      # value v appears (v % 5) + 1 times ... plus 3 heavy hitters
        nums.extend([v] * ((v % 5) + 1))
    nums.extend([-1] * 500 + [-2] * 400 + [-3] * 300)
    rnd.shuffle(nums)
    assert fast(m.top_k_frequent, 2.0, nums, 3) == [-1, -2, -3]


def test_subarray_sum_equals_k():
    assert m.subarray_sum_equals_k([1, 1, 1], 2) == 2
    assert m.subarray_sum_equals_k([1, 2, 3], 3) == 2               # [1,2] and [3]
    assert m.subarray_sum_equals_k([], 0) == 0
    assert m.subarray_sum_equals_k([0, 0, 0], 0) == 6               # zeros: every non-empty subarray
    assert m.subarray_sum_equals_k([1, -1, 0], 0) == 3              # negatives
    assert m.subarray_sum_equals_k([5], 5) == 1


def test_subarray_sum_random_vs_oracle():
    rnd = random.Random(7)
    for _ in range(200):
        nums = [rnd.randint(-3, 3) for _ in range(rnd.randint(0, 12))]
        k = rnd.randint(-4, 4)
        want = sum(1 for i in range(len(nums)) for j in range(i, len(nums)) if sum(nums[i:j + 1]) == k)
        assert m.subarray_sum_equals_k(list(nums), k) == want, (nums, k)


def test_subarray_sum_big():
    nums = [1, -1] * 50_000                                         # 100,000 elements
    got = fast(m.subarray_sum_equals_k, 2.0, nums, 0)
    # prefix sums alternate 1,0,1,0,...: 50,001 zeros and 50,000 ones -> C(50001,2) + C(50000,2)
    assert got == 50_001 * 50_000 // 2 + 50_000 * 49_999 // 2


# ------------------------------------------------------------------ two pointers, window
def test_pair_sum_sorted():
    _valid_pair([1, 2, 4, 7, 11], 9, m.pair_sum_sorted([1, 2, 4, 7, 11], 9))
    _valid_pair([2, 2], 4, m.pair_sum_sorted([2, 2], 4))
    _valid_pair([-5, -1, 0, 3, 8], 3, m.pair_sum_sorted([-5, -1, 0, 3, 8], 3))
    assert m.pair_sum_sorted([], 1) is None
    assert m.pair_sum_sorted([4], 8) is None                        # must not pair an element with itself
    assert m.pair_sum_sorted([1, 2, 3], 10) is None


def test_pair_sum_sorted_big():
    n = 200_000
    nums = list(range(n))
    got = fast(m.pair_sum_sorted, 2.0, nums, (n - 1) + (n - 2))
    _valid_pair(nums, (n - 1) + (n - 2), got)


def test_longest_unique_substring():
    assert m.longest_unique_substring("abcabcbb") == 3
    assert m.longest_unique_substring("bbbbb") == 1
    assert m.longest_unique_substring("pwwkew") == 3
    assert m.longest_unique_substring("") == 0
    assert m.longest_unique_substring("a") == 1
    assert m.longest_unique_substring("abba") == 2                   # the classic: left pointer must never move back
    assert m.longest_unique_substring("tmmzuxt") == 5


def test_longest_unique_substring_random_vs_oracle():
    rnd = random.Random(3)
    for _ in range(300):
        s = "".join(rnd.choice("abc") for _ in range(rnd.randint(0, 14)))
        want = max((j - i for i in range(len(s)) for j in range(i, len(s) + 1) if len(set(s[i:j])) == j - i), default=0)
        assert m.longest_unique_substring(s) == want, s


def test_longest_unique_substring_big():
    s = "".join(chr(0x4E00 + i) for i in range(20_000)) * 2             # 40,000 chars, 20,000 distinct
    assert fast(m.longest_unique_substring, 1.5, s) == 20_000


def test_max_sum_window():
    assert m.max_sum_window([2, 1, 5, 1, 3, 2], 3) == 9
    assert m.max_sum_window([-1, -2, -3, -4], 2) == -3               # all negative: do not start best at 0
    assert m.max_sum_window([5], 1) == 5
    assert m.max_sum_window([1, 2, 3], 3) == 6                       # window as long as the list
    assert m.max_sum_window([4, 2, 1, 7], 1) == 7


def test_max_sum_window_errors():
    for bad in (0, -1, 4):
        with pytest.raises(ValueError):
            m.max_sum_window([1, 2, 3], bad)
    with pytest.raises(ValueError):
        m.max_sum_window([], 1)


def test_max_sum_window_big():
    n = 200_000
    nums = [(i * 37) % 101 - 50 for i in range(n)]
    k = 100_000
    want = sum(nums[:k])
    cur = want
    for i in range(k, n):
        cur += nums[i] - nums[i - k]
        want = max(want, cur)
    assert fast(m.max_sum_window, 1.5, nums, k) == want


# ------------------------------------------------------------------ stack
@pytest.mark.parametrize("s,ok", [
    ("", True), ("()", True), ("()[]{}", True), ("{[()]}", True), ("([{}])()", True),
    ("(", False), (")", False), ("(]", False), ("([)]", False), ("((", False), ("))", False),
    ("{[}", False), ("]", False), ("(()", False),
])
def test_valid_parentheses(s, ok):
    assert m.valid_parentheses(s) is ok


def test_valid_parentheses_big():
    n = 200_000
    assert fast(m.valid_parentheses, 1.5, "(" * n + ")" * n) is True
    assert fast(m.valid_parentheses, 1.5, "(" * n + ")" * (n - 1)) is False


# ------------------------------------------------------------------ binary search, sorting
def test_binary_search():
    nums = [-5, -1, 0, 3, 8, 12]
    for i, v in enumerate(nums):
        assert m.binary_search(nums, v) == i
    assert m.binary_search(nums, 4) == -1
    assert m.binary_search(nums, -100) == -1
    assert m.binary_search(nums, 100) == -1
    assert m.binary_search([], 1) == -1
    assert m.binary_search([7], 7) == 0
    assert m.binary_search([7], 8) == -1


def test_binary_search_all_sizes():
    for n in range(0, 40):
        nums = list(range(0, 2 * n, 2))
        for i, v in enumerate(nums):
            assert m.binary_search(nums, v) == i
        for v in (-1, 1, 2 * n - 1, 2 * n):
            assert m.binary_search(nums, v) == -1


def test_binary_search_big():
    nums = list(range(1_000_000))
    t0 = time.perf_counter()
    for t in range(999_999, 997_999, -1):                           # 2,000 searches near the far end
        assert m.binary_search(nums, t) == t
    took = time.perf_counter() - t0
    assert took < 1.5, f"2,000 searches took {took:.2f}s: this is not O(log n)"


def test_first_last_position():
    assert m.first_last_position([5, 7, 7, 8, 8, 10], 8) == [3, 4]
    assert m.first_last_position([5, 7, 7, 8, 8, 10], 6) == [-1, -1]
    assert m.first_last_position([], 0) == [-1, -1]
    assert m.first_last_position([1], 1) == [0, 0]
    assert m.first_last_position([2, 2, 2, 2], 2) == [0, 3]
    assert m.first_last_position([1, 2, 2, 2], 1) == [0, 0]
    assert m.first_last_position([1, 2, 2, 2], 2) == [1, 3]
    assert m.first_last_position([1, 1, 2], 3) == [-1, -1]


def test_first_last_position_random_vs_oracle():
    rnd = random.Random(5)
    for _ in range(300):
        nums = sorted(rnd.randint(0, 6) for _ in range(rnd.randint(0, 12)))
        t = rnd.randint(-1, 7)
        idx = [i for i, v in enumerate(nums) if v == t]
        want = [idx[0], idx[-1]] if idx else [-1, -1]
        assert m.first_last_position(list(nums), t) == want, (nums, t)


def test_first_last_position_big():
    nums = [3] * 1_000_000
    t0 = time.perf_counter()
    for _ in range(200):
        assert m.first_last_position(nums, 3) == [0, 999_999]
    took = time.perf_counter() - t0
    assert took < 1.5, f"200 calls took {took:.2f}s: a linear scan is not good enough"


def test_merge_intervals():
    assert m.merge_intervals([[1, 3], [2, 6], [8, 10], [15, 18]]) == [[1, 6], [8, 10], [15, 18]]
    assert m.merge_intervals([[1, 4], [4, 5]]) == [[1, 5]]               # touching merges
    assert m.merge_intervals([[8, 10], [1, 3], [2, 6]]) == [[1, 6], [8, 10]]   # unsorted input
    assert m.merge_intervals([[1, 10], [2, 3], [4, 5]]) == [[1, 10]]     # contained intervals: keep the larger end
    assert m.merge_intervals([]) == []
    assert m.merge_intervals([[2, 2]]) == [[2, 2]]
    assert m.merge_intervals([[1, 2], [3, 4]]) == [[1, 2], [3, 4]]


def test_merge_intervals_does_not_mutate_input():
    data = [[5, 6], [1, 3], [2, 4]]
    snapshot = [list(x) for x in data]
    m.merge_intervals(data)
    assert data == snapshot


def test_merge_intervals_random_vs_oracle():
    rnd = random.Random(9)
    for _ in range(200):
        iv = []
        for _ in range(rnd.randint(0, 8)):
            a = rnd.randint(0, 20)
            iv.append([a, a + rnd.randint(0, 5)])
        covered = set()
        for a, b in iv:
            covered.update(range(a * 2, b * 2 + 1))          # doubled so "touching" is distinguishable from "adjacent"
        got = m.merge_intervals([list(x) for x in iv])
        for (a, b), (c, d) in zip(got, got[1:]):
            assert b < c, "result intervals must not touch or overlap"
        got_cov = set()
        for a, b in got:
            got_cov.update(range(a * 2, b * 2 + 1))
        assert got_cov == covered, iv


def test_merge_intervals_big():
    rnd = random.Random(2)
    iv = []
    for i in range(100_000):
        a = i * 3
        iv.append([a, a + rnd.choice((1, 2, 4))])                # chains of overlaps separated by gaps
    rnd.shuffle(iv)
    got = fast(m.merge_intervals, 3.0, iv)
    assert got == sorted(got) and all(x[1] < y[0] for x, y in zip(got, got[1:]))
    assert len(got) > 1


# ------------------------------------------------------------------ linked lists
def test_reverse_list():
    assert to_values(m.reverse_list(make_list([1, 2, 3, 4]))) == [4, 3, 2, 1]
    assert to_values(m.reverse_list(make_list([1]))) == [1]
    assert m.reverse_list(None) is None
    assert to_values(m.reverse_list(make_list([1, 2]))) == [2, 1]


def test_reverse_list_relinks_nodes_and_terminates():
    nodes = [ListNode(i) for i in range(5)]
    for a, b in zip(nodes, nodes[1:]):
        a.next = b
    head = m.reverse_list(nodes[0])
    assert head is nodes[4]
    assert nodes[0].next is None, "the old head must become the tail (otherwise you made a cycle)"


def test_reverse_list_big():
    n = 100_000
    out = fast(m.reverse_list, 1.5, make_list(list(range(n))))
    assert out.val == n - 1
    assert to_values(out) == list(range(n - 1, -1, -1))


def test_has_cycle():
    assert m.has_cycle(None) is False
    assert m.has_cycle(make_list([1])) is False
    assert m.has_cycle(make_list([1, 2, 3, 4])) is False
    a, b, c = ListNode(1), ListNode(2), ListNode(3)
    a.next, b.next, c.next = b, c, b
    assert m.has_cycle(a) is True                                   # cycle not at the head
    a2 = ListNode(1)
    a2.next = a2
    assert m.has_cycle(a2) is True                                  # one node pointing at itself
    x, y = ListNode(1), ListNode(2)
    x.next, y.next = y, x
    assert m.has_cycle(x) is True


def test_has_cycle_equal_values_are_not_a_cycle():
    assert m.has_cycle(make_list([7, 7, 7, 7, 7])) is False         # compare nodes with `is`, not values


def test_has_cycle_big():
    n = 200_000
    head = make_list(list(range(n)))
    assert fast(m.has_cycle, 1.5, head) is False
    tail = head
    while tail.next:
        tail = tail.next
    tail.next = head.next.next                                      # cycle back to node 2
    assert fast(m.has_cycle, 1.5, head) is True


def test_merge_two_sorted():
    assert to_values(m.merge_two_sorted(make_list([1, 2, 4]), make_list([1, 3, 4]))) == [1, 1, 2, 3, 4, 4]
    assert m.merge_two_sorted(None, None) is None
    assert to_values(m.merge_two_sorted(None, make_list([0]))) == [0]
    assert to_values(m.merge_two_sorted(make_list([5, 6]), None)) == [5, 6]
    assert to_values(m.merge_two_sorted(make_list([1, 2, 3]), make_list([7, 8]))) == [1, 2, 3, 7, 8]   # one list runs out first
    assert to_values(m.merge_two_sorted(make_list([7, 8]), make_list([1, 2, 3]))) == [1, 2, 3, 7, 8]


def test_merge_two_sorted_relinks_and_is_stable():
    a1, a2 = ListNode(1), ListNode(2)
    a1.next = a2
    b1 = ListNode(1)
    head = m.merge_two_sorted(a1, b1)
    assert head is a1 and head.next is b1 and head.next.next is a2, "equal values: take from a first, reuse the nodes"


# ------------------------------------------------------------------ trees
def test_level_order():
    t = tree_from_level([3, 9, 20, None, None, 15, 7])
    assert m.level_order(t) == [[3], [9, 20], [15, 7]]
    assert m.level_order(None) == []
    assert m.level_order(TreeNode(1)) == [[1]]
    left_only = TreeNode(1, TreeNode(2, TreeNode(3)))
    assert m.level_order(left_only) == [[1], [2], [3]]
    right_only = TreeNode(1, None, TreeNode(2))
    assert m.level_order(right_only) == [[1], [2]]


def test_level_order_big():
    t = balanced(16)                                                # 65,535 nodes, 16 levels
    out = fast(m.level_order, 1.5, t)
    assert [len(level) for level in out] == [2 ** i for i in range(16)]


def test_max_depth():
    assert m.max_depth(None) == 0
    assert m.max_depth(TreeNode(1)) == 1
    assert m.max_depth(tree_from_level([3, 9, 20, None, None, 15, 7])) == 3
    assert m.max_depth(TreeNode(1, TreeNode(2, TreeNode(3, TreeNode(4))))) == 4          # left spine
    assert m.max_depth(TreeNode(1, None, TreeNode(2, None, TreeNode(3)))) == 3           # right spine
    assert m.max_depth(TreeNode(1, TreeNode(2), TreeNode(3, None, TreeNode(4)))) == 3


def test_max_depth_big():
    assert fast(m.max_depth, 1.5, balanced(16)) == 16


def test_is_valid_bst():
    assert m.is_valid_bst(None) is True
    assert m.is_valid_bst(TreeNode(2, TreeNode(1), TreeNode(3))) is True
    assert m.is_valid_bst(TreeNode(5, TreeNode(1), TreeNode(4, TreeNode(3), TreeNode(6)))) is False
    # the classic trap: every node is fine against its own children, but 3 sits in the right subtree of 5
    trap = TreeNode(5, TreeNode(4), TreeNode(6, TreeNode(3), TreeNode(7)))
    assert m.is_valid_bst(trap) is False
    assert m.is_valid_bst(TreeNode(2, TreeNode(2), None)) is False          # duplicates are invalid
    assert m.is_valid_bst(TreeNode(2, None, TreeNode(2))) is False
    assert m.is_valid_bst(TreeNode(1)) is True
    assert m.is_valid_bst(TreeNode(-(2 ** 31), None, TreeNode(2 ** 31 - 1))) is True    # extreme values: no sentinel clash
    assert m.is_valid_bst(TreeNode(0, TreeNode(-1), None)) is True


def test_is_valid_bst_big():
    assert fast(m.is_valid_bst, 1.5, balanced(16)) is True


# ------------------------------------------------------------------ graphs
def grid_of(rows):
    return [list(r) for r in rows]


def test_num_islands():
    assert m.num_islands(grid_of(["11110", "11010", "11000", "00000"])) == 1
    assert m.num_islands(grid_of(["11000", "11000", "00100", "00011"])) == 3
    assert m.num_islands([]) == 0
    assert m.num_islands(grid_of(["0"])) == 0
    assert m.num_islands(grid_of(["1"])) == 1
    assert m.num_islands(grid_of(["101", "010", "101"])) == 5            # diagonals are NOT connected
    assert m.num_islands(grid_of(["1", "0", "1"])) == 2
    assert m.num_islands(grid_of(["111", "010", "111"])) == 1            # U shape joined by the middle


def test_num_islands_does_not_modify_input():
    g = grid_of(["110", "001", "001"])
    snapshot = [list(r) for r in g]
    assert m.num_islands(g) == 2
    assert g == snapshot


def test_num_islands_random_vs_oracle():
    rnd = random.Random(11)

    def oracle(g):
        R, C = len(g), len(g[0])
        parent = {(r, c): (r, c) for r in range(R) for c in range(C) if g[r][c] == "1"}

        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x
        for (r, c) in list(parent):
            for nb in ((r + 1, c), (r, c + 1)):
                if nb in parent:
                    parent[find(nb)] = find((r, c))
        return len({find(x) for x in parent})

    for _ in range(200):
        R, C = rnd.randint(1, 6), rnd.randint(1, 6)
        g = [[rnd.choice("10") for _ in range(C)] for _ in range(R)]
        assert m.num_islands(g) == oracle(g), g


def test_num_islands_big():
    n = 200
    all_land = [["1"] * n for _ in range(n)]                          # one island, 40,000 cells deep
    assert fast(m.num_islands, 2.0, all_land) == 1
    checker = [["1" if (r + c) % 2 == 0 else "0" for c in range(n)] for r in range(n)]
    assert fast(m.num_islands, 2.0, checker) == n * n // 2           # 20,000 one-cell islands


def _is_topological(n, edges, order):
    if sorted(order) != list(range(n)):
        return False
    pos = {v: i for i, v in enumerate(order)}
    return all(pos[a] < pos[b] for a, b in edges)


def test_topo_sort():
    edges = [(5, 2), (5, 0), (4, 0), (4, 1), (2, 3), (3, 1)]
    order = m.topo_sort(6, edges)
    assert _is_topological(6, edges, order)
    assert m.topo_sort(0, []) == []
    assert m.topo_sort(1, []) == [0]
    assert sorted(m.topo_sort(3, [])) == [0, 1, 2]                    # no edges: any order, but every node once
    assert _is_topological(4, [(0, 1), (0, 2), (1, 3), (2, 3)], m.topo_sort(4, [(0, 1), (0, 2), (1, 3), (2, 3)]))


def test_topo_sort_cycles():
    assert m.topo_sort(2, [(0, 1), (1, 0)]) == []
    assert m.topo_sort(3, [(0, 1), (1, 2), (2, 0)]) == []
    assert m.topo_sort(1, [(0, 0)]) == []                             # self-loop
    assert m.topo_sort(4, [(0, 1), (2, 3), (3, 2)]) == []             # a cycle in one component only


def test_topo_sort_big():
    n = 100_000
    edges = [(i, i + 1) for i in range(n - 1)]
    order = fast(m.topo_sort, 2.0, n, edges)
    assert order == list(range(n))
    assert fast(m.topo_sort, 2.0, n, edges + [(n - 1, 0)]) == []


# ------------------------------------------------------------------ dynamic programming
def test_climb_stairs():
    assert [m.climb_stairs(n) for n in range(1, 9)] == [1, 2, 3, 5, 8, 13, 21, 34]
    assert m.climb_stairs(25) == 121393


def test_climb_stairs_big():
    assert fast(m.climb_stairs, 0.5, 35) == 14930352                 # naive recursion makes ~30 million calls


def test_rob():
    assert m.rob([]) == 0
    assert m.rob([7]) == 7
    assert m.rob([2, 1]) == 2
    assert m.rob([1, 2, 3, 1]) == 4
    assert m.rob([2, 7, 9, 3, 1]) == 12
    assert m.rob([2, 1, 1, 2]) == 4                                  # greedy "take the bigger neighbour" gives 3
    assert m.rob([0, 0, 0]) == 0
    assert m.rob([5, 1, 1, 5]) == 10


def test_rob_random_vs_oracle():
    rnd = random.Random(13)
    for _ in range(200):
        nums = [rnd.randint(0, 9) for _ in range(rnd.randint(0, 10))]
        best = 0
        for mask in range(1 << len(nums)):
            if mask & (mask >> 1):
                continue
            best = max(best, sum(nums[i] for i in range(len(nums)) if mask >> i & 1))
        assert m.rob(list(nums)) == best, nums


def test_rob_big():
    nums = [(i * 7919) % 1000 for i in range(100_000)]
    take = skip = 0
    for x in nums:
        take, skip = skip + x, max(take, skip)
    assert fast(m.rob, 1.5, nums) == max(take, skip)


def test_coin_change():
    assert m.coin_change([1, 2, 5], 11) == 3
    assert m.coin_change([2], 3) == -1
    assert m.coin_change([1], 0) == 0
    assert m.coin_change([2], 0) == 0
    assert m.coin_change([1], 2) == 2
    assert m.coin_change([1, 3, 4], 6) == 2                          # greedy takes 4+1+1 = 3 coins: wrong
    assert m.coin_change([5, 10], 3) == -1
    assert m.coin_change([], 7) == -1
    assert m.coin_change([3, 7], 1) == -1


def test_coin_change_random_vs_oracle():
    rnd = random.Random(17)
    for _ in range(150):
        coins = sorted(set(rnd.randint(1, 7) for _ in range(rnd.randint(1, 3))))
        amount = rnd.randint(0, 25)
        best = [0] + [None] * amount
        for a in range(1, amount + 1):
            options = [best[a - c] + 1 for c in coins if c <= a and best[a - c] is not None]
            best[a] = min(options) if options else None
        want = -1 if best[amount] is None else best[amount]
        assert m.coin_change(list(coins), amount) == want, (coins, amount)


def test_coin_change_big():
    # A famous case where plain recursion never finishes. If this test hangs, add a cache or a table.
    assert fast(m.coin_change, 2.0, [186, 419, 83, 408], 6249) == 20
    assert fast(m.coin_change, 2.0, [1, 5, 10, 25, 50], 20_000) == 400
