import numpy as np
from audio import MoteurAudio

class Synth:
    def __init__(self, moteur: MoteurAudio):
        self.moteur = moteur
    
    def _note_to_frequency(self, note):
        return self.moteur.tuning*2**((note-69)/12) #formule pour convert midi en fréquence
        
    def generate_sine(self, note: int = 69):
        """
        Simple sine wave oscillator, takes a MIDI input argument and outputs a sine wave
        """
        note_frequency = _note_to_frequency(note)
        temps = np.linspace(0,1,self.moteur.sample_rate)
        self.output = np.sin(2*np.pi*note_frequency*temps)
        return self.output
    
    def generate_saw(self, note):
        pass
    
    def generate_square(self,note):
        pass
