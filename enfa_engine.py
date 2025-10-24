"""
Epsilon-NFA (ε-NFA) Engine
Matches a head motif, a variable-length spacer (min..max bases), then a tail
motif. Example input: "TATA{1,10}TATA" for a promoter-like box with flexible
spacing.

The engine keeps nondeterministic states covering:
 - progress in head motif
 - count within spacer
 - progress in tail motif for each feasible spacer length
"""

from dataclasses import dataclass
from typing import List, Set, Tuple

from automata_base import BaseAutomaton, AutomataType


@dataclass(frozen=True)
class ENFAState:
    phase: str  # 'head', 'spacer', 'tail'
    k: int      # progress in current phase (for spacer: count so far)


def _parse_enfa_pattern(spec: str) -> Tuple[str, int, int, str]:
    """Parse patterns like HEAD{min,max}TAIL.
    Returns (head, min_gap, max_gap, tail). Raises ValueError if invalid.
    """
    s = (spec or "").upper()
    if "{" not in s or "}" not in s:
        raise ValueError("Epsilon-NFA expects pattern like HEAD{m,n}TAIL, e.g., TATA{1,10}TATA")
    head, rest = s.split("{", 1)
    rng, tail = rest.split("}", 1)
    if "," in rng:
        a, b = rng.split(",", 1)
        min_gap = int(a)
        max_gap = int(b)
    else:
        min_gap = max_gap = int(rng)
    if min_gap < 0 or max_gap < min_gap:
        raise ValueError("Invalid spacer range")
    return head, min_gap, max_gap, tail


class EpsilonNFA(BaseAutomaton):
    def __init__(self, pattern: str):
        super().__init__(pattern, AutomataType.ENFA)
        self.head, self.min_gap, self.max_gap, self.tail = _parse_enfa_pattern(pattern)
        self.current_states: Set[ENFAState] = set()
        self.reset()

    # ----- Visualization adapter -----
    def get_type(self):
        return AutomataType.ENFA

    def get_states(self) -> List[ENFAState]:
        states: List[ENFAState] = []
        # head
        for k in range(len(self.head) + 1):
            states.append(ENFAState("head", k))
        # spacer
        for g in range(self.max_gap + 1):
            states.append(ENFAState("spacer", g))
        # tail
        for k in range(len(self.tail) + 1):
            states.append(ENFAState("tail", k))
        return states

    def get_initial_states(self):
        return {ENFAState("head", 0)}

    def get_accept_states(self):
        return {ENFAState("tail", len(self.tail))}

    def get_current_states(self):
        return set(self.current_states)

    def get_symbol_set(self):
        return list(self.alphabet)

    def get_state_label(self, state: ENFAState):
        return f"{state.phase}:{state.k}"

    def get_transitions(self):
        trans = {}
        # head transitions
        for k in range(len(self.head)):
            a = self.head[k]
            s = ENFAState("head", k)
            ns = ENFAState("head", k + 1)
            trans.setdefault((s, a), set()).add(ns)
        # epsilon to spacer from end of head
        s = ENFAState("head", len(self.head))
        ns = ENFAState("spacer", 0)
        trans.setdefault((s, None), set()).add(ns)
        # spacer transitions on any base up to max
        for g in range(self.max_gap):
            s = ENFAState("spacer", g)
            for a in self.alphabet:
                trans.setdefault((s, a), set()).add(ENFAState("spacer", g + 1))
            if g >= self.min_gap and len(self.tail) > 0:
                a0 = self.tail[0]
                trans.setdefault((s, a0), set()).add(ENFAState("tail", 1))
        # tail transitions
        for k in range(len(self.tail)):
            a = self.tail[k]
            s = ENFAState("tail", k)
            trans.setdefault((s, a), set()).add(ENFAState("tail", k + 1))
        return trans

    def reset(self) -> None:
        # Start at head progress 0 and also allow epsilon to restart head at any time
        self.current_states = {ENFAState("head", 0)}

    def _epsilon_closure(self, states: Set[ENFAState]) -> Set[ENFAState]:
        # In this simplified model we only add the ability to always (re)start matching
        # from the head via epsilon.
        closure = set(states)
        closure.add(ENFAState("head", 0))
        return closure

    def step(self, symbol: str):
        symbol = symbol.upper()
        prev = self._epsilon_closure(self.current_states)
        next_states: Set[ENFAState] = set()

        for st in prev:
            if st.phase == "head":
                if st.k < len(self.head) and self.head[st.k] == symbol:
                    nk = st.k + 1
                    if nk == len(self.head):
                        # epsilon into spacer with count 0
                        next_states.add(ENFAState("spacer", 0))
                    else:
                        next_states.add(ENFAState("head", nk))
            elif st.phase == "spacer":
                # consume any base while count < max
                if st.k < self.max_gap:
                    next_states.add(ENFAState("spacer", st.k + 1))
                # if we've met min_gap already, try transition to tail on this symbol as first tail char
                if st.k >= self.min_gap:
                    if len(self.tail) > 0 and self.tail[0] == symbol:
                        next_states.add(ENFAState("tail", 1))
            elif st.phase == "tail":
                if st.k < len(self.tail) and self.tail[st.k] == symbol:
                    next_states.add(ENFAState("tail", st.k + 1))

        self.current_states = self._epsilon_closure(next_states)
        accepting = any(st.phase == "tail" and st.k == len(self.tail) for st in self.current_states)

        def fmt(states: Set[ENFAState]) -> str:
            return "{" + ", ".join(f"{s.phase}:{s.k}" for s in sorted(states, key=lambda x:(x.phase,x.k))) + "}"

        desc = f"Read '{symbol}': {fmt(prev)} → {fmt(self.current_states)}"
        if accepting:
            desc += " [MATCH]"
        return self.current_states, accepting, desc

    def get_state_description(self, state) -> str:
        if not state:
            return "No active states"
        # show a concise summary
        best = sorted(state, key=lambda s:(s.phase, s.k))[-1]
        if best.phase == "tail" and best.k == len(self.tail):
            return f"ACCEPT: {self.head} + spacer[{self.min_gap},{self.max_gap}] + {self.tail}"
        if best.phase == "head":
            need = self.head[best.k:best.k+1]
            return f"Head: matched {best.k}/{len(self.head)} need '{need}'"
        if best.phase == "spacer":
            return f"Spacer length so far: {best.k} (min {self.min_gap})"
        need = self.tail[best.k:best.k+1]
        return f"Tail: matched {best.k}/{len(self.tail)} need '{need}'"

    def find_all_matches(self, sequence: str) -> List[Tuple[int, int]]:
        """Return matches for head + spacer[min,max] + tail.
        We compute deterministically for robustness: find all head positions,
        extend spacer in [min,max], and check tail.
        """
        s = sequence.upper()
        matches: List[Tuple[int, int]] = []
        n = len(s)
        Lh = len(self.head)
        Lt = len(self.tail)
        for i in range(0, n - Lh + 1):
            if s[i:i+Lh] != self.head:
                continue
            # spacer length g in [min,max] where tail fully fits
            for g in range(self.min_gap, self.max_gap + 1):
                j = i + Lh + g
                if j + Lt <= n and s[j:j+Lt] == self.tail:
                    matches.append((i, j + Lt - 1))
        return matches
