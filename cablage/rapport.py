#!/usr/bin/env python3
"""Rédige livrables/plan_cablage/README.md à partir des résultats (resume.json, wifi/bornes.json).
Usage : python3 cablage/rapport.py   (en dernier, après plan_cablage.py)"""
import datetime
import json
from pathlib import Path

import batiment as bat
import regles as R

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "livrables" / "plan_cablage"
NOMS = {"N-1": "Sous-sol", "N0": "RDC", "N1": "Étage 1"}


def main():
    res = json.loads((OUT / "resume.json").read_text(encoding="utf-8"))
    wifi = json.loads((OUT / "wifi" / "bornes.json").read_text(encoding="utf-8"))
    data = bat.charger()
    h = wifi["hypotheses"]
    t = res["par_type"]
    m = lambda v: f"{v:,.0f}".replace(",", " ")
    L = [
        "# Plan de câblage – Site de Marseille (point 04)", "",
        f"Généré le {datetime.date.today():%d/%m/%Y} par `cablage/` à partir des plans d'architecte (`docs/plans_batiment/`). "
        "Pour régénérer : `python3 cablage/salles.py && python3 cablage/etude_rssi.py && python3 cablage/plan_cablage.py "
        "&& python3 cablage/rapport.py && python3 chiffrage/estimation.py`.", "",
        "## Décisions de l'équipe (12/11/2026)", "",
        "| Sujet | Décision |", "|---|---|",
        f"| Salle serveur | Partie sud de la **SALLE J05** (sous-sol), ≈ {bat.SURFACE_SALLE_SERVEUR:.0f} m² cloisonnés, contre le L.TECH 01 du sous-sol. Au centre du bâtiment : rocades les plus courtes. |",
        "| Répartiteurs d'étage | Les **6 L.TECH** des plans, 2 par niveau. |",
        "| Logement de fonction (étage 1, aile nord-est) | **Hors périmètre** : abonnement opérateur séparé, aucune prise. |",
        "| Densité de prises | Bureau : 2 par poste (PC + téléphone). Salle de TP : 1 par poste (≈ 2,5 m²/poste, 24 max) + 2 enseignant. Salle de TD, cours, réunion : 3. Projet : 8. |",
        "| Wi-Fi | Nombre de bornes fixé par une **étude RSSI prédictive** (ci-dessous), validée par l'équipe. |",
        f"| Sécurité | {t['camera']} caméras IP, {t['badge']} badgeuses (salle serveur, 6 L.TECH, entrées, salles réseaux). |",
        f"| Téléphonie IP | 1 téléphone par bureau d'enseignant + l'accueil (secrétariat) : {res['telephones']} postes, sur la 2ᵉ prise du bureau. |",
        "| Adductions opérateur | **Deux entrées séparées** : FAI 1 façade ouest (L.TECH 02 du sous-sol, côté chaufferie), FAI 2 façade est (parking). |",
        "| Rocades | **Deux fibres OM4 par local, par deux chemins disjoints** (une par colonne montante). |", "",
        "## Résultats", "",
        f"- **{res['prises']} prises RJ45 Cat6A** : {t['usager']} usagers, {t['wifi']} bornes Wi-Fi, {t['camera']} caméras, {t['badge']} badgeuses.",
        f"- **{m(res['cable_cuivre_m'])} m de câble cuivre**, lien moyen {res['lien_moyen_m']} m, **lien le plus long {res['lien_max_m']} m** "
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
    L += ["", "Le local du RDC nord (`L.TECH`, ≈ 2 m²) est un placard : baie murale 24U, ventilation à prévoir. "
          "Le L.TECH 02 de l'étage reçoit la baie au sol 42U (aile sud, salles de TP).", "",
          "### Rocades (fibre OM4 12 brins)", "", "| Local | Voie | Chemin | Longueur |", "|---|---|---|---:|"]
    for r in res["rocades"]:
        L.append(f"| {r['local']} | {r['voie']} | {r['par']} | {r['longueur']:.0f} m |")
    L += ["", "Colonne **Nord** : à l'aplomb du L.TECH du RDC nord, depuis le vide sanitaire 01. Colonne **Sud** : à l'aplomb des L.TECH 02 du RDC et de l'étage, "
          "depuis le plafond du parking. La voie B d'un local passe toujours par l'autre colonne : une colonne coupée n'isole aucun local.", "",
          "### Adductions", "", "| Opérateur | Entrée | Longueur jusqu'à la salle serveur |", "|---|---|---:|"]
    for a in res["adductions"]:
        L.append(f"| {a['operateur']} | {a['entree']} | {a['longueur_interne']:.0f} m (dont 15 m jusqu'à la chambre de tirage) |")
    L += ["", "### Chemins de câbles (circulations et locaux)", "", "| Niveau | Dimension (mm) | Longueur |", "|---|---|---:|"]
    for c, d in res["chemins_de_cables_m"].items():
        for dim, v in d.items():
            L.append(f"| {NOMS[c]} | {dim} | {v} m |")
    L += ["", f"Dimension choisie pour un taux de remplissage ≤ 40 % (câble Cat6A Ø 7,5 mm). Dans les salles, le câble suit une goulotte périmétrique depuis la porte.", "",
          "## Étude Wi-Fi prédictive (RSSI)", "",
          f"Modèle multi-murs à {h['frequence_MHz']} MHz : PIRE {h['PIRE_dBm']:.0f} dBm, exposant {h['exposant']}, "
          f"mur porteur {h['affaiblissements_dB']['mur']:.0f} dB, cloison {h['affaiblissements_dB']['cloison']:.0f} dB, vitrage {h['affaiblissements_dB']['vitrage']:.0f} dB "
          "(parois lues sur le plan). Objectif : **≥ −67 dBm** (voix et vidéo) sur 98 % de chaque niveau et 90 % de chaque salle occupée. "
          "Une borne par salle de TP, de TD et de projet pour la capacité, deux pour l'amphithéâtre et S.Cours.", "",
          "| Niveau | Bornes | Surface couverte | ≥ −67 dBm | 2ᵉ borne ≥ −70 dBm (itinérance) |", "|---|---:|---:|---:|---:|"]
    for n in wifi["niveaux"]:
        s = n["stats"]
        nb = sum(b["niveau"] == n["code"] for b in wifi["bornes"])
        L.append(f"| {NOMS[n['code']]} | {nb} | {s['surface_cible_m2']} m² | {s['couverture_pct']} % | {s['itinerance_pct']} % |")
    L += ["", f"Plan de canaux : 12 canaux de 40 MHz à 5 GHz, {wifi['conflits_co_canal']} conflit co-canal (niveaux compris). "
          "Cartes : `wifi/N-1_rssi.png`, `wifi/N0_rssi.png`, `wifi/N1_rssi.png` ; liste des bornes : `wifi/bornes.csv`.", "",
          "## Fichiers", "",
          "| Fichier | Contenu |", "|---|---|",
          "| `plans/<niveau>_cablage.pdf` (.svg, .png) | Plan A3 de chaque niveau : prises, bornes, caméras, badgeuses, chemins de câbles, rocades, colonnes, salles teintées par local |",
          "| `synoptique.pdf` (.svg, .png) | Rocades, colonnes montantes, adductions, contenu de chaque baie |",
          "| `prises.csv` | Toutes les prises : repère (`N0-LT02-P017`), local, salle, type, usage, PoE, position, longueur |",
          "| `baies.csv`, `rocades.csv`, `resume.json` | Dimensionnement des baies, longueurs des rocades, synthèse |",
          "| `wifi/` | Étude RSSI : cartes de couverture, bornes et canaux |", "",
          "## Normes et règles appliquées", "",
          "- Câblage structuré ISO/IEC 11801-1 et EN 50173-1 : classe EA (Cat6A, 10GBASE-T), lien permanent ≤ 90 m, canal ≤ 100 m.",
          "- Installation EN 50174-2 : séparation courants forts / faibles, rayons de courbure, rebouchage coupe-feu des traversées.",
          "- Câbles Euroclasse Cca-s1b,d1,a1 (règlement CPR, établissement recevant du public).",
          "- Repérage TIA-606 : `<niveau>-LT<local>-P<numéro>`, la même étiquette sur la prise et au panneau de brassage.",
          "- Longueur d'un lien = 1,10 × cheminement sur le plan + 3 m de descentes + 2 m de lovage.", "",
          "## Limites et points à valider avec le client", "",
          "- Échelle mesurée sur le cartouche des plans : précision ±2 %. Les longueurs sont des estimations, à confirmer au relevé.",
          "- Étude Wi-Fi prédictive, faite sur plan : affaiblissements estimés d'après le trait des parois, pertes entre étages ignorées. Une mesure sur site (site survey) devra la confirmer.",
          "- Emplacement des chambres de tirage des deux opérateurs et accord pour faire passer les chemins de câbles en vide sanitaire et au plafond du parking.",
          "- Salle serveur dans J05 : cloison coupe-feu, plancher technique, détection de fuite (sous-sol), climatisation et réaffectation de la salle.",
          "- L'amphithéâtre de l'étage n'est accessible que par le bas : ses prises sont câblées depuis le RDC, par les gradins.",
          "- Les petites salles J02 à J04 et la partie restante de J05 sont comptées comme des salles de TD (3 prises), à confirmer selon leur usage.", ""]
    (OUT / "README.md").write_text("\n".join(L), encoding="utf-8")
    print(f"README.md : {len(L)} lignes")


if __name__ == "__main__":
    main()
