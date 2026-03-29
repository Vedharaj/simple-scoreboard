import sys
import signal
from PyQt6.QtWidgets import (QApplication, QTableWidget, QTableWidgetItem,
                             QVBoxLayout, QWidget, QHeaderView, QHBoxLayout,
                             QPushButton, QLabel, QSizeGrip)
from PyQt6.QtCore import Qt, QPoint, QTimer
from PyQt6.QtGui import QColor, QFont
class ProfessionalOverlay(QWidget):
    def __init__(self):
        super().__init__()
        # 1. Window Configuration
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | # No system title bar
            Qt.WindowType.WindowStaysOnTopHint | # Always on top
            Qt.WindowType.Tool # No taskbar icon
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
       
        # Initial size
        self.resize(700, 220)
        self.setMinimumSize(500, 180)
        # 2. UI Structure
        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0) # Remove outer padding
        self.main_layout.setSpacing(0)
        # Title/Close Bar
        self.title_bar = QWidget()
        self.title_bar.setFixedHeight(30)
        self.title_bar.setStyleSheet("background-color: #000; border: 1px solid #555; border-bottom: none;")
       
        title_layout = QHBoxLayout(self.title_bar)
        title_layout.setContentsMargins(10, 0, 5, 0)
       
        self.title_label = QLabel("SCOREBOARD (DRAG TO MOVE)")
        self.title_label.setStyleSheet("color: #888; font-size: 10px; font-weight: bold;")
       
        self.close_btn = QPushButton("✕")
        self.close_btn.setFixedSize(20, 20)
        self.close_btn.setStyleSheet("""
            QPushButton { background: transparent; color: #888; border: none; font-weight: bold; }
            QPushButton:hover { color: white; background: #cc0000; }
        """)
        self.close_btn.clicked.connect(self.close)
        title_layout.addWidget(self.title_label)
        title_layout.addStretch()
        title_layout.addWidget(self.close_btn)
        # Table Setup
        self.table = QTableWidget(4, 6)
        self.init_table()
        self.main_layout.addWidget(self.title_bar)
        self.main_layout.addWidget(self.table)
        # Bottom-right grip enables manual resize for frameless windows.
        self.resize_bar = QWidget()
        self.resize_bar.setFixedHeight(14)
        self.resize_bar.setStyleSheet("background-color: rgba(0, 0, 0, 220); border: 1px solid #555; border-top: none;")
        resize_layout = QHBoxLayout(self.resize_bar)
        resize_layout.setContentsMargins(0, 0, 2, 2)
        resize_layout.addStretch()
        self.size_grip = QSizeGrip(self.resize_bar)
        self.size_grip.setFixedSize(12, 12)
        self.size_grip.setStyleSheet("background: transparent;")
        resize_layout.addWidget(self.size_grip)
        self.main_layout.addWidget(self.resize_bar)
        self.setLayout(self.main_layout)
        self.drag_pos = QPoint()
    def init_table(self):
        # Professional Dark Theme Styling
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #000;
                color: white;
                gridline-color: #444;
                border: 1px solid #555;
                font-family: 'Segoe UI', Arial;
            }
            QHeaderView::section {
                background-color: #000;
                color: #ddd;
                border: 1px solid #555;
                font-weight: bold;
                padding: 4px;
            }
        """)

        headers = ["TEAM", "Shuffled", "puzzle", "bio-scope", "cup taken", "TOTAL"]
        self.table.setHorizontalHeaderLabels(headers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSortIndicator(5, Qt.SortOrder.DescendingOrder)
        self.table.verticalHeader().setVisible(False)
        
        # IMPORTANT: Disable sorting during setup to prevent row-swapping bugs
        self.table.setSortingEnabled(False) 

        teams = [
            ("Team A", "#FF4D4D"), ("Team B", "#4D94FF"),
            ("Team C", "#FFCC00"), ("Team D", "#4DFF88")
        ]

        for row, (name, color) in enumerate(teams):
            # 1. Team Name (Editable)
            name_item = QTableWidgetItem(name)
            name_item.setForeground(QColor(color))
            # Ensure name is editable if you want to change "Team A" to a custom name
            name_item.setFlags(name_item.flags() | Qt.ItemFlag.ItemIsEditable) 
            self.table.setItem(row, 0, name_item)

            # 2. Game Scores (G1 - G4)
            for col in range(1, 5):
                score_item = QTableWidgetItem("0") # Set initial value to 0
                score_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                # Explicitly allow editing
                score_item.setFlags(score_item.flags() | Qt.ItemFlag.ItemIsEditable) 
                self.table.setItem(row, col, score_item)

            # 3. Total Column (Keep non-editable as it's a calculation)
            total_item = QTableWidgetItem("0")
            total_item.setData(Qt.ItemDataRole.EditRole, 0) 
            total_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            total_item.setFlags(total_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            total_item.setForeground(QColor(color))
            self.table.setItem(row, 5, total_item)

        # Re-enable sorting after the table is populated
        self.table.setSortingEnabled(True)
        self.table.sortItems(5, Qt.SortOrder.DescendingOrder)
        self.table.cellChanged.connect(self.update_scores)
        
    def update_scores(self, row, col):
        # Only trigger if one of the score columns (1-4) is changed
        if 1 <= col <= 4:
            self.recalculate_and_sort_totals()

    def recalculate_and_sort_totals(self):
        # Recalculate all totals before sorting to keep team order stable.
        self.table.setSortingEnabled(False)
        self.table.blockSignals(True)

        try:
            for row in range(self.table.rowCount()):
                total = 0
                for col in range(1, 5):
                    item = self.table.item(row, col)
                    if not item:
                        continue

                    text = item.text().strip()
                    if not text:
                        item.setText("0")
                        text = "0"

                    try:
                        score = int(text)
                    except ValueError:
                        score = 0
                        item.setText("0")

                    total += score

                total_item = self.table.item(row, 5)
                if total_item:
                    # Use EditRole so Qt sorts numerically, not lexicographically.
                    total_item.setText(str(total))
                    total_item.setData(Qt.ItemDataRole.EditRole, total)
        finally:
            self.table.blockSignals(False)
            self.table.setSortingEnabled(True)

        self.table.sortItems(5, Qt.SortOrder.DescendingOrder)
    # --- Mouse Events (Moving & Resizing) ---
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            # Move the window
            self.move(event.globalPosition().toPoint() - self.drag_pos)
            event.accept()
    # Right-bottom corner resize handle is handled natively if we enable it,
    # but for frameless windows, we can just let the table expand.
    # To allow resizing, we can use the WindowFlags or custom logic.
    # Added native resize support:
    def resizeEvent(self, event):
        super().resizeEvent(event)
if __name__ == "__main__":
    app = QApplication(sys.argv)
    overlay = ProfessionalOverlay()

    # Keep Python signal handling alive while Qt event loop is running.
    # This allows Ctrl+C from a terminal to terminate the app cleanly.
    signal.signal(signal.SIGINT, lambda *_: app.quit())
    heartbeat = QTimer(app)
    heartbeat.timeout.connect(lambda: None)
    heartbeat.start(100)
   
    # Optional: enable native resizing on frameless window for Windows
    # If on Windows, you can drag the edges to resize
    overlay.setWindowFlags(overlay.windowFlags() | Qt.WindowType.CustomizeWindowHint | Qt.WindowType.WindowSystemMenuHint)
   
    overlay.show()
    sys.exit(app.exec())
