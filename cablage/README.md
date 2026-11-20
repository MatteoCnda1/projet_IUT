# cablage/ — scripts du plan de câblage et de l'étude Wi-Fi (point 04)

Lancer dans l'ordre, depuis la racine du dépôt :

```bash
python3 cablage/salles.py        # salles extraites des plans PDF (contours, surfaces, échelle)
python3 cablage/etude_rssi.py    # étude Wi-Fi prédictive -> livrables/plan_cablage/wifi/
python3 cablage/plan_cablage.py  # prises, cheminements, rocades, baies, plans, implantation -> livrables/plan_cablage/
python3 cablage/rapport.py       # livrables/plan_cablage/README.md
python3 energie/energie.py       # point 14 : lit plan_cablage/resume.json et les lignes de chiffrage/estimation.py
python3 chiffrage/estimation.py  # point 18 : reprend les quantités du plan de câblage et le lot énergie
```

Chaîne complète du dépôt, dans l'ordre des dépendances : `bash outils/ci/generer_tout.sh`. Le document d'implantation lit les
équipements de la salle serveur directement dans `chiffrage/estimation.py` : un seul passage suffit.

| Fichier | Rôle |
|---|---|
| `regles.py` | Décisions de l'équipe et hypothèses : types de salles, densité de prises, hypothèses radio |
| `batiment.py` | Aménagements : salle serveur dans J05, contour de l'amphithéâtre, corrections de types |
| `salles.py` | Lecture des plans (pdftotext, pdftoppm) et délimitation des salles |
| `etude_rssi.py` | Propagation multi-murs à 5 GHz, choix des bornes, plan de canaux |
| `plan_cablage.py` | Placement des prises, plus courts chemins vers les L.TECH, rocades et adductions, dimensionnement |
| `rendu_cablage.py` | Plans A3 et synoptique (PDF, SVG, PNG) |
| `document.py` | Document d'implantation RLI-ETU-001 (HTML, PDF), à la charte commune (`commun/charte.py`) |
| `rapport.py` | README du plan de câblage (`livrables/plan_cablage/README.md`) |

Dépendances : poppler-utils, Chrome ou Chromium (PDF), Python 3 avec numpy, scipy, opencv-python et matplotlib. Les fichiers
intermédiaires (`cablage/build/`) ne sont pas versionnés.
