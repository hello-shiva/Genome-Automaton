"""
Automata Visualizer Module
Draws and animates the DFA state diagram with transitions.
"""

import math
from PyQt5.QtWidgets import QWidget, QSizePolicy
from PyQt5.QtCore import Qt, QPointF, QRectF
from PyQt5.QtGui import QPainter, QColor, QFont, QPen, QBrush, QPainterPath

class AutomataVisualizer(QWidget):
    """Widget for visualizing DFA/NFA/ε-NFA state diagrams and transitions."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.automaton = None
        self.current_state = 0
        self.current_states = set()
        self.last_transition = None  # (from_state, to_state, symbol)
        self.state_positions = {}
        self.node_radius = 35
        
        # Allow the diagram to expand/shrink naturally within splitters
        self.setMinimumHeight(250)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Interactive view controls (zoom/pan)
        self._zoom = 1.0
        self._min_zoom = 0.6
        self._max_zoom = 3.0
        self._vertical_zoom = 1.0
        self._min_vertical_zoom = 0.6
        self._max_vertical_zoom = 3.0
        self._pan = QPointF(0, 0)
        self._v_pan = 0  # Vertical panning for canvas area expansion
        self._dragging = False
        self._last_mouse_pos = None
        # Interaction enhancements
        self.setMouseTracking(True)
        self._hover_state = None
        self._dim_nonfocus = True
        self.show_restart_edges = False  # hide NFA global restarts by default
    
    def set_automaton(self, automaton):
        """Set any FA-like automaton (DFA/NFA/ENFA) to visualize."""
        self.automaton = automaton
        self.current_state = 0
        # Reset state index map for consistent layout
        self._state_index_map = {}
        # Pre-enumerate states to lock indices
        try:
            states = list(self._safe_get_states())
            self._state_index_map = {s: i for i, s in enumerate(states)}
        except Exception:
            self._state_index_map = {}
        self.current_states = self._safe_get_current_states()
        self.last_transition = None
        self.reset_view()
        self._calculate_state_positions()
        self.update()

    # Back-compat for older calls
    def set_dfa(self, dfa):
        self.set_automaton(dfa)
    
    def set_current_state(self, state):
        """Update the current state highlight."""
        self.current_state = state
        self.update()
    
    def set_current_states(self, states):
        """Update highlights for multiple current states (NFA/ENFA)."""
        try:
            self.current_states = set(states)
        except Exception:
            self.current_states = set()
        self.update()

    def set_last_transition(self, from_state, to_state, symbol):
        """Highlight a transition."""
        self.last_transition = (from_state, to_state, symbol)
        self.update()
    
    def clear_transition(self):
        """Clear transition highlight."""
        self.last_transition = None
        self.update()
    
    def reset(self):
        """Reset visualization state."""
        self.current_state = 0
        self.last_transition = None
        self.update()

    def reset_view(self):
        """Reset zoom and pan to defaults."""
        self._zoom = 1.0
        self._vertical_zoom = 1.0
        self._pan = QPointF(0, 0)
        self._v_pan = 0
    
    def _calculate_state_positions(self):
        """Calculate positions for state nodes. Prefer layered flow when small."""
        if not self.automaton:
            return

        # Layout bounds
        top_margin = 60
        side_margin = 50
        bottom_margin = 40

        width = max(1, self.width() - 2 * side_margin)
        height = max(1, self.height() - (top_margin + bottom_margin))

        states = self._safe_get_states()
        num_states = len(states)

        # Try layered left-to-right layout for small graphs (<= 12 states)
        use_layered = False
        try:
            atype = (self.automaton.get_type() if hasattr(self.automaton, 'get_type') else None)
            if atype in ("NFA", "Epsilon-NFA") and num_states <= 12:
                use_layered = True
        except Exception:
            pass

        if use_layered and hasattr(self.automaton, 'get_transitions'):
            # Build adjacency ignoring symbols AND ignoring edges back to start (final returns)
            trans = self._safe_get_transitions()
            initials = set(self._safe_get_initial_states()) or {0}
            
            adj = {}
            for (u, _sym), vset in trans.items():
                for v in vset:
                    # Skip back-to-start edges for depth calculation
                    if v not in initials or u in initials:
                        adj.setdefault(u, set()).add(v)

            # BFS for layered depths from start
            depth = {}
            for init in initials:
                depth[init] = 0
            queue = list(initials)
            seen = set(initials)
            
            while queue:
                u = queue.pop(0)
                for v in adj.get(u, set()):
                    if v not in seen:
                        depth[v] = depth.get(u, 0) + 1
                        seen.add(v)
                        queue.append(v)

            # Assign unvisited nodes to depth 0 (shouldn't happen with valid NFA)
            for s in states:
                depth.setdefault(s, 0)

            max_d = max(depth.values()) if depth else 0
            cols = max(1, max_d + 1)
            
            # Horizontal spacing between columns
            col_width = width / max(1, cols)

            # Group by depth to arrange rows
            layers = {}
            for s in states:
                layers.setdefault(depth[s], []).append(s)

            # Place nodes per column, vertically centered
            for d, layer_states in layers.items():
                layer_states = self._ordered_states(layer_states)
                rows = len(layer_states)
                
                # Vertical spacing for this column
                if rows > 1:
                    total_h = min(height * 0.7, rows * 120)
                    gap = total_h / (rows - 1)
                else:
                    total_h = 0
                    gap = 0
                
                base_y = top_margin + (height - total_h) / 2
                x = side_margin + col_width * (d + 0.5)
                
                for i, s in enumerate(layer_states):
                    y = base_y + i * gap
                    idx = self._state_index(s)
                    # Apply zoom, pan, and vertical panning
                    self.state_positions[idx] = QPointF(
                        (x + self._pan.x()) * self._zoom,
                        (y + self._pan.y()) * self._zoom * self._vertical_zoom - self._v_pan
                    )
            return

        # Fallback: circular/elliptic layout
        center_x = side_margin + width / 2 + self._pan.x()
        center_y = top_margin + height / 2 + self._pan.y() - self._v_pan
        spread = 1.0 + min(1.2, max(0, (num_states - 8) * 0.05))
        radius_x = max(60, min(width / 2 - 60, 260)) * self._zoom * spread
        radius_y = max(45, min(height / 2 - 60, 200)) * self._zoom * spread * self._vertical_zoom

        for i in range(num_states):
            angle = 0 if num_states == 1 else 2 * math.pi * i / num_states - math.pi / 2
            x = center_x + radius_x * math.cos(angle)
            y = center_y + radius_y * math.sin(angle)
            self.state_positions[i] = QPointF(x, y)
    
    def paintEvent(self, event):
        """Draw the automata state diagram."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Background
        painter.fillRect(self.rect(), QColor(25, 30, 40))
        
        if not self.automaton:
            # Draw placeholder
            painter.setPen(QColor(100, 100, 100))
            painter.setFont(QFont('Segoe UI', 12))
            painter.drawText(self.rect(), Qt.AlignCenter,
                           "Enter a pattern to generate automaton")
            return
        
        # Recalculate positions in case of resize
        self._calculate_state_positions()
        
        # Draw transitions first (so they appear behind nodes)
        self._draw_transitions(painter)
        
        # Draw state nodes
        self._draw_states(painter)
        
        # Draw pattern label
        painter.setPen(QColor(150, 150, 200))
        painter.setFont(QFont('Segoe UI', 11, QFont.Bold))
        # Determine type label robustly
        try:
            type_label = getattr(self.automaton, 'automata_type', None) or (
                self.automaton.get_type() if hasattr(self.automaton, 'get_type') else 'FA'
            )
        except Exception:
            type_label = 'FA'
        painter.drawText(QRectF(10, 10, self.width() - 20, 30),
                         Qt.AlignCenter,
                         f"Automaton: {type_label}")

    # ------------- Interaction: zoom & pan -------------
    def wheelEvent(self, event):
        # Zoom in/out around the center; mouse position centric zoom would
        # require mapping through transforms, so we keep it simple.
        delta = event.angleDelta().y() if hasattr(event, 'angleDelta') else event.delta()
        factor = 1.0 + (0.1 if delta > 0 else -0.1)
        self._zoom = max(self._min_zoom, min(self._max_zoom, self._zoom * factor))
        self.update()

    def keyPressEvent(self, event):
        """Handle keyboard input for vertical panning and view control."""
        if event.isAutoRepeat():
            return
        
        scroll_amount = 30
        max_v_pan = max(0, 200)  # Estimate of canvas height
        
        if event.key() == Qt.Key_Up:
            # Vertical pan up (scroll down on canvas)
            self._v_pan = min(max_v_pan, self._v_pan + scroll_amount)
            self._calculate_state_positions()
            self.update()
        elif event.key() == Qt.Key_Down:
            # Vertical pan down (scroll up on canvas)
            self._v_pan = max(0, self._v_pan - scroll_amount)
            self._calculate_state_positions()
            self.update()
        elif event.key() == Qt.Key_R:
            # Reset view
            self.reset_view()
            self._calculate_state_positions()
            self.update()
        else:
            super().keyPressEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._dragging = True
            self._last_mouse_pos = event.pos()
            self.setCursor(Qt.ClosedHandCursor)
            self.setFocus()

    def mouseMoveEvent(self, event):
        if self._dragging and self._last_mouse_pos is not None:
            delta = event.pos() - self._last_mouse_pos
            self._pan += QPointF(delta.x(), delta.y())
            self._v_pan = max(0, self._v_pan - delta.y())  # Add vertical panning
            self._last_mouse_pos = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._dragging = False
            self._last_mouse_pos = None
            self.setCursor(Qt.ArrowCursor)

    def mouseDoubleClickEvent(self, event):
        # Double-click to reset the view
        self.reset_view()
        self.update()
    
    def _draw_states(self, painter):
        """Draw all state nodes."""
        zoom_radius = max(20, int(self.node_radius * self._zoom))
        states = self._ordered_states(self._safe_get_states())
        accept = self._safe_get_accept_states()
        current_set = self._safe_get_current_states()
        for state in states:
            idx = self._state_index(state)
            pos = self.state_positions.get(idx)
            if not pos:
                continue
            
            is_current = (state in current_set)
            is_accept = (state in accept)
            
            # Determine colors
            if is_accept:
                if is_current:
                    fill_color = QColor(0, 255, 150, 200)
                    border_color = QColor(0, 255, 150)
                    border_width = 4
                else:
                    fill_color = QColor(0, 180, 100, 150)
                    border_color = QColor(0, 200, 120)
                    border_width = 3
            elif is_current:
                fill_color = QColor(0, 200, 255, 180)
                border_color = QColor(0, 255, 255)
                border_width = 4
            else:
                fill_color = QColor(60, 70, 90)
                border_color = QColor(120, 140, 170)
                border_width = 2
            
            # Draw outer circle for accept states
            if is_accept:
                painter.setPen(QPen(border_color, 2))
                painter.setBrush(Qt.NoBrush)
                painter.drawEllipse(pos, zoom_radius + 5, zoom_radius + 5)
            
            # Draw main circle
            painter.setPen(QPen(border_color, border_width))
            painter.setBrush(QBrush(fill_color))
            painter.drawEllipse(pos, zoom_radius, zoom_radius)
            
            # Draw state label
            painter.setPen(QColor(255, 255, 255))
            painter.setFont(QFont('Segoe UI', 12, QFont.Bold))
            label = self._safe_get_state_label(state)
            painter.drawText(QRectF(pos.x() - zoom_radius, pos.y() - 10,
                               zoom_radius * 2, 20),
                         Qt.AlignCenter, label)

              # Draw state description below
            desc = "✓" if is_accept else ""
            painter.setFont(QFont('Segoe UI', 8))
            painter.setPen(QColor(180, 180, 200))
            painter.drawText(QRectF(pos.x() - zoom_radius - 10, pos.y() + 10,
                            zoom_radius * 2 + 20, 20),
                        Qt.AlignCenter, desc)
    
    def _draw_transitions(self, painter):
        """Draw transition arrows between states."""
        trans = self._safe_get_transitions()
        if not trans:
            return

        # Optionally filter noisy restart edges (e.g., NFA restarts → initials)
        initials = self._safe_get_initial_states()
        # Preserve special restart edges (final-return) if engine exposes them
        keep_restart: set = set()
        if hasattr(self.automaton, 'get_important_restart_edges'):
            try:
                keep_restart = set(self.automaton.get_important_restart_edges())
            except Exception:
                keep_restart = set()

        if self.show_restart_edges is False and initials:
            filtered = {}
            for (s, sym), nset in trans.items():
                preserved_to_initial = set()
                if (s, sym) in keep_restart:
                    preserved_to_initial = set(n for n in nset if n in initials)
                nn = (set(nset) - set(initials)) | preserved_to_initial
                if nn:
                    filtered[(s, sym)] = nn
            trans = filtered
        
        # Group transitions by (from_state, to_state) to handle multiple symbols
        grouped_transitions = {}
        for (state, symbol), next_states in trans.items():
            for ns in next_states:
                key = (state, ns)
                grouped_transitions.setdefault(key, []).append(symbol)
        
        # For curved vs straight: detect bidirectional pairs
        bidir_pairs = set()
        for (a, b) in list(grouped_transitions.keys()):
            if (b, a) in grouped_transitions:
                bidir_pairs.add((min(a, b, key=str), max(a, b, key=str)))

        # Draw each unique transition
        for (from_state, to_state), symbols in grouped_transitions.items():
            fi = self._state_index(from_state)
            ti = self._state_index(to_state)
            if fi not in self.state_positions or ti not in self.state_positions:
                continue
            from_pos = self.state_positions[fi]
            to_pos = self.state_positions[ti]
            
            # Check if this transition was just taken
            is_active = (self.last_transition and 
                        self.last_transition[0] == from_state and
                        self.last_transition[1] == to_state)
            
            # Self-loop
            if fi == ti:
                self._draw_self_loop(painter, from_pos, symbols, is_active)
            else:
                key = (min(from_state, to_state, key=str), max(from_state, to_state, key=str))
                curved = key in bidir_pairs
                # Curve edges that return to an initial state for better readability
                try:
                    if to_state in initials and from_state != to_state:
                        curved = True
                except Exception:
                    pass
                self._draw_arrow(painter, from_pos, to_pos, symbols, is_active, curved)
    
    def _draw_arrow(self, painter, from_pos, to_pos, symbols, is_active, curved=False):
        """Draw an arrow from one state to another."""
        # Calculate arrow points (accounting for node radius)
        dx = to_pos.x() - from_pos.x()
        dy = to_pos.y() - from_pos.y()
        distance = math.sqrt(dx*dx + dy*dy)
        
        if distance < 0.01:
            return
        
        # Unit vector
        ux = dx / distance
        uy = dy / distance
        
        # Start and end points (on circle edges)
        r = max(20, int(self.node_radius * self._zoom))
        start = QPointF(from_pos.x() + ux * r,
                   from_pos.y() + uy * r)
        end = QPointF(to_pos.x() - ux * r,
                 to_pos.y() - uy * r)
        
        # Determine if this is an epsilon-only edge; dashed style for ε
        is_epsilon = all(s is None for s in symbols)
        pen = QPen(QColor(0, 255, 255), 3) if is_active else QPen(QColor(100, 120, 150), 1)
        if is_epsilon:
            pen.setStyle(Qt.DashLine)
        # Dim non-focused edges when hovering a node
        if self._dim_nonfocus and self._hover_state is not None:
            try:
                hover_idx = self._state_index(self._hover_state)
                if hover_idx not in (None,):
                    if not (from_pos == self.state_positions.get(hover_idx) or to_pos == self.state_positions.get(hover_idx)):
                        c = pen.color(); c.setAlpha(90); pen.setColor(c)
            except Exception:
                pass
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)

        if curved:
            # Quadratic Bezier with control point offset perpendicular to vector
            mid = QPointF((start.x() + end.x()) / 2, (start.y() + end.y()) / 2)
            # perpendicular
            nx, ny = -uy, ux
            # Much tighter curvature for return-to-start edges
            curvature = min(40, distance * 0.08)
            ctrl = QPointF(mid.x() + nx * curvature, mid.y() + ny * curvature)
            path = QPainterPath(start)
            path.quadTo(ctrl, end)
            painter.drawPath(path)
        else:
            painter.drawLine(start, end)
        
        # Draw arrowhead
        arrow_size = 10
        angle = math.atan2(dy, dx)
        p1 = QPointF(end.x() - arrow_size * math.cos(angle - math.pi/6),
                    end.y() - arrow_size * math.sin(angle - math.pi/6))
        p2 = QPointF(end.x() - arrow_size * math.cos(angle + math.pi/6),
                    end.y() - arrow_size * math.sin(angle + math.pi/6))
        
        path = QPainterPath()
        path.moveTo(end)
        path.lineTo(p1)
        path.lineTo(p2)
        path.closeSubpath()
        
        if is_active:
            painter.setBrush(QBrush(QColor(0, 255, 255)))
        else:
            painter.setBrush(QBrush(QColor(100, 120, 150)))
        painter.drawPath(path)
        
        # Draw label (symbols that trigger this transition)
        def sym_to_text(s):
            return 'ε' if s is None else str(s)
        label_syms = [sym_to_text(s) for s in symbols[:2]]
        label = ",".join(label_syms)
        if len(symbols) > 2:
            label += "..."
        
        mid_x = (from_pos.x() + to_pos.x()) / 2
        mid_y = (from_pos.y() + to_pos.y()) / 2
        
        # Offset label perpendicular to arrow
        offset = 15
        label_x = mid_x - uy * offset
        label_y = mid_y + ux * offset
        
        painter.setFont(QFont('Consolas', 9, QFont.Bold))
        color = QColor(0, 255, 255) if is_active else QColor(150, 170, 200)
        if self._dim_nonfocus and self._hover_state is not None:
            try:
                hover_idx = self._state_index(self._hover_state)
                if hover_idx not in (None,):
                    if not (from_pos == self.state_positions.get(hover_idx) or to_pos == self.state_positions.get(hover_idx)):
                        color = QColor(color.red(), color.green(), color.blue(), 120)
            except Exception:
                pass
        painter.setPen(color)
        
        painter.drawText(QPointF(label_x - 20, label_y), label)
    
    def _draw_self_loop(self, painter, pos, symbols, is_active):
        """Draw a self-loop arc."""
        if is_active:
            painter.setPen(QPen(QColor(0, 255, 255), 3))
        else:
            painter.setPen(QPen(QColor(100, 120, 150), 1))
        
        # Draw loop above the node
        loop_r = max(20, int(self.node_radius * self._zoom))
        loop_rect = QRectF(pos.x() - 20, pos.y() - loop_r - 40, 40, 40)
        painter.drawArc(loop_rect, 0, 180 * 16)  # 180 degrees
        
        # Label
        def sym_to_text(s):
            return 'ε' if s is None else str(s)
        label = ",".join([sym_to_text(s) for s in symbols[:2]])
        if len(symbols) > 2:
            label += "..."
        
        painter.setFont(QFont('Consolas', 9, QFont.Bold))
        if is_active:
            painter.setPen(QColor(0, 255, 255))
        else:
            painter.setPen(QColor(150, 170, 200))
        
        painter.drawText(QPointF(pos.x() - 15, pos.y() - loop_r - 45), label)

    # ----- Safe accessors for heterogeneous engines -----
    def _safe_get_states(self):
        if hasattr(self.automaton, 'get_states'):
            return list(self.automaton.get_states())
        # DFA fallback
        return list(range(getattr(self.automaton, 'num_states', 0)))

    def _ordered_states(self, states):
        # Group tuple states (i,k) to form clean clusters for NFA
        try:
            return sorted(states, key=lambda s: (s[0], s[1]) if isinstance(s, tuple) and len(s) == 2 else (9999, str(s)))
        except Exception:
            return list(states)

    def _safe_get_accept_states(self):
        if hasattr(self.automaton, 'get_accept_states'):
            return set(self.automaton.get_accept_states())
        acc = getattr(self.automaton, 'accept_state', None)
        return {acc} if acc is not None else set()

    def _safe_get_current_states(self):
        if hasattr(self.automaton, 'get_current_states'):
            return set(self.automaton.get_current_states())
        return {getattr(self.automaton, 'current_state', 0)}

    def _safe_get_transitions(self):
        if hasattr(self.automaton, 'get_transitions'):
            return self.automaton.get_transitions()
        # Convert DFA table if present
        trans = {}
        t = getattr(self.automaton, 'transitions', {})
        for (s, sym), ns in t.items():
            trans.setdefault((s, sym), set()).add(ns)
        return trans

    def _safe_get_initial_states(self):
        if hasattr(self.automaton, 'get_initial_states'):
            try:
                return set(self.automaton.get_initial_states())
            except Exception:
                return set()
        # DFA start is {0}
        return {0}

    def _safe_get_state_label(self, state):
        if hasattr(self.automaton, 'get_state_label'):
            try:
                return str(self.automaton.get_state_label(state))
            except Exception:
                pass
        return f"{state}"

    def _state_index(self, state):
        """Map arbitrary state objects to a stable index for node placement."""
        # For consistent layout across runs, index by enumeration order
        if not hasattr(self, '_state_index_map'):
            self._state_index_map = {}
        key = state
        if key not in self._state_index_map:
            self._state_index_map[key] = len(self._state_index_map)
        return self._state_index_map[key]

    # ----- Hover focus handling -----
    def _nearest_state_under(self, pos):
        # Find closest node center within radius threshold
        try:
            for state in self._ordered_states(self._safe_get_states()):
                idx = self._state_index(state)
                p = self.state_positions.get(idx)
                if not p:
                    continue
                dist2 = (pos.x() - p.x())**2 + (pos.y() - p.y())**2
                r = max(20, int(self.node_radius * self._zoom))
                if dist2 <= (r*1.2)**2:
                    return state
        except Exception:
            pass
        return None

    def mouseMoveEvent(self, event):
        # Keep panning behavior if dragging
        if self._dragging and self._last_mouse_pos is not None:
            delta = event.pos() - self._last_mouse_pos
            self._pan += QPointF(delta.x(), delta.y())
            self._last_mouse_pos = event.pos()
            self.update()
            return
        # Hover highlighting
        st = self._nearest_state_under(event.pos())
        if st != self._hover_state:
            self._hover_state = st
            self.update()
