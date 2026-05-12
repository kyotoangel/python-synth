import numpy as np
import sounddevice as sd

class MoteurAudio:
    def __init__(self, sample_rate: int = 44100, volume: float = -18.0, tuning: int = 440, buffer_size = 256) -> None:
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
        gain_samples = samples * 10**(self.volume/20) #corrige avec le volume (dB deviennent linéaires)
        sd.play(gain_samples, self.sample_rate)

    def start(self, synth):
        self.synth = synth
        self.stream = sd.OutputStream(samplerate=self.sample_rate, channels=1, callback=self.callback, blocksize=self.buffer_size, dtype='float32')
        self.stream.start()

    def stop(self):
        """
        Stops the sound
        """
        sd.stop()

    def get_gain(self):
        return 10 ** (self.volume / 20)

    def callback(self, outdata, frames, time, status):
        buffer = np.zeros(frames)

        for note, data in self.synth.notes_actives.items():
            frequence = self.synth._note_to_frequency(note)
            phase = data["phase"]

            phases = phase + np.arange(frames) * frequence / self.sample_rate
            buffer += np.sin(2 * np.pi * phases)

            data["phase"] = phases[-1] % 1.0

        outdata[:, 0] = buffer * self.get_gain()