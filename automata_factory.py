"""
Automata Factory
Creates the appropriate automaton engine based on a selected type.
"""

from typing import Tuple, List

from automata_base import AutomataType
from automata_engine import DFA
from nfa_engine import NFA
from enfa_engine import EpsilonNFA
from pda_engine import PDA


def create_automaton(automata_type: str, pattern: str):
	"""Instantiate an automaton engine.

	Args:
		automata_type: one of AutomataType.* strings
		pattern: pattern string (see type-specific formats)

	Returns:
		Engine instance with reset(), step(), find_all_matches().
	"""
	if automata_type == AutomataType.DFA:
		return DFA(pattern)
	if automata_type == AutomataType.NFA:
		return NFA(pattern)
	if automata_type == AutomataType.ENFA:
		return EpsilonNFA(pattern)
	if automata_type == AutomataType.PDA:
		return PDA(pattern or "PALINDROME")
	raise ValueError(f"Unsupported automata type: {automata_type}")


def available_types() -> List[Tuple[str, str]]:
	"""Return (type, label) for UI dropdown."""
	return [
		(AutomataType.DFA, "DFA – Exact literal matching"),
		(AutomataType.NFA, "NFA – Alternatives (ATG|TAA|TGA)"),
		(AutomataType.ENFA, "ε-NFA – Spacer ranges (TATA{1,10}TATA)"),
		(AutomataType.PDA, "PDA – Complement palindromes (hairpins)"),
	]
