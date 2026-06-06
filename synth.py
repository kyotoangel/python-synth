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
        """
        Convertit une note (information midi) en fréquence
        """
        return self.moteur.tuning*2**((note-69)/12) #formule pour convert midi en fréquence

    # ---- Oscillateurs

    def _compute_sine(self, phase):
        """
        Prend en entrée les données de l'accumulateur de phase et retourne une sinusoidale
        (fait office d'oscillateur sinusoidal)
        """
        return np.sin(2*np.pi*phase)

    def _compute_square(self, phase):
        """
        Prend en entrée les données de l'accumulateur de phase et retourne un carré
        (fait office d'oscillateur carré)
        """
        return np.sign(np.sin(2*np.pi*phase))

    def _compute_saw(self, phase):
        """
        Prend en entrée les données de l'accumulateur de phase et retourne une dent de scie
        (fait office d'oscillateur dent de scie)
        """
        return (phase % 1.0) * 2 - 1

    def _compute_triangle(self, phase):
        """
        Prend en entrée les données de l'accumulateur de phase et retourne un triangle
        (fait office d'oscillateur triangle)
        """
        return np.abs((phase % 1.0) * 4 - 2) - 1

    def note_on(self, note, velocity=100):
        """
        Ajoute une note (argument) au dictionnaire des notes actives
        """
        if note not in self.notes_actives:
            self.notes_actives[note] = {"phase": 0.0,
                                        "adsr_phase": "attack",
                                        "adsr_position": 0.0,
                                        "velocity": velocity / 127.0}

    def note_off(self, note):
        """
        Enlève une note (prise en argument) du dictionnaire des notes actives
        """
        if note in self.notes_actives:
            self.notes_actives[note]["adsr_phase"] = "release"
            self.notes_actives[note]["adsr_position"] = 0.0

    def compute_adsr(self, frames, data): # data étant le dictionnaire de la note
        """
        Calcule et génère l'enveloppe ADSR sur la durée d'un buffer complet
        en utilisant une interpolation linéaire
        arguments :
        frames (int) -> nombre d'échantillons du buffer audio
        data (dictionnaire) -> dictionnaire contenant l'état actuel des notes jouées :
                                "adsr_phase" : phase actuelle de la note (attack ou decay ou sustain...)
                                "adsr_position" : la position de la note dans la phase actuelle

        retourne un tableau 1D contenant l'amplitude associée à chaque échantillon du buffer
        """
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
        """
        Prend en entrée un buffer et applique un filtre sur celui-ci
        (Passe-Bas ou Pass-Haut, selon le type défini)
        La fréquence de coupure, le type de filtre ne sont pas pris en argument,
        car ce sont des attributs de la classe "synth"

        Le filtre est la version la plus simple des filtres "IIR" (Infinite Impulse Response)
        Il est fait à partir de l'équation aux différences d'un passe-bas/passe-haut du 1er ordre.

        Retourne le buffer "filtré"
        """
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
        """
        Prend en entrée le buffer audio et applique une réverberation sur celui-ci
        (utilisant la bibliothèque pedalboard, de spotify)
        Retourne le buffer après application de la reverberation
        """
        # actualisation des valeurs renvoyées par l'ui d'antoine
        self.reverb.wet_level = self.reverb_mix
        self.reverb.dry_level = 1.0 - self.reverb_mix

        audio_2d = np.array([buffer])

        processed = self.reverb(audio_2d, self.moteur.sample_rate, reset=False)

        return processed[0]