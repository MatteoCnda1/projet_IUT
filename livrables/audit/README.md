# Audit de l'infrastructure (15/11/2026)
<!-- onglet: Audit -->

Audit indépendant en lecture seule de tout le dossier (schémas, adressage, L2/L3, chiffrage, énergie), réalisé avec Gemini (trois rôles : réseau, sécurité/ANSSI, systèmes/datacenter). Note : **16,9 / 20**, 9 constats (2 critiques, 5 majeurs, 2 mineurs).

| Fichier | Contenu |
|---|---|
| [`traitement_audit.pdf`](traitement_audit.pdf) | RLI-AUD-001 : vérification de chaque constat, corrections de la v2, livrables touchés, réponses aux 14 questions du jury |
| [`rapport_audit_2026-11-15.pdf`](rapport_audit_2026-11-15.pdf) | Rapport d'audit d'origine (aussi en `.html`) |

## Versions de l'infrastructure

- **v1** (auditée) : figée dans `livrables/archives/v1_2026-11-15/` et `architecture/archives/v1_2026-11-15/`.
- **v2** (actuelle) : tous les livrables régénérés ; les changements sont repérés **v2** dans les documents.

| | v1 | v2 |
|---|---:|---:|
| Serveurs physiques | 16 | 9 |
| VLAN (hors transits) | 37 | 41 |
| Pool Wi-Fi étudiants | /22 par bloc, 94 % (bloc 1) | /20 pour le bâtiment, 37 % |
| Puissance de la salle serveur | 4.15 kW | 3.46 kW |
| Électricité par an | 61 557 kWh | 53 510 kWh |
| Autonomie avec un seul onduleur | 24 min | 33 min |
| CAPEX (aléas compris) | 582 951 € | 606 403 € |
| OPEX annuel | 44 081 € | 44 892 € |
| Coût sur 5 ans | 859 070 € | 881 177 € |

Régénérer : `python3 architecture/reseau/build.py && python3 energie/energie.py && python3 chiffrage/estimation.py && python3 architecture/audit/traitement_audit.py`. Le rapport d'audit et le script qui l'a produit (`generer_rapport_audit.py`) sont dans `architecture/audit/`.
