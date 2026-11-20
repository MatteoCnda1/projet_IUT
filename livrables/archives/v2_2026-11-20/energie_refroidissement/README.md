# Énergie et refroidissement (point 14)

> **Archive de la version 2** (15/11/2026, après l'audit), figée le 20/11/2026 depuis le commit `7e1db0b`. Version en vigueur : `livrables/energie_refroidissement/` (v2.1). Sources de cette version : `energie_v2.py` (ce dossier). Les commandes « Régénérer » ci-dessous visent les scripts en vigueur, pas cette archive.

Document principal : **[energie_refroidissement.pdf](energie_refroidissement.pdf)**. Tout est calculé par `energie/energie.py` à partir du chiffrage et du plan de câblage (`python3 energie/energie.py && python3 chiffrage/estimation.py`).

| | |
|---|---|
| Salle serveur | 3.46 kW typique, 4.49 kW en pointe, 2 baies 42U |
| Onduleurs | 2 × APC SRT 6 kVA en ligne (voies A et B) + 1 pack batterie chacun : 33 min même avec un onduleur en panne · 6 × 1,5 kVA dans les locaux techniques |
| Climatisation | 2 climatiseurs techniques 7.1 kW (1 en secours), allée froide, consigne 27 °C · ventilation des locaux techniques |
| Efficacité | PUE 1.34 (contre 1.41 pour une salle classique) · 53 510 kWh/an · ≈ 2.8 t CO₂/an |
| Finances | Investissement 71 900 € HT · 13 702 € HT/an · 140 410 € HT sur 5 ans |

Fichiers : `energie_refroidissement.pdf` (et `.html`), `schemas/` (alimentation électrique, plan de la salle serveur), `bilan_puissance.csv`, `resume.json` (repris par le chiffrage).

**Version 2 (après l'audit du 15/11/2026)** : serveurs virtualisés (12 serveurs physiques → 4 hyperviseurs + témoin), contrôleurs Wi-Fi physiques, plancher surélevé, batardeau, câble de détection de fuite et extinction automatique au gaz intégrés au lot (SYS-03), arrêt ordonné sur batterie par NUT. Le groupe électrogène reste une option à valider avec le campus. La v1 est archivée dans `livrables/archives/v1_2026-11-15/energie_refroidissement/` ; le traitement de l'audit est dans `livrables/audit/`.

Historique : la toute première version (Gemini) est dans git (commit 1fbc1c1).
