"""Rendu du plan de câblage : un plan par niveau (PDF, SVG, PNG) et le synoptique des rocades."""
import datetime
from pathlib import Path

import cv2
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import Patch, Rectangle, FancyBboxPatch  # noqa: E402

HERE = Path(__file__).resolve().parent
BUILD = HERE / "build"
OUT = HERE.parent / "livrables" / "plan_cablage"
ENCRE = "#1F4E8C"
TEINTES = {"LT01": "#2C6E8C", "LT02": "#8C682C"}
NOMS = {"N-1": "Sous-sol", "N0": "Rez-de-chaussée", "N1": "Étage 1"}
G = 0.25
TYPES_CHEMIN = {"circulation", "technique", "salle_serveur", "parking", "exterieur"}

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 7, "svg.fonttype": "none"})


def _xy(cells, W):
    ys, xs = np.divmod(np.array(cells), W)
    return (xs + 0.5) * G, (ys + 0.5) * G


def plans(data, ppm, reseaux, prises, locaux, srv, chemins, traces, adductions, colonnes, resume):
    (OUT / "plans").mkdir(parents=True, exist_ok=True)
    date = datetime.date.today().strftime("%d/%m/%Y")
    for niv in data["niveaux"]:
        code = niv["code"]
        rs = reseaux[code]
        H, W = rs.shape
        fond = cv2.imread(str(BUILD / f"{code}.png"), cv2.IMREAD_GRAYSCALE)
        mes = [p for p in prises if p["niveau"] == code]
        # emprise utile
        ys, xs = np.nonzero(rs.cout > 0)
        x0, x1 = xs.min() * G - 3, xs.max() * G + 3
        y0, y1 = ys.min() * G - 3, ys.max() * G + 3

        fig = plt.figure(figsize=(16.54, 11.69))  # A3 paysage
        ax = fig.add_axes([0.02, 0.04, 0.70, 0.90])
        ax.imshow(fond, cmap="gray", extent=(0, fond.shape[1] / ppm, fond.shape[0] / ppm, 0), alpha=0.45, vmin=0, vmax=255)

        # Salles teintées selon le local qui les dessert
        teinte = np.zeros((H, W, 4))
        par_salle = {}
        for p in mes:
            par_salle.setdefault(p["salle"], []).append(p["local"][-4:])
        for s in niv["salles"]:
            if s["nom"] in par_salle and s.get("contour"):
                lt = max(set(par_salle[s["nom"]]), key=par_salle[s["nom"]].count)
                m = np.zeros((H, W), np.uint8)
                cv2.fillPoly(m, [np.round(np.array(s["contour"]) / G).astype(np.int32)], 1)
                rgb = np.array(matplotlib.colors.to_rgb(TEINTES[lt]))
                teinte[m > 0, :3] = rgb
                teinte[m > 0, 3] = 0.10
        ax.imshow(teinte, extent=(0, W * G, H * G, 0), interpolation="nearest")

        # Chemins de câbles, épaisseur selon le nombre de câbles. Dans les salles, les câbles
        # suivent une goulotte le long des murs depuis la porte : on ne dessine que les
        # chemins des circulations et locaux techniques, et les entrées dans les salles.
        cnt = chemins[code].copy()
        types = [s["type"] for s in niv["salles"]]
        dans_salle = np.zeros((H, W), bool)
        z = rs.zone
        for i, t in enumerate(types):
            if t not in TYPES_CHEMIN:
                dans_salle |= z == i
        cnt[dans_salle] = 0  # restent les couloirs, les locaux et les embrasures de portes (entrées)
        img = np.zeros((H, W, 4))
        for lim, col in ((1, "#C98A2B"), (41, "#A8650B"), (91, "#7A3E0B")):
            m = cv2.dilate((cnt >= lim).astype(np.uint8), np.ones((2 if lim == 1 else 3, 2 if lim == 1 else 3), np.uint8)) > 0
            img[m, :3] = matplotlib.colors.to_rgb(col)
            img[m, 3] = 0.85
        ax.imshow(img, extent=(0, W * G, H * G, 0), interpolation="nearest")

        # Rocades et adductions
        for voie, cells in traces[code]:
            if not cells:
                continue
            X, Y = _xy(cells, W)
            if voie == "FAI":
                ax.plot(X, Y, color="#1D7A4E", lw=2.2, alpha=0.9, solid_capstyle="round")
            else:
                ax.plot(X, Y, color=ENCRE, lw=1.6, ls="-" if voie == "A" else (0, (4, 2)), alpha=0.9)

        # Prises
        styles = {"usager": dict(marker="s", ms=2.6, mfc="#212121", mec="none"),
                  "wifi": dict(marker="o", ms=6, mfc=ENCRE, mec="white", mew=0.8),
                  "camera": dict(marker="^", ms=6, mfc="#B3261E", mec="white", mew=0.8),
                  "badge": dict(marker="D", ms=5, mfc="#5C2C8C", mec="white", mew=0.8)}
        for t, st in styles.items():
            pts = [(p["x"], p["y"]) for p in mes if p["type"] == t]
            if pts:
                ax.plot(*zip(*pts), ls="", **st)

        # Locaux techniques, salle serveur, colonnes
        for lc, lt in locaux.items():
            if lt["niveau"] != code:
                continue
            ax.add_patch(Rectangle((lt["x"] - 0.9, lt["y"] - 0.9), 1.8, 1.8, fc=TEINTES[lc[-4:]], ec="white", lw=1.2, zorder=5))
            ax.annotate(lc, (lt["x"], lt["y"] - 1.2), ha="center", va="bottom", fontsize=7.5, weight="bold",
                        color=TEINTES[lc[-4:]], zorder=6,
                        bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.85))
        if code == "N-1":
            bx0, by0, bx1, by1 = srv["bbox"]
            ax.add_patch(Rectangle((bx0, by0), bx1 - bx0, by1 - by0, fc="#1F4E8C22", ec=ENCRE, lw=1.4, hatch="////", zorder=4))
            ax.annotate("SALLE SERVEUR\n(cœur, DMZ, datacenter, NM)", ((bx0 + bx1) / 2, (by0 + by1) / 2), ha="center", va="center",
                        fontsize=7, weight="bold", color=ENCRE, zorder=6,
                        bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="none", alpha=0.9))
            for a in adductions:
                dx = -4 if a["operateur"] == "FAI 1" else 4
                ax.annotate(a["operateur"], (a["x"], a["y"]), xytext=(a["x"] + dx, a["y"] + 2.5), color="#1D7A4E", weight="bold",
                            fontsize=8, ha="center", arrowprops=dict(arrowstyle="-|>", color="#1D7A4E", lw=1.5), zorder=7)
        for nomc, c in colonnes.items():
            ax.plot(c["x"], c["y"] + (1.6 if code != "N0" else 0), marker="o", ms=10, mfc="white", mec=ENCRE, mew=2, zorder=7)
            ax.plot(c["x"], c["y"] + (1.6 if code != "N0" else 0), marker="o", ms=3, mfc=ENCRE, mec=ENCRE, zorder=8)
            ax.annotate(f"colonne {nomc}", (c["x"], c["y"] + (1.6 if code != "N0" else 0)), xytext=(8, -2), textcoords="offset points",
                        fontsize=6.5, color=ENCRE, zorder=8)

        # Échelle 5 m
        sx, sy = x0 + 2, y1 - 1.5
        ax.plot([sx, sx + 5], [sy, sy], color="#212121", lw=2)
        ax.text(sx + 2.5, sy - 0.5, "5 m", ha="center", fontsize=7)
        ax.set_xlim(x0, x1)
        ax.set_ylim(y1, y0)
        ax.set_aspect("equal")
        ax.set_axis_off()

        # Panneau de droite : titre, légende, chiffres
        side = fig.add_axes([0.74, 0.04, 0.24, 0.90])
        side.set_axis_off()
        side.text(0, 1.0, "Plan de câblage", fontsize=15, weight="bold", family="DejaVu Serif", va="top")
        side.text(0, 0.965, f"{NOMS[code]} · Site de Marseille (IUT Génie Télécom, Luminy)", fontsize=8.5, va="top")
        side.text(0, 0.945, f"Point 04 du cahier des charges · {date} · fond : plan M301_25", fontsize=7, color="#6C6861", va="top")
        leg = [Line2D([], [], ls="", **styles["usager"], label="prise RJ45 Cat6A (usager)"),
               Line2D([], [], ls="", **styles["wifi"], label="borne Wi-Fi (prise au plafond)"),
               Line2D([], [], ls="", **styles["camera"], label="caméra IP"),
               Line2D([], [], ls="", **styles["badge"], label="badgeuse"),
               Patch(fc=TEINTES["LT01"], label="local technique LT01 (salles desservies teintées)"),
               Patch(fc=TEINTES["LT02"], label="local technique LT02"),
               Line2D([], [], color="#C98A2B", lw=2, label="chemin de câbles 100×50 (≤ 40 câbles)"),
               Line2D([], [], color="#A8650B", lw=3, label="chemin de câbles 200×60 (41 à 90)"),
               Line2D([], [], color="#7A3E0B", lw=4, label="chemin de câbles 300×100 (> 90)"),
               Line2D([], [], color=ENCRE, lw=1.6, label="rocade fibre OM4, voie A"),
               Line2D([], [], color=ENCRE, lw=1.6, ls=(0, (4, 2)), label="rocade fibre OM4, voie B"),
               Line2D([], [], marker="o", ls="", ms=8, mfc="white", mec=ENCRE, mew=2, label="colonne montante")]
        if code == "N-1":
            leg.append(Line2D([], [], color="#1D7A4E", lw=2.2, label="adduction opérateur"))
        side.legend(handles=leg, loc="upper left", bbox_to_anchor=(0, 0.92), frameon=False, fontsize=7.5)
        y = 0.56
        side.text(0, y, "Ce niveau", fontsize=9, weight="bold")
        par = {t: sum(p["type"] == t for p in mes) for t in ("usager", "wifi", "camera", "badge")}
        lignes = [f"{len(mes)} prises : {par['usager']} usagers, {par['wifi']} bornes, {par['camera']} caméras, {par['badge']} badgeuses",
                  f"Lien le plus long : {max(p['longueur'] for p in mes):.0f} m (limite 90 m)" if mes else ""]
        for b in resume["baies"]:
            if b["niveau"] == code:
                lignes.append(f"{b['local']} ({b['salle']}, {b['surface_m2']:.0f} m²) : {b['prises']} prises, {b['switchs_48p']} switch(s) 48p, "
                              f"{b['hauteur_U']}U, PoE {b['poe_W']} W")
        for k, l in enumerate(lignes):
            side.text(0, y - 0.025 * (k + 1), l, fontsize=7.2, wrap=True)
        y2 = y - 0.025 * (len(lignes) + 2)
        side.text(0, y2, "Règles", fontsize=9, weight="bold")
        regles = ["Câble Cat6A U/FTP, Euroclasse Cca-s1b,d1,a1 ; prises RJ45 Cat6A blindées.",
                  "Lien permanent ≤ 90 m (ISO/IEC 11801-1, EN 50173-1).",
                  "Longueur = 1,10 × cheminement + 3 m de descentes + 2 m de lovage.",
                  "Séparation courants forts / faibles selon EN 50174-2.",
                  "Repérage des prises : <local>-P<numéro> (ex. N0-LT02-P017), TIA-606.",
                  "Dans les salles : goulotte périmétrique depuis la porte (non dessinée).",
                  "Fond de plan : échelle mesurée sur le cartouche (±2 %)."]
        for k, l in enumerate(regles):
            side.text(0, y2 - 0.022 * (k + 1), "· " + l, fontsize=6.8, color="#3A3833")
        for ext in ("pdf", "svg", "png"):
            fig.savefig(OUT / "plans" / f"{code}_cablage.{ext}", dpi=170 if ext == "png" else None)
        plt.close(fig)


def synoptique(locaux, rocades, adductions, baies, resume):
    fig, ax = plt.subplots(figsize=(16.54, 10.5))
    ax.set_axis_off()
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 66)
    ax.text(0, 65.5, "Synoptique des rocades et adductions", fontsize=15, weight="bold", family="DejaVu Serif", va="top")
    ax.text(0, 62.6, "Fibre OM4 12 brins. Deux câbles par local, par deux chemins disjoints : voie A par la colonne montante la "
                     f"plus proche, voie B par l'autre colonne. Total ≈ {resume['fibre_m']} m de fibre.", fontsize=8, color="#3A3833", va="top")
    bandes = {"N1": (46, 56), "N0": (30, 40), "N-1": (5, 24)}
    for c, (y0, y1) in bandes.items():
        ax.add_patch(Rectangle((0, y0), 100, y1 - y0, fc="#F6F4EF", ec="none", zorder=0))
        ax.text(50, y1 - 1.0, NOMS[c], fontsize=9, color="#6C6861", weight="bold", va="top", ha="center")
    xcol = {"Nord": 36, "Sud": 64}
    for nomc, x in xcol.items():
        ax.add_patch(Rectangle((x - 2.6, 22), 5.2, 34, fc="#DCE6F3", ec="none", zorder=1))
        ax.text(x, 57.5, f"Colonne {nomc}", ha="center", fontsize=9, color=ENCRE, weight="bold")
    roc = {(r["local"], r["voie"]): r for r in rocades}
    bb = {b["local"]: b for b in baies}
    BW, BH = 24, 9.0
    pos = {"N1-LT01": (14, 51), "N1-LT02": (86, 51), "N0-LT01": (14, 35), "N0-LT02": (86, 35),
           "N-1-LT02": (14, 12), "N-1-LT01": (86, 12)}
    srv = (50, 12)

    def boite(lc, x, y):
        b = bb[lc]
        col = TEINTES[lc[-4:]]
        ax.add_patch(FancyBboxPatch((x - BW / 2, y - BH / 2), BW, BH, boxstyle="round,pad=0.3", fc="white", ec=col, lw=1.6, zorder=5))
        ax.text(x, y + 3.2, f"{lc} · {b['salle']} ({b['surface_m2']:.0f} m²)", ha="center", fontsize=8.5, weight="bold", color=col, zorder=6)
        ax.text(x, y + 1.4, f"{b['prises']} prises · {b['switchs_48p']} switch(s) 48p PoE+ · PoE {b['poe_W']} W", ha="center", fontsize=7.2, zorder=6)
        ax.text(x, y - 0.3, f"baie {b['baie']} ({b['hauteur_U']}U occupés)", ha="center", fontsize=7, color="#6C6861", zorder=6)
        for k, v in enumerate("AB"):
            r = roc[(lc, v)]
            ax.text(x, y - 2.1 - 1.6 * k, f"voie {v} : {r['par']} · {r['longueur']:.0f} m", ha="center", fontsize=7,
                    color=ENCRE, zorder=6)

    # Salle serveur
    ax.add_patch(FancyBboxPatch((srv[0] - 13, srv[1] - 5), 26, 10, boxstyle="round,pad=0.3", fc="#EAF0F8", ec=ENCRE, lw=1.8, zorder=5))
    ax.text(srv[0], srv[1] + 3, "SALLE SERVEUR · partie sud de J05", ha="center", fontsize=9.5, weight="bold", color=ENCRE, zorder=6)
    ax.text(srv[0], srv[1] + 0.8, "cœur CL-SW1/2, distribution DL-SW1 à 4", ha="center", fontsize=7.5, zorder=6)
    ax.text(srv[0], srv[1] - 1.0, "egress, DMZ, datacenter, Net Management", ha="center", fontsize=7.5, zorder=6)
    ax.text(srv[0], srv[1] - 3.0, "2 baies 42U · onduleurs A/B · clim N+1", ha="center", fontsize=7, color="#6C6861", zorder=6)

    # Fibres des locaux du RDC et de l'étage, par les colonnes
    decal = {"N0-LT01": -1.8, "N1-LT01": -0.6, "N0-LT02": 0.6, "N1-LT02": 1.8}
    for lc, (x, y) in pos.items():
        if lc.startswith("N-1"):
            continue
        for v in "AB":
            r = roc[(lc, v)]
            xc = xcol[r["par"].split()[-1]] + decal[lc]
            dy = 1.2 if v == "A" else -1.2
            bord = x + BW / 2 + 0.4 if x < 50 else x - BW / 2 - 0.4
            xs = [srv[0] + decal[lc] * 3, srv[0] + decal[lc] * 3, xc, xc, bord]
            ys = [srv[1] + 5.3, 19.5 + (0.4 if v == "A" else 0), 21 + (0.4 if v == "A" else 0), y + dy, y + dy]
            ax.plot(xs, ys, color=ENCRE, lw=1.3, ls="-" if v == "A" else (0, (4, 2)), zorder=3)
    # Locaux du sous-sol
    for lc in ("N-1-LT02", "N-1-LT01"):
        x, y = pos[lc]
        for v, dy in (("A", 1.0), ("B", -1.0)):
            xa = srv[0] - 13.3 if x < 50 else srv[0] + 13.3
            xb = x + BW / 2 + 0.4 if x < 50 else x - BW / 2 - 0.4
            ax.plot([xa, xb], [srv[1] + dy, y + dy], color=ENCRE, lw=1.3, ls="-" if v == "A" else (0, (4, 2)), zorder=3)
    for lc, (x, y) in pos.items():
        boite(lc, x, y)

    # Adductions
    for a in adductions:
        gauche = a["operateur"] == "FAI 1"
        xa = 2 if gauche else 98
        ax.annotate("", xy=(srv[0] - 13.3 if gauche else srv[0] + 13.3, srv[1] - 3.5), xytext=(xa, 2.5),
                    arrowprops=dict(arrowstyle="-|>", color="#1D7A4E", lw=2.2), zorder=4)
        ax.text(xa, 0.6, f"{a['operateur']} · {a['entree']} · {a['longueur_interne']:.0f} m jusqu'à la salle serveur",
                ha="left" if gauche else "right", fontsize=7.5, color="#1D7A4E", weight="bold")
    ax.legend(handles=[Line2D([], [], color=ENCRE, lw=1.3, label="fibre voie A"),
                       Line2D([], [], color=ENCRE, lw=1.3, ls=(0, (4, 2)), label="fibre voie B"),
                       Line2D([], [], color="#1D7A4E", lw=2.2, label="adduction opérateur")],
              loc="upper right", bbox_to_anchor=(1, 0.985), fontsize=7.5, frameon=False, ncol=3)
    for ext in ("pdf", "svg", "png"):
        fig.savefig(OUT / f"synoptique.{ext}", dpi=170 if ext == "png" else None, bbox_inches="tight")
    plt.close(fig)
