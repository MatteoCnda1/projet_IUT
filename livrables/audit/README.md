# Audits de l'infrastructure (15/11/2026 et 20/11/2026)
<!-- onglet: Audit -->

Les deux audits du dossier et leur traitement : l'audit du 15/11/2026 (version 1 : 16,9 / 20, 9 constats), qui a produit la version 2, puis l'audit v2.1 du 20/11/2026 (4 audits en parallèle, 167 constats, plus 8 sur la maquette hors dépôt), qui a produit la version 2.1.

| Document | Réf. | Contenu |
|---|---|---|
| **[traitement_audit.pdf](traitement_audit.pdf)** | RLI-AUD-001 | Partie A : vérification et correction des 9 constats du 15/11/2026, livrables touchés, réponses aux 14 questions du jury. Partie B : audit v2.1 (méthode, constats par audit, bloquants et majeurs avec leur traitement, BET et groupe électrogène, intégration continue, décisions D1 à D6, chiffres des trois versions, points ouverts) |
| **[rapport_audit_2026-11-15.pdf](rapport_audit_2026-11-15.pdf)** | — | Rapport d'audit d'origine du 15/11/2026, texte figé (aussi en `.html`) |
| [`constats_v21.json`](../../architecture/audit/constats_v21.json) | — | Les 175 constats de l'audit v2.1, hors dépôt compris (4 bloquants et 48 majeurs dans le dépôt), leur traitement et leur statut (146 traités sur 155 dans le dépôt), les décisions et les points ouverts : source de la partie B |

## Versions de l'infrastructure

| Version | Date | Ce qui la définit | Où |
|---|---|---|---|
| v1 | 13/11/2026 | Première version, auditée le 15/11/2026 | `livrables/archives/v1_2026-11-15/`, `architecture/archives/v1_2026-11-15/` |
| v2 | 15/11/2026 | Les 9 constats de l'audit du 15/11 traités (repères « v2 » dans les documents) | `livrables/archives/v2_2026-11-20/`, `architecture/archives/v2_2026-11-20/` |
| **v2.1** | 20/11/2026 | Audit v2.1 traité, BET des locaux techniques, groupe électrogène, charte commune, intégration continue (repères « v2.1 ») | livrables en vigueur |

| Indicateur (montants HT) | v1 (13/11/2026) | v2 (15/11/2026) | v2.1 (20/11/2026) |
|---|---:|---:|---:|
| Serveurs physiques | 16 | 9 | 9 |
| VLAN (hors transits) | 37 | 41 | 41 |
| Puissance IT de la salle serveur | 4,15 kW | 3,46 kW | 3,57 kW |
| PUE de la salle serveur | 1,34 | 1,34 | 1,45 |
| Électricité par an | 61 557 kWh | 53 510 kWh | 59 422 kWh |
| Autonomie avec un seul onduleur | 24 min | 33 min | 32 min |
| Secours long | aucun | aucun | groupe 33 kVA, 61 h |
| Lot énergie (investissement) | 57 000 € | 71 900 € | 104 550 € |
| CAPEX (aléas compris) | 582 951 € | 606 403 € | 678 991 € |
| OPEX annuel | 44 081 € | 44 892 € | 66 756 € |
| Coût sur 5 ans | 859 070 € | 881 177 € | 1 065 251 € |

v1 et v2 sont relues dans leurs archives (`livrables/archives/`), la v2.1 dans `chiffrage/estimation.json` et `livrables/energie_refroidissement/resume.json`.

**Version 2.1 — 20/11/2026** : partie B (audit v2.1) ajoutée au traitement, constat SYS-03 complété (groupe électrogène intégré), mise en page de la charte commune. Version précédente du traitement : dans git (tag `v2`).

Régénérer : `python3 architecture/audit/traitement_audit.py` (sources : `architecture/audit/constats_v21.json` pour les constats v2.1 et leur statut, les archives v1 et v2, `chiffrage/estimation.json`, `livrables/energie_refroidissement/resume.json`). Chaîne complète : `bash outils/ci/generer_tout.sh`. Le rapport d'audit d'origine et le script qui l'a produit (`generer_rapport_audit.py`) sont dans `architecture/audit/`.
