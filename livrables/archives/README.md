# Archives des versions de l'infrastructure

Chaque version livrée puis remplacée est figée ici telle qu'elle était au moment du gel : documents (PDF, HTML), tables, chiffrage, et le script qui les a produits. Ces fichiers ne se corrigent plus : la CI les exclut du lint Python et du contrôle d'orthographe, et les liens qu'ils contiennent restent valides.

| Version | Date | Gelée le | Ce qu'elle est | Documents | Schémas et sources |
|---|---|---|---|---|---|
| **v1** | 13/11/2026 | 15/11/2026 (jour de l'audit, tag git `v1`) | Version soumise à l'audit du 15/11/2026 (16,9 / 20, 9 constats) | [`v1_2026-11-15/`](v1_2026-11-15/) | `architecture/archives/v1_2026-11-15/` |
| **v2** | 15/11/2026 | 20/11/2026 (commit `7e1db0b`, tag git `v2`) | Version corrigée après l'audit du 15/11/2026, remplacée par la v2.1 après l'audit v2.1 du 20/11/2026 | [`v2_2026-11-20/`](v2_2026-11-20/) | `architecture/archives/v2_2026-11-20/` |

**Version en vigueur : v2.1 — 20/11/2026**, dans `livrables/` hors de ce dossier. Ce qui a changé d'une version à l'autre, constat par constat : [`livrables/audit/traitement_audit.pdf`](../audit/traitement_audit.pdf) (RLI-AUD-001) ; les chiffres clés des trois versions côte à côte : [`livrables/audit/README.md`](../audit/README.md).

## Contenu de chaque archive

| Dossier | v1 | v2 |
|---|---|---|
| `plan_adressage/` | PDF, HTML, `vlans.csv`, `equipements.csv`, `interconnexions.csv` (37 VLAN + 6 transits) | mêmes fichiers (41 VLAN + 6 transits, VLAN 310 tier 0) |
| `architecture_l2/` | PDF, HTML, schémas PNG | mêmes fichiers |
| `architecture_l3/` | PDF, HTML, schéma PNG | mêmes fichiers |
| `energie_refroidissement/` | PDF, HTML, `schemas/`, `bilan_puissance.csv`, `resume.json`, script `energie_v1.py` | mêmes fichiers, script `energie_v2.py` |
| `chiffrage/` | `estimation_infra.md`, `.csv`, `estimation.json`, script `estimation.py` | mêmes fichiers |

Les schémas draw.io (`Projet_Marseille_site`, `architecture_l2`, `architecture_l3`) et les scripts du réseau (`reseau/donnees.py`, `documents.py`, `schemas.py`, `build.py`, `drawio.py`) de chaque version sont dans `architecture/archives/vN_AAAA-MM-JJ/`. Les schémas plus anciens (`Projet_Marseille_site_2025-10-06.drawio`, `_2026-10-09.drawio`) y sont aussi.

Chaque README d'archive commence par un encadré qui donne la date du gel et le dossier en vigueur. Les commandes « Régénérer » qu'ils contiennent visent les scripts en vigueur : une archive ne se régénère pas.

## Règles

- Nom du dossier : `vN_AAAA-MM-JJ`, la date étant celle du gel (jour où la version suivante commence).
- Le contenu vient de git, pas de la copie de travail : `git show <commit>:<chemin> > <archive>/<chemin>` pour chaque fichier, puis `cmp` contre git.
- Comparer deux versions d'un livrable : `git diff v1 v2 -- livrables/plan_adressage/vlans.csv`, ou `diff` entre l'archive et le dossier en vigueur.
- Les montants v1 et v2 cités ailleurs (README de l'audit, traitement de l'audit) sont relus dans `v1_2026-11-15/chiffrage/estimation.json` et `v2_2026-11-20/chiffrage/estimation.json`, jamais recopiés.
