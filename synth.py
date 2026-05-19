import numpy as np
from audio import MoteurAudio

class Synth:
    def __init__(self, moteur: MoteurAudio, waveform: str = "sine"):
        self.moteur = moteur
        self.waveform = waveform
        self.notes_actives = {}
        self.attack = 0.05 # maximum 2 secondes d'attack
        self.decay = 6 # 6 secondes maximum !!!
        self.sustain = 0.8 # valeurs entre 0 et 1
        self.release = 0.05 # maximum 2 secondes

    def _note_to_frequency(self, note):
        return self.moteur.tuning*2**((note-69)/12) #formule pour convert midi en fréquence

    def _compute_sine(self, phase):
        return np.sin(2*np.pi*phase)

    def _compute_square(self, phase):
        return np.sign(np.sin(2*np.pi*phase))

    def _compute_saw(self, phase):
        return (phase % 1.0) * 2 - 1

    def note_on(self, note):
        if note not in self.notes_actives:
            self.notes_actives[note] = {"phase" : 0.0,
                                        "adsr_phase" : "attack", #état de l'enveloppe
                                        "adsr_position" : 0.0} # position en seconde dans l'état

    def note_off(self, note):
        if note in self.notes_actives:
            del self.notes_actives[note] #on retire la note

    def compute_adsr(self, frames, data): # data étant le dictionnaire de la note
        enveloppe = np.zeros(frames)

        return enveloppe