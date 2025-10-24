"""
Reference NFA Engine (diagram-first)

This implementation builds a compact, readable automaton that mirrors the
reference diagram style provided by the user:
 - Single start/accept state Q0 (double circle)
 - For each alternative literal (e.g., "ATG"), we create a chain of states
   from Q0 following the characters, and the final character transition
   returns to Q0. That keeps the graph minimal and visually intuitive.
 - During simulation, we allow starting a new attempt on every step while
   continuing any in-flight paths. A match is signaled when a "final return"
   transition to Q0 fires.

Example for alternatives ["ATG", "TAA"]:
  Q0 -A-> Q1 -T-> Q2 -G-> Q0
  Q0 -T-> Q3 -A-> Q4 -A-> Q0

This recognizes the set of motifs cleanly while the diagram stays close to the
reference layout.
"""

from typing import Dict, List, Set, Tuple

from automata_base import BaseAutomaton, AutomataType


class NFA(BaseAutomaton):
    """NFA over literal alternatives with start/accept Q0 and final returns."""

    def __init__(self, pattern: str):
        super().__init__(pattern, AutomataType.NFA)
        # Parse alternatives
        self.alternatives: List[str] = [p for p in (pattern or "").upper().split("|") if p]
        if not self.alternatives:
            self.alternatives = [""]

        # Graph representation
        # states are ints; 0 is start/accept
        self._next_state_id = 1
        self.transitions: Dict[Tuple[int, str], Set[int]] = {}
        # Edges that represent a full match (return-to-start)
        self._final_return_edges: Set[Tuple[int, str]] = set()

        # Build trie-like graph with final return edges
        self._build_graph()

        # Simulation state: a set of active nodes
        self.current_states: Set[int] = set()
        self.reset()

    # ----- Construction helpers -----
    def _new_state(self) -> int:
        s = self._next_state_id
        self._next_state_id += 1
        return s

    def _add_edge(self, u: int, sym: str, v: int):
        self.transitions.setdefault((u, sym), set()).add(v)

    def _build_graph(self) -> None:
        # Map from (prefix_string) -> state id (state after consuming prefix)
        prefix_to_state: Dict[str, int] = {"": 0}

        for alt in self.alternatives:
            if not alt:
                continue
            u = 0
            for i, ch in enumerate(alt):
                is_last = (i == len(alt) - 1)
                if is_last:
                    # Final transition goes back to start on the last character
                    self._add_edge(u, ch, 0)
                    self._final_return_edges.add((u, ch))
                else:
                    prefix = alt[: i + 1]
                    if prefix not in prefix_to_state:
                        prefix_to_state[prefix] = self._new_state()
                    v = prefix_to_state[prefix]
                    self._add_edge(u, ch, v)
                    u = v

    # ----- Visualization adapter -----
    def get_type(self):
        return AutomataType.NFA

    def get_states(self) -> List[int]:
        return list(range(self._next_state_id))

    def get_initial_states(self):
        return {0}

    def get_accept_states(self):
        # Draw Q0 as the only accept (double circle) per reference
        return {0}

    def get_current_states(self):
        return set(self.current_states)

    def get_symbol_set(self):
        return list(self.alphabet)

    def get_state_label(self, state):
        return f"Q{state}"

    def get_transitions(self):
        # Already in nondet form: (state, symbol) -> set(next_states)
        return {k: set(v) for k, v in self.transitions.items()}

    # Edges to initial that represent full matches; used by visualizer to keep
    # these even when generic restart edges are hidden for clarity.
    def get_important_restart_edges(self) -> Set[Tuple[int, str]]:
        return set(self._final_return_edges)

    # ------------- Engine API -------------
    def reset(self) -> None:
        self.current_states = {0}

    def step(self, symbol: str):
        symbol = symbol.upper()
        prev = set(self.current_states)

        # Start new attempts from Q0 and advance from all current states
        candidates = set(prev)
        candidates.add(0)

        next_states: Set[int] = set()
        matched_now = False

        for u in candidates:
            for v in self.transitions.get((u, symbol), set()):
                next_states.add(v)
                # Detect final return (full motif completed on this symbol)
                if (u, symbol) in self._final_return_edges or (v == 0 and u != 0):
                    matched_now = True

        # Always keep Q0 available to continue scanning even if no edges fired
        if not next_states:
            next_states = {0}

        self.current_states = next_states

        # Description string
        def fmt(states: Set[int]) -> str:
            return "{" + ", ".join(f"Q{s}" for s in sorted(states)) + "}"

        desc = f"Read '{symbol}': {fmt(prev)} → {fmt(self.current_states)}"
        if matched_now:
            desc += " [MATCH]"
        return self.current_states, matched_now, desc

    def get_state_description(self, state) -> str:
        if not state:
            return "No active states"
        if 0 in state:
            return "Ready (Q0 is accept; looking for start)"
        # Report one of the non-zero states as partial progress
        s = min(state)
        return f"Partial path at Q{s}"

    def find_all_matches(self, sequence: str) -> List[Tuple[int, int]]:
        s = sequence.upper()
        matches: List[Tuple[int, int]] = []
        # Precompute alternative lengths for back-calculating start index
        alt_lens = set(len(a) for a in self.alternatives if a)
        self.reset()
        for i, ch in enumerate(s):
            _, matched, _ = self.step(ch)
            if matched:
                # choose the longest feasible alternative that can end here
                L = 0
                for Lcand in alt_lens:
                    if Lcand > L and i - Lcand + 1 >= 0:
                        # check actual substring membership for robustness
                        if s[i-Lcand+1:i+1] in self.alternatives:
                            L = Lcand
                if L:
                    matches.append((i - L + 1, i))
        self.reset()
        return matches
