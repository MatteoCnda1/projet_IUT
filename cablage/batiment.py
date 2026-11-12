"""Bâtiment tel que l'équipe l'aménage : salles extraites des plans + décisions du projet.

Charge cablage/build/salles.json (produit par salles.py) et applique :
  - le type de chaque salle (regles.type_salle) et quelques corrections ;
  - le contour de l'amphithéâtre (ovale mesuré sur le plan de l'étage 1, l'extraction
    automatique ne le délimite pas à cause des gradins) ;
  - la salle serveur, cloisonnée dans la partie sud de la SALLE J05 (sous-sol).
Coordonnées en mètres, repère commun aux trois niveaux (origine : coin haut gauche du plan).
"""
import json
import math
from pathlib import Path

import regles as R

BUILD = Path(__file__).resolve().parent / "build"

# Ovale de l'amphithéâtre (étage 1), mesuré sur le plan : centre et axes en m
AMPHI = {"centre": (54.75, 10.64), "axes": (15.65, 12.85)}
SURFACE_SALLE_SERVEUR = 25.0  # m², partie sud de la SALLE J05

# Corrections de type : (niveau, nom) -> type
CORRECTIONS = {
    ("N-1", "CIRCULATION 01"): "technique",   # passage technique sous l'amphi, entre vides sanitaires
    ("N-1", "DOUCHE"): "sanitaire",
    ("N0", "PL.ELEC"): "technique",
    ("N0", "PL"): "technique",
}


def ellipse_contour(c, axes, n=72):
    (cx, cy), (a, b) = c, axes
    return [[round(cx + a / 2 * math.cos(2 * math.pi * k / n), 2), round(cy + b / 2 * math.sin(2 * math.pi * k / n), 2)]
            for k in range(n)]


def charger():
    data = json.loads((BUILD / "salles.json").read_text(encoding="utf-8"))
    for niv in data["niveaux"]:
        code = niv["code"]
        salles = []
        for s in niv["salles"]:
            s = dict(s)
            s["type"] = CORRECTIONS.get((code, s["nom"])) or R.type_salle(s["nom"], code)
            if s["nom"] == "DOUCHE" and code == "N-1":
                s["contour"] = None  # le remplissage a débordé à l'extérieur
            if code == "N1" and s["nom"] == "AMPHITHEATRE":
                (cx, cy), (a, b) = AMPHI["centre"], AMPHI["axes"]
                s.update(x=cx, y=cy, surface=round(math.pi * a * b / 4, 1), bbox=[cx - a / 2, cy - b / 2, cx + a / 2, cy + b / 2],
                         contour=ellipse_contour(AMPHI["centre"], AMPHI["axes"]), fuite=False)
            if code == "N-1" and s["nom"] == "SALLE J05":
                x0, y0, x1, y1 = s["bbox"]
                ycut = y1 - SURFACE_SALLE_SERVEUR / (x1 - x0)
                serveur = {"nom": "SALLE SERVEUR", "type": "salle_serveur", "x": (x0 + x1) / 2, "y": (ycut + y1) / 2,
                           "surface": SURFACE_SALLE_SERVEUR, "bbox": [x0, ycut, x1, y1],
                           "contour": [[x0, ycut], [x1, ycut], [x1, y1], [x0, y1]],
                           "note": f"cloisonnée dans la partie sud de la SALLE J05 ({SURFACE_SALLE_SERVEUR:.0f} m²)"}
                s.update(y=(y0 + ycut) / 2, surface=round(s["surface"] - SURFACE_SALLE_SERVEUR, 1), bbox=[x0, y0, x1, ycut],
                         contour=[[x0, y0], [x1, y0], [x1, ycut], [x0, ycut]], note="partie nord, après cloisonnement")
                salles.append(s)
                salles.append(serveur)
                continue
            salles.append(s)
        niv["salles"] = salles
    return data


def salle(data, code, nom):
    niv = next(n for n in data["niveaux"] if n["code"] == code)
    return next(s for s in niv["salles"] if s["nom"] == nom)
