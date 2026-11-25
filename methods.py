"""Exact maxima of every complete window. Input: a finite sequence of integers."""
from collections import deque


def validate(x, k):
    if not isinstance(k, int) or isinstance(k, bool) or not 1 <= k <= len(x):
        raise ValueError("Expected an integer width in the range 1..len(scores)")


def scan(x, k):
    validate(x, k)
    out = []
    for start in range(len(x) - k + 1):
        best = x[start]
        for j in range(start + 1, start + k):
            if x[j] > best:
                best = x[j]
        out.append(best)
    return out


def monotone(x, k):
    validate(x, k)
    candidates = deque()
    out = []
    for i, value in enumerate(x):
        if candidates and candidates[0] <= i - k:
            candidates.popleft()
        while candidates and value >= x[candidates[-1]]:
            candidates.pop()
        candidates.append(i)
        if i >= k - 1:
            out.append(x[candidates[0]])
    return out


def block(x, k):
    validate(x, k)
    n = len(x)
    left = list(x)
    right = list(x)
    for i in range(1, n):
        if i % k:
            left[i] = max(left[i - 1], x[i])
    for i in range(n - 2, -1, -1):
        if (i + 1) % k:
            right[i] = max(right[i + 1], x[i])
    return [max(right[s], left[s + k - 1]) for s in range(n - k + 1)]


METHODS = (scan, monotone, block)
