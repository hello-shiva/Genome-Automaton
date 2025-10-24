"""
Pushdown Automaton (PDA) Engine
Detects complementary palindromic sequences (e.g., hairpin-like patterns)
within a DNA string. We provide an efficient finder that expands around
centers and checks reverse-complement symmetry.

This class also provides a simple step() that logs push-style behavior for
visual continuity, while the actual matches are computed in find_all_matches.
"""

from typing import List, Tuple

from automata_base import BaseAutomaton, AutomataType


def _comp(base: str) -> str:
    return {"A": "T", "T": "A", "G": "C", "C": "G"}.get(base, "?")


class PDA(BaseAutomaton):
    def __init__(self, pattern: str = "PALINDROME", min_len: int = 4):
        super().__init__(pattern, AutomataType.PDA)
        self.min_len = max(2, int(min_len))
        self.stack: List[str] = []
        self.pos = 0
        self.mode = "push"  # UI-friendly label; not a formal construction here

    def reset(self) -> None:
        self.stack.clear()
        self.pos = 0
        self.mode = "push"

    # Visualization helpers
    def get_type(self):
        return AutomataType.PDA

    def get_stack(self):
        return list(self.stack)

    def get_control_state(self):
        return self.mode

    def step(self, symbol: str):
        # For logging only: push current symbol; periodically pop to simulate
        # comparison when stack is large. This keeps the transition log
        # informative without constraining actual detection.
        symbol = symbol.upper()
        before = list(self.stack)
        action = "PUSH"
        self.stack.append(symbol)
        self.pos += 1
        if len(self.stack) > 8:  # arbitrary pop phase for demo visuals
            self.mode = "pop"
            self.stack.pop(0)
            action = "SHIFT"
        else:
            self.mode = "push"
        desc = f"Read '{symbol}': mode={self.mode}, {action}, stack={''.join(before)}→{''.join(self.stack)}"
        # Acceptance is not determined incrementally here
        return (self.mode, False, desc)

    def get_state_description(self, state) -> str:
        if self.mode == "pop":
            return f"Stack sliding (size {len(self.stack)})"
        return f"Scanning (stack {len(self.stack)})"

    # --------- Core palindrome finder ---------
    def find_all_matches(self, sequence: str) -> List[Tuple[int, int]]:
        s = sequence.upper()
        n = len(s)
        matches: List[Tuple[int, int]] = []

        def expand(l: int, r: int):
            # expand while s[l] complements s[r]
            while l >= 0 and r < n and _comp(s[l]) == s[r]:
                l -= 1
                r += 1
            # after loop, last valid was (l+1, r-1)
            L = l + 1
            R = r - 1
            if R - L + 1 >= self.min_len:
                matches.append((L, R))

        # even-length complement palindromes around centers (i, i+1)
        for i in range(n - 1):
            expand(i, i + 1)

        # odd-length variants are uncommon for perfect complement palindromes;
        # skip for clarity. Could be added by expand(i-1, i+1) if needed.

        # de-duplicate and sort
        matches = sorted(set(matches))
        return matches
