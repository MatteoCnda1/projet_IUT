#!/usr/bin/env python3
"""Étude Wi-Fi prédictive (RSSI) à partir des plans d'architecte.

Modèle multi-murs (type COST 231) à 5 GHz :
    RSSI = PIRE - [FSPL(1 m) + 10·n·log10(d)] - Σ affaiblissement des parois traversées
Les parois sont lues sur le plan : trait noir = mur porteur, trait de couleur = cloison,
trait bleu = vitrage (voir salles.py et regles.py).

Méthode :
  1. bornes imposées par la capacité (salles de TP, TD, projet, amphithéâtre, foyer) ;
  2. ajout glouton de bornes aux emplacements candidats (centres des salles, points
     répartis dans les circulations) jusqu'à couvrir les zones à l'objectif ;
  3. plan de canaux 5 GHz (40 MHz) par coloration de graphe, niveaux compris.

Entrée : cablage/build/salles.json et <niveau>_murs.png (lancer salles.py avant).
Sortie : livrables/plan_cablage/wifi/ (cartes PNG, bornes.csv, bornes.json, etude_rssi.md)
Usage  : python3 cablage/etude_rssi.py
"""
import csv
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

import batiment as bat
import regles as R

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from commun import charte as CH  # noqa: E402
BUILD = HERE / "build"
OUT = HERE.parent / "livrables" / "plan_cablage" / "wifi"
GRILLE = 0.5      # m, maille d'évaluation
PORTEE = 40.0     # m, au-delà le signal est sous l'objectif même sans paroi
FSPL1 = 20 * math.log10(R.FREQ_MHZ) - 27.55
HAUTEUR_NIVEAU = 3.5


def perte(d):
    return FSPL1 + 10 * R.EXPOSANT * np.log10(np.maximum(d, 1.0))


# ---------------------------------------------------------------------------
# Carte des parois
# ---------------------------------------------------------------------------
def carte_parois(code, px_par_m, amphi=None):
    cls = cv2.imread(str(BUILD / f"{code}_murs.png"), cv2.IMREAD_GRAYSCALE)
    # Petits traits isolés (tirets, flèches, poteaux, hachures) : pas des parois
    n, lab, stats, _ = cv2.connectedComponentsWithStats((cls > 0).astype(np.uint8), 8)
    diag = np.hypot(stats[:, cv2.CC_STAT_WIDTH], stats[:, cv2.CC_STAT_HEIGHT]) / px_par_m
    petits = np.flatnonzero(diag < 0.6)
    cls[np.isin(lab, petits)] = 0
    if amphi is not None:
        # Gradins de l'amphithéâtre : traits de mobilier, pas des cloisons
        m = np.zeros_like(cls)
        (cx, cy), (a, b) = amphi
        cv2.ellipse(m, ((cx * px_par_m, cy * px_par_m), (a * px_par_m * 0.95, b * px_par_m * 0.95), 0), 1, -1)
        cls[m > 0] = 0
    db = np.zeros(cls.shape, np.float32)
    for c, v in R.AFFAIBLISSEMENT.items():
        db[cls == c] = v
    # Réduction par maximum sur des blocs d'environ 0,1 m
    k = max(1, int(round(px_par_m * 0.1)))
    h, w = db.shape
    H, W = h // k, w // k
    red = db[:H * k, :W * k].reshape(H, k, W, k).max(axis=(1, 3))
    return red, k / px_par_m, cls


# ---------------------------------------------------------------------------
# Propagation
# ---------------------------------------------------------------------------
def rssi(ap, pts, parois, res, pas=0.05):
    """RSSI (dBm) reçu en chaque point de pts (N×2, m) depuis la borne ap (x, y)."""
    ap = np.asarray(ap, float)
    out = np.full(len(pts), -120.0)
    d = np.hypot(pts[:, 0] - ap[0], pts[:, 1] - ap[1])
    ok = np.flatnonzero(d <= PORTEE)
    K = int(PORTEE / pas) + 2
    t = np.linspace(0.0, 1.0, K)[:, None]
    H, W = parois.shape
    for s in range(0, len(ok), 1500):
        idx = ok[s:s + 1500]
        P = pts[idx]
        X = ap[0] + t * (P[:, 0] - ap[0])
        Y = ap[1] + t * (P[:, 1] - ap[1])
        ix = np.clip((X / res).astype(np.int32), 0, W - 1)
        iy = np.clip((Y / res).astype(np.int32), 0, H - 1)
        v = parois[iy, ix]
        entree = (v[1:] > 0) & (v[:-1] == 0)
        murs = (v[1:] * entree).sum(axis=0)
        out[idx] = R.PIRE_DBM - perte(d[idx]) - murs
    return out


# ---------------------------------------------------------------------------
# Étude d'un niveau
# ---------------------------------------------------------------------------
def masque_poly(contour, shape, g):
    m = np.zeros(shape, np.uint8)
    pts = np.round(np.array(contour) / g).astype(np.int32)
    cv2.fillPoly(m, [pts], 1)
    return m.astype(bool)


def etudier(niv, ppm):
    code = niv["code"]
    w_px, h_px = niv["taille_px"]
    shape = (int(h_px / ppm / GRILLE) + 1, int(w_px / ppm / GRILLE) + 1)
    salles = niv["salles"]
    amphi = (bat.AMPHI["centre"], bat.AMPHI["axes"]) if code == "N1" else None
    parois, res, _ = carte_parois(code, ppm, amphi)

    # Zones à couvrir
    zone = np.zeros(shape, np.int32)  # indice de salle + 1
    batiment = np.zeros(shape, bool)
    for i, s in enumerate(salles):
        if not s.get("contour") or s["type"] in ("exterieur", "hors"):
            continue
        m = masque_poly(s["contour"], shape, GRILLE)
        batiment |= m
        if s["type"] in R.TYPES_WIFI and not R.SANS_OBJECTIF.match(s["nom"]):
            zone[m & (zone == 0)] = i + 1
    if amphi:  # l'estrade et la régie sont dans l'ovale, l'amphi les englobe
        for i, s in enumerate(salles):
            if s["nom"] in ("ESTRADE", "S.TECH"):
                zone[masque_poly(s["contour"], shape, GRILLE)] = i + 1
    cy, cx = np.nonzero(zone)
    cibles = np.c_[(cx + 0.5) * GRILLE, (cy + 0.5) * GRILLE]
    cible_salle = zone[cy, cx] - 1

    # Emplacements candidats
    def point_dans(i, x, y):
        sel = np.flatnonzero(cible_salle == i)
        if not len(sel):
            return None
        j = sel[np.argmin(np.hypot(cibles[sel, 0] - x, cibles[sel, 1] - y))]
        return float(cibles[j, 0]), float(cibles[j, 1])

    imposees, candidats = [], []
    for i, s in enumerate(salles):
        if not np.any(cible_salle == i):
            continue
        n = R.bornes_capacite(s["type"], s["nom"], s.get("surface"))
        x0, y0, x1, y1 = s.get("bbox") or [s["x"] - 1, s["y"] - 1, s["x"] + 1, s["y"] + 1]
        if n == 2:
            if x1 - x0 >= y1 - y0:
                pts = [(x0 + (x1 - x0) / 4, s["y"]), (x1 - (x1 - x0) / 4, s["y"])]
            else:
                pts = [(s["x"], y0 + (y1 - y0) / 4), (s["x"], y1 - (y1 - y0) / 4)]
        else:
            pts = [(s["x"], s["y"])]
        for k, (x, y) in enumerate(pts):
            p = point_dans(i, x, y)
            if p:
                (imposees if k < n else candidats).append((p, i))
        if s["type"] == "circulation" or (s.get("surface") or 0) > 60:
            sel = np.flatnonzero(cible_salle == i)
            pris = []
            for j in sel[np.argsort(cibles[sel, 0] + 1e-3 * cibles[sel, 1])]:
                p = cibles[j]
                if all(math.hypot(p[0] - q[0], p[1] - q[1]) >= 4.0 for q in pris):
                    pris.append(p)
                    candidats.append(((float(p[0]), float(p[1])), i))

    tous = imposees + candidats
    M = np.array([rssi(p, cibles, parois, res) for p, _ in tous]) if tous else np.zeros((0, len(cibles)))

    # Sélection gloutonne
    choix = list(range(len(imposees)))
    meilleur = M[choix].max(axis=0) if choix else np.full(len(cibles), -120.0)
    # Objectif : 98 % de la surface du niveau ET chaque salle occupée (hors circulations)
    # couverte à 90 % au moins. Les cellules des salles en défaut comptent triple.
    occupee = np.array([salles[i]["type"] != "circulation" for i in cible_salle], bool)
    while True:
        manque = meilleur < R.OBJECTIF_DBM
        ok = meilleur >= R.OBJECTIF_DBM
        couv = np.bincount(cible_salle, ok, minlength=len(salles)) / np.maximum(np.bincount(cible_salle, minlength=len(salles)), 1)
        defaut = occupee & (couv[cible_salle] < 0.90)
        if manque.mean() <= 0.02 and not defaut.any():
            break
        poids = np.where(defaut, 3.0, 1.0) * manque
        gains = ((M >= R.OBJECTIF_DBM) * poids).sum(axis=1)
        gains[choix] = 0
        j = int(np.argmax(gains))
        if gains[j] < 4:  # moins de 1 m² gagné
            break
        choix.append(j)
        meilleur = np.maximum(meilleur, M[j])

    bornes = []
    for k, j in enumerate(choix):
        (x, y), i = tous[j]
        bornes.append({"id": f"AP-{code}-{k + 1:02d}", "niveau": code, "x": round(x, 2), "y": round(y, 2),
                       "salle": salles[i]["nom"], "motif": "capacité" if j < len(imposees) else "couverture"})
    Msel = M[choix]
    tri = np.sort(Msel, axis=0) if len(choix) > 1 else np.vstack([np.full(len(cibles), -120.0), Msel])
    second = tri[-2]

    # Statistiques par salle
    par_salle = []
    for i in sorted(set(cible_salle.tolist())):
        sel = cible_salle == i
        par_salle.append({"salle": salles[i]["nom"], "type": salles[i]["type"],
                          "surface": salles[i].get("surface"),
                          "min": round(float(meilleur[sel].min()), 1),
                          "moyen": round(float(meilleur[sel].mean()), 1),
                          "couvert": round(float((meilleur[sel] >= R.OBJECTIF_DBM).mean() * 100), 1)})
    stats = {
        "surface_cible_m2": round(len(cibles) * GRILLE ** 2),
        "couverture_pct": round(float((meilleur >= R.OBJECTIF_DBM).mean() * 100), 1),
        "itinerance_pct": round(float((second >= R.ROAMING_DBM).mean() * 100), 1),
        "candidats": len(tous),
    }
    return {"code": code, "nom": niv["nom"], "salles": salles, "bornes": bornes, "stats": stats,
            "par_salle": par_salle, "parois": parois, "res": res, "shape": shape, "batiment": batiment,
            "zone": zone, "ppm": ppm}


# ---------------------------------------------------------------------------
# Plan de canaux (tous niveaux)
# ---------------------------------------------------------------------------
def plan_canaux(etudes):
    aps = [(e, b) for e in etudes for b in e["bornes"]]
    n = len(aps)
    I = np.full((n, n), -120.0)
    niveaux = {"N-1": -1, "N0": 0, "N1": 1}
    for a, (ea, ba) in enumerate(aps):
        for b, (eb, bb) in enumerate(aps):
            if a == b:
                continue
            if ea is eb:
                I[a, b] = rssi((ba["x"], ba["y"]), np.array([[bb["x"], bb["y"]]]), ea["parois"], ea["res"])[0]
            else:
                dz = abs(niveaux[ea["code"]] - niveaux[eb["code"]])
                d = math.sqrt((ba["x"] - bb["x"]) ** 2 + (ba["y"] - bb["y"]) ** 2 + (dz * HAUTEUR_NIVEAU) ** 2)
                I[a, b] = R.PIRE_DBM - float(perte(np.array([d]))[0]) - R.PLANCHER_DB * dz
    I = np.maximum(I, I.T)
    deg = (I >= R.SEUIL_CO_CANAL).sum(axis=1)
    canal = {}
    conflits = 0
    for a in np.argsort(-deg):
        cout = []
        for c in R.CANAUX_40:
            voisins = [b for b, cb in canal.items() if cb == c]
            pire = max([I[a, b] for b in voisins], default=-120.0)
            cout.append((pire >= R.SEUIL_CO_CANAL, pire, c))
        cout.sort()
        canal[a] = cout[0][2]
        conflits += int(cout[0][0])
    for a, (_e, b) in enumerate(aps):
        b["canal"] = canal[a]
    return conflits


# ---------------------------------------------------------------------------
# Rendu
# ---------------------------------------------------------------------------
BANDES = [(-60, "≥ −60 dBm", (39, 116, 64)), (-67, "−60 à −67 (objectif)", (122, 178, 96)),
          (-72, "−67 à −72", (232, 196, 77)), (-80, "−72 à −80", (226, 128, 58)), (-200, "< −80", (190, 60, 50))]


def carte(e):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Patch

    from rendu_cablage import fond_murs, etiquettes_salles
    fond = fond_murs(e["code"])
    ppm = e["ppm"]
    ys, xs = np.nonzero(e["batiment"])
    x0, x1 = xs.min() * GRILLE - 2, (xs.max() + 1) * GRILLE + 2
    y0, y1 = ys.min() * GRILLE - 2, (ys.max() + 1) * GRILLE + 2
    # RSSI sur une grille fine dans le bâtiment
    g = 0.25
    Y, X = np.mgrid[y0:y1:g, x0:x1:g]
    pts = np.c_[X.ravel(), Y.ravel()]
    zone = e["zone"]
    zi = np.clip((pts[:, 1] / GRILLE).astype(int), 0, zone.shape[0] - 1)
    zj = np.clip((pts[:, 0] / GRILLE).astype(int), 0, zone.shape[1] - 1)
    dedans = zone[zi, zj] > 0
    val = np.full(len(pts), np.nan)
    if e["bornes"]:
        best = np.full(dedans.sum(), -120.0)
        for b in e["bornes"]:
            best = np.maximum(best, rssi((b["x"], b["y"]), pts[dedans], e["parois"], e["res"]))
        val[dedans] = best
    img = np.zeros((len(pts), 4))
    for lim, _l, col in reversed(BANDES):
        sel = ~np.isnan(val) & (val >= lim)
        img[sel, :3] = np.array(col) / 255
        img[sel, 3] = 0.55
    img = img.reshape(X.shape + (4,))

    fig, ax = plt.subplots(figsize=(11.7, 11.7 * (y1 - y0) / (x1 - x0) + 1.2), dpi=150)
    ax.imshow(img, extent=(x0, x1, y1, y0), interpolation="nearest")
    ax.imshow(fond, extent=(0, fond.shape[1] / ppm, fond.shape[0] / ppm, 0), interpolation="antialiased")
    etiquettes_salles(ax, {"salles": e["salles"]}, [], gris_circ=True)
    for b in e["bornes"]:
        ax.plot(b["x"], b["y"], marker="o", ms=7, mfc=CH.ENCRE, mec="white", mew=1.2, zorder=10)
        ax.annotate(f"{b['id']} · canal {b['canal']}", (b["x"], b["y"]), xytext=(5, -9), textcoords="offset points",
                    fontsize=6, color=CH.ENCRE, weight="bold", zorder=11,
                    bbox=dict(boxstyle="square,pad=0.12", fc="white", ec="none", alpha=0.85))
    ax.set_xlim(x0, x1)
    ax.set_ylim(y1, y0)
    ax.set_axis_off()
    s = e["stats"]
    noms = {"N-1": "Sous-sol", "N0": "Rez-de-chaussée", "N1": "Étage 1"}
    ax.set_title(f"Couverture Wi-Fi prévue (5 GHz) · {noms[e['code']]} · {len(e['bornes'])} bornes\n"
                 f"Signal reçu de la meilleure borne. Objectif ≥ {R.OBJECTIF_DBM:.0f} dBm atteint sur {s['couverture_pct']} % "
                 f"de la surface ; une 2e borne ≥ {R.ROAMING_DBM:.0f} dBm (passage d'une borne à l'autre) sur {s['itinerance_pct']} %.",
                 fontsize=9, loc="left", color=CH.ENCRE)
    fig.text(0.01, 0.005, CH.mention_figure("04") + " · étude Wi-Fi prédictive", fontsize=6.5, color=CH.DISCRET)
    ax.legend(handles=[Patch(color=np.array(c) / 255, label=l, alpha=0.7) for _v, l, c in BANDES]
              + [plt.Line2D([], [], marker="o", ls="", mfc=CH.ENCRE, mec="white", label="borne Wi-Fi (AP-niveau-nn · canal)")],
              loc="lower right", fontsize=7.5, framealpha=0.95, title="Signal reçu", title_fontsize=8)
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / f"{e['code']}_rssi.png", bbox_inches="tight")
    plt.close(fig)


def main():
    data = bat.charger()
    ppm = data["pt_par_m"] * data["dpi"] / 72
    etudes = []
    for niv in data["niveaux"]:
        e = etudier(niv, ppm)
        etudes.append(e)
        s = e["stats"]
        print(f"{e['code']} : {len(e['bornes'])} bornes ({sum(b['motif'] == 'capacité' for b in e['bornes'])} capacité), "
              f"couverture {s['couverture_pct']} %, itinérance {s['itinerance_pct']} %, {s['surface_cible_m2']} m² à couvrir")
    conflits = plan_canaux(etudes)
    print(f"Plan de canaux : {len(R.CANAUX_40)} canaux de 40 MHz, {conflits} conflit(s) co-canal restant(s)")
    OUT.mkdir(parents=True, exist_ok=True)
    for e in etudes:
        carte(e)
    bornes = [b for e in etudes for b in e["bornes"]]
    with open(OUT / "bornes.csv", "w", newline="", encoding="utf-8") as f:
        wr = csv.DictWriter(f, fieldnames=["id", "niveau", "salle", "x", "y", "canal", "motif"])
        wr.writeheader()
        for b in bornes:
            wr.writerow({k: b[k] for k in wr.fieldnames})
    resume = {"hypotheses": {"frequence_MHz": R.FREQ_MHZ, "PIRE_dBm": R.PIRE_DBM, "exposant": R.EXPOSANT,
                             "affaiblissements_dB": {"mur": R.AFFAIBLISSEMENT[1], "cloison": R.AFFAIBLISSEMENT[2],
                                                     "vitrage": R.AFFAIBLISSEMENT[3]},
                             "objectif_dBm": R.OBJECTIF_DBM, "itinerance_dBm": R.ROAMING_DBM},
              "niveaux": [{"code": e["code"], "nom": e["nom"], "stats": e["stats"], "par_salle": e["par_salle"]}
                          for e in etudes],
              "bornes": bornes, "conflits_co_canal": conflits}
    (OUT / "bornes.json").write_text(json.dumps(resume, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Total : {len(bornes)} bornes -> {OUT}")


if __name__ == "__main__":
    main()
