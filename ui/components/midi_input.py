import mido
from PyQt6.QtCore import QThread, pyqtSignal

class MidiInput(QThread):
    """
    Écoute un port MIDI externe et permet d'envoyer les notes sur les signaux note_on et note_off.
    """
    note_on  = pyqtSignal(int)
    note_off = pyqtSignal(int)

    def __init__(self, port_name: str):
        super().__init__()
        self._port_name = port_name
        self._stopped   = False

    def stop(self):
        self._stopped = True

    def run(self):
        with mido.open_input(self._port_name) as port:
            for message in port:
                if self._stopped:
                    break
                if message.type == "note_on" and message.velocity > 0:
                    self.note_on.emit(message.note)
                elif message.type == "note_off" or (message.type == "note_on" and message.velocity == 0):
                    self.note_off.emit(message.note)

    @staticmethod
    def list_ports() -> list[str]:
        # Retourne la liste des ports MIDI disponibles
        return mido.get_input_names()