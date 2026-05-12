from audio import MoteurAudio
from synth import Synth
import sounddevice as sd
import time

if __name__ == '__main__':
    moteur = MoteurAudio()
    synth = Synth(moteur)

    moteur.start(synth)

    synth.note_on(60)  # Do4
    synth.note_on(64)  # Mi4
    synth.note_on(67)  # Sol4

    time.sleep(2)

    synth.note_off(60)
    synth.note_off(64)
    synth.note_off(67)

    moteur.stop()