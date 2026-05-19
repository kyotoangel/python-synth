import sys
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *

from audio import MoteurAudio
from components.osc_widget import VitalOsc
from components.envelope_widget import EnvelopeWidget
from components.lfo_widget import LfoWidget
from components.filter_widget import FilterWidget
from synth import Synth
import math


def linear_to_db(value):
    # Handle the -inf case (silence)
    if value <= 0:
        return float('-inf')

    # Standard formula with your -18dB ceiling
    db = 20 * math.log10(value) - 18
    return db


class MainWindow(QMainWindow):
    """
    Fenêtre principale qui assemble tous les composants
    comme dans l'interface de Vital.
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("PySynth")
        self.setStyleSheet("background: #070809;")

        self.moteur = MoteurAudio()
        self.synth = Synth(self.moteur)

        self.synth.note_on(60)  # Do4

        self.moteur.start(self.synth)

        central = QWidget()
        self.setCentralWidget(central)

        # Layout principal : colonne gauche (OSC) | colonne droite (ENV + LFO)
        root = QHBoxLayout(central)
        root.setSpacing(4)
        root.setContentsMargins(8, 8, 8, 8)

        # --- Colonne gauche  ---
        osc_col = QVBoxLayout()
        osc_col.setSpacing(2)

        self.osc = VitalOsc()

        # On écoute les changements de chaque oscillateur
        self.osc.config_updated.connect(lambda cfg: self._on_osc_change(1, cfg))

        osc_col.addWidget(self.osc)
        osc_col.addStretch()

        self.filter = FilterWidget()

        osc_col.addWidget(self.filter)

        # --- Colonne droite ---
        right_col = QVBoxLayout()
        right_col.setSpacing(4)

        self.env = EnvelopeWidget()
        self.lfo = LfoWidget()

        right_col.addWidget(self.env)
        right_col.addWidget(self.lfo)

        # Assemblage final
        root.addLayout(osc_col)
        root.addLayout(right_col)

    def _on_osc_change(self, osc_number, config):
        """
        Appelée quand un oscillateur change.
        Pour l'instant on affiche juste dans le terminal —
        plus tard ça enverra les données au moteur audio.
        """
        print(f"OSC {osc_number} → {config}")

        self.synth.waveform = config["waveform"]


        self.moteur.volume = linear_to_db(config["level"])


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())