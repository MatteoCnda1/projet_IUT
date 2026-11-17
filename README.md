# Projet IUT – Infrastructure réseau du site de Marseille

Projet BUT3 R&T (R5.08 Gestion de projets / SAÉ 5.02) : concevoir le réseau complet du bâtiment IUT Génie Télécom (Luminy), relié à un site jumeau (Digne/Gap), dans le rôle d'une SS2I de conseil réseau.

**Roadmap interactive (suivi partagé des 21 points, journal de bord, chiffrage)** : https://claude.ai/artifact/KP4Dycvm54F3N8PZLvhXbW
(privée : la partager aux membres du groupe avec le niveau *Contributeur* depuis le menu Partager.)

## Arborescence

| Dossier | Contenu |
|---|---|
| `docs/cahier_des_charges/` | Consignes du projet (`PS5 Projet.pptx`, `Presentation_Projets_LP2021.pptx`) et grille des 21 points (`Avancement projet.xlsx`) |
| `docs/cours/` | Cours architecture d'entreprise (CCNP ch. 22), présentation du réseau AMU / Luminy |
| `docs/plans_batiment/` | Plans du bâtiment : sous-sol, RDC, étage 1, toiture |
| `docs/anssi/` | Référentiel des guides ANSSI applicables, reliés aux points du CdC et au schéma |
| `docs/references_prix/` | `cisco-price-list.pdf` (ancienne, gammes des années 2000) |
| `architecture/` | Schéma `Projet_Marseille_site.drawio` (version du 9 oct.) + `archives/` |
| `chiffrage/` | Estimation budgétaire de l'infra : `estimation_infra.md`, `.csv`, script `estimation.py` (reprend les quantités du plan de câblage) |
| `cablage/` | Scripts du plan de câblage et de l'étude Wi-Fi RSSI, à partir des plans PDF (voir `cablage/README.md`) |
| `roadmap/` | Source de la roadmap (`roadmap.template.html`, `build.py`, `seed_points.json`). `build.py` y injecte le chiffrage et le référentiel ANSSI |
| `livrables/` | Rapport, présentation, maquette GNS3, site web, journal de bord, vidéo en anglais. **`livrables/plan_cablage/`** : plan de câblage (point 04) et étude Wi-Fi |

## Chiffrage (résumé)

| | HT |
|---|---:|
| CAPEX (avec 10 % d'aléas) | 567 001 € |
| OPEX annuel (années 1 à 3) | 39 181 € |
| Coût total sur 5 ans | 818 620 € |

Détail et hypothèses : [`chiffrage/estimation_infra.md`](chiffrage/estimation_infra.md). Après une modification de `estimation.py` ou de `docs/anssi/referentiel_anssi.md` : `python3 chiffrage/estimation.py && python3 roadmap/build.py`, puis republier la page.

## Livrables attendus

Rapport technique (30 p. + annexes) · présentation orale · maquette Packet Tracer/GNS3 · site web du projet · journal de bord · vidéo en anglais. Tous les supports sont à rendre 8 à 10 jours avant l'oral.
