import numpy as np
import sounddevice as sd

from synth import Synth


class MoteurAudio:
    def __init__(self, sample_rate: int = 44100, volume: float = -25.0, tuning: int = 440, buffer_size = 256) -> None:
        self.sample_rate = sample_rate
        self.buffer_size = buffer_size
        self.volume = volume
        self.tuning = tuning
        self.stream = None
        
    def play(self, samples: np.ndarray):
        gain_samples = samples * 10**(self.volume/20) #corrige avec le volume (dB deviennent linéaires)
        sd.play(gain_samples, self.sample_rate)

    def start(self, synth):
        self.synth = synth
        self.stream = sd.OutputStream(samplerate=self.sample_rate, channels=1, callback=self.callback, blocksize=self.buffer_size, dtype='float32')
        self.stream.start()

    def stop(self):
        sd.stop()

    def get_gain(self):
        return 10 ** (self.volume / 20)

    def callback(self, outdata, frames, time, status):
        buffer = np.zeros(frames)
        notes_a_supprimer = []

        for note, data in list(self.synth.notes_actives.items()):
            frequence = self.synth._note_to_frequency(note)
            phase = data["phase"]

            phases = phase + np.arange(frames) * frequence / self.sample_rate

            if self.synth.waveform == "sine" :
                vel = data["velocity"]
                buffer += self.synth._compute_sine(phases) * self.synth.compute_adsr(frames, self.synth.notes_actives[note]) #* vel
            elif self.synth.waveform == "saw":
                vel = data["velocity"]
                buffer += self.synth._compute_saw(phases) * self.synth.compute_adsr(frames, self.synth.notes_actives[note]) #* vel
            elif self.synth.waveform == "square":
                vel = data["velocity"]
                buffer += self.synth._compute_square(phases) * self.synth.compute_adsr(frames, self.synth.notes_actives[note]) #* vel
            elif self.synth.waveform == "triangle":
                buffer += self.synth._compute_triangle(phases) * self.synth.compute_adsr(frames, self.synth.notes_actives[note]) #* vel

            data["phase"] = phases[-1] % 1.0

            if data["adsr_phase"] == "terminee":
                notes_a_supprimer.append(note)

        for note in notes_a_supprimer:
            del self.synth.notes_actives[note]

        # application du filtre
        buffer = self.synth.apply_filter(buffer)
        buffer = self.synth.apply_reverb(buffer)

        outdata[:, 0] = buffer * self.get_gain()