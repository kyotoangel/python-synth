import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFileDialog, QMessageBox, QInputDialog)
from PyQt6.QtCore import Qt
from audio import MoteurAudio
from components.osc_widget import OscWidget
from components.envelope_widget import EnvelopeWidget
from components.reverb_widget import ReverbWidget
from components.filter_widget import FilterWidget
from synth import Synth
from components.piano_widget import PianoWidget, WHITE_H
from components.midi_player import MidiPlayer
from components.midi_input import MidiInput
from utils import linear_to_db, interpoler

STYLE_BTN: str = """
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

class MainWindow(QMainWindow):
    """
    Fenêtre principale de l'application.
    Elle embarque les quatre composants principaux : Oscillateur, Enveloppe, Filtre et Reverb.
    Elle ajoute aussi le piano MIDI en bas en ajoutant un bouton de chaque côté de ce dernier pour ouvrir un fichier MIDI et un input MIDI.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ShurimaSynth - Le synthétiseur le plus cool de la planète !")
        self.setStyleSheet("background: #070809;")

        # On instancie le moteur audio du synthétiseur que l'on démarre.
        self.moteur = MoteurAudio()
        self.synth = Synth(self.moteur)
        self.moteur.start(self.synth)

        self._midi_player = None
        self._midi_input = None

        central = QWidget()
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setSpacing(4)
        root.setContentsMargins(8, 8, 8, 8)

        main_row = QHBoxLayout()
        main_row.setSpacing(4)

        # Colonne gauche.
        left_col = QVBoxLayout()
        left_col.setSpacing(2)

        # On instancie les composants OscWidget et FilterWidget dans la colonne gauche.
        self.osc = OscWidget()
        # On relie le signal config_updated à la fonction _on_osc_change.
        self.osc.config_updated.connect(self._on_osc_change)

        self.filter = FilterWidget()
        # On relie le signal config_updated à la fonction _on_filter_change.
        self.filter.config_updated.connect(self._on_filter_change)

        left_col.addWidget(self.osc)
        left_col.addWidget(self.filter)

        # Colonne droite.
        right_col = QVBoxLayout()
        right_col.setSpacing(4)

        # On instancie les composants EnvelopeWidget et ReverbWidget dans la colonne droite.
        self.env = EnvelopeWidget()
        # On relie le signal config_updated à la fonction _on_env_change.
        self.env.config_updated.connect(self._on_env_change)

        self.reverb = ReverbWidget()
        # On relie le signal config_updated à la fonction _on_reverb_change.
        self.reverb.config_updated.connect(self._on_reverb_change)

        right_col.addWidget(self.env)
        right_col.addWidget(self.reverb)

        main_row.addLayout(left_col)
        main_row.addLayout(right_col)

        piano_row = QHBoxLayout()
        piano_row.setSpacing(8)
        piano_row.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        # On instancie le composant Piano ainsi que les boutons pour ouvrir un fichier MIDI et un input MIDI.
        self.piano = PianoWidget()
        self.piano.note_on.connect(self._on_note_on)
        self.piano.note_off.connect(self._on_note_off)

        self.btn_midi = QPushButton("▶  Open MIDI")
        self.btn_midi.setFixedSize(90, WHITE_H)
        self.btn_midi.setStyleSheet(STYLE_BTN)
        # On connecte le click à la fonction _open_midi.
        self.btn_midi.clicked.connect(self._open_midi)

        self.btn_midi_in = QPushButton("🎹  MIDI IN")
        self.btn_midi_in.setFixedSize(90, WHITE_H)
        self.btn_midi_in.setStyleSheet(STYLE_BTN)
        # On connecte le click à la fonction _open_midi_in.
        self.btn_midi_in.clicked.connect(self._open_midi_in)
        piano_row.addWidget(self.btn_midi_in)

        piano_row.addWidget(self.piano)
        piano_row.addWidget(self.btn_midi)

        root.addLayout(main_row)
        root.addLayout(piano_row)

    def _open_midi(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Ouvrir un fichier MIDI", "", "MIDI (*.mid *.midi)")
        if not path:
            return

        # S'il y a déjà un fichier MIDI en cours, on le stoppe.
        if self._midi_player is not None:
            self._midi_player.stop()
            self._midi_player.wait()
            self.piano.release_all()

        # On instancie un nouveau MidiPlayer qui va jouer le fichier MIDI.
        self._midi_player = MidiPlayer(path)
        self._midi_player.note_on.connect(self._on_midi_note_on)
        self._midi_player.note_off.connect(self._on_midi_note_off)
        self._midi_player.finished.connect(self._on_midi_finished)
        self._midi_player.start()

        # On change le texte du bouton pour indiquer qu'on est en train de jouer le fichier MIDI.
        self.btn_midi.setText("■  Stop")
        self.btn_midi.clicked.disconnect()
        self.btn_midi.clicked.connect(self._stop_midi)

    def _stop_midi(self) -> None:
        # On stoppe le player MIDI et on reset le bouton.
        if self._midi_player:
            self._midi_player.stop()
            self._midi_player.wait()
            self._release_all_notes()
            self._midi_player = None
        self._reset_btn()

    def _on_midi_finished(self) -> None:
        # On relâche toutes les touches du piano MIDI et on reset le bouton quand le fichier est terminé.
        self.piano.release_all()
        self._midi_player = None
        self._reset_btn()

    def _reset_btn(self) -> None:
        # On remet le bouton dans son état initial.
        self.btn_midi.setText("▶  Open MIDI")
        self.btn_midi.clicked.disconnect()
        self.btn_midi.clicked.connect(self._open_midi)

    def _on_midi_note_on(self, midi: int) -> None:
        # On presse la touche MIDI et on joue la note sur le synth.
        self.piano.press_note(midi)
        self.synth.note_on(midi)

    def _on_midi_note_off(self, midi: int) -> None:
        # On retire la note MIDI et on arrête de jouer la note sur le synth.
        self.piano.release_note(midi)
        self.synth.note_off(midi)

    def _release_all_notes(self) -> None:
        # On désactive toutes les notes MIDI sur le synth et sur le piano MIDI.
        for midi in self.piano.pressed_notes():
            self.synth.note_off(midi)
        self.piano.release_all()

    def _on_note_on(self, midi: int) -> None:
        # On joue la note sur le synth lorsqu'on clique sur la touche du piano.
        self.synth.note_on(midi)

    def _on_note_off(self, midi: int) -> None:
        # On arrête de jouer la note sur le synth lorsque l'on relâche la touche.
        self.synth.note_off(midi)

    def _open_midi_in(self) -> None:
        # On récupère la liste des ports MIDI disponibles.
        ports = MidiInput.list_ports()
        if not ports:
            QMessageBox.warning(self, "MIDI IN", "Aucun port MIDI détecté.")
            return

        # Si un seul port disponible, on le sélectionne automatiquement.
        if len(ports) == 1:
            port = ports[0]
        else:
            port, ok = QInputDialog.getItem(self, "MIDI IN", "Choisir un port MIDI :", ports, 0, False)
            if not ok:
                return

        # Si un input MIDI est déjà en cours, on le stoppe.
        if self._midi_input is not None:
            self._midi_input.stop()
            self._midi_input.wait()

        # On instancie un nouveau MidiInput qui va récupérer les notes envoyées depuis le port MIDI
        self._midi_input = MidiInput(port)
        self._midi_input.note_on.connect(self._on_midi_note_on)
        self._midi_input.note_off.connect(self._on_midi_note_off)
        self._midi_input.start()

        self.btn_midi_in.setText("■  Disconnect")
        self.btn_midi_in.clicked.disconnect()
        self.btn_midi_in.clicked.connect(self._close_midi_in)

    def _close_midi_in(self) -> None:
        # On stoppe l'input MIDI et on reset le bouton.
        if self._midi_input:
            self._midi_input.stop()
            self._midi_input.wait()
            self._midi_input = None
        self._release_all_notes()
        self.btn_midi_in.setText("🎹  MIDI IN")
        self.btn_midi_in.clicked.disconnect()
        self.btn_midi_in.clicked.connect(self._open_midi_in)

    def _on_osc_change(self, config: dict) -> None:
        # Lorsque le composant oscillateur est mis à jour, on change la configuration du MoteurAudio en ajustant le volume et le tuning.
        self.synth.waveform = config["waveform"]

        self.moteur.volume = linear_to_db(config["level"])
        self.moteur.tuning = config["tuning"]

    def _on_env_change(self, config: dict) -> None:
        # Lorsque le composant enveloppe est mis à jour, on change la configuration du Synth en ajustant les valeurs de ce dernier.
        self.synth.attack = interpoler(config["attack"], 0.05, 0.5)
        self.synth.decay = interpoler(config["decay"], 0.05, 6)
        self.synth.sustain = interpoler(config["sustain"], 0.05, 1)
        self.synth.release = interpoler(config["release"], 0.05, 2)

    def _on_filter_change(self, config: dict) -> None:
        # Lorsque le composant filtre est mis à jour, on change la configuration du Synth en ajustant le cutoff et le type de filtre.
        self.synth.filter_cutoff = config["cutoff"]
        self.synth.filter_type = config["filter_type"]

    def _on_reverb_change(self, config: dict) -> None:
        # Lorsque le composant reverb est mis à jour, on change la configuration du Synth en ajustant les valeurs de ce dernier.
        self.synth.reverb_mix = config["reverb_mix"]
        self.synth.room_size = interpoler(config["decay"], 0, 1)
        self.synth.damping = config["damping"]

    def closeEvent(self, event):
        # Événement de fermeture de la fenêtre : on arrête tout.
        if self._midi_player:
            self._midi_player.stop()
            self._midi_player.wait()
        if self._midi_input:
            self._midi_input.stop()
            self._midi_input.wait()
        self.moteur.stop()
        super().closeEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())