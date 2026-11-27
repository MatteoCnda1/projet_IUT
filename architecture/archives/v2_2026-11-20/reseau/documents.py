"""Documents HTML (puis PDF) : plan d'adressage, architecture L2, architecture L3."""
import datetime
import html
import ipaddress as ip

import donnees as D

e = html.escape
DATE = datetime.date.today().strftime("%d/%m/%Y")
BLOCS = {1: ["N-1-LT01", "N-1-LT02", "N0-LT01", "N0-LT02"], 2: ["N1-LT01", "N1-LT02"]}

CSS_PLUS = """
code, pre { font-family: 'DejaVu Sans Mono', monospace; font-size: 7.4pt; }
pre { background: #F3F4F6; border: 1px solid #DEDAD1; border-radius: 1.5mm; padding: 2mm 3mm; white-space: pre-wrap; page-break-inside: avoid; }
.vrf { display: inline-block; padding: 0 1.5mm; border-radius: 1mm; color: #fff; font-size: 7.4pt; font-weight: bold; }
td.m { font-family: 'DejaVu Sans Mono', monospace; font-size: 7.4pt; white-space: nowrap; }
.ok { color: #05893e; font-weight: bold; } .ko { color: #c13c3b; font-weight: bold; }
.v2 { display: inline-block; padding: 0 1.2mm; border-radius: 1mm; background: #05893e; color: #fff; font-size: 6.8pt; font-weight: bold; }
.version { border: 1px solid #05893e; background: #EEF7F1; border-radius: 1.5mm; padding: 2mm 3mm; margin: 2mm 0 4mm; }
img.schema { border: none; }
@page paysage { size: A4 landscape; margin: 10mm; }
.paysage { page: paysage; page-break-before: always; page-break-after: always; }
.paysage img { max-height: 180mm; width: auto; max-width: 100%; display: block; margin: 0 auto; }
"""


V2 = "<span class='v2'>v2</span>"  # marque les éléments modifiés après l'audit


def tete(titre, sous, css, changements=()):
    H = [f"<!doctype html><html lang='fr'><head><meta charset='utf-8'><title>{e(titre)}</title><style>{css}{CSS_PLUS}</style></head><body>",
         f"<h1>{e(titre)}</h1>", f"<p class='sous'>Site de Marseille · IUT Génie Télécom, Luminy · RudyLink Infrastructure · "
         f"<b>version 2</b> · {DATE}<br>{sous}</p>"]
    if changements:
        H.append(f"<div class='version'><b>Version 2, après l'audit du {D.DATE_AUDIT}.</b> La version 1 est archivée dans "
                 "<code>livrables/archives/v1_2026-11-15/</code>. Le traitement de chaque constat est détaillé dans "
                 "<code>livrables/audit/traitement_audit.pdf</code>. Changements dans ce document (repérés " + V2 + ") :<ul>"
                 + "".join(f"<li>{c}</li>" for c in changements) + "</ul></div>")
    return H


def badge(vrf):
    if not vrf:
        return "—"
    c = D.VRF[vrf]["couleur"] if vrf in D.VRF else {"T0": "#5b2c8c"}.get(vrf, "#a75c00")
    return f"<span class='vrf' style='background:{c}'>{vrf}</span>"


def tableau(entetes, lignes, mono=()):
    H = ["<table><tr>" + "".join(f"<th>{x}</th>" for x in entetes) + "</tr>"]
    for l in lignes:
        H.append("<tr>" + "".join(f"<td class='m'>{x}</td>" if i in mono else f"<td>{x}</td>" for i, x in enumerate(l)) + "</tr>")
    H.append("</table>")
    return "".join(H)


def besoins(plan):
    """Besoins par bloc d'après le plan de câblage (livrables/plan_cablage/resume.json)."""
    b = {}
    for n, locaux in BLOCS.items():
        bs = [x for x in plan["baies"] if x["local"] in locaux]
        b[n] = {k: sum(x[k] for x in bs) for k in ("usagers", "wifi", "cameras", "badges", "telephones", "switchs_48p")}
    return b


# ===========================================================================
# Plan d'adressage
# ===========================================================================
def doc_adressage(css, plan):
    H = tete("Plan d'adressage IPv4 et IPv6", "Point 05 du cahier des charges · VLAN, sous-réseaux, passerelles, adresses fixes, réserves", css, [
        "<b>Wi-Fi</b> (NET-01) : les VLAN Wi-Fi par bloc (n14, n15) sont remplacés par trois VLAN à l'échelle du bâtiment (514, 515, 530), "
        "passerelles sur le cœur. Le pool étudiants passe d'un /22 à 94 % à un /20 à 37 %, avec un bail de 2 h.",
        "<b>Tier 0</b> (SEC-02) : VLAN 310 SRV-T0 pour les contrôleurs de domaine, passerelle sur le Stormshield.",
        "<b>Sauvegarde</b> (SEC-03, SEC-01) : VLAN 909 pour le Proxmox Backup Server, en VRF ADM.",
        "<b>Virtualisation</b> (SYS-02) : hyperviseurs DT-PVE1/2 et DM-PVE1/2, VLAN 403 et 908 (corosync), liens directs de réplication ; "
        "VLAN 907 pour les contrôleurs Wi-Fi physiques.",
        "<b>BGP</b> (Q4) : lien iBGP 139.124.112.4/30 entre EL-RTR1 et EL-RTR2.",
        "<b>Correction</b> : les adresses fixes des VLAN 401 et 402 sortaient de leur sous-réseau en v1 (ex. FortiGate en 172.16.13.65 dans 172.16.13.32/27)."])
    nb_vlan = len([v for v in D.VLANS if v < 1000])
    H += ["<div class='cles'>",
          f"<div class='cle'><b>{nb_vlan} VLAN</b>+ {len(D.TRANSITS)} VLAN de transit vers les pare-feu</div>",
          "<div class='cle'><b>10.13.0.0/16</b>IPv4 privé du site (13 = Bouches-du-Rhône)</div>",
          "<div class='cle'><b>139.124.112.0/24</b>IPv4 public, dans le bloc AMU 139.124.0.0/16</div>",
          "<div class='cle'><b>2001:660:5402:4000::/52</b>IPv6, dans le /48 de Luminy</div></div>",
          "<h2>1. Principes</h2><ul>",
          "<li><b>Double pile partout</b> : chaque VLAN routé a un sous-réseau IPv4 et un /64 IPv6. Les seules exceptions sont les réseaux internes "
          "au cluster Proxmox (corosync, réplication), non routés, en IPv4 seulement.</li>",
          "<li><b>Lecture directe du préfixe IPv6</b> : le 4e groupe vaut « 4 » suivi du numéro de VLAN. VLAN 112 → <code>2001:660:5402:4112::/64</code>. "
          "Les numéros de VLAN ne contiennent que des chiffres de 0 à 9, donc pas d'ambiguïté hexadécimale.</li>",
          "<li><b>Numéro de VLAN structuré</b> : 1er chiffre = zone (1 = bloc de distribution 1, 2 = bloc 2, 3 = datacenter, 4 = DMZ, 9 = administration), "
          "5 = Wi-Fi du bâtiment " + V2 + ", 2e chiffre = VRF dans un bloc (1 USR, 2 IOT, 3 GST, 9 ADM). Chaque VRF d'un bloc tient donc dans un /60 IPv6 et dans un ou deux résumés IPv4, "
          "ce qui garde courtes les routes et les règles du pare-feu.</li>",
          "<li><b>VLSM</b> : chaque sous-réseau IPv4 est dimensionné sur le besoin réel (plan de câblage, étude Wi-Fi) avec une marge d'au moins 50 %, "
          "puis rangé dans un /20 par bloc pour garder des résumés propres.</li>",
          "<li><b>Passerelle = première adresse</b> (.1 en IPv4, ::1 en IPv6). Un équipement garde la même terminaison dans les deux familles "
          "(10.13.59.41 ↔ 2001:660:5402:4904::41).</li>",
          "<li><b>Pas de VLAN étendu entre les blocs</b> : la frontière L2/L3 est sur la distribution. Un VLAN filaire n'existe que dans son bloc. "
          "Les VLAN Wi-Fi 5xx " + V2 + " ne passent pas non plus par les blocs : le trafic des clients arrive en tunnel CAPWAP sur les contrôleurs, "
          "raccordés au cœur, qui portent leurs passerelles. Un client garde donc son adresse dans tout le bâtiment.</li>",
          "<li><b>Site jumeau</b> (Digne ou Gap) : 10.4.0.0/16 réservé, même découpage, pour que l'interconnexion MPLS (point 07) se résume à une route par site et par VRF.</li></ul>",
          "<h2>2. Blocs attribués</h2>"]
    H.append(tableau(["Bloc", "Origine", "Usage dans le projet"], [
        ["139.124.0.0/16", "AMU (historique, sites marseillais dont Luminy)", "On demande à la DSI AMU un /24 pour le bâtiment : <b>139.124.112.0/24</b> (valeur à confirmer)"],
        ["2001:660:5400::/40", "AMU, AS2457 (RENATER)", "—"],
        ["2001:660:5402::/48", "Sous-réseaux du campus de Luminy", "On réserve un /52 pour le bâtiment : <b>2001:660:5402:4000::/52</b> (4 096 /64)"],
        ["10.13.0.0/16", "RFC 1918", "Tout l'adressage interne du site"],
        ["172.16.13.0/24", "RFC 1918", "DMZ (publiée en IPv4 par NAT 1:1 sur le FortiGate ; en IPv6 adresses globales, sans NAT)"],
        ["10.4.0.0/16", "RFC 1918", "Réservé au site jumeau"],
        [f"{D.FAI2['lien4']}, {D.FAI2['pa6']}", "Plages de documentation (RFC 5737, RFC 3849)",
         "Valeurs d'exemple pour le FAI 2 : à remplacer par celles du contrat"]], mono=(0,)))
    H.append("<h3>Découpage du /52 IPv6</h3>")
    H.append(tableau(["Préfixe", "Usage"], [
        ["2001:660:5402:4000::/64", "Boucles locales (/128)"],
        ["2001:660:5402:4110::/60 … 4190::/60", "Bloc 1 : un /60 par VRF (USR 411x, IOT 412x, GST 413x, ADM 419x)"],
        ["2001:660:5402:4210::/60 … 4290::/60", "Bloc 2 : idem (421x, 422x, 423x, 429x)"],
        ["2001:660:5402:4300::/60", "Datacenter (VRF SRV)"],
        ["2001:660:5402:4310::/64", "Tier 0 (contrôleurs de domaine) " + V2 + ", hors du résumé SRV"],
        ["2001:660:5402:4400::/60", "DMZ"],
        ["2001:660:5402:4510::/60, 4530::/60", "Wi-Fi du bâtiment " + V2 + " (USR 451x, GST 453x)"],
        ["2001:660:5402:4900::/60", "Administration centrale (VRF ADM)"],
        ["2001:660:5402:4F00::/56", "Interconnexions : 4F00/4F01 OUT-A/B, 4F10 TR-FW, 4F2v CL↔SNS, 4F3v/4F4v CL↔DL (/127), 4FF0 lien FAI 1, 4FF1 iBGP " + V2]], mono=(0,)))
    H.append("<h3>Découpage du /24 public</h3>")
    H.append(tableau(["Préfixe", "Usage", "Détail"], [list(map(e, x)) for x in D.PUBLIC], mono=(0,)))
    H.append(f"<p>FAI 2 (exemple) : lien {D.FAI2['lien4']} et {D.FAI2['lien6']}, préfixe fournisseur {D.FAI2['pa6']} utilisé en secours IPv6 (NPTv6).</p>")
    # VLAN
    H.append("<h2 class='saut'>3. Table des VLAN</h2>")
    lignes = []
    for vid in sorted(D.VLANS):
        v = D.VLANS[vid]
        if vid >= 1000:
            continue
        dh = D.DHCP.get(v["vrf"], "—") if v["gw4"] else "—"
        if vid in (900, 901, 902, 903, 905, 907, 908, 909, 300, 310) or v["vrf"] == "DMZ":
            dh = "statique"
        if vid in D.BAIL:
            dh += f", bail {D.BAIL[vid]}"
        nv = f" {V2}" if vid in (130, 230, 191, 291, 300, 310, 402, 403, 514, 515, 530, 902, 904, 907, 908, 909) else ""
        lignes.append([str(vid) + nv, f"<b>{e(v['nom'])}</b>", badge(v["vrf"]), v["v4"] or "—", v["gw4"] or "—",
                       str(v["taille"]) if v["taille"] else "—", v["v6"] or "—", e(v["gw_eq"] or "non routé"), e(dh), e(v["usage"])])
    H.append(tableau(["VLAN", "Nom", "VRF", "IPv4", "Passerelle", "Hôtes", "IPv6", "Routé par", "DHCP", "Usage"], lignes, mono=(3, 4, 6)))
    H.append("<p class='sous'>DHCP : DT-DHCP1/2 = 10.13.48.31 / .32 (Windows, basculement) ; Kea = 10.13.59.11 / .12 (haute disponibilité). "
             "Passerelle IPv6 = ::1 du préfixe (adresse fixe sur la SVI) ; les clients utilisent l'adresse lien-local fe80::1 annoncée par RA. "
             "Wi-Fi : un /64 suffit quel que soit le nombre de clients ; les sous-réseaux IPv4 viennent de l'étude de couverture "
             f"({D.WIFI_CLIENTS_PAR_BORNE} clients par borne). VLAN 310 : passerelle sur le Stormshield, donc tout flux vers les contrôleurs "
             "de domaine est filtré, même depuis le VLAN 300.</p>")
    # Dimensionnement
    b = besoins(plan)
    H.append("<h3>Dimensionnement : besoin contre capacité</h3>")
    rows = []
    bornes = b[1]["wifi"] + b[2]["wifi"]
    clients = bornes * D.WIFI_CLIENTS_PAR_BORNE
    lignes_dim = [(515, clients, f"{bornes} bornes × {D.WIFI_CLIENTS_PAR_BORNE} clients (tout le bâtiment)"),
                  (514, clients // 3, "≈ un tiers des clients Wi-Fi"),
                  (530, clients // 4, "≈ un quart des clients Wi-Fi")]
    for n in (1, 2):
        x = b[n]
        for vid, besoin, src in ((n * 100 + 11, x["usagers"], f"{x['usagers']} prises usager (étudiants et personnel confondus)"),
                                 (n * 100 + 10, x["usagers"] // 2, "≈ la moitié des prises usager"),
                                 (n * 100 + 12, x["telephones"], f"{x['telephones']} téléphones du plan de câblage"),
                                 (n * 100 + 20, x["cameras"], f"{x['cameras']} caméras"),
                                 (n * 100 + 21, x["badges"], f"{x['badges']} badgeuses"),
                                 (n * 100 + 90, x["switchs_48p"] + 2, f"{x['switchs_48p']} switchs d'accès + DL"),
                                 (n * 100 + 91, x["wifi"], f"{x['wifi']} bornes")):
            lignes_dim.append((vid, besoin, src))
    for vid, besoin, src in lignes_dim:
        if True:
            v = D.VLANS[vid]
            ok = v["taille"] >= besoin * 1.5
            rows.append([str(vid), e(v["nom"]), e(src), str(besoin), f"{v['v4']} ({v['taille']})",
                         f"<span class='{'ok' if ok else 'ko'}'>{round(100 * besoin / v['taille'])} %</span>"])
    H.append(tableau(["VLAN", "Nom", "Base du besoin", "Besoin", "Capacité", "Occupation"], rows, mono=(4,)))
    H.append("<p class='sous'>Vert : marge d'au moins 50 %. En v1, WIFI-ETU-B1 (/22) était à 94 % avec 960 clients pour 1 022 adresses, "
             "risque d'épuisement relevé par l'audit (NET-01) ; le VLAN 515 unique (/20) et le bail de 2 h règlent ce point.</p>")
    # Transits
    H.append("<h2>4. Interconnexions</h2><h3>Transits vers les pare-feu (VLAN commutés par le cœur CL, Stormshield raccordé en direct " + V2 + ")</h3>")
    H.append(tableau(["VLAN", "Nom", "VRF", "IPv4", "Côté A", "Côté B", "IPv6"],
                     [[str(vid), e(n), badge(vrf), v4, f"{a[0]} {D.VLANS[vid]['a'][1]}", f"{b_[0]} {D.VLANS[vid]['b'][1]}", f"{D.V6}{p6}::/64 (::{a[1]} / ::{b_[1]})"]
                      for vid, n, vrf, v4, a, b_, p6 in D.TRANSITS], mono=(3, 4, 5, 6)))
    H.append("<p>Les deux nœuds d'un cluster de pare-feu (actif/passif) partagent les mêmes adresses : une seule adresse par cluster.</p>")
    H.append("<h3>Liens routés cœur ↔ distribution (/31 et /127, RFC 3021 et RFC 6164)</h3>")
    H.append(tableau(["Bloc", "VRF", "Sous-interface", "IPv4", "CL", "DL", "IPv6 CL", "IPv6 DL"],
                     [[str(q["bloc"]), badge(q["vrf"]), q["sous_if"], q["v4"], q["cl4"], q["dl4"], q["cl6"], q["dl6"]] for q in D.P2P],
                     mono=(2, 3, 4, 5, 6, 7)))
    H.append("<h3>Liens directs entre hyperviseurs " + V2 + " (non routés)</h3>")
    H.append(tableau(["Lien", "IPv4", "Adresses", "Support"], [list(x) for x in D.LIENS_DIRECTS], mono=(1,)))
    H.append("<h3>Boucles locales (Loopback0, VRF ADM)</h3>")
    H.append(tableau(["Équipement", "IPv4", "IPv6"], [list(x) for x in D.BOUCLES], mono=(1, 2)))
    # Hôtes
    H.append("<h2 class='saut'>5. Adresses fixes des équipements</h2>")
    rows = []
    for vid in sorted(D.HOTES):
        v = D.VLANS[vid]
        for nom, fin in D.HOTES[vid]:
            if isinstance(fin, str):
                net = ip.ip_network(v["v4"])
                a, z = fin.split("-")
                a4 = f"{net.network_address + int(a)} – .{z}"
                a6 = f"{D.V6}4{vid:03d}::{a} – ::{z}" if v["v6"] else "—"
            else:
                a4, a6 = D.adresse(vid, fin)
            rows.append([f"{vid} {e(v['nom'])}", e(nom), a4, a6 or "—"])
    H.append(tableau(["VLAN", "Équipement", "IPv4", "IPv6"], rows, mono=(2, 3)))
    H.append("<p class='sous'>Les deux nœuds HA d'un pare-feu ont chacun une adresse de gestion propre (VLAN 900) en plus des adresses partagées des transits. "
             "Les bornes, postes d'admin et switchs d'accès reçoivent une réservation DHCP Kea (adresse fixe gérée au même endroit).</p>")
    # Résumés
    H.append("<h2>6. Résumés par VRF</h2><p>Ce sont les routes statiques du Stormshield vers le cœur et les objets réseau de ses règles de filtrage.</p>")
    H.append(tableau(["VRF", "IPv4", "IPv6"], [[badge(k), "<br>".join(x for x in r if ":" not in x), "<br>".join(x for x in r if ":" in x)]
                                              for k, r in D.RESUMES.items()], mono=(1, 2)))
    H.append("<h2>7. Réserves</h2><ul>"
             "<li>Dans chaque bloc : 10.13.x.192/26 après l'impression, le reste du /20 (dont les anciens sous-réseaux Wi-Fi de la v1 : "
             "10.13.20.0/22, 10.13.24.0/23, 10.13.36.0/22, 10.13.40.0/23) ; VLAN x14-x19, x23-x29, x31-x39 libres.</li>"
             "<li>Wi-Fi du bâtiment : 10.13.64.0/18 réservé (10.13.88.0 à 10.13.127.255 libres).</li>"
             "<li>10.13.4.0/22 à 10.13.12.0/22 : interconnexions futures (MPLS, VPN), 10.13.49.0 à 10.13.51.255 et 10.13.52.32 à 10.13.55.255 : "
             "extension datacenter.</li>"
             "<li>10.13.128.0 à 10.13.255.255 : bâtiments ou blocs supplémentaires.</li>"
             "<li>IPv6 : 4500::/56 à 4E00::/56 libres, soit plus de 2 300 /64.</li></ul></body></html>")
    return "\n".join(H)


# ===========================================================================
# Architecture L2
# ===========================================================================
PORTS_C9500 = 16      # C9500-16X : 16 ports 10G SFP+ (les liens SVL 2×40G sont sur le module réseau C9500-NM-2Q)
PORTS_DAD = 1         # un port 10G par membre réservé au lien de détection double actif
UPLINKS_COEUR = 4     # Po101 / Po102 : 4 liens vers le cœur par bloc
PRIX_DL = 9500        # € HT par C9500-16X (chiffrage/estimation_infra.md)


def justification_blocs(b, plan):
    """Pourquoi trois couches, pourquoi deux blocs, pourquoi un découpage par étage."""
    dispo = 2 * (PORTS_C9500 - PORTS_DAD)
    prises = {n: sum(x["prises"] for x in plan["baies"] if x["local"] in BLOCS[n]) for n in (1, 2)}
    rows = []
    for n in (1, 2):
        sw = b[n]["switchs_48p"]
        pris = 2 * sw + UPLINKS_COEUR
        rows.append([f"Bloc {n} (DL-SW{2 * n - 1}/{2 * n})", ", ".join(BLOCS[n]), str(sw), str(prises[n]),
                     f"{pris} / {dispo}", f"{dispo - pris} ports, soit {(dispo - pris) // 2} switchs d'accès de plus"])
    total_sw = b[1]["switchs_48p"] + b[2]["switchs_48p"]
    un_bloc = 2 * total_sw + UPLINKS_COEUR
    return "".join([
        "<h3>Pourquoi trois couches, deux blocs de distribution, découpés par étage</h3>",
        "<p><b>Les blocs sont logiques, pas physiques.</b> Les quatre DL-SW sont dans la baie 1 de la salle serveur (sous-sol), à côté du cœur "
        "(bilan de puissance du point 14). Chaque local technique y remonte par deux fibres, l'une par la colonne Nord, l'autre par la colonne Sud "
        "(plan de câblage). Un bloc est donc un groupe de locaux qui partagent une paire de DL et les mêmes VLAN : on peut rattacher un local à "
        "l'autre bloc en changeant deux jarretières, sans recâbler.</p>",
        tableau(["Bloc", "Locaux techniques", "Switchs d'accès", "Prises", "Ports 10G utilisés", "Marge"], rows),
        f"<p class='sous'>Ports disponibles par paire : 2 × ({PORTS_C9500} ports 10G − {PORTS_DAD} port DAD) = {dispo}. "
        f"Chaque switch d'accès prend 2 ports (un par DL) ; {UPLINKS_COEUR} ports vont au cœur. Les liens SVL utilisent le module 2×40G.</p>",
        "<p><b>Capacité : deux blocs suffisent largement.</b> Un switch d'accès a 48 ports 1G pour 2 × 10G de montée, soit un rapport de "
        "2,4 pour 1 (on recommande de rester sous 20 pour 1 à l'accès). Chaque bloc garde au moins un tiers de ses ports 10G libres.</p>",
        f"<p><b>Un seul bloc ne tiendrait pas sur des C9500-16X</b> : les {total_sw} switchs d'accès demanderaient {un_bloc} ports pour {dispo} "
        f"disponibles. Un <b>cœur replié</b> (accès raccordé directement au cœur) non plus : il faudrait {2 * total_sw} ports pour l'accès, plus "
        f"{3 * UPLINKS_COEUR} vers EL-SW, DT-SW et NM-SW, soit {2 * total_sw + 3 * UPLINKS_COEUR} ports pour {dispo}. Ces deux options imposent un "
        "cœur plus dense (C9500-48Y4C, 48 ports 1/10/25G, à chiffrer). Elles économiseraient alors une partie des "
        f"{4 * PRIX_DL:,} € HT des quatre DL-SW et environ 640 W. ".replace("000 €", "000 €").replace(",000", " 000") +
        "Cette variante est chiffrée dans le dossier (pistes d'optimisation du chiffrage, constat NET-02 de l'audit). "
        "Nous gardons pourtant les trois couches, pour trois raisons :</p><ul>"
        "<li>le cahier des charges demande explicitement un réseau en trois couches « accès, distribution, cœur » ;</li>"
        "<li><b>domaines de panne plus petits</b> : une boucle, une tempête de broadcast ou une erreur de configuration reste dans un bloc, "
        "et le cœur ne porte aucun VLAN filaire d'usager (seuls les VLAN Wi-Fi, amenés par les contrôleurs, y ont leur passerelle) ;</li>"
        "<li><b>évolution</b> : un nouveau bâtiment, ou le doublement des prises, se fait en ajoutant un bloc, sans toucher au cœur ni à l'adressage "
        "(un /20 IPv4 et un /56 IPv6 par bloc sont déjà réservés).</li></ul>",
        "<p><b>Pourquoi par étage et pas par aile.</b> Aucun VLAN filaire n'est partagé entre deux blocs. Le découpage par étage équilibre "
        "les blocs (8 et 7 switchs, contre environ 5 et 10 en regroupant les locaux 01 et 02) et se lit directement dans les numéros : "
        "VLAN 1xx = sous-sol et RDC, VLAN 2xx = 1er étage.</p>",
        "<p><b>Wi-Fi " + V2 + "</b> : en v1, les bornes commutaient le trafic localement (FlexConnect) dans le VLAN Wi-Fi de leur bloc. Un client "
        "qui prenait l'escalier changeait de sous-réseau et perdait ses connexions (visio, SSH) : c'est le constat critique NET-01 de l'audit. "
        "En v2, les bornes sont en <b>mode local</b> : le trafic des clients remonte en CAPWAP à deux contrôleurs physiques C9800-L (HA SSO) "
        "raccordés au cœur, qui le posent dans un VLAN unique par SSID pour tout le bâtiment (514, 515, 530). Le client garde son adresse "
        "partout ; l'itinérance 802.11r/OKC ne dure que quelques dizaines de millisecondes. La v1 avait écarté cette solution parce que le "
        "contrôleur était une VM du cluster NM raccordée en 1G : les contrôleurs physiques sont branchés en 2×10G sur le cœur.</p>",
        "<p><b>Revers assumé</b> : si les deux DL d'une paire tombent en même temps (panne double, très improbable, ou erreur de configuration "
        "sur le bloc), c'est un étage entier qui est coupé plutôt qu'une demi-aile.</p>",
    ])


def doc_l2(css, plan):
    H = tete("Architecture de niveau 2", "Points 03 et 06 · VLAN, trunks, agrégats, piles, Spanning Tree, profils de ports, sécurité L2, zone Net Management", css, [
        "<b>Wi-Fi</b> (NET-01) : bornes en mode local, deux contrôleurs physiques C9800-L en HA SSO sur le cœur, VLAN Wi-Fi uniques pour le bâtiment.",
        "<b>Stormshield raccordé directement au cœur</b> (SEC-01, NET « goulot EL-SW ») : les transits inter-VRF ne passent plus par la pile C9200L EL-SW.",
        "<b>Virtualisation</b> (SYS-02) : clusters Proxmox DT (2 nœuds, tier 0) et DMZ (2 nœuds + témoin) à la place de 12 serveurs physiques.",
        "<b>Tier 0</b> (SEC-02) : VLAN 310 commuté sur CL et DT-SW, sans SVI : la passerelle est le Stormshield.",
        "<b>Caméras et badgeuses</b> (Q10) : 802.1X EAP-TLS quand l'équipement le permet, sinon MAB avec ACL téléchargée par RADIUS.",
        "<b>Zone NM</b> : le contrôleur Wi-Fi virtuel est retiré ; collecteurs de journaux en double (SEC-04) ; réplication de la supervision toutes les minutes."])
    b = besoins(plan)
    H += ["<div class='cles'>",
          f"<div class='cle'><b>{b[1]['switchs_48p'] + b[2]['switchs_48p']} switchs d'accès</b>répartis en 2 blocs de distribution</div>",
          "<div class='cle'><b>0 VLAN étendu</b>entre les blocs : frontière L3 sur la distribution</div>",
          "<div class='cle'><b>MEC partout</b>agrégats LACP vers des paires logiques : STP ne bloque aucun lien</div>",
          "<div class='cle'><b>802.1X / MAB</b>VLAN attribué par RADIUS sur chaque prise</div></div>",
          "<h2>1. Choix structurants</h2><ul>",
          "<li><b>Paires logiques</b> : cœur (CL-SW1/2) et distribution (DL-SW1/2, DL-SW3/4) en <b>StackWise Virtual</b> ; EL-SW, DM-SW et NM-SW en pile "
          "<b>StackWise-80</b> (kit de pile C9200L) ; DT-SW en pile <b>StackWise-1T</b> (C9300X). Chaque paire est un seul switch logique : "
          "un équipement raccordé aux deux membres le fait par un agrégat LACP unique (MEC, Multichassis EtherChannel).</li>",
          "<li><b>Conséquence</b> : aucune boucle L2 active. Spanning Tree reste activé comme filet de sécurité (erreur de câblage, prise murale bouclée), "
          "mais ne bloque aucun lien en fonctionnement normal : toute la bande passante est utilisée.</li>",
          "<li><b>Frontière L2/L3 sur la distribution</b> : les VLAN d'un bloc s'arrêtent à son DL. Une tempête de broadcast ou une boucle reste confinée au bloc.</li>",
          "<li><b>VLAN 1 jamais utilisé</b>, VLAN natif des trunks 999 (ne transporte rien), ports libres en VLAN 998 et désactivés. VTP en mode <i>off</i>.</li>",
          "<li><b>Listes de VLAN autorisés explicites</b> sur chaque trunk (jamais « all »).</li>",
          "<li>" + V2 + " <b>Stormshield en direct sur le cœur</b> : chaque nœud est raccordé aux deux membres CL par un agrégat 2×10G. "
          "Les VLAN de transit ne vivent plus que sur CL ; EL-SW ne porte plus que la gestion (VLAN 900) des routeurs et pare-feu. "
          "Le trafic inter-VRF ne traverse donc plus les petits tampons des C9200L.</li>",
          "<li>" + V2 + " <b>Contrôleurs Wi-Fi physiques</b> (2 × C9800-L-F, HA SSO) raccordés au cœur, chacun par un agrégat 2×10G.</li></ul>",
          justification_blocs(b, plan),
          "<div class='paysage'><h2>2. Schéma de niveau 2</h2><img class='schema' src='architecture_l2.png' alt='Schéma L2'></div>",
          "<h2>3. Présence des VLAN par équipement</h2>"]
    groupes = [("AL bloc 1", lambda v: 100 <= v < 200), ("DL-B1", lambda v: 100 <= v < 200),
               ("AL bloc 2", lambda v: 200 <= v < 300), ("DL-B2", lambda v: 200 <= v < 300),
               ("CL", lambda v: v in (300, 310, 514, 515, 530, 900, 901, 902, 904, 906, 907, 909) or 1000 <= v < 1100),
               ("WLC", lambda v: v in (514, 515, 530, 907)),
               ("DT-SW", lambda v: v in (300, 310, 900, 901, 902, 908, 909)), ("NM-SW", lambda v: 900 <= v <= 906 and v != 905),
               ("EL-SW", lambda v: v == 900), ("DM-SW", lambda v: 400 <= v < 500)]
    rows = []
    for vid in sorted(D.VLANS):
        if vid in (998, 999, 1100):
            continue
        v = D.VLANS[vid]
        rows.append([str(vid), e(v["nom"]), badge(v["vrf"])] +
                    [("<b>SVI</b>" if (g in ("DL-B1", "DL-B2", "CL") and f(vid) and v["gw_eq"] in ("DL-B1", "DL-B2", "CL")
                                       and g == v["gw_eq"]) or (g == "CL" and 1000 <= vid < 1100)
                      else ("✓" if f(vid) else "")) for g, f in groupes])
    H.append(tableau(["VLAN", "Nom", "VRF"] + [g for g, _ in groupes], rows))
    H.append("<p class='sous'>SVI : interface routée (passerelle) du VLAN. Le VLAN 1100 (TR-FW) relie directement les deux pare-feu, sans switch. "
             "Le VLAN 905 (réplication) est un câble direct entre les deux hyperviseurs NM. Les VLAN 903 et 908 (corosync) ne quittent pas "
             "leur pile (NM-SW, DT-SW), le 403 reste sur DM-SW. Le VLAN 310 traverse CL sans SVI : sa passerelle est le Stormshield. "
             "Les VLAN 514, 515 et 530 n'existent que sur CL et sur les contrôleurs : ils ne descendent jamais vers les blocs.</p>")
    H.append("<h2>4. Agrégats et trunks</h2>")
    po = [
        ["Po1 (×15)", "AL-SWn", "DL-B1 ou DL-B2", "2×10G SFP+ (1 vers chaque DL)", "trunk", "n10-n13, n20-n22, n30, n90, n91 " + V2, "999"],
        ["Po101", "DL-B1", "CL", "4×10G (maillage complet)", "routé, sous-interfaces 802.1Q", "tags 10, 20, 30, 90 (VRF)", "—"],
        ["Po102", "DL-B2", "CL", "4×10G", "routé, sous-interfaces 802.1Q", "tags 10, 20, 30, 90 (VRF)", "—"],
        ["Po2 / Po3 " + V2, "EL-SNS1 / EL-SNS2", "CL (1 lien par membre)", "2×10G chacun (module 10G du SN710)", "trunk", "1010, 1020, 1030, 1040, 1090, 310", "999"],
        ["Po4 " + V2, "CL", "pile EL-SW", "2×10G", "trunk", "900", "999"],
        ["—", "EL-FGT1/2, EL-SNS1/2, EL-RTR1/2 (mgmt)", "pile EL-SW", "1G", "access", "900", "—"],
        ["redundant", "EL-FGT ↔ EL-SNS", "direct (maillage 2×2)", "10G", "routé", "TR-FW (non tagué)", "—"],
        ["Po30 / Po31 " + V2, "WLC1 / WLC2 (C9800-L-F)", "CL (1 lien par membre)", "2×10G chacun", "trunk", "514, 515, 530, 907", "999"],
        ["Po10", "CL", "pile NM-SW", "4×10G", "trunk", "900, 901, 902, 904, 906", "999"],
        ["Po20 " + V2, "CL", "pile DT-SW", "4×10G", "trunk", "300, 310, 900, 901, 902, 909", "999"],
        ["Po21 / Po22 " + V2, "pile DT-SW", "DT-PVE1 / DT-PVE2 (bond1)", "2×25G LACP", "trunk", "300, 310 (VM)", "999"],
        ["Po23 " + V2, "pile DT-SW", "DT-BKP1", "2×25G LACP", "access", "909", "—"],
        ["Po1", "EL-FGT (port DMZ)", "pile DM-SW", "2×10G", "trunk", "400, 401, 402", "999"],
        ["Po11 / Po12 " + V2, "pile DM-SW", "DM-PVE1 / DM-PVE2 (bond1)", "2×10G LACP", "trunk", "400, 401 (VM)", "999"],
        ["Po31 / Po32", "pile NM-SW", "NM-PVE1 / NM-PVE2 (bond1)", "2×1G LACP", "trunk", "904", "999"],
    ]
    H.append(tableau(["Agrégat", "De", "Vers", "Liens", "Mode", "VLAN autorisés", "Natif"], po))
    H.append("<p class='sous'>Ports 10G du cœur (2 × C9500-16X = 32 ports) : Po101 4, Po102 4, Po2 + Po3 4, Po4 2, Po10 4, Po20 4, "
             "Po30 + Po31 4, DAD 2 : 28 utilisés, 4 libres. Les liens SVL sont sur le module 2×40G.</p>")
    H.append("<p>LACP en mode <i>active</i> des deux côtés, hachage src-dst-ip-l4port. Les liens fibre ont UDLD agressif. "
             "Les liens d'un agrégat passent par des chemins de câbles différents (rocades Nord et Sud du plan de câblage).</p>")
    H.append("<h2>5. Paires et piles : détection de séparation</h2>")
    H.append(tableau(["Paire", "Technologie", "Liens de la paire", "Détection double actif"], [
        ["CL-SW1/2, DL-SW1/2, DL-SW3/4", "StackWise Virtual (C9500)", "2×40G SVL", "lien DAD dédié 10G (fast-hello)"],
        ["WLC1/2 " + V2, "C9800 HA SSO (actif/veille à chaud)", "port de redondance RP direct (RJ45)", "RMI + passerelle (10.13.60.71/.72) ; bornes et clients conservés"],
        ["EL-SW, NM-SW, DM-SW", "StackWise-80 (C9200L + kit de pile)", "2 câbles de pile 80 Gb/s en anneau", "intégrée à la pile"],
        ["DT-SW1/2", "StackWise-1T (C9300X)", "2 câbles de pile", "intégrée à la pile"],
        ["EL-FGT1/2", "FortiGate FGCP actif/passif", "ha1 + ha2 directs", "heartbeat sur 2 liens, priorité + override off"],
        ["EL-SNS1/2", "Stormshield HA actif/passif", "2 liens HA directs", "liens HA redondés"]]))
    H.append("<h2 class='saut'>6. Spanning Tree</h2><ul>"
             "<li>Mode <b>Rapid PVST+</b> (802.1w par VLAN) sur tous les switchs.</li>"
             "<li>Racine : <b>DL-B1</b> pour les VLAN 1xx et <b>DL-B2</b> pour les VLAN 2xx (priorité 0) ; <b>CL</b> pour 300, 310, 5xx, 9xx, 10xx (priorité 4096). "
             "Les switchs d'accès restent à 61440 : ils ne peuvent jamais devenir racine.</li>"
             "<li>Ports d'accès : <code>portfast</code> + <b>BPDU guard</b> (un switch branché sur une prise coupe le port). "
             "Descentes des DL vers l'accès : <b>root guard</b>. Agrégats : <b>loop guard</b> par défaut.</li>"
             "<li>Ports vers les serveurs, pare-feu et hyperviseurs : <code>portfast trunk</code> + BPDU guard.</li></ul>"
             "<h2>7. Profils de ports d'accès</h2>")
    H.append(tableau(["Profil", "Mode", "VLAN", "Authentification", "PoE / QoS", "Sécurité"], [
        ["Usager (poste + téléphone)", "access + voice", "n10 ou n11 donné par RADIUS ; voice n12", "802.1X puis MAB (multi-auth), échec → n30 restreint",
         "PoE+ pour le téléphone ; trust DSCP du téléphone (EF / CS3)", "BPDU guard, storm-control 1 %, DHCP snooping, DAI, IPSG"],
        ["Borne Wi-Fi " + V2, "access (mode local : tout passe en CAPWAP)", "n91", "802.1X (supplicant de la borne, certificat)", "PoE+ (classe 4, ≈ 25 W)", "BPDU guard"],
        ["Caméra IP " + V2, "access", "n20", "802.1X EAP-TLS (certificat machine) si supporté, sinon MAB",
         "PoE (classe 3)", "ACL téléchargée par RADIUS : seulement l'enregistreur (RTSP/HTTPS) ; port-security 1 MAC, violation → shutdown"],
        ["Badgeuse " + V2, "access", "n21", "MAB (EAP-TLS si le modèle le permet)", "PoE", "ACL téléchargée : seulement le serveur de contrôle d'accès ; port-security 1 MAC"],
        ["Imprimante", "access", "n13", "MAB", "—", "port-security 2 MAC"],
        ["Port libre", "access", "998", "—", "—", "shutdown"]]))
    H.append("""<pre>! Exemple : AL-SW1 (bloc 1), prise usager
interface GigabitEthernet1/0/12
 description PRISE N0-B014-02
 switchport mode access
 switchport access vlan 111
 switchport voice vlan 112
 authentication host-mode multi-auth
 authentication order dot1x mab
 authentication event fail action authorize vlan 130
 access-session port-control auto
 dot1x pae authenticator
 mab
 spanning-tree portfast
 spanning-tree bpduguard enable
 storm-control broadcast level 1.00
 ip dhcp snooping limit rate 15
!
interface GigabitEthernet1/0/40
 description CAMERA C07 (v2 : EAP-TLS, sinon MAB + ACL telechargee)
 switchport mode access
 switchport access vlan 120
 authentication order dot1x mab
 authentication priority dot1x mab
 access-session port-control auto
 access-session host-mode single-host
 dot1x pae authenticator
 mab
 switchport port-security
 switchport port-security violation shutdown
 ip access-group ACL-PAR-DEFAUT-IOT in      ! remplacee par la dACL RADIUS
 spanning-tree portfast
 spanning-tree bpduguard enable
! RADIUS (NPS) renvoie : Cisco-AVPair = "ip:inacl#10=permit tcp any host 10.13.48.60 eq 554"
!                                    "ip:inacl#20=permit tcp any host 10.13.48.60 eq 443"  "ip:inacl#99=deny ip any any log"
!
interface Port-channel1
 description UPLINK vers DL-B1 (MEC)
 switchport mode trunk
 switchport trunk native vlan 999
 switchport trunk allowed vlan 110-113,120-122,130,190,191
 ip dhcp snooping trust
 ip arp inspection trust
!
ip dhcp snooping vlan 110-113,120-122,130,190,191
ip arp inspection vlan 110-113,120-122,130
vtp mode off
spanning-tree mode rapid-pvst
spanning-tree vlan 1-4094 priority 61440</pre>""")
    H.append("<h2>8. Sécurité de niveau 2 (première ligne)</h2><ul>"
             "<li><b>DHCP snooping</b> (+ option 82) : seuls les uplinks sont de confiance. <b>DAI</b> et <b>IP Source Guard</b> s'appuient sur sa table.</li>"
             "<li><b>IPv6 First Hop Security</b> : RA guard (seules les SVI des DL annoncent), DHCPv6 guard, ND inspection, source guard IPv6.</li>"
             "<li><b>Storm-control</b> broadcast et multicast sur les ports d'accès. <b>CDP</b> désactivé sur les ports d'accès, <b>LLDP-MED</b> gardé pour les téléphones.</li>"
             "<li><b>802.1X</b> contre DT-RAD1/2 (NPS) : VLAN dynamique selon le groupe AD (personnel / étudiant).</li>"
             "<li>" + V2 + " <b>Objets (caméras, badgeuses)</b> : une adresse MAC se lit et se copie, donc le MAB seul ne prouve rien (question Q10 "
             "de l'audit). Les caméras qui le supportent (la plupart des modèles récents) font du 802.1X EAP-TLS avec un certificat machine. Pour les "
             "autres, le MAB n'ouvre qu'une <b>ACL téléchargée</b> depuis RADIUS : seuls l'enregistreur ou le serveur de contrôle d'accès sont joignables, "
             "sur leurs ports. Un portable branché à la place d'une caméra, avec sa MAC, ne voit donc rien d'autre. Le port est coupé à la "
             "première violation et la supervision reçoit une alerte (le lien qui tombe sur un port de caméra est lui-même un événement).</li>"
             "<li>Gestion des switchs uniquement depuis la VRF ADM (SSH v2, SNMPv3 authPriv, TACACS+/RADIUS), jamais depuis les VLAN usagers.</li></ul>")
    H.append("<h2>9. Wi-Fi : SSID et VLAN</h2>")
    H.append(tableau(["SSID", "Sécurité", "VLAN bloc 1 / bloc 2", "VRF"], [
        ["AMU-Personnel", "WPA3-Entreprise (802.1X, NPS)", "514 (tout le bâtiment) " + V2, badge("USR")],
        ["AMU-Etudiants", "WPA3-Entreprise", "515 " + V2, badge("USR")],
        ["eduroam", "WPA3/WPA2-Entreprise, proxy RADIUS vers la fédération", "515 " + V2, badge("USR")],
        ["AMU-Invites", "OWE + portail captif du WLC, isolation des clients", "530 " + V2, badge("GST")]]).replace("VLAN bloc 1 / bloc 2", "VLAN"))
    H.append("<p>" + V2 + " Les bornes CW9164I sont en <b>mode local (commutation centrale)</b> : le trafic des clients remonte en tunnel CAPWAP "
             "jusqu'aux contrôleurs, qui le posent dans le VLAN du SSID. Ces VLAN ont leur passerelle sur le cœur. Un client garde la même adresse "
             "dans tout le bâtiment : passer du RDC au 1er étage ne coupe plus ses connexions (constat NET-01). Itinérance rapide 802.11r et OKC "
             "sur toutes les bornes.</p><ul>"
             "<li><b>Contrôleurs</b> : 2 × Catalyst 9800-L-F (4 ports 10G, jusqu'à 250 bornes et 5 000 clients, débit de 5 Gb/s extensible à "
             "10 Gb/s par licence) en <b>HA SSO</b>. Si l'actif tombe, le second reprend en moins d'une seconde sans déconnecter bornes ni clients.</li>"
             "<li><b>Débit</b> : 38 bornes et environ 1 500 clients. Le trafic Wi-Fi va surtout vers Internet (1 Gb/s) et vers l'AD : on reste loin des "
             "5 Gb/s.</li>"
             "<li><b>Gestion</b> : interface de gestion sans fil 10.13.60.70 (VLAN 907, VRF ADM), annoncée aux bornes par l'option DHCP 43.</li>"
             "<li>Le contrôleur virtuel C9800-CL de la v1 est retiré du cluster NM.</li></ul>")
    # NM
    H.append("<h2 class='saut'>10. Zone Net Management en détail</h2>"
             "<p>Deux hyperviseurs Proxmox et un <b>témoin</b> (QDevice) : le quorum tient avec deux voix sur trois, donc la perte d'un nœud ne bloque pas le cluster. "
             "Le stockage est local (ZFS miroir) et répliqué sur l'autre nœud par un câble direct 25G : pas de stockage partagé à acheter. "
             "Chaque service critique existe deux fois (un par nœud : DHCP, NTP, DNS, Teleport, collecteur de journaux " + V2 + ") ; seule la VM de supervision "
             "redémarre sur l'autre nœud en cas de panne (HA Proxmox). " + V2 + " Sa réplication passe de 5 minutes à <b>1 minute</b> (perte maximale d'une "
             "minute de métriques), et les journaux ne dépendent plus d'elle : ils sont reçus par les deux collecteurs LXC. Le contrôleur Wi-Fi n'est plus une VM.</p>"
             "<p>" + V2 + " Le témoin NM-WITNESS sert aussi de QDevice au cluster DT (même VLAN 902), et de serveur <b>NUT</b> qui commande l'arrêt ordonné "
             "de la salle sur batterie (voir le document énergie).</p><img src='nm_zone.png' alt='Zone Net Management'>")
    H.append(tableau(["Réseau", "Interfaces de chaque nœud", "Switch", "VLAN", "Rôle"], [
        ["ipmi", "iDRAC dédié 1G", "PVE1 → NM-SW1, PVE2 → NM-SW2", "901 access", "Console à distance, alimentation, même si l'OS est planté"],
        ["mgmt", "bond0 actif/secours : eno1 (SW1) + ens2f0 (SW2)", "les deux membres", "902 access", "GUI 8006, SSH, API, corosync lien 1 (secours)"],
        ["cluster", "eno2 1G dédié", "PVE1 → SW1, PVE2 → SW2, témoin → SW1", "903 access", "Corosync lien 0 : latence faible, pas de trafic parasite"],
        ["workload", "bond1 LACP : ens2f1 (SW1) + ens2f2 (SW2), pont vmbr1 VLAN-aware", "les deux membres (MEC)", "trunk 904", "Trafic des VM et conteneurs"],
        ["replication", "ens1f0 25G SFP28, câble DAC direct", "aucun", "905 (non tagué)", "Réplication ZFS, migration à chaud, MTU 9000"]]))
    H.append("""<pre># /etc/network/interfaces (NM-PVE1)
auto bond0
iface bond0 inet manual
    bond-slaves eno1 ens2f0
    bond-mode active-backup
    bond-primary eno1
auto vmbr0
iface vmbr0 inet static            # mgmt, VLAN 902 (port access côté switch)
    address 10.13.58.11/27
    gateway 10.13.58.1
    bridge-ports bond0
    bridge-stp off
iface vmbr0 inet6 static
    address 2001:660:5402:4902::11/64
    gateway 2001:660:5402:4902::1
auto eno2
iface eno2 inet static             # cluster, VLAN 903, corosync lien 0
    address 10.13.58.41/28
auto ens1f0
iface ens1f0 inet static           # réplication, câble direct vers NM-PVE2
    address 10.13.58.49/30
    mtu 9000
auto bond1
iface bond1 inet manual
    bond-slaves ens2f1 ens2f2
    bond-mode 802.3ad
    bond-xmit-hash-policy layer3+4
auto vmbr1
iface vmbr1 inet manual            # workload : les VM sont taguées 904
    bridge-ports bond1
    bridge-vlan-aware yes
    bridge-vids 904

# corosync : ring0 = 10.13.58.41/.42 (cluster), ring1 = 10.13.58.11/.12 (mgmt)
# pvecm qdevice setup 10.13.58.40   (NM-WITNESS)
# datacenter.cfg : migration: secure,network=10.13.58.48/30</pre>""")
    H.append("<p class='note'>" + V2 + " Le chiffrage v2 suit cette architecture (constat SYS-01) : 2 nœuds R660xs sans Ceph au lieu de 3, une carte 4×1G par nœud, "
             "le témoin NM-WITNESS, les kits de pile C9200L (EL-SW, NM-SW, DM-SW) et deux souscriptions Proxmox de moins pour ce cluster.</p>")
    H.append(clusters_dt_dmz())
    H.append("<h2>12. Points à valider</h2><ul><li>Nombre exact de switchs par local (le schéma général n'en montre que 4, le plan de câblage en prévoit 15).</li>"
             "<li>Référence exacte du module 10G du SN710 et support du LACP vers une paire StackWise Virtual (sinon : redundant actif/secours, même câblage).</li>"
             "<li>Modèles de caméras et badgeuses : support du 802.1X EAP-TLS (à exiger dans le cahier des charges du lot sûreté).</li>"
             "<li>Emplacement des postes d'administration (salle de supervision raccordée à NM-SW ou VLAN PAW dans les blocs).</li></ul></body></html>")
    return "\n".join(H)


def clusters_dt_dmz():
    """v2 : virtualisation du datacenter et de la DMZ (audit SYS-02)."""
    return "".join([
        "<h2 class='saut'>11. Clusters du datacenter et de la DMZ " + V2 + "</h2>",
        "<p>En v1, chaque service du datacenter et de la DMZ avait son serveur physique 1U (12 serveurs pour DNS, DHCP, RADIUS, AD, web, "
        "messagerie). L'audit (SYS-02) jugeait ce choix coûteux en achat, en place et en électricité. En v2, ces services sont des VM sur "
        "deux clusters Proxmox séparés, construits comme la zone NM (2 nœuds, ZFS répliqué en câble direct, HA) :</p>",
        tableau(["", "Cluster DT (datacenter)", "Cluster DMZ"], [
            ["Nœuds", "DT-PVE1, DT-PVE2 : Dell R660xs, 1 × 16 cœurs, 128 Go, 4 × 1,92 To SSD (ZFS miroir)",
             "DM-PVE1, DM-PVE2 : Dell R360, 8 cœurs, 64 Go, 4 × 960 Go SSD (ZFS miroir)"],
            ["VM", "DT-AD1 / DT-AD2 (VLAN 310, tier 0), DT-RAD1/2 (NPS) et DT-DHCP1/2 (VLAN 300) : une de chaque par nœud",
             "DM-RP1 / DM-RP2 (Caddy, un par nœud), DM-DNS1 / DM-DNS2 (le DNS public devient redondant), DM-WEB1, DM-MAIL1, DM-SRV1"],
            ["Quorum", "QDevice sur NM-WITNESS (VLAN 902), qui sert les deux clusters internes",
             "DM-WITNESS, témoin propre à la DMZ (VLAN 403) : aucun flux de la DMZ vers l'administration"],
            ["Réseaux de chaque nœud", "mgmt bond0 actif/secours → VLAN 902 ; corosync → VLAN 908 ; bond1 LACP 2×25G → trunk 300, 310 ; "
             "réplication 25G DAC 10.13.58.52/30 ; iDRAC → 901",
             "mgmt → VLAN 402 ; corosync → VLAN 403 ; bond1 LACP 2×10G → trunk 400, 401 ; réplication 10G DAC 172.16.13.112/30 ; iDRAC → 402"],
            ["Sauvegarde", "vzdump par le réseau de gestion vers DT-BKP1 (VLAN 909) : même VRF ADM, aucun passage par le Stormshield",
             "vzdump vers DT-BKP1 : seul flux DMZ → interne autorisé (tcp/8007, depuis DM-PVE1/2 uniquement)"],
            ["Administration", "Tier 0 : rôle Teleport dédié, MFA matériel, PAW tier 0 ; ni DT-PVE ni DT-BKP1 ne sont dans le domaine",
             "Via Teleport puis le FortiGate (VPN d'administration), comme les iDRAC de la DMZ en v1"]]),
        "<p><b>Pourquoi deux clusters et pas un seul.</b> Une VM de la DMZ et un contrôleur de domaine ne doivent jamais partager un hyperviseur : "
        "une faille d'évasion de VM en DMZ donnerait la main sur l'AD. Les hyperviseurs qui portent les contrôleurs de domaine sont eux-mêmes "
        "tier 0 (guide ANSSI PA-099). Les DMZ restent physiquement à part (switchs DM-SW, hyperviseurs, témoin), derrière le FortiGate.</p>"
        "<p><b>Licences Windows.</b> Une licence Windows Server Standard couvre 16 cœurs et deux VM. Les 6 VM Windows doivent pouvoir tourner sur un seul "
        "nœud de 16 cœurs (panne de l'autre) : il faut donc 3 licences par nœud, soit 6, comme en v1.</p>",
    ])


# ===========================================================================
# Architecture L3
# ===========================================================================
FLUX = [  # source, destination, autorisé
    ("USR", "T0 (DT-AD1/2) v2", "Kerberos, LDAP/LDAPS, DNS, SMB (SYSVOL, GPO), RPC restreint ; IPS actif"),
    ("USR", "SRV", "DHCP relayé vers DT-DHCP1/2 ; RADIUS non (seuls les switchs et les WLC parlent RADIUS)"),
    ("SRV (NPS, DHCP) v2", "T0", "LDAP/Kerberos/RPC vers les contrôleurs de domaine (authentification NPS, mise à jour DNS par le DHCP)"),
    ("T0 v2", "Internet", "<span class='ko'>interdit</span> : les contrôleurs de domaine ne sortent jamais. Mises à jour par un proxy limité à Windows Update (VRF SRV)"),
    ("USR", "Internet", "HTTP/HTTPS, DNS via les résolveurs internes, NTP via chrony ; SNAT .64/28"),
    ("USR", "DMZ", "HTTPS vers Caddy (site, applications), SMTP soumission/IMAPS vers MAIL1"),
    ("USR", "IOT / ADM / GST", "<span class='ko'>interdit</span>"),
    ("IOT", "SRV", "Caméras → enregistreur 10.13.48.60, badgeuses → serveur de contrôle d'accès 10.13.48.61 ; doublé par l'ACL téléchargée sur le port"),
    ("IOT", "Internet", "<span class='ko'>interdit</span> (mises à jour poussées depuis l'administration)"),
    ("GST", "Internet", "HTTP/HTTPS, DNS seulement ; SNAT .88/29 ; débit limité"),
    ("GST", "tout le reste", "<span class='ko'>interdit</span>"),
    ("SRV", "Internet", "Mises à jour (proxy), synchronisation eduroam ; SNAT .80/29"),
    ("ADM (Teleport, PAW)", "toutes les gestions", "SSH, HTTPS, SNMP, API des équipements : uniquement depuis Teleport 10.13.59.40-42 ; "
     "équipements tier 0 (DT-PVE, DT-BKP1, contrôleurs de domaine) : rôle Teleport tier 0 seulement"),
    ("DMZ-GEST (DM-PVE1/2) v2", "SAUVEGARDE (DT-BKP1)", "tcp/8007 seulement (envoi des sauvegardes des VM de la DMZ)"),
    ("SAUVEGARDE v2", "Internet", "HTTPS vers le stockage objet externalisé (copie immuable) ; SNAT .80/29"),
    ("toutes les VRF", "ADM services", "DHCP relayé vers Kea, NTP (chrony), syslog vers les collecteurs 10.13.59.55, traps SNMP vers la supervision"),
    ("Internet", "DMZ", "VIP : 443/80 → Caddy, 25 → MAIL1, 53 → DNS1 ; 443 VPN SSL admin → FortiGate"),
    ("DMZ", "interne", "<span class='ko'>interdit</span> sauf DM-MAIL1 → AD (LDAPS) et DM-SRV1 → SRV (port applicatif précis)"),
]


def politique_inspection():
    """v2 : audit SEC-01, débit du Stormshield."""
    return "".join([
        "<h3>Politique d'inspection du Stormshield " + V2 + "</h3>",
        "<p>Le SN710 est très rapide en simple filtrage à états, mais son débit chute quand l'analyse applicative (IPS, antivirus) est active "
        "sur tout le trafic. L'audit (SEC-01) craignait qu'une sauvegarde ou un gros transfert entre VRF le sature. Trois mesures :</p><ul>",
        "<li><b>Les gros flux ne le traversent plus</b> : les sauvegardes des hyperviseurs NM et DT restent dans la VRF ADM (VLAN 902 vers 909, routés "
        "par le cœur). Seule la DMZ envoie ses sauvegardes à travers les pare-feu, et c'est un petit volume, incrémental et dédupliqué.</li>",
        "<li><b>Raccordement direct au cœur</b> en 2 × 10G par nœud, sans passer par la pile C9200L.</li>",
        "<li><b>Profil adapté à chaque flux</b> :</li></ul>",
        tableau(["Flux", "Volume", "Profil"], [
            ["USR → T0 (AD), USR → SRV", "faible (authentification, GPO, DHCP)", "IPS complet, protocoles contrôlés"],
            ["IOT → SRV (caméras → enregistreur)", "≈ 15 caméras × 4-8 Mb/s, soit ≈ 0,1 Gb/s", "filtrage à états, IPS en mode léger (flux vidéo RTSP)"],
            ["SRV → T0", "faible", "IPS complet"],
            ["DMZ-GEST → SAUVEGARDE (tcp/8007)", "quelques Go par nuit", "filtrage à états seul (flux TLS chiffré, inspection inutile)"],
            ["Tout le reste", "—", "refusé et journalisé"]]),
        "<p class='sous'>Les débits du SN710 selon le profil d'analyse sont à vérifier sur la fiche constructeur et en maquette. Si la supervision "
        "montre un taux d'occupation durable au-dessus de 60 %, la piste est un SN910 (même gamme, même configuration).</p>",
        "<h3>Inspection TLS sur le FortiGate " + V2 + "</h3>",
        "<p>Plus de 90 % du trafic vers Internet est chiffré : sans déchiffrement, l'antivirus et l'IPS ne voient que les noms de domaine "
        "(question Q7 de l'audit). Suivant les recommandations de l'ANSSI sur l'analyse des flux HTTPS :</p><ul>",
        "<li><b>Postes gérés</b> (VLAN PERS et ETU des salles de TP, postes du domaine) : inspection complète sur le FortiGate. Le certificat de "
        "l'autorité interne du FortiGate est déployé par GPO.</li>",
        "<li><b>Liste d'exclusion</b> : banques, santé, administrations, messageries personnelles, et toute application qui épingle son certificat. "
        "Le trafic de ces catégories n'est pas déchiffré.</li>",
        "<li><b>Appareils personnels</b> (Wi-Fi étudiants, eduroam, invités) : <b>pas de déchiffrement</b> (impossible sans installer un certificat "
        "sur l'appareil, et intrusif). Le contrôle se fait sur le SNI et la réputation des domaines, plus un filtrage DNS sur les résolveurs.</li>",
        "<li><b>Cadre légal</b> : charte informatique annexée au règlement intérieur, information des utilisateurs, aucune conservation des contenus "
        "déchiffrés. Un DPIA (RGPD) est à faire avec le DPO de l'AMU.</li></ul>",
    ])


def journalisation():
    """v2 : audit SEC-04, conservation légale des journaux."""
    return "".join([
        "<h2 class='saut'>10. Journalisation et conservation légale " + V2 + "</h2>",
        "<p>Un établissement qui donne accès à Internet doit conserver un an les données qui identifient l'auteur d'une connexion (article L34-1 "
        "et R10-13 du code des postes et communications électroniques). Pour nous, cela veut dire : journaux NAT/PAT du FortiGate (adresse privée, "
        "port, adresse publique, horodatage), baux DHCP, authentifications 802.1X et Wi-Fi (NPS), portail invités. En v1, tout reposait sur un "
        "conteneur syslog dans la VM de supervision (constat SEC-04). La chaîne v2 suit le guide ANSSI sur l'architecture d'un système de "
        "journalisation :</p>",
        tableau(["Étape", "Comment"], [
            ["Production", "équipements réseau, pare-feu, NPS, DHCP, hyperviseurs ; horloge commune (chrony)"],
            ["Collecte", "2 LXC rsyslog (10.13.59.56 sur NM-PVE1, .57 sur NM-PVE2) derrière la VIP .55 ; TCP + TLS, file d'attente sur disque si un collecteur est absent"],
            ["Stockage légal", "fichiers bruts par jour et par source, compressés (zstd). Chaque jour, une empreinte SHA-256 est horodatée (RFC 3161) : "
             "on peut prouver qu'un fichier n'a pas été modifié. Conservation 1 an, puis suppression automatique"],
            ["Copies", "les archives sont sauvegardées par DT-BKP1, donc sur le disque hors ligne et dans le stockage immuable (voir PRA)"],
            ["Recherche", "Loki (dans la VM de supervision) indexe 90 jours pour l'exploitation ; les réquisitions se traitent sur les archives brutes"],
            ["Accès", "lecture des archives réservée à deux personnes nommées (registre des accès), via Teleport"]]),
        "<p><b>Volume estimé</b> : environ 600 utilisateurs simultanés et quelques milliers de sessions par jour et par utilisateur, soit "
        "3 à 5 millions de lignes par jour pour le NAT, environ 1,5 Go brut par jour, 0,15 Go compressé. Sur un an, on compte environ 60 Go "
        "compressés. Un volume ZFS de 500 Go par collecteur laisse une large marge.</p>",
    ])


def doc_l3(css):
    H = tete("Architecture de niveau 3", "Points 03, 05 et 07 · VRF, routage IPv4/IPv6, bordure BGP, NAT, filtrage entre zones, services IP", css, [
        "<b>Tier 0</b> (SEC-02) : contrôleurs de domaine dans le VLAN 310, passerelle sur le Stormshield, sans accès Internet.",
        "<b>Stormshield</b> (SEC-01) : raccordé au cœur en 2×10G, politique d'inspection par flux ; les sauvegardes ne le traversent plus.",
        "<b>Inspection TLS</b> (question Q7) : déchiffrement sur le FortiGate pour les postes gérés, avec liste d'exclusion ; jamais sur les appareils personnels.",
        "<b>BGP</b> (Q4) : iBGP entre les routeurs, annonce conditionnelle vers le FAI 2 (plus d'asymétrie), BFD vers les opérateurs.",
        "<b>PMTUD</b> : ICMP « Packet Too Big » explicitement autorisé, MTU 1500 sur les hôtes, ajustement du MSS sur les tunnels.",
        "<b>Journalisation</b> (SEC-04) : chaîne dédiée, conservation légale d'un an, archives scellées et copiées hors ligne.",
        "<b>Wi-Fi</b> (NET-01) : passerelles des VLAN Wi-Fi sur le cœur."])
    H += ["<div class='cles'>",
          "<div class='cle'><b>5 VRF + tier 0</b>cloisonnées au cœur, reliées seulement par le Stormshield</div>",
          "<div class='cle'><b>OSPFv3 (v4 + v6)</b>par VRF entre le cœur et les blocs, BFD</div>",
          f"<div class='cle'><b>eBGP AS{D.AS_SITE}</b>double opérateur, FAI 1 prioritaire</div>",
          "<div class='cle'><b>2 pare-feu en série</b>FortiGate (Internet, DMZ, NAT) puis Stormshield (zones internes)</div></div>",
          "<h2>1. Vue d'ensemble</h2><ol>",
          "<li><b>Bordure</b> : EL-RTR1 (FAI 1, AMU/RENATER) et EL-RTR2 (FAI 2) parlent eBGP avec les opérateurs, et iBGP entre eux " + V2 + ". "
          "Le /24 public n'est annoncé au FAI 2 que si le FAI 1 est perdu.</li>",
          "<li><b>FortiGate</b> (pare-feu externe, deux marques différentes comme le recommande l'ANSSI) : choix du lien de sortie (SD-WAN), NAT, publication de la DMZ, "
          "VPN d'administration, inspection TLS des postes gérés " + V2 + ".</li>",
          "<li><b>Stormshield</b> (pare-feu interne, qualifié ANSSI) : seul point de passage entre les VRF, raccordé directement au cœur " + V2 + ". "
          "Il porte la matrice de flux du paragraphe 4 et la passerelle du tier 0 (VLAN 310).</li>",
          "<li><b>Cœur</b> : VRF-lite, passerelles du datacenter, de l'administration et du Wi-Fi " + V2 + ", une route par défaut par VRF vers le Stormshield.</li>",
          "<li><b>Distribution</b> : passerelles des VLAN d'un bloc, OSPF par VRF vers le cœur. Le routage entre VLAN d'une même VRF se fait ici, à pleine vitesse "
          "(ACL de base entre personnel et étudiants).</li></ol>",
          "<div class='paysage'><img class='schema' src='architecture_l3.png' alt='Schéma L3'></div>",
          "<h2>2. VRF</h2>"]
    H.append(tableau(["VRF", "Id", "Rôle", "Présente sur", "Résumés IPv4", "Résumés IPv6"],
                     [[badge(k), str(v["id"]), e(v["role"]), "CL, DL-B1, DL-B2" if k in ("USR", "IOT", "GST", "ADM") else "CL",
                       "<br>".join(x for x in D.RESUMES[k] if ":" not in x), "<br>".join(x for x in D.RESUMES[k] if ":" in x)]
                      for k, v in D.VRF.items()], mono=(4, 5)))
    H.append("<p>" + V2 + " <b>Zone tier 0</b> (VLAN 310, contrôleurs de domaine) : ce n'est pas une VRF du cœur. Le VLAN traverse CL et DT-SW au niveau 2, "
             "et sa passerelle 10.13.52.1 / 2001:660:5402:4310::1 est une interface du Stormshield. Tout ce qui parle à un contrôleur de domaine, y compris "
             "un serveur du VLAN 300, passe donc par le pare-feu (guide ANSSI PA-099 : étanchéité entre tier 0 et tier 1).</p>")
    H.append("<p>Pourquoi des VRF plutôt que des ACL sur le cœur : une erreur d'ACL ouvre un flux, alors qu'entre deux VRF il n'existe <b>aucune route</b>. "
             "Le filtrage est fait par un vrai pare-feu (états, journaux, IPS), et le cœur reste simple. C'est le cloisonnement demandé par le guide ANSSI "
             "sur l'administration sécurisée (SI d'administration séparé) et par la note sur l'interconnexion des objets connectés.</p>")
    H.append("<h2>3. Passerelles par défaut</h2>")
    H.append(tableau(["Où", "Passerelle", "Redondance"], [
        ["VLAN des blocs (1xx, 2xx)", "SVI .1 / ::1 sur DL-B1 ou DL-B2", "StackWise Virtual : une seule passerelle logique, reprise en &lt; 1 s si un DL tombe ; pas de HSRP/VRRP nécessaire"],
        ["VLAN 300, 5xx " + V2 + ", 9xx", "SVI .1 / ::1 sur CL (.65 pour le 907, .129 pour le 909)", "StackWise Virtual"],
        ["VLAN 310 (tier 0) " + V2, "Stormshield 10.13.52.1 / ::1", "HA Stormshield (adresse partagée par le cluster)"],
        ["DMZ 400-402", "FortiGate .1 / .33 / .65", "FGCP : adresse virtuelle et MAC virtuelle reprises par le passif"],
        ["Services DMZ publiés", "VIP Caddy 172.16.13.10 (keepalived/VRRP entre DM-RP1 et DM-RP2)", "VRRP, préemption désactivée"],
        ["Teleport", "VIP 10.13.59.40 (keepalived entre les deux LXC)", "VRRP"],
        ["Clients IPv6", "fe80::1 annoncée par RA (priorité high, durée 1800 s)", "identique sur toutes les SVI"]]))
    H.append("<h2>4. Matrice des flux entre zones (Stormshield et FortiGate)</h2><p>Politique par défaut : tout refuser et journaliser. Seuls ces flux sont ouverts.</p>")
    marque = lambda x: e(x.replace(" v2", "")) + (" " + V2 if x.endswith(" v2") else "")
    H.append(tableau(["Source", "Destination", "Autorisé"], [[marque(a), marque(b), c] for a, b, c in FLUX]))
    H.append(politique_inspection())
    H.append("<h2 class='saut'>5. Routage interne</h2><h3>Cœur ↔ distribution : OSPF par VRF</h3>")
    H.append(tableau(["Paramètre", "Valeur"], [
        ["Processus", "OSPFv3 avec deux address-families, IPv4 et IPv6 (RFC 5838), un processus par VRF : 10 = USR, 20 = IOT, 30 = GST, 90 = ADM"],
        ["Zone", "Zone 0 unique par VRF : 2 routeurs logiques et ~15 préfixes par VRF, un découpage en zones n'apporte rien"],
        ["Router-id", "Loopback0 : CL 10.13.0.1, DL-B1 10.13.0.2, DL-B2 10.13.0.3"],
        ["Interfaces", "passive-interface default ; actives : sous-interfaces Po101.x / Po102.x (type point-to-point)"],
        ["Liens", "/31 IPv4 et /127 IPv6 ; MTU 9198 ; BFD 300 ms × 3"],
        ["Authentification", "OSPFv3 avec trailer d'authentification HMAC-SHA-256 (RFC 7166, key-chain), IPv4 comme IPv6"],
        ["Route par défaut", "le cœur l'injecte dans chaque VRF (default-information originate), seulement si sa route statique vers le Stormshield est présente"],
        ["Convergence", "panne d'un membre SVL ou d'un lien : agrégat, pas de recalcul OSPF ; panne d'un bloc : BFD &lt; 1 s"]]))
    H.append("<h3>Cœur ↔ Stormshield : routes statiques</h3><p>Pas de routage dynamique avec les pare-feu (règle ANSSI : la table d'un pare-feu ne doit pas pouvoir être modifiée depuis le réseau interne).</p>")
    rows = []
    for vid, n, vrf, v4, a, b_, p6 in D.TRANSITS[:5]:
        rows.append([badge(vrf), f"0.0.0.0/0 → {D.VLANS[vid]['b'][1]}<br>::/0 → {D.VLANS[vid]['b'][2]}",
                     "<br>".join(f"{r} → {D.VLANS[vid]['a'][1] if ':' not in r else D.VLANS[vid]['a'][2]}" for r in D.RESUMES[vrf])])
    H.append(tableau(["VRF", "Sur CL (vers le Stormshield)", "Sur le Stormshield (vers CL)"], rows, mono=(1, 2)))
    H.append("<p>Stormshield : route par défaut 0.0.0.0/0 → 10.13.3.1 et ::/0 → 2001:660:5402:4F10::1 (FortiGate). "
             "FortiGate : 10.13.0.0/16 et 2001:660:5402:4000::/52 (sauf DMZ) → 10.13.3.2 / 2001:660:5402:4F10::2.</p>")
    H.append("<h2>6. Bordure : BGP et choix du lien</h2>")
    H.append(tableau(["", "EL-RTR1 (FAI 1)", "EL-RTR2 (FAI 2)"], [
        ["Voisin", "AS2457, 139.124.112.1 et 2001:660:5402:4FF0::", f"{D.FAI2['as']}, 203.0.113.1 et 2001:db8:ffff::"],
        ["iBGP " + V2, "EL-RTR2 139.124.112.6 (câble direct)", "EL-RTR1 139.124.112.5"],
        ["Annonce", "139.124.112.0/24, 2001:660:5402:4000::/52",
         f"139.124.112.0/24 <b>seulement si la route par défaut du FAI 1 a disparu</b> (annonce conditionnelle) {V2} ; {D.FAI2['pa6']} non annoncé (PA)"],
        ["Reçu", "route par défaut seulement (v4 + v6)", "route par défaut seulement"],
        ["Préférence sortante", "local-pref 200", "local-pref 100"],
        ["Filtres", "prefix-list sortante stricte (pas de transit), entrée : bogons refusés, max-prefix", "idem"],
        ["Protection", "TTL security (GTSM), MD5/TCP-AO avec l'opérateur, uRPF strict côté opérateur", "idem"],
        ["Détection de panne " + V2, "BFD 300 ms × 3 si l'opérateur le propose, sinon timers 10/30 s (au lieu de 60/180)", "idem"],
        ["Vers le FortiGate", "statiques 139.124.112.32/27 et .64/26 → .14 ; ::/0 côté LAN → 4F00::e", "statiques → .22 ; 4F01::e"]]))
    H.append("<p><b>FortiGate SD-WAN</b> : deux membres (OUT-A via 139.124.112.9, OUT-B via .17), règle « priorité au FAI 1 » avec sonde SLA (ping et HTTP toutes les "
             "500 ms vers deux cibles). Si OUT-A perd la sonde, le trafic passe sur OUT-B en quelques secondes. Les flux publiés (VIP) restent possibles par les deux chemins.</p>"
             "<p><b>IPv6 en secours</b> : le /52 AMU n'est routé que par l'AMU. Si le FAI 1 tombe, le FortiGate traduit le préfixe interne vers le préfixe du FAI 2 "
             f"(<b>NPTv6</b>, RFC 6296, {D.FAI2['pa6']}) sans état, puis revient au natif quand le FAI 1 revient.</p>"
             "<p>" + V2 + " <b>Pas de routage asymétrique.</b> En v1, le /24 était annoncé aux deux opérateurs (prepend ×3 vers le FAI 2). Le prepend "
             "ne garantit rien : un opérateur qui préfère ses routes vers le FAI 2 (local-preference) y envoie quand même le trafic retour, et "
             "le FortiGate, pare-feu à états, rejette un retour qui arrive par OUT-B pour une session sortie par OUT-A (question Q4 de l'audit). "
             "Désactiver le contrôle d'état (<code>asymroute</code>) supprimerait la protection : nous l'écartons. En v2, EL-RTR2 n'annonce le "
             "/24 au FAI 2 que si la route par défaut apprise du FAI 1 (repérée par une communauté, transmise en iBGP) a disparu. En marche "
             "normale, tout entre et sort par le FAI 1 ; en secours, tout passe par le FAI 2. Avec BFD, la bascule prend moins d'une seconde "
             "côté BGP au lieu de 180 s (hold-time par défaut). L'AMU doit annoncer le /24 lui-même, en plus de son /16, pour que les deux "
             "chemins soient comparables.</p>")
    H.append("<h2 class='saut'>7. NAT et publication</h2>")
    H.append(tableau(["Type", "Source / adresse interne", "Adresse publique", "Remarque"], [
        ["SNAT (PAT)", "VRF USR", "139.124.112.64/28", "pool overload, journaux conservés 1 an (paragraphe 10)"],
        ["SNAT (PAT)", "VRF SRV, ADM", "139.124.112.80/29", ""],
        ["SNAT (PAT)", "VRF GST", "139.124.112.88/29", "séparé pour la traçabilité"],
        ["VIP 1:1", "172.16.13.10 (VIP Caddy)", "139.124.112.33", "80, 443 ; IPv6 : 2001:660:5402:4400::10 sans NAT"],
        ["VIP port", "172.16.13.21 (MAIL1)", "139.124.112.34", "25, 465, 587, 993"],
        ["VIP port", "172.16.13.20 (DNS1)", "139.124.112.35", "53 TCP/UDP (DNS public faisant autorité)"],
        ["Local", "FortiGate", "139.124.112.36", "VPN SSL/IPsec des administrateurs, puis Teleport"],
        ["IPv6", "tout le site", "—", "aucun NAT (adresses globales), sauf NPTv6 en secours sur le FAI 2"]], mono=(1, 2)))
    H.append("<h2>8. IPv6 : détails</h2>")
    H.append(tableau(["VLAN", "Attribution", "Drapeaux RA", "Détail"], [
        ["Usagers filaires et Wi-Fi (USR)", "SLAAC + DHCPv6 sans état", "A=1, M=0, O=1", "DNS par RDNSS (RFC 8106) et DHCPv6 ; adresses temporaires autorisées"],
        ["Invités (GST)", "SLAAC", "A=1, M=0, O=0", "DNS par RDNSS"],
        ["Objets (IOT)", "DHCPv6 avec état (Kea, réservations DUID) ou IPv4 seul", "A=0, M=1", "selon le support des équipements"],
        ["Serveurs, admin, DMZ", "statique", "A=0, M=0", "terminaison identique à l'IPv4"],
        ["Liens point à point", "/127", "RA supprimées", "RFC 6164 ; un /64 réservé par lien"]]))
    H.append("<p>ICMPv6 indispensable autorisé sur les pare-feu (RFC 4890 : Packet Too Big, ND, échos limités). RA guard et DHCPv6 guard sur l'accès (voir L2).</p>"
             "<h3>MTU et découverte du MTU du chemin " + V2 + "</h3><ul>"
             "<li>Les grandes trames (MTU 9198) ne servent que sur les liens d'infrastructure : agrégats cœur ↔ distribution, liens SVL, réplication "
             "(9000). Tous les hôtes, VM et SVI d'utilisateurs restent à <b>1500</b> : un poste ne peut pas émettre une trame qu'Internet refuserait.</li>"
             "<li>Les deux pare-feu laissent passer, dans tous les sens, <b>ICMPv4 type 3 code 4</b> (fragmentation nécessaire) et <b>ICMPv6 type 2</b> "
             "(Packet Too Big), sans quoi les connexions TCP se bloquent en silence quand un lien a un MTU plus petit.</li>"
             "<li>Ajustement du MSS (<code>tcp-mss</code>) sur les tunnels du FortiGate (VPN d'administration, MPLS/IPsec vers le site jumeau), "
             "dont l'encapsulation réduit le MTU utile.</li></ul>")
    H.append("<h2>9. Services IP</h2>")
    H.append(tableau(["Service", "Serveurs", "Configuration réseau"], [
        ["DHCPv4 usagers", "DT-DHCP1/2 10.13.48.31-32 (basculement)", "ip helper-address sur les SVI USR des DL (le relais traverse le Stormshield USR → SRV)"],
        ["DHCP IOT, GST, ADM", "Kea 10.13.59.11-12 (haute dispo hot-standby)", "ip helper-address ; option 43 pour les bornes (WLC 10.13.60.70) " + V2],
        ["DHCPv6", "DT-DHCP (USR, sans état), Kea (IOT)", "ipv6 dhcp relay destination"],
        ["DNS", "AD 10.13.52.11-12 " + V2 + " pour les usagers ; Unbound 10.13.59.31-32 pour l'infrastructure ; DM-DNS1/2 publics", "résolution Internet par les Unbound uniquement (les AD leur transmettent)"],
        ["NTP", "chrony 10.13.59.21-22 (sources : ntp RENATER et GPS/NTS)", "tous les équipements, authentifié"],
        ["Journaux " + V2, "collecteurs rsyslog 10.13.59.56-57 (VIP .55)", "source = Loopback0 ou interface de gestion ; TCP + TLS (RFC 5425)"],
        ["Supervision", "VM supervision 10.13.59.50 (traps, LibreNMS, Loki, Grafana)", "SNMPv3 authPriv"],
        ["AAA équipements", "DT-RAD1/2 (RADIUS) ou TACACS+", "source Loopback0, VRF ADM"]]))
    H.append(journalisation())
    H.append("<h2 class='saut'>11. Extraits de configuration</h2>")
    H.append("""<pre>! ===== CL (cœur, IOS-XE) : VRF et route par défaut vers le Stormshield
vrf definition USR
 address-family ipv4
 address-family ipv6
!
interface Vlan1010
 description TR-USR vers EL-SNS
 vrf forwarding USR
 ip address 10.13.2.1 255.255.255.248
 ipv6 address 2001:660:5402:4F21::1/64
!
interface Port-channel101.10
 description DL-B1 VRF USR
 encapsulation dot1Q 10
 vrf forwarding USR
 ip address 10.13.1.0 255.255.255.254
 ipv6 address 2001:660:5402:4F31::/127
 ip ospf network point-to-point
 bfd interval 300 min_rx 300 multiplier 3
!
ip route vrf USR 0.0.0.0 0.0.0.0 10.13.2.2 name SNS
ipv6 route vrf USR ::/0 2001:660:5402:4F21::2
!
router ospfv3 10
 router-id 10.13.0.1
 address-family ipv4 unicast vrf USR
  passive-interface default
  no passive-interface Port-channel101.10
  no passive-interface Port-channel102.10
  default-information originate
 address-family ipv6 unicast vrf USR
  passive-interface default
  no passive-interface Port-channel101.10
  no passive-interface Port-channel102.10
  default-information originate</pre><pre>! ===== DL-B1 : passerelle d'un VLAN usager
interface Vlan111
 description ETU-B1
 vrf forwarding USR
 ip address 10.13.16.1 255.255.254.0
 ip helper-address 10.13.48.31
 ip helper-address 10.13.48.32
 ipv6 address FE80::1 link-local
 ipv6 address 2001:660:5402:4111::1/64
 ipv6 nd other-config-flag
 ipv6 nd router-preference High
 ipv6 dhcp relay destination 2001:660:5402:4300::31
 ip access-group ETU-VERS-PERS in</pre><pre>! ===== EL-RTR1 : BGP vers AMU / RENATER
router bgp 65013
 bgp router-id 139.124.112.2
 neighbor 139.124.112.1 remote-as 2457
 neighbor 139.124.112.1 ttl-security hops 1
 neighbor 139.124.112.1 password 7 ********
 neighbor 2001:660:5402:4FF0:: remote-as 2457
 address-family ipv4
  network 139.124.112.0 mask 255.255.255.0
  neighbor 139.124.112.1 prefix-list SORTIE-V4 out
  neighbor 139.124.112.1 prefix-list DEFAUT-SEUL in
  neighbor 139.124.112.1 route-map LP200 in
 address-family ipv6
  network 2001:660:5402:4000::/52
  neighbor 2001:660:5402:4FF0:: activate
  neighbor 2001:660:5402:4FF0:: prefix-list SORTIE-V6 out
!
ip route 139.124.112.0 255.255.255.0 Null0 tag 666
ip route 139.124.112.32 255.255.255.224 139.124.112.14
ip route 139.124.112.64 255.255.255.192 139.124.112.14
ip prefix-list SORTIE-V4 permit 139.124.112.0/24
! v2 : la route par défaut de l'AMU est marquée et transmise à EL-RTR2 en iBGP
route-map LP200 permit 10
 set local-preference 200
 set community 65013:2457
router bgp 65013
 neighbor 139.124.112.6 remote-as 65013
 neighbor 139.124.112.6 update-source GigabitEthernet0/0/3
 neighbor 139.124.112.1 fall-over bfd
 address-family ipv4
  neighbor 139.124.112.6 activate
  neighbor 139.124.112.6 send-community
  neighbor 139.124.112.6 next-hop-self</pre><pre>! ===== EL-RTR2 (v2) : annonce du /24 au FAI 2 seulement si le FAI 1 est perdu
ip bgp-community new-format
ip community-list standard DEPUIS-FAI1 permit 65013:2457
ip prefix-list PL-PA permit 139.124.112.0/24
ip prefix-list PL-DEFAUT permit 0.0.0.0/0
route-map ANNONCE-PA permit 10
 match ip address prefix-list PL-PA
route-map FAI1-VIVANT permit 10
 match ip address prefix-list PL-DEFAUT
 match community DEPUIS-FAI1
!
router bgp 65013
 neighbor 139.124.112.5 remote-as 65013
 neighbor 203.0.113.1 remote-as 64496
 neighbor 203.0.113.1 ttl-security hops 1
 neighbor 203.0.113.1 fall-over bfd
 address-family ipv4
  network 139.124.112.0 mask 255.255.255.0
  neighbor 203.0.113.1 advertise-map ANNONCE-PA non-exist-map FAI1-VIVANT
  neighbor 203.0.113.1 prefix-list SORTIE-V4 out
  neighbor 203.0.113.1 prefix-list DEFAUT-SEUL in</pre><pre># ===== FortiGate : SD-WAN, FAI 1 prioritaire
config system sdwan
    set status enable
    config members
        edit 1  set interface "OUT-A"  set gateway 139.124.112.9   next
        edit 2  set interface "OUT-B"  set gateway 139.124.112.17  next
    end
    config health-check
        edit "internet"  set server "193.51.24.1" "9.9.9.9"  set members 1 2  set interval 500  next
    end
    config service
        edit 1  set name "FAI1-prioritaire"  set mode priority  set priority-members 1 2  set health-check "internet"  next
    end
end</pre>""")
    H.append("<h2>12. Tests de validation (maquette, point 06)</h2>")
    H.append(tableau(["Test", "Résultat attendu"], [
        ["Couper un membre du cœur (CL-SW1)", "aucune perte de route ; &lt; 1 s de coupure (agrégats)"],
        ["Couper DL-SW1", "le bloc 1 reste joignable par DL-SW2, passerelle inchangée"],
        ["Couper le FAI 1", "SD-WAN bascule sur OUT-B en &lt; 3 s ; IPv6 sort en NPTv6"],
        ["Basculer le FortiGate ou le Stormshield actif", "sessions conservées (synchronisation des sessions)"],
        ["Un poste étudiant tente SSH vers 10.13.56.0/24", "refusé et journalisé par le Stormshield (pas de route USR → ADM au cœur)"],
        ["Un invité tente d'atteindre 10.13.52.11 (contrôleur de domaine)", "refusé"],
        ["Éteindre NM-PVE1", "Kea, NTP, DNS, Teleport, journaux toujours servis par NM-PVE2 ; VM supervision redémarrée en ~2 min (perte ≤ 1 min)"],
        ["Appel visio sur le Wi-Fi en montant du RDC au 1er étage " + V2, "même adresse IP, appel non coupé (itinérance 802.11r &lt; 50 ms)"],
        ["Éteindre le WLC actif " + V2, "le WLC de secours reprend (SSO) sans déconnecter bornes ni clients"],
        ["Couper le FAI 1 (BGP) " + V2, "le /24 apparaît chez le FAI 2 en moins de 2 s (BFD) ; retour par le même chemin que l'aller"],
        ["Depuis DT-RAD1 (VLAN 300), tenter SMB/RPC vers DT-AD1 hors flux autorisés " + V2, "refusé et journalisé par le Stormshield (passerelle du tier 0)"],
        ["Supprimer une sauvegarde avec le jeton API d'un hyperviseur " + V2, "refusé (droit DatastoreBackup sans suppression)"],
        ["Restaurer une VM depuis le disque hors ligne " + V2, "VM restaurée sur DT-PVE2, durée mesurée (objectif de reprise)"],
        ["traceroute et ping v4/v6 de chaque VLAN vers Internet", "sortie par l'adresse SNAT prévue ; IPv6 sans NAT"]]))
    H.append("<h2>12. Points à valider avec la DSI AMU</h2><ul>"
             "<li>Attribution du /24 public (139.124.112.0/24 est une proposition) et du /52 IPv6 dans 2001:660:5402::/48.</li>"
             "<li>Raccordement au réseau du campus : eBGP avec AS privé, ou routage statique fourni par l'AMU (dans ce cas EL-RTR1 garde une route statique).</li>"
             "<li>Lettre d'autorisation (LOA) pour annoncer le /24 par le FAI 2, ou à défaut un préfixe du FAI 2 en NAT de secours.</li>"
             "<li>Site jumeau : MPLS L3VPN avec une VPN par VRF (route-target), point 07.</li>"
             "<li>" + V2 + " Annonce du /24 par l'AMU (en plus du /16) et support de BFD par les deux opérateurs.</li></ul></body></html>")
    return "\n".join(H)
