import numpy as np
from PyQt6.QtWidgets import QHBoxLayout, QSlider
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QPainter, QPen, QPainterPath, QLinearGradient, QColor, QPixmap
from PyQt6.QtCore import QPointF

from components.base_component import SynthComponent

WIDGET_HEIGHT = 250
SCREEN_HEIGHT = 160

class ReverbWidget(SynthComponent):

    config_updated = pyqtSignal(dict)

    def __init__(self):
        super().__init__(widget_height=WIDGET_HEIGHT, screen_height=SCREEN_HEIGHT)
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)

        knobs = QHBoxLayout()
        knobs.setSpacing(10)
        knobs.addStretch()

        self.dial_mix = self._make_dial(knobs, "MIX",  20, 50, 50)
        self.dial_decay = self._make_dial(knobs, "DECAY",   30, 50, 50)
        self.dial_damping = self._make_dial(knobs, "DAMPING", 70, 50, 50)

        for dial in (self.dial_mix, self.dial_decay, self.dial_damping):
            dial.valueChanged.connect(self._sync)

        knobs.addStretch()
        layout.addLayout(knobs)

        self._sync()

    def _sync(self):
        super()._sync()

    def _config(self) -> dict:
        return {
            "reverb_mix": self.dial_mix.value() / 100.0,
            "decay": self.dial_decay.value() / 100.0,
            "damping": self.dial_damping.value() / 100.0,
        }

    def _draw(self):
        pass