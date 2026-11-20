#!/usr/bin/env python3
"""Contrôles de cohérence du dépôt (job « Cohérence » de la CI, utilisable aussi en local).

    python3 outils/ci/verifier_coherence.py              tous les contrôles
    python3 outils/ci/verifier_coherence.py adressage    un ou plusieurs contrôles (voir --liste)
    python3 outils/ci/verifier_coherence.py --liste

Bibliothèque standard seulement : rien à installer. Code retour 0 si tout passe, 1 s'il y a au moins une erreur (✘).
Les avertissements (⚠) ne bloquent pas.

Les sources Python du projet ne sont pas importées (elles chargent matplotlib, etc.) : quand un contrôle a besoin d'une
constante (zones de la matrice des flux, blocs d'adresses), il la lit dans le code avec le module ast.

Ajouter un contrôle : écrire une fonction `def controle_xxx(r):` décorée par `@controle("xxx", "Titre")`, qui appelle
r.ok(...), r.erreur(message, fichier, ligne) ou r.avert(...). Voir outils/ci/README.md.
"""
import ast
import csv
import ipaddress as ip
import json
import re
import sys
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sortie_ci import RACINE, Rapport, fichiers_suivis  # noqa: E402

CONTROLES = []


def controle(nom, titre):
    def deco(f):
        CONTROLES.append((nom, titre, f))
        return f
    return deco


# ---------------------------------------------------------------------------
# Outils
# ---------------------------------------------------------------------------
_SUIVIS = None


def suivis():
    """Fichiers suivis par git (ou tous les fichiers du disque hors d'un dépôt git), en chemins relatifs."""
    global _SUIVIS
    if _SUIVIS is None:
        liste = fichiers_suivis()
        if liste is None:
            liste = [str(p.relative_to(RACINE)) for p in RACINE.rglob("*") if p.is_file() and ".git" not in p.parts]
        _SUIVIS = liste
    return _SUIVIS


def lire_csv(chemin):
    with open(RACINE / chemin, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def lire_json(chemin):
    return json.loads((RACINE / chemin).read_text(encoding="utf-8"))


def constantes(chemin, *noms):
    """Valeurs littérales de variables globales d'un fichier Python, lues sans l'exécuter.

    ip.ip_network("10.13.0.0/16") est rendu sous la forme de sa chaîne. Une variable absente ou non littérale vaut None."""
    arbre = ast.parse((RACINE / chemin).read_text(encoding="utf-8"))
    out = dict.fromkeys(noms)
    for noeud in arbre.body:
        if isinstance(noeud, ast.Assign) and len(noeud.targets) == 1 and isinstance(noeud.targets[0], ast.Name):
            nom = noeud.targets[0].id
            if nom in out:
                val = noeud.value
                if isinstance(val, ast.Call) and val.args and isinstance(val.args[0], ast.Constant):
                    val = val.args[0]  # ip.ip_network("...") -> "..."
                try:
                    out[nom] = ast.literal_eval(val)
                except ValueError:
                    out[nom] = None
    return out


def noeud_global(chemin, nom):
    """Nœud ast de la valeur affectée à une variable globale (ou None)."""
    arbre = ast.parse((RACINE / chemin).read_text(encoding="utf-8"))
    for noeud in arbre.body:
        if isinstance(noeud, ast.Assign) and any(isinstance(t, ast.Name) and t.id == nom for t in noeud.targets):
            return noeud.value
    return None


ESPACES = "[   ]"
MONTANT = rf"\d{{1,3}}(?:{ESPACES}\d{{3}})*"


def en_entier(texte):
    return int(re.sub(ESPACES, "", texte))


def fr(n):
    return f"{n:,}".replace(",", " ")


def ligne_de(texte, position):
    return texte.count("\n", 0, position) + 1


# ---------------------------------------------------------------------------
# 1. Plan d'adressage
# ---------------------------------------------------------------------------
ADR = "livrables/plan_adressage"
DONNEES = "architecture/reseau/donnees.py"
BLOC_DMZ = ip.ip_network("172.16.13.0/24")  # DMZ privée (même règle que donnees.verifier())


def _reseau(texte, strict=True):
    try:
        return ip.ip_network(texte, strict=strict)
    except ValueError:
        return None


@controle("adressage", "Plan d'adressage (livrables/plan_adressage/*.csv)")
def controle_adressage(r):
    c = constantes(DONNEES, "V6", "P6_SITE", "P4_PRIVE", "P4_PUBLIC")
    p4_prive, p4_public, p6_site = (ip.ip_network(c[k]) for k in ("P4_PRIVE", "P4_PUBLIC", "P6_SITE"))
    v6 = c["V6"]
    f_vlans, f_equip, f_inter = f"{ADR}/vlans.csv", f"{ADR}/equipements.csv", f"{ADR}/interconnexions.csv"

    # --- vlans.csv
    vlans, noms, reseaux4 = {}, {}, []
    err0 = r.erreurs
    for i, v in enumerate(lire_csv(f_vlans), start=2):
        try:
            vid = int(v["vlan"])
        except ValueError:
            r.erreur(f"numéro de VLAN invalide « {v['vlan']} »", f_vlans, i)
            continue
        if vid in vlans:
            r.erreur(f"VLAN {vid} en double", f_vlans, i)
        if v["nom"] in noms:
            r.erreur(f"nom « {v['nom']} » en double (VLAN {noms[v['nom']]} et {vid})", f_vlans, i)
        noms[v["nom"]] = vid
        v["ligne"], v["net4"], v["net6"] = i, None, None
        vlans[vid] = v
        if v["ipv4"]:
            net = _reseau(v["ipv4"])
            if net is None:
                r.erreur(f"VLAN {vid} : « {v['ipv4']} » n'est pas une adresse de réseau IPv4 valide", f_vlans, i)
            else:
                v["net4"] = net
                reseaux4.append((net, f"VLAN {vid} {v['nom']}"))
                if not (net.subnet_of(p4_prive) or net.subnet_of(BLOC_DMZ)):
                    r.erreur(f"VLAN {vid} : {net} hors des blocs privés du site ({p4_prive}, {BLOC_DMZ})", f_vlans, i)
                if v["hotes"] and int(v["hotes"]) != net.num_addresses - 2:
                    r.erreur(f"VLAN {vid} : {v['hotes']} hôtes annoncés, {net.num_addresses - 2} dans un /{net.prefixlen}", f_vlans, i)
                if v["passerelle_v4"]:
                    gw = ip.ip_address(v["passerelle_v4"])
                    if gw not in net or gw in (net.network_address, net.broadcast_address):
                        r.erreur(f"VLAN {vid} : passerelle {gw} invalide dans {net}", f_vlans, i)
                    elif gw != net.network_address + 1:
                        r.erreur(f"VLAN {vid} : passerelle {gw} ≠ première adresse {net.network_address + 1} "
                                 "(convention de donnees.py)", f_vlans, i)
                if bool(v["passerelle_v4"]) != bool(v["route_par"]):
                    r.erreur(f"VLAN {vid} : passerelle et « route_par » doivent être renseignées ensemble", f_vlans, i)
        if v["ipv6"]:
            net6 = _reseau(v["ipv6"])
            if net6 is None:
                r.erreur(f"VLAN {vid} : « {v['ipv6']} » n'est pas un préfixe IPv6 valide", f_vlans, i)
                continue
            v["net6"] = net6
            if not net6.subnet_of(p6_site):
                r.erreur(f"VLAN {vid} : {net6} hors du préfixe du site {p6_site}", f_vlans, i)
            if vid < 1000 and net6 != ip.ip_network(f"{v6}4{vid:03d}::/64"):
                r.erreur(f"VLAN {vid} : préfixe {net6} ≠ {v6}4{vid:03d}::/64 (règle « VLAN n → 4nnn::/64 »)", f_vlans, i)
            if v["passerelle_v6"]:
                gw6 = ip.ip_address(v["passerelle_v6"])
                if gw6 not in net6 or gw6 != net6.network_address + 1:
                    r.erreur(f"VLAN {vid} : passerelle IPv6 {gw6} ≠ première adresse de {net6}", f_vlans, i)
    if r.erreurs == err0:
        r.ok(f"vlans.csv : {len(vlans)} VLAN, numéros et noms uniques, passerelles et préfixes conformes")

    # --- interconnexions.csv
    err0 = r.erreurs
    p2p = {}
    for i, lg in enumerate(lire_csv(f_inter), start=2):
        net = _reseau(lg["prefixe"])
        if net is None:
            r.erreur(f"« {lg['prefixe']} » n'est pas un préfixe valide", f_inter, i)
            continue
        sous_if = lg["usage"].split()[0]
        if sous_if.startswith("Po"):
            if not net.subnet_of(p4_prive):
                r.erreur(f"{net} ({sous_if}) hors de {p4_prive}", f_inter, i)
            net6 = _reseau(lg["detail"])
            if net6 is None or not net6.subnet_of(p6_site):
                r.erreur(f"{sous_if} : préfixe IPv6 « {lg['detail']} » invalide ou hors de {p6_site}", f_inter, i)
            if sous_if in p2p:
                r.erreur(f"sous-interface {sous_if} en double", f_inter, i)
            p2p[sous_if] = (net, net6)
        elif not net.subnet_of(p4_public):
            r.erreur(f"{net} hors du bloc public {p4_public}", f_inter, i)
        reseaux4.append((net, f"{lg['prefixe']} ({lg['usage'][:40]})"))
    if r.erreurs == err0:
        r.ok(f"interconnexions.csv : {len(p2p)} liens point à point et blocs publics valides")

    # --- chevauchements (VLAN + interconnexions)
    err0 = r.erreurs
    for k, (a, na) in enumerate(reseaux4):
        for b, nb in reseaux4[k + 1:]:
            if a.overlaps(b):
                r.erreur(f"chevauchement : {na} ({a}) et {nb} ({b})", f"{ADR}/")
    if r.erreurs == err0:
        r.ok(f"aucun chevauchement entre les {len(reseaux4)} réseaux IPv4")

    # --- equipements.csv
    err0 = r.erreurs
    vus4, vus6, vus_nom = {}, {}, set()
    equip = lire_csv(f_equip)
    for i, e in enumerate(equip, start=2):
        quoi = f"{e['nom_vlan']} / {e['equipement']}"
        net4 = net6 = None
        if e["vlan"]:
            vid = int(e["vlan"])
            if vid not in vlans:
                r.erreur(f"{quoi} : VLAN {vid} absent de vlans.csv", f_equip, i)
                continue
            if e["nom_vlan"] != vlans[vid]["nom"]:
                r.erreur(f"VLAN {vid} nommé « {e['nom_vlan']} » ici et « {vlans[vid]['nom']} » dans vlans.csv", f_equip, i)
            net4, net6 = vlans[vid]["net4"], vlans[vid]["net6"]
            if (vid, e["equipement"]) in vus_nom:
                r.erreur(f"{quoi} : équipement en double dans le VLAN {vid}", f_equip, i)
            vus_nom.add((vid, e["equipement"]))
        elif e["nom_vlan"].startswith("Po"):
            if e["nom_vlan"] not in p2p:
                r.erreur(f"{quoi} : sous-interface absente de interconnexions.csv", f_equip, i)
                continue
            net4, net6 = p2p[e["nom_vlan"]]
        elif e["nom_vlan"].startswith("Loopback"):
            net4, net6 = p4_prive, p6_site
        else:
            r.erreur(f"{quoi} : ni VLAN, ni lien point à point, ni boucle locale", f_equip, i)
            continue

        a4 = a6 = None
        # IPv4 : adresse, adresse/32 (boucles) ou « plage .a-b »
        m = re.fullmatch(r"plage \.(\d+)-(\d+)", e["ipv4"])
        if m and net4 is not None:
            base = int(net4.network_address) & ~0xFF
            debut, fin = (ip.ip_address(base + int(x)) for x in m.groups())
            if debut not in net4 or fin not in net4:
                relu = f"{net4.network_address + int(m[1])}–{net4.network_address + int(m[2])}"
                r.erreur(f"{quoi} : « {e['ipv4']} » se lit {debut}–{fin}, hors du sous-réseau {net4} "
                         f"(si ce sont des décalages dans le sous-réseau : {relu} ; écrire la plage en adresses complètes)",
                         f_equip, i)
        elif e["ipv4"]:
            try:
                a4 = ip.ip_interface(e["ipv4"]).ip
            except ValueError:
                r.erreur(f"{quoi} : « {e['ipv4']} » n'est pas une adresse IPv4", f_equip, i)
            if a4 is not None and net4 is not None:
                if a4 not in net4:
                    # Terminaison prise pour un décalage alors qu'elle était absolue dans le /24 (ou l'inverse) ?
                    absolue = ip.ip_address((int(net4.network_address) & ~0xFF) + int(a4) - int(net4.network_address))
                    piste = f" ({absolue} si la terminaison {int(absolue) & 0xFF} est absolue dans le /24)" if absolue in net4 else ""
                    r.erreur(f"{quoi} : {a4} hors du sous-réseau {net4}{piste}", f_equip, i)
                    a4 = None
                elif net4.prefixlen < 31 and a4 in (net4.network_address, net4.broadcast_address):
                    r.erreur(f"{quoi} : {a4} est l'adresse de réseau ou de diffusion de {net4}", f_equip, i)
            if a4 is not None:
                if a4 in vus4:
                    r.erreur(f"{quoi} : {a4} déjà attribuée ({vus4[a4]})", f_equip, i)
                vus4[a4] = quoi
        # IPv6
        if e["ipv6"] and not e["ipv6"].startswith("plage"):
            try:
                a6 = ip.ip_interface(e["ipv6"]).ip
            except ValueError:
                r.erreur(f"{quoi} : « {e['ipv6']} » n'est pas une adresse IPv6", f_equip, i)
            if a6 is not None and net6 is not None and a6 not in net6:
                r.erreur(f"{quoi} : {a6} hors du préfixe {net6}", f_equip, i)
                a6 = None
            if a6 is not None:
                if a6 in vus6:
                    r.erreur(f"{quoi} : {a6} déjà attribuée ({vus6[a6]})", f_equip, i)
                vus6[a6] = quoi
        # Convention de donnees.py : même terminaison en IPv4 et en IPv6, hors liens /31 - /127 et hors passerelles
        # (pour elles, la convention « première adresse : .1 / ::1 » prime ; leur IPv6 est contrôlée plus bas)
        passerelle = bool(e["vlan"]) and str(a4) == vlans[int(e["vlan"])]["passerelle_v4"]
        if a4 is not None and a6 is not None and not e["nom_vlan"].startswith("Po") and not passerelle \
                and e["ipv6"].split("/")[0].rsplit(":", 1)[1] != str(a4).rsplit(".", 1)[1]:
            r.erreur(f"{quoi} : terminaisons différentes en IPv4 ({a4}) et en IPv6 ({a6}) "
                     "(convention de donnees.py)", f_equip, i)
        e["a4"], e["a6"] = a4, a6

    # Passerelles : l'équipement qui porte la passerelle IPv4 doit porter la passerelle IPv6 annoncée dans vlans.csv
    for i, e in enumerate(equip, start=2):
        if not e["vlan"] or e.get("a4") is None:
            continue
        v = vlans.get(int(e["vlan"]))
        if v and v["passerelle_v4"] and str(e["a4"]) == v["passerelle_v4"] and v["passerelle_v6"] and e.get("a6") is not None \
                and e["a6"] != ip.ip_address(v["passerelle_v6"]):
            r.erreur(f"VLAN {e['vlan']} : la passerelle {e['a4']} ({e['equipement']}) a l'IPv6 {e['a6']} ici, "
                     f"mais vlans.csv (l. {v['ligne']}) annonce la passerelle IPv6 {v['passerelle_v6']}", f_equip, i)
    if r.erreurs == err0:
        r.ok(f"equipements.csv : {len(equip)} lignes, adresses dans leur sous-réseau, sans doublon, passerelles cohérentes")
    return vlans


# ---------------------------------------------------------------------------
# 2. Matrice des flux
# ---------------------------------------------------------------------------
FLUX = "securite/flux.py"
MATRICE = "livrables/securite/matrice_flux.csv"
SERVICE = re.compile(r"(tcp|udp)/(\d+)(?:-(\d+))?|(icmp|icmpv6)/[a-z-]+|tout")


@controle("flux", "Matrice des flux (livrables/securite/matrice_flux.csv)")
def controle_flux(r):
    c = constantes(FLUX, "ZONES", "INTERNES", "PROPOSITIONS")
    zones, internes, propositions = c["ZONES"] or {}, set(c["INTERNES"] or ()), c["PROPOSITIONS"] or {}
    vrf_proposees = {p["vrf"] for p in propositions.values()}
    vlans = {int(v["vlan"]): v for v in lire_csv(f"{ADR}/vlans.csv")}
    vrf_plan = {v["vrf"] for v in vlans.values() if v["vrf"]}

    # Objets de flux.py et VLAN qu'ils citent : V(110, 111), H(400, 10), ("passerelle", 514), GW_USR
    objets = noeud_global(FLUX, "OBJETS")
    noms_objets = {k.value for k in objets.keys} if isinstance(objets, ast.Dict) else set()
    cites = []  # (vlan, terminaison ou None, ligne dans flux.py)
    for racine in (objets, noeud_global(FLUX, "GW_USR")):
        for n in ast.walk(racine) if racine is not None else ():
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in ("V", "H") and n.args:
                vals = [a.value for a in n.args if isinstance(a, ast.Constant)]
                if n.func.id == "V":
                    cites += [(v, None, n.lineno) for v in vals]
                else:
                    cites += [(vals[0], f, n.lineno) for f in vals[1:]]
            elif isinstance(n, ast.Tuple) and n.elts and isinstance(n.elts[0], ast.Constant) and n.elts[0].value == "passerelle":
                if isinstance(n.elts[1], ast.Constant):
                    cites.append((n.elts[1].value, None, n.lineno))
            elif isinstance(n, ast.comprehension) and isinstance(n.iter, ast.Tuple):  # GW_USR : for vid in (110, ...)
                cites += [(e.value, None, n.iter.lineno) for e in n.iter.elts if isinstance(e, ast.Constant)]

    err0 = r.erreurs
    equip = lire_csv(f"{ADR}/equipements.csv")
    adresses = {e["ipv4"] for e in equip}
    plages = [(int(e["vlan"]), *map(int, re.fullmatch(r"plage \.(\d+)-(\d+)", e["ipv4"]).groups()))
              for e in equip if e["ipv4"].startswith("plage")]
    for vid, fin, ligne in cites:
        if vid in propositions:
            continue
        if vid not in vlans:
            r.erreur(f"objet de flux.py : VLAN {vid} absent du plan d'adressage", FLUX, ligne)
            continue
        if fin is None or not vlans[vid]["ipv4"]:
            continue
        net = ip.ip_network(vlans[vid]["ipv4"])
        if isinstance(fin, str):  # plage d'hôtes « 21-28 »
            continue
        k = fin if fin < net.num_addresses else fin - (int(net.network_address) & 0xFF)  # même règle que donnees.adresse()
        a4 = str(net.network_address + k)
        if a4 not in adresses and not any(p[0] == vid and p[1] <= fin <= p[2] for p in plages):
            r.erreur(f"objet de flux.py : hôte {a4} (VLAN {vid}, terminaison {fin}) absent de equipements.csv", FLUX, ligne)
    for vid in sorted(propositions):
        if vid in vlans:
            r.erreur(f"VLAN {vid} proposé dans flux.py (PROPOSITIONS) mais déjà au plan d'adressage : retirer la proposition", FLUX)
    for vrf in sorted(vrf_plan - set(zones)):
        r.erreur(f"VRF {vrf} du plan d'adressage sans zone de sécurité dans flux.py (ZONES)", FLUX)
    if r.erreurs == err0:
        r.ok(f"flux.py : {len(noms_objets)} objets, {len(cites)} références de VLAN ou d'hôte, toutes au plan d'adressage")

    err0 = r.erreurs
    lignes = lire_csv(MATRICE)
    zones_vues = set()
    for i, lg in enumerate(lignes, start=2):
        for cote in ("source", "destination"):
            obj, z = lg[cote], lg[f"zone_{cote}"]
            if obj != "tout" and obj not in noms_objets:
                r.erreur(f"{lg['id']} : objet {cote} « {obj} » inconnu de flux.py", MATRICE, i)
            if z == "tout":
                continue
            zones_vues.add(z)
            if z not in zones:
                r.erreur(f"{lg['id']} : zone {cote} « {z} » inconnue (ZONES de flux.py)", MATRICE, i)
            elif z in internes and z not in vrf_plan and z not in vrf_proposees:
                r.erreur(f"{lg['id']} : zone interne « {z} » sans aucun VLAN au plan d'adressage", MATRICE, i)
        for s in lg["services"].split():
            m = SERVICE.fullmatch(s)
            if not m:
                r.erreur(f"{lg['id']} : service « {s} » mal formé (attendu tcp/443, udp/16384-32767, icmp/echo-request, tout)",
                         MATRICE, i)
            elif m[2] and not (1 <= int(m[2]) <= int(m[3] or m[2]) <= 65535):
                r.erreur(f"{lg['id']} : ports « {s} » hors de 1-65535 ou plage inversée", MATRICE, i)
        if lg["action"] not in ("autoriser", "refuser"):
            r.erreur(f"{lg['id']} : action « {lg['action']} » (attendu autoriser ou refuser)", MATRICE, i)
    if r.erreurs == err0:
        r.ok(f"matrice_flux.csv : {len(lignes)} lignes, zones {', '.join(sorted(zones_vues))} et objets connus, services valides")
    for z in sorted(zones_vues & vrf_proposees - vrf_plan):
        vids = ", ".join(str(k) for k, p in propositions.items() if p["vrf"] == z)
        r.avert(f"zone « {z} » : proposition (VLAN {vids} de flux.py), pas encore au plan d'adressage", MATRICE)


# ---------------------------------------------------------------------------
# 3. Montants cités dans les README
# ---------------------------------------------------------------------------
CHIFFRAGE = "chiffrage/estimation.json"
CHIFFRAGE_V1 = "livrables/archives/v1_2026-11-15/chiffrage/estimation.json"
ENERGIE = "livrables/energie_refroidissement/resume.json"
N = rf"{MONTANT}{ESPACES}?€"  # un montant quelconque
M = rf"(?P<m>{MONTANT}){ESPACES}?€"  # le montant contrôlé

# (fichier, motif où {M} est le montant contrôlé, fichier JSON, chemin de la clé, libellé)
CITATIONS = [
    ("README.md", rf"\|\s*CAPEX[^|\n]*\|\s*{M}", CHIFFRAGE, "capex", "CAPEX"),
    ("README.md", rf"\|\s*OPEX annuel[^|\n]*\|\s*{M}", CHIFFRAGE, "opex_total", "OPEX annuel"),
    ("README.md", rf"\|\s*Coût total sur 5 ans[^|\n]*\|\s*{M}", CHIFFRAGE, "tco5", "coût sur 5 ans"),
    ("README.md", rf"Version 1\s*:\s*{M}", CHIFFRAGE_V1, "capex", "CAPEX v1"),
    ("README.md", rf"Version 1\s*:\s*{N}\s*/\s*{M}", CHIFFRAGE_V1, "opex_total", "OPEX v1"),
    ("README.md", rf"Version 1\s*:\s*{N}\s*/\s*{N}\s*/\s*{M}", CHIFFRAGE_V1, "tco5", "coût sur 5 ans v1"),
    ("livrables/energie_refroidissement/README.md", rf"Investissement {M}", ENERGIE, "capex_lot", "investissement du lot"),
    ("livrables/energie_refroidissement/README.md", rf"{M} HT/an", ENERGIE, "opex_total", "coûts annuels du lot"),
    ("livrables/energie_refroidissement/README.md", rf"{M} HT sur 5 ans", ENERGIE, "cout_5ans", "coût du lot sur 5 ans"),
    ("livrables/energie_refroidissement/README.md", rf"(?P<m>{MONTANT}) kWh/an", ENERGIE, "energie.kwh", "consommation annuelle"),
    ("livrables/audit/README.md", rf"\|\s*CAPEX[^|\n]*\|\s*{M}", CHIFFRAGE_V1, "capex", "CAPEX v1"),
    ("livrables/audit/README.md", rf"\|\s*CAPEX[^|\n]*\|\s*{N}\s*\|\s*{M}", CHIFFRAGE, "capex", "CAPEX v2"),
    ("livrables/audit/README.md", rf"\|\s*OPEX annuel\s*\|\s*{M}", CHIFFRAGE_V1, "opex_total", "OPEX v1"),
    ("livrables/audit/README.md", rf"\|\s*OPEX annuel\s*\|\s*{N}\s*\|\s*{M}", CHIFFRAGE, "opex_total", "OPEX v2"),
    ("livrables/audit/README.md", rf"\|\s*Coût sur 5 ans\s*\|\s*{M}", CHIFFRAGE_V1, "tco5", "coût sur 5 ans v1"),
    ("livrables/audit/README.md", rf"\|\s*Coût sur 5 ans\s*\|\s*{N}\s*\|\s*{M}", CHIFFRAGE, "tco5", "coût sur 5 ans v2"),
]


def _cle(donnees, chemin):
    for k in chemin.split("."):
        donnees = donnees[k]
    return donnees


@controle("montants", "Montants du chiffrage et de l'énergie cités dans les README")
def controle_montants(r):
    jsons = {}
    err0 = r.erreurs
    for fichier, motif, source, cle, libelle in CITATIONS:
        texte = (RACINE / fichier).read_text(encoding="utf-8")
        m = re.search(motif, texte)
        attendu = _cle(jsons.setdefault(source, lire_json(source)), cle)
        if not m:
            r.erreur(f"{libelle} introuvable (attendu {fr(attendu)}, format du texte changé ?)", fichier)
        elif en_entier(m["m"]) != attendu:
            r.erreur(f"{libelle} : {m['m']} écrit, {fr(attendu)} dans {source} ({cle})", fichier, ligne_de(texte, m.start("m")))
    if r.erreurs == err0:
        r.ok(f"{len(CITATIONS)} montants cités dans README.md, energie_refroidissement/ et audit/ égaux aux JSON")

    # Cohérence interne du chiffrage et liens avec le lot énergie et le plan de câblage
    err0 = r.erreurs
    ch, en = jsons[CHIFFRAGE], jsons[ENERGIE]
    for i, lg in enumerate(ch["capex_lignes"], start=1):
        if lg["quantite"] * lg["pu_ht"] != lg["total_ht"]:
            r.erreur(f"ligne {i} « {lg['solution'][:50]} » : {lg['quantite']} × {lg['pu_ht']} ≠ {lg['total_ht']}", CHIFFRAGE)
    verifs = [
        ("somme des lignes CAPEX = sous_total", sum(lg["total_ht"] for lg in ch["capex_lignes"]), ch["sous_total"]),
        ("sous_total + aleas = capex", ch["sous_total"] + ch["aleas"], ch["capex"]),
        ("somme des OPEX = opex_total", sum(o["montant"] for o in ch["opex"]), ch["opex_total"]),
        ("somme des renouvellements = renouvellement_total", sum(o["montant"] for o in ch["renouvellement"]),
         ch["renouvellement_total"]),
        ("somme par catégorie = sous_total", sum(ch["par_categorie"].values()), ch["sous_total"]),
        ("catégories « Énergie / … » du chiffrage = investissement du lot énergie (capex_lot)",
         sum(v for k, v in ch["par_categorie"].items() if k.startswith("Énergie")), en["capex_lot"]),
    ]
    for libelle, calcule, attendu in verifs:
        if calcule != attendu:
            r.erreur(f"{libelle} : {fr(calcule) if calcule is not None else 'absent'} ≠ {fr(attendu)}", CHIFFRAGE)
    opex_ch = {(o["poste"], o["montant"]) for o in ch["opex"]}
    for o in en["opex"]:
        if (o["poste"], o["montant"]) not in opex_ch:
            r.erreur(f"OPEX du lot énergie « {o['poste']} » ({fr(o['montant'])} €) absent du chiffrage : relancer "
                     "chiffrage/estimation.py après energie/energie.py", CHIFFRAGE)
    cab = lire_json("livrables/plan_cablage/resume.json")
    bornes = lire_json("livrables/plan_cablage/wifi/bornes.json")
    quantites = [("Prise RJ45", cab["prises"], "prises du plan de câblage"),
                 ("Borne Wi-Fi", cab["par_type"]["wifi"], "bornes Wi-Fi du plan de câblage"),
                 ("Fibre OM4", len(cab["rocades"]), "rocades du plan de câblage")]
    for debut, attendu, libelle in quantites:
        lignes = [lg for lg in ch["capex_lignes"] if lg["solution"].startswith(debut)]
        if not lignes:
            r.avert(f"ligne « {debut}… » introuvable dans le chiffrage : contrôle des {libelle} sauté", CHIFFRAGE)
        elif lignes[0]["quantite"] != attendu:
            r.erreur(f"« {debut} » : {lignes[0]['quantite']} au chiffrage, {attendu} {libelle}", CHIFFRAGE)
    if len(bornes["bornes"]) != cab["par_type"]["wifi"]:
        r.erreur(f"{len(bornes['bornes'])} bornes dans l'étude RSSI, {cab['par_type']['wifi']} prises Wi-Fi au plan de câblage",
                 "livrables/plan_cablage/resume.json")
    if r.erreurs == err0:
        r.ok("chiffrage cohérent : totaux, lot énergie (CAPEX et OPEX), quantités du plan de câblage")


# ---------------------------------------------------------------------------
# 4. Liens relatifs
# ---------------------------------------------------------------------------
LIEN_MD = re.compile(r"!?\[[^\]\n]*\]\(\s*<?([^)\s>]+)>?(?:\s+\"[^\"]*\")?\s*\)")
LIEN_HTML = re.compile(r"""(?:href|src)\s*=\s*["']([^"']+)["']""")


def _verifier_lien(r, source, cible, ligne, existants):
    if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", cible) or cible.startswith(("#", "//")) or "${" in cible or "{{" in cible:
        return 0
    chemin = urllib.parse.unquote(cible.split("#")[0].split("?")[0])
    if not chemin:
        return 0
    dest = (RACINE / source).parent / chemin
    try:
        rel = dest.resolve().relative_to(RACINE).as_posix()
    except ValueError:
        r.erreur(f"lien « {cible} » hors du dépôt", source, ligne)
        return 1
    if not dest.exists():
        r.erreur(f"lien cassé « {cible} » ({rel} n'existe pas)", source, ligne)
    elif dest.is_file() and rel not in existants:
        r.avert(f"lien « {cible} » vers un fichier non suivi par git (il manquera sur GitHub)", source, ligne)
    return 1


@controle("liens", "Liens relatifs (Markdown du dépôt, HTML des livrables)")
def controle_liens(r):
    existants = set(suivis())
    err0, n_md, n_html = r.erreurs, 0, 0
    for f in sorted(p for p in existants if p.endswith(".md")):
        texte = (RACINE / f).read_text(encoding="utf-8")
        for m in LIEN_MD.finditer(texte):
            n_md += _verifier_lien(r, f, m[1], ligne_de(texte, m.start()), existants)
    for f in sorted(p for p in existants if p.startswith("livrables/") and p.endswith(".html")):
        texte = (RACINE / f).read_text(encoding="utf-8", errors="replace")
        for m in LIEN_HTML.finditer(texte):
            n_html += _verifier_lien(r, f, m[1], ligne_de(texte, m.start()), existants)
    if r.erreurs == err0:
        r.ok(f"{n_md} liens Markdown et {n_html} liens HTML relatifs, tous vers un fichier existant")


# ---------------------------------------------------------------------------
# 5. Règles de dépôt GesTT (CLAUDE.md du projet)
# ---------------------------------------------------------------------------
MAX_OCTETS = 20 * 1000 * 1000  # 20 Mo
EXT_DEPOT = {"pdf", "docx", "xlsx", "pptx", "odt", "ods", "odp", "csv", "md", "txt", "json", "png", "jpg", "jpeg", "svg",
             "drawio", "html", "zip", "py"}


@controle("gestt", "Règles de dépôt GesTT (taille, extensions, dossiers)")
def controle_gestt(r):
    liste = suivis()
    err0, avert0 = r.erreurs, r.avertissements
    livrables = [p for p in liste if p.startswith("livrables/")]
    for p in livrables:
        taille = (RACINE / p).stat().st_size if (RACINE / p).exists() else 0
        if taille > MAX_OCTETS:
            r.erreur(f"{taille / 1e6:.1f} Mo : un dépôt GesTT est limité à 20 Mo", p)
    dossiers = {str(Path(p).parent) for p in livrables}
    for d in sorted(dossiers):
        if re.search(r"[^A-Za-z0-9._/-]", d):
            r.avert(f"dossier « {d} » : espaces ou accents refusés par GesTT comme dossier de dépôt")
    depots = [p for p in liste if p.startswith("livrables/depots/")]
    par_dossier = {}
    for p in depots:
        morceaux = p.split("/")
        if len(morceaux) != 4:
            r.erreur("livrables/depots/<pxx>/ ne doit contenir que des fichiers, sans sous-dossier", p)
            continue
        par_dossier.setdefault(morceaux[2], []).append(p)
        ext = p.rsplit(".", 1)[-1].lower() if "." in morceaux[3] else ""
        if ext not in EXT_DEPOT:
            r.erreur(f"extension « .{ext} » refusée par GesTT (acceptées : {', '.join(sorted(EXT_DEPOT))})", p)
        if not re.fullmatch(r"RLI-P\d{2}-[A-Za-z0-9._-]+", morceaux[3]):
            r.avert("nommage hors modèle RLI-Pxx-<sujet>.<ext>", p)
    for dossier, fichiers in sorted(par_dossier.items()):
        if not re.fullmatch(r"p\d{2}", dossier):
            r.erreur(f"dossier de dépôt « {dossier} » : attendu pxx (p02, p19…)", f"livrables/depots/{dossier}/")
        total = sum((RACINE / f).stat().st_size for f in fichiers if (RACINE / f).exists())
        if len(fichiers) > 20:
            r.erreur(f"{len(fichiers)} fichiers : un dépôt GesTT est limité à 20", f"livrables/depots/{dossier}/")
        if total > MAX_OCTETS:
            r.erreur(f"{total / 1e6:.1f} Mo au total : un dépôt GesTT est limité à 20 Mo", f"livrables/depots/{dossier}/")
    if r.erreurs == err0:
        detail = f"{len(par_dossier)} dossier(s) dans livrables/depots/" if par_dossier else "pas de livrables/depots/ sur cette branche"
        r.ok(f"{len(livrables)} fichiers dans livrables/, aucun au-delà de 20 Mo ; {detail}")
    if r.avertissements > avert0:
        r.info("(les avertissements GesTT ne bloquent pas)")


# ---------------------------------------------------------------------------
# 6. Hygiène du dépôt : fichiers temporaires et secrets suivis par git
# ---------------------------------------------------------------------------
INTERDITS = [
    (re.compile(r"(^|/)__pycache__/|\.py[co]$"), "cache Python"),
    (re.compile(r"\.(bkp|dtmp)$"), "sauvegarde automatique draw.io"),
    (re.compile(r"(^|/)\.\$"), "fichier de verrou draw.io / Office"),
    (re.compile(r"(^|/)\.DS_Store$"), "fichier macOS"),
    (re.compile(r"(^|/)~\$"), "fichier de verrou Office"),
    (re.compile(r"keys?_vault", re.I), "clés Vault"),
    (re.compile(r"\.(pem|key|p12|pfx|kdbx|jks)$|(^|/)id_(rsa|dsa|ecdsa|ed25519)(\.pub)?$|(^|/)\.env$", re.I),
     "clé, certificat ou fichier de secrets"),
]
# Motifs de contenu : écrits en morceaux pour que ce fichier ne se signale pas lui-même
SECRETS = [
    (re.compile("-----BEGIN (?:[A-Z]+ )*" + "PRIVATE KEY-----"), "clé privée PEM"),
    (re.compile(r"\bAKIA" + r"[0-9A-Z]{16}\b"), "clé d'accès AWS"),
    (re.compile(r"\bgh[pousr]_" + r"[A-Za-z0-9]{36,}\b|\bgithub_pat_" + r"[A-Za-z0-9_]{40,}"), "jeton GitHub"),
    (re.compile(r"\bxox[abprs]-" + r"[A-Za-z0-9-]{10,}"), "jeton Slack"),
    (re.compile(r"\bhv[sb]\." + r"[A-Za-z0-9_-]{20,}"), "jeton Vault"),
    (re.compile(r'"unseal_keys_' + r'(?:b64|hex)"\s*:'), "clés de descellement Vault"),
    (re.compile(r'"root_' + r'token"\s*:\s*"[^"]+"'), "jeton root Vault"),
]


@controle("hygiene", "Hygiène du dépôt (caches, sauvegardes, secrets)")
def controle_hygiene(r):
    liste = suivis()
    err0 = r.erreurs
    for p in liste:
        for motif, quoi in INTERDITS:
            if motif.search(p):
                r.erreur(f"{quoi} suivi par git : le retirer (git rm --cached) et compléter .gitignore", p)
    n = 0
    for p in liste:
        f = RACINE / p
        if not f.is_file() or f.stat().st_size > 5_000_000:
            continue
        brut = f.read_bytes()
        if b"\0" in brut[:8192]:
            continue  # binaire
        texte = brut.decode("utf-8", errors="replace")
        n += 1
        for motif, quoi in SECRETS:
            m = motif.search(texte)
            if m:
                r.erreur(f"{quoi} probable dans le contenu : le retirer et le révoquer", p, ligne_de(texte, m.start()))
    if r.erreurs == err0:
        r.ok(f"{len(liste)} fichiers suivis : ni cache, ni sauvegarde, ni secret évident ({n} fichiers texte lus)")


# ---------------------------------------------------------------------------
# 7. Copies du site web à jour
# ---------------------------------------------------------------------------
@controle("copies", "Copies du site web identiques à leurs originaux")
def controle_copies(r):
    paires = []
    site_docs = noeud_global("communication/build.py", "SITE_DOCS")
    for src, nom in (ast.literal_eval(site_docs).items() if site_docs is not None else ()):
        paires.append((src, f"livrables/site_web/documents/{nom}", "python3 communication/build.py"))
    for f in sorted(p for p in suivis() if p.startswith("livrables/site_web/assets/")):
        nom = Path(f).name
        for d in ("livrables/communication/logo", "livrables/communication/fonts", "communication/fonts"):
            if (RACINE / d / nom).exists():
                paires.append((f"{d}/{nom}", f, f"copier {d}/{nom}"))
                break
    err0 = r.erreurs
    for src, copie, remede in paires:
        a, b = RACINE / src, RACINE / copie
        if not a.exists() or not b.exists():
            r.erreur(f"copie ou original absent ({src})", copie)
        elif a.read_bytes() != b.read_bytes():
            r.erreur(f"différente de {src} : {remede}", copie)
    if r.erreurs == err0:
        r.ok(f"{len(paires)} copies identiques (documents PDF, logos, polices)")


# ---------------------------------------------------------------------------
def main(args):
    if "--liste" in args or "-h" in args or "--help" in args:
        print(__doc__)
        for nom, titre, _ in CONTROLES:
            print(f"  {nom:10} {titre}")
        return 0
    inconnus = [a for a in args if a not in {n for n, _, _ in CONTROLES}]
    if inconnus:
        print(f"Contrôle(s) inconnu(s) : {', '.join(inconnus)} (voir --liste)")
        return 2
    r = Rapport("Cohérence du dépôt")
    for nom, titre, f in CONTROLES:
        if args and nom not in args:
            continue
        r.section(titre)
        try:
            f(r)
        except (OSError, KeyError, ValueError, TypeError, SyntaxError) as exc:
            r.erreur(f"contrôle interrompu : {type(exc).__name__} : {exc}")
    return r.bilan()


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
