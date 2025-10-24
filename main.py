"""
Automata for Genetic Pattern Analysis
Main entry point for the application.
Integrates UI layout with automata engine and visualizers.
"""

import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from ui_layout import MainWindow

def main():
    """Initialize and run the application."""
    # Enable high DPI scaling for better display on modern screens
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    app = QApplication(sys.argv)
    
    # Load custom stylesheet
    try:
        with open('assets/theme.qss', 'r') as f:
            app.setStyleSheet(f.read())
    except FileNotFoundError:
        print("Warning: theme.qss not found. Using default styling.")
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
