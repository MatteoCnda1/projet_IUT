#!/usr/bin/env python3
"""Points 03 et 05 : plan d'adressage IPv4/IPv6, architecture L2 et L3, zone Net Management du schéma.

Usage : python3 architecture/reseau/build.py   (après cablage/plan_cablage.py)
Entrées : donnees.py (source unique), architecture/Projet_Marseille_site.png, livrables/plan_cablage/resume.json
Le schéma principal architecture/Projet_Marseille_site.drawio (+ .png) n'est pas réécrit : c'est le schéma de référence de
l'équipe, celui que GesTT référence (commit 7e1db0b). Il se modifie à la main dans draw.io, puis s'exporte en PNG.
Sorties :
  architecture/architecture_l2.drawio, architecture_l3.drawio   schémas logiques modifiables
  livrables/plan_adressage/   plan_adressage.pdf (+ .html), vlans.csv, equipements.csv, interconnexions.csv
  livrables/architecture_l2/  architecture_l2.pdf (+ .html, .png)
  livrables/architecture_l3/  architecture_l3.pdf (+ .html, .png)
"""
import csv
import json
import sys
from pathlib import Path

ICI = Path(__file__).resolve().parent
ROOT = ICI.parent.parent
sys.path.insert(0, str(ICI))
sys.path.insert(1, str(ROOT))
import donnees as D  # noqa: E402
import documents  # noqa: E402
import schemas  # noqa: E402
from commun import charte as CH  # noqa: E402
from drawio import exporter  # noqa: E402

ARCHI = ROOT / "architecture"
LIV = ROOT / "livrables"
PLAN = json.loads((LIV / "plan_cablage" / "resume.json").read_text(encoding="utf-8"))


def csvs(out):
    with open(out / "vlans.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["vlan", "nom", "vrf", "ipv4", "passerelle_v4", "hotes", "ipv6", "passerelle_v6", "route_par", "usage"])
        for vid in sorted(D.VLANS):
            v = D.VLANS[vid]
            w.writerow([vid, v["nom"], v["vrf"] or "", v["v4"] or "", v["gw4"] or "", v["taille"] or "", v["v6"] or "",
                        v["gw6"] or "", v["gw_eq"] or "", v["usage"]])
    with open(out / "equipements.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["vlan", "nom_vlan", "equipement", "ipv4", "ipv6"])
        for vid in sorted(D.HOTES):
            for nom, fin in D.HOTES[vid]:
                if isinstance(fin, str):
                    w.writerow([vid, D.VLANS[vid]["nom"], nom, f"plage .{fin}", f"plage ::{fin}"])
                else:
                    a4, a6 = D.adresse(vid, fin)
                    w.writerow([vid, D.VLANS[vid]["nom"], nom, a4, a6 or ""])
        for vid in sorted(v for v in D.VLANS if v >= 1000):
            v = D.VLANS[vid]
            for cote in ("a", "b"):
                w.writerow([vid, v["nom"], v[cote][0], v[cote][1], v[cote][2]])
        for q in D.P2P:
            w.writerow(["", q["sous_if"], "CL", q["cl4"], q["cl6"]])
            w.writerow(["", q["sous_if"], f"DL-B{q['bloc']}", q["dl4"], q["dl6"]])
        for nom, a4, a6 in D.BOUCLES:
            w.writerow(["", "Loopback0", nom, a4, a6])
    with open(out / "interconnexions.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["prefixe", "usage", "detail"])
        w.writerows(D.PUBLIC)
        for q in D.P2P:
            w.writerow([q["v4"], f"{q['sous_if']} CL <-> DL-B{q['bloc']} (VRF {q['vrf']})", q["v6"]])


def readme(dossier, titre, onglet, corps):
    (dossier / "README.md").write_text(f"# {titre}\n<!-- onglet: {onglet} -->\n\n{corps}\n", encoding="utf-8")


def main():
    D.verifier()
    print("Contrôles d'adressage : OK (aucun chevauchement, résumés exacts, chaque adresse dans son sous-réseau)")
    acces = {n: x["switchs_48p"] for n, x in documents.besoins(PLAN).items()}
    schemas.ecrire_schemas(ARCHI, acces)
    out = {k: LIV / k for k in ("plan_adressage", "architecture_l2", "architecture_l3")}
    for d in out.values():
        d.mkdir(parents=True, exist_ok=True)
    exporter(ARCHI / "architecture_l2.drawio", out["architecture_l2"] / "architecture_l2.png", echelle=1.5)
    exporter(ARCHI / "architecture_l3.drawio", out["architecture_l3"] / "architecture_l3.png", echelle=1.5)
    # Schéma principal : référence de l'équipe et de GesTT, laissé tel quel ; seule la zone NM en est recadrée pour le L2
    from PIL import Image
    im = Image.open(ARCHI / "Projet_Marseille_site.png")
    W, H = im.size
    x0, y0, x1, y1 = -2930, -1750, 8210, 4955
    sx, sy = W / (x1 - x0 + 20), H / (y1 - y0 + 20)
    im.crop((int((4280 - x0) * sx), int((1655 - y0) * sy), W, H)).save(out["architecture_l2"] / "nm_zone.png")
    csvs(out["plan_adressage"])
    for cle, fonction in (("plan_adressage", documents.doc_adressage), ("architecture_l2", documents.doc_l2),
                          ("architecture_l3", documents.doc_l3)):
        page = out[cle] / f"{cle}.html"
        CH.ecrire_et_imprimer(fonction(PLAN, out[cle]), page, out[cle] / f"{cle}.pdf")
        print(f"  {page.relative_to(ROOT)} -> .pdf")
    version = (f"**Version {CH.VERSION[1:]} — {CH.DATE_VERSION}** : {{}}, repérés « v2.1 » dans le document (les changements de la v2, "
               "après l'audit du 15/11/2026, restent repérés « v2 » ; détail par constat dans "
               f"[`../audit/traitement_audit.pdf`](../audit/traitement_audit.pdf)). Version précédente : `{CH.ARCHIVE_PRECEDENTE}`.\n\n"
               "Régénérer : `python3 architecture/reseau/build.py` (source unique : `architecture/reseau/donnees.py` ; "
               "documents : `documents.py`, schémas : `schemas.py`).")
    nb = f"{len([v for v in D.VLANS if v < 1000])} VLAN + {len(D.TRANSITS)} transits"
    readme(out["plan_adressage"], "Plan d'adressage IPv4 et IPv6 (point 05)", "Adressage",
           "VLAN, sous-réseaux IPv4 et IPv6, passerelles, interconnexions et adresses fixes du bâtiment, avec les tables qui en sont tirées.\n\n"
           "| Document | Réf. | Contenu |\n|---|---|---|\n"
           "| **[plan_adressage.pdf](plan_adressage.pdf)** | RLI-ETU-003 | Principes, blocs attribués, table des VLAN et dimensionnement, "
           "interconnexions, adresses fixes, résumés par VRF, réserves |\n"
           f"| `vlans.csv` | — | {nb} : VRF, IPv4, IPv6, passerelles, usage |\n"
           "| `equipements.csv` | — | Adresses fixes des équipements (IPv4 et IPv6), transits, liens point à point, boucles |\n"
           "| `interconnexions.csv` | — | Bloc public 139.124.112.0/24 et liens cœur-distribution |\n\n"
           "IPv4 privé 10.13.0.0/16, public 139.124.112.0/24 (bloc AMU, à confirmer par la DSI), IPv6 2001:660:5402:4000::/52 "
           "(VLAN *n* → 2001:660:5402:4*nnn*::/64), 5 VRF (USR, IOT, GST, SRV, ADM) et une zone tier 0 (VLAN 310).\n\n"
           + version.format(documents.CHANGEMENTS_ADRESSAGE))
    readme(out["architecture_l2"], "Architecture de niveau 2 (points 03 et 06)", "Archi L2",
           "Architecture de niveau 2 du bâtiment : VLAN, agrégats, piles, Spanning Tree, ports d'accès et zone Net Management.\n\n"
           "| Document | Réf. | Contenu |\n|---|---|---|\n"
           "| **[architecture_l2.pdf](architecture_l2.pdf)** | RLI-ETU-004 | VLAN par équipement, agrégats et trunks, piles et StackWise "
           "Virtual, Rapid PVST+, profils de ports 802.1X et MAB, sécurité de niveau 2, SSID et contrôleurs Wi-Fi, zone Net Management "
           "(2 nœuds Proxmox et un témoin), clusters DT et DMZ, enregistreur vidéo |\n"
           "| `architecture_l2.png`, `nm_zone.png` | — | Schéma de niveau 2 et zone Net Management (schémas modifiables : "
           "`architecture/architecture_l2.drawio`, `architecture/Projet_Marseille_site.drawio`) |\n\n"
           + version.format(documents.CHANGEMENTS_L2))
    readme(out["architecture_l3"], "Architecture de niveau 3 (points 03, 05 et 07)", "Archi L3",
           "Architecture de niveau 3 du bâtiment : VRF, routage, bordure, NAT, filtrage entre zones et services IP.\n\n"
           "| Document | Réf. | Contenu |\n|---|---|---|\n"
           "| **[architecture_l3.pdf](architecture_l3.pdf)** | RLI-ETU-005 | VRF-lite et zone tier 0, matrice résumée des flux, OSPFv3 par "
           "VRF, routes statiques vers les pare-feu, politique d'inspection et inspection TLS, eBGP à deux opérateurs avec annonce "
           "conditionnelle, SD-WAN, NAT et VIP, IPv6 (SLAAC, DHCPv6, NPTv6 de secours), MTU, services IP, journalisation légale, "
           "extraits de configuration, tests de bascule |\n"
           "| `architecture_l3.png` | — | Schéma de niveau 3 (modifiable : `architecture/architecture_l3.drawio`) |\n\n"
           + version.format(documents.CHANGEMENTS_L3))


if __name__ == "__main__":
    main()
