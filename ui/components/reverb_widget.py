from PyQt6.QtWidgets import QFrame, QLabel, QVBoxLayout
from PyQt6.QtCore import Qt


class ReverbWidget(QFrame):
    """
    Composant Reverb
    Paramètres : ?
    """

    def __init__(self):
        super().__init__()
        self.setFixedSize(400, 280)
        self.setStyleSheet("background: #0d1117; border: 1px solid #30363d; border-radius: 6px;")

        layout = QVBoxLayout(self)
        lbl = QLabel("Reverb — à construire")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet("color: #555; font-size: 11px;")
        layout.addWidget(lbl)