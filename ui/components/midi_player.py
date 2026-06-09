import mido
from PyQt6.QtCore import QThread, pyqtSignal

class MidiPlayer(QThread):
    """
    Lit un fichier MIDI et permet d'envoyer les notes sur les signaux note_on et note_off.
    """
    note_on = pyqtSignal(int)
    note_off = pyqtSignal(int)
    finished = pyqtSignal()

    def __init__(self, path: str):
        super().__init__()
        self._path = path
        self._stopped = False

    def stop(self):
        self._stopped = True

    def run(self):
        mid = mido.MidiFile(self._path)
        for message in mid.play():
            if self._stopped:
                break
            if message.type == "note_on" and message.velocity > 0:
                self.note_on.emit(message.note)
            elif message.type == "note_off" or (message.type == "note_on" and message.velocity == 0):
                self.note_off.emit(message.note)
        self.finished.emit()