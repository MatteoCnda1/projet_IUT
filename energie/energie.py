#!/usr/bin/env python3
"""Point 14 du cahier des charges : énergie et refroidissement.

Calcule, à partir de l'inventaire du chiffrage et du plan de câblage :
  1. le bilan de puissance (salle serveur, baie par baie, et les 6 locaux techniques) ;
  2. le dimensionnement des onduleurs et leur autonomie ;
  3. la climatisation de la salle serveur et la ventilation des locaux techniques ;
  4. la consommation annuelle, le PUE et les gains Green IT (développement durable) ;
  5. les finances du lot : investissement, coûts annuels, économies, coût sur 5 ans.

Sorties dans livrables/energie_refroidissement/ : energie_refroidissement.pdf (+ .html),
bilan_puissance.csv, schemas/*.png|svg, resume.json (repris par chiffrage/estimation.py), README.md.
Usage : python3 energie/energie.py   (après cablage/plan_cablage.py ; puis python3 chiffrage/estimation.py)

Version 2 (après l'audit du 15/11/2026) : serveurs virtualisés (SYS-02), contrôleurs Wi-Fi physiques (NET-01),
protection contre l'eau et extinction automatique (SYS-03), arrêt ordonné par NUT. v1 : livrables/archives/v1_2026-11-15/.
"""
import csv
import datetime
import html
import json
import math
import shutil
import subprocess
import tempfile
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyBboxPatch, Rectangle  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "livrables" / "energie_refroidissement"
PLAN = json.loads((ROOT / "livrables" / "plan_cablage" / "resume.json").read_text(encoding="utf-8"))
ENCRE = "#1F4E8C"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8, "svg.fonttype": "none"})

# ---------------------------------------------------------------------------
# Hypothèses (toutes modifiables ici)
# ---------------------------------------------------------------------------
PRIX_KWH = 0.20            # € HT, même valeur que le chiffrage
CO2_KG_KWH = 0.052         # kg CO2e/kWh, électricité France (ordre de grandeur ADEME)
FOISONNEMENT = 0.80        # pointe réaliste = 80 % de la somme des maxima constructeur
RENDEMENT_ONDULEUR = 0.95  # onduleur en ligne double conversion (SRT)
PERTES_ONDULEUR_LT = 0.04  # onduleurs line-interactive des locaux techniques
EER = {"22 °C (usuel)": 3.0, "27 °C (proposé)": 3.4}  # efficacité de la clim selon la consigne
GAIN_CONFINEMENT = 0.10    # obturateurs + rideaux d'allée froide : -10 % sur la clim
SURFACE_SALLE = 25.0       # m² (partie sud de J05, plan de câblage)
DIM_SALLE = (6.35, 3.94)   # m
ECLAIRAGE_W_M2 = 8.0
HEURES_COUPURE_POE = 103   # h/semaine bornes coupées : 20h-7h en semaine + week-end
MARGE_NORMALE = 0.80       # charge maximale d'un onduleur en marche normale
MARGE_SECOURS = 0.90       # charge maximale d'un onduleur seul (l'autre en panne), en pointe
AUTONOMIE_VISEE = 20.0     # min, si un des deux onduleurs est en panne : arrêt ordonné NUT (13 min) + marge (v2 ; v1 : 10 min)

# Inventaire de la salle serveur : (repères, modèle, nombre, baie, alimentations, W typique, W max, U)
# Puissances : fiches constructeur, valeurs typiques arrondies (à affiner avec les configurateurs).
SALLE = [
    ("EL-RTR1, EL-RTR2", "Cisco C8200L-1N-4T", 2, "1", 1, 20, 30, 1),
    ("EL-FGT1, EL-FGT2", "FortiGate 120G", 2, "1", 2, 40, 65, 1),
    ("EL-SW1, EL-SW2", "Cisco C9200L-24T-4X", 2, "1", 1, 40, 60, 1),
    ("EL-SNS1, EL-SNS2", "Stormshield SN710", 2, "1", 1, 45, 70, 1),
    ("DM-SW1, DM-SW2", "Cisco C9200L-24T-4X", 2, "1", 1, 40, 60, 1),
    ("CL-SW1, CL-SW2", "Cisco C9500-16X", 2, "1", 2, 160, 260, 1),
    ("DL-SW1 à DL-SW4", "Cisco C9500-16X", 4, "1", 2, 160, 260, 1),
    ("NM-SW1, NM-SW2", "Cisco C9200L-24T-4X", 2, "1", 1, 40, 60, 1),
    ("WLC1, WLC2", "Cisco Catalyst 9800-L-F", 2, "1", 1, 55, 90, 1),
    ("Tiroirs optiques", "Rocades et adductions", 3, "1", 0, 0, 0, 1),
    ("DM-PVE1, DM-PVE2 (VM de la DMZ)", "Dell PowerEdge R360", 2, "2", 2, 120, 200, 1),
    ("NM-WITNESS, DM-WITNESS", "Dell PowerEdge R260 (entrée de gamme)", 2, "2", 2, 60, 110, 1),
    ("DT-SW1, DT-SW2", "Cisco C9300X-12Y", 2, "2", 2, 130, 220, 1),
    ("DT-PVE1, DT-PVE2 (VM AD, NPS, DHCP)", "Dell PowerEdge R660xs", 2, "2", 2, 240, 400, 1),
    ("NM-PVE1, NM-PVE2", "Dell PowerEdge R660xs", 2, "2", 2, 260, 420, 1),
    ("DT-BKP1", "Dell PowerEdge R760xd2", 1, "2", 2, 320, 480, 2),
]
ONDULEUR_U = 4 + 3  # SRT 6 kVA (4U) + pack batterie (3U), un par baie

# Locaux techniques : switch C9200L-48P-4X et appareils alimentés par le câble (PoE)
SWITCH_LT_W = 55            # W, switch 48 ports sans charge PoE
RENDEMENT_POE = 0.90
POE_TYPIQUE = {"wifi": 13.0, "camera": 6.0, "badge": 4.0, "telephone": 4.0}
BORNES_COUPEES = 30         # bornes des salles (pas celles des couloirs) coupées hors horaires
VENTILATEUR_W = 20

# Autonomies constructeur indicatives : (W, minutes) à mi-charge et pleine charge
AUTONOMIE = {
    "SRT 6 kVA": [(3000, 12.6), (6000, 3.9)],
    "SRT 6 kVA + 1 pack": [(3000, 37.0), (6000, 13.0)],
    "SMT 1500": [(500, 21.7), (1000, 5.7)],
}
CLIM_TAILLES = [3.5, 5.0, 7.1, 10.0]  # kW frigorifiques disponibles

# Prix (€ HT, posé) des éléments du lot qui ne sont pas déjà dans le chiffrage
PRIX = {
    "pack": 1400, "ventilation": 450, "tableau": 6000, "confinement": 1200, "sondes": 1200, "incendie": 1500,
    "maintenance_clim": 450, "batterie_srt": 1500, "batterie_smt": 250,
    "extinction": 8500, "plancher": 160, "batardeau": 1500, "cable_fuite": 900, "maintenance_extinction": 600,
}
AUTONOMIE_ARRET = 15       # min : l'arrêt ordonné doit être fini avant (marge sur l'autonomie avec un seul onduleur)


def autonomie(modele, w):
    (p1, t1), (p2, t2) = AUTONOMIE[modele]
    b = math.log(t1 / t2) / math.log(p2 / p1)
    return t1 * (p1 / max(w, 1)) ** b


# ---------------------------------------------------------------------------
# 1. Bilan de puissance
# ---------------------------------------------------------------------------
def bilan():
    lignes = []
    for rep, mod, n, baie, alim, wt, wm, u in SALLE:
        lignes.append(dict(reperes=rep, modele=mod, nombre=n, baie=baie, alimentations=alim, w_typ=wt, w_max=wm,
                           u=u * n, total_typ=wt * n, total_max=wm * n))
    baies = {}
    for b in ("1", "2"):
        ls = [l for l in lignes if l["baie"] == b]
        baies[b] = {"typ": sum(l["total_typ"] for l in ls), "max": sum(l["total_max"] for l in ls),
                    "u": sum(l["u"] for l in ls) + ONDULEUR_U}
    it_typ = sum(v["typ"] for v in baies.values())
    it_max = sum(v["max"] for v in baies.values())
    it_pointe = max(it_typ, FOISONNEMENT * it_max)
    # Équipements à une alimentation : le n°1 sur la voie A, le n°2 sur la voie B
    simple = sum(l["total_typ"] for l in lignes if l["alimentations"] == 1) / 2
    simple_max = FOISONNEMENT * sum(l["total_max"] for l in lignes if l["alimentations"] == 1) / 2
    double = it_typ - 2 * simple
    double_max = it_pointe - 2 * simple_max

    lt = []
    for b in PLAN["baies"]:
        poe_typ = b["wifi"] * POE_TYPIQUE["wifi"] + b["cameras"] * POE_TYPIQUE["camera"] + b["badges"] * POE_TYPIQUE["badge"] \
            + b["telephones"] * POE_TYPIQUE["telephone"]
        charge_typ = b["switchs_48p"] * SWITCH_LT_W + poe_typ / RENDEMENT_POE
        charge_max = b["switchs_48p"] * SWITCH_LT_W + b["poe_W"] / RENDEMENT_POE
        chaleur = b["switchs_48p"] * SWITCH_LT_W + poe_typ * (1 / RENDEMENT_POE - 1) + charge_typ * PERTES_ONDULEUR_LT
        debit = chaleur * 3600 / (1.2 * 1005 * 10)  # m³/h pour ΔT = 10 K
        ventile = b["salle"] == "L.TECH" or chaleur > 200 or b["surface_m2"] < 4
        lt.append(dict(local=b["local"], salle=b["salle"], surface=b["surface_m2"], switchs=b["switchs_48p"],
                       poe_typ=round(poe_typ), poe_max=b["poe_W"], charge_typ=round(charge_typ), charge_max=round(charge_max),
                       taux=round(100 * charge_max / 1000), autonomie=round(autonomie("SMT 1500", charge_max)),
                       chaleur=round(chaleur), debit=round(debit), ventilation="extracteur" if ventile else "grilles hautes/basses"))
    return lignes, baies, dict(it_typ=it_typ, it_max=it_max, it_pointe=round(it_pointe), simple=simple, simple_max=simple_max,
                               double=double, double_max=double_max), lt


# ---------------------------------------------------------------------------
# 2. Onduleurs, 3. Clim, 4. Énergie
# ---------------------------------------------------------------------------
def calculs():
    lignes, baies, s, lt = bilan()
    # Onduleurs de la salle : en marche normale chacun porte la moitié des équipements à 2 alimentations
    normal = s["double"] / 2 + s["simple"]
    degrade = s["double"] + s["simple"]               # l'autre onduleur est en panne
    degrade_pointe = s["double_max"] + s["simple_max"]
    auto_int = autonomie("SRT 6 kVA", degrade)
    pack = auto_int < AUTONOMIE_VISEE
    modele = "SRT 6 kVA + 1 pack" if pack else "SRT 6 kVA"
    ond = dict(capacite=6000, normal=round(normal), degrade=round(degrade), degrade_pointe=round(degrade_pointe),
               taux_normal=round(100 * normal / 6000), taux_degrade=round(100 * degrade_pointe / 6000),
               ok=normal <= MARGE_NORMALE * 6000 and degrade_pointe <= MARGE_SECOURS * 6000, autonomie_interne=round(auto_int, 1), pack=pack,
               autonomie_normal=round(autonomie(modele, normal)), autonomie_degrade=round(autonomie(modele, degrade)))
    # Climatisation
    pertes = s["it_typ"] * (1 / RENDEMENT_ONDULEUR - 1)
    pertes_pointe = s["it_pointe"] * (1 / RENDEMENT_ONDULEUR - 1)
    eclairage = SURFACE_SALLE * ECLAIRAGE_W_M2
    q_typ = (s["it_typ"] + pertes + 0.1 * eclairage) / 1000
    q_pointe = (s["it_pointe"] + pertes_pointe + eclairage + 100) / 1000
    taille = next(t for t in CLIM_TAILLES if t >= 1.15 * q_pointe)
    clim = dict(q_typ=round(q_typ, 2), q_pointe=round(q_pointe, 2), unite_kw=taille, taux=round(100 * q_typ / taille))
    # Énergie et PUE : situation usuelle vs proposée
    def salle_kw(eer, confinement):
        c = q_typ / eer * (1 - (GAIN_CONFINEMENT if confinement else 0))
        total = s["it_typ"] / 1000 + c + pertes / 1000 + 0.1 * eclairage / 1000
        return total, c
    usuel, c_usuel = salle_kw(EER["22 °C (usuel)"], False)
    propose, c_prop = salle_kw(EER["27 °C (proposé)"], True)
    pue_usuel = usuel / (s["it_typ"] / 1000)
    pue = propose / (s["it_typ"] / 1000)
    n_vent = sum(1 for l in lt if l["ventilation"] == "extracteur")
    lt_kw = sum(l["charge_typ"] for l in lt) * (1 + PERTES_ONDULEUR_LT) / 1000 + n_vent * VENTILATEUR_W / 1000
    eco_poe_kwh = BORNES_COUPEES * POE_TYPIQUE["wifi"] / RENDEMENT_POE * HEURES_COUPURE_POE * 52 / 1000
    kwh_usuel = (usuel + lt_kw) * 8760
    kwh = (propose + lt_kw) * 8760 - eco_poe_kwh
    energie = dict(it_kw=round(s["it_typ"] / 1000, 2), clim_kw=round(c_prop, 2), pertes_kw=round(pertes / 1000, 2),
                   salle_kw=round(propose, 2), lt_kw=round(lt_kw, 2), pue=round(pue, 2), pue_usuel=round(pue_usuel, 2),
                   kwh=round(kwh), kwh_usuel=round(kwh_usuel), cout=round(kwh * PRIX_KWH), cout_usuel=round(kwh_usuel * PRIX_KWH),
                   co2_t=round(kwh * CO2_KG_KWH / 1000, 1))
    gains = [
        ("Consigne de la salle à 27 °C au lieu de 22 °C (plage recommandée ASHRAE A1 : 18-27 °C)",
         (q_typ / EER["22 °C (usuel)"] - q_typ / EER["27 °C (proposé)"]) * 8760, 0),
        ("Allée froide confinée (obturateurs de U vides, rideaux aux extrémités)",
         q_typ / EER["27 °C (proposé)"] * GAIN_CONFINEMENT * 8760, PRIX["confinement"]),
        (f"Coupure programmée de {BORNES_COUPEES} bornes Wi-Fi des salles la nuit et le week-end ({HEURES_COUPURE_POE} h/semaine)",
         eco_poe_kwh, 0),
    ]
    gains = [dict(mesure=m, kwh=round(k), euros=round(k * PRIX_KWH), co2_kg=round(k * CO2_KG_KWH), cout=c,
                  retour=(f"{c / (k * PRIX_KWH):.1f} ans" if c else "immédiat")) for m, k, c in gains]
    # Pistes d'optimisation du chiffrage, vues côté énergie
    optim = [
        ("Cœur replié : suppression de DL-SW1 à DL-SW4 (variante étudiée, non retenue : CdC en 3 couches)", 4 * 160),
    ]
    optim = [dict(piste=p, w=w, kwh=round(w / 1000 * pue * 8760), euros=round(w / 1000 * pue * 8760 * PRIX_KWH)) for p, w in optim]
    return lignes, baies, s, lt, ond, clim, energie, gains, optim, n_vent


# ---------------------------------------------------------------------------
# 5. Finances
# ---------------------------------------------------------------------------
def finances(ond, n_vent, energie):
    ch = json.loads((ROOT / "chiffrage" / "estimation.json").read_text(encoding="utf-8"))
    # lignes du chiffrage d'origine (sans celles que ce script y ajoute, marquées « (point 14) »)
    deja = [l for l in ch["capex_lignes"] if l["categorie"] == "Énergie / locaux" and not l["note"].endswith("(point 14)")]
    nouveaux = []
    if ond["pack"]:
        nouveaux.append(("Salle serveur", "Pack batterie externe APC SRT192RMBP (1 par onduleur)", 2, PRIX["pack"],
                         f"Autonomie si un onduleur tombe : {ond['autonomie_interne']} min sans pack, {ond['autonomie_degrade']} min avec"))
    nouveaux += [
        ("Salle serveur + L.TECH", "Tableau électrique informatique (TD-INFO) et circuits dédiés", 1, PRIX["tableau"],
         "2 départs 32 A onduleurs, 2 départs clim, 6 départs 16 A L.TECH, protections différentielles"),
        ("Salle serveur", "Confinement d'allée froide (obturateurs, rideaux)", 1, PRIX["confinement"], "Green IT : -10 % sur la clim"),
        ("Salle serveur + L.TECH", "Sondes température/humidité et détection de fuite d'eau", 1, PRIX["sondes"],
         "Remontées dans LibreNMS ; fuite : salle au sous-sol"),
        ("Salle serveur", "Détection incendie raccordée au SSI + extincteurs CO2", 1, PRIX["incendie"], "Report d'alarme au SSI du bâtiment"),
        ("Salle serveur", "Extinction automatique par gaz inerte (IG-541) + détection précoce par aspiration (VESDA)", 1, PRIX["extinction"],
         "v2 (audit SYS-03) : un incendie la nuit ne détruit plus la salle. Gaz inerte : sans danger pour le matériel"),
        ("Salle serveur", "Plancher technique surélevé 30 cm, baies et onduleurs sur socles", round(SURFACE_SALLE), PRIX["plancher"],
         "v2 (SYS-03) : matériel hors d'eau en cas d'inondation du sous-sol (prix au m²)"),
        ("Salle serveur", "Batardeau amovible à la porte (60 cm) + clapet anti-retour sur l'évacuation des condensats", 1, PRIX["batardeau"],
         "v2 (SYS-03) : retarde l'entrée de l'eau par la circulation"),
        ("Salle serveur", "Câble de détection de fuite sous le plancher (centrale + 20 m)", 1, PRIX["cable_fuite"],
         "v2 (SYS-03) : alerte dès les premiers centimètres, avant que l'eau n'atteigne le matériel"),
        ("Locaux techniques", "Extracteur d'air avec thermostat", n_vent, PRIX["ventilation"], "Locaux les plus chargés ou les plus petits"),
    ]
    nouveaux = [dict(categorie="Énergie / locaux", schema=a, solution=b, quantite=q, pu_ht=p, total_ht=q * p, note=n) for a, b, q, p, n in nouveaux]
    capex = sum(l["total_ht"] for l in deja) + sum(l["total_ht"] for l in nouveaux)
    batteries = (2 * PRIX["batterie_srt"] * (2 if ond["pack"] else 1) + 6 * PRIX["batterie_smt"]) / 5
    opex = [
        ("Électricité du réseau", f"{num(energie['kwh'])} kWh/an × {PRIX_KWH:.2f} € (salle serveur, PUE {energie['pue']}, 6 locaux techniques)",
         energie["cout"]),
        ("Maintenance de la climatisation", "Contrat d'entretien, 2 unités", 2 * PRIX["maintenance_clim"]),
        ("Provision batteries d'onduleurs", "Remplacement tous les 5 ans, lissé par an", round(batteries)),
        ("Maintenance de l'extinction automatique", "Visite annuelle obligatoire (APSAD R13), contrôle des bouteilles", PRIX["maintenance_extinction"]),
    ]
    total_opex = sum(o[2] for o in opex)
    options = [
        ("Groupe électrogène dédié (20 kVA)", 18000, "Seulement si le campus n'en a pas : à demander au client. Sans groupe, la salle "
         "s'arrête proprement sur batterie (arrêt ordonné par NUT, paragraphe 3)"),
        ("Déplacer la salle serveur au RDC (hors zone inondable)", None, "Aucune salle de 25 m² libre hors des salles d'enseignement ; le sous-sol garde "
         "les rocades les plus courtes. Risque d'eau traité par le plancher, le batardeau et la détection"),
        ("Armoires de climatisation de précision (au lieu de 2 climatiseurs techniques)", 2 * 14000 - 12000,
         "Surcoût ; utile au-delà de ~10 kW"),
        ("Free-cooling (air extérieur)", None, "Non faisable : salle au sous-sol sans accès à l'air extérieur"),
    ]
    return dict(deja=deja, nouveaux=nouveaux, capex=capex, opex=opex, opex_total=total_opex, cout_5ans=capex + 5 * total_opex,
                options=options)


# ---------------------------------------------------------------------------
# Schémas
# ---------------------------------------------------------------------------
def boite(ax, x, y, w, h, titre, detail="", fc="white", ec=ENCRE, bold=True):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.08", fc=fc, ec=ec, lw=1.3))
    ax.text(x + w / 2, y + h / 2 + (0.13 if detail else 0), titre, ha="center", va="center", fontsize=7.6, weight="bold" if bold else "normal")
    if detail:
        ax.text(x + w / 2, y + h / 2 - 0.17, detail, ha="center", va="center", fontsize=6.4, color="#3A3833")


def fleche(ax, x1, y1, x2, y2, col="#3A3833", ls="-"):
    ax.annotate("", (x2, y2), (x1, y1), arrowprops=dict(arrowstyle="-|>", color=col, lw=1.2, ls=ls))


def schema_electrique(ond, clim):
    fig, ax = plt.subplots(figsize=(11.7, 7.6))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 8)
    ax.set_axis_off()
    ax.text(0, 7.85, "Alimentation électrique de l'infrastructure", fontsize=14, weight="bold", family="DejaVu Serif", va="top")
    ax.text(0, 7.45, "Chaque équipement critique est alimenté par deux voies indépendantes (A et B). La panne d'un onduleur "
                     "ou d'un circuit ne coupe aucun service.", fontsize=8, color="#3A3833", va="top")
    boite(ax, 4.6, 6.4, 2.8, 0.6, "Arrivée électrique du bâtiment", "TGBT existant", fc="#F6F4EF", ec="#8C8880")
    boite(ax, 4.3, 5.3, 3.4, 0.65, "Tableau informatique TD-INFO", "sous-sol, à côté de la salle serveur · nouveau", fc="#EAF0F8")
    fleche(ax, 6.0, 6.4, 6.0, 5.95)
    A, B = "#2C6E8C", "#8C682C"
    boite(ax, 1.0, 3.95, 2.6, 0.75, "Onduleur A", f"APC SRT 6 kVA{' + pack batterie' if ond['pack'] else ''}", ec=A)
    boite(ax, 4.7, 3.95, 2.6, 0.75, "Onduleur B", f"APC SRT 6 kVA{' + pack batterie' if ond['pack'] else ''}", ec=B)
    fleche(ax, 5.0, 5.3, 2.3, 4.7, A)
    fleche(ax, 6.0, 5.3, 6.0, 4.7, B)
    ax.text(2.9, 5.0, "départ 32 A", fontsize=6.5, color=A)
    ax.text(6.1, 5.0, "départ 32 A", fontsize=6.5, color=B)
    boite(ax, 8.4, 3.95, 3.2, 0.75, f"2 climatiseurs {clim['unite_kw']} kW", "1 en marche, 1 en secours, alternance", ec="#1D7A4E")
    fleche(ax, 7.0, 5.3, 9.6, 4.7, "#1D7A4E")
    ax.text(8.4, 5.0, "2 départs 16 A", fontsize=6.5, color="#1D7A4E")
    for i, (x, nom) in enumerate(((0.4, "Baie 1 · réseau et sécurité"), (4.1, "Baie 2 · serveurs"))):
        boite(ax, x, 2.35, 3.4, 0.8, nom, "PDU A (bleue) + PDU B (ocre), métrées", ec="#3A3833")
    for xb in (2.1, 5.8):
        fleche(ax, 2.3, 3.95, xb - 0.35, 3.15, A)
        fleche(ax, 6.0, 3.95, xb + 0.35, 3.15, B)
    boite(ax, 0.4, 0.95, 3.4, 0.9, "Équipements à 2 alimentations", "cœur, distribution, pare-feux FortiGate,\nserveurs : 1 alim sur A, 1 sur B",
          fc="white", ec="#3A3833", bold=True)
    boite(ax, 4.1, 0.95, 3.4, 0.9, "Équipements à 1 alimentation", "routeurs, switchs C9200L, Stormshield :\nle n°1 sur A, le n°2 sur B",
          fc="white", ec="#3A3833", bold=True)
    fleche(ax, 2.1, 2.35, 2.1, 1.85)
    fleche(ax, 5.8, 2.35, 5.8, 1.85)
    boite(ax, 8.4, 1.95, 3.2, 1.2, "6 locaux techniques", "1 départ 16 A chacun\n→ onduleur 1,5 kVA → switchs PoE+\n→ bornes, caméras, badgeuses, téléphones",
          ec="#5C2C8C")
    fleche(ax, 7.7, 5.45, 10.0, 3.15, "#5C2C8C")
    ax.text(8.9, 0.95, "Coupure secteur : bascule sur batterie\nsans interruption (onduleurs en ligne),\n"
                       f"{ond['autonomie_degrade']} min même si un onduleur est en panne.", fontsize=7, color="#3A3833", va="bottom")
    return fig


def schema_salle(clim):
    L, P = DIM_SALLE
    fig, ax = plt.subplots(figsize=(11.7, 7.6))
    ax.set_aspect("equal")
    ax.set_xlim(-0.6, L + 4.2)
    ax.set_ylim(P + 1.0, -1.2)
    ax.set_axis_off()
    ax.text(-0.6, -1.15, "Salle serveur : implantation et circulation de l'air", fontsize=14, weight="bold", family="DejaVu Serif", va="top")
    ax.text(-0.6, -0.72, f"Partie sud de la salle J05 (sous-sol), {L:.2f} × {P:.2f} m ≈ {SURFACE_SALLE:.0f} m². Vue de dessus.",
            fontsize=8, color="#3A3833", va="top")
    ax.add_patch(Rectangle((0, 0), L, P, fc="#FBFAF7", ec="#211F1C", lw=3))
    # cloison nouvelle (nord) en pointillé, porte à l'est
    ax.plot([0, L], [0, 0], color="white", lw=3)
    ax.plot([0, L], [0, 0], color="#211F1C", lw=2.2, ls=(0, (6, 3)))
    ax.text(L / 2, -0.12, "cloison nouvelle (reste de J05 au nord)", ha="center", va="bottom", fontsize=6.5, color="#6C6861")
    ax.plot([L, L], [2.35, 3.25], color="#FBFAF7", lw=4)
    ax.plot([L + 0.05, L + 0.05], [2.35, 3.25], color="#A85A07", lw=3)
    ax.text(L + 0.15, 2.8, "porte vers CIRC 02 · batardeau\nbadge B1 · caméra C3", fontsize=6.5, va="center")
    ax.add_patch(Rectangle((0.03, 0.03), L - 0.06, P - 0.06, fc="none", ec="#A85A07", lw=0.8, ls=":"))
    ax.text(L / 2, P + 0.25, "mur sud : local technique N-1-LT01 (passage des fibres)", ha="center", fontsize=6.5, color="#6C6861")
    # baies (faces avant vers le sud = allée froide)
    for i, nom in enumerate(("Baie 1\nréseau, sécurité", "Baie 2\nserveurs")):
        x = 2.0 + i * 0.8
        ax.add_patch(Rectangle((x, 0.9), 0.8, 1.0, fc="#EAF0F8", ec=ENCRE, lw=1.4))
        ax.text(x + 0.4, 1.4, nom, ha="center", va="center", fontsize=6.3, weight="bold", color=ENCRE)
    ax.add_patch(Rectangle((1.6, 1.9), 2.4, 1.2, fc="#2C6E8C22", ec="#2C6E8C", lw=1, ls="--"))
    ax.text(2.8, 2.55, "ALLÉE FROIDE (confinée)\nair à 24-27 °C devant les baies", ha="center", va="center", fontsize=6.6, color="#2C6E8C", weight="bold")
    ax.add_patch(Rectangle((1.6, 0.05), 2.4, 0.85, fc="#B3261E14", ec="#B3261E", lw=1, ls="--"))
    ax.text(2.8, 0.47, "allée chaude (arrière des baies)", ha="center", va="center", fontsize=6.3, color="#B3261E")
    # climatiseurs
    for k, y in enumerate((1.0, 2.7)):
        ax.add_patch(Rectangle((0.05, y), 0.55, 0.6, fc="#1D7A4E22", ec="#1D7A4E", lw=1.4))
        ax.text(0.33, y + 0.3, f"CLIM {k + 1}", ha="center", va="center", fontsize=6, weight="bold", color="#1D7A4E", rotation=90)
        ax.annotate("", (1.55, 2.5), (0.65, y + 0.3), arrowprops=dict(arrowstyle="-|>", color="#2C6E8C", lw=1.4))
    ax.annotate("", (0.65, 0.6), (1.55, 0.4), arrowprops=dict(arrowstyle="-|>", color="#B3261E", lw=1.4))
    ax.text(0.9, 0.2, "reprise d'air chaud", fontsize=6, color="#B3261E")
    # coffret TD-INFO, sondes, fuite, extincteur
    ax.add_patch(Rectangle((L - 0.5, 0.2), 0.4, 0.5, fc="#EAF0F8", ec=ENCRE))
    ax.text(L - 0.3, 0.45, "TD", ha="center", va="center", fontsize=6, weight="bold")
    for (x, y, t, c) in ((2.8, 3.05, "T/H", "#5C2C8C"), (1.3, 1.9, "T/H", "#5C2C8C"), (0.33, 3.5, "fuite", "#A85A07"),
                         (0.33, 0.85, "fuite", "#A85A07"), (L - 0.3, 3.55, "CO2", "#B3261E"), (L - 0.9, 0.45, "gaz", "#B3261E"),
                         (4.6, 1.5, "VESDA", "#B3261E")):
        ax.plot(x, y, marker="o", ms=6, mfc="white", mec=c, mew=1.6)
        ax.text(x + 0.12, y - 0.1, t, fontsize=5.8, color=c, weight="bold")
    # cotes
    ax.annotate("", (L, P + 0.6), (0, P + 0.6), arrowprops=dict(arrowstyle="<->", color="#6C6861", lw=0.8))
    ax.text(L / 2, P + 0.75, f"{L:.2f} m", ha="center", fontsize=7, color="#6C6861")
    ax.annotate("", (-0.35, P), (-0.35, 0), arrowprops=dict(arrowstyle="<->", color="#6C6861", lw=0.8))
    ax.text(-0.45, P / 2, f"{P:.2f} m", ha="right", va="center", fontsize=7, color="#6C6861", rotation=90)
    # légende
    lx = L + 0.6
    items = [("Baie 42U 800×1000 : onduleur et pack en bas, PDU A et B à l'arrière", ENCRE),
             (f"Climatiseur technique {clim['unite_kw']} kW (1 en marche, 1 en secours)", "#1D7A4E"),
             ("Air froid soufflé dans l'allée froide", "#2C6E8C"), ("Air chaud repris derrière les baies", "#B3261E"),
             ("T/H : sonde température/humidité (supervision)", "#5C2C8C"), ("fuite : détecteur de fuite d'eau au sol", "#A85A07"),
             ("CO2 : extincteur · gaz : bouteilles IG-541 · VESDA : détection", "#B3261E"), ("TD : tableau électrique informatique", "#3A3833"),
             ("pointillé ocre : plancher surélevé 30 cm · batardeau à la porte", "#A85A07")]
    ax.text(lx, 0.05, "LÉGENDE", fontsize=8, weight="bold")
    for k, (t, c) in enumerate(items):
        ax.add_patch(Rectangle((lx, 0.35 + k * 0.42), 0.22, 0.22, fc=c, ec="none", alpha=0.8))
        ax.text(lx + 0.35, 0.47 + k * 0.42, t, fontsize=6.6, va="center")
    ax.text(lx, 4.0, f"Chaleur à évacuer : {clim['q_typ']} kW (pointe {clim['q_pointe']} kW).\nUn seul climatiseur suffit ; "
                     "le second prend le relais\nen cas de panne ou d'entretien.", fontsize=7, va="top", color="#3A3833")
    return fig


def sauver(fig, nom):
    (OUT / "schemas").mkdir(parents=True, exist_ok=True)
    for ext in ("png", "svg", "pdf"):
        fig.savefig(OUT / "schemas" / f"{nom}.{ext}", dpi=170 if ext == "png" else None, bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------------------
# Document
# ---------------------------------------------------------------------------
CSS = (ROOT / "cablage" / "document.py").read_text(encoding="utf-8").split('CSS = """', 1)[1].split('"""', 1)[0]
e = html.escape
eur = lambda v: f"{v:,.0f} €".replace(",", " ")
num = lambda v: f"{v:,.0f}".replace(",", " ")


V1 = ROOT / "livrables" / "archives" / "v1_2026-11-15" / "energie_refroidissement" / "resume.json"


def encadre_version(s, en, fin):
    """Comparaison avec la version 1 archivée (avant l'audit)."""
    if not V1.exists():
        return ""
    v1 = json.loads(V1.read_text(encoding="utf-8"))
    lignes = [("Puissance de la salle (typique)", f"{v1['salle']['it_typ']} W", f"{s['it_typ']} W"),
              ("Consommation annuelle", f"{num(v1['energie']['kwh'])} kWh", f"{num(en['kwh'])} kWh"),
              ("Électricité par an", eur(v1['energie']['cout']), eur(en['cout'])),
              ("Investissement du lot", eur(v1['capex_lot']), eur(fin['capex']))]
    return ("<div class='note' style='border-left-color:#05893e'><b>Version 2, après l'audit du 15/11/2026.</b> La version 1 est archivée dans "
            "<code>livrables/archives/v1_2026-11-15/</code> ; le traitement de chaque constat est dans <code>livrables/audit/traitement_audit.pdf</code>. "
            "Changements : 12 serveurs physiques remplacés par 4 hyperviseurs et un témoin (SYS-02), 3 nœuds NM ramenés à 2 + témoin (SYS-01), "
            "contrôleurs Wi-Fi physiques (NET-01), plancher surélevé, batardeau, détection de fuite et extinction automatique au gaz (SYS-03), "
            "arrêt ordonné sur batterie par NUT.<table><tr><th></th><th class='n'>v1</th><th class='n'>v2</th></tr>"
            + "".join(f"<tr><td>{a}</td><td class='n'>{b}</td><td class='n'><b>{c}</b></td></tr>" for a, b, c in lignes) + "</table></div>")


def arret_ordonne(ond):
    """v2 : séquence d'arrêt sur batterie (audit, question Q13)."""
    return ("<h3>Arrêt ordonné sur batterie (NUT) <span style='color:#05893e'>v2</span></h3>"
            "<p>Il n'y a pas de groupe électrogène dédié. Une coupure longue doit donc finir par un <b>arrêt propre</b>, avant que les batteries "
            "soient vides : un hyperviseur coupé brutalement peut abîmer ses disques ou ses VM. Les cartes réseau des deux onduleurs (VLAN 900) "
            "sont lues par <b>NUT</b> (Network UPS Tools), dont le serveur tourne sur le témoin NM-WITNESS. Ce petit serveur physique s'éteint en "
            "dernier. Les hyperviseurs, le PBS et les témoins sont clients NUT.</p>"
            "<table><tr><th>Moment</th><th>Action</th></tr>"
            "<tr><td>T0 : coupure secteur</td><td>Les onduleurs basculent sur batterie sans interruption. Alerte (supervision, courriel, SMS d'astreinte).</td></tr>"
            "<tr><td>T0 + 5 min</td><td>Si le secteur n'est pas revenu (on ignore les microcoupures) : arrêt des VM non essentielles (supervision, VM applicatives de la DMZ).</td></tr>"
            "<tr><td>T0 + 8 min</td><td>Arrêt des VM d'infrastructure : DHCP, NPS, Teleport, journaux (après vidage de leurs files d'attente), puis des contrôleurs de domaine.</td></tr>"
            "<tr><td>T0 + 11 min</td><td>Arrêt des hyperviseurs (DT, DM, NM) et du serveur de sauvegarde, une fois leurs VM arrêtées.</td></tr>"
            f"<tr><td>T0 + 13 min</td><td>Arrêt de NM-WITNESS. Les onduleurs coupent leurs sorties serveurs. Les switchs et pare-feu restent alimentés jusqu'à "
            f"l'épuisement des batteries (≈ {ond['autonomie_degrade']} min avec un seul onduleur), car ils redémarrent sans risque.</td></tr>"
            "<tr><td>Retour du secteur</td><td>Les onduleurs ne rallument les serveurs que lorsque leurs batteries sont rechargées à 40 % (une seconde coupure ne doit pas "
            "les surprendre à vide). Le démarrage suit l'ordre inverse : témoins, hyperviseurs, puis les VM selon leur ordre de démarrage Proxmox.</td></tr></table>"
            f"<p class='sous'>L'arrêt est déclenché par l'autonomie restante annoncée par l'onduleur, pas seulement par l'heure. La séquence complète doit être "
            f"finie en moins de {AUTONOMIE_ARRET} min, même avec un seul onduleur ({ond['autonomie_degrade']} min d'autonomie). Elle est testée une fois par an.</p>")


def document(lignes, baies, s, lt, ond, clim, en, gains, optim, fin):
    date = datetime.date.today().strftime("%d/%m/%Y")
    H = [f"<!doctype html><html lang='fr'><head><meta charset='utf-8'><title>Énergie et refroidissement</title><style>{CSS}</style></head><body>",
         "<h1>Énergie et refroidissement</h1>",
         f"<p class='sous'>Site de Marseille · IUT Génie Télécom, Luminy · point 14 du cahier des charges · <b>version 2</b> · {date}<br>"
         "Alimentation électrique, onduleurs, climatisation des locaux techniques, consommation et coûts de l'infrastructure réseau.</p>",
         encadre_version(s, en, fin),
         "<div class='cles'>",
         f"<div class='cle'><b>{s['it_typ'] / 1000:.1f} kW</b>consommés par la salle serveur (typique)</div>",
         f"<div class='cle'><b>{ond['autonomie_degrade']} min</b>d'autonomie, même avec un onduleur en panne</div>",
         f"<div class='cle'><b>PUE {en['pue']}</b>contre {en['pue_usuel']} dans une salle classique</div>",
         f"<div class='cle'><b>{eur(en['cout'])}</b>d'électricité par an ({num(en['kwh'])} kWh)</div></div>",
         "<h2>1. Ce que demande le projet, et notre réponse</h2>",
         "<table><tr><th>Demande</th><th>Source</th><th>Réponse</th><th>Partie</th></tr>",
         "<tr><td>Locaux techniques : rack, alimentation électrique, climatisation, accès par badge</td><td>Consignes, traitement A (architecture physique)</td>"
         "<td>Salle serveur + 6 locaux, baies, onduleurs, clim/ventilation, badgeuses</td><td>2, 3, 4</td></tr>",
         "<tr><td>Bilan de puissance par baie</td><td>Roadmap, point 14</td><td>Bilan équipement par équipement, baie par baie et local par local</td><td>2</td></tr>",
         "<tr><td>Dimensionner les onduleurs</td><td>Roadmap, point 14</td><td>2 onduleurs en ligne 6 kVA (voies A/B) + 6 onduleurs 1,5 kVA, autonomie vérifiée</td><td>3</td></tr>",
         "<tr><td>Climatisation de la salle serveur</td><td>Roadmap, point 14</td><td>2 climatiseurs techniques (1 en secours), allée froide, ventilation des locaux</td><td>4</td></tr>",
         "<tr><td>Mesure de consommation, PUE et Green IT ; développement durable obligatoire</td><td>Roadmap ; consignes (DD, green IT)</td>"
         "<td>PDU et sondes supervisées, PUE calculé, 3 mesures d'économie chiffrées</td><td>5</td></tr>",
         "<tr><td>Data center : règles de base, PRA</td><td>Consignes, traitement C</td><td>Redondance électrique et frigorifique ; le PRA complet est traité au point 15</td><td>3, 4</td></tr>",
         "<tr><td>Chiffrage « carte blanche mais réaliste »</td><td>Consignes</td><td>Investissement, coûts annuels, économies, coût sur 5 ans, options écartées</td><td>6</td></tr></table>"]
    # 2. Bilan
    H += ["<h2>2. Bilan de puissance</h2>",
          f"<p>Puissances relevées sur les fiches constructeur (valeur typique et maximale). La pointe réaliste retient {int(FOISONNEMENT * 100)} % "
          "de la somme des maxima, car tous les équipements ne sont jamais au maximum en même temps.</p>",
          "<table><tr><th>Baie</th><th>Équipements</th><th>Modèle</th><th class='n'>Nb</th><th class='n'>Alim.</th><th class='n'>Typique</th><th class='n'>Max.</th></tr>"]
    for l in lignes:
        H.append(f"<tr><td>{l['baie']}</td><td>{e(l['reperes'])}</td><td>{e(l['modele'])}</td><td class='n'>{l['nombre']}</td>"
                 f"<td class='n'>{l['alimentations'] or '—'}</td><td class='n'>{num(l['total_typ'])} W</td><td class='n'>{num(l['total_max'])} W</td></tr>")
    H.append(f"<tr><td colspan='5'><b>Baie 1 (réseau, sécurité) : {baies['1']['u']}U occupés sur 42 · Baie 2 (serveurs) : {baies['2']['u']}U</b></td>"
             f"<td class='n'><b>{num(s['it_typ'])} W</b></td><td class='n'><b>{num(s['it_max'])} W</b></td></tr></table>"
             f"<p><b>Salle serveur : {s['it_typ'] / 1000:.2f} kW en fonctionnement normal, {s['it_pointe'] / 1000:.2f} kW en pointe réaliste.</b></p>")
    H.append("<h3>Locaux techniques</h3><table><tr><th>Local</th><th class='n'>Switchs</th><th class='n'>PoE typique</th><th class='n'>PoE max.</th>"
             "<th class='n'>Charge typique</th><th class='n'>Charge max.</th></tr>")
    for l in lt:
        H.append(f"<tr><td>{l['local']}</td><td class='n'>{l['switchs']}</td><td class='n'>{l['poe_typ']} W</td><td class='n'>{l['poe_max']} W</td>"
                 f"<td class='n'>{l['charge_typ']} W</td><td class='n'>{l['charge_max']} W</td></tr>")
    H.append("</table><p class='sous'>PoE : alimentation des bornes Wi-Fi, caméras, badgeuses et téléphones par leur câble réseau. "
             "« Max. » = puissance réservée par le switch (classe PoE) ; « typique » = consommation réelle moyenne.</p>")
    # 3. Onduleurs
    H += ["<h2 class='saut'>3. Alimentation électrique et onduleurs</h2>", "<img src='schemas/synoptique_electrique.png' alt='Alimentation électrique'>",
          "<h3>Salle serveur : deux onduleurs, deux voies</h3><ul>",
          "<li>Un tableau électrique informatique (TD-INFO) au sous-sol, avec deux départs 32 A, un par onduleur.</li>",
          "<li>Onduleurs <b>en ligne double conversion</b> (APC SRT 6 kVA / 6 kW) : les équipements ne voient jamais une coupure ni une perturbation du réseau.</li>",
          "<li>Équipements à deux alimentations : l'une sur l'onduleur A, l'autre sur l'onduleur B. Équipements à une seule alimentation (routeurs, switchs C9200L, "
          "Stormshield) : ils vont par paires, le n°1 sur A et le n°2 sur B, donc la panne d'une voie laisse toujours un équipement de la paire en service.</li></ul>",
          "<table><tr><th>Situation</th><th class='n'>Charge d'un onduleur</th><th class='n'>Taux</th><th class='n'>Autonomie</th></tr>",
          f"<tr><td>Normale (les deux onduleurs se partagent la charge)</td><td class='n'>{num(ond['normal'])} W</td><td class='n'>{ond['taux_normal']} %</td>"
          f"<td class='n'>{ond['autonomie_normal']} min</td></tr>",
          f"<tr><td>Un onduleur en panne : l'autre porte tout</td><td class='n'>{num(ond['degrade'])} W</td><td class='n'>{round(100 * ond['degrade'] / 6000)} %</td>"
          f"<td class='n'>{ond['autonomie_degrade']} min</td></tr>",
          f"<tr><td>Un onduleur en panne, en pointe</td><td class='n'>{num(ond['degrade_pointe'])} W</td><td class='n'>{ond['taux_degrade']} %</td><td class='n'>—</td></tr></table>",
          f"<p>{'✔' if ond['ok'] else '✘'} Règle de dimensionnement : moins de {int(MARGE_NORMALE * 100)} % en marche normale "
          f"({ond['taux_normal']} %) et moins de {int(MARGE_SECOURS * 100)} % pour un onduleur seul en pointe ({ond['taux_degrade']} %), "
          "situation rare qui cumule une panne et une pointe. Des onduleurs de 8 kVA (≈ 2 800 € de plus) ne sont donc pas nécessaires. "
          + (f"Sans batterie supplémentaire, l'autonomie avec un seul onduleur ne serait que de {ond['autonomie_interne']} min : "
             f"on ajoute <b>un pack batterie par onduleur</b> pour dépasser l'objectif de {AUTONOMIE_VISEE:.0f} min : la séquence d'arrêt "
             "ordonné (13 min, voir plus bas) doit tenir avec une marge, même si un onduleur est en panne." if ond["pack"] else "L'autonomie interne suffit.") + "</p>",
          "<h3>Locaux techniques : un onduleur 1,5 kVA chacun</h3><table><tr><th>Local</th><th class='n'>Charge max.</th><th class='n'>Taux</th><th class='n'>Autonomie</th></tr>"]
    for l in lt:
        H.append(f"<tr><td>{l['local']}</td><td class='n'>{l['charge_max']} W</td><td class='n'>{l['taux']} %</td><td class='n'>{l['autonomie']} min</td></tr>")
    H.append("</table><p>Chaque local a son départ 16 A dédié. Les bornes, les téléphones et les badgeuses restent alimentés pendant une coupure. "
             "Autonomies : courbes constructeur indicatives, à confirmer avec l'outil du fabricant.</p>")
    H.append(arret_ordonne(ond))
    # 4. Clim
    H += ["<h2 class='saut'>4. Climatisation et ventilation</h2>", "<img src='schemas/salle_serveur.png' alt='Implantation de la salle serveur'>",
          "<h3>Salle serveur</h3>",
          f"<p>Toute l'électricité consommée devient de la chaleur. À évacuer : <b>{clim['q_typ']} kW</b> en fonctionnement normal et "
          f"<b>{clim['q_pointe']} kW</b> en pointe (équipements, pertes des onduleurs, éclairage, une personne).</p>",
          f"<ul><li><b>2 climatiseurs techniques de {clim['unite_kw']} kW</b> (fonctionnement 24 h/24) : un seul suffit, à {clim['taux']} % de sa capacité en "
          "marche normale. Le second est en secours et ils alternent chaque semaine (usure égale, test permanent du secours).</li>",
          "<li><b>Allée froide</b> : les baies se font face côté froid ; obturateurs sur les U vides et rideaux aux extrémités, pour que l'air froid "
          "passe dans les équipements au lieu de contourner les baies.</li>",
          "<li><b>Consigne à 27 °C</b> à l'entrée des équipements, dans la plage recommandée (ASHRAE A1 : 18 à 27 °C) : la clim consomme moins.</li>",
          "<li>Sondes de température et d'humidité, détecteur de fuite d'eau (salle au sous-sol), alertes dans la supervision. "
          "L'humidité relative est tenue entre 40 et 60 % : plus sec, risque d'électricité statique ; plus humide, condensation pendant les épisodes "
          "pluvieux.</li></ul>"
          "<h3>Risques propres à une salle en sous-sol <span style='color:#05893e'>v2</span></h3>"
          "<p>La salle est au sous-sol, où une inondation (épisode méditerranéen, canalisation) est le premier risque, et un incendie de nuit le "
          "second (constat SYS-03 de l'audit). En v1, ces protections étaient des options écartées. Elles font maintenant partie du lot :</p><ul>"
          "<li><b>Eau</b> : plancher technique surélevé de 30 cm (baies, onduleurs et climatiseurs posés dessus) ; batardeau amovible à la porte ; "
          "clapet anti-retour sur l'évacuation des condensats ; câble de détection de fuite sous le plancher, relié à la supervision et à l'astreinte. "
          "Si l'eau monte quand même, l'alerte arrive tôt et l'arrêt ordonné protège les données.</li>"
          "<li><b>Feu</b> : détection précoce par aspiration (VESDA) et extinction automatique par gaz inerte (IG-541), sans danger pour le matériel. "
          "Report au SSI du bâtiment, temporisation et coupure de la climatisation avant le déclenchement, extincteurs CO2 en complément.</li>"
          "<li><b>Reprise</b> : si la salle est perdue malgré tout, les sauvegardes hors site permettent de reconstruire ailleurs (PRA, point 15).</li></ul>",
          "<h3>Locaux techniques</h3><table><tr><th>Local</th><th class='n'>Surface</th><th class='n'>Chaleur dégagée</th><th class='n'>Débit d'air nécessaire</th><th>Solution</th></tr>"]
    for l in lt:
        H.append(f"<tr><td>{l['local']}</td><td class='n'>{l['surface']:.0f} m²</td><td class='n'>{l['chaleur']} W</td><td class='n'>{l['debit']} m³/h</td>"
                 f"<td>{e(l['ventilation'])}</td></tr>")
    H.append("</table><p>Les locaux dégagent peu de chaleur (la puissance PoE est dissipée par les bornes et caméras, pas dans le local). "
             "Débit calculé pour 10 °C d'écart entre l'air entrant et sortant. Pas de climatisation nécessaire : une ventilation suffit.</p>")
    # 5. Green IT
    H += ["<h2>5. Mesure, PUE et Green IT</h2>",
          "<p><b>PUE</b> (efficacité énergétique) = électricité totale de la salle ÷ électricité des équipements informatiques. 1,0 serait parfait.</p>",
          "<table><tr><th>Salle serveur</th><th class='n'>Salle classique (22 °C)</th><th class='n'>Notre proposition</th></tr>",
          f"<tr><td>Équipements informatiques</td><td class='n'>{en['it_kw']} kW</td><td class='n'>{en['it_kw']} kW</td></tr>",
          f"<tr><td>Climatisation, pertes onduleurs, éclairage</td><td class='n'>{en['it_kw'] * (en['pue_usuel'] - 1):.2f} kW</td>"
          f"<td class='n'>{en['salle_kw'] - en['it_kw']:.2f} kW</td></tr>",
          f"<tr><td><b>PUE</b></td><td class='n'><b>{en['pue_usuel']}</b></td><td class='n'><b>{en['pue']}</b></td></tr></table>",
          "<p><b>Mesure en continu :</b> les PDU métrées (par prise), les onduleurs et les sondes sont interrogés par la supervision déjà prévue "
          "(LibreNMS et Grafana, zone NM). Le PUE réel est suivi chaque mois : la valeur ci-dessus est une estimation à confirmer.</p>",
          "<h3>Mesures d'économie retenues</h3><table><tr><th>Mesure</th><th class='n'>kWh/an</th><th class='n'>€/an</th><th class='n'>CO₂/an</th>"
          "<th class='n'>Coût</th><th class='n'>Retour</th></tr>"]
    for g in gains:
        H.append(f"<tr><td>{e(g['mesure'])}</td><td class='n'>{num(g['kwh'])}</td><td class='n'>{eur(g['euros'])}</td><td class='n'>{g['co2_kg']} kg</td>"
                 f"<td class='n'>{eur(g['cout']) if g['cout'] else '0 €'}</td><td class='n'>{g['retour']}</td></tr>")
    H.append(f"</table><p>Avec ces mesures, le réseau consomme <b>{num(en['kwh'])} kWh/an</b> au lieu de {num(en['kwh_usuel'])}, "
             f"soit <b>{eur(en['cout_usuel'] - en['cout'])} économisés chaque année</b>. Électricité française peu carbonée : "
             f"≈ {en['co2_t']} t de CO₂ par an.</p><h3>Pistes d'optimisation du chiffrage, côté énergie</h3>"
             "<table><tr><th>Piste</th><th class='n'>Puissance en moins</th><th class='n'>kWh/an</th><th class='n'>€/an</th></tr>")
    for o in optim:
        H.append(f"<tr><td>{e(o['piste'])}</td><td class='n'>{o['w']} W</td><td class='n'>{num(o['kwh'])}</td><td class='n'>{eur(o['euros'])}</td></tr>")
    H.append("</table><p class='sous'>Économies d'électricité en plus des économies d'achat déjà indiquées dans le chiffrage.</p>")
    # 6. Finances
    H += ["<h2 class='saut'>6. Finances du lot énergie et refroidissement</h2>", "<h3>Investissement (CAPEX, € HT)</h3>",
          "<table><tr><th>Élément</th><th>Où</th><th class='n'>Qté</th><th class='n'>Prix unitaire</th><th class='n'>Total</th><th>Remarque</th></tr>"]
    for l in fin["deja"] + fin["nouveaux"]:
        nv = " <b>(ajouté)</b>" if l in fin["nouveaux"] else ""
        H.append(f"<tr><td>{e(l['solution'])}{nv}</td><td>{e(l['schema'])}</td><td class='n'>{l['quantite']}</td><td class='n'>{eur(l['pu_ht'])}</td>"
                 f"<td class='n'>{eur(l['total_ht'])}</td><td class='chemin'>{e(l['note'])}</td></tr>")
    H.append(f"<tr><td colspan='4'><b>Total du lot</b></td><td class='n'><b>{eur(fin['capex'])}</b></td><td></td></tr></table>"
             "<h3>Coûts annuels (OPEX, € HT)</h3><table><tr><th>Poste</th><th>Détail</th><th class='n'>Par an</th></tr>")
    for a, b, c in fin["opex"]:
        H.append(f"<tr><td>{e(a)}</td><td class='chemin'>{e(b)}</td><td class='n'>{eur(c)}</td></tr>")
    H.append(f"<tr><td colspan='2'><b>Total par an</b></td><td class='n'><b>{eur(fin['opex_total'])}</b></td></tr></table>"
             f"<p><b>Coût du lot sur 5 ans : {eur(fin['cout_5ans'])}</b> (investissement + 5 années de fonctionnement). "
             "Ces montants sont intégrés au chiffrage global du projet (<code>chiffrage/estimation_infra.md</code>).</p>"
             "<h3>Options étudiées et écartées</h3><table><tr><th>Option</th><th class='n'>Coût</th><th>Pourquoi</th></tr>")
    for a, c, p in fin["options"]:
        H.append(f"<tr><td>{e(a)}</td><td class='n'>{eur(c) if c else '—'}</td><td>{e(p)}</td></tr>")
    H.append("</table><h2>7. Hypothèses et points à valider avec le client</h2><ul>"
             "<li>Existence d'un groupe électrogène sur le campus et puissance disponible au TGBT du bâtiment.</li>"
             "<li>Emplacement des unités extérieures des climatiseurs (cour ou façade la plus proche du sous-sol) et passage des liaisons.</li>"
             "<li>Puissances des équipements : fiches constructeur, à affiner avec les configurateurs ; autonomies indicatives.</li>"
             f"<li>Électricité à {PRIX_KWH:.2f} € HT/kWh, comme dans le chiffrage ; facteur carbone ≈ {CO2_KG_KWH * 1000:.0f} g CO₂/kWh.</li>"
             "<li>Le plan de reprise d'activité (PRA) relève du point 15. L'étude de l'extinction automatique (volume de la salle, étanchéité, "
             "évent de surpression) est à confier à un installateur certifié APSAD.</li>"
             "<li>Cote de crue et historique des remontées d'eau du sous-sol : à demander aux services techniques du campus.</li></ul></body></html>")
    page = OUT / "energie_refroidissement.html"
    page.write_text("\n".join(H), encoding="utf-8")
    chrome = shutil.which("google-chrome") or shutil.which("chromium")
    if chrome:
        with tempfile.TemporaryDirectory() as prof:
            subprocess.run([chrome, "--headless=new", "--no-sandbox", "--disable-gpu", f"--user-data-dir={prof}", "--no-pdf-header-footer",
                            f"--print-to-pdf={OUT / 'energie_refroidissement.pdf'}", page.as_uri()], check=True, capture_output=True, timeout=180)


def main():
    lignes, baies, s, lt, ond, clim, en, gains, optim, n_vent = calculs()
    fin = finances(ond, n_vent, en)
    OUT.mkdir(parents=True, exist_ok=True)
    sauver(schema_electrique(ond, clim), "synoptique_electrique")
    sauver(schema_salle(clim), "salle_serveur")
    with open(OUT / "bilan_puissance.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(lignes[0].keys()))
        w.writeheader()
        w.writerows(lignes)
    resume = dict(salle=s, baies=baies, locaux=lt, onduleurs=ond, clim=clim, energie=en, gains=gains, optimisations=optim,
                  capex_nouveaux=fin["nouveaux"], capex_lot=fin["capex"],
                  opex=[dict(poste=a, detail=b, montant=c) for a, b, c in fin["opex"]], opex_total=fin["opex_total"], cout_5ans=fin["cout_5ans"])
    (OUT / "resume.json").write_text(json.dumps(resume, ensure_ascii=False, indent=1), encoding="utf-8")
    document(lignes, baies, s, lt, ond, clim, en, gains, optim, fin)
    readme = [
        "# Énergie et refroidissement (point 14)", "",
        "Document principal : **[energie_refroidissement.pdf](energie_refroidissement.pdf)**. Tout est calculé par `energie/energie.py` "
        "à partir du chiffrage et du plan de câblage (`python3 energie/energie.py && python3 chiffrage/estimation.py`).", "",
        "| | |", "|---|---|",
        f"| Salle serveur | {s['it_typ'] / 1000:.2f} kW typique, {s['it_pointe'] / 1000:.2f} kW en pointe, 2 baies 42U |",
        f"| Onduleurs | 2 × APC SRT 6 kVA en ligne (voies A et B){' + 1 pack batterie chacun' if ond['pack'] else ''} : {ond['autonomie_degrade']} min "
        f"même avec un onduleur en panne · 6 × 1,5 kVA dans les locaux techniques |",
        f"| Climatisation | 2 climatiseurs techniques {clim['unite_kw']} kW (1 en secours), allée froide, consigne 27 °C · ventilation des locaux techniques |",
        f"| Efficacité | PUE {en['pue']} (contre {en['pue_usuel']} pour une salle classique) · {num(en['kwh'])} kWh/an · ≈ {en['co2_t']} t CO₂/an |",
        f"| Finances | Investissement {eur(fin['capex'])} HT · {eur(fin['opex_total'])} HT/an · {eur(fin['cout_5ans'])} HT sur 5 ans |", "",
        "Fichiers : `energie_refroidissement.pdf` (et `.html`), `schemas/` (alimentation électrique, plan de la salle serveur), "
        "`bilan_puissance.csv`, `resume.json` (repris par le chiffrage).", "",
        "**Version 2 (après l'audit du 15/11/2026)** : serveurs virtualisés (12 serveurs physiques → 4 hyperviseurs + témoin), contrôleurs Wi-Fi "
        "physiques, plancher surélevé, batardeau, câble de détection de fuite et extinction automatique au gaz intégrés au lot (SYS-03), "
        "arrêt ordonné sur batterie par NUT. Le groupe électrogène reste une option à valider avec le campus. "
        "La v1 est archivée dans `livrables/archives/v1_2026-11-15/energie_refroidissement/` ; le traitement de l'audit est dans `livrables/audit/`.", "",
        "Historique : la toute première version (Gemini) est dans git (commit 1fbc1c1).", ""]
    (OUT / "README.md").write_text("\n".join(readme), encoding="utf-8")
    print(f"Salle : {s['it_typ']} W typ., {s['it_pointe']} W pointe | onduleur seul {ond['degrade_pointe']} W ({ond['taux_degrade']} %), "
          f"autonomie {ond['autonomie_degrade']} min, pack={ond['pack']} | clim {clim['q_typ']}/{clim['q_pointe']} kW -> 2×{clim['unite_kw']} kW")
    print(f"PUE {en['pue']} (usuel {en['pue_usuel']}) | {en['kwh']} kWh/an = {en['cout']} € | CAPEX lot {fin['capex']} € | "
          f"OPEX {fin['opex_total']} €/an | 5 ans {fin['cout_5ans']} €")


if __name__ == "__main__":
    main()
