import numpy as np
import sounddevice as sd


class MoteurAudio:
    def __init__(self, sample_rate: int = 44100, volume: float = -6.0, tuning: int = 440, buffer_size=256) -> None:
        self.sample_rate = sample_rate
        self.buffer_size = buffer_size
        self.volume = volume
        self.tuning = tuning
        self.stream = None

    def play(self, samples: np.ndarray):
        """
        Allows the speakers to make the sound ! 
        (takes a numpy array in argument, describing the waveform)
        """
        gain_samples = samples * 10 ** (self.volume / 20)  # corrige avec le volume (dB deviennent linéaires)
        sd.play(gain_samples, self.sample_rate)

    def start(self, synth):
        self.synth = synth
        self.stream = sd.OutputStream(samplerate=self.sample_rate, channels=1, callback=self.callback,
                                      blocksize=self.buffer_size, dtype='float32')
        self.stream.start()

    def stop(self):
        """
        Stops the sound
        """
        sd.stop()

    def get_gain(self):
        return 10 ** (self.volume / 20)

    def callback(self, outdata, frames, time, status):
        # 1. Créer un buffer vide (silence)
        # 2. Pour chaque note dans synth.notes_actives :
        #    - générer les samples avec la phase courante
        #    - les additionner au buffer
        #    - mettre à jour la phase
        # 3. Remplir outdata avec le buffer
        pass