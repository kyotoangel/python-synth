import numpy as np
from audio import MoteurAudio

class Synth:
    def __init__(self, moteur: MoteurAudio, waveform: str = "sine"):
        self.moteur = moteur
        self.waveform = waveform
    def _note_to_frequency(self, note):
        return self.moteur.tuning*2**((note-69)/12) #formule pour convert midi en fréquence

    def _compute_sine(self, phase):
        return np.sin(2*np.pi*phase)

    def _compute_rectangle(self, phase):
        return np.sign(np.sin(2*np.pi*phase))

    def _compute_saw(self, phase):
        return (phase % 1.0) * 2 - 1

    def generate_buffer(self):
        buffer = np.zeros(self.moteur.buffer_size)

        if note self.moteur.notes_actives :
            return buffer

        notes_a_traiter = list(self.moteur.notes_actives.items())

        for note, current_phase in notes_a_traiter:
            freq = self._note_to_frequency(note)
            delta_phi = freq / self.moteur.sample_rate

            # on créé le vecteur de phase pour ce bloc
            phase = current_phase + np.arange(self.moteur.buffer_size) * delta_phi

            if self.waveform == "sine":
                wave = self._compute_sine(phase)
            elif self.waveform == "square":
                wave = self._compute_rectangle(phase)
            elif self.waveform == "saw":
                wave = self._compute_saw(phase)
            else :
                wave = self._compute_sine(phase)

            buffer += wave

            # sauvegarde de la phase pour le prochain buffer
            self.moteur.notes_actives[note] = (phases[-1] + delta_phi) % 1.0

        # gain et normalisation
        nb_notes = len(self.moteur.notes_actives)
        return buffer * (self.moteur.get_gain() / max(nb_notes, 1))