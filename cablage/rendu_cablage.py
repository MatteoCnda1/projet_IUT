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


def fond_murs(code):
    """Fond de plan sans le texte de l'architecte : murs foncés, cloisons grises, vitrages bleutés."""
    cls = cv2.imread(str(BUILD / f"{code}_murs.png"), cv2.IMREAD_GRAYSCALE)
    rgba = np.zeros(cls.shape + (4,), np.float32)
    for c, (col, a) in {1: ("#3A3833", 1.0), 2: ("#8C8880", 0.9), 3: ("#7FA6C9", 0.9)}.items():
        rgba[cls == c, :3] = matplotlib.colors.to_rgb(col)
        rgba[cls == c, 3] = a
    return rgba


ETIQ_SALLES = {"tp", "projet", "cours", "accueil", "bureau", "atelier", "prepa", "vie", "amphi", "salle_serveur"}


def etiquettes_salles(ax, niv, mes, gris_circ=True):
    nb = {}
    for p in mes:
        if p["type"] == "usager":
            nb[p["salle"]] = nb.get(p["salle"], 0) + 1
    for s in niv["salles"]:
        if not s.get("contour") or not s.get("surface"):
            continue
        if s["type"] in ETIQ_SALLES:
            txt = s["nom"] + (f"\n{nb[s['nom']]} prises" if nb.get(s["nom"]) else "")
            ax.text(s["x"], s["y"] + 1.1, txt, ha="center", va="top", fontsize=5.6, color="#212121", zorder=9,
                    bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.75))
        elif gris_circ and s["type"] in ("circulation", "parking") and s["surface"] > 15:
            ax.text(s["x"], s["y"], s["nom"], ha="center", va="center", fontsize=5, color="#8C8880", style="italic", zorder=8)


def plans(data, ppm, reseaux, prises, locaux, srv, chemins, traces, adductions, colonnes, resume):
    (OUT / "plans").mkdir(parents=True, exist_ok=True)
    date = datetime.date.today().strftime("%d/%m/%Y")
    for niv in data["niveaux"]:
        code = niv["code"]
        rs = reseaux[code]
        H, W = rs.shape
        mes = [p for p in prises if p["niveau"] == code]
        routes = [p for p in prises if p.get("_route") == code]
        ys, xs = np.nonzero(rs.cout > 0)
        x0, x1 = xs.min() * G - 3, xs.max() * G + 3
        y0, y1 = ys.min() * G - 3, ys.max() * G + 3

        fig = plt.figure(figsize=(16.54, 11.69))  # A3 paysage
        ax = fig.add_axes([0.01, 0.03, 0.72, 0.92])
        murs = fond_murs(code)
        ax.imshow(murs, extent=(0, murs.shape[1] / ppm, murs.shape[0] / ppm, 0), interpolation="antialiased", zorder=1)

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
                teinte[m > 0, :3] = matplotlib.colors.to_rgb(TEINTES[lt])
                teinte[m > 0, 3] = 0.08
        ax.imshow(teinte, extent=(0, W * G, H * G, 0), interpolation="nearest", zorder=2)

        # Chemins de câbles (couloirs, locaux), épaisseur selon le nombre de câbles
        cnt = chemins[code].copy()
        dans_salle = np.zeros((H, W), bool)
        for k, s in enumerate(niv["salles"]):
            if s["type"] not in TYPES_CHEMIN:
                dans_salle |= rs.zone == k
        cnt[dans_salle] = 0
        img = np.zeros((H, W, 4))
        for lim, col, e in ((1, "#D9A441", 2), (41, "#B8741A", 3), (91, "#7A3E0B", 4)):
            m = cv2.dilate((cnt >= lim).astype(np.uint8), np.ones((e, e), np.uint8)) > 0
            img[m, :3] = matplotlib.colors.to_rgb(col)
            img[m, 3] = 0.9
        ax.imshow(img, extent=(0, W * G, H * G, 0), interpolation="nearest", zorder=3)

        # Câbles dans les salles : de la porte (chemin de câbles) jusqu'à la prise, en goulotte
        for p in routes:
            cells = p.get("_cells") or []
            seg = []
            for c in cells:
                seg.append(c)
                k = rs.zone.flat[c]
                if k >= 0 and niv["salles"][k]["type"] in TYPES_CHEMIN:
                    break
            if len(seg) > 1:
                pts = np.c_[_xy(seg, W)].astype(np.float32)
                pts = cv2.approxPolyDP(pts.reshape(-1, 1, 2), 0.25, False).reshape(-1, 2)
                ax.plot(pts[:, 0], pts[:, 1], color="#B8741A", lw=0.45, alpha=0.8, zorder=4)

        # Rocades et adductions
        for voie, cells in traces[code]:
            if cells:
                X, Y = _xy(cells, W)
                if voie == "FAI":
                    ax.plot(X, Y, color="#1D7A4E", lw=2.4, alpha=0.95, zorder=6, solid_capstyle="round")
                else:
                    ax.plot(X, Y, color=ENCRE, lw=1.8, ls="-" if voie == "A" else (0, (4, 2)), alpha=0.95, zorder=6)

        etiquettes_salles(ax, niv, mes)

        # Équipements, avec repères
        styles = {"usager": dict(marker="s", ms=2.8, mfc="#212121", mec="none"),
                  "wifi": dict(marker="o", ms=7, mfc=ENCRE, mec="white", mew=0.9),
                  "camera": dict(marker="^", ms=7, mfc="#B3261E", mec="white", mew=0.9),
                  "badge": dict(marker="D", ms=5.5, mfc="#5C2C8C", mec="white", mew=0.9)}
        for t, st in styles.items():
            pts = [(p["x"], p["y"]) for p in mes if p["type"] == t]
            if pts:
                ax.plot(*zip(*pts), ls="", zorder=10, **st)
        for t, pref, col in (("wifi", "AP", ENCRE), ("camera", "C", "#B3261E"), ("badge", "B", "#5C2C8C")):
            for k, p in enumerate(sorted((p for p in mes if p["type"] == t), key=lambda p: (p["y"], p["x"])), 1):
                lab = pref + p["usage"].split()[1][-2:] if t == "wifi" else f"{pref}{k}"
                p["repere"] = lab
                ax.annotate(lab, (p["x"], p["y"]), xytext=(5, 3), textcoords="offset points", fontsize=5.8, weight="bold",
                            color=col, zorder=11, bbox=dict(boxstyle="round,pad=0.1", fc="white", ec="none", alpha=0.8))

        for lc, lt in locaux.items():
            if lt["niveau"] != code:
                continue
            ax.add_patch(Rectangle((lt["x"] - 0.9, lt["y"] - 0.9), 1.8, 1.8, fc=TEINTES[lc[-4:]], ec="white", lw=1.2, zorder=12))
            ax.annotate(f"{lc}\nlocal technique", (lt["x"], lt["y"] - 1.1), ha="center", va="bottom", fontsize=7, weight="bold",
                        color=TEINTES[lc[-4:]], zorder=13, bbox=dict(boxstyle="round,pad=0.2", fc="white", ec=TEINTES[lc[-4:]], lw=0.8))
        if code == "N-1":
            bx0, by0, bx1, by1 = srv["bbox"]
            ax.add_patch(Rectangle((bx0, by0), bx1 - bx0, by1 - by0, fc="#1F4E8C22", ec=ENCRE, lw=1.6, hatch="////", zorder=5))
            ax.annotate("SALLE SERVEUR", ((bx0 + bx1) / 2, (by0 + by1) / 2), ha="center", va="center", fontsize=8, weight="bold",
                        color=ENCRE, zorder=13, bbox=dict(boxstyle="round,pad=0.2", fc="white", ec=ENCRE, lw=0.8))
            for a in adductions:
                dx = -5 if a["operateur"] == "FAI 1" else 5
                ax.annotate(f"Arrivée {a['operateur']}", (a["x"], a["y"]), xytext=(a["x"] + dx, a["y"] + 3), color="#1D7A4E",
                            weight="bold", fontsize=8, ha="center", zorder=13,
                            arrowprops=dict(arrowstyle="-|>", color="#1D7A4E", lw=1.6))
        for nomc, c in colonnes.items():
            yy = c["y"] + (1.6 if code != "N0" else 0)
            ax.plot(c["x"], yy, marker="o", ms=11, mfc="white", mec=ENCRE, mew=2.2, zorder=12)
            ax.plot(c["x"], yy, marker="o", ms=3.5, mfc=ENCRE, mec=ENCRE, zorder=13)
            ax.annotate(f"colonne montante {nomc}", (c["x"], yy), xytext=(9, -3), textcoords="offset points", fontsize=6.5,
                        color=ENCRE, weight="bold", zorder=13, bbox=dict(boxstyle="round,pad=0.1", fc="white", ec="none", alpha=0.85))

        # Échelle 5 m
        sx, sy = x0 + 2, y1 - 1.5
        ax.plot([sx, sx + 5], [sy, sy], color="#212121", lw=2.5)
        ax.plot([sx, sx], [sy - 0.4, sy + 0.4], color="#212121", lw=1.5)
        ax.plot([sx + 5, sx + 5], [sy - 0.4, sy + 0.4], color="#212121", lw=1.5)
        ax.text(sx + 2.5, sy - 0.7, "5 m", ha="center", fontsize=7.5)
        ax.set_xlim(x0, x1)
        ax.set_ylim(y1, y0)
        ax.set_aspect("equal")
        ax.set_axis_off()

        # Panneau de droite : titre, légende, chiffres
        side = fig.add_axes([0.745, 0.03, 0.245, 0.92])
        side.set_axis_off()
        side.set_xlim(0, 1)
        side.set_ylim(0, 1)
        side.text(0, 1.0, "Plan de câblage", fontsize=16, weight="bold", family="DejaVu Serif", va="top")
        side.text(0, 0.968, NOMS[code], fontsize=12, weight="bold", color=ENCRE, va="top")
        side.text(0, 0.945, f"IUT Génie Télécom, Luminy · point 04 · {date}", fontsize=7.5, color="#6C6861", va="top")
        side.add_patch(Rectangle((0, 0.655), 1, 0.27, fc="#F6F4EF", ec="#DEDAD1", lw=0.8))
        side.text(0.03, 0.91, "LÉGENDE", fontsize=8.5, weight="bold", va="top")
        leg = [Line2D([], [], ls="", **styles["usager"], label="prise RJ45 Cat6A (poste, téléphone)"),
               Line2D([], [], ls="", **styles["wifi"], label="borne Wi-Fi au plafond (APxx)"),
               Line2D([], [], ls="", **styles["camera"], label="caméra IP (Cx)"),
               Line2D([], [], ls="", **styles["badge"], label="lecteur de badge (Bx)"),
               Patch(fc=TEINTES["LT01"], label="local technique LT01 et salles qu'il dessert"),
               Patch(fc=TEINTES["LT02"], label="local technique LT02 et salles qu'il dessert"),
               Line2D([], [], color="#D9A441", lw=2.5, label="chemin de câbles en couloir (≤ 40 câbles)"),
               Line2D([], [], color="#B8741A", lw=3.5, label="chemin de câbles (41 à 90 câbles)"),
               Line2D([], [], color="#7A3E0B", lw=4.5, label="chemin de câbles (> 90 câbles)"),
               Line2D([], [], color="#B8741A", lw=0.6, label="câble d'une prise, en goulotte dans la salle"),
               Line2D([], [], color=ENCRE, lw=1.8, label="fibre vers la salle serveur, voie A"),
               Line2D([], [], color=ENCRE, lw=1.8, ls=(0, (4, 2)), label="fibre de secours, voie B"),
               Line2D([], [], marker="o", ls="", ms=9, mfc="white", mec=ENCRE, mew=2, label="colonne montante (passage entre niveaux)")]
        if code == "N-1":
            leg.append(Line2D([], [], color="#1D7A4E", lw=2.4, label="arrivée opérateur (fibre Internet)"))
        side.legend(handles=leg, loc="upper left", bbox_to_anchor=(0.02, 0.895), frameon=False, fontsize=7.3, handlelength=2.2,
                    labelspacing=0.55)
        y = 0.62
        side.text(0, y, "Sur ce niveau", fontsize=10, weight="bold")
        par = {t: sum(p["type"] == t for p in mes) for t in ("usager", "wifi", "camera", "badge")}
        lignes = [f"{len(mes)} prises : {par['usager']} postes, {par['wifi']} bornes,", f"{par['camera']} caméras, {par['badge']} badgeuses",
                  f"Câble le plus long : {max(p['longueur'] for p in mes):.0f} m (maximum 90 m)" if mes else "", ""]
        for b in resume["baies"]:
            if b["niveau"] == code:
                lignes += [f"{b['local']} ({b['salle']} du plan, {b['surface_m2']:.0f} m²)",
                           f"   {b['prises']} prises · {b['switchs_48p']} switch(s) · baie {b['baie']}", ""]
        for k, l in enumerate(lignes):
            side.text(0, y - 0.024 * (k + 1), l, fontsize=7.6, weight="bold" if l.startswith(("N-1-", "N0-", "N1-")) else "normal")
        y2 = 0.13
        side.text(0, y2, "Comment lire ce plan", fontsize=9, weight="bold")
        aide = ["Chaque câble part d'une prise, longe la salle en goulotte,",
                "sort par la porte et rejoint le local technique par le chemin",
                "de câbles du couloir (en faux plafond). Les fibres relient",
                "chaque local à la salle serveur du sous-sol par deux chemins.",
                "Détail salle par salle : implantation.pdf · repères : prises.csv"]
        for k, l in enumerate(aide):
            side.text(0, y2 - 0.02 * (k + 1), l, fontsize=7, color="#3A3833")
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
