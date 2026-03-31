from audio import MoteurAudio
from synth import Synth
import sounddevice as sd

moteur = MoteurAudio()
synth = Synth(moteur)
samples = synth.generate_saw(69)
moteur.play(samples)
sd.wait()