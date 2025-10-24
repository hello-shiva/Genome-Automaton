"""
UI Layout Module
Defines the main window structure and integrates all components.
Rewired to support multiple automata types (DFA, NFA, ε-NFA, PDA)
via a factory and unified engine API.
"""

from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QLineEdit, QTextEdit, 
                             QSplitter, QFrame, QMessageBox, QComboBox, QButtonGroup)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont

from automata_base import AutomataType
from automata_factory import create_automaton, available_types
from automata_engine import DFA, generate_random_dna
from dna_visualizer import DNAVisualizer
from automata_visualizer import AutomataVisualizer
from pda_visualizer import PDAVisualizer


class MainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self):
        super().__init__()
        # Current engine & type
        self.engine = None
        self.engine_type = None
        self.selected_type = AutomataType.DFA
        self.simulation_timer = None
        self.simulation_index = 0
        self.simulation_speed = 300  # ms per step
        
        self._init_ui()
        self._apply_styles()
    
    def _init_ui(self):
        """Initialize user interface components."""
        self.setWindowTitle("Automata for Genetic Pattern Analysis")
        self.setGeometry(100, 100, 1400, 800)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Top bar
        self._create_top_bar(main_layout)
        
        # Main content area (splitter for resizable panels)
        splitter = QSplitter(Qt.Horizontal)
        
        # Left panel
        left_panel = self._create_left_panel()
        splitter.addWidget(left_panel)
        
        # Center panel (visualizations)
        center_panel = self._create_center_panel()
        splitter.addWidget(center_panel)
        
        # Right panel
        right_panel = self._create_right_panel()
        splitter.addWidget(right_panel)
        
        # Set initial sizes (30% - 45% - 25%)
        splitter.setSizes([350, 700, 350])
        
        main_layout.addWidget(splitter)
        
        # Footer status bar
        self._create_footer(main_layout)
    
    def _create_top_bar(self, parent_layout):
        """Create top bar with title and main controls."""
        top_bar = QFrame()
        top_bar.setObjectName("topBar")
        top_bar.setFixedHeight(60)
        
        layout = QHBoxLayout(top_bar)
        layout.setContentsMargins(15, 5, 15, 5)
        
        # Title
        title = QLabel("🧬 Automata for Genetic Pattern Analysis")
        title.setObjectName("appTitle")
        title.setFont(QFont('Segoe UI', 16, QFont.Bold))
        layout.addWidget(title)
        
        layout.addStretch()
        
        # Control buttons
        self.btn_run = QPushButton("▶ Run Simulation")
        self.btn_run.setObjectName("btnRun")
        self.btn_run.setFixedSize(170, 45)
        self.btn_run.clicked.connect(self._run_simulation)
        layout.addWidget(self.btn_run)
        
        self.btn_pause = QPushButton("⏸ Pause")
        self.btn_pause.setObjectName("btnPause")
        self.btn_pause.setFixedSize(130, 45)
        self.btn_pause.setEnabled(False)
        self.btn_pause.clicked.connect(self._pause_simulation)
        layout.addWidget(self.btn_pause)
        
        self.btn_reset = QPushButton("⟲ Reset")
        self.btn_reset.setObjectName("btnReset")
        self.btn_reset.setFixedSize(130, 45)
        self.btn_reset.clicked.connect(self._reset_simulation)
        layout.addWidget(self.btn_reset)
        
        parent_layout.addWidget(top_bar)
    
    def _create_left_panel(self):
        """Create left input panel."""
        panel = QFrame()
        panel.setObjectName("leftPanel")
        panel.setMinimumWidth(300)
        panel.setMaximumWidth(500)
        
        layout = QVBoxLayout(panel)
        layout.setSpacing(15)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # (Automaton Type section moved below Pattern section)

        # DNA Input Section
        dna_label = QLabel("DNA Sequence:")
        dna_label.setFont(QFont('Segoe UI', 11, QFont.Bold))
        layout.addWidget(dna_label)
        
        self.dna_input = QTextEdit()
        self.dna_input.setObjectName("dnaInput")
        self.dna_input.setMaximumHeight(120)
        self.dna_input.setPlaceholderText("Enter DNA sequence (A, T, G, C)...")
        self.dna_input.setFont(QFont('Consolas', 10))
        layout.addWidget(self.dna_input)
        
        btn_generate = QPushButton("🎲 Generate Random DNA")
        btn_generate.setObjectName("btnGenerate")
        btn_generate.setFixedHeight(45)
        btn_generate.clicked.connect(self._generate_random_dna)
        layout.addWidget(btn_generate)
        
        # Pattern Input Section
        pattern_label = QLabel("Pattern:")
        pattern_label.setFont(QFont('Segoe UI', 11, QFont.Bold))
        layout.addWidget(pattern_label)
        
        self.pattern_input = QLineEdit()
        self.pattern_input.setObjectName("patternInput")
        self.pattern_input.setPlaceholderText("DFA: ATG | NFA: ATG|TAA | ε-NFA: TATA{1,10}TATA | PDA: (ignored)")
        self.pattern_input.setFont(QFont('Consolas', 12))
        layout.addWidget(self.pattern_input)
        # (Helper/placeholder will be initialized after automaton type widgets are created)
        
        # Example patterns
        examples_label = QLabel("Common patterns:\n• DFA: ATG (start)\n• NFA: ATG|TAA|TGA (alts)\n• ε-NFA: TATA{1,10}TATA (spacer)\n• PDA: finds complement palindromes")
        examples_label.setObjectName("examplesLabel")
        examples_label.setFont(QFont('Segoe UI', 9))
        layout.addWidget(examples_label)

        # Automaton Type section (styled like Simulation Speed buttons) — placed after Pattern
        type_label = QLabel("Automaton Type:")
        type_label.setFont(QFont('Segoe UI', 11, QFont.Bold))
        layout.addWidget(type_label)

        type_layout = QHBoxLayout()
        self.type_group = QButtonGroup(self)
        self.type_group.setExclusive(True)

        def add_type_btn(text, atype, tooltip=None):
            btn = QPushButton(text)
            btn.setCheckable(True)
            btn.setFixedHeight(40)
            # Reuse speed button styling for visual consistency
            btn.setObjectName("speedBtn")
            if tooltip:
                btn.setToolTip(tooltip)
            btn.setProperty('atype', atype)
            self.type_group.addButton(btn)
            type_layout.addWidget(btn)
            return btn

        btn_dfa = add_type_btn("DFA", AutomataType.DFA, "Exact literal matching")
        btn_nfa = add_type_btn("NFA", AutomataType.NFA, "Alternatives with | e.g., ATG|TAA|TGA")
        btn_enfa = add_type_btn("ε-NFA", AutomataType.ENFA, "Spacer ranges HEAD{m,n}TAIL")
        btn_pda = add_type_btn("PDA", AutomataType.PDA, "Complement palindromes (hairpins)")

        layout.addLayout(type_layout)
        btn_dfa.setChecked(True)
        self.type_group.buttonClicked.connect(self._on_type_button)

        # Helper description under the type buttons
        self.type_help = QLabel()
        self.type_help.setObjectName("typeHelp")
        self.type_help.setWordWrap(True)
        self.type_help.setFont(QFont('Segoe UI', 9))
        layout.addWidget(self.type_help)

        # Initialize helper/placeholder for default selection
        self._set_selected_type(self.selected_type)

        # Divider after Automaton Type
        sep = QFrame()
        sep.setObjectName("sectionDivider")
        sep.setFrameShape(QFrame.HLine)
        sep.setFrameShadow(QFrame.Sunken)
        layout.addWidget(sep)
        layout.addSpacing(5)
        
        layout.addSpacing(20)
        
        # Build Automaton Button
        btn_build = QPushButton("🔨 Build Automaton")
        btn_build.setObjectName("btnBuild")
        btn_build.setFixedHeight(50)
        btn_build.clicked.connect(self._build_automaton)
        layout.addWidget(btn_build)
        
        # Speed Control
        speed_label = QLabel("Simulation Speed:")
        speed_label.setFont(QFont('Segoe UI', 10, QFont.Bold))
        layout.addWidget(speed_label)
        
        speed_layout = QHBoxLayout()
        btn_slow = QPushButton("Slow")
        btn_slow.setFixedHeight(40)
        btn_slow.clicked.connect(lambda: self._set_speed(500))
        btn_medium = QPushButton("Medium")
        btn_medium.setFixedHeight(40)
        btn_medium.clicked.connect(lambda: self._set_speed(300))
        btn_fast = QPushButton("Fast")
        btn_fast.setFixedHeight(40)
        btn_fast.clicked.connect(lambda: self._set_speed(100))
        
        for btn in [btn_slow, btn_medium, btn_fast]:
            btn.setObjectName("speedBtn")
            speed_layout.addWidget(btn)
        
        layout.addLayout(speed_layout)
        
        layout.addStretch()
        
        return panel
    
    def _create_center_panel(self):
        """Create center visualization panel."""
        panel = QFrame()
        panel.setObjectName("centerPanel")
        
        layout = QVBoxLayout(panel)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Automaton visualization
        automata_label = QLabel("Automaton State Diagram:")
        automata_label.setFont(QFont('Segoe UI', 11, QFont.Bold))
        layout.addWidget(automata_label)
        
        self.automata_viz = AutomataVisualizer()
        self.automata_viz.setObjectName("automataViz")
        layout.addWidget(self.automata_viz, 3)

        # PDA live visualization (stack/control)
        self.pda_viz = PDAVisualizer()
        self.pda_viz.setObjectName("pdaViz")
        self.pda_viz.setVisible(False)
        layout.addWidget(self.pda_viz, 1)
        
        # Create DNA visualizer first
        self.dna_viz = DNAVisualizer()
        self.dna_viz.setObjectName("dnaViz")
        
        # DNA visualization with controls
        dna_label_layout = QHBoxLayout()
        dna_label = QLabel("DNA Double Helix Visualization:")
        dna_label.setFont(QFont('Segoe UI', 11, QFont.Bold))
        dna_label_layout.addWidget(dna_label)
        dna_label_layout.addStretch()
        
        # DNA visualization controls
        self.btn_helix = QPushButton("🌀 3D Helix")
        self.btn_helix.setCheckable(True)
        self.btn_helix.setChecked(True)
        self.btn_helix.setFixedSize(130, 40)
        self.btn_helix.clicked.connect(self.dna_viz.toggle_helix)
        dna_label_layout.addWidget(self.btn_helix)
        
        self.btn_glow = QPushButton("✨ Glow")
        self.btn_glow.setCheckable(True)
        self.btn_glow.setChecked(True)
        self.btn_glow.setFixedSize(110, 40)
        self.btn_glow.clicked.connect(self.dna_viz.toggle_glow)
        dna_label_layout.addWidget(self.btn_glow)
        
        layout.addLayout(dna_label_layout)
        layout.addWidget(self.dna_viz, 2)
        
        return panel
    
    def _create_right_panel(self):
        """Create right information panel."""
        panel = QFrame()
        panel.setObjectName("rightPanel")
        panel.setMinimumWidth(280)
        panel.setMaximumWidth(450)
        
        layout = QVBoxLayout(panel)
        layout.setSpacing(15)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Current State Section
        state_label = QLabel("Current State:")
        state_label.setFont(QFont('Segoe UI', 11, QFont.Bold))
        layout.addWidget(state_label)
        
        self.current_state_label = QLabel("Ready")
        self.current_state_label.setObjectName("currentStateLabel")
        self.current_state_label.setFont(QFont('Segoe UI', 12))
        self.current_state_label.setWordWrap(True)
        layout.addWidget(self.current_state_label)
        
        # Transition Log
        log_label = QLabel("Transition Log:")
        log_label.setFont(QFont('Segoe UI', 11, QFont.Bold))
        layout.addWidget(log_label)
        
        self.transition_log = QTextEdit()
        self.transition_log.setObjectName("transitionLog")
        self.transition_log.setReadOnly(True)
        self.transition_log.setFont(QFont('Consolas', 9))
        layout.addWidget(self.transition_log, 2)
        
        # Results Section
        results_label = QLabel("Results:")
        results_label.setFont(QFont('Segoe UI', 11, QFont.Bold))
        layout.addWidget(results_label)
        
        self.results_display = QTextEdit()
        self.results_display.setObjectName("resultsDisplay")
        self.results_display.setReadOnly(True)
        self.results_display.setFont(QFont('Segoe UI', 10))
        self.results_display.setMaximumHeight(150)
        layout.addWidget(self.results_display)
        
        layout.addStretch()
        
        return panel
    
    def _create_footer(self, parent_layout):
        """Create footer status bar."""
        footer = QFrame()
        footer.setObjectName("footer")
        footer.setFixedHeight(35)
        
        layout = QHBoxLayout(footer)
        layout.setContentsMargins(15, 5, 15, 5)
        
        self.status_label = QLabel("Ready. Enter DNA sequence and pattern to begin.")
        self.status_label.setFont(QFont('Segoe UI', 9))
        layout.addWidget(self.status_label)
        
        layout.addStretch()
        
        info_label = QLabel("© 2025 | Genetic Pattern Analysis with Automata")
        info_label.setFont(QFont('Segoe UI', 8))
        layout.addWidget(info_label)
        
        parent_layout.addWidget(footer)
    
    def _apply_styles(self):
        """Apply inline styles if theme.qss is not loaded."""
        # This provides fallback styling
        pass
    
    def _set_selected_type(self, t):
        """Centralize UI updates when automaton type changes."""
        self.selected_type = t
        if t == AutomataType.DFA:
            self.pattern_input.setPlaceholderText("e.g., ATG, GAATTC")
            self.type_help.setText("DFA: exact literal matching. Example: ATG, GAATTC.")
        elif t == AutomataType.NFA:
            self.pattern_input.setPlaceholderText("e.g., ATG|TAA|TGA (alternatives)")
            self.type_help.setText("NFA: alternatives separated by |. Example: ATG|TAA|TGA.")
        elif t == AutomataType.ENFA:
            self.pattern_input.setPlaceholderText("e.g., TATA{1,10}TATA (spacer range)")
            self.type_help.setText("ε‑NFA: pattern HEAD{min,max}TAIL with a flexible spacer. Example: TATA{1,10}TATA.")
        else:
            self.pattern_input.setPlaceholderText("PDA ignores pattern; finds complement palindromes")
            self.type_help.setText("PDA: pattern field ignored. Finds reverse‑complement palindromes (hairpins).")

    def _on_type_button(self, btn):
        atype = btn.property('atype')
        self._set_selected_type(atype)
        self.pattern_input.clear()

    def _generate_random_dna(self):
        """Generate and insert random DNA sequence."""
        dna = generate_random_dna(80)
        self.dna_input.setPlainText(dna)
        self.status_label.setText("Random DNA sequence generated.")
    
    def _build_automaton(self):
        """Build automaton from selected type and pattern input."""
        pattern = self.pattern_input.text().strip().upper()
        atype = self.selected_type

        # For DFA/NFA/ENFA, validate characters only when a pattern is required
        if atype in (AutomataType.DFA, AutomataType.NFA, AutomataType.ENFA):
            if not pattern:
                QMessageBox.warning(self, "Input Error", "Please enter a pattern to detect.")
                return
            # ENFA allows braces and comma; validate broadly except those
            valid_bases = set('ATGC')
            if atype == AutomataType.ENFA:
                # Strip the {m,n} part for a soft check of bases around
                base_only = ''.join([c for c in pattern if c in 'ATGC{}.,0123456789'])
                if not base_only:
                    QMessageBox.warning(self, "Input Error", "Invalid ε-NFA pattern.")
                    return
            elif atype in (AutomataType.DFA, AutomataType.NFA):
                alt_str = pattern.replace('|', '')
                if not all(c in valid_bases for c in alt_str):
                    QMessageBox.warning(self, "Input Error",
                                        "Pattern must contain only A, T, G, C (and '|' for NFA).")
                    return

        # Build engine via factory
        try:
            self.engine = create_automaton(atype, pattern)
            self.engine_type = atype
        except Exception as e:
            QMessageBox.critical(self, "Build Failed", f"Could not build automaton: {e}")
            return

        # Update visualizers
        if atype == AutomataType.PDA:
            self.pda_viz.setVisible(True)
            self.pda_viz.set_automaton(self.engine)
            self.automata_viz.setVisible(False)
        else:
            self.pda_viz.setVisible(False)
            self.automata_viz.setVisible(True)
            self.automata_viz.set_automaton(self.engine)

        # Reset displays
        self.dna_viz.reset()
        self.transition_log.clear()
        self.results_display.clear()

        # Update status
        label = next((lbl for (t, lbl) in available_types() if t == self.selected_type), self.selected_type)
        self.status_label.setText(f"Built: {label}")
        try:
            # Use engine's description API
            desc = self.engine.get_state_description(getattr(self.engine, 'current_state', 0))
        except Exception:
            desc = "Ready"
        self.current_state_label.setText(desc)

        QMessageBox.information(self, "Success",
                                f"Automaton generated successfully!\nType: {label}\nPattern: {pattern or '(n/a)'}")
    
    def _run_simulation(self):
        """Start simulation animation."""
        if not self.engine:
            QMessageBox.warning(self, "No Automaton",
                              "Please build an automaton first.")
            return
        
        dna_sequence = self.dna_input.toPlainText().strip().upper().replace(" ", "").replace("\n", "")
        
        if not dna_sequence:
            QMessageBox.warning(self, "Input Error",
                              "Please enter a DNA sequence.")
            return
        
        # Validate DNA sequence
        valid_bases = set('ATGC')
        if not all(c in valid_bases for c in dna_sequence):
            QMessageBox.warning(self, "Input Error",
                              "DNA sequence must contain only A, T, G, C bases.")
            return
        
        # Setup simulation
        try:
            self.engine.reset()
        except Exception:
            pass
        self.simulation_index = 0
        self.dna_viz.set_dna_sequence(dna_sequence)
        self.dna_viz.clear_matches()
        if self.engine_type != AutomataType.PDA:
            self.automata_viz.reset()
        self.transition_log.clear()
        self.results_display.clear()
        
        # Update UI
        self.btn_run.setEnabled(False)
        self.btn_pause.setEnabled(True)
        self.status_label.setText("Simulation running...")
        
        # Start animation timer
        self.simulation_timer = QTimer()
        self.simulation_timer.timeout.connect(self._simulation_step)
        self.simulation_timer.start(self.simulation_speed)
    
    def _simulation_step(self):
        """Execute one step of simulation."""
        dna_sequence = self.dna_input.toPlainText().strip().upper().replace(" ", "").replace("\n", "")
        
        if self.simulation_index >= len(dna_sequence):
            self._finish_simulation()
            return
        
        # Get current base
        current_base = dna_sequence[self.simulation_index]
        
        # Update DNA visualization
        self.dna_viz.set_current_index(self.simulation_index)
        
        # Process through engine
        old_state = getattr(self.engine, 'current_state', None)
        try:
            new_state, is_accepting, description = self.engine.step(current_base)
        except Exception as e:
            description = f"Step error on '{current_base}': {e}"
            is_accepting = False
            new_state = None

        # Update automaton visualization/state labels
        if self.engine_type == AutomataType.PDA:
            # Update PDA visual
            stack = getattr(self.engine, 'stack', [])
            mode = getattr(self.engine, 'mode', 'push')
            self.pda_viz.update_stack(stack, mode)
            try:
                desc_state = self.engine.get_state_description(None)
            except Exception:
                desc_state = f"Stack size {len(stack)}"
            self.current_state_label.setText(desc_state)
        else:
            # For FA-like engines, update diagram
            try:
                current_states = set(self.engine.get_current_states())
            except Exception:
                current_states = {getattr(self.engine, 'current_state', 0)}
            self.automata_viz.set_current_states(current_states)
            # Only set last transition for DFA where old/new are ints
            if self.engine_type == AutomataType.DFA and isinstance(old_state, int) and isinstance(new_state, int):
                self.automata_viz.set_last_transition(old_state, new_state, current_base)
            else:
                self.automata_viz.clear_transition()
            # State description text
            try:
                desc_state = self.engine.get_state_description(current_states if self.engine_type != AutomataType.DFA else new_state)
            except Exception:
                desc_state = str(new_state)
            self.current_state_label.setText(desc_state)
        
        # Add to transition log
        self.transition_log.append(description)
        self.transition_log.verticalScrollBar().setValue(
            self.transition_log.verticalScrollBar().maximum())
        
        # If match found, highlight only for DFA (NFA/ENFA/PDA finalized later)
        if is_accepting and self.engine_type == AutomataType.DFA:
            try:
                pat_len = len(getattr(self.engine, 'pattern', ''))
                start = self.simulation_index - pat_len + 1
                end = self.simulation_index
                self.dna_viz.add_match(start, end)
                result_text = f"✓ Match found at positions {start}-{end}\n"
                self.results_display.append(result_text)
            except Exception:
                pass
        
        self.simulation_index += 1
    
    def _finish_simulation(self):
        """Finish simulation and display results."""
        if self.simulation_timer:
            self.simulation_timer.stop()
        
        self.btn_run.setEnabled(True)
        self.btn_pause.setEnabled(False)
        self.status_label.setText("Simulation complete.")
        
        # Find all matches
        dna_sequence = self.dna_input.toPlainText().strip().upper().replace(" ", "").replace("\n", "")
        try:
            matches = self.engine.find_all_matches(dna_sequence)
        except Exception:
            matches = []
        
        if matches:
            summary = f"\n{'='*30}\nTotal matches found: {len(matches)}\n"
            for i, (start, end) in enumerate(matches, 1):
                summary += f"{i}. Position {start}-{end}: {dna_sequence[start:end+1]}\n"
                # Highlight on DNA viz as well
                try:
                    self.dna_viz.add_match(start, end)
                except Exception:
                    pass
        else:
            summary = f"\n{'='*30}\nNo matches found.\n"
        
        self.results_display.append(summary)
    
    def _pause_simulation(self):
        """Pause running simulation."""
        if self.simulation_timer:
            self.simulation_timer.stop()
        
        self.btn_run.setEnabled(True)
        self.btn_pause.setEnabled(False)
        self.status_label.setText("Simulation paused.")
    
    def _reset_simulation(self):
        """Reset simulation to initial state."""
        if self.simulation_timer:
            self.simulation_timer.stop()
        
        if self.engine:
            try:
                self.engine.reset()
            except Exception:
                pass
        
        self.simulation_index = 0
        self.dna_viz.reset()
        if self.engine_type != AutomataType.PDA:
            self.automata_viz.reset()
        self.transition_log.clear()
        self.results_display.clear()
        
        # Reset visualization buttons
        self.btn_helix.setChecked(True)
        self.btn_glow.setChecked(True)
        
        self.current_state_label.setText("Ready")
        
        self.btn_run.setEnabled(True)
        self.btn_pause.setEnabled(False)
        self.status_label.setText("Simulation reset.")
    
    def _set_speed(self, speed_ms):
        """Set simulation speed."""
        self.simulation_speed = speed_ms
        self.status_label.setText(f"Speed set to {speed_ms}ms per step.")
