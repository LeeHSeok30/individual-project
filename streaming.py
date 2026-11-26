"""Exact maximum of the last k scores as new games arrive."""
from collections import deque


class RollingMax:
    """Keep the newest equal maximum. Only candidate games remain in memory."""

    def __init__(self, k):
        if not isinstance(k, int) or isinstance(k, bool) or k < 1:
            raise ValueError("k must be a positive integer")
        self._width = k
        self._games = 0
        self._candidates = deque()

    @property
    def candidate_count(self):
        return len(self._candidates)

    def push(self, score):
        """Accept one integer and return the maximum, or None during warm-up."""
        if not isinstance(score, int) or isinstance(score, bool):
            raise ValueError("score must be an integer")
        self._games += 1
        candidates = self._candidates
        if candidates and candidates[0][0] <= self._games - self._width:
            candidates.popleft()
        while candidates and score >= candidates[-1][1]:
            candidates.pop()
        candidates.append((self._games, score))
        if self._games >= self._width:
            return candidates[0][1]
        return None
