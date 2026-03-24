import numpy as np
import sounddevice as sd

class MoteurAudio:
    def __init__(self, sample_rate: int = 44100, volume: float = -6.0, tuning: int = 440) -> None:
        self.sample_rate = sample_rate
        self.volume = volume
        self.tuning = tuning
    
    def generate_sine(self, note: int = 69):
        """
        Simple sine wave oscillator, takes a MIDI input argument and outputs a sine wave
        """
        self.note_frequency = self.tuning*2**((note-69)/12) #formule pour convert midi en fréquence
        temps = np.linspace(0,1,self.sample_rate)
        self.output = np.sin(2*np.pi*self.note_frequency*temps)
        return self.output
        
    def play(self, samples: np.ndarray):
        gain_samples = samples * 10**(self.volume/20) #corrige avec le volume (dB deviennent linéaires)
        sd.play(gain_samples, self.sample_rate)
    
    def stop(self):
        sd.stop()
