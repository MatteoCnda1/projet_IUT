#!/usr/bin/env python3
"""Points 03 et 05 : plan d'adressage IPv4/IPv6, architecture L2 et L3, zone Net Management du schéma.

Usage : python3 architecture/reseau/build.py   (après cablage/plan_cablage.py)
Entrées : donnees.py (source unique), architecture/Projet_Marseille_site.drawio, livrables/plan_cablage/resume.json
Sorties :
  architecture/Projet_Marseille_site.drawio   zone Net Management redessinée (pve-1 / pve-2 / witness), piles précisées
  architecture/architecture_l2.drawio, architecture_l3.drawio   schémas logiques modifiables
  livrables/plan_adressage/   plan_adressage.pdf (+ .html), vlans.csv, equipements.csv, interconnexions.csv
  livrables/architecture_l2/  architecture_l2.pdf (+ .html, .png)
  livrables/architecture_l3/  architecture_l3.pdf (+ .html, .png)
"""
import csv
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI))
import donnees as D  # noqa: E402
import documents  # noqa: E402
import schemas  # noqa: E402
from drawio import exporter  # noqa: E402

ROOT = ICI.parent.parent
ARCHI = ROOT / "architecture"
LIV = ROOT / "livrables"
PLAN = json.loads((LIV / "plan_cablage" / "resume.json").read_text(encoding="utf-8"))
CSS = (ROOT / "cablage" / "document.py").read_text(encoding="utf-8").split('CSS = """', 1)[1].split('"""', 1)[0]


def pdf(page, sortie):
    chrome = shutil.which("google-chrome") or shutil.which("chromium")
    if not chrome:
        print("  (pas de Chrome : PDF non produit)")
        return
    with tempfile.TemporaryDirectory() as prof:
        subprocess.run([chrome, "--headless=new", "--no-sandbox", "--disable-gpu", f"--user-data-dir={prof}", "--no-pdf-header-footer",
                        f"--print-to-pdf={sortie}", page.as_uri()], check=True, capture_output=True, timeout=180)


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
    print("Contrôles d'adressage : OK (aucun chevauchement, résumés exacts)")
    principal = ARCHI / "Projet_Marseille_site.drawio"
    n = schemas.patcher_principal(principal, principal)
    print(f"Schéma principal : zone Net Management redessinée ({n} anciens éléments retirés)")
    schemas.ecrire_schemas(ARCHI)
    out = {k: LIV / k for k in ("plan_adressage", "architecture_l2", "architecture_l3")}
    for d in out.values():
        d.mkdir(parents=True, exist_ok=True)
    exporter(ARCHI / "architecture_l2.drawio", out["architecture_l2"] / "architecture_l2.png", echelle=1.5)
    exporter(ARCHI / "architecture_l3.drawio", out["architecture_l3"] / "architecture_l3.png", echelle=1.5)
    exporter(principal, ARCHI / "Projet_Marseille_site.png", echelle=0.3)
    from PIL import Image  # recadrage de la zone NM pour le document L2
    im = Image.open(ARCHI / "Projet_Marseille_site.png")
    W, H = im.size
    x0, y0, x1, y1 = -2930, -1750, 8210, 4955
    sx, sy = W / (x1 - x0 + 20), H / (y1 - y0 + 20)
    im.crop((int((4280 - x0) * sx), int((1655 - y0) * sy), W, H)).save(out["architecture_l2"] / "nm_zone.png")
    csvs(out["plan_adressage"])
    for cle, fonction, args in (("plan_adressage", documents.doc_adressage, (CSS, PLAN)),
                                ("architecture_l2", documents.doc_l2, (CSS, PLAN)),
                                ("architecture_l3", documents.doc_l3, (CSS,))):
        page = out[cle] / f"{cle}.html"
        page.write_text(fonction(*args), encoding="utf-8")
        pdf(page, out[cle] / f"{cle}.pdf")
        print(f"  {page.relative_to(ROOT)} -> .pdf")
    regen = ("**Version 2** (après l'audit du 15/11/2026) : changements repérés « v2 » dans le document, détail par constat dans "
             "[`../audit/traitement_audit.pdf`](../audit/README.md). Version 1 : `livrables/archives/v1_2026-11-15/`.\n\n"
             "Régénérer : `python3 architecture/reseau/build.py` (source unique : `architecture/reseau/donnees.py`).")
    readme(out["plan_adressage"], "Plan d'adressage IPv4 et IPv6 (point 05)", "Adressage",
           "Document principal : **[plan_adressage.pdf](plan_adressage.pdf)**. Tables : `vlans.csv`, `equipements.csv`, `interconnexions.csv`.\n\n"
           "| | |\n|---|---|\n| IPv4 privé | 10.13.0.0/16 (bloc 1 : 10.13.16.0/20, bloc 2 : 10.13.32.0/20, datacenter 10.13.48.0/22, tier 0 10.13.52.0/27, admin 10.13.56.0/21, Wi-Fi 10.13.64.0/18) |\n"
           "| IPv4 public | 139.124.112.0/24 dans le bloc AMU 139.124.0.0/16 (à confirmer par la DSI) |\n"
           "| IPv6 | 2001:660:5402:4000::/52 dans 2001:660:5402::/48 (Luminy) ; VLAN *n* → 2001:660:5402:4*nnn*::/64 |\n"
           f"| VLAN | {len([v for v in D.VLANS if v < 1000])} VLAN + {len(D.TRANSITS)} transits, 5 VRF (USR, IOT, GST, SRV, ADM) + zone tier 0 (VLAN 310) |\n\n" + regen)
    readme(out["architecture_l2"], "Architecture de niveau 2 (points 03 et 06)", "Archi L2",
           "Document principal : **[architecture_l2.pdf](architecture_l2.pdf)** : VLAN par équipement, agrégats et trunks, piles et StackWise Virtual, "
           "Rapid PVST+, profils de ports 802.1X/MAB, sécurité L2, SSID et contrôleurs Wi-Fi, zone Net Management (2 nœuds Proxmox + témoin, réseaux ipmi / mgmt / cluster / "
           "workload / réplication), clusters DT et DMZ.\n\nSchéma modifiable : `architecture/architecture_l2.drawio`. " + regen)
    readme(out["architecture_l3"], "Architecture de niveau 3 (points 03, 05 et 07)", "Archi L3",
           "Document principal : **[architecture_l3.pdf](architecture_l3.pdf)** : VRF-lite, matrice des flux entre zones, OSPFv3 par VRF, "
           "routes statiques vers les pare-feu, zone tier 0, politique d'inspection et inspection TLS, eBGP double opérateur avec annonce conditionnelle, "
           "SD-WAN FortiGate, NAT et VIP, IPv6 (SLAAC/DHCPv6, NPTv6 de secours), MTU, journalisation légale, services IP, extraits de configuration, tests de bascule.\n\nSchéma modifiable : `architecture/architecture_l3.drawio`. " + regen)


if __name__ == "__main__":
    main()
