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

from components.piano_widget import PianoWidget


def linear_to_db(value):
    # Handle the -inf case (silence)
    if value <= 0:
        return float('-inf')

    # Standard formula with your -18dB ceiling
    db = 20 * math.log10(value) - 18
    return db


def interpoler(valeur, min_cible, max_cible):
    """
    Transforme une valeur comprise entre 0 et 1
    en une valeur comprise entre min_cible et max_cible.
    """
    return min_cible + (valeur * (max_cible - min_cible))


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
        self.moteur.start(self.synth)

        central = QWidget()
        self.setCentralWidget(central)

        # Layout racine : tout en colonne
        root = QVBoxLayout(central)
        root.setSpacing(4)
        root.setContentsMargins(8, 8, 8, 8)

        # ── Rangée du haut : OSC | ENV+LFO ──
        top_row = QHBoxLayout()
        top_row.setSpacing(4)

        # Colonne gauche
        osc_col = QVBoxLayout()
        osc_col.setSpacing(2)

        self.osc = VitalOsc()
        self.osc.config_updated.connect(lambda cfg: self._on_osc_change(1, cfg))
        osc_col.addWidget(self.osc)
        osc_col.addStretch()

        self.filter = FilterWidget()
        osc_col.addWidget(self.filter)

        # Colonne droite
        right_col = QVBoxLayout()
        right_col.setSpacing(4)

        self.env = EnvelopeWidget()
        self.lfo = LfoWidget()
        right_col.addWidget(self.env)
        right_col.addWidget(self.lfo)

        top_row.addLayout(osc_col)
        top_row.addLayout(right_col)

        # ── Piano en bas ──
        self.piano = PianoWidget()
        self.piano.note_on.connect(self._on_note_on)
        self.piano.note_off.connect(self._on_note_off)

        root.addLayout(top_row)
        root.addWidget(self.piano, alignment=Qt.AlignmentFlag.AlignHCenter)

    def _on_osc_change(self, osc_number, config):
        """
        Appelée quand un oscillateur change.
        Pour l'instant on affiche juste dans le terminal —
        plus tard ça enverra les données au moteur audio.
        """
        self.synth.waveform = config["waveform"]


        self.moteur.volume = linear_to_db(config["level"])

    def _on_env_change(self, env_number, config):
        self.synth.attack = interpoler(config["attack"], 0.05, 2)
        self.synth.decay = interpoler(config["decay"], 0, 6)
        self.synth.sustain = interpoler(config["sustain"], 0, 1)
        self.synth.release = interpoler(config["release"], 0.05, 2)

        print(self.synth)

    def _on_note_on(self, midi):
        print(f"note_on  {midi}")
        self.synth.note_on(midi)

    def _on_note_off(self, midi):
        print(f"note_off {midi}")
        self.synth.note_off(midi)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())