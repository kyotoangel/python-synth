from PyQt6.QtWidgets import QHBoxLayout, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt
from components.base_component import SynthComponent

# Un peu modifié pour aligner
WIDGET_HEIGHT = 230

class ReverbWidget(SynthComponent):

    def __init__(self):
        super().__init__(widget_height=WIDGET_HEIGHT)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)

        lbl_title = QLabel("REVERB")
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_title.setStyleSheet("color: #eee; font-size: 11px; font-weight: bold; background: transparent;")
        layout.addWidget(lbl_title)

        knobs = QHBoxLayout()
        knobs.setSpacing(10)
        knobs.addStretch()

        self.dial_mix = self._make_knob(knobs, "MIX", 50, 50, 50)
        self.dial_decay = self._make_knob(knobs, "DECAY", 50, 50, 50)
        self.dial_damping = self._make_knob(knobs, "DAMPING", 50, 50, 50)

        # On connecte chaque dial avec la fonction _sync() lorsque leur valeur change
        for dial in (self.dial_mix, self.dial_decay, self.dial_damping):
            dial.valueChanged.connect(self._sync)

        knobs.addStretch()
        layout.addLayout(knobs)

        self._sync()

    def _config(self) -> dict:
        # On retourne un dictionnaire avec les valeurs des dials
        return {
            "reverb_mix": self.dial_mix.value() / 100.0,
            "decay": self.dial_decay.value() / 100.0,
            "damping": self.dial_damping.value() / 100.0,
        }

    def _draw(self) -> None:
        # Il n'y a pas de dessin pour le reverb
        pass