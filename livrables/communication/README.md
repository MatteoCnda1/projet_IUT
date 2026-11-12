# Point 02 · Communication sur la société fictive

**RudyLink Infrastructure**, société de conseil et d'ingénierie réseau du jeu de rôle (MOE), face à l'IUT Aix-Marseille (MOA).
Le nom vient de **RudyLink**, la micro-entreprise réelle de Mattéo Canada (rudylink.eu, services Nutrition et Knowledge) : la société du projet en est une troisième branche, imaginaire, qui reprend la charte « Console » existante.

Tout est produit par `communication/build.py` (voir plus bas) ; ne pas modifier les fichiers générés à la main.

## Documents

| Fichier | Réf. | Contenu |
|---|---|---|
| [`charte_graphique.pdf`](charte_graphique.pdf) | RLI-COM-001 | Société (nom, réel / fictif, mission, valeurs), logo, couleurs, typographie, règles graphiques, rédaction, supports |
| [`plaquette_rudylink_infrastructure.pdf`](plaquette_rudylink_infrastructure.pdf) | RLI-COM-002 | Plaquette 2 pages : offre, méthode, référence IUT avec les chiffres du projet, équipe, contact |
| [`organisation_projet.pdf`](organisation_projet.pdf) | RLI-COM-003 | MOA / MOE, organigramme, 6 rôles, matrice RACI des 21 points, instances, circuit de validation, gestion documentaire |

## Logo (`logo/`)

Symbole : la hiérarchie trois couches (1 cœur en émeraude, 2 distributions, 3 accès, accès central double-attaché). Textes vectorisés, donc aucun besoin de police pour les SVG.

| Fichier | Usage |
|---|---|
| `rudylink-infrastructure-couleur.svg/.png` | Par défaut, fond clair |
| `rudylink-infrastructure-inverse.svg/.png` | Fond encre (couvertures, slides) |
| `rudylink-infrastructure-constellation.svg/.png` | Fond vert du portail rudylink.eu |
| `rudylink-infrastructure-mono.svg/.png` | Noir et blanc |
| `rudylink-infrastructure-vertical-*.svg` | Formats carrés, avatar, affiche |
| `symbole.svg/.png`, `symbole-inverse.*`, `favicon.svg` | Icône seule |

## Modèles (`modeles/`)

| Fichier | Pour |
|---|---|
| `modele_rapport.docx` | Rapport technique (point 21) : couverture, suivi des versions, sommaire automatique, plan en 9 parties relié aux 21 points, exemples de tableau, encadrés et code |
| `modele_compte_rendu.docx` | Comptes rendus des réunions client `RLI-CR-nnn` (point 01) |
| `modele_presentation.pptx` | Soutenance : titre, sommaire, intercalaire, contenu, 8 chiffres clés, comparaison d'options, schéma, questions (chiffres réels du projet) |
| `modele_rapport.html/.pdf`, `rudylink-document.css` | Documents HTML imprimés en PDF, comme les livrables des points 04 et 14 |
| `signature_mail.html` | Signature de courriel à coller dans Gmail / Outlook |

**Polices** : installer les fichiers de `polices/` (Space Grotesk, IBM Plex Mono, licence SIL OFL) avant d'ouvrir les modèles Word et PowerPoint, sinon Office les remplace par une police par défaut. Remplacement prévu par la charte : Arial et Consolas.

## Site vitrine

[`../site_web/`](../site_web/README.md) : trois pages HTML simples (accueil, projet, journal de bord), écrites à la main, aux couleurs et polices de la charte. Hébergement prévu dans la DMZ (DM-WEB1 derrière les reverse proxies Caddy DM-RP1/2) : voir son README.

## Équipe et GesTT

`societe.json` (nom, équipe, rôles, documents) est lu par l'import de GesTT, qui affiche la société dans « Infos projet ». Les membres et leurs titres viennent des comptes GesTT : Mattéo Canada (chef de projet), Rafael Maunier, Solal Kruczinsky, Raphael Hovsepian.

## Régénérer

```bash
pip install python-docx python-pptx    # pour les modèles Office (sinon ils sont sautés)
python3 communication/build.py         # logos, PDF, modèles, societe.json, copie des PDF pour le site
```

Chrome ou Chromium est nécessaire (PDF et PNG). Les chiffres de la plaquette et des slides sont lus dans `livrables/plan_cablage/resume.json`, `livrables/energie_refroidissement/resume.json`, `chiffrage/estimation.json` et `roadmap/seed_points.json` : une mise à jour de ces fichiers suivie d'un build met tout à jour.

## Reste à faire

- Répartir les pôles ARC, PHY, SYS, SEC et COM entre les quatre membres : `EQUIPE` et `ROLES` dans `communication/documents.py`, puis le tableau de l'équipe dans `livrables/site_web/index.html`.
- Créer l'alias `infra@rudylink.eu` (Cloudflare Email Routing) ou changer `CONTACT` dans `communication/marque.py`. La signature de courriel charge son logo depuis `https://infra.rudylink.eu/assets/logo/symbole.png`.
