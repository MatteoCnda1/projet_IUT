# cablage/ — scripts du plan de câblage et de l'étude Wi-Fi

Lancer dans l'ordre, depuis la racine du repo :

```bash
python3 cablage/salles.py       # salles extraites des plans PDF (contours, surfaces, échelle)
python3 cablage/etude_rssi.py   # étude Wi-Fi prédictive -> livrables/plan_cablage/wifi/
python3 cablage/plan_cablage.py # prises, cheminements, rocades, baies -> livrables/plan_cablage/
python3 cablage/rapport.py      # livrables/plan_cablage/README.md
python3 chiffrage/estimation.py # reprend les quantités du plan de câblage
```

| Fichier | Rôle |
|---|---|
| `regles.py` | Décisions de l'équipe et hypothèses : types de salles, densité de prises, hypothèses radio |
| `batiment.py` | Aménagements : salle serveur dans J05, contour de l'amphithéâtre, corrections de types |
| `salles.py` | Lecture des plans (pdftotext, pdftoppm) et délimitation des salles |
| `etude_rssi.py` | Propagation multi-murs à 5 GHz, choix des bornes, plan de canaux |
| `plan_cablage.py` | Placement des prises, plus courts chemins vers les L.TECH, rocades, dimensionnement |
| `rendu_cablage.py` | Plans A3 et synoptique (PDF, SVG, PNG) |

Dépendances : poppler-utils, Python 3 avec numpy, scipy, opencv-python et matplotlib. Les fichiers
intermédiaires (`cablage/build/`) ne sont pas versionnés.
