from audio import MoteurAudio
import sounddevice as sd

moteur = MoteurAudio()
samples = moteur.generate_sine(69)
moteur.play(samples)
sd.wait()

