import numpy as np
import sounddevice as sd

class MoteurAudio:
    def __init__(self, sample_rate: int = 44100, volume: float = -25.0, tuning: int = 440, buffer_size = 256) -> None:
        self.sample_rate = sample_rate
        self.buffer_size = buffer_size
        self.volume = volume
        self.tuning = tuning
        self.stream = None
        
    def play(self, samples: np.ndarray):
        """
        Prend en entrée des samples (buffer audio) et les joue (au volume correspondant à l'attribut "volume")
        """
        gain_samples = samples * 10**(self.volume/20) #corrige avec le volume (dB deviennent linéaires)
        sd.play(gain_samples, self.sample_rate)

    def start(self, synth):
        """
        Démarre le moteur audio et connecte le synthetiseur (classe synth)

        Créé un flux de sortie audio (connecte Python à la carte son),
        et enregistre le callback qui sera appelé en boucle par sounddevice pour générer les samples en temps réel.

        synth: instance du synthétiseur, utilisée par le callback pour accéder aux notes actives et formes d'ondes
        """
        self.synth = synth
        self.stream = sd.OutputStream(samplerate=self.sample_rate, channels=1, callback=self.callback, blocksize=self.buffer_size, dtype='float32')
        self.stream.start()

    def stop(self):
        """
        Arrête le moteur audio (coupe le flux audio)
        """
        sd.stop()

    def get_gain(self):
        """
        Retourne la valeur du volume du moteur audio
        (convertit les dB (-infini à 0dB) -> (0 à 1))
        Cette conversion est obligatoire pour appliquer le volume à un tableau de samples
        """
        return 10 ** (self.volume / 20)

    def callback(self, outdata, frames, time, status):
        """
        Callback audio appelé automatiquement par sounddevice toutes les
        buffer_size / sample_rate secondes (~5ms pour 256 samples à 44,1 kHz).

        Pour chaque note active, génère les samples de la waveform courante
        en utilisant l'accumulateur de phase, applique l'enveloppe ADSR,
        et additionne le résultat dans le buffer de sortie.
        Une fois toutes les notes traitées, applique le filtre et la reverb,
        puis envoie le buffer à la carte son via outdata.
        Les notes dont l'enveloppe est terminée (fin de l'étape release pour l'enveloppe ADSR), sont supprimées après l'itération.

        Arguments:
            outdata (np.ndarray): buffer de sortie sounddevice, forme (frames, channels).
                                  (remplit avec les samples à envoyer à la carte son).
            frames (int): nombre de samples demandés par sounddevice (= buffer_size).
            time: timestamp sounddevice, non utilisé.
            status: informations de débogage sounddevice, non utilisé.
        """
        buffer = np.zeros(frames)
        notes_a_supprimer = []

        for note, data in list(self.synth.notes_actives.items()):
            frequence = self.synth._note_to_frequency(note)
            phase = data["phase"]

            phases = phase + np.arange(frames) * frequence / self.sample_rate

            if self.synth.waveform == "sine" :
                buffer += self.synth._compute_sine(phases) * self.synth.compute_adsr(frames, self.synth.notes_actives[note])
            elif self.synth.waveform == "saw":
                buffer += self.synth._compute_saw(phases) * self.synth.compute_adsr(frames, self.synth.notes_actives[note])
            elif self.synth.waveform == "square":
                buffer += self.synth._compute_square(phases) * self.synth.compute_adsr(frames, self.synth.notes_actives[note])
            elif self.synth.waveform == "triangle":
                buffer += self.synth._compute_triangle(phases) * self.synth.compute_adsr(frames, self.synth.notes_actives[note])

            data["phase"] = phases[-1] % 1.0

            if data["adsr_phase"] == "terminee":
                notes_a_supprimer.append(note)

        for note in notes_a_supprimer:
            del self.synth.notes_actives[note]

        # application du filtre
        buffer = self.synth.apply_filter(buffer)
        buffer = self.synth.apply_reverb(buffer)

        outdata[:, 0] = buffer * self.get_gain() #[:,0] car on est en mono