from audio import MoteurAudio
from synth import Synth
import time

# initialisation
moteur = MoteurAudio()
synth = Synth(moteur)
moteur.start(synth)

# test 1 : note simple
print("Test 1 : La4 (note 69) - sinusoide")
synth.note_on(69)
time.sleep(1)
synth.note_off(69)
time.sleep(0.5)
synth.reverb_mix = 0

# test 2 : polyphonie
print("Test 2 : accord Do-Mi-Sol - sinusoide")
synth.note_on(60)
synth.note_on(64)
synth.note_on(67)
time.sleep(2)
synth.note_off(60)
synth.note_off(64)
synth.note_off(67)
time.sleep(0.5)

# test 3 : waveforms
for waveform in ["saw", "square", "triangle"]:
    print(f"Test 3 : La4 - {waveform}")
    synth.waveform = waveform
    synth.note_on(69)
    time.sleep(1)
    synth.note_off(69)
    time.sleep(0.5)

# test 4 : filtre
print("Test 4 : filtre passe-bas")
synth.waveform = "saw"
synth.filter_active = True
synth.filter_alpha = 0.05
synth.note_on(69)
time.sleep(1.5)
synth.note_off(69)
time.sleep(0.5)

# test 5 : reverb
print("Test 5 : reverb")
synth.filter_active = False
synth.reverb_mix = 0.4
synth.note_on(69)
time.sleep(2)
synth.note_off(69)
time.sleep(1)

moteur.stop()
print("=== Tests terminés ===")