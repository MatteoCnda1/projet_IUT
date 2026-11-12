#!/usr/bin/env python3
"""Plan de câblage du bâtiment (point 04 du cahier des charges).

À partir des salles extraites des plans (salles.py), des décisions de l'équipe (batiment.py,
regles.py) et des bornes de l'étude RSSI (etude_rssi.py) :
  1. place les prises : usagers (densité par type de salle), bornes Wi-Fi, caméras, badgeuses ;
  2. rattache chaque prise au local technique (L.TECH) le plus proche de son niveau, par le
     plus court chemin dans le bâtiment (couloirs privilégiés), et vérifie le lien permanent
     ≤ 90 m (ISO/IEC 11801-1, EN 50173-1) ;
  3. en déduit les chemins de câbles et leur largeur ;
  4. trace les rocades fibre (2 par local, par deux chemins disjoints et deux colonnes
     montantes) et les deux adductions opérateur ;
  5. dimensionne chaque baie (ports, switchs, U, budget PoE).

Sorties dans livrables/plan_cablage/ :
  plans/<niveau>_cablage.pdf|svg|png, synoptique.pdf|svg|png, prises.csv, baies.csv,
  rocades.csv, resume.json
Usage : python3 cablage/plan_cablage.py   (après salles.py et etude_rssi.py)
"""
import csv
import json
import math
from pathlib import Path

import cv2
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import dijkstra

import batiment as bat
import etude_rssi as rf
import regles as R

HERE = Path(__file__).resolve().parent
BUILD = HERE / "build"
OUT = HERE.parent / "livrables" / "plan_cablage"
G = 0.25                 # m, maille de cheminement
HAUTEUR_NIVEAU = 3.5     # m, d'un niveau à l'autre
DESCENTES = 3.0          # m, remontée en faux plafond + descente à la prise
LOVAGE = 2.0             # m, réserve au brassage
COEF_TRACE = 1.10        # le câble suit le chemin de câbles, pas la ligne idéale
LIEN_MAX = 90.0          # m, lien permanent

NIVEAUX = ["N-1", "N0", "N1"]
ALTITUDE = {"N-1": -1, "N0": 0, "N1": 1}
LOCAUX = {  # nom du L.TECH sur le plan -> code
    ("N-1", "L.TECH 01"): "N-1-LT01", ("N-1", "L.TECH 02"): "N-1-LT02",
    ("N0", "L.TECH"): "N0-LT01", ("N0", "L.TECH 02"): "N0-LT02",
    ("N1", "L.TECH 01"): "N1-LT01", ("N1", "L.TECH 02"): "N1-LT02",
}
# Colonnes montantes : à l'aplomb des deux locaux du RDC
COLONNES = {"Nord": ("N0", "L.TECH"), "Sud": ("N0", "L.TECH 02")}

# Caméras : (niveau, salle, position le long du grand axe de la salle, 0 à 1)
CAMERAS = [
    ("N-1", "PARKING", 0.25), ("N-1", "PARKING EST", 0.75), ("N-1", "SALLE SERVEUR", 0.5), ("N-1", "CIRC 02", 0.8),
    ("N0", "ENTREE", 0.5), ("N0", "HALL D'ENTREE", 0.15), ("N0", "HALL D'ENTREE", 0.85), ("N0", "CIRCULATION 02", 0.5),
    ("N0", "CIRCULATION 04", 0.5), ("N0", "FOYER ETUDIANTS", 0.5), ("N0", "DGMT", 0.5),
    ("N1", "CIRCULATION 01", 0.5), ("N1", "CIRC 04", 0.5), ("N1", "CIRC 05", 0.5), ("N1", "PASSERELLE", 0.5),
]
# Badgeuses : à la porte de ces locaux
BADGEUSES = [("N-1", "SALLE SERVEUR")] + [(n, s) for (n, s) in LOCAUX] + [
    ("N0", "ENTREE"), ("N0", "HALL D'ENTREE"), ("N1", "S.RESEAUX 01"), ("N1", "S RESEAUX 02")]
# Adductions opérateur : point d'entrée dans le bâtiment (sous-sol)
ADDUCTIONS = {"FAI 1": ("N-1", "L.TECH 02", "façade ouest, chambre de tirage côté chaufferie"),
              "FAI 2": ("N-1", "PARKING EST", "façade est, par le parking")}

PUISSANCE_POE = {"wifi": 25.5, "camera": 12.95, "badge": 6.5, "telephone": 6.5}  # W, classes 802.3at/af
BUDGET_POE_SWITCH = 370.0   # W, Catalyst C9200L-48P-4X
PORTS_SWITCH = 48
MARGE_PORTS = 1.10
CABLE_MM2 = 44.0            # section d'un câble Cat6A U/FTP (Ø 7,5 mm)
REMPLISSAGE = 0.40
CHEMINS = [(100, 50), (200, 60), (300, 100)]  # largeur × hauteur (mm)
TYPES_CHEMIN = {"circulation", "technique", "salle_serveur", "parking", "exterieur"}


# ---------------------------------------------------------------------------
# Géométrie
# ---------------------------------------------------------------------------
def poly_mask(contour, shape):
    m = np.zeros(shape, np.uint8)
    cv2.fillPoly(m, [np.round(np.array(contour) / G).astype(np.int32)], 1)
    return m.astype(bool)


def le_long(s, f):
    x0, y0, x1, y1 = s["bbox"]
    if x1 - x0 >= y1 - y0:
        return x0 + f * (x1 - x0), s["y"]
    return s["x"], y0 + f * (y1 - y0)


def perimetre(contour, n, retrait=0.3, cx=None, cy=None):
    """n points répartis le long du contour, légèrement en retrait vers l'intérieur."""
    pts = np.array(contour + [contour[0]], float)
    seg = np.hypot(*np.diff(pts, axis=0).T)
    L = seg.sum()
    out = []
    for k in range(n):
        d = (k + 0.5) * L / n
        i = int(np.searchsorted(np.cumsum(seg), d))
        i = min(i, len(seg) - 1)
        t = (d - (np.cumsum(seg)[i] - seg[i])) / max(seg[i], 1e-6)
        p = pts[i] + t * (pts[i + 1] - pts[i])
        v = np.array([cx - p[0], cy - p[1]])
        p = p + retrait * v / max(np.linalg.norm(v), 1e-6)
        out.append((round(float(p[0]), 2), round(float(p[1]), 2)))
    return out


# ---------------------------------------------------------------------------
# Graphe de cheminement d'un niveau
# ---------------------------------------------------------------------------
class Reseau:
    def __init__(self, niv, ppm):
        self.code = niv["code"]
        w_px, h_px = niv["taille_px"]
        self.shape = (int(h_px / ppm / G) + 1, int(w_px / ppm / G) + 1)
        amphi = (bat.AMPHI["centre"], bat.AMPHI["axes"]) if self.code == "N1" else None
        parois, res, _ = rf.carte_parois(self.code, ppm, amphi)
        # parois -> grille G (une cellule est bloquée si elle contient un trait)
        k = G / res
        H, W = self.shape
        yy = (np.arange(H)[:, None] * k + k / 2).astype(int).clip(0, parois.shape[0] - 1)
        xx = (np.arange(W)[None, :] * k + k / 2).astype(int).clip(0, parois.shape[1] - 1)
        mur = np.zeros(self.shape, np.float32)  # affaiblissement le plus fort dans la cellule (12 = mur porteur)
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                mur = np.maximum(mur, parois[(yy + dy).clip(0, parois.shape[0] - 1), (xx + dx).clip(0, parois.shape[1] - 1)])
        self.mur = mur > 0
        cout = np.zeros(self.shape, np.float32)
        emprise = np.zeros(self.shape, np.uint8)
        self.zone = np.full(self.shape, -1, np.int32)
        for i, s in enumerate(niv["salles"]):
            if not s.get("contour"):
                continue
            t = s["type"]
            if t == "hors" or (t == "exterieur" and not s["nom"].startswith(("VIDE SANITAIRE", "SOUS AMPHI"))):
                continue
            m = poly_mask(s["contour"], self.shape)
            emprise |= m.astype(np.uint8)
            c = {"circulation": 1.0, "technique": 1.2, "salle_serveur": 1.2, "parking": 1.1, "exterieur": 1.3}.get(t, 3.0)
            sel = m & ((cout == 0) | (cout > c))
            cout[sel] = c
            self.zone[m & (self.zone < 0)] = i
        # Épaisseur des parois entre deux salles : franchissable (passage en faux plafond,
        # percement rebouché coupe-feu) mais pénalisé, pour que le câble suive couloirs et portes.
        # Extérieur : vide relié au bord du plan sans traverser ni trait ni salle
        salles_m = emprise > 0
        libre = ((~self.mur) & ~salles_m).astype(np.uint8)
        ext = np.zeros((H + 2, W + 2), np.uint8)
        for seed in ((0, 0), (W - 1, 0), (0, H - 1), (W - 1, H - 1)):
            if libre[seed[1], seed[0]]:
                cv2.floodFill(libre, ext, seed, 2, flags=4 | (255 << 8) | cv2.FLOODFILL_MASK_ONLY)
        exterieur = (ext[1:-1, 1:-1] > 0) & ~salles_m
        r = int(round(0.6 / G))
        emprise = cv2.dilate(emprise, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))) > 0
        interieur = emprise & ~exterieur
        cout[interieur & (cout == 0)] = 1.4
        cout[interieur & (mur > 0) & (mur < 12)] = 6.0     # cloison, vitrage : ≈ +3 m par traversée
        cout[interieur & (mur >= 12)] = 20.0               # mur porteur : ≈ +10 m par traversée
        cout[~interieur] = 0
        self.cout = cout
        self._graphe()

    def _graphe(self):
        H, W = self.shape
        idx = np.arange(H * W).reshape(H, W)
        ok = self.cout > 0
        ys, xs = np.nonzero(ok)
        rows, cols, data = [], [], []
        for dy, dx in [(0, 1), (1, 0), (1, 1), (1, -1)]:
            y1, x1 = ys + dy, xs + dx
            v = (y1 < H) & (x1 >= 0) & (x1 < W)
            y0, x0, y1, x1 = ys[v], xs[v], y1[v], x1[v]
            v = ok[y1, x1]
            if dy and dx:  # pas de diagonale qui coupe l'angle d'un mur
                v &= ok[y0 + dy, x0] & ok[y0, x0 + dx]
            y0, x0, y1, x1 = y0[v], x0[v], y1[v], x1[v]
            w = 0.5 * (self.cout[y0, x0] + self.cout[y1, x1]) * G * math.hypot(dy, dx)
            rows += [idx[y0, x0], idx[y1, x1]]
            cols += [idx[y1, x1], idx[y0, x0]]
            data += [w, w]
        self.graphe = coo_matrix((np.concatenate(data), (np.concatenate(rows), np.concatenate(cols))), shape=(H * W, H * W)).tocsr()
        self.idx = idx

    def cellule(self, x, y):
        """Cellule praticable la plus proche du point (m)."""
        H, W = self.shape
        i, j = int(y / G), int(x / G)
        for r in range(0, 40):
            y0, y1, x0, x1 = max(0, i - r), min(H, i + r + 1), max(0, j - r), min(W, j + r + 1)
            ys, xs = np.nonzero(self.cout[y0:y1, x0:x1] > 0)
            if len(ys):
                k = np.argmin((ys + y0 - i) ** 2 + (xs + x0 - j) ** 2)
                return int(ys[k] + y0), int(xs[k] + x0)
        return None

    def depuis(self, x, y, penalite=None):
        """Distances (pondérées) et prédécesseurs depuis le point (x, y)."""
        c = self.cellule(x, y)
        g = self.graphe
        if penalite is not None:
            g = g.copy()
            pen = penalite.ravel()[g.indices]
            g.data = g.data * np.where(pen, 8.0, 1.0)
        dist, pred = dijkstra(g, indices=int(self.idx[c]), return_predecessors=True)
        return dist.reshape(self.shape), pred

    def chemin(self, pred, x, y):
        c = self.cellule(x, y)
        n = int(self.idx[c])
        out = []
        while n >= 0:
            out.append(n)
            n = int(pred[n])
        return out

    def longueur(self, cells):
        if len(cells) < 2:
            return 0.0
        H, W = self.shape
        ys, xs = np.divmod(np.array(cells), W)
        return float(np.hypot(np.diff(xs), np.diff(ys)).sum() * G)


# ---------------------------------------------------------------------------
# Prises
# ---------------------------------------------------------------------------
def placer_prises(data, bornes):
    prises = []
    for niv in data["niveaux"]:
        code = niv["code"]
        par_nom = {s["nom"]: s for s in niv["salles"]}
        for s in niv["salles"]:
            n, motif = R.prises_utilisateurs(s["type"], s["nom"], s.get("surface"))
            if not n or not s.get("contour"):
                continue
            tel = 1 if R.TELEPHONE.match(s["nom"]) else 0
            for k, (x, y) in enumerate(perimetre(s["contour"], n, cx=s["x"], cy=s["y"])):
                prises.append({"niveau": code, "salle": s["nom"], "type": "usager", "x": x, "y": y,
                               "usage": motif, "poe": "telephone" if (tel and k == 1) else ""})
        for b in bornes:
            if b["niveau"] == code:
                prises.append({"niveau": code, "salle": b["salle"], "type": "wifi", "x": b["x"], "y": b["y"],
                               "usage": f"borne {b['id']} (canal {b['canal']}), au plafond", "poe": "wifi"})
        for c, nom, f in CAMERAS:
            if c == code and nom in par_nom:
                x, y = le_long(par_nom[nom], f)
                prises.append({"niveau": code, "salle": nom, "type": "camera", "x": round(x, 2), "y": round(y, 2),
                               "usage": "caméra IP, VLAN vidéo", "poe": "camera"})
        circ = [s for s in niv["salles"] if s["type"] == "circulation" and s.get("contour")]
        for c, nom in BADGEUSES:
            if c != code or nom not in par_nom:
                continue
            s = par_nom[nom]
            # sommet du contour le plus proche d'une circulation : là où est la porte
            best = min(((math.hypot(px - q["x"], py - q["y"]), px, py) for px, py in s["contour"] for q in circ if q["nom"] != nom),
                       default=(0, s["x"], s["y"]))
            prises.append({"niveau": code, "salle": nom, "type": "badge", "x": best[1], "y": best[2],
                           "usage": "lecteur de badge, VLAN contrôle d'accès", "poe": "badge"})
    return prises


def passage(rs, salles, cells, depart=None):
    """Noms des circulations et locaux traversés, dans l'ordre (prise -> local)."""
    H, W = rs.shape
    out = []
    for c in cells:
        i = rs.zone.flat[c]
        if i < 0:
            continue
        s = salles[i]
        if s["type"] in ("circulation", "parking", "exterieur", "salle_serveur", "technique") and s["nom"] != depart:
            nom = s["nom"]
            if not out or out[-1] != nom:
                out.append(nom)
    return " → ".join(out)


def dimension_chemin(n):
    for w, h in CHEMINS:
        if n * CABLE_MM2 <= w * h * REMPLISSAGE:
            return f"{w}×{h}"
    w, h = CHEMINS[-1]
    return f"{w}×{h} ×{math.ceil(n * CABLE_MM2 / (w * h * REMPLISSAGE))}"


# ---------------------------------------------------------------------------
# Programme principal
# ---------------------------------------------------------------------------
def main():
    data = bat.charger()
    ppm = data["pt_par_m"] * data["dpi"] / 72
    wifi = json.loads((OUT / "wifi" / "bornes.json").read_text(encoding="utf-8"))
    niveaux = {n["code"]: n for n in data["niveaux"]}
    reseaux = {c: Reseau(niveaux[c], ppm) for c in NIVEAUX}
    salle = lambda c, nom: next(s for s in niveaux[c]["salles"] if s["nom"] == nom)
    locaux = {code: dict(niveau=c, nom=nom, x=salle(c, nom)["x"], y=salle(c, nom)["y"], surface=salle(c, nom)["surface"])
              for (c, nom), code in LOCAUX.items()}
    srv = salle("N-1", "SALLE SERVEUR")

    # 1-2. Prises et rattachement
    prises = placer_prises(data, wifi["bornes"])
    arbres = {}
    for code, lt in locaux.items():
        arbres[code] = reseaux[lt["niveau"]].depuis(lt["x"], lt["y"])
    chemins_par_niveau = {c: np.zeros(reseaux[c].shape, np.int32) for c in NIVEAUX}
    def meilleur_local(niveau, x, y):
        c = reseaux[niveau].cellule(x, y)
        return min((arbres[code][0][c], code) for code, lt in locaux.items() if lt["niveau"] == niveau)

    for p in prises:
        niveau, monte = p["niveau"], 0.0
        d, code = meilleur_local(niveau, p["x"], p["y"])
        if not np.isfinite(d) and ALTITUDE[niveau] > -1:
            # pas d'accès sur ce niveau (amphithéâtre de l'étage, entouré de toiture-terrasse) :
            # câble tiré depuis le niveau inférieur, par les gradins
            niveau = next(k for k, v in ALTITUDE.items() if v == ALTITUDE[p["niveau"]] - 1)
            d, code = meilleur_local(niveau, p["x"], p["y"])
            monte = HAUTEUR_NIVEAU
            p["remarque"] = f"câblée depuis {niveau} (pas d'accès sur son niveau), +{HAUTEUR_NIVEAU:.1f} m de montée"
        rs = reseaux[niveau]
        cells = rs.chemin(arbres[code][1], p["x"], p["y"])
        geo = rs.longueur(cells)
        if not np.isfinite(d):
            geo = 1.3 * (abs(p["x"] - locaux[code]["x"]) + abs(p["y"] - locaux[code]["y"]))
            p["remarque"] = "chemin estimé (pas de passage trouvé sur le plan)"
        p["local"] = code
        p["longueur"] = round(COEF_TRACE * geo + monte + DESCENTES + LOVAGE, 1)
        p["_cells"], p["_route"] = cells, niveau
        p["passage"] = passage(rs, niveaux[niveau]["salles"], cells, p["salle"])
        if np.isfinite(d):
            H, W = rs.shape
            ys, xs = np.divmod(np.array(cells), W)
            chemins_par_niveau[niveau][ys, xs] += 1
    # numérotation par local, dans l'ordre des salles
    for code in locaux:
        mes = sorted((p for p in prises if p["local"] == code), key=lambda p: (["usager", "wifi", "camera", "badge"].index(p["type"]), p["salle"], p["y"], p["x"]))
        for k, p in enumerate(mes, 1):
            p["id"] = f"{code}-P{k:03d}"
    prises.sort(key=lambda p: p["id"])

    # 3. Chemins de câbles
    # Métré : chemins des circulations et locaux uniquement. Dans les salles, le câble suit une
    # goulotte depuis la porte (comprise dans le prix de la prise posée).
    chemins = {}
    for c in NIVEAUX:
        cnt = chemins_par_niveau[c].copy()
        rs = reseaux[c]
        for i, s in enumerate(niveaux[c]["salles"]):
            if s["type"] not in TYPES_CHEMIN:
                cnt[rs.zone == i] = 0
        lng = {}
        ys, xs = np.nonzero(cnt)
        # une cellule traversée en diagonale compte pour sa diagonale ; on approche par la maille
        for y, x in zip(ys, xs):
            dim = dimension_chemin(int(cnt[y, x]))
            lng[dim] = lng.get(dim, 0) + G
        chemins[c] = {k: round(v) for k, v in sorted(lng.items()) if round(v) > 0}

    # 4. Rocades : 2 fibres par local, par deux chemins disjoints
    rs_ss = reseaux["N-1"]
    d_srv, p_srv = rs_ss.depuis(srv["x"], srv["y"])
    col = {}
    for nomc, (c, nom) in COLONNES.items():
        s = salle(c, nom)
        col[nomc] = {"x": s["x"], "y": s["y"]}
    # pied de chaque colonne au sous-sol
    for nomc, pt in col.items():
        cells = rs_ss.chemin(p_srv, pt["x"], pt["y"])
        pt["cells_ss"] = cells
        pt["horiz_ss"] = rs_ss.longueur(cells)
    rocades = []
    traces = {c: [] for c in NIVEAUX}
    for code, lt in locaux.items():
        c = lt["niveau"]
        if c == "N-1":
            cA = rs_ss.chemin(p_srv, lt["x"], lt["y"])
            pen = np.zeros(rs_ss.shape, bool)
            H, W = rs_ss.shape
            ys, xs = np.divmod(np.array(cA), W)
            pen[ys, xs] = True
            pen = cv2.dilate(pen.astype(np.uint8), np.ones((5, 5), np.uint8)).astype(bool)
            # on garde libres les abords immédiats des deux locaux
            for x, y in ((srv["x"], srv["y"]), (lt["x"], lt["y"])):
                i, j = int(y / G), int(x / G)
                pen[max(0, i - 8):i + 9, max(0, j - 8):j + 9] = False
            _dB, pB = rs_ss.depuis(srv["x"], srv["y"], penalite=pen)
            cB = rs_ss.chemin(pB, lt["x"], lt["y"])
            for voie, cells in (("A", cA), ("B", cB)):
                L = COEF_TRACE * rs_ss.longueur(cells) + 2 * LOVAGE + 2 * DESCENTES
                rocades.append({"local": code, "voie": voie, "par": "sous-sol" + (" (chemin direct)" if voie == "A" else " (second chemin)"),
                                "longueur": round(L, 1),
                                "chemin": "SALLE SERVEUR → " + passage(rs_ss, niveaux["N-1"]["salles"], cells[::-1], "SALLE SERVEUR") + f" → {code}"})
                traces["N-1"].append((voie, cells))
            continue
        # locaux du RDC et de l'étage : voie A par la colonne la plus proche, voie B par l'autre
        rs = reseaux[c]
        dist = {}
        for nomc, pt in col.items():
            d, pr = rs.depuis(pt["x"], pt["y"])
            cells = rs.chemin(pr, lt["x"], lt["y"])
            dist[nomc] = (rs.longueur(cells), cells)
        ordre = sorted(dist, key=lambda k: dist[k][0])
        for voie, nomc in zip(("A", "B"), ordre):
            h_niv, cells = dist[nomc]
            vert = HAUTEUR_NIVEAU * (ALTITUDE[c] - ALTITUDE["N-1"])
            L = COEF_TRACE * (col[nomc]["horiz_ss"] + h_niv) + vert + 2 * LOVAGE + 2 * DESCENTES
            bas = passage(rs_ss, niveaux["N-1"]["salles"], col[nomc]["cells_ss"][::-1], "SALLE SERVEUR")
            haut = passage(rs, niveaux[c]["salles"], cells[::-1])
            rocades.append({"local": code, "voie": voie, "par": f"colonne {nomc}", "longueur": round(L, 1),
                            "chemin": f"SALLE SERVEUR → {bas} → colonne {nomc} (montée {vert:.1f} m) → {haut} → {code}"})
            traces[c].append((voie, cells))
            traces["N-1"].append((voie, col[nomc]["cells_ss"]))

    # Adductions
    adductions = []
    for fai, (c, nom, ou) in ADDUCTIONS.items():
        s = salle(c, nom)
        x, y = (s["bbox"][0], s["y"]) if fai == "FAI 1" else (s["bbox"][2], s["y"])
        cells = rs_ss.chemin(p_srv, x, y)
        L = COEF_TRACE * rs_ss.longueur(cells) + 15.0  # + 15 m jusqu'à la chambre de tirage extérieure
        adductions.append({"operateur": fai, "entree": ou, "x": round(x, 2), "y": round(y, 2), "longueur_interne": round(L, 1),
                           "chemin": "chambre de tirage → " + passage(rs_ss, niveaux["N-1"]["salles"], cells, "SALLE SERVEUR") + " → SALLE SERVEUR"})
        traces["N-1"].append(("FAI", cells))

    # 5. Baies
    baies = []
    for code, lt in locaux.items():
        mes = [p for p in prises if p["local"] == code]
        n = len(mes)
        poe = sum(PUISSANCE_POE.get(p["poe"], 0) for p in mes)
        sw = max(1, math.ceil(n * MARGE_PORTS / PORTS_SWITCH), math.ceil(poe / (0.8 * BUDGET_POE_SWITCH)))
        panneaux = math.ceil(n / 24)
        u = panneaux + math.ceil(panneaux / 2) + sw + math.ceil(sw / 2) + 1 + 2 + 2  # + tiroir optique, onduleur, réserve
        baies.append({"local": code, "salle": lt["nom"], "niveau": lt["niveau"], "surface_m2": lt["surface"],
                      "prises": n, "usagers": sum(p["type"] == "usager" for p in mes),
                      "wifi": sum(p["type"] == "wifi" for p in mes), "cameras": sum(p["type"] == "camera" for p in mes),
                      "badges": sum(p["type"] == "badge" for p in mes),
                      "telephones": sum(p["poe"] == "telephone" for p in mes),
                      "poe_W": round(poe), "switchs_48p": sw, "panneaux_24": panneaux, "hauteur_U": u,
                      "baie": "24U murale" if u <= 22 else "42U au sol",
                      "lien_max_m": max(p["longueur"] for p in mes) if mes else 0})

    # Sorties
    OUT.mkdir(parents=True, exist_ok=True)
    champs = ["id", "niveau", "local", "salle", "type", "usage", "poe", "x", "y", "longueur", "passage", "remarque"]
    with open(OUT / "prises.csv", "w", newline="", encoding="utf-8") as f:
        wr = csv.DictWriter(f, fieldnames=champs, extrasaction="ignore")
        wr.writeheader()
        for p in prises:
            wr.writerow({k: p.get(k, "") for k in champs})
    for nom, rows in (("baies.csv", baies), ("rocades.csv", rocades)):
        with open(OUT / nom, "w", newline="", encoding="utf-8") as f:
            wr = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            wr.writeheader()
            wr.writerows(rows)
    longs = [p["longueur"] for p in prises]
    resume = {
        "prises": len(prises), "par_type": {t: sum(p["type"] == t for p in prises) for t in ("usager", "wifi", "camera", "badge")},
        "telephones": sum(p["poe"] == "telephone" for p in prises),
        "cable_cuivre_m": round(sum(longs)), "lien_moyen_m": round(sum(longs) / len(longs), 1), "lien_max_m": max(longs),
        "liens_hors_norme": [p["id"] for p in prises if p["longueur"] > LIEN_MAX],
        "chemins_de_cables_m": chemins, "baies": baies, "rocades": rocades, "adductions": adductions,
        "fibre_m": round(sum(r["longueur"] for r in rocades)),
        "hypotheses": {"coef_trace": COEF_TRACE, "descentes_m": DESCENTES, "lovage_m": LOVAGE, "lien_max_m": LIEN_MAX,
                       "hauteur_niveau_m": HAUTEUR_NIVEAU, "maille_m": G},
    }
    (OUT / "resume.json").write_text(json.dumps(resume, ensure_ascii=False, indent=1), encoding="utf-8")

    import document
    import rendu_cablage
    rendu_cablage.plans(data, ppm, reseaux, prises, locaux, srv, chemins_par_niveau, traces, adductions, col, resume)
    rendu_cablage.synoptique(locaux, rocades, adductions, baies, resume)
    document.implantation(data, prises, locaux, srv, baies, rocades, adductions, resume, wifi)

    print(f"{len(prises)} prises ({resume['par_type']}), {resume['telephones']} téléphones")
    print(f"Cuivre : {resume['cable_cuivre_m']} m, lien moyen {resume['lien_moyen_m']} m, max {resume['lien_max_m']} m, "
          f"{len(resume['liens_hors_norme'])} lien(s) > {LIEN_MAX:.0f} m")
    for b in baies:
        print(f"  {b['local']:9} {b['salle']:10} {b['prises']:3} prises, {b['switchs_48p']} switch(s), {b['hauteur_U']}U ({b['baie']}), "
              f"PoE {b['poe_W']} W, lien max {b['lien_max_m']} m, local {b['surface_m2']} m²")
    for r in rocades:
        print(f"  rocade {r['local']} {r['voie']} {r['par']:24} {r['longueur']} m")
    for a in adductions:
        print(f"  {a['operateur']} : {a['entree']}, {a['longueur_interne']} m jusqu'à la salle serveur")
    print("Chemins de câbles (m) :", chemins)


if __name__ == "__main__":
    main()
