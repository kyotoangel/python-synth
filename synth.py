import numpy as np
from scipy.signal import fftconvolve
from pedalboard import Reverb

class Synth:
    def __init__(self, moteur: "MoteurAudio", waveform: str = "sine"):
        self.moteur = moteur
        self.waveform = waveform
        self.notes_actives = {}

        # enveloppe ADSR
        self.attack = 0.05 # maximum 2 secondes d'attack
        self.decay = 6 # 6 secondes maximum !!!
        self.sustain = 0.8 # valeurs entre 0 et 1
        self.release = 0.05 # maximum 2 secondes

        # filtre
        self.filter_cutoff = 1000  # entre 0 et 1 - fréquence de coupure
        self.filter_prev = 0.0  # mémoire entre buffers
        self.filter_active = True
        self.filter_type = "low_pass"

        self.filter_alpha = 1 - np.exp(-2 * np.pi * self.filter_cutoff / self.moteur.sample_rate)

        # reverb

        self.reverb_mix = 0.5 # de 0% à 100%
        self.room_size = 0.5 #valeur de 0 à 1
        self.damping = 0.0 #valeur de 0 à 1 ?

        self.reverb = Reverb(
            room_size = self.room_size,
            damping = 0.5,
            wet_level = self.reverb_mix,
            dry_level = 1 - self.reverb_mix
        )

    def _note_to_frequency(self, note):
        return self.moteur.tuning*2**((note-69)/12) #formule pour convert midi en fréquence

    def _compute_sine(self, phase):
        return np.sin(2*np.pi*phase)

    def _compute_square(self, phase):
        return np.sign(np.sin(2*np.pi*phase))

    def _compute_saw(self, phase):
        return (phase % 1.0) * 2 - 1

    def _compute_triangle(self, phase):
        return np.abs((phase % 1.0) * 4 - 2) - 1

    def note_on(self, note, velocity=100):
        if note not in self.notes_actives:
            self.notes_actives[note] = {"phase": 0.0,
                                        "adsr_phase": "attack",
                                        "adsr_position": 0.0,
                                        "velocity": velocity / 127.0}

    def note_off(self, note):
        if note in self.notes_actives:
            self.notes_actives[note]["adsr_phase"] = "release"
            self.notes_actives[note]["adsr_position"] = 0.0

    def compute_adsr(self, frames, data): # data étant le dictionnaire de la note
        enveloppe = np.zeros(frames)

        if data["adsr_phase"] == "attack" :

            adsr_position_arrivee = data["adsr_position"] + frames / self.moteur.sample_rate # secondes = buffer_size/freq_echantillonnage

            depart_enveloppe = data["adsr_position"] / self.attack #valeur de l'enveloppe au début du buffer
            arrivee_enveloppe = adsr_position_arrivee / self.attack #valeur de l'enveloppe à la fin du buffer

            enveloppe = np.clip(np.linspace(depart_enveloppe, arrivee_enveloppe, frames), 0.0, 1.0)

            data["adsr_position"] = adsr_position_arrivee

            if arrivee_enveloppe >= 1 :
                data["adsr_phase"] = "decay"
                data["adsr_position"] = 0.0

        elif data["adsr_phase"] == "decay" :

            depart_enveloppe = 1.0 - (data["adsr_position"] / self.decay) * (1.0 - self.sustain)

            adsr_position_arrivee = data["adsr_position"] + frames / self.moteur.sample_rate

            arrivee_enveloppe = 1.0 - (adsr_position_arrivee / self.decay) * (1.0 - self.sustain)

            enveloppe = np.clip(np.linspace(depart_enveloppe, arrivee_enveloppe, frames), 0.0, 1.0)

            data["adsr_position"] = adsr_position_arrivee

            if arrivee_enveloppe <= self.sustain :
                data["adsr_phase"] = "sustain"
                data["adsr_position"] = 0.0

        elif data["adsr_phase"] == "sustain" :
            enveloppe = np.ones(frames) * self.sustain

        elif data["adsr_phase"] == "release" :

            depart_enveloppe = self.sustain * (1-(data["adsr_position"] / self.release))
            adsr_position_arrivee = data["adsr_position"] + frames / self.moteur.sample_rate
            arrivee_enveloppe = self.sustain * (1.0-(adsr_position_arrivee / self.release))

            enveloppe = np.clip(np.linspace(depart_enveloppe, arrivee_enveloppe, frames), 0.0, 1.0)

            data["adsr_position"] = adsr_position_arrivee

            if adsr_position_arrivee >= self.release :
                data["adsr_phase"] = "terminee" # a supprimer - dans le callback
                data["adsr_position"] = 0.0

        return enveloppe

    # filtre

    def apply_filter(self, buffer):
        self.filter_alpha = 1 - np.exp(-2 * np.pi * self.filter_cutoff / self.moteur.sample_rate)
        output = np.zeros(len(buffer))
        if self.filter_type == "low_pass":
            for i in range(len(buffer)):
                self.filter_prev = self.filter_alpha * buffer[i] + (1 - self.filter_alpha) * self.filter_prev
                output[i] = self.filter_prev
        elif self.filter_type == "high_pass":
            for i in range(len(buffer)):
                lp = self.filter_alpha * buffer[i] + (1 - self.filter_alpha) * self.filter_prev
                self.filter_prev = lp
                output[i] = buffer[i] - lp  # HP = signal - LP
        else:
            output = buffer
        return output

    # reverb

    def apply_reverb(self, buffer):

        audio_2d = np.array([buffer])
        processed = self.reverb(audio_2d, self.moteur.sample_rate)

        return processed[0]