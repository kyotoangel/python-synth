import math
import numpy as np


def linear_to_db(value: float) -> float:
    """
    Transforme une valeur comprise entre 0 et 1 en une valeur entre -inf et -18db.
    :param float value: La valeur que l'on souhaite convertir.
    :return float db: La valeur convertie en db.
    """
    if value <= 0:
        return -math.inf

    db = 20 * math.log10(value) - 18
    return db

def interpoler(valeur: float, min_cible: float, max_cible: float) -> float:
    """
    Transforme une valeur comprise entre 0 et 1 en une valeur comprise entre min_cible et max_cible.
    :param float valeur: La valeur que l'on souhaite interpoler.
    :param float min_cible: La valeur minimale de la cible.
    :param float max_cible: La valeur maximale de la cible.
    :return float: La valeur interpolée entre min_cible et max_cible.
    """
    return min_cible + (valeur * (max_cible - min_cible))

def lp_response(frequencies: np.ndarray, cutoff: float) -> np.ndarray:
    """
    Calcule la réponse en amplitude d'un filtre passe-bas du premier ordre.

    :param np.ndarray frequencies: Tableau de fréquences en Hz pour lesquelles évaluer la réponse.
    :param float cutoff: Fréquence de coupure du filtre en Hz.
    :return np.ndarray: Amplitude normalisée entre 0 et 1 pour chaque fréquence.
    """
    ratio = frequencies / cutoff
    return 1.0 / (1.0 + ratio ** 2)

def hp_response(frequencies: np.ndarray, cutoff: float) -> np.ndarray:
    """
    Calcule la réponse en amplitude d'un filtre passe-haut du premier ordre.

    :param np.ndarray frequencies: Tableau de fréquences en Hz pour lesquelles évaluer la réponse.
    :param float cutoff: Fréquence de coupure du filtre en Hz.
    :return np.ndarray: Amplitude normalisée entre 0 et 1 pour chaque fréquence.
    """
    ratio = frequencies / cutoff
    return ratio ** 2 / (1.0 + ratio ** 2)