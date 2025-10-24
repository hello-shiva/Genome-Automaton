"""
DNA Visualizer Module - Professional Double Helix Animation
Animated 3D-like DNA double helix with particle effects, smooth transitions,
and stunning visual feedback for genetic pattern analysis.
"""

from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt, QRectF, QPointF, QTimer, QTime
from PyQt5.QtGui import QPainter, QColor, QFont, QPen, QBrush, QLinearGradient, QRadialGradient
import math

class DNAVisualizer(QWidget):
    """Professional DNA sequence visualizer with animated double helix."""
    
    # Color mapping for DNA bases (biotech neon theme)
    BASE_COLORS = {
        'A': QColor(255, 80, 80),    # Red
        'T': QColor(80, 150, 255),   # Blue
        'G': QColor(80, 255, 120),   # Green
        'C': QColor(255, 220, 80),   # Yellow
    }
    
    # Complementary base mapping
    COMPLEMENT = {'A': 'T', 'T': 'A', 'G': 'C', 'C': 'G'}
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.dna_sequence = ""
        self.current_index = -1
        self.matched_ranges = []
        self.scroll_offset = 0
        
        # Animation parameters
        self.animation_time = QTime()
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.update)
        self.animation_timer.start(30)  # 30ms = ~33fps
        
        # Helix parameters - ADJUSTED FOR PROPER 3D LOOK
        self.helix_radius = 60  # Larger radius for wider helix
        self.helix_pitch = 100  # Vertical distance per rotation
        self.base_pair_spacing = 35  # More horizontal spacing
        self.turns = 3  # Number of complete rotations
        
        # Feature toggles
        self.show_helix = True
        self.show_glow = True
        
        self.particle_system = []
        self.pulse_intensity = 0
        self.rotation_angle = 0
        
        # Mouse drag for scrolling
        self._is_dragging = False
        self._drag_start_x = 0
        self._drag_start_offset = 0
        self._drag_start_y = 0
        self._drag_start_v_offset = 0
        
        # Horizontal and vertical scrolling for canvas expansion
        self.v_scroll_offset = 0  # Vertical scroll offset
        self.helix_height = 200  # Virtual height of the helix content
        
        self.setMinimumHeight(250)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setMouseTracking(True)
        
    def set_dna_sequence(self, sequence):
        """Set the DNA sequence to visualize."""
        self.dna_sequence = sequence.upper()
        self.current_index = -1
        self.matched_ranges = []
        self.scroll_offset = 0
        self.animation_time.start()
        self.update()
    
    def set_current_index(self, index):
        """Highlight the base at the given index with particle effect."""
        if index != self.current_index:
            self.current_index = index
            
            # Create particle burst effect
            if 0 <= index < len(self.dna_sequence):
                self._create_particle_burst(index)
            
            # Auto-scroll
            if index >= 0:
                base_x = index * self.base_pair_spacing
                widget_width = self.width()
                
                if base_x - self.scroll_offset > widget_width - 100:
                    self.scroll_offset = base_x - widget_width + 100
                elif base_x - self.scroll_offset < 50:
                    self.scroll_offset = max(0, base_x - 50)
        
        self.update()
    
    def add_match(self, start, end):
        """Add a matched region with glow effect."""
        self.matched_ranges.append((start, end))
        self.update()
    
    def clear_matches(self):
        """Clear all matched regions."""
        self.matched_ranges = []
        self.update()
    
    def reset(self):
        """Reset visualization state."""
        self.current_index = -1
        self.matched_ranges = []
        self.scroll_offset = 0
        self.v_scroll_offset = 0
        self.particle_system = []
        self.update()
    
    def toggle_helix(self):
        """Toggle 3D helix visualization."""
        self.show_helix = not self.show_helix
        self.update()
    
    def toggle_glow(self):
        """Toggle glow effects."""
        self.show_glow = not self.show_glow
        self.update()
    
    def toggle_complement(self):
        """Toggle complementary strand display."""
        self.show_complement = not self.show_complement
        self.update()
    
    def toggle_grid(self):
        """Toggle grid background."""
        self.show_grid = not self.show_grid
        self.update()
    
    def toggle_codon_frames(self):
        """Toggle codon frame highlighting."""
        self.show_codon_frames = not self.show_codon_frames
        self.update()
    
    def _create_particle_burst(self, index):
        """Create particle effect at base position."""
        base_color = self.BASE_COLORS.get(self.dna_sequence[index], QColor(100, 100, 100))
        
        for i in range(12):
            angle = (360 / 12) * i
            self.particle_system.append({
                'angle': angle,
                'speed': 2.5 + (i % 3) * 0.5,
                'life': 1.0,
                'color': base_color,
                'index': index
            })
    
    def _update_particles(self):
        """Update and remove dead particles."""
        for particle in self.particle_system[:]:
            particle['life'] -= 0.05
            if particle['life'] <= 0:
                self.particle_system.remove(particle)
    
    def paintEvent(self, event):
        """Draw the animated DNA double helix."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        
        # Background with gradient
        self._draw_background(painter)
        
        if not self.dna_sequence:
            painter.setPen(QColor(100, 100, 100))
            painter.setFont(QFont('Segoe UI', 14))
            painter.drawText(self.rect(), Qt.AlignCenter, "Enter DNA sequence to visualize")
            return
        
        # Update animations
        self._update_particles()
        if not self.animation_time.isValid():
            self.animation_time.start()
        
        elapsed = self.animation_time.elapsed() / 1000.0
        self.pulse_intensity = 0.5 + 0.5 * math.sin(elapsed * 2)
        self.rotation_angle = elapsed * 30
        
        # Draw the double helix - adjusted for vertical scrolling
        center_y = self.height() // 2 - self.v_scroll_offset
        
        if self.show_helix:
            self._draw_3d_helix(painter, center_y)
        else:
            self._draw_linear_sequence(painter, center_y)
        
        # Draw particles
        self._draw_particles(painter, center_y)
    
    def _draw_background(self, painter):
        """Draw animated gradient background."""
        gradient = QLinearGradient(0, 0, self.width(), self.height())
        gradient.setColorAt(0, QColor(15, 20, 30))
        gradient.setColorAt(0.5, QColor(20, 25, 40))
        gradient.setColorAt(1, QColor(15, 20, 30))
        painter.fillRect(self.rect(), gradient)
        
        # Add subtle scanlines effect
        painter.setPen(QPen(QColor(50, 50, 70, 10), 1))
        for i in range(0, self.height(), 2):
            painter.drawLine(0, i, self.width(), i)
    
    def _draw_3d_helix(self, painter, center_y):
        """Draw 3D-style DNA double helix with proper perspective."""
        
        # Store all base pair data first
        pairs_data = []
        
        for i, base in enumerate(self.dna_sequence):
            x = i * self.base_pair_spacing - self.scroll_offset + 50
            
            if x < -100 or x > self.width() + 100:
                continue
            
            # Calculate helix positions with proper 3D curve
            t = i / max(len(self.dna_sequence), 1)
            
            # Add rotation to the helix (makes it spin smoothly)
            rotation = math.radians(self.rotation_angle)
            
            # Horizontal sine wave (left-right helix motion) + rotation
            helix_x_offset = math.sin(t * math.pi * self.turns + rotation) * self.helix_radius
            
            # Vertical sine wave (up-down helix motion) - opposite phase + rotation
            helix_y_offset = math.cos(t * math.pi * self.turns + rotation) * self.helix_radius
            
            # Top strand position
            top_x = x + helix_x_offset
            top_y = center_y - 50 + helix_y_offset
            
            # Bottom strand position (opposite curve)
            bottom_x = x - helix_x_offset
            bottom_y = center_y + 50 - helix_y_offset
            
            # Get colors
            top_color = self.BASE_COLORS.get(base, QColor(100, 100, 100))
            complement_base = self.COMPLEMENT.get(base, 'N')
            bottom_color = self.BASE_COLORS.get(complement_base, QColor(100, 100, 100))
            
            # Determine states
            is_current = (i == self.current_index)
            is_matched = any(start <= i <= end for start, end in self.matched_ranges)
            
            pairs_data.append({
                'i': i,
                'x': x,
                'top_x': top_x,
                'top_y': top_y,
                'bottom_x': bottom_x,
                'bottom_y': bottom_y,
                'top_base': base,
                'top_color': top_color,
                'bottom_base': complement_base,
                'bottom_color': bottom_color,
                'is_current': is_current,
                'is_matched': is_matched,
                'helix_y_offset': helix_y_offset,
                'depth': helix_y_offset  # Use for sorting
            })
        
        # Draw backbones first (behind everything)
        painter.setPen(QPen(QColor(80, 100, 140), 3))
        
        for i in range(len(pairs_data) - 1):
            curr = pairs_data[i]
            next_pair = pairs_data[i + 1]
            
            # Top strand backbone
            painter.drawLine(int(curr['top_x']), int(curr['top_y']), 
                           int(next_pair['top_x']), int(next_pair['top_y']))
            
            # Bottom strand backbone
            painter.drawLine(int(curr['bottom_x']), int(curr['bottom_y']),
                           int(next_pair['bottom_x']), int(next_pair['bottom_y']))
        
        # Draw bridges and bases (sorted by depth for proper 3D effect)
        pairs_data.sort(key=lambda p: p['depth'])
        
        for pair in pairs_data:
            # Draw connecting bridge
            if self.show_glow and (pair['is_current'] or pair['is_matched']):
                self._draw_glowing_bridge(painter, pair['top_x'], pair['top_y'], 
                                         pair['bottom_x'], pair['bottom_y'], pair['is_matched'])
            else:
                painter.setPen(QPen(QColor(60, 100, 140, 120), 2))
                painter.drawLine(int(pair['top_x']), int(pair['top_y']), 
                               int(pair['bottom_x']), int(pair['bottom_y']))
            
            # Draw bases
            self._draw_helix_base(painter, pair['top_x'], pair['top_y'], pair['top_base'], 
                                pair['top_color'], pair['is_current'], pair['is_matched'], True)
            
            self._draw_helix_base(painter, pair['bottom_x'], pair['bottom_y'], pair['bottom_base'],
                                pair['bottom_color'], pair['is_current'], pair['is_matched'], False)
    
    def _draw_helix_base(self, painter, x, y, base, color, is_current, is_matched, is_top):
        """Draw a base pair in the helix with 3D effect and depth."""
        # Size varies with depth (back bases smaller)
        base_size = 20 if is_current else 16
        size = base_size
        
        if is_matched:
            # Single clean glow for matched base
            glow_color = QColor(0, 255, 150)
            painter.setPen(QPen(glow_color, 2))
            
            # Draw outer glow ring (no multiple layers)
            painter.setBrush(QBrush(QColor(0, 255, 150, 40)))
            painter.drawEllipse(QPointF(x, y), size + 10, size + 10)
        elif is_current:
            # Pulsing current base with clean aura
            glow_size = size + int(self.pulse_intensity * 8)
            painter.setPen(QPen(QColor(0, 255, 255), 2))
            painter.setBrush(QBrush(QColor(0, 255, 255, 50)))
            painter.drawEllipse(QPointF(x, y), glow_size, glow_size)
            painter.setPen(QPen(color, 2))
        else:
            painter.setPen(QPen(color, 2))
        
        # Draw base circle with radial gradient (3D sphere effect)
        gradient = QRadialGradient(QPointF(x - size/3, y - size/3), size)
        gradient.setColorAt(0, color.lighter(180))
        gradient.setColorAt(0.5, color.lighter(120))
        gradient.setColorAt(1, color.darker(130))
        painter.setBrush(QBrush(gradient))
        painter.drawEllipse(QPointF(x, y), size, size)
        
        # Draw base letter
        painter.setFont(QFont('Consolas', 11 if is_current else 9, QFont.Bold))
        painter.setPen(QColor(255, 255, 255))
        painter.drawText(QRectF(x - size, y - size, size * 2, size * 2), Qt.AlignCenter, base)
    
    def _draw_glowing_bridge(self, painter, x1, y1, x2, y2, is_matched):
        """Draw glowing bridge between base pairs."""
        if is_matched:
            gradient = QLinearGradient(x1, y1, x2, y2)
            gradient.setColorAt(0, QColor(0, 255, 150, 200))
            gradient.setColorAt(0.5, QColor(0, 200, 100, 255))
            gradient.setColorAt(1, QColor(0, 255, 150, 200))
            
            pen = QPen(QColor(0, 255, 150, 200), 5)
            painter.setPen(pen)
        else:
            gradient = QLinearGradient(x1, y1, x2, y2)
            gradient.setColorAt(0, QColor(0, 255, 255, 150))
            gradient.setColorAt(1, QColor(100, 200, 255, 100))
            
            pen = QPen(QColor(0, 255, 255, 150), 4)
            painter.setPen(pen)
        
        painter.drawLine(int(x1), int(y1), int(x2), int(y2))
    
    def _draw_linear_sequence(self, painter, center_y):
        """Draw linear sequence mode (toggle alternative)."""
        y = center_y
        
        for i, base in enumerate(self.dna_sequence):
            x = i * self.base_pair_spacing - self.scroll_offset + 30
            
            if x < -50 or x > self.width() + 50:
                continue
            
            color = self.BASE_COLORS.get(base, QColor(100, 100, 100))
            is_current = (i == self.current_index)
            is_matched = any(start <= i <= end for start, end in self.matched_ranges)
            
            size = 20 if is_current else 8
            
            if is_current or is_matched:
                painter.setPen(QPen(QColor(0, 255, 255), 2))
            else:
                painter.setPen(QPen(color, 1))
            
            gradient = QRadialGradient(QPointF(x, y), size)
            gradient.setColorAt(0, color.lighter(140))
            gradient.setColorAt(1, color)
            painter.setBrush(QBrush(gradient))
            painter.drawEllipse(QPointF(x, y), size, size)
            
            painter.setFont(QFont('Consolas', 9, QFont.Bold))
            painter.setPen(QColor(255, 255, 255))
            painter.drawText(QRectF(x - size, y - size, size * 2, size * 2), 
                           Qt.AlignCenter, base)
    
    def _draw_particles(self, painter, center_y):
        """Draw particle burst effects."""
        for particle in self.particle_system:
            i = particle['index']
            x_base = i * self.base_pair_spacing - self.scroll_offset + 30
            
            angle_rad = math.radians(particle['angle'])
            distance = particle['speed'] * 50 * (1 - particle['life'])
            
            x = x_base + math.cos(angle_rad) * distance
            y = center_y + math.sin(angle_rad) * distance
            
            alpha = int(particle['life'] * 200)
            color = QColor(particle['color'])
            color.setAlpha(alpha)
            
            size = 3 + particle['life'] * 2
            painter.setBrush(QBrush(color))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPointF(x, y), size, size)

    def wheelEvent(self, event):
        """Handle mouse wheel scrolling for horizontal and vertical navigation."""
        # Get modifiers
        modifiers = event.modifiers()
        delta = event.angleDelta()
        
        scroll_amount = 50
        max_scroll = max(0, len(self.dna_sequence) * self.base_pair_spacing - self.width() + 100)
        max_v_scroll = max(0, self.helix_height - self.height() + 100)
        
        if modifiers & Qt.ShiftModifier:
            # Shift + wheel = vertical scroll
            v_delta = -delta.y() if delta.y() != 0 else delta.x()
            if v_delta > 0:
                self.v_scroll_offset = min(max_v_scroll, self.v_scroll_offset + scroll_amount)
            else:
                self.v_scroll_offset = max(0, self.v_scroll_offset - scroll_amount)
        else:
            # Regular wheel = horizontal scroll (default behavior)
            h_delta = delta.x()
            if h_delta == 0:
                h_delta = -delta.y()
            
            if h_delta > 0:
                self.scroll_offset = max(0, self.scroll_offset - scroll_amount)
            else:
                self.scroll_offset = min(max_scroll, self.scroll_offset + scroll_amount)
        
        self.update()
    
    def keyPressEvent(self, event):
        """Handle keyboard navigation."""
        if event.isAutoRepeat():
            return
        
        scroll_amount = 30
        max_scroll = max(0, len(self.dna_sequence) * self.base_pair_spacing - self.width() + 100)
        max_v_scroll = max(0, self.helix_height - self.height() + 100)
        
        if event.key() == Qt.Key_Left:
            # Scroll left
            self.scroll_offset = max(0, self.scroll_offset - scroll_amount)
            self.update()
        elif event.key() == Qt.Key_Right:
            # Scroll right
            self.scroll_offset = min(max_scroll, self.scroll_offset + scroll_amount)
            self.update()
        elif event.key() == Qt.Key_Home:
            # Jump to start
            self.scroll_offset = 0
            self.update()
        elif event.key() == Qt.Key_End:
            # Jump to end
            self.scroll_offset = max_scroll
            self.update()
        elif event.key() == Qt.Key_Up:
            # Scroll up
            self.v_scroll_offset = max(0, self.v_scroll_offset - scroll_amount)
            self.update()
        elif event.key() == Qt.Key_Down:
            # Scroll down
            self.v_scroll_offset = min(max_v_scroll, self.v_scroll_offset + scroll_amount)
            self.update()
        else:
            super().keyPressEvent(event)
    
    def mousePressEvent(self, event):
        """Handle mouse press for drag scrolling."""
        if event.button() == Qt.LeftButton:
            self._is_dragging = True
            self._drag_start_x = event.x()
            self._drag_start_y = event.y()
            self._drag_start_offset = self.scroll_offset
            self._drag_start_v_offset = self.v_scroll_offset
            self.setCursor(Qt.ClosedHandCursor)
    
    def mouseMoveEvent(self, event):
        """Handle mouse move for drag scrolling."""
        if self._is_dragging:
            delta_x = event.x() - self._drag_start_x
            delta_y = event.y() - self._drag_start_y
            max_scroll = max(0, len(self.dna_sequence) * self.base_pair_spacing - self.width() + 100)
            max_v_scroll = max(0, self.helix_height - self.height() + 100)
            
            # Drag right = scroll left (negative delta), drag left = scroll right (positive delta)
            self.scroll_offset = self._drag_start_offset - delta_x
            self.scroll_offset = max(0, min(max_scroll, self.scroll_offset))
            
            # Drag down = scroll up (negative delta), drag up = scroll down (positive delta)
            self.v_scroll_offset = self._drag_start_v_offset - delta_y
            self.v_scroll_offset = max(0, min(max_v_scroll, self.v_scroll_offset))
            self.update()
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release to stop drag scrolling."""
        if event.button() == Qt.LeftButton:
            self._is_dragging = False
            self.setCursor(Qt.ArrowCursor)

