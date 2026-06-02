import sys
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *

from audio import MoteurAudio
from components.osc_widget import VitalOsc
from components.envelope_widget import EnvelopeWidget
from components.reverb_widget import ReverbWidget
from components.filter_widget import FilterWidget
from synth import Synth
import math

from components.piano_widget import PianoWidget, WHITE_H
from components.midi_player import MidiPlayer

STYLE_BTN = """
    QPushButton {
        color: #aaa;
        background: #1a1a1a;
        border: 1px solid #333;
        border-radius: 4px;
        padding: 4px 10px;
        font-size: 11px;
    }
    QPushButton:hover  { color: white; border-color: #555; }
    QPushButton:pressed { background: #111; }
"""


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
        self.setWindowTitle("Synthétiseur Python Trop Cool")
        self.setStyleSheet("background: #070809;")

        self.moteur = MoteurAudio()
        self.synth = Synth(self.moteur)
        self.moteur.start(self.synth)

        self._midi_player = None

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
        self.osc.config_updated.connect(lambda cfg: self._on_osc_change(cfg))
        osc_col.addWidget(self.osc)
        osc_col.addStretch()

        self.filter = FilterWidget()
        self.synth._filter_widget = self.filter
        self.filter.config_updated.connect(lambda cfg: self._on_filter_change(cfg))
        osc_col.addWidget(self.filter)

        # Colonne droite
        right_col = QVBoxLayout()
        right_col.setSpacing(4)

        self.env = EnvelopeWidget()
        self.env.config_updated.connect(lambda cfg: self._on_env_change( cfg))
        self.reverb = ReverbWidget()
        right_col.addWidget(self.env)
        right_col.addWidget(self.reverb)

        top_row.addLayout(osc_col)
        top_row.addLayout(right_col)

        # ── Rangée piano + bouton ──
        piano_row = QHBoxLayout()
        piano_row.setSpacing(8)
        piano_row.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        self.piano = PianoWidget()
        self.piano.note_on.connect(self._on_note_on)
        self.piano.note_off.connect(self._on_note_off)

        self.btn_midi = QPushButton("▶  Open MIDI")
        self.btn_midi.setFixedHeight(WHITE_H + 16 if True else 0)  # même hauteur que le piano
        self.btn_midi.setStyleSheet(STYLE_BTN)
        self.btn_midi.clicked.connect(self._open_midi)

        self.btn_midi.setFixedSize(90, WHITE_H + 16)

        piano_row.addWidget(self.piano)
        piano_row.addWidget(self.btn_midi)

        root.addLayout(top_row)
        root.addLayout(piano_row)

    # ── MIDI file ─────────────────────────────────────────────
    def _open_midi(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Ouvrir un fichier MIDI", "", "MIDI (*.mid *.midi)"
        )
        if not path:
            return

        # Arrête un éventuel player déjà en cours
        if self._midi_player is not None:
            self._midi_player.stop()
            self._midi_player.wait()
            self.piano.release_all()

        self._midi_player = MidiPlayer(path)
        self._midi_player.note_on.connect(self._on_midi_note_on)
        self._midi_player.note_off.connect(self._on_midi_note_off)
        self._midi_player.finished.connect(self._on_midi_finished)
        self._midi_player.start()

        self.btn_midi.setText("■  Stop")
        self.btn_midi.clicked.disconnect()
        self.btn_midi.clicked.connect(self._stop_midi)

    def _stop_midi(self):
        if self._midi_player:
            self._midi_player.stop()
            self._midi_player.wait()
            self._release_all_notes()
            self._midi_player = None
        self._reset_btn()

    def _on_midi_finished(self):
        self.piano.release_all()
        self._midi_player = None
        self._reset_btn()

    def _reset_btn(self):
        self.btn_midi.setText("▶  Open MIDI")
        self.btn_midi.clicked.disconnect()
        self.btn_midi.clicked.connect(self._open_midi)

    def _on_midi_note_on(self, midi, velocity):
        self.piano.press_note(midi)
        self.synth.note_on(midi, velocity)

    def _on_midi_note_off(self, midi):
        self.piano.release_note(midi)
        self.synth.note_off(midi)

    def _release_all_notes(self):
        for midi in range(128):
            self.synth.note_off(midi)
        self.piano.release_all()

    def _on_osc_change(self, config):
        """
        Appelée quand un oscillateur change.
        """
        self.synth.waveform = config["waveform"]

        self.moteur.volume = linear_to_db(config["level"])
        self.moteur.tuning = config["tuning"]

    def _on_env_change(self, config):
        self.synth.attack = interpoler(config["attack"], 0.05, 2)
        self.synth.decay = interpoler(config["decay"], 0, 6)
        self.synth.sustain = interpoler(config["sustain"], 0, 1)
        self.synth.release = interpoler(config["release"], 0.05, 2)
        print(self.synth.attack, self.synth.decay, self.synth.sustain, self.synth.release)

    def _on_filter_change(self, config):
        self.synth.filter_cutoff = config["cutoff"]
        self.synth.filter_type = config["filter_type"]
        self.synth.filter_active = config["active"]

    def _on_note_on(self, midi):
        self.synth.note_on(midi)

    def _on_note_off(self, midi):
        self.synth.note_off(midi)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())