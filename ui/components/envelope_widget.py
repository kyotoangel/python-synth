from PyQt6.QtWidgets import QFrame, QLabel, QVBoxLayout
from PyQt6.QtCore import Qt


class EnvelopeWidget(QFrame):
    """
    Composant Enveloppe (ENV 1/2/3) — à construire.
    Paramètres : Delay, Attack, Hold, Decay, Sustain, Release
    """

    def __init__(self):
        super().__init__()
        self.setFixedSize(400, 200)
        self.setStyleSheet("background: #0d1117; border: 1px solid #30363d; border-radius: 6px;")

        layout = QVBoxLayout(self)
        lbl = QLabel("ENV — à construire")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet("color: #555; font-size: 11px;")
        layout.addWidget(lbl)