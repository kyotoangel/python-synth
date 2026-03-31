import numpy as np
import sounddevice as sd

class MoteurAudio:
    def __init__(self, sample_rate: int = 44100, volume: float = -6.0, tuning: int = 440, buffer_size = 256) -> None:
        self.sample_rate = sample_rate
        self.buffer_size = buffer_size
        self.volume = volume
        self.tuning = tuning
        self.notes_actives = {}
        
    def play(self, samples: np.ndarray):
        """
        Allows the speakers to make the sound ! 
        (takes a numpy array in argument, describing the waveform)
        """
        gain_samples = samples * 10**(self.volume/20) #corrige avec le volume (dB deviennent linéaires)
        sd.play(gain_samples, self.sample_rate)
    
    def stop(self):
        """
        Stops the sound
        """
        sd.stop()

    def note_on(self, note):
        if note not in self.notes_actives:
            self.notes_actives[note] = 0.0 #on initialise la phase à 0

    def note_off(self, note):
        if note in self.notes_actives:
            del self.notes_actives[note] #on retire la note

    def get_gain(self):
        return 10 ** (self.volume / 20)