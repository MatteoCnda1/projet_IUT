# Énergie et refroidissement (point 14)
<!-- onglet: Énergie -->

Alimentation électrique, onduleurs, groupe électrogène, climatisation et ventilation des locaux techniques, consommation et coûts du lot énergie de l'infrastructure réseau, avec l'étude BET de chaque local technique.

| Document | Réf. | Contenu |
|---|---|---|
| **[energie_refroidissement.pdf](energie_refroidissement.pdf)** | RLI-ETU-002 | Document principal : bilan de puissance, onduleurs, groupe électrogène, arrêt ordonné, climatisation et ventilation, PUE et Green IT, finances du lot |
| **[bet_locaux_techniques.pdf](bet_locaux_techniques.pdf)** | RLI-ETU-013 | Étude BET : inventaire, chaleur, ventilation et circuits de chaque local, tableau informatique, TGBT, groupe électrogène, vérifications, réserve sur la plateforme d'IA |
| `bet_dissipation.csv`, `bilan_puissance.csv` | — | Une ligne par équipement et par local (W absorbés, W dissipés, BTU/h) ; bilan de la salle serveur |
| `schemas/`, `resume.json` | — | Alimentation électrique, plan de la salle serveur, montée en température ; synthèse reprise par le chiffrage |

| | |
|---|---|
| Salle serveur | 3,57 kW typique, 4,64 kW en pointe, 2 baies 42U (enregistreur vidéo VS-NVR1 compris) ; chaleur 4,00 kW (pointe 5,38 kW) |
| Onduleurs | 2 × APC SRT 6 kVA en ligne (voies A et B) + 1 pack batterie chacun : 32 min même avec un onduleur en panne · 6 × 1,5 kVA dans les locaux techniques |
| Groupe électrogène (v2.1) | 33 kVA ESP / 30 kVA PRP diesel capoté, cuve 250 l (61 h à la charge moyenne), inverseur de source automatique en tête du TD-INFO ; arrêt ordonné NUT seulement si le groupe n'a pas repris à T0 + 3 min |
| Climatisation | 2 climatiseurs techniques 7,1 kW (1 en secours), allée froide, consigne 27 °C · L.TECH : N-1-LT01 grilles, N-1-LT02 grilles, N0-LT01 extracteur 150 m³/h, N0-LT02 extracteur 300 m³/h, N1-LT01 extracteur 300 m³/h, N1-LT02 mini-split 2,5 kW |
| Électricité | 13 départs au TD-INFO ; réserve au TGBT : 20 kVA (départ 4P 63 A), à vérifier sur site |
| Efficacité | PUE 1,45 (contre 1,53 pour une salle classique) · 59 422 kWh/an · environ 3,1 t CO₂/an |
| Finances | Investissement 104 550 € HT (dont groupe électrogène 32 000 €) · 19 566 € HT/an · 202 380 € HT sur 5 ans |
| Maintenance (v2.1) | Onduleurs et climatiseurs de la salle : dépannage 24 h/24 7 j/7, rétablissement en 4 h |

**Version 2.1 — 20/11/2026** : étude BET de chaque local (RLI-ETU-013 : inventaire, chaleur, ventilation, circuits, vérifications). Le client confirme qu'il n'y a pas de groupe électrogène sur le site : un groupe 33 kVA ESP et un inverseur automatique sont intégrés au lot. Ventilation renforcée de N0-LT02, N1-LT01, N1-LT02 (trop chauds en été), pertes réelles des onduleurs à faible charge et auxiliaires comptés (PUE 1,34 → 1,45), différentiels adaptés (type B, F, A SI), batteries des L.TECH remplacées tous les 4 ans, enregistreur vidéo VS-NVR1 au bilan, 29 bornes coupées la nuit, maintenance en 4 h des onduleurs et des climatiseurs. Le contrôle d'accès par badge (5 000 € en v2) passe au lot sûreté. Lot : 71 900 € (dont 5 000 € de contrôle d'accès, soit 66 900 € à périmètre égal) → 104 550 € HT d'investissement, 13 702 € → 19 566 € par an. Repérés « v2.1 » dans les documents. Version précédente : `livrables/archives/v2_2026-11-20/`.

**Version 2 (15/11/2026, après l'audit)** : serveurs virtualisés (16 serveurs physiques → 9 : 6 hyperviseurs DM/DT/NM, 2 témoins, 1 serveur de sauvegarde), contrôleurs Wi-Fi physiques, plancher surélevé, batardeau, câble de détection de fuite et extinction automatique au gaz intégrés au lot (SYS-03), arrêt ordonné sur batterie par NUT. La v1 est archivée dans `livrables/archives/v1_2026-11-15/energie_refroidissement/` ; le traitement de l'audit est dans `livrables/audit/`. La toute première version (Gemini) est dans git (commit 1fbc1c1).

Régénérer : `python3 energie/energie.py` (sources : `energie/energie.py`, qui appelle `energie/bet.py` ; lit `livrables/plan_cablage/` et les lignes de `chiffrage/estimation.py`), puis `python3 chiffrage/estimation.py`. Chaîne complète : `bash outils/ci/generer_tout.sh`.
