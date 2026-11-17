#!/usr/bin/env python3
"""Extrait les salles des plans d'architecte (docs/plans_batiment/*.pdf).

Pour chaque niveau :
  - lit les étiquettes de salle et leur position (pdftotext -bbox-layout) ;
  - rastérise le plan (pdftoppm), efface le texte, garde les traits (murs, cloisons,
    vitrages) en les classant par couleur ;
  - ferme les ouvertures de portes (dilatation), puis remplit chaque salle depuis
    son étiquette pour obtenir son contour et sa surface ;
  - mesure l'échelle graphique (« 5.00 m ») du cartouche.

Produit cablage/build/salles.json et, par niveau, cablage/build/<niveau>_murs.png
(carte des obstacles utilisée par l'étude RSSI) et <niveau>_salles.png (contrôle visuel).

Dépendances : poppler-utils (pdftotext, pdftoppm), numpy, opencv-python.
Usage : python3 cablage/salles.py
"""
import json
import re
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
PLANS = ROOT / "docs" / "plans_batiment"
BUILD = Path(__file__).resolve().parent / "build"
DPI = 200
PX_PER_PT = DPI / 72

NIVEAUX = [
    ("N-1", "SOUS-SOL"),
    ("N0", "RDC"),
    ("N1", "ETAGE 1"),
]


def pdf(nom):
    return PLANS / f"M301_25 - LUMINY - IUT-GENIE TELECOMMUNICATION - {nom}.pdf"


# ---------------------------------------------------------------------------
# Étiquettes
# ---------------------------------------------------------------------------
def etiquettes(path):
    out = subprocess.run(["pdftotext", "-bbox-layout", str(path), "-"], capture_output=True, text=True, check=True).stdout
    out = re.sub(r"<!DOCTYPE[^>]*>", "", out)
    out = re.sub(r'xmlns="[^"]+"', "", out)
    root = ET.fromstring(out)
    lignes, mots = [], []
    for line in root.iter("line"):
        words = [w for w in line.iter("word")]
        txt = " ".join((w.text or "").strip() for w in words).strip()
        box = [float(line.get(k)) for k in ("xMin", "yMin", "xMax", "yMax")]
        lignes.append((txt, box))
        for w in words:
            mots.append(((w.text or "").strip(), [float(w.get(k)) for k in ("xMin", "yMin", "xMax", "yMax")]))
    return lignes, mots


def echelle(img_gray, mots):
    """Longueur en points de la barre « 5.00 m » du cartouche."""
    for t, (x0, y0, x1, y1) in mots:
        if t == "5.00":
            cx = (x0 + x1) / 2 * PX_PER_PT
            best = 0
            for dy in range(0, int(14 * PX_PER_PT)):
                y = int(y1 * PX_PER_PT) + dy
                row = img_gray[y] < 110
                # plus longue suite sombre qui contient l'abscisse du texte
                xs = np.flatnonzero(row)
                if not len(xs):
                    continue
                runs = np.split(xs, np.flatnonzero(np.diff(xs) > 2) + 1)
                for r in runs:
                    n = r[-1] - r[0] + 1
                    # la barre est centrée sous le texte et ne fait que quelques fois sa largeur
                    if r[0] <= cx <= r[-1] and abs((r[0] + r[-1]) / 2 - cx) < 0.15 * n and n < 8 * (x1 - x0) * PX_PER_PT:
                        best = max(best, n)
            if best:
                return best / PX_PER_PT / 5.0  # points par mètre
    raise RuntimeError("échelle introuvable")


# ---------------------------------------------------------------------------
# Traits du plan, classés par couleur
# ---------------------------------------------------------------------------
def rasteriser(path, stem):
    BUILD.mkdir(exist_ok=True)
    out = BUILD / stem
    subprocess.run(["pdftoppm", "-r", str(DPI), "-png", "-singlefile", str(path), str(out)], check=True)
    return cv2.imread(str(out) + ".png", cv2.IMREAD_COLOR)


def classer_traits(bgr):
    """0 = vide, 1 = mur (noir/gris foncé), 2 = cloison (couleur), 3 = vitrage (bleu)."""
    b, g, r = [bgr[..., i].astype(int) for i in range(3)]
    dark = (r + g + b) < 3 * 140
    sat = (np.max(bgr, axis=2).astype(int) - np.min(bgr, axis=2).astype(int)) > 60
    bleu = sat & (b > r + 40) & (b > g + 40)
    cloison = sat & ~bleu
    mur = dark & ~sat
    cls = np.zeros(bgr.shape[:2], np.uint8)
    cls[cloison] = 2
    cls[bleu] = 3
    cls[mur] = 1
    return cls


# Zones sans étiquette sur le plan, ajoutées à partir d'un point (niveau, nom, x m, y m)
ZONES_SANS_ETIQUETTE = [
    ("N-1", "PARKING EST", 62.0, 45.0),  # le parking se prolonge à l'est d'une cloison, sans étiquette
    # les poutres (pointillés) découpent le parking en bandes : bandes nord et sud
    ("N-1", "PARKING NORD", 45.0, 40.5), ("N-1", "PARKING NORD EST", 62.0, 40.5),
    ("N-1", "PARKING SUD", 40.0, 51.8), ("N-1", "PARKING SUD EST", 66.0, 51.8),
]

EXCLUS_TEXTE = re.compile(r"^(Echelle|Bâtiment|Plan|Nom|Date|M301|00|5\.00|libre|REZ|ETAGE 1 -|SOUS-SOL -|TOITURE -)")


def main():
    # Les plans partagent le même repère (l'escalier ESC 01 tombe au même endroit sur les
    # trois niveaux) : on mesure l'échelle graphique de chacun et on garde la moyenne.
    mesures = {}
    for code, nom in NIVEAUX:
        path = pdf(nom)
        _l, mots = etiquettes(path)
        gray = cv2.cvtColor(rasteriser(path, code), cv2.COLOR_BGR2GRAY)
        mesures[code] = echelle(gray, mots)
    pt_par_m = sum(mesures.values()) / len(mesures)
    px_par_m = pt_par_m * PX_PER_PT
    print("Échelles mesurées (pt/m) : " + ", ".join(f"{k} {v:.2f}" for k, v in mesures.items())
          + f" -> {pt_par_m:.2f} retenue (écart ±{100 * (max(mesures.values()) - min(mesures.values())) / 2 / pt_par_m:.1f} %)")
    data = {"dpi": DPI, "pt_par_m": round(pt_par_m, 4), "mesures_pt_par_m": {k: round(v, 3) for k, v in mesures.items()},
            "niveaux": []}
    for code, nom in NIVEAUX:
        path = pdf(nom)
        lignes, mots = etiquettes(path)
        bgr = cv2.imread(str(BUILD / code) + ".png", cv2.IMREAD_COLOR)
        gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
        h, w = gray.shape

        # Cartouche (bas à droite) et texte effacés
        cls = classer_traits(bgr)
        cls[int(0.865 * h):, int(0.495 * w):] = 0
        for _t, (x0, y0, x1, y1) in mots:
            cls[int(y0 * PX_PER_PT) - 1:int(y1 * PX_PER_PT) + 2, int(x0 * PX_PER_PT) - 1:int(x1 * PX_PER_PT) + 2] = 0
        cv2.imwrite(str(BUILD / f"{code}_murs.png"), cls)

        # Fermeture des portes : dilatation des traits d'environ 0,5 m
        traits = (cls > 0).astype(np.uint8)
        r = max(3, int(round(0.5 * px_par_m)))
        noyau = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))
        ferme = cv2.dilate(traits, noyau)
        libre = (ferme == 0).astype(np.uint8)
        libre_vrai = (traits == 0).astype(np.uint8)

        salles = []
        deja = np.zeros_like(libre)
        vis = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
        rng = np.random.default_rng(1)
        extra = [(nom2, [x * pt_par_m - 1, y * pt_par_m - 1, x * pt_par_m + 1, y * pt_par_m + 1])
                 for c2, nom2, x, y in ZONES_SANS_ETIQUETTE if c2 == code]
        for txt, (x0, y0, x1, y1) in lignes + extra:
            if not txt or EXCLUS_TEXTE.match(txt) or y0 > 0.865 * 842 and x0 > 0.495 * 1191:
                continue
            cx, cy = int((x0 + x1) / 2 * PX_PER_PT), int((y0 + y1) / 2 * PX_PER_PT)
            # point libre le plus proche de l'étiquette
            ys, xs = np.nonzero(libre[max(0, cy - 3 * r):cy + 3 * r, max(0, cx - 3 * r):cx + 3 * r])
            if not len(xs):
                salles.append({"nom": txt, "x": cx / px_par_m, "y": cy / px_par_m, "surface": None})
                continue
            i = np.argmin((xs + max(0, cx - 3 * r) - cx) ** 2 + (ys + max(0, cy - 3 * r) - cy) ** 2)
            sx, sy = xs[i] + max(0, cx - 3 * r), ys[i] + max(0, cy - 3 * r)
            mask = np.zeros((h + 2, w + 2), np.uint8)
            cv2.floodFill(libre, mask, (int(sx), int(sy)), 2, flags=4 | (255 << 8) | cv2.FLOODFILL_MASK_ONLY)
            m0 = mask[1:-1, 1:-1]
            bx, by, bw, bh = cv2.boundingRect(m0)
            if bx <= 2 or by <= 2 or bx + bw >= w - 3 or by + bh >= h - 3 or bw * bh > (60 * px_par_m) ** 2:
                salles.append({"nom": txt, "x": cx / px_par_m, "y": cy / px_par_m, "surface": None, "fuite": True})
                continue
            # travail sur un recadrage autour de la salle
            pad = r + 3
            X0, Y0, X1, Y1 = max(0, bx - pad), max(0, by - pad), min(w, bx + bw + pad), min(h, by + bh + pad)
            mc = (cv2.dilate(m0[Y0:Y1, X0:X1], noyau) > 0) & (libre_vrai[Y0:Y1, X0:X1] > 0)
            m = np.zeros((h, w), bool)
            m[Y0:Y1, X0:X1] = mc
            surf = float(mc.sum()) / px_par_m ** 2
            ys2, xs2 = np.nonzero(mc)
            xs2 = xs2 + X0
            ys2 = ys2 + Y0
            cnts, _ = cv2.findContours(mc.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            cnt = max(cnts, key=cv2.contourArea) + np.array([X0, Y0])
            poly = cv2.approxPolyDP(cnt, 0.15 * px_par_m, True).reshape(-1, 2)
            mom = cv2.moments(mc.astype(np.uint8), binaryImage=True)
            mom = {"m00": mom["m00"], "m10": mom["m10"] + X0 * mom["m00"], "m01": mom["m01"] + Y0 * mom["m00"]}
            salles.append({
                "nom": txt,
                "x": mom["m10"] / mom["m00"] / px_par_m,
                "y": mom["m01"] / mom["m00"] / px_par_m,
                "surface": round(surf, 1),
                "bbox": [round(v / px_par_m, 2) for v in (xs2.min(), ys2.min(), xs2.max(), ys2.max())],
                "contour": [[round(float(px) / px_par_m, 2), round(float(py) / px_par_m, 2)] for px, py in poly],
                "partage": bool((deja[Y0:Y1, X0:X1] & mc).any()),
            })
            deja[Y0:Y1, X0:X1] |= mc.astype(np.uint8)
            col = [int(c) for c in rng.integers(60, 230, 3)]
            sub = vis[Y0:Y1, X0:X1]
            sub[mc] = (0.55 * sub[mc] + 0.45 * np.array(col)).astype(np.uint8)
            cv2.putText(vis, f"{txt} {surf:.0f}", (cx - 40, cy), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 0), 1, cv2.LINE_AA)
        cv2.imwrite(str(BUILD / f"{code}_salles.png"), vis)
        data["niveaux"].append({
            "code": code, "nom": nom, "pt_par_m": round(pt_par_m, 4), "px_par_m": round(px_par_m, 4),
            "taille_px": [w, h], "salles": salles,
        })
        ok = sum(1 for s in salles if s.get("surface"))
        print(f"{code} ({nom}) : {ok}/{len(salles)} salles délimitées")
    (BUILD / "salles.json").write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
