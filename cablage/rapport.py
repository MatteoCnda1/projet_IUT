#!/usr/bin/env python3
"""Rédige livrables/plan_cablage/README.md à partir des résultats (resume.json, wifi/bornes.json).
Structure du README de livrable de la charte (modèle A8) : titre « (point 04) », onglet GesTT, tableau des documents,
bloc de version, ligne « Régénérer ». Markdown : virgule décimale, espaces ordinaires (pas d'insécable).
Usage : python3 cablage/rapport.py   (après plan_cablage.py)"""
import json
import sys
from pathlib import Path

import batiment as bat

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from commun import charte as CH  # noqa: E402

OUT = HERE.parent / "livrables" / "plan_cablage"
NOMS = {"N-1": "Sous-sol", "N0": "RDC", "N1": "Étage 1"}


def m(v, d=0):
    """Nombre pour le Markdown : virgule décimale, espace ordinaire pour les milliers."""
    return f"{v:,.{d}f}".replace(",", " ").replace(".", ",")


def main():
    res = json.loads((OUT / "resume.json").read_text(encoding="utf-8"))
    wifi = json.loads((OUT / "wifi" / "bornes.json").read_text(encoding="utf-8"))
    h = wifi["hypotheses"]
    t = res["par_type"]
    communs = res.get("points_communs", {})
    add_commun = communs.get("adductions", [])
    roc_communs = {k: v for k, v in communs.items() if k != "adductions"}
    L = [
        "# Plan de câblage (point 04)",
        "<!-- onglet: Câblage -->", "",
        "Plan de câblage du bâtiment Génie des Télécommunications de l'IUT, campus de Luminy : prises, locaux techniques, fibres, arrivées "
        "opérateur et étude Wi-Fi, calculés à partir des plans d'architecte (`docs/plans_batiment/`).", "",
        "| Document | Réf. | Contenu |", "|---|---|---|",
        "| **[implantation.pdf](implantation.pdf)** | RLI-ETU-001 | Document d'implantation : salle serveur, locaux techniques, fibres, arrivées "
        "opérateur, et salle par salle le local de rattachement et le chemin des câbles |",
        "| [plans/N-1_cablage.pdf](plans/N-1_cablage.pdf), [N0](plans/N0_cablage.pdf), [N1](plans/N1_cablage.pdf) (.svg, .png) | — | Plan A3 de "
        "chaque niveau : prises, bornes, caméras, badgeuses, chemins de câbles, rocades, colonnes, salles teintées par local |",
        "| [synoptique.pdf](synoptique.pdf) (.svg, .png) | — | Rocades, colonnes montantes, adductions, contenu de chaque baie |",
        "| `prises.csv` | — | Toutes les prises : repère (`N0-LT02-P017`), local, salle, type, usage, PoE, position, longueur, repère de l'équipement |",
        "| `baies.csv`, `rocades.csv`, `resume.json` | — | Dimensionnement des baies, longueurs et chemins des rocades, synthèse (lue par le chiffrage, "
        "l'énergie, l'adressage et les CCTP) |",
        "| `wifi/` | — | Étude RSSI : cartes de couverture, bornes et canaux |", "",
        f"**Version 2.1 — {CH.DATE_VERSION}** : caméra du foyer des étudiants retirée ({t['camera']} caméras, {res['prises']} prises), voies B du "
        "sous-sol et arrivée FAI 2 tracées par d'autres circulations que la voie A, câbles écartés de la gaine d'ascenseur, repères uniques des "
        "bornes, caméras et badgeuses, charte commune, repérés « v2.1 » dans les documents. Version précédente : "
        f"`{CH.ARCHIVE_PRECEDENTE}`.", "",
        "Régénérer : `python3 cablage/salles.py && python3 cablage/etude_rssi.py && python3 cablage/plan_cablage.py && python3 cablage/rapport.py` "
        "(sources : `cablage/`). Chaîne complète du dépôt, dans l'ordre des dépendances : `bash outils/ci/generer_tout.sh`.", "",
        "## Décisions de l'équipe (12/11/2026, complétées le 20/11/2026)", "",
        "| Sujet | Décision |", "|---|---|",
        f"| Salle serveur | Partie sud de la **SALLE J05** (sous-sol), environ {bat.SURFACE_SALLE_SERVEUR:.0f} m² cloisonnés, contre le L.TECH 01 du sous-sol. "
        "Au centre du bâtiment : rocades les plus courtes. |",
        "| Répartiteurs d'étage | Les **6 L.TECH** des plans, 2 par niveau. |",
        "| Logement de fonction (étage 1, aile nord-est) | **Hors périmètre** : abonnement opérateur séparé, aucune prise. |",
        "| Densité de prises | Bureau : 2 par poste (PC, téléphone ou réserve). Salle de TP : 1 par poste (environ 2,5 m² par poste, 24 au plus) "
        "+ 2 pour l'enseignant. Salle de TD, cours, réunion : 3. Projet : 8. |",
        "| Wi-Fi | Nombre de bornes fixé par une **étude RSSI prédictive** (ci-dessous), validée par l'équipe. |",
        f"| Sûreté | {t['camera']} caméras IP (v2.1 : aucune au foyer des étudiants, lieu de pause), {t['badge']} badgeuses (salle serveur, "
        "6 L.TECH, entrée, hall, 2 salles réseaux). |",
        f"| Téléphonie IP | 1 téléphone par bureau d'enseignant + l'accueil (secrétariat) : {res['telephones']} postes, sur la 2e prise du bureau. |",
        "| Adductions opérateur | **Deux entrées séparées** : FAI 1 façade ouest (L.TECH 02 du sous-sol, côté chaufferie), FAI 2 façade est (parking) ; "
        "v2.1 : le tracé intérieur de FAI 2 évite les circulations de FAI 1. |",
        "| Rocades | **Deux fibres OM4 par local, par deux chemins distincts** : une par colonne montante (RDC, étage) ; au sous-sol, voie B par "
        "d'autres circulations et une autre traversée de mur que la voie A (v2.1). |", "",
        "## Résultats", "",
        f"- **{res['prises']} prises RJ45 Cat6A** : {t['usager']} usagers, {t['wifi']} bornes Wi-Fi, {t['camera']} caméras, {t['badge']} badgeuses.",
        f"- **{m(res['cable_cuivre_m'])} m de câble cuivre**, lien moyen {m(res['lien_moyen_m'], 1)} m, **lien le plus long {m(res['lien_max_m'], 1)} m** "
        f"({'aucun' if not res['liens_hors_norme'] else len(res['liens_hors_norme'])} au-delà de {res['hypotheses']['lien_max_m']:.0f} m).",
        f"- **{len(res['rocades'])} rocades fibre**, {m(res['fibre_m'])} m au total.",
        f"- **{sum(b['switchs_48p'] for b in res['baies'])} switchs d'accès** 48 ports PoE+ (Catalyst C9200L-48P-4X) répartis dans les 6 locaux.", "",
        "### Locaux techniques et baies", "",
        "| Local | Salle du plan | Surface | Prises | Usagers / Wi-Fi / caméras / badges | Switchs 48p | Baie | PoE | Lien max |",
        "|---|---|---:|---:|---|---:|---|---:|---:|",
    ]
    for b in res["baies"]:
        L.append(f"| {b['local']} | {b['salle']} | {b['surface_m2']:.0f} m² | {b['prises']} | {b['usagers']} / {b['wifi']} / {b['cameras']} / {b['badges']} | "
                 f"{b['switchs_48p']} | {b['baie']} ({b['hauteur_U']}U) | {b['poe_W']} W | {b['lien_max_m']:.0f} m |")
    L += ["", "Le local du RDC nord (`L.TECH`, environ 2 m²) est un placard : baie murale 24U, ventilation dimensionnée par l'étude BET du point 14. "
          "Le L.TECH 02 de l'étage reçoit la baie au sol 42U (aile sud, salles de TP).", "",
          "### Rocades (fibre OM4 12 brins)", "", "| Local | Voie | Par | Chemin | Longueur |", "|---|---|---|---|---:|"]
    for r in res["rocades"]:
        L.append(f"| {r['local']} | {r['voie']} | {r['par']} | {r['chemin']} | {r['longueur']:.0f} m |")
    L += ["", "Colonne **Nord** : à l'aplomb du L.TECH du RDC nord, depuis le vide sanitaire 01. Colonne **Sud** : à l'aplomb des L.TECH 02 du RDC et "
          "de l'étage, depuis le plafond du parking. La voie B d'un local passe toujours par l'autre colonne : une colonne coupée n'isole aucun local. "
          "Au sous-sol, la voie B évite les salles, circulations et traversées de mur de la voie A (v2.1) : "
          + ("aucune circulation commune." if not roc_communs else
             "seul reste commun : " + " ; ".join(f"{k} ({', '.join(v)})" for k, v in roc_communs.items()) + "."), "",
          "### Adductions", "", "| Opérateur | Entrée | Chemin jusqu'à la salle serveur | Longueur |", "|---|---|---|---:|"]
    for a in res["adductions"]:
        L.append(f"| {a['operateur']} | {a['entree']} | {a['chemin']} | {a['longueur_interne']:.0f} m (dont 15 m jusqu'à la chambre de tirage) |")
    if add_commun:
        L += ["", f"Point commun restant : les deux fourreaux traversent le {', '.join(add_commun)}, seul passage du côté est vers la salle serveur "
              "(supports distincts au plafond du parking)."]
    L += ["", "### Chemins de câbles (circulations et locaux)", "", "| Niveau | Dimension (mm) | Longueur |", "|---|---|---:|"]
    for c, d in res["chemins_de_cables_m"].items():
        for dim, v in d.items():
            L.append(f"| {NOMS[c]} | {dim} | {v} m |")
    L += ["", "Dimension choisie pour un taux de remplissage ≤ 40 % (câble Cat6A de 7,5 mm de diamètre). Dans les salles, le câble suit une goulotte "
          "périmétrique depuis la porte.", "",
          "## Étude Wi-Fi prédictive (RSSI)", "",
          f"Modèle multi-murs à {m(h['frequence_MHz'])} MHz : PIRE {h['PIRE_dBm']:.0f} dBm, exposant {m(h['exposant'], 1)}, "
          f"mur porteur {h['affaiblissements_dB']['mur']:.0f} dB, cloison {h['affaiblissements_dB']['cloison']:.0f} dB, vitrage {h['affaiblissements_dB']['vitrage']:.0f} dB "
          "(parois lues sur le plan). Objectif : **≥ −67 dBm** (voix et vidéo) sur 98 % de chaque niveau et 90 % de chaque salle occupée. "
          "Une borne par salle de TP, de TD et de projet de 20 m² ou plus, une au foyer, deux pour l'amphithéâtre et S.Cours.", "",
          "| Niveau | Bornes | Surface couverte | ≥ −67 dBm | 2e borne ≥ −70 dBm (itinérance) |", "|---|---:|---:|---:|---:|"]
    for n in wifi["niveaux"]:
        s = n["stats"]
        nb = sum(b["niveau"] == n["code"] for b in wifi["bornes"])
        L.append(f"| {NOMS[n['code']]} | {nb} | {m(s['surface_cible_m2'])} m² | {m(s['couverture_pct'], 1)} % | {m(s['itinerance_pct'], 1)} % |")
    L += ["", f"Plan de canaux : 12 canaux de 40 MHz à 5 GHz, {wifi['conflits_co_canal']} conflit co-canal (niveaux compris). "
          "Cartes : `wifi/N-1_rssi.png`, `wifi/N0_rssi.png`, `wifi/N1_rssi.png` ; liste des bornes : `wifi/bornes.csv`.", "",
          "## Normes et règles appliquées", "",
          "- Câblage structuré ISO/IEC 11801-1 et EN 50173-1 : classe EA (Cat6A, 10GBASE-T), lien permanent ≤ 90 m, canal ≤ 100 m.",
          "- Installation EN 50174-2 : séparation courants forts / faibles, rayons de courbure, rebouchage coupe-feu des traversées.",
          "- Aucun câble dans la gaine ni dans le local de machinerie d'ascenseur (NF EN 81-20) : le calcul des chemins les évite (v2.1).",
          "- Câbles Euroclasse Cca-s1b,d1,a1 (règlement CPR, établissement recevant du public).",
          "- Repérage TIA-606 : prise `<niveau>-LT<local>-P<numéro>`, la même étiquette sur la prise et au panneau de brassage ; équipement raccordé "
          "`AP-<niveau>-<nn>` (borne, identifiant de l'étude Wi-Fi), `<niveau>-C<n>` (caméra), `<niveau>-B<n>` (badgeuse), uniques dans le bâtiment.",
          "- Longueur d'un lien = 1,10 × cheminement sur le plan + 3 m de descentes + 2 m de lovage.", "",
          "## Limites et points à valider avec le client", "",
          "- Échelle mesurée sur le cartouche des plans : précision ±2 %. Les longueurs sont des estimations, à confirmer au relevé.",
          "- Étude Wi-Fi prédictive, faite sur plan : affaiblissements estimés d'après le trait des parois, pertes entre étages ignorées. "
          "Une mesure sur site (site survey) devra la confirmer.",
          "- Emplacement des chambres de tirage des deux opérateurs et accord pour faire passer les chemins de câbles en vide sanitaire et au plafond du parking.",
          ("- Les deux arrivées opérateur traversent toutes deux le " + ", ".join(add_commun) + " : point commun accepté (supports séparés) ou autre "
           "entrée pour FAI 2, à décider avec les opérateurs." if add_commun else "- Arrivées opérateur : aucune circulation commune à l'intérieur."),
          "- Salle serveur dans J05 : réaffectation de la salle et cloison coupe-feu à valider ; plancher technique, détection de fuite, extinction "
          "et climatisation sont au lot énergie (point 14).",
          "- L'amphithéâtre de l'étage n'est accessible que par le bas : ses prises sont câblées depuis le RDC, par les gradins.",
          "- Les petites salles J02 à J04 et la partie restante de J05 sont comptées comme des salles de TD (3 prises), à confirmer selon leur usage.", ""]
    (OUT / "README.md").write_text("\n".join(L), encoding="utf-8")
    print(f"README.md : {len(L)} lignes")


if __name__ == "__main__":
    main()
