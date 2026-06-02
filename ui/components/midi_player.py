import mido
from PyQt6.QtCore import QThread, pyqtSignal


class MidiPlayer(QThread):
    """
    Lit un fichier MIDI dans un thread séparé.
    Émet note_on(midi, velocity) et note_off(midi) avec le bon timing.
    """
    note_on  = pyqtSignal(int, int)   # midi, velocity
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
        for msg in mid.play():
            if self._stopped:
                break
            if msg.type == "note_on" and msg.velocity > 0:
                self.note_on.emit(msg.note, msg.velocity)
            elif msg.type == "note_off" or (msg.type == "note_on" and msg.velocity == 0):
                self.note_off.emit(msg.note)
        self.finished.emit()