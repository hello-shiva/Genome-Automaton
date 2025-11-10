# 🧬 Automata for Genetic Pattern Analysis

A visually stunning desktop application that combines **Automata Theory** with **Genetic Pattern Recognition**. This educational tool demonstrates how Deterministic Finite Automata (DFA), Non-deterministic FAs (NFA, ε-NFA), and a Pushdown Automaton (PDA) can be used to identify motifs and structures in DNA sequences through real-time visualization and animation.

## 🌟 Features

- **Multiple Automata Types**: DFA, NFA (alternatives), ε-NFA (spacer ranges), and PDA (complement palindromes)
- **Dynamic DFA/NFA Generation**: Automatically builds an automaton from input genetic patterns
- **Real-time Visualization**: Watch the automaton process DNA sequences base by base
- **Color-coded DNA Display**: A, T, G, C bases are distinctly colored for easy identification
- **Interactive State Diagram**: See current state, transitions, and accepting states highlighted
- **Pattern Matching**: Detects all occurrences of genetic motifs (start codons, stop codons, TATA boxes, etc.)
- **Educational Overlays**: Transition logs explain each step in biological context
- **Biotech Aesthetic**: Modern dark theme with neon cyan/green accents
- **Adjustable Speed**: Control simulation speed for presentation or study

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- PyQt5

### Installation

```powershell
# Install required dependencies
pip install -r requirements.txt
```

### Running the Application

```powershell
python main.py
```

## 📖 Usage Guide

1. **Enter DNA Sequence**

   - Type a DNA sequence manually (e.g., `ATGATGCTAGCTAA`)
   - Or click "Generate Random DNA" for a test sequence

2. **Pick Automaton Type + Pattern**

   - Choose one from the Automaton Type dropdown:
     - DFA – exact literal (e.g., `ATG`, `GAATTC`)
     - NFA – alternatives with `|` (e.g., `ATG|TAA|TGA`)
     - ε-NFA – spacer ranges with `{min,max}` (e.g., `TATA{1,10}TATA`)
     - PDA – finds reverse-complement palindromes (pattern field ignored)
   - Common patterns:
     - `ATG` - Start codon (translation initiation)
     - `TAA`, `TAG`, `TGA` - Stop codons
     - `TATA{1,10}TATA` - Promoter-like box with flexible spacing
     - `GAATTC` - EcoRI restriction site

3. **Build Automaton**

   - Click "Build Automaton" to generate the DFA
   - View the state diagram showing all states and transitions

4. **Run Simulation**

   - Click "Run Simulation" to start pattern detection
   - Watch as the automaton processes each base
   - Matched patterns are highlighted in green
   - For NFA/ε-NFA/PDA, all matches are computed and highlighted at the end
   - View detailed transition logs in real-time

5. **Analyze Results**
   - See all match locations listed in the results panel
   - Reset and try different patterns or sequences

## 🏗️ Architecture

### Project Structure

```
automata_genetic_analysis/
│
├── main.py                 # Application entry point
├── automata_base.py        # Common interfaces and types
├── automata_engine.py      # DFA logic and pattern matching
├── nfa_engine.py           # NFA over literal alternatives
├── enfa_engine.py          # ε-NFA: head{m,n}tail
├── pda_engine.py           # PDA: reverse-complement palindromes
├── automata_factory.py     # Factory for building the selected engine
├── dna_visualizer.py       # DNA sequence visualization
├── automata_visualizer.py  # State diagram rendering
├── ui_layout.py            # Main window and UI components
├── assets/
│   └── theme.qss          # Biotech dark theme stylesheet
└── README.md
```

### Module Overview

#### `automata_engine.py`

- **DFA Class**: Implements deterministic finite automaton
- **Pattern Matching Logic**: Uses KMP-inspired failure function for efficient state transitions
- **State Management**: Tracks current state and accepts states
- Automatically constructs transition table from input pattern
- Provides biological context descriptions for each state

#### `nfa_engine.py`

- NFA over alternatives like `ATG|TAA|TGA`
- Tracks a set of active states and advances in parallel
- Works with the shared visualization adapter

#### `enfa_engine.py`

- ε-NFA that matches `HEAD{min,max}TAIL` patterns (e.g., `TATA{1,10}TATA`)
- Nondeterministic spacer length; deterministic matcher for results

#### `pda_engine.py`

- PDA that detects reverse-complement palindromes (hairpin-like)
- Efficient center expansion for matches; light step() logs for visuals

#### `dna_visualizer.py`

- **DNAVisualizer Widget**: Custom PyQt widget for DNA rendering
- **Color Coding**: Maps bases to distinct colors (A=Red, T=Blue, G=Green, C=Yellow)
- **Scrolling Animation**: Auto-scrolls to keep current base visible
- **Match Highlighting**: Green glow effect for detected patterns
- **Real-time Updates**: Smooth animations as bases are processed

#### `automata_visualizer.py`

- **AutomataVisualizer Widget**: Renders DFA state diagram
- **Circular Layout**: Arranges states in visually pleasing circle/ellipse
- **Transition Arrows**: Shows all possible state transitions with labels
- **State Highlighting**: Current state glows cyan, accept states glow green
- **Self-loops**: Handles transitions from a state to itself
- **Active Transition**: Highlights the transition being taken

#### `ui_layout.py`

- **MainWindow Class**: Orchestrates all components
- **Three-Panel Layout**: Left (input), Center (visualization), Right (info)
- **Automaton Type Selector**: Build DFA/NFA/ε-NFA/PDA via factory
- **Control Flow**: Manages simulation timer and state updates
- **User Interactions**: Button handlers for run, pause, reset, build
- **Status Updates**: Real-time feedback on simulation progress

#### `assets/theme.qss`

- **Biotech Aesthetic**: Dark background (#1A1F2E) with neon accents
- **Color Scheme**: Cyan (#00D9FF), Green (#00FFAA) highlights
- **Gradients**: Subtle gradients for depth and polish
- **Hover Effects**: Interactive feedback on buttons and controls

## 🧠 How It Works

### Automaton Construction (DFA)

1. Given pattern `P` (e.g., "ATG"), create `|P| + 1` states (Q0...Q3)
2. State `Qi` represents "matched first `i` characters of pattern"
3. For each state and each input symbol (A/T/G/C), compute next state:
   - If symbol matches next pattern character, advance to next state
   - Otherwise, find longest prefix match and transition accordingly
   - Use failure function similar to KMP algorithm for efficiency

### Pattern Detection

1. Start in state Q0
2. Read DNA sequence one base at a time
3. Transition between states based on current state and input base
4. When reaching accept state Q|P|, pattern is detected
5. Continue processing to find all occurrences

### Biological Relevance

- **Start Codon (ATG)**: Marks beginning of protein coding sequence
- **Stop Codons (TAA/TAG/TGA)**: Signals end of translation
- **TATA Box**: Promoter region for transcription initiation
- **Restriction Sites**: Recognition sequences for enzymes

This approach mirrors how molecular machinery "reads" DNA sequences to find functional elements!

## 🎨 Design Philosophy

- **Educational First**: Code clarity over algorithmic complexity
- **Visual Appeal**: Smooth animations and modern aesthetics
- **Modular Structure**: Each component has single responsibility
- **Well-Commented**: Inline documentation explains biology + CS concepts
- **Minimal Dependencies**: Only PyQt5 required
- **Academic Ready**: Perfect for presentations and demonstrations

## 🔬 Technical Details

- **Language**: Python 3
- **GUI Framework**: PyQt5
- **Graphics**: QPainter for custom rendering
- **Animation**: QTimer for smooth frame updates
- **Pattern Matching**: O(n) DFA; NFAs simulate multiple alternatives; ε-NFA uses bounded spacer checks; PDA uses center expansion
- **Space Complexity**: O(|pattern| × |alphabet|) for transition table

## 🎓 Educational Use Cases

- **Theory of Computation**: Demonstrate DFA concepts visually
- **Bioinformatics**: Show real-world applications of automata
- **Algorithm Design**: Illustrate pattern matching techniques
- **Molecular Biology**: Explain genetic motif recognition
- **Software Engineering**: Showcase modular architecture

## 📝 Example Patterns to Try

| Pattern  | Biological Significance | Expected Behavior           |
| -------- | ----------------------- | --------------------------- |
| `ATG`    | Start codon             | Marks protein start         |
| `TAA`    | Stop codon              | Terminates translation      |
| `TATA`   | TATA box                | Promoter region             |
| `GAATTC` | EcoRI site              | Restriction enzyme cut site |
| `CG`     | CpG island              | Regulatory region marker    |

## � Future Enhancements

- Export state diagrams as images
- Save/load DNA sequences and patterns
- Additional pattern types (regex support)
- Performance metrics (time, memory usage)
- Multiple sequence alignment support
- Export match results to CSV/JSON

## �📄 License

Free for educational and academic use.

## 👨‍💻 Author

**AamishB**
**Shivam Kumar**  
Repository: [Genome-Automaton](https://github.com/AamishB/Genome-Automaton)
