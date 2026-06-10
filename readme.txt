DÉPENDANCES
-----------
Python 3.8+

Installer les dépendances :
    pip install -r requirements.txt


COMMENT ÇA MARCHE
-----------------
Le synthé est organisé en deux couches :

1. MOTEUR AUDIO (audio.py)
   MoteurAudio ouvre un flux audio en continu via sounddevice (sd.OutputStream).
   Toutes les ~5ms, sounddevice appelle automatiquement le callback qui génère
   les prochains samples et les envoie à la carte son.

2. SYNTHÈSE (synth.py)
   Synth gère les notes actives dans un dictionnaire. Chaque note stocke :
   - sa phase courante (accumulateur de phase)
   - son état ADSR (attack, decay, sustain, release)
   Le callback parcourt ce dictionnaire, génère les samples de chaque note
   et les additionne.

WAVEFORMS DISPONIBLES
---------------------
- sine     : onde sinusoïdale, son pur et doux
- square   : onde carrée, son riche en harmoniques
- saw      : dent de scie, son brillant et agressif
- triangle : onde triangulaire, "intermédiaire" entre sine et square

Ce sont les formes basiques des premiers synthétiseurs analogiques (aussi appelées "Basic Shapes")

ENVELOPPE ADSR
--------------
Chaque note suit une enveloppe en 4 phases :
- Attack  : montée du volume de 0 à 1 (en secondes)
- Decay   : descente du volume jusqu'au niveau sustain (en secondes)
- Sustain : niveau de volume tenu tant que la note est pressée (entre 0 et 1)
- Release : descente du volume à 0 après le relâchement (en secondes)

Les valeurs de l'attack, de la decay, du sustain et de la release sont modifiables directement depuis l'UI

EFFETS
------
- Filtre passe-bas  : atténue les aigus (contrôlé par filter_alpha)
- Filtre passe-haut : atténue les graves (contrôlé par filter_alpha)
- Reverb            : simule un espace acoustique - c'est le seul composant qui n'a pas été implémenté directement
                      (nous utilisons pedalboard, la librairie de spotify)

LANCER LE PROJET
----------------
    python -m ui.ui

LANCER LES TESTS
----------------
    python tests.py