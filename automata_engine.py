"""
Automata Engine Module
Implements DFA creation and pattern matching logic for DNA sequences.
Builds a clean linear chain DFA matching the reference diagram style.
"""

from automata_base import AutomataType

class DFA:
    """
    Deterministic Finite Automaton for exact literal pattern matching.
    Creates a simple linear chain: Q0 -> Q1 -> ... -> Qn -> Q0
    """
    
    def __init__(self, pattern):
        """
        Initialize DFA for a given pattern.
        
        Args:
            pattern (str): The genetic pattern to detect (e.g., "ATG")
        """
        self.pattern = pattern.upper()
        self.alphabet = ['A', 'T', 'G', 'C']
        self.transitions = {}
        self.current_state = 0
        
        # Build simple linear chain
        self._build_linear_chain()

    # ----- Visualization adapter (finite automata) -----
    def get_type(self):
        return AutomataType.DFA

    def get_states(self):
        # Q0 through Q(n-1) where n = pattern length
        return list(range(len(self.pattern)))

    def get_initial_states(self):
        return {0}

    def get_accept_states(self):
        # Q0 is the accept state (matches NFA style)
        return {0}

    def get_current_states(self):
        return {self.current_state}

    def get_transitions(self):
        # Convert to nondet format: (state, symbol) -> set(next_states)
        nd = {}
        for (s, sym), ns in self.transitions.items():
            nd.setdefault((s, sym), set()).add(ns)
        return nd

    def get_symbol_set(self):
        return list(self.alphabet)

    def get_state_label(self, state):
        return f"Q{int(state)}"
    
    def get_important_restart_edges(self):
        """Mark the final return edge as important for visualization."""
        if len(self.pattern) > 0:
            last_state = len(self.pattern) - 1
            last_symbol = self.pattern[-1]
            return {(last_state, last_symbol)}
        return set()
    
    def _build_linear_chain(self):
        """
        Build a simple linear chain DFA:
        Q0 --pattern[0]--> Q1 --pattern[1]--> Q2 ... Q(n-1) --pattern[n-1]--> Q0
        
        All non-matching edges loop back to Q0.
        """
        n = len(self.pattern)
        
        if n == 0:
            # Empty pattern: all edges self-loop at Q0
            for sym in self.alphabet:
                self.transitions[(0, sym)] = 0
            return
        
        # Build the main chain
        for i in range(n):
            current_char = self.pattern[i]
            
            for sym in self.alphabet:
                if sym == current_char:
                    if i == n - 1:
                        # Last character: loop back to Q0 (accept and restart)
                        self.transitions[(i, sym)] = 0
                    else:
                        # Advance to next state
                        self.transitions[(i, sym)] = i + 1
                else:
                    # Non-matching symbol: check if it matches start of pattern
                    if sym == self.pattern[0] and i != 0:
                        # Start new potential match from Q1
                        self.transitions[(i, sym)] = 1
                    else:
                        # Return to Q0
                        self.transitions[(i, sym)] = 0
    
    def reset(self):
        """Reset automaton to initial state."""
        self.current_state = 0
    
    def step(self, symbol):
        """
        Process one input symbol and transition to next state.
        
        Args:
            symbol (str): DNA base to process
            
        Returns:
            tuple: (new_state, is_accepting, transition_description)
        """
        symbol = symbol.upper()
        old_state = self.current_state
        
        if symbol in self.alphabet:
            next_state = self.transitions.get((self.current_state, symbol), 0)
            # Detect match: we're about to return to Q0 from the last state
            is_match = (self.current_state == len(self.pattern) - 1 and 
                       next_state == 0 and 
                       symbol == self.pattern[-1])
            self.current_state = next_state
        else:
            is_match = False
        
        # Generate human-readable transition description
        description = f"Read '{symbol}': Q{old_state} → Q{self.current_state}"
        if is_match:
            description += " [PATTERN MATCHED!]"
        elif self.current_state > old_state:
            description += f" (Matched {self.current_state}/{len(self.pattern)})"
        elif self.current_state < old_state or (self.current_state == 0 and old_state != 0):
            description += " (Reset/backtrack to start)"
        
        return (self.current_state, is_match, description)
    
    def get_state_description(self, state):
        """
        Get biological description of a state.
        
        Args:
            state (int): State number
            
        Returns:
            str: Description of what this state represents
        """
        if state == 0:
            return "Start State: Looking for pattern start (also accept)"
        else:
            matched = self.pattern[:state]
            remaining = self.pattern[state:]
            return f"Partial Match: '{matched}' (need '{remaining}')"
    
    def find_all_matches(self, dna_sequence):
        """
        Find all occurrences of pattern in DNA sequence.
        
        Args:
            dna_sequence (str): DNA sequence to search
            
        Returns:
            list: List of (start_index, end_index) tuples for matches
        """
        matches = []
        self.reset()
        
        for i, base in enumerate(dna_sequence):
            _, is_match, _ = self.step(base)
            if is_match:
                # Pattern ends at position i
                start = i - len(self.pattern) + 1
                end = i
                matches.append((start, end))
        
        self.reset()
        return matches


def generate_random_dna(length=100):
    """
    Generate a random DNA sequence.
    
    Args:
        length (int): Length of sequence to generate
        
    Returns:
        str: Random DNA sequence
    """
    import random
    bases = ['A', 'T', 'G', 'C']
    return ''.join(random.choice(bases) for _ in range(length))
