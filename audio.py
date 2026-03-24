import numpy as np
import sounddevice as sd

class MoteurAudio:
    def __init__(self, sample_rate: int = 44100, volume: float = -6.0, tuning: int = 440) -> None:
        self.sample_rate = sample_rate
        self.volume = volume
        self.tuning = tuning
        
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

