"""
PDA Visualizer
Renders a simple live view for PDA engines: control-state badge and stack.
"""

from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QPainter, QColor, QFont, QPen, QBrush


class PDAVisualizer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.stack = []
        self.control_state = "push"
        self.automaton = None
        self.setMinimumHeight(200)

    def set_automaton(self, automaton):
        self.automaton = automaton
        self.update_stack(getattr(automaton, 'stack', []), getattr(automaton, 'mode', 'push'))

    def update_stack(self, stack, control_state):
        self.stack = list(stack)
        self.control_state = control_state
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        # Background
        p.fillRect(self.rect(), QColor(25, 30, 40))

        # Control state badge
        badge_text = f"State: {self.control_state.upper()}"
        p.setFont(QFont('Segoe UI', 11, QFont.Bold))
        p.setPen(QColor(180, 200, 220))
        p.drawText(QRectF(10, 10, self.width()-20, 24), Qt.AlignLeft | Qt.AlignVCenter, badge_text)

        # Draw stack (top at the right)
        cell_w = 36
        cell_h = 28
        gap = 6
        left = 20
        top = 50
        p.setFont(QFont('Consolas', 11, QFont.Bold))
        for i, sym in enumerate(self.stack[-20:]):  # cap to last 20 for brevity
            idx = len(self.stack[-20:]) - 1 - i
            x = left + idx * (cell_w + gap)
            y = top
            rect = QRectF(x, y, cell_w, cell_h)
            # highlight top-of-stack
            bg = QColor(0, 200, 255, 80) if i == 0 else QColor(90, 110, 140)
            p.setBrush(QBrush(bg))
            p.setPen(QPen(QColor(150, 170, 200), 2))
            p.drawRoundedRect(rect, 6, 6)
            p.setPen(QColor(255, 255, 255))
            p.drawText(rect, Qt.AlignCenter, sym)
