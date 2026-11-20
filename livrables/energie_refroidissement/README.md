# Énergie et refroidissement (point 14)

Document principal : **[energie_refroidissement.pdf](energie_refroidissement.pdf)**. Étude BET de chaque local technique : **[bet_locaux_techniques.pdf](bet_locaux_techniques.pdf)** (v2.1). Tout est calculé par `energie/energie.py`, qui appelle `energie/bet.py`, à partir du chiffrage et du plan de câblage (`python3 energie/energie.py && python3 chiffrage/estimation.py && python3 roadmap/build.py`).

| | |
|---|---|
| Salle serveur | 3.49 kW typique, 4.52 kW en pointe, 2 baies 42U ; chaleur 3.92 kW (pointe 5.26 kW) |
| Onduleurs | 2 × APC SRT 6 kVA en ligne (voies A et B) + 1 pack batterie chacun : 33 min même avec un onduleur en panne · 6 × 1,5 kVA dans les locaux techniques |
| Groupe électrogène (v2.1) | 33 kVA ESP / 30 kVA PRP diesel capoté, cuve 250 l (62 h à la charge moyenne), inverseur de source automatique en tête du TD-INFO ; arrêt ordonné NUT seulement si le groupe n'a pas repris à T0 + 3 min |
| Climatisation | 2 climatiseurs techniques 7.1 kW (1 en secours), allée froide, consigne 27 °C · L.TECH : N-1-LT01 grilles, N-1-LT02 grilles, N0-LT01 extracteur 150 m³/h, N0-LT02 extracteur 300 m³/h, N1-LT01 extracteur 300 m³/h, N1-LT02 mini-split 2,5 kW |
| Électricité | 13 départs au TD-INFO, réserve à demander au TGBT : 20 kVA (départ 4P 63 A) |
| Efficacité | PUE 1.45 (contre 1.53 pour une salle classique) · 58 491 kWh/an · ≈ 3.0 t CO₂/an |
| Finances | Investissement 109 550 € HT (dont groupe électrogène 32 000 €) · 16 879 € HT/an · 193 945 € HT sur 5 ans |

Fichiers : `energie_refroidissement.pdf` (et `.html`), `bet_locaux_techniques.pdf` (et `.html`), `bet_dissipation.csv` (une ligne par équipement et par local : W absorbés, W dissipés dans le local, BTU/h), `schemas/` (alimentation électrique avec le groupe, plan de la salle serveur, montée en température sans refroidissement), `bilan_puissance.csv`, `resume.json` (repris par le chiffrage).

**Version 2.1 (20/11/2026)** : étude BET de chaque local (inventaire, chaleur, ventilation, circuits, vérifications). Le client confirme qu'il n'y a pas de groupe électrogène sur le site : un groupe 33 kVA ESP et un inverseur automatique sont intégrés au lot. Ventilation renforcée de N0-LT02, N1-LT01, N1-LT02 (trop chauds en été), pertes réelles des onduleurs à faible charge et auxiliaires comptés (PUE 1.34 → 1.45), différentiels adaptés (type B, F, A SI), batteries des L.TECH remplacées tous les 4 ans. Lot : 71 900 € → 109 550 € HT d'investissement, 13 702 € → 16 879 € HT/an.

**Version 2 (après l'audit du 15/11/2026)** : serveurs virtualisés (12 serveurs physiques → 4 hyperviseurs + témoin), contrôleurs Wi-Fi physiques, plancher surélevé, batardeau, câble de détection de fuite et extinction automatique au gaz intégrés au lot (SYS-03), arrêt ordonné sur batterie par NUT. La v1 est archivée dans `livrables/archives/v1_2026-11-15/energie_refroidissement/` ; le traitement de l'audit est dans `livrables/audit/`.

Historique : la toute première version (Gemini) est dans git (commit 1fbc1c1).
