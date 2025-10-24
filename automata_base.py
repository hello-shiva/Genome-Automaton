"""
Common Automata Interfaces and Types
Defines a lightweight base class and an enum-like type string for different
automata so the UI can work with any engine in a uniform way.
"""

from typing import Any, Iterable, List, Optional, Sequence, Tuple, Union


class AutomataType:
    DFA = "DFA"
    NFA = "NFA"
    ENFA = "Epsilon-NFA"
    PDA = "PDA"


class BaseAutomaton:
    """Lightweight base defining the surface API expected by the UI.

    Subclasses should implement:
    - reset()
    - step(symbol) -> (state_or_states, is_accepting, description)
    - find_all_matches(sequence) -> List[(start, end)]
    - get_state_description(state_or_states) -> str
    """

    alphabet: Sequence[str] = ("A", "T", "G", "C")

    def __init__(self, pattern: str, automata_type: str):
        self.pattern = (pattern or "").upper()
        self.automata_type = automata_type

    # --- Virtuals ---
    def reset(self) -> None:  # pragma: no cover - interface only
        raise NotImplementedError

    def step(self, symbol: str) -> Tuple[Any, bool, str]:  # pragma: no cover
        raise NotImplementedError

    def find_all_matches(self, sequence: str) -> List[Tuple[int, int]]:  # pragma: no cover
        raise NotImplementedError

    def get_state_description(self, state: Any) -> str:  # pragma: no cover
        raise NotImplementedError
