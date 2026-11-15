"""Schémas : zone Net Management du schéma principal, schéma logique L2, schéma logique L3."""
import xml.etree.ElementTree as ET

import donnees as D
from drawio import Page, ecrire, h

ENCRE = "#101217"
COUL = {nom: c for nom, _, c in D.NM_RESEAUX}

# ===========================================================================
# 1. Zone Net Management du schéma principal (même échelle : polices de 30 à 90 px)
# ===========================================================================
NM_ZONE = (4280, 1655, 8210, 4840)          # rectangle existant CVoWMKzBPITZB_2SDfIO-11
GARDER = {"CVoWMKzBPITZB_2SDfIO-11", "CVoWMKzBPITZB_2SDfIO-13"}
A_SUPPRIMER = {"9UCobsFVLry4QQOgntYh-3", "cl-nm1-ell", "cl-nm1a", "9UCobsFVLry4QQOgntYh-1",
               "9UCobsFVLry4QQOgntYh-7", "9UCobsFVLry4QQOgntYh-8"}
ICONE_SWITCH = ("sketch=0;points=[[0.015,0.015,0],[0.985,0.015,0],[0.985,0.985,0],[0.015,0.985,0],[0.25,0,0],[0.5,0,0],"
                "[0.75,0,0],[1,0.25,0],[1,0.5,0],[1,0.75,0],[0.75,1,0],[0.5,1,0],[0.25,1,0],[0,0.75,0],[0,0.5,0],[0,0.25,0]];"
                "verticalLabelPosition=bottom;html=1;verticalAlign=top;aspect=fixed;align=center;pointerEvents=1;"
                "shape=mxgraph.cisco19.rect;prIcon=l2_switch;fillColor=#FAFAFA;strokeColor=#005073;fontSize=60;")
ICONE_POSTE = ("points=[[0.03,0.03,0],[0.5,0,0],[0.97,0.03,0],[1,0.4,0],[0.97,0.745,0],[0.5,1,0],[0.03,0.745,0],[0,0.4,0]];"
               "verticalLabelPosition=bottom;sketch=0;html=1;verticalAlign=top;aspect=fixed;align=center;pointerEvents=1;"
               "shape=mxgraph.cisco19.workstation2;fillColor=#fafafa;strokeColor=#005073;fontSize=44;fontStyle=1;")


def _dans_zone(c, cells):
    g = c.find("mxGeometry")
    x0, y0, x1, y1 = NM_ZONE
    if c.get("vertex") and g is not None and g.get("x") is not None:
        x, y = float(g.get("x")), float(g.get("y"))
        return x0 <= x <= x1 and y0 <= y <= y1
    return False


def patcher_principal(source, sortie):
    """Supprime l'ancienne zone NM (et l'icône Teleport isolée) puis redessine la zone façon pve-1 / pve-2 / witness."""
    arbre = ET.parse(source)
    racine = arbre.getroot().find("diagram/mxGraphModel/root")
    cells = {c.get("id"): c for c in racine.iter("mxCell")}
    for i in [i for i in cells if i.startswith("nm2-")]:  # relance : on retire ce que ce script a déjà dessiné
        racine.remove(cells.pop(i))
    supp = {i for i, c in cells.items() if (_dans_zone(c, cells) and i not in GARDER)} | A_SUPPRIMER
    for i, c in cells.items():  # liens accrochés à un élément supprimé ou dont un bout est dans la zone
        if c.get("edge") and (c.get("source") in supp or c.get("target") in supp):
            supp.add(i)
        elif c.get("edge"):
            for p in c.iter("mxPoint"):
                if p.get("as") in ("sourcePoint", "targetPoint") and not c.get(p.get("as")[:-5]):
                    x, y = float(p.get("x", 0)), float(p.get("y", 0))
                    if NM_ZONE[0] <= x <= NM_ZONE[2] and NM_ZONE[1] <= y <= NM_ZONE[3]:
                        supp.add(i)
    supp |= {i for i in V2_SUPPR if i in cells}
    for i, c in cells.items():  # v2 : liens des serveurs physiques retirés
        if c.get("edge") and (c.get("source") in V2_SUPPR or c.get("target") in V2_SUPPR):
            supp.add(i)
    supp &= set(cells)
    for i in supp:
        racine.remove(cells[i])
    v2_retoucher(cells)
    cells["CVoWMKzBPITZB_2SDfIO-11"].find("mxGeometry").set("height", "3300")  # place pour la légende
    p = Page("tmp", "tmp")
    p.n = 0
    dessiner_nm(p)
    dessiner_piles(p)
    dessiner_v2(p)
    for c in p.cellules:
        c.set("id", "nm2-" + c.get("id"))
        for k in ("source", "target"):
            if c.get(k) and not c.get(k).startswith(("CVo", "cl-", "dt", "kR", "9U", "nm2-", "fw-", "rt-", "dmz-", "eg-", "wan-")):
                c.set(k, "nm2-" + c.get(k))
        racine.append(c)
    ET.indent(arbre)
    arbre.write(sortie, encoding="unicode")
    return len(supp)


def _guest(p, x, y, w, hh, type_, nom, ip4, couleur="#E3EEF6", trait="#005073", pointille=False):
    st = (f"rounded=1;arcSize=8;whiteSpace=wrap;html=1;fillColor={couleur};strokeColor={trait};strokeWidth=4;fontSize=30;"
          f"verticalAlign=middle;{'dashed=1;' if pointille else ''}")
    return p.boite(f"<i>{h(type_)}</i><br><b>{h(nom)}</b><br><font style='font-size:28px'>{h(ip4)}</font>", x, y, w, hh, st)


def dessiner_nm(p):
    x0 = 4280
    # --- hyperviseurs ---------------------------------------------------------------------------------
    st_pve = "rounded=0;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#101217;strokeWidth=10;verticalAlign=top;fontSize=70;fontStyle=1;spacingTop=20;"
    pve = {}
    for k, (nom, x) in enumerate((("NM-PVE1", x0 + 170), ("NM-PVE2", x0 + 2170))):
        n = k + 1
        pve[n] = p.boite(f"{nom}<br><font style='font-size:34px;font-weight:normal'>Dell R660xs · Proxmox VE 8 · ZFS miroir · "
                         f"mgmt 10.13.58.1{n}</font>", x, 1900, 1590, 1050, st_pve)
        gx = x + 40
        for j, (t, nm, fin) in enumerate((("LXC", f"DHCP Kea {n}" + (" (primaire)" if n == 1 else " (secondaire)"), 10 + n),
                                          ("LXC", f"NTP {n} chrony", 20 + n), ("LXC", f"DNS interne {n}", 30 + n),
                                          ("LXC", f"Bastion Teleport {n}", 40 + n))):
            _guest(p, gx + j * 380, 2090, 360, 250, t, nm, f"10.13.59.{fin}")
        if n == 1:
            vm = p.boite("<b>VM Debian – Docker Compose</b> <font style='font-size:28px'>10.13.59.50 · HA Proxmox, répliquée sur PVE2</font>",
                         gx, 2380, 1130, 520, "rounded=1;arcSize=4;whiteSpace=wrap;html=1;fillColor=#F4F4F4;strokeColor=#4d525b;"
                         "strokeWidth=4;verticalAlign=top;fontSize=32;spacingTop=10;")
            for j, nm in enumerate(("NMS LibreNMS", "Traps SNMP snmptrapd", "Loki (recherche journaux)", "Grafana")):
                _guest(p, gx + 20 + j * 275, 2520, 260, 340, "conteneur", nm, "", couleur="#FDEBD3", trait="#a75c00")
        else:
            _guest(p, gx, 2380, 1130, 520, "réplique ZFS (toutes les minutes)", "VM Docker supervision",
                   "démarrée ici par le HA si NM-PVE1 tombe", couleur="#FAFAFA", trait="#6d727b", pointille=True)
        _guest(p, gx + 1160, 2380, 350, 520, "LXC (v2)", f"Journaux {n}\nrsyslog · archives LCEN",
               f"10.13.59.5{5 + n}\nVIP .55", couleur="#EDE7F6", trait="#5b2c8c")
    # --- témoin ---------------------------------------------------------------------------------------
    wit = p.boite("NM-WITNESS<br><font style='font-size:28px;font-weight:normal'>QDevice clusters NM + DT<br>serveur NUT · Dell R260</font>",
                  6045, 2250, 400, 360, st_pve.replace("fontSize=70", "fontSize=40").replace("strokeWidth=10", "strokeWidth=8"))
    # --- réplication directe ------------------------------------------------------------------------
    p.lien(pve[1], pve[2], f"strokeWidth=10;strokeColor={COUL['replication']};fontSize=36;fontColor={COUL['replication']};"
           "labelBackgroundColor=#ffffff;fontStyle=1;",
           h("replication\n25G DAC direct · MTU 9000\n10.13.58.49 ↔ .50 /30"), sx=1, sy=0.12, tx=0, ty=0.12)
    # --- pile de switchs ------------------------------------------------------------------------------
    p.boite("", x0 + 650, 3640, 2700, 430, "rounded=1;arcSize=10;whiteSpace=wrap;html=1;fillColor=none;dashed=1;strokeWidth=8;strokeColor=#6d727b;")
    p.texte("Pile StackWise-80 (1 switch logique)<br>C9200L-24T-4X-E + kit de pile", x0 + 1400, 3955, 1200, 110, taille=34, couleur="#4d525b")
    sw1 = p.boite("NM-SW1", x0 + 900, 3720, 285, 285, ICONE_SWITCH + "labelPosition=left;verticalLabelPosition=middle;align=right;verticalAlign=middle;spacingRight=20;")
    sw2 = p.boite("NM-SW2", x0 + 2820, 3720, 285, 285, ICONE_SWITCH + "labelPosition=right;verticalLabelPosition=middle;align=left;verticalAlign=middle;spacingLeft=20;")
    p.lien(sw1, sw2, "strokeWidth=14;strokeColor=#101217;fontSize=32;labelBackgroundColor=#ffffff;", h("câbles de pile 2 × 80 Gb/s"), sx=1, sy=0.75, tx=0, ty=0.75)
    # --- liens hyperviseurs -> switchs -------------------------------------------------------------------
    st_l = lambda c: f"strokeWidth=8;strokeColor={c};fontSize=32;fontColor={c};labelBackgroundColor=#ffffff;fontStyle=1;edgeStyle=orthogonalEdgeStyle;"
    # (réseau, nœud, sortie X sur le bas du PVE, switch, entrée X, texte)
    liens = [
        ("ipmi", 1, 0.06, sw1, 0.1, "ipmi\n10.13.57.11"),
        ("mgmt", 1, 0.22, sw1, 0.3, "mgmt bond0\n10.13.58.11"),
        ("cluster", 1, 0.38, sw1, 0.5, "cluster\n10.13.58.41"),
        ("workload", 1, 0.54, sw1, 0.7, "workload\nbond1 · 904"),
        ("mgmt", 1, 0.74, sw2, 0.1, ""),
        ("workload", 1, 0.90, sw2, 0.22, ""),
        ("ipmi", 2, 0.94, sw2, 0.9, "ipmi\n10.13.57.12"),
        ("mgmt", 2, 0.78, sw2, 0.7, "mgmt bond0\n10.13.58.12"),
        ("cluster", 2, 0.62, sw2, 0.5, "cluster\n10.13.58.42"),
        ("workload", 2, 0.46, sw2, 0.36, "workload\nbond1 · 904"),
        ("mgmt", 2, 0.26, sw1, 0.82, ""),
        ("workload", 2, 0.10, sw1, 0.94, ""),
    ]
    geo_pve = {1: x0 + 170, 2: x0 + 2170}
    geo_sw = {sw1: x0 + 900, sw2: x0 + 2820}
    niveaux = {0: 3480, 1: 3420, 2: 3360, 3: 3300, 4: 3180, 5: 3120, 6: 3480, 7: 3420, 8: 3360, 9: 3300, 10: 3240, 11: 3060}
    for i, (res, n, sx, sw, tx, t) in enumerate(liens):
        xa, xb, yy = geo_pve[n] + 1590 * sx, geo_sw[sw] + 285 * tx, niveaux[i]
        p.lien(pve[n], sw, st_l(COUL[res]), h(t), sx=sx, sy=1, tx=tx, ty=0, points=[(xa, yy), (xb, yy)], pos=-0.8)
    p.lien(wit, sw1, st_l(COUL["cluster"]), h("cluster\n10.13.58.40"), sx=0.3, sy=1, tx=1, ty=0.15,
           points=[(6165, 3560), (5540, 3560), (5540, 3763)], pos=-0.5)
    p.lien(wit, sw2, st_l(COUL["mgmt"]), h("mgmt\n10.13.58.13"), sx=0.7, sy=1, tx=0, ty=0.15,
           points=[(6325, 3600), (7040, 3600), (7040, 3763)], pos=-0.5)
    # --- postes d'administration ------------------------------------------------------------------------
    paw = p.boite("ADMIN-PAW (VLAN 906)", x0 + 3330, 4200, 340, 272, ICONE_POSTE)
    p.lien(sw2, paw, "strokeWidth=8;strokeColor=#c13c3b;edgeStyle=orthogonalEdgeStyle;", "", sx=1, sy=0.5, tx=0.5, ty=0)
    # --- liaison vers le cœur ---------------------------------------------------------------------------
    # cl-pair : x 680..2480, y 1590..1960 ; on arrive sur son bord droit
    for k in range(4):
        xv, ya = 3700 + 45 * k, 1590 + 370 * (0.55 + 0.1 * k)
        if k < 2:   # NM-SW1 : par son côté gauche
            sy = 0.3 + 0.4 * k
            pts = [(xv, 3720 + 285 * sy), (xv, ya)]
            p.lien(sw1, "cl-pair", "strokeWidth=10;strokeColor=#101217;", "", sx=0, sy=sy, tx=1, ty=0.55 + 0.1 * k, points=pts)
        else:       # NM-SW2 : par le bas, sous la pile
            sx = 0.35 + 0.3 * (k - 2)
            yb = 4110 + 45 * (k - 2)
            pts = [(x0 + 2820 + 285 * sx, yb), (xv, yb), (xv, ya)]
            p.lien(sw2, "cl-pair", "strokeWidth=10;strokeColor=#101217;", "", sx=sx, sy=1, tx=1, ty=0.55 + 0.1 * k, points=pts)
    p.boite("", 3690, 2700, 190, 70, "ellipse;whiteSpace=wrap;html=1;strokeWidth=10;fillColor=none;")
    p.texte("<b>Po10</b> · 4 × 10G LACP (MEC)<br>trunk 900, 901, 902, 904, 906<br>natif 999 · passerelles sur CL (VRF ADM)",
            3140, 2790, 540, 200, taille=34, align="right")
    # --- légende ------------------------------------------------------------------------------------------
    lx, ly = x0 + 120, 4260
    p.boite("", lx, ly, 3060, 600, "rounded=0;whiteSpace=wrap;html=1;fillColor=#EEEEEE;strokeColor=#4d525b;strokeWidth=4;")
    for k, (res, vid, c) in enumerate(D.NM_RESEAUX):
        v = D.VLANS[vid]
        v6 = v["v6"] or "IPv4 seulement (non routé)"
        p.texte(f"<b>{res}</b> · VLAN {vid} · {v['v4']} · {v6}", lx + 40, ly + 30 + 95 * k, 2950, 80, taille=40, couleur=c, align="left")
    p.texte("<b>uplink</b> · Po10 vers CL · <b>ADMIN-PAW</b> · VLAN 906 · 10.13.60.0/26 · 2001:660:5402:4906::/64",
            lx + 40, ly + 30 + 95 * 5, 2950, 80, taille=40, couleur="#101217", align="left")


def dessiner_piles(p):
    """Le reste du schéma : préciser les piles (EL-SW et DM-SW), sans rien déplacer."""
    p.lien("CVoWMKzBPITZB_2SDfIO-95", "CVoWMKzBPITZB_2SDfIO-96", "strokeWidth=10;", "", sx=1, sy=0.4, tx=0, ty=0.4)
    p.lien("CVoWMKzBPITZB_2SDfIO-95", "CVoWMKzBPITZB_2SDfIO-96", "strokeWidth=10;", "", sx=1, sy=0.6, tx=0, ty=0.6)
    p.texte("Pile StackWise-80", 1150, 620, 900, 80, taille=44, couleur="#4d525b")
    p.texte("Pile<br>StackWise-80", -1130, 1020, 300, 140, taille=36, couleur="#4d525b")
    p.texte("Pile<br>StackWise-1T", 5800, 1290, 360, 140, taille=36, couleur="#4d525b")


# ---------------------------------------------------------------------------
# Version 2 du schéma principal (audit du 15/11/2026)
# ---------------------------------------------------------------------------
V2_SUPPR = {  # serveurs physiques remplacés par des VM (SYS-02) ; liens EL-SW <-> CL croisés (Po4 réduit à 2×10G)
    "CVoWMKzBPITZB_2SDfIO-105", "dmz-caddy2", "CVoWMKzBPITZB_2SDfIO-110", "CVoWMKzBPITZB_2SDfIO-111",
    "CVoWMKzBPITZB_2SDfIO-112", "CVoWMKzBPITZB_2SDfIO-113",
    "dt-rad1", "dt-rad2", "dt-ad1", "dt-ad2", "dt-dhcp1", "dt-dhcp2",
    "CVoWMKzBPITZB_2SDfIO-101", "CVoWMKzBPITZB_2SDfIO-102",
}
CL1, CL2 = "CVoWMKzBPITZB_2SDfIO-73", "CVoWMKzBPITZB_2SDfIO-74"


def v2_retoucher(cells):
    """Stormshield raccordé directement au cœur (SEC-01) ; libellé de DT-BKP1."""
    for ident, cible, ex in (("eg-12", CL1, 0.5), ("eg-13", CL2, 0.2), ("eg-14", CL2, 0.5), ("eg-15", CL1, 0.8)):
        c = cells.get(ident)
        if c is not None:
            c.set("target", cible)
            st = ";".join(x for x in c.get("style").split(";") if x and not x.startswith(("entryX", "entryY")))
            c.set("style", st + f";entryX={ex};entryY=0;")
    if "dt-bkp1" in cells:
        cells["dt-bkp1"].set("value", "DT-BKP1<br>PBS · VLAN 909")


def _hyperviseur(p, nom, detail, x, y, w, hh):
    st = ("rounded=0;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#101217;strokeWidth=8;verticalAlign=top;fontSize=56;"
          "fontStyle=1;spacingTop=14;")
    return p.boite(f"{nom}<br><font style='font-size:30px;font-weight:normal'>{h(detail)}</font>", x, y, w, hh, st)


def dessiner_v2(p):
    epais = "strokeWidth=10;strokeColor=#101217;"
    lien_l = lambda c: f"strokeWidth=8;strokeColor={c};fontSize=30;fontColor={c};labelBackgroundColor=#ffffff;fontStyle=1;"
    # --- titre de version
    p.texte("<b>Version 2</b> · après l'audit du 15/11/2026<br><font style='font-size:40px'>v1 : architecture/archives/v1_2026-11-15/</font>",
            -1220, -430, 1050, 220, taille=56, couleur="#05893e")
    # --- DMZ : 2 hyperviseurs + témoin à la place de 6 serveurs physiques et 2 Caddy
    dm = {}
    vms = {1: [("VM", "DM-RP1 Caddy", "172.16.13.11"), ("VM", "DM-DNS1 ns1", ".20"), ("VM", "DM-WEB1", ".51"), ("VM", "DM-SRV1", ".52")],
           2: [("VM", "DM-RP2 Caddy", "172.16.13.12"), ("VM", "DM-DNS2 ns2", ".22"), ("VM", "DM-MAIL1", ".21"),
               ("répliques ZFS", "WEB1, SRV1", "HA")]}
    for n, y in ((1, 230), (2, 960)):
        dm[n] = _hyperviseur(p, f"DM-PVE{n}", f"Dell R360 · Proxmox VE · ZFS miroir · mgmt 172.16.13.6{6 + n}", -2890, y, 1180, 620)
        for j, (t, nm, a) in enumerate(vms[n]):
            pt = t.startswith("répliques")
            _guest(p, -2860 + j * 285, y + 160, 270, 300, t, nm, a, couleur="#FAFAFA" if pt else "#FFF4E5",
                   trait="#6d727b" if pt else "#a75c00", pointille=pt)
        p.texte("VIP Caddy 172.16.13.10 (keepalived)" if n == 1 else "trunk 400, 401 · corosync 403", -2860, y + 480, 1120, 60,
                taille=30, couleur="#a75c00", align="left")
        for k, sw in enumerate(("CVoWMKzBPITZB_2SDfIO-94", "dmz-sw2")):
            p.lien(dm[n], sw, epais, "", sx=1, sy=0.35 + 0.3 * k, tx=0, ty={(1, 0): 0.4, (1, 1): 0.3, (2, 0): 0.65, (2, 1): 0.7}[(n, k)])
    p.lien(dm[1], dm[2], lien_l("#7B1FA2"), h("DM-REPL 10G DAC"), sx=0.5, sy=1, tx=0.5, ty=0)
    wit = p.boite("DM-WITNESS<br><font style='font-size:26px;font-weight:normal'>QDevice DMZ</font>", -1690, 1540, 340, 120,
                  "rounded=0;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#101217;strokeWidth=6;fontSize=34;fontStyle=1;")
    p.lien("dmz-sw2", wit, epais.replace("10", "6"), "", sx=0, sy=0.9, tx=1, ty=0.5)
    # --- Datacenter : 2 hyperviseurs tier 0 à la place de 6 serveurs physiques
    dt = {}
    for n, x in ((1, 4330), (2, 5790)):
        dt[n] = _hyperviseur(p, f"DT-PVE{n}", f"Dell R660xs · Proxmox VE · tier 0 · mgmt 10.13.58.1{3 + n}", x, 380, 1300, 560)
        for j, (t, nm, a, c, tr) in enumerate(((f"VM tier 0 · VLAN 310", f"DT-AD{n}", f"10.13.52.1{n}", "#EDE7F6", "#5b2c8c"),
                                               ("VM · VLAN 300", f"DT-RAD{n} (NPS)", f"10.13.48.2{n}", "#E6F4F4", "#008889"),
                                               ("VM · VLAN 300", f"DT-DHCP{n}", f"10.13.48.3{n}", "#E6F4F4", "#008889"))):
            _guest(p, x + 30 + j * 420, 530, 400, 260, t, nm, a, couleur=c, trait=tr)
        p.texte("bond1 2×25G trunk 300, 310 · corosync 908 · QDevice NM-WITNESS", x + 30, 820, 1240, 90, taille=28, couleur="#4d525b", align="left")
        for k, sw in enumerate(("CVoWMKzBPITZB_2SDfIO-93", "dt-sw2")):
            p.lien(dt[n], sw, epais, "", sx=0.35 + 0.3 * k, sy=1, tx=0.3 + 0.4 * k, ty=0)
    p.lien(dt[1], dt[2], lien_l("#7B1FA2"), h("DT-REPL\n25G DAC"), sx=1, sy=0.15, tx=0, ty=0.15)
    # --- Stormshield sur le cœur, EL-SW réduit à la gestion
    p.texte("<b>v2 : Po2 / Po3</b> · Stormshield → cœur<br>2×10G MEC par nœud<br>transits 1010-1090 + tier 0 (310)",
            2600, 1080, 900, 200, taille=34, couleur="#2b2f8c", align="left")
    p.texte("EL-SW : gestion seulement (VLAN 900)<br>Po4 2×10G vers CL", 2600, 900, 900, 120, taille=32, couleur="#4d525b", align="left")
    # --- iBGP entre les routeurs de bordure
    p.lien("CVoWMKzBPITZB_2SDfIO-108", "rt-2", "strokeWidth=8;strokeColor=#101217;dashed=1;fontSize=34;labelBackgroundColor=#ffffff;fontStyle=1;",
           h("iBGP 139.124.112.4/30\nannonce conditionnelle vers FAI 2"), sx=1, sy=0.5, tx=0, ty=0.5)
    # --- contrôleurs Wi-Fi physiques
    p.boite("", -1170, 1745, 1060, 380, "rounded=1;arcSize=8;whiteSpace=wrap;html=1;fillColor=none;dashed=1;strokeWidth=6;strokeColor=#05893e;")
    p.texte("<b>v2 : contrôleurs Wi-Fi</b> · HA SSO · bornes en mode local", -1150, 1750, 1020, 60, taille=32, couleur="#05893e", align="left")
    st_w = "rounded=1;arcSize=10;whiteSpace=wrap;html=1;fillColor=#E8F3E8;strokeColor=#05893e;strokeWidth=6;fontSize=40;fontStyle=1;"
    w1 = p.boite("WLC1<br><font style='font-size:26px;font-weight:normal'>C9800-L-F · actif</font>", -1130, 1830, 420, 180, st_w)
    w2 = p.boite("WLC2<br><font style='font-size:26px;font-weight:normal'>C9800-L-F · veille</font>", -580, 1830, 420, 180, st_w)
    p.lien(w1, w2, "strokeWidth=6;strokeColor=#05893e;dashed=1;fontSize=26;labelBackgroundColor=#ffffff;", "RP", sx=1, sy=0.5, tx=0, ty=0.5)
    p.lien(w2, "cl-pair", epais, "", sx=1, sy=0.3, tx=0, ty=0.82, points=[(500, 1884), (500, 1893)])
    p.lien(w2, "cl-pair", epais, "", sx=1, sy=0.7, tx=0, ty=0.92, points=[(540, 1956), (540, 1930)])
    p.lien(w1, "cl-pair", epais, "", sx=0.5, sy=1, tx=0.05, ty=1, points=[(-920, 2090), (770, 2090)])
    p.lien(w1, "cl-pair", epais, "", sx=0.7, sy=1, tx=0.1, ty=1, points=[(-836, 2060), (860, 2060)])
    p.texte("Po30 / Po31 · 2×10G par WLC · trunk 514, 515, 530, 907", -1150, 2135, 1060, 50, taille=28, couleur="#05893e", align="left")


# ===========================================================================
# 2. Schéma logique L2
# ===========================================================================
def _eq(p, nom, sous, x, y, w=260, hh=70, fond="#FFFFFF", trait=ENCRE):
    st = (f"rounded=1;arcSize=12;whiteSpace=wrap;html=1;fillColor={fond};strokeColor={trait};strokeWidth=2;fontSize=13;fontStyle=1;")
    return p.boite(f"{h(nom)}<br><font style='font-size:10px;font-weight:normal'>{h(sous)}</font>", x, y, w, hh, st)


def _groupe(p, titre, x, y, w, hh, coul="#6d727b"):
    p.boite("", x, y, w, hh, f"rounded=1;arcSize=6;whiteSpace=wrap;html=1;fillColor=none;dashed=1;strokeColor={coul};strokeWidth=2;")
    p.texte(titre, x + 6, y + 2, w - 12, 18, taille=10, couleur=coul, gras=True, align="left")


def _l(p, a, b, texte, coul=ENCRE, ep=2, pointille=False, **kw):
    st = (f"strokeWidth={ep};strokeColor={coul};fontSize=10;fontColor={coul};labelBackgroundColor=#ffffff;"
          f"{'dashed=1;' if pointille else ''}")
    return p.lien(a, b, st, h(texte), **kw)


def schema_l2():
    p = Page("Architecture L2", "l2")
    p.texte("Architecture de niveau 2 – VLAN, agrégats, piles · version 2 (après audit)", 20, 10, 1100, 30, taille=20, gras=True, align="left")
    p.texte("Trait plein : trunk 802.1Q (VLAN natif 999, VLAN 1 jamais utilisé) · trait épais : agrégat LACP multi-châssis (MEC) · "
            "pointillé : lien routé (pas de VLAN étendu entre les blocs)", 20, 40, 1500, 20, taille=11, couleur="#4d525b", align="left")
    # Bordure
    _groupe(p, "DMZ · pile DM-SW1/2 (StackWise-80)", 30, 90, 420, 300, "#a75c00")
    dm = _eq(p, "DM-SW1 / DM-SW2", "pile C9200L · VLAN 400, 401, 402, 403", 110, 130)
    dmr = _eq(p, "DM-PVE1 / DM-PVE2", "VM Caddy, DNS, web, mail · bond1 trunk 400+401", 40, 260, 200, 60, "#FFF4E5", "#a75c00")
    dms = _eq(p, "DM-WITNESS", "QDevice · corosync 403 · mgmt 402", 260, 260, 180, 60)
    _l(p, dm, dmr, "Po11-12 2×10G", ep=4)
    _l(p, dm, dms, "access", ep=2)
    _groupe(p, "Pare-feu externe · FortiGate 120G HA (FGCP actif/passif)", 520, 90, 560, 130, "#c13c3b")
    fgt = _eq(p, "EL-FGT1 ⇄ EL-FGT2", "ha1/ha2 : 2 liens de cœur HA directs · mgmt1 en VLAN 900", 670, 130, 300, 70, "#FDECEC", "#c13c3b")
    _l(p, fgt, dm, "Po1 (redundant/LACP vers la pile)\ntrunk 400, 401, 402", "#a75c00", 4)
    _groupe(p, "Pare-feu interne · Stormshield SN710 HA (actif/passif)", 520, 270, 560, 130, "#2b2f8c")
    sns = _eq(p, "EL-SNS1 ⇄ EL-SNS2", "liens HA dédiés · mgmt en VLAN 900", 670, 310, 300, 70, "#ECECFB", "#2b2f8c")
    _l(p, fgt, sns, "TR-FW (1100) · 10.13.3.0/29\nmaillage 2×2, interfaces actif/secours", "#2b2f8c", 2)
    rtr = _eq(p, "EL-RTR1 / EL-RTR2", "C8200L · ports routés (OUT-A, OUT-B)", 1180, 130, 260, 70)
    _l(p, rtr, fgt, "OUT-A / OUT-B\n(ports routés, sans VLAN)", ENCRE, 2, True)
    # EL-SW (v2 : gestion seulement)
    _groupe(p, "Pile EL-SW1/2 (StackWise-80) – gestion seulement", 1120, 440, 400, 120)
    el = _eq(p, "EL-SW1 / EL-SW2", "pile C9200L-24T-4X · VLAN 900", 1170, 475, 300, 70)
    # Cœur
    _groupe(p, "Cœur · CL-SW1 + CL-SW2 en StackWise Virtual (2×40G SVL + lien DAD)", 380, 630, 840, 150, "#0079b5")
    cl = _eq(p, "CL (CL-SW1 ⇄ CL-SW2)", "C9500-16X · STP racine des VLAN 300, 310, 5xx, 9xx, 10xx (priorité 4096)", 600, 670, 400, 80, "#E6F1F8", "#0079b5")
    _l(p, sns, cl, "v2 : Po2 (SNS1) + Po3 (SNS2) · 2×10G MEC chacun, en direct sur le cœur\ntrunk 1010, 1020, 1030, 1040, 1090, 310 (tier 0)", "#2b2f8c", 4)
    _l(p, el, cl, "Po4 · 2×10G\ntrunk 900", ENCRE, 4)
    wlc = _eq(p, "WLC1 ⇄ WLC2 (v2)", "C9800-L-F, HA SSO · bornes en mode local", 60, 660, 280, 70, "#E8F3E8", "#05893e")
    _l(p, wlc, cl, "Po30 / Po31 · 2×10G chacun\ntrunk 514, 515, 530, 907", "#05893e", 4)
    dt = _eq(p, "DT-SW1 / DT-SW2", "pile C9300X StackWise-1T · VLAN 300, 310, 900-902, 908, 909", 1320, 560, 300, 70)
    _l(p, cl, dt, "Po20 · 4×10G MEC\ntrunk 300, 310, 900, 901, 902, 909", ENCRE, 5)
    dts = _eq(p, "DT-PVE1 / DT-PVE2 + DT-BKP1", "VM AD (310), NPS, DHCP (300) · bond1 2×25G · corosync 908 · PBS en 909", 1680, 560, 340, 70, "#EDE7F6", "#5b2c8c")
    _l(p, dt, dts, "Po21-23", ENCRE, 4)
    nm = _eq(p, "NM-SW1 / NM-SW2", "pile C9200L StackWise-80 · VLAN 900-906", 1320, 760, 300, 70)
    _l(p, cl, nm, "Po10 · 4×10G MEC\ntrunk 900, 901, 902, 904, 906", ENCRE, 5)
    pv = _eq(p, "NM-PVE1 / NM-PVE2 / NM-WITNESS", "ipmi 901 · mgmt 902 · cluster 903 · workload 904 · repl 905 direct", 1680, 760, 340, 70)
    _l(p, nm, pv, "access + bond1 LACP", ENCRE, 3)
    # Distribution (frontière L3)
    for n, x in ((1, 160), (2, 980)):
        _groupe(p, f"Bloc {n} · DL-SW{2 * n - 1} + DL-SW{2 * n} en StackWise Virtual · STP racine des VLAN {n}xx (priorité 0)",
                x - 40, 850, 760, 140, "#05893e")
        dl = _eq(p, f"DL-B{n}", "C9500-16X SVL · SVI passerelles des VLAN du bloc", x + 120, 890, 380, 70, "#E8F3E8", "#05893e")
        _l(p, dl, cl, f"Po10{n} · 4×10G L3 (routé)\nsous-interfaces .10 .20 .30 .90", "#05893e", 5, True)
        _groupe(p, f"Accès bloc {n} · {8 if n == 1 else 7} switchs C9200L-48P-4X (1 ou 2 par local technique, piles locales)",
                x - 40, 1040, 760, 120)
        al = _eq(p, f"AL-SW bloc {n}", ("N-1-LT01/LT02, N0-LT01/LT02" if n == 1 else "N1-LT01, N1-LT02") + " · gestion VLAN " + f"{n}90",
                 x + 120, 1075, 380, 70)
        _l(p, al, dl, f"Po1 par switch · 2×10G MEC (1 lien vers chaque DL)\n"
                      f"trunk {n}10-{n}13, {n}20-{n}22, {n}30, {n}90, {n}91 · natif 999", ENCRE, 4)
        y = 1240
        pr = [("Poste + téléphone", f"access {n}10/{n}11 (RADIUS) + voice {n}12"), ("Borne Wi-Fi CW9164I", f"access {n}91 · CAPWAP vers les WLC"),
              ("Caméra / badgeuse", f"access {n}20 / {n}21 (EAP-TLS ou MAB + dACL)"), ("Imprimante", f"access {n}13 (MAB)")]
        for k, (t, s) in enumerate(pr):
            c = _eq(p, t, s, x - 30 + k * 185, y, 175, 60, "#FAFAFA", "#6d727b")
            _l(p, al, c, "", "#6d727b", 1)
    # légende des VLAN
    lx, ly = 1700, 900
    p.boite("", lx, ly, 640, 500, "rounded=0;whiteSpace=wrap;html=1;fillColor=#F3F4F6;strokeColor=#cfd2d8;")
    p.texte("Plages de VLAN", lx + 10, ly + 6, 600, 22, taille=13, gras=True, align="left")
    lignes = [("x10-x13", "USR : personnel, étudiants, voix, impression", D.VRF["USR"]["couleur"]),
              ("x20-x22", "IOT : caméras, badgeuses, GTB", D.VRF["IOT"]["couleur"]),
              ("x30", "GST : VLAN restreint (échec 802.1X filaire)", D.VRF["GST"]["couleur"]),
              ("x90-x91", "ADM du bloc : gestion des switchs, bornes", D.VRF["ADM"]["couleur"]),
              ("300", "SRV : serveurs tier 1 (VM NPS, DHCP)", D.VRF["SRV"]["couleur"]),
              ("310", "Tier 0 : contrôleurs de domaine (passerelle SNS)", "#5b2c8c"),
              ("400-403", "DMZ (derrière le FortiGate)", "#a75c00"),
              ("514-530", "Wi-Fi du bâtiment (WLC, passerelle CL)", D.VRF["USR"]["couleur"]),
              ("900-909", "ADM central : gestion, IPMI, Proxmox, PAW, WLC, PBS", D.VRF["ADM"]["couleur"]),
              ("1010-1100", "Transits vers les pare-feu", "#2b2f8c"),
              ("998 / 999", "Ports inutilisés / natif des trunks", "#6d727b")]
    for k, (a, b, c) in enumerate(lignes):
        p.texte(f"<b>{a}</b>&nbsp;&nbsp;{b}", lx + 14, ly + 36 + k * 40, 610, 34, taille=12, couleur=c, align="left")
    p.texte("x = 1 pour le bloc 1, 2 pour le bloc 2", lx + 14, ly + 36 + 11 * 40, 600, 24, taille=11, couleur="#4d525b", align="left")
    return p


# ===========================================================================
# 3. Schéma logique L3
# ===========================================================================
def schema_l3():
    p = Page("Architecture L3", "l3")
    p.texte("Architecture de niveau 3 – VRF, routage, NAT, IPv4 et IPv6 · version 2 (après audit)", 20, 10, 1200, 30, taille=20, gras=True, align="left")
    p.texte("Le cœur sépare 5 VRF sans route entre elles : tout flux d'une VRF à l'autre, et tout flux vers le tier 0, traverse le Stormshield. "
            "Le FortiGate porte Internet, la DMZ et le NAT.", 20, 40, 1500, 20, taille=11, couleur="#4d525b", align="left")
    nuage = "ellipse;shape=cloud;whiteSpace=wrap;html=1;fontSize=12;fontStyle=1;"
    f1 = p.boite("FAI 1 · AMU / RENATER<br><font style='font-size:10px;font-weight:normal'>AS2457</font>", 380, 70, 260, 110, nuage)
    f2 = p.boite(f"FAI 2 · opérateur commercial<br><font style='font-size:10px;font-weight:normal'>{D.FAI2['as']} (exemple)</font>",
                 1060, 70, 260, 110, nuage)
    r1 = _eq(p, "EL-RTR1", f"eBGP AS{D.AS_SITE} → AS2457 · local-pref 200", 380, 230, 260, 60)
    r2 = _eq(p, "EL-RTR2", f"eBGP AS{D.AS_SITE} → {D.FAI2['as']} · annonce conditionnelle", 1060, 230, 260, 60)
    _l(p, r1, r2, "v2 : iBGP 139.124.112.4/30 (BFD vers les FAI)", ENCRE, 2, True)
    _l(p, f1, r1, "139.124.112.0/30 (.2)\n2001:660:5402:4FF0::/127")
    _l(p, f2, r2, f"{D.FAI2['lien4']} (.2)\n{D.FAI2['lien6']}")
    fgt = _eq(p, "Cluster FortiGate (EL-FGT1/2)", "SD-WAN OUT-A prioritaire · SNAT par VRF · VIP DMZ · NPTv6 sur FAI 2", 640, 360, 420, 70,
              "#FDECEC", "#c13c3b")
    _l(p, r1, fgt, "OUT-A 139.124.112.8/29\nRTR1 .9 · FGT .14\n2001:660:5402:4F00::/64")
    _l(p, r2, fgt, "OUT-B 139.124.112.16/29\nRTR2 .17 · FGT .22\n2001:660:5402:4F01::/64")
    p.texte("Annoncé au FAI 1 : <b>139.124.112.0/24</b>, <b>2001:660:5402:4000::/52</b><br>au FAI 2 : le /24 seulement si le FAI 1 est perdu<br>"
            f"secours IPv6 FAI 2 : {D.FAI2['pa6']} (NPTv6)", 680, 280, 340, 70, taille=10, couleur="#4d525b")
    dmz = _eq(p, "DMZ (VM sur DM-PVE1/2)", "400 FRONT 172.16.13.0/27 · 4400::/64\n401 BACK 172.16.13.32/27 · 4401::/64\n402 GEST 172.16.13.64/27 · 403 cluster",
              60, 360, 380, 90, "#FFF4E5", "#a75c00")
    _l(p, fgt, dmz, "VIP 139.124.112.32/27\n(.33 web · .34 mail · .35 ns1)", "#a75c00", 2)
    sns = _eq(p, "Cluster Stormshield (EL-SNS1/2)", "filtrage inter-VRF · passerelle du tier 0 · défaut vers 10.13.3.1", 640, 520, 420, 70,
              "#ECECFB", "#2b2f8c")
    t0 = _eq(p, "Tier 0 (v2)", "310 SRV-T0 10.13.52.0/27 · 4310::/64\nDT-AD1 .11 · DT-AD2 .12 · pas d'Internet", 1180, 520, 330, 60, "#EDE7F6", "#5b2c8c")
    _l(p, sns, t0, "passerelle .1", "#5b2c8c", 2)
    _l(p, fgt, sns, "TR-FW 10.13.3.0/29 · FGT .1 · SNS .2\n2001:660:5402:4F10::/64", "#2b2f8c", 2)
    cl = _eq(p, "Cœur CL (VRF-lite : USR · IOT · GST · SRV · ADM)",
             "défaut statique par VRF vers le SNS · OSPFv2 + OSPFv3 par VRF vers les blocs · Lo0 10.13.0.1", 520, 760, 660, 70,
             "#E6F1F8", "#0079b5")
    for k, (vid, nom, vrf, v4, a, b, p6) in enumerate(D.TRANSITS[:5]):
        c = D.VRF[vrf]["couleur"]
        x = 0.1 + 0.2 * k
        _l(p, sns, cl, f"{nom} ({vid})\n{v4}\nCL .{a[1] % 8} · SNS .{b[1] % 8}", c, 2, sx=x, sy=1, tx=x, ty=0)
    srv = _eq(p, "VRF SRV (SVI sur CL)", "300 SRV-INFRA 10.13.48.0/24 · 4300::/64 (VM NPS, DHCP)", 1280, 690, 400, 50, "#E6F4F4", D.VRF["SRV"]["couleur"])
    adm = _eq(p, "VRF ADM (SVI sur CL)",
              "900 GEST-RESEAU 10.13.56.0/24 · 901 IPMI 10.13.57.0/24\n902 PVE-MGMT 10.13.58.0/27 · 904 WORKLOAD 10.13.59.0/24\n"
              "906 PAW 10.13.60.0/26 · 907 WLC 10.13.60.64/28 · 909 PBS 10.13.60.128/27\n(903, 905, 908 non routés)",
              1280, 760, 440, 95, "#FBECEC", D.VRF["ADM"]["couleur"])
    wifi = _eq(p, "Wi-Fi du bâtiment (v2, SVI sur CL)", "514 WIFI-PERS 10.13.80.0/22 · 515 WIFI-ETU 10.13.64.0/20 (USR)\n"
               "530 WIFI-INVITES 10.13.84.0/22 (GST) · trafic amené par les WLC", 40, 650, 420, 70, "#E6F1F8", "#0079b5")
    _l(p, cl, srv, "", D.VRF["SRV"]["couleur"])
    _l(p, cl, adm, "", D.VRF["ADM"]["couleur"])
    _l(p, cl, wifi, "", D.VRF["USR"]["couleur"])
    for n, x in ((1, 120), (2, 900)):
        base = 16 if n == 1 else 32
        dl = _eq(p, f"DL-B{n} (DL-SW{2 * n - 1}/{2 * n}, StackWise Virtual)",
                 f"passerelle unique .1 / ::1 (pas de HSRP/VRRP) · Lo0 10.13.0.{n + 1} · relais DHCP", x, 960, 620, 60, "#E8F3E8", "#05893e")
        p2p = [q for q in D.P2P if q["bloc"] == n]
        _l(p, cl, dl, "OSPF zone 0 par VRF, BFD\n" + "\n".join(f"{q['sous_if']} {q['v4']}" for q in p2p), "#05893e", 3, True)
        rows = [("USR", [110, 111, 112, 113]), ("IOT", [120, 121, 122]), ("GST", [130]), ("ADM", [190, 191])]
        y = 1060
        for vrf, ids in rows:
            ids = [n * 100 + (i - 100) for i in ids]
            t = " · ".join(f"{i} {D.VLANS[i]['v4']}" for i in ids)
            hh = 20 + 16 * ((len(ids) + 1) // 2)
            p.boite(f"<b>{vrf}</b> · {t}<br><font color='#4d525b'>IPv6 2001:660:5402:4{n}{D.VLANS[ids[0]]['id'] % 100 // 10}0::/60 (un /64 par VLAN)</font>",
                    x, y, 620, hh, f"rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor={D.VRF[vrf]['couleur']};"
                                   f"strokeWidth=2;fontSize=10;align=left;spacingLeft=6;")
            y += hh + 8
    # légende des VRF
    lx, ly = 1780, 360
    p.boite("", lx, ly, 560, 300, "rounded=0;whiteSpace=wrap;html=1;fillColor=#F3F4F6;strokeColor=#cfd2d8;")
    p.texte("VRF", lx + 10, ly + 6, 500, 22, taille=13, gras=True, align="left")
    for k, (code, v) in enumerate(D.VRF.items()):
        p.texte(f"<b>{code}</b> ({v['id']}) {h(v['nom'])} – {h(v['role'])}", lx + 14, ly + 34 + k * 52, 535, 50, taille=10,
                couleur=v["couleur"], align="left")
    return p


def ecrire_schemas(dossier):
    ecrire([schema_l2()], dossier / "architecture_l2.drawio", largeur=2400, hauteur=1400)
    ecrire([schema_l3()], dossier / "architecture_l3.drawio", largeur=2400, hauteur=1400)
