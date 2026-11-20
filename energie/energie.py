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

Version 2.1 (20/11/2026) : étude BET de chaque local (energie/bet.py -> bet_locaux_techniques.pdf, bet_dissipation.csv),
groupe électrogène et inverseur de source (le site n'en a pas), pertes réelles des onduleurs, ventilation des L.TECH recalculée ;
enregistreur vidéo VS-NVR1 (lot sûreté) dans la baie 2 ; contrôle d'accès sorti du lot énergie (catégorie « Sûreté » du chiffrage) ;
contrats de maintenance 24 h/24 7 j/7 en 4 h des onduleurs et des climatiseurs ; charte commune (commun/charte.py).
Les lignes du chiffrage reprises dans le lot sont lues dans chiffrage/estimation.py (et non dans estimation.json, écrit après) :
un seul passage suffit.
Ordre : python3 cablage/plan_cablage.py (si besoin) ; python3 energie/energie.py (appelle bet.py) ; python3 chiffrage/estimation.py.
"""
import csv
import html
import importlib.util
import json
import math
import sys
from pathlib import Path

import matplotlib

import bet  # BET des locaux techniques et groupe électrogène (v2.1), même dossier

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Rectangle  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from commun import charte as CH  # noqa: E402

OUT = ROOT / "livrables" / "energie_refroidissement"
PLAN = json.loads((ROOT / "livrables" / "plan_cablage" / "resume.json").read_text(encoding="utf-8"))
BORNES = json.loads((ROOT / "livrables" / "plan_cablage" / "wifi" / "bornes.json").read_text(encoding="utf-8"))["bornes"]
PRISES = list(csv.DictReader((ROOT / "livrables" / "plan_cablage" / "prises.csv").open(encoding="utf-8")))
REF = "RLI-ETU-002"
ENCRE = CH.ENCRE
VOIE_A, VOIE_B = CH.EMERAUDE_FONCE, CH.ALERTE        # voies électriques A et B (PDU, onduleurs)
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8, "svg.fonttype": "none", "svg.hashsalt": "rudylink", "text.color": CH.CORPS})
META = {"png": {}, "svg": {"Date": None}, "pdf": {"CreationDate": None, "ModDate": None}}

# ---------------------------------------------------------------------------
# Hypothèses (toutes modifiables ici)
# ---------------------------------------------------------------------------
PRIX_KWH = 0.20            # € HT, même valeur que le chiffrage
CO2_KG_KWH = 0.052         # kg CO2e/kWh, électricité France (ordre de grandeur ADEME)
FOISONNEMENT = 0.80        # pointe réaliste = 80 % de la somme des maxima constructeur
# Pertes des onduleurs : bet.pertes_srt (en ligne, 100 W + 3 %) et bet.pertes_smt (line-interactive, 12 W + 2 %).
# v2 : rendement fixe de 95 % (SRT) et 4 % de pertes (SMT), trop optimiste à faible charge.
EER = {"22 °C (usuel)": 3.0, "27 °C (proposé)": 3.4}  # efficacité de la clim selon la consigne
GAIN_CONFINEMENT = 0.10    # obturateurs + rideaux d'allée froide : -10 % sur la clim
SURFACE_SALLE = 25.0       # m² (partie sud de J05, plan de câblage)
DIM_SALLE = (6.35, 3.94)   # m
ECLAIRAGE_W_M2 = 8.0
HEURES_COUPURE_POE = 103   # h/semaine bornes coupées : 20h-7h en semaine + week-end
MARGE_NORMALE = 0.80       # charge maximale d'un onduleur en marche normale
MARGE_SECOURS = 0.90       # charge maximale d'un onduleur seul (l'autre en panne), en pointe
AUTONOMIE_VISEE = 20.0     # min, si un des deux onduleurs est en panne : attente du groupe (3 min) + arrêt ordonné NUT (11 min) + marge
                           # et batteries en fin de vie (v2.1 ; v2 : arrêt de 13 min sans groupe ; v1 : 10 min)

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
    ("VS-NVR1 (lot sûreté)", "Enregistreur vidéo 2U, 8 × 8 To RAID 6", 1, "2", 2, 80, 150, 2),  # v2.1 : enregistreur physique (D3)
    ("PDU-1A, PDU-1B", "PDU métrée et managée 16 A (électronique)", 2, "1", 1, 8, 10, 0),  # v2.1 : ajoutées au bilan
    ("PDU-2A, PDU-2B", "PDU métrée et managée 16 A (électronique)", 2, "2", 1, 8, 10, 0),
]
ONDULEUR_U = 4 + 3  # SRT 6 kVA (4U) + pack batterie (3U), un par baie

# Locaux techniques : switch C9200L-48P-4X et appareils alimentés par le câble (PoE)
SWITCH_LT_W = 55            # W, switch 48 ports sans charge PoE (typique)
SWITCH_LT_W_MAX = 65        # W, idem au maximum (ventilateurs à fond, tous les ports actifs) : v2.1
RENDEMENT_POE = 0.90
POE_TYPIQUE = {"wifi": 13.0, "camera": 6.0, "badge": 4.0, "telephone": 4.0}
BORNES_COUPEES = sum(b["motif"] == "capacité" for b in BORNES)  # v2.1 : bornes « capacité » des salles (étude Wi-Fi) ; v2 : 30 écrit en dur

# Autonomies constructeur indicatives : (W, minutes) à mi-charge et pleine charge
AUTONOMIE = {
    "SRT 6 kVA": [(3000, 12.6), (6000, 3.9)],
    "SRT 6 kVA + 1 pack": [(3000, 37.0), (6000, 13.0)],
    "SMT 1500": [(500, 21.7), (1000, 5.7)],
}
CLIM_TAILLES = [3.5, 5.0, 7.1, 10.0]  # kW frigorifiques disponibles

# Prix (€ HT, posé) des éléments du lot qui ne sont pas déjà dans le chiffrage
PRIX = {
    "pack": 1400, "ventilation": 450, "tableau": 6800, "confinement": 1200, "sondes": 1200, "incendie": 1500,
    "maintenance_clim": 450, "batterie_srt": 1500, "batterie_smt": 250,
    "extinction": 8500, "plancher": 160, "batardeau": 1500, "cable_fuite": 900, "maintenance_extinction": 600,
    # v2.1 : groupe électrogène (ordres de grandeur distributeurs et installateurs, à confirmer par devis ; le groupe : bet.GE_GAMME)
    "inverseur": 3500, "ge_genie_civil": 4500, "ge_raccordement": 4000, "ge_mise_en_service": 2500,
    "ge_maintenance": 1100, "ge_banc": 700, "ge_analyse_gazole": 80,
    # v2.1 : corrections du BET
    "split_lt": 3200, "maintenance_split": 150, "coffret_lt": 350,
    # v2.1 : rétablissement en 4 h, 24 h/24 7 j/7, des onduleurs et des climatiseurs de la salle (décision D4)
    "astreinte_clim_4h": 1200, "contrat_srt_4h": 650,
}
AUTONOMIE_ARRET = 15       # min : l'arrêt ordonné doit être fini avant (marge sur l'autonomie avec un seul onduleur)
DUREE_BATTERIE_SMT = 4     # ans : batteries des L.TECH, locaux à 28-33 °C l'été (v2 : 5 ans)
# Valeurs publiées en v2 (15/11/2026, commit 7e1db0b), pour l'encadré « v2 → v2.1 »
V2_REF = dict(it_typ=3460, pue=1.34, kwh=53510, cout=10702, capex_lot=71900, opex_total=13702, cout_5ans=140410, autonomie_degrade=33)
ESTIMATION = ROOT / "chiffrage" / "estimation.py"


def fr(v, d=1):
    """Nombre au format français pour le HTML (virgule, insécable des milliers)."""
    return CH.nombre(v, d)


def md(v, d=0):
    """Nombre pour le Markdown du README : virgule décimale, espace ordinaire."""
    return f"{v:,.{d}f}".replace(",", " ").replace(".", ",")


def lignes_chiffrage():
    """Lignes CAPEX de chiffrage/estimation.py (module chargé par son chemin), au format de estimation.json."""
    spec = importlib.util.spec_from_file_location("estimation_chiffrage", ESTIMATION)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return [dict(categorie=c, schema=s, solution=so, quantite=q, pu_ht=pu, total_ht=q * pu, note=n) for c, s, so, q, pu, n in mod.CAPEX]


def repere_salle_serveur(t):
    """Repère de la caméra ou de la badgeuse de la salle serveur dans prises.csv, et circulation de la porte."""
    p = next((p for p in PRISES if p["salle"] == "SALLE SERVEUR" and p["type"] == t), None)
    return (p["repere"], p["passage"].split(" → ")[0]) if p else ("", "")


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
        # v2.1 : inventaire, dissipation et ventilation calculés par le BET (energie/bet.py)
        th = bet.local_technique(b, SWITCH_LT_W, SWITCH_LT_W_MAX, RENDEMENT_POE)
        poe_typ = sum(b[k] * t for k, _, t, _ in bet.POE_APPAREILS)
        lt.append(dict(local=b["local"], salle=b["salle"], surface=b["surface_m2"], switchs=b["switchs_48p"], baie=b["baie"],
                       poe_typ=round(poe_typ), poe_max=b["poe_W"], charge_typ=round(th["charge_typ"]), charge_max=round(th["charge_max"]),
                       taux=round(100 * th["charge_max"] / 1000), autonomie=round(autonomie("SMT 1500", th["charge_max"])),
                       chaleur=round(th["dissipation_typ"]), chaleur_pointe=round(th["p_dim"]), debit=round(th["debit_10k"]),
                       ventilation=th["solution_libelle"], ventilation_v2=th["v2_court"], t_ete=round(th["t_ete"], 1), bet=th))
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
    # Climatisation (v2.1 : pertes réelles des onduleurs, auxiliaires de sécurité et tableau comptés, bet.charge_salle)
    cs = bet.charge_salle(s["it_typ"], s["it_pointe"])
    pertes = cs["pertes_typ"]
    q_typ = cs["q_typ"] / 1000
    q_pointe = cs["q_pointe"] / 1000
    taille = next(t for t in CLIM_TAILLES if t * bet.SHR_CLIM >= 1.15 * q_pointe)  # puissance sensible d'une unité ≥ pointe + 15 %
    clim = dict(q_typ=round(q_typ, 2), q_pointe=round(q_pointe, 2), unite_kw=taille, taux=round(100 * q_typ / taille))
    # Énergie et PUE : situation usuelle vs proposée. Tout ce qui chauffe la salle (q_typ) + la clim + les auxiliaires du groupe électrogène
    def salle_kw(eer, confinement):
        c = q_typ / eer * (1 - (GAIN_CONFINEMENT if confinement else 0))
        total = q_typ + c + bet.GE_AUX_W / 1000
        return total, c
    usuel, c_usuel = salle_kw(EER["22 °C (usuel)"], False)
    propose, c_prop = salle_kw(EER["27 °C (proposé)"], True)
    pue_usuel = usuel / (s["it_typ"] / 1000)
    pue = propose / (s["it_typ"] / 1000)
    n_vent = sum(1 for l in lt if l["bet"]["solution"][0] == "extracteur")
    lt_kw = sum(l["bet"]["charge_typ"] + l["bet"]["pertes_ond_typ"] + l["bet"]["elec_vent_moy"] for l in lt) / 1000
    eco_poe_kwh = BORNES_COUPEES * POE_TYPIQUE["wifi"] / RENDEMENT_POE * HEURES_COUPURE_POE * 52 / 1000
    kwh_usuel = (usuel + lt_kw) * 8760
    kwh = (propose + lt_kw) * 8760 - eco_poe_kwh
    energie = dict(it_kw=round(s["it_typ"] / 1000, 2), clim_kw=round(c_prop, 2), pertes_kw=round(pertes / 1000, 2),
                   aux_kw=round((cs["aux"] + cs["td"] + 0.1 * cs["eclairage"]) / 1000, 2), ge_aux_kw=round(bet.GE_AUX_W / 1000, 2),
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
                  retour=(f"{fr(c / (k * PRIX_KWH))} ans" if c else "immédiat")) for m, k, c in gains]
    # Pistes d'optimisation du chiffrage, vues côté énergie
    optim = [
        ("Cœur replié : suppression de DL-SW1 à DL-SW4 (variante étudiée, non retenue : CdC en 3 couches)", 4 * 160),
    ]
    optim = [dict(piste=p, w=w, kwh=round(w / 1000 * pue * 8760), euros=round(w / 1000 * pue * 8760 * PRIX_KWH)) for p, w in optim]
    return lignes, baies, s, lt, ond, clim, energie, gains, optim, n_vent


# ---------------------------------------------------------------------------
# 5. Finances
# ---------------------------------------------------------------------------
def finances(ond, lt, energie, ge):
    # Lignes du chiffrage d'origine (sans celles que ce script y ajoute, marquées « (point 14) »). v2.1 : le contrôle d'accès est passé
    # dans la catégorie « Sûreté » (lot 4) et sort donc du lot énergie ; seule la catégorie « Énergie / locaux » est reprise.
    deja = [l for l in lignes_chiffrage() if l["categorie"] == "Énergie / locaux" and not l["note"].endswith("(point 14)")]
    n_vent = sum(1 for l in lt if l["bet"]["solution"][0] == "extracteur")
    nouveaux = []
    if ond["pack"]:
        nouveaux.append(("Salle serveur", "Pack batterie externe APC SRT192RMBP (1 par onduleur)", 2, PRIX["pack"],
                         f"Autonomie si un onduleur tombe : {md(ond['autonomie_interne'], 1)} min sans pack, {ond['autonomie_degrade']} min avec"))
    nouveaux += [
        ("Salle serveur + L.TECH", "Tableau électrique informatique (TD-INFO) et circuits dédiés", 1, PRIX["tableau"],
         "2 départs 32 A onduleurs (différentiel type B), 2 départs 20 A clim (type F), 6 départs 20 A L.TECH, éclairage, prises, auxiliaires. "
         "v2.1 : différentiels adaptés (BET)"),
        ("Salle serveur", "Confinement d'allée froide (obturateurs, rideaux)", 1, PRIX["confinement"], "Green IT : −10 % sur la clim"),
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
        ("Locaux techniques", "Extracteur d'air de gaine avec thermostat (150 ou 300 m³/h)", n_vent, PRIX["ventilation"],
         "v2.1 : débit vérifié pour l'été par le BET (" + ", ".join(f"{l['local']} {l['bet']['solution'][1]} m³/h" for l in lt
                                                               if l["bet"]["solution"][0] == "extracteur") + ")"),
    ]
    n_split = sum(1 for l in lt if l["bet"]["solution"][0] == "split")
    if n_split:
        nouveaux.append(("Locaux techniques", f"Mini-split {bet.fr(bet.SPLIT_KW)} kW froid (unité extérieure en toiture-terrasse)", n_split,
                         PRIX["split_lt"], "v2.1 (BET) : " + ", ".join(l["local"] for l in lt if l["bet"]["solution"][0] == "split")
                         + " trop chaud en été sous la toiture, même avec un extracteur"))
    nouveaux.append(("Locaux techniques", "Coffret électrique de L.TECH (différentiels 30 mA type A SI et F, prise détrompée de l'onduleur)", len(lt),
                     PRIX["coffret_lt"], "v2.1 (BET) : protections adaptées aux onduleurs et aux ventilateurs"))
    nouveaux = [dict(categorie="Énergie / locaux", schema=a, solution=b, quantite=q, pu_ht=p, total_ht=q * p, note=n) for a, b, q, p, n in nouveaux]
    # v2.1 : groupe électrogène (le client confirme qu'il n'y en a pas sur le site)
    lignes_ge = [
        ("Extérieur, façade est", f"Groupe électrogène diesel {ge['esp']} kVA ESP / {ge['prp']} kVA PRP, capoté insonorisé, cuve double paroi "
         f"{ge['cuve']} l, démarrage automatique", 1, ge["prix"],
         "v2.1 : le site n'a pas de groupe. Groupe 30 kVA capoté : 15 à 20 k€ HT fourni chez les distributeurs (ordre de grandeur)"),
        ("TD-INFO", "Inverseur de source automatique 4P 63 A (NF EN 60947-6-1), coffret, reports d'état", 1, PRIX["inverseur"],
         "v2.1 : bascule réseau / groupe en tête du tableau informatique. Appareil ≈ 1,5 à 2 k€, plus coffret, pose et mise en service"),
        ("Extérieur, façade est", "Génie civil : dalle béton armé ≈ 3 × 2 m, fourreaux, clôture et portillon", 1, PRIX["ge_genie_civil"],
         "v2.1 : ordre de grandeur d'entreprise de génie civil"),
        ("GE → TD-INFO, TGBT", f"Raccordement : câble 5G{ge['cable_section']:g} mm² (≈ {ge['cable_L']:.0f} m) en fourreau, câble de commande, "
         "départ 4P 63 A au TGBT, circuit des auxiliaires du groupe", 1, PRIX["ge_raccordement"], "v2.1 : ≈ 40 €/m posé pour le câble de puissance, plus l'appareillage"),
        ("Groupe électrogène", "Transport, levage, mise en service, essai de réception sur banc de charge (4 h), premier plein, formation", 1,
         PRIX["ge_mise_en_service"], "v2.1 : forfait installateur"),
    ]
    nouveaux += [dict(categorie="Énergie / secours", schema=a, solution=b, quantite=q, pu_ht=p, total_ht=q * p, note=n, ge=True) for a, b, q, p, n in lignes_ge]
    capex = sum(l["total_ht"] for l in deja) + sum(l["total_ht"] for l in nouveaux)
    batteries = 2 * PRIX["batterie_srt"] * (2 if ond["pack"] else 1) / 5 + len(lt) * PRIX["batterie_smt"] / DUREE_BATTERIE_SMT
    opex = [
        ("Électricité du réseau", f"{md(energie['kwh'])} kWh/an × {md(PRIX_KWH, 2)} € (salle serveur, PUE {md(energie['pue'], 2)}, 6 locaux techniques)",
         energie["cout"]),
        ("Maintenance de la climatisation", "v2.1 : 2 unités, 2 visites par an, dépannage 24 h/24 7 j/7 avec rétablissement en 4 h "
         f"(astreinte {md(PRIX['astreinte_clim_4h'])} €)", 2 * PRIX["maintenance_clim"] + PRIX["astreinte_clim_4h"]),
        ("Maintenance des onduleurs de la salle", f"v2.1 : 2 APC SRT 6 kVA, contrat 24 h/24 7 j/7, intervention sur site en 4 h, une visite "
         f"préventive par an ({md(PRIX['contrat_srt_4h'])} € par onduleur)", 2 * PRIX["contrat_srt_4h"]),
        ("Provision batteries d'onduleurs", f"Remplacement tous les 5 ans (salle) et tous les {DUREE_BATTERIE_SMT} ans (L.TECH, v2.1), lissé par an",
         round(batteries)),
        ("Maintenance de l'extinction automatique", "Visite annuelle obligatoire (APSAD R13), contrôle des bouteilles", PRIX["maintenance_extinction"]),
        ("Maintenance du groupe électrogène et de l'inverseur", "v2.1 : contrat de 2 visites par an (vidange, filtres, liquide, batterie de démarrage, "
         "contrôle de l'inverseur)", PRIX["ge_maintenance"]),
        ("Essai annuel du groupe sur banc de charge", "v2.1 : location du banc et technicien, 2 h à 75 % de la PRP", PRIX["ge_banc"]),
        ("Gazole du groupe électrogène", f"v2.1 : {ge['litres_an']:.0f} l/an × {md(bet.PRIX_GAZOLE, 2)} € (essais mensuels, banc, coupures) "
         "+ analyse et traitement du gazole", round(ge["litres_an"] * bet.PRIX_GAZOLE + PRIX["ge_analyse_gazole"])),
    ]
    if n_split:
        opex.append(("Maintenance du mini-split des L.TECH", "v2.1 : visite annuelle (filtres, contrôle d'étanchéité)", n_split * PRIX["maintenance_split"]))
    total_opex = sum(o[2] for o in opex)
    options = [
        ("Groupe électrogène en toiture-terrasse ou dans le parking du sous-sol", None, "v2.1 : écartés (structure et livraison du gazole en toiture ; "
         "local coupe-feu, air et échappement dans le parking). Le groupe retenu est à l'extérieur, façade est (étude BET)"),
        ("Climatiser tous les locaux techniques", (len(lt) - n_split) * PRIX["split_lt"], "Inutile : grilles ou extracteur suffisent hors de "
         "l'étage sous toiture (étude BET, section 3)"),
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
    ax.add_patch(Rectangle((x, y), w, h, fc=fc, ec=ec, lw=1.3))
    ax.text(x + w / 2, y + h / 2 + (0.13 if detail else 0), titre, ha="center", va="center", fontsize=7.6, weight="bold" if bold else "normal",
            color=ENCRE)
    if detail:
        ax.text(x + w / 2, y + h / 2 - 0.17, detail, ha="center", va="center", fontsize=6.4, color=CH.SECONDAIRE)


def fleche(ax, x1, y1, x2, y2, col=CH.SECONDAIRE, ls="-"):
    ax.annotate("", (x2, y2), (x1, y1), arrowprops=dict(arrowstyle="-|>", color=col, lw=1.2, ls=ls))


def schema_electrique(ond, clim, ge=None, lt=None):
    fig, ax = plt.subplots(figsize=(11.7, 8.2))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 8.6)
    ax.set_axis_off()
    ax.text(0, 8.55, "Alimentation électrique de l'infrastructure", fontsize=14, weight="bold", color=ENCRE, va="top")
    ax.text(0, 8.15, "Chaque équipement critique est alimenté par deux voies indépendantes (A et B). La panne d'un onduleur "
                     "ou d'un circuit ne coupe aucun service.", fontsize=8, color=CH.SECONDAIRE, va="top")
    ax.text(0, 7.88, "v2.1 : un groupe électrogène et un inverseur de source secourent tout le tableau informatique (coupure longue).",
            fontsize=8, color=CH.EMERAUDE_FONCE, va="top", weight="bold")
    V, A, B, CLIM, LT = CH.EMERAUDE, VOIE_A, VOIE_B, CH.SECONDAIRE, CH.DISCRET
    VERT_CLAIR = "#E8F8EC"
    # Sources : réseau (TGBT) et groupe électrogène, inverseur de source, tableau informatique
    boite(ax, 1.6, 6.75, 3.3, 0.62, "Arrivée électrique du bâtiment", "TGBT existant (RDC) · départ 4P 63 A", fc=CH.REMPLISSAGE, ec=CH.DISCRET)
    if ge:
        boite(ax, 7.1, 6.75, 3.6, 0.62, f"Groupe électrogène {ge['esp']} kVA ESP · v2.1",
              f"{ge['prp']} kVA PRP, diesel, capoté · cuve {ge['cuve']} l (≈ {ge['autonomie_moy']:.0f} h) · extérieur", fc=VERT_CLAIR, ec=V)
        boite(ax, 4.0, 5.85, 4.0, 0.6, "Inverseur de source automatique · v2.1", "4P 63 A · bascule en ≈ 15 s · reports vers la supervision",
              fc=VERT_CLAIR, ec=V)
        fleche(ax, 3.25, 6.75, 5.0, 6.45)
        fleche(ax, 8.9, 6.75, 7.0, 6.45, V)
        ax.text(2.3, 6.5, "réseau (normal)", fontsize=6.5, color=CH.SECONDAIRE)
        ax.text(8.75, 6.5, "secours", fontsize=6.5, color=V)
        fleche(ax, 6.0, 5.85, 6.0, 5.55)
    else:
        fleche(ax, 3.25, 6.75, 6.0, 5.55)
    boite(ax, 4.3, 4.95, 3.4, 0.6, "Tableau informatique TD-INFO", "dans la salle serveur, hors d'eau · 13 départs", fc=CH.REMPLISSAGE)
    boite(ax, 1.0, 3.6, 2.6, 0.72, "Onduleur A", f"APC SRT 6 kVA{' + pack batterie' if ond['pack'] else ''}", ec=A)
    boite(ax, 4.7, 3.6, 2.6, 0.72, "Onduleur B", f"APC SRT 6 kVA{' + pack batterie' if ond['pack'] else ''}", ec=B)
    fleche(ax, 5.0, 4.95, 2.3, 4.32, A)
    fleche(ax, 6.0, 4.95, 6.0, 4.32, B)
    ax.text(1.0, 4.62, "départ 32 A · diff. type B", fontsize=6.5, color=A)
    ax.text(6.1, 4.62, "départ 32 A · type B", fontsize=6.5, color=B)
    boite(ax, 8.4, 3.6, 3.2, 0.72, f"2 climatiseurs {fr(clim['unite_kw'])} kW", "1 en marche, 1 en secours · relance temporisée", ec=CLIM)
    fleche(ax, 7.0, 4.95, 9.6, 4.32, CLIM)
    ax.text(8.45, 4.62, "2 départs 20 A · type F", fontsize=6.5, color=CLIM)
    for x, nom in ((0.4, "Baie 1 · réseau et sécurité"), (4.1, "Baie 2 · serveurs, enregistreur vidéo")):
        boite(ax, x, 2.1, 3.4, 0.75, nom, "PDU A (verte) + PDU B (ocre), métrées", ec=CH.SECONDAIRE)
    for xb in (2.1, 5.8):
        fleche(ax, 2.3, 3.6, xb - 0.35, 2.85, A)
        fleche(ax, 6.0, 3.6, xb + 0.35, 2.85, B)
    boite(ax, 0.4, 0.75, 3.4, 0.9, "Équipements à 2 alimentations", "cœur, distribution, switchs DT, pare-feu FortiGate,\nserveurs : 1 alim sur A, 1 sur B",
          fc="white", ec=CH.SECONDAIRE, bold=True)
    boite(ax, 4.1, 0.75, 3.4, 0.9, "Équipements à 1 alimentation", "routeurs, switchs C9200L, Stormshield,\ncontrôleurs Wi-Fi 9800-L : n°1 sur A, n°2 sur B",
          fc="white", ec=CH.SECONDAIRE, bold=True)
    fleche(ax, 2.1, 2.1, 2.1, 1.65)
    fleche(ax, 5.8, 2.1, 5.8, 1.65)
    n_ext = sum(1 for l in (lt or []) if l["bet"]["solution"][0] == "extracteur")
    n_spl = sum(1 for l in (lt or []) if l["bet"]["solution"][0] == "split")
    vent = f"\nventilation : {n_ext} extracteurs, {n_spl} mini-split (v2.1)" if lt else ""
    boite(ax, 8.4, 1.85, 3.2, 1.05, "", "", ec=LT)
    ax.text(10.0, 2.72, "6 locaux techniques", ha="center", va="center", fontsize=7.6, weight="bold", color=ENCRE)
    ax.text(10.0, 2.52, "coffret du local → onduleur 1,5 kVA → switchs PoE+\n→ bornes, caméras, badgeuses, téléphones" + vent,
            ha="center", va="top", fontsize=6.4, color=CH.SECONDAIRE)
    ax.plot([7.7, 11.8, 11.8], [5.25, 5.25, 3.3], color=LT, lw=1.2)
    fleche(ax, 11.8, 3.3, 11.3, 2.9, LT)
    ax.text(9.0, 5.32, "6 départs 20 A · 300 mA type A-S", fontsize=6.5, color=LT)
    txt = ("Coupure secteur : onduleurs sur batterie sans interruption ;\n"
           + (f"groupe en charge en ≈ 15 s, clim relancée à 60 s. Groupe absent :\narrêt ordonné à T0 + {bet.ARRET_GE_ABSENT_MIN} min "
              f"({ond['autonomie_degrade']} min d'autonomie avec 1 onduleur)." if ge else
              f"{ond['autonomie_degrade']} min même si un onduleur est en panne."))
    ax.text(8.2, 0.55, txt, fontsize=6.8, color=CH.SECONDAIRE, va="bottom")
    ax.text(0, 0.05, CH.mention_figure("14"), fontsize=6.6, color=CH.DISCRET, va="bottom")
    return fig


def schema_salle(clim):
    L, P = DIM_SALLE
    cam, _ = repere_salle_serveur("camera")
    bad, porte = repere_salle_serveur("badge")   # la badgeuse est à la porte : sa première circulation est celle de la porte
    FROID, CHAUD, CLIM, SONDE, EAU = CH.EMERAUDE_FONCE, CH.ROUGE, CH.SECONDAIRE, CH.SECONDAIRE, CH.ALERTE
    fig, ax = plt.subplots(figsize=(11.7, 7.6))
    ax.set_aspect("equal")
    ax.set_xlim(-0.6, L + 5.7)
    ax.set_ylim(P + 1.2, -1.2)
    ax.set_axis_off()
    ax.text(-0.6, -1.15, "Salle serveur : implantation et circulation de l'air", fontsize=14, weight="bold", color=ENCRE, va="top")
    ax.text(-0.6, -0.72, f"Partie sud de la salle J05 (sous-sol), {fr(L, 2)} × {fr(P, 2)} m ≈ {SURFACE_SALLE:.0f} m². Vue de dessus.",
            fontsize=8, color=CH.SECONDAIRE, va="top")
    ax.add_patch(Rectangle((0, 0), L, P, fc="#FBFBFC", ec=ENCRE, lw=3))
    # cloison nouvelle (nord) en pointillé, porte à l'est
    ax.plot([0, L], [0, 0], color="white", lw=3)
    ax.plot([0, L], [0, 0], color=ENCRE, lw=2.2, ls=(0, (6, 3)))
    ax.text(L / 2, -0.12, "cloison nouvelle (reste de J05 au nord)", ha="center", va="bottom", fontsize=6.5, color=CH.DISCRET)
    ax.plot([L, L], [2.35, 3.25], color="#FBFBFC", lw=4)
    ax.plot([L + 0.05, L + 0.05], [2.35, 3.25], color=EAU, lw=3)
    ax.text(L + 0.15, 2.8, f"porte vers {porte or 'CIRC 03'}\nbatardeau\nbadge {bad or 'B'}\ncaméra {cam or 'C'}", fontsize=6.5, va="center")
    ax.add_patch(Rectangle((0.03, 0.03), L - 0.06, P - 0.06, fc="none", ec=EAU, lw=0.8, ls=":"))
    ax.text(L / 2, P + 0.25, "mur sud : local technique N-1-LT01 (passage des fibres)", ha="center", fontsize=6.5, color=CH.DISCRET)
    # baies (faces avant vers le sud = allée froide)
    for i, nom in enumerate(("Baie 1\nréseau,\nsécurité", "Baie 2\nserveurs,\nNVR")):
        x = 2.0 + i * 0.8
        ax.add_patch(Rectangle((x, 0.9), 0.8, 1.0, fc=CH.REMPLISSAGE, ec=ENCRE, lw=1.4))
        ax.text(x + 0.4, 1.4, nom, ha="center", va="center", fontsize=6.3, weight="bold", color=ENCRE)
    ax.add_patch(Rectangle((1.6, 1.9), 2.4, 1.2, fc=FROID + "22", ec=FROID, lw=1, ls="--"))
    ax.text(2.8, 2.55, "ALLÉE FROIDE (confinée)\nair à 24-27 °C devant les baies", ha="center", va="center", fontsize=6.6, color=FROID, weight="bold")
    ax.add_patch(Rectangle((1.6, 0.05), 2.4, 0.85, fc=CHAUD + "14", ec=CHAUD, lw=1, ls="--"))
    ax.text(2.8, 0.47, "allée chaude (arrière des baies)", ha="center", va="center", fontsize=6.3, color=CHAUD)
    # climatiseurs
    for k, y in enumerate((1.0, 2.7)):
        ax.add_patch(Rectangle((0.05, y), 0.55, 0.6, fc=CLIM + "22", ec=CLIM, lw=1.4))
        ax.text(0.33, y + 0.3, f"CLIM {k + 1}", ha="center", va="center", fontsize=6, weight="bold", color=ENCRE, rotation=90)
        ax.annotate("", (1.55, 2.5), (0.65, y + 0.3), arrowprops=dict(arrowstyle="-|>", color=FROID, lw=1.4))
    ax.annotate("", (0.65, 0.6), (1.55, 0.4), arrowprops=dict(arrowstyle="-|>", color=CHAUD, lw=1.4))
    ax.text(0.9, 0.2, "reprise d'air chaud", fontsize=6, color=CHAUD)
    # coffret TD-INFO, sondes, fuite, extincteur
    ax.add_patch(Rectangle((L - 0.5, 0.2), 0.4, 0.5, fc=CH.REMPLISSAGE, ec=ENCRE))
    ax.text(L - 0.3, 0.45, "TD", ha="center", va="center", fontsize=6, weight="bold", color=ENCRE)
    for (x, y, t_, c) in ((2.8, 3.05, "T/H", SONDE), (1.3, 1.9, "T/H", SONDE), (0.33, 3.5, "fuite", EAU),
                          (0.33, 0.85, "fuite", EAU), (L - 0.3, 3.55, "CO2", CHAUD), (L - 0.9, 0.45, "gaz", CHAUD),
                          (4.6, 1.5, "VESDA", CHAUD)):
        ax.plot(x, y, marker="o", ms=6, mfc="white", mec=c, mew=1.6)
        ax.text(x + 0.12, y - 0.1, t_, fontsize=5.8, color=c, weight="bold")
    # cotes
    ax.annotate("", (L, P + 0.6), (0, P + 0.6), arrowprops=dict(arrowstyle="<->", color=CH.DISCRET, lw=0.8))
    ax.text(L / 2, P + 0.75, f"{fr(L, 2)} m", ha="center", fontsize=7, color=CH.DISCRET)
    ax.annotate("", (-0.35, P), (-0.35, 0), arrowprops=dict(arrowstyle="<->", color=CH.DISCRET, lw=0.8))
    ax.text(-0.45, P / 2, f"{fr(P, 2)} m", ha="right", va="center", fontsize=7, color=CH.DISCRET, rotation=90)
    # légende
    lx = L + 1.5
    items = [("Baie 42U 800 × 1000 : onduleur et pack en bas, PDU A et B à l'arrière", ENCRE),
             (f"Climatiseur technique {fr(clim['unite_kw'])} kW (1 en marche, 1 en secours)", CLIM),
             ("Air froid soufflé dans l'allée froide", FROID), ("Air chaud repris derrière les baies", CHAUD),
             ("T/H : sonde température/humidité (supervision)", SONDE), ("fuite : détecteur de fuite d'eau au sol", EAU),
             ("CO2 : extincteur · gaz : bouteilles IG-541 · VESDA : détection", CHAUD),
             ("TD : tableau informatique et inverseur de source (v2.1)", ENCRE),
             ("pointillé ocre : plancher surélevé 30 cm · batardeau à la porte", EAU)]
    ax.text(lx, 0.05, "LÉGENDE", fontsize=8, weight="bold", color=ENCRE)
    for k, (t_, c) in enumerate(items):
        ax.add_patch(Rectangle((lx, 0.35 + k * 0.42), 0.22, 0.22, fc=c, ec="none", alpha=0.8))
        ax.text(lx + 0.35, 0.47 + k * 0.42, t_, fontsize=6.6, va="center")
    ax.text(lx, 4.25, f"Chaleur à évacuer : {fr(clim['q_typ'], 2)} kW (pointe {fr(clim['q_pointe'], 2)} kW).\nUn seul climatiseur suffit ; "
                     "le second prend le relais\nen cas de panne ou d'entretien.", fontsize=7, va="top", color=CH.SECONDAIRE)
    ax.text(-0.6, P + 1.15, CH.mention_figure("14"), fontsize=6.6, color=CH.DISCRET, va="bottom")
    return fig


def sauver(fig, nom):
    (OUT / "schemas").mkdir(parents=True, exist_ok=True)
    for ext in ("png", "svg", "pdf"):
        fig.savefig(OUT / "schemas" / f"{nom}.{ext}", dpi=170 if ext == "png" else None, bbox_inches="tight", metadata=META[ext])
    plt.close(fig)


# ---------------------------------------------------------------------------
# Document
# ---------------------------------------------------------------------------
e = html.escape


def num(v):
    return CH.nombre(round(v))


def eur(v):
    return f"{CH.nombre(round(v))} €"


def meur(v):
    """Montant pour le Markdown du README (espace ordinaire, que lit outils/ci/verifier_coherence.py)."""
    return f"{md(v)} €"


V1 = ROOT / "livrables" / "archives" / "v1_2026-11-15" / "energie_refroidissement" / "resume.json"


def encadre_version(s, en, fin):
    """Comparaison avec la version 1 archivée (avant l'audit)."""
    if not V1.exists():
        return ""
    v1 = json.loads(V1.read_text(encoding="utf-8"))
    lignes = [("Puissance de la salle (typique)", f"{num(v1['salle']['it_typ'])} W", f"{num(s['it_typ'])} W"),
              ("Consommation annuelle", f"{num(v1['energie']['kwh'])} kWh", f"{num(en['kwh'])} kWh"),
              ("Électricité par an", eur(v1['energie']['cout']), eur(en['cout'])),
              ("Investissement du lot", eur(v1['capex_lot']), eur(fin['capex']))]
    return (f"<div class='note'><b>Version 2, après l'audit du 15/11/2026</b> {CH.badge('v2')}. La version 1 est archivée dans "
            "<code>livrables/archives/v1_2026-11-15/</code> ; le traitement de chaque constat est dans <code>livrables/audit/traitement_audit.pdf</code>. "
            "Changements : 12 serveurs physiques remplacés par 4 hyperviseurs et un témoin (SYS-02), 3 nœuds NM ramenés à 2 + témoin (SYS-01), "
            "contrôleurs Wi-Fi physiques (NET-01), plancher surélevé, batardeau, détection de fuite et extinction automatique au gaz (SYS-03), "
            "arrêt ordonné sur batterie par NUT.<table><tr><th></th><th class='n'>v1</th><th class='n'>actuel (v2.1)</th></tr>"
            + "".join(f"<tr><td>{a}</td><td class='n'>{b}</td><td class='n'><b>{c}</b></td></tr>" for a, b, c in lignes) + "</table></div>")


V21 = bet.V21


def encadre_v21(s, en, fin, ond, ge, lt):
    """Comparaison avec la version 2 publiée le 15/11/2026."""
    renf = [l["local"] for l in lt if not l["bet"]["v2_ok"]]
    lignes = [("Puissance de la salle (typique)", f"{num(V2_REF['it_typ'])} W", f"{num(s['it_typ'])} W"),
              ("PUE", fr(V2_REF['pue'], 2), fr(en['pue'], 2)),
              ("Consommation annuelle", f"{num(V2_REF['kwh'])} kWh", f"{num(en['kwh'])} kWh"),
              ("Investissement du lot", eur(V2_REF['capex_lot']) + " *", eur(fin['capex'])),
              ("Coûts annuels du lot", eur(V2_REF['opex_total']), eur(fin['opex_total'])),
              ("Coût du lot sur 5 ans", eur(V2_REF['cout_5ans']), eur(fin['cout_5ans']))]
    return (f"<div class='note'><b>Version 2.1 — {CH.DATE_VERSION}</b> {V21}. La version 2 est archivée dans <code>{CH.ARCHIVE_PRECEDENTE}</code>. "
            f"Changements dans ce document (repérés {V21}) : étude BET de chaque local "
            f"(<code>bet_locaux_techniques.pdf</code>, {bet.REF}, inventaire dans <code>bet_dissipation.csv</code>) ; <b>groupe électrogène "
            f"{ge['esp']} kVA ESP et inverseur de source</b> (le client confirme qu'il n'y en a pas sur le site) ; ventilation renforcée de "
            f"{', '.join(renf)} (trop chauds en été) ; pertes réelles des onduleurs à faible charge et auxiliaires de la salle comptés (PUE corrigé) ; "
            "différentiels adaptés (type B, F, A SI) et coffret par local ; arrêt ordonné déclenché seulement si le groupe n'a pas repris ; "
            "enregistreur vidéo VS-NVR1 dans la baie 2 ; contrôle d'accès sorti du lot (lot 4, sûreté) ; maintenance 24 h/24 7 j/7 en 4 h des "
            f"onduleurs et des climatiseurs ; {BORNES_COUPEES} bornes coupées la nuit (bornes « capacité » de l'étude Wi-Fi, v2 : 30)."
            "<table><tr><th></th><th class='n'>v2</th><th class='n'>v2.1</th></tr>"
            + "".join(f"<tr><td>{a}</td><td class='n'>{b}</td><td class='n'><b>{c}</b></td></tr>" for a, b, c in lignes) + "</table>"
            "<p class='sous'>* v2 : dont 5 000 € de contrôle d'accès par badge, chiffré en v2.1 avec le lot sûreté (catégorie « Sûreté » du chiffrage).</p></div>")


def arret_ordonne(ond):
    """v2 : séquence d'arrêt sur batterie (audit, question Q13) ; v2.1 : déclenchée seulement si le groupe électrogène n'a pas repris."""
    t0 = bet.ARRET_GE_ABSENT_MIN
    return (f"<h3>Arrêt ordonné sur batterie (NUT) {CH.badge('v2')} {V21}</h3>"
            "<p>Avec le groupe électrogène, l'onduleur ne fait plus que le <b>pont</b> pendant les ≈ 15 s de son démarrage. L'arrêt ordonné reste "
            "indispensable si le groupe ne démarre pas (sa panne la plus fréquente) : un hyperviseur coupé brutalement peut abîmer ses disques ou ses VM. "
            "Les cartes réseau des deux onduleurs (VLAN 900) sont lues par <b>NUT</b> (Network UPS Tools), dont le serveur tourne sur le témoin "
            "NM-WITNESS. Ce petit serveur physique s'éteint en dernier. Les hyperviseurs, le PBS, l'enregistreur vidéo VS-NVR1 et les témoins "
            "sont clients NUT.</p>"
            "<table><tr><th>Moment</th><th>Action</th></tr>"
            "<tr><td>T0 : coupure secteur</td><td>Les onduleurs basculent sur batterie sans interruption ; le groupe démarre. Alerte (supervision, courriel, SMS d'astreinte).</td></tr>"
            "<tr><td>T0 + 15 s</td><td>Le groupe est en tension, l'inverseur bascule : les onduleurs repassent « en ligne ». NUT annule son minuteur : rien ne s'arrête.</td></tr>"
            f"<tr><td>T0 + {t0} min</td><td>Si l'onduleur est <b>encore sur batterie</b> (groupe en défaut après trois tentatives, inverseur bloqué) : "
            "arrêt des VM non essentielles (supervision, VM applicatives de la DMZ). v2 : T0 + 5 min.</td></tr>"
            f"<tr><td>T0 + {t0 + 3} min</td><td>Arrêt des VM d'infrastructure : DHCP, NPS, Teleport, journaux (après vidage de leurs files d'attente), puis des contrôleurs de domaine.</td></tr>"
            f"<tr><td>T0 + {t0 + 6} min</td><td>Arrêt des hyperviseurs (DT, DM, NM) une fois leurs VM arrêtées, du serveur de sauvegarde et de "
            "l'enregistreur vidéo VS-NVR1.</td></tr>"
            f"<tr><td>T0 + {bet.FIN_ARRET_MIN} min</td><td>Arrêt de NM-WITNESS. Les onduleurs coupent leurs sorties serveurs. Les switchs et pare-feu restent alimentés jusqu'à "
            f"l'épuisement des batteries (≈ {ond['autonomie_degrade']} min avec un seul onduleur), car ils redémarrent sans risque.</td></tr>"
            "<tr><td>Retour du secteur</td><td>Les onduleurs ne rallument les serveurs que lorsque leurs batteries sont rechargées à 40 % (une seconde coupure ne doit pas "
            "les surprendre à vide). Le démarrage suit l'ordre inverse : témoins, hyperviseurs, puis les VM selon leur ordre de démarrage Proxmox.</td></tr></table>"
            f"<p class='sous'>Réglage NUT (upssched) : un minuteur de {t0} min démarre au passage sur batterie et s'annule au retour en ligne. Deux déclencheurs de "
            f"sécurité s'ajoutent : autonomie restante annoncée inférieure à {AUTONOMIE_ARRET} min, et température d'allée froide supérieure à "
            f"{bet.T_CRITIQUE:.0f} °C (groupe en défaut : les climatiseurs ne sont plus alimentés). La séquence est finie à T0 + {bet.FIN_ARRET_MIN} min, même avec un "
            f"seul onduleur ({ond['autonomie_degrade']} min d'autonomie, {round(bet.VIEILLISSEMENT * ond['autonomie_degrade'])} min en fin de vie des batteries). "
            "Elle est testée une fois par an, groupe volontairement bloqué.</p>")


def groupe_electrogene(ge, lt):
    """v2.1 : synthèse du groupe électrogène (détail dans bet_locaux_techniques.pdf, section 4)."""
    return (f"<h3>Groupe électrogène et inverseur de source {V21}</h3>"
            "<p>Le client confirme qu'il n'y a <b>pas de groupe électrogène sur le site</b> : ce n'est plus une option. Un groupe dédié secourt "
            "<b>tout le tableau informatique</b> : salle serveur (onduleurs, climatiseurs, éclairage, sécurité) et les 6 locaux techniques (Wi-Fi, "
            "téléphonie IP, badgeuses et caméras restent en service pendant une coupure longue). Le reste du bâtiment n'est pas secouru.</p><ul>"
            f"<li><b>Groupe diesel {ge['esp']} kVA ESP / {ge['prp']} kVA PRP</b> (NF ISO 8528), 400 V, capoté insonorisé, cuve double paroi de {ge['cuve']} l. "
            f"Besoin : {fr(ge['besoin'])} kVA (règle usuelle : 1,5 × la puissance des onduleurs, + climatiseurs et locaux) ; charge réelle maximale "
            f"{ge['taux_max']:.0f} % de la PRP.</li>"
            f"<li><b>Autonomie</b> : {ge['autonomie_moy']:.0f} h à la charge moyenne et {ge['autonomie_75']:.0f} h à 75 % de la PRP, cuve remplie à 75 % ; "
            "contrat de livraison de gazole sous 24 h.</li>"
            "<li><b>Inverseur de source automatique</b> 4P 63 A en tête du TD-INFO : réseau absent 3 s → démarrage du groupe → bascule en ≈ 15 s → "
            "climatiseurs relancés à 60 et 90 s. Les onduleurs font le pont, sans aucune coupure pour les équipements.</li>"
            "<li><b>Emplacement</b> : extérieur, façade est, sur dalle près de l'entrée du parking (accès du camion de gazole), échappement loin des prises d'air "
            "(emplacement exact à vérifier sur site). Essai mensuel en charge réelle, essai annuel sur banc de charge, contrat de maintenance.</li></ul>"
            "<p class='sous'>Dimensionnement, séquence de reprise, carburant, raccordement, réglementation : <code>bet_locaux_techniques.pdf</code>, section 4.</p>")


def document(lignes, baies, s, lt, ond, clim, en, gains, optim, fin, etd):
    ge = etd["ge"]
    ia = etd["reserve_ia"]
    H = [encadre_v21(s, en, fin, ond, ge, lt),
         encadre_version(s, en, fin),
         "<div class='cles'>",
         f"<div class='cle'><b>{fr(s['it_typ'] / 1000, 1)} kW</b>consommés par la salle serveur (typique)</div>",
         f"<div class='cle'><b>{ge['autonomie_moy']:.0f} h</b>de secours par le groupe électrogène, {ond['autonomie_degrade']} min sur batterie "
         "même avec un onduleur en panne</div>",
         f"<div class='cle'><b>PUE {fr(en['pue'], 2)}</b>contre {fr(en['pue_usuel'], 2)} dans une salle classique</div>",
         f"<div class='cle'><b>{eur(en['cout'])}</b>d'électricité par an ({num(en['kwh'])} kWh)</div></div>",
         "<h2>1. Ce que demande le projet, et notre réponse</h2>",
         "<table><tr><th>Demande</th><th>Source</th><th>Réponse</th><th>Partie</th></tr>",
         "<tr><td>Locaux techniques : rack, alimentation électrique, climatisation, accès par badge</td><td>Consignes, traitement A (architecture physique)</td>"
         "<td>Salle serveur + 6 locaux, baies, onduleurs, clim/ventilation, badgeuses</td><td>2, 3, 4</td></tr>",
         "<tr><td>Bilan de puissance par baie</td><td>Roadmap, point 14</td><td>Bilan équipement par équipement, baie par baie et local par local</td><td>2</td></tr>",
         "<tr><td>Dimensionner les onduleurs</td><td>Roadmap, point 14</td><td>2 onduleurs en ligne 6 kVA (voies A/B) + 6 onduleurs 1,5 kVA, autonomie vérifiée</td><td>3</td></tr>",
         "<tr><td>Climatisation de la salle serveur</td><td>Roadmap, point 14</td><td>2 climatiseurs techniques (1 en secours), allée froide, ventilation des locaux</td><td>4</td></tr>",
         "<tr><td>Mesure de consommation, PUE et Green IT ; développement durable obligatoire</td><td>Roadmap ; consignes (DD, Green IT)</td>"
         "<td>PDU et sondes supervisées, PUE calculé, 3 mesures d'économie chiffrées</td><td>5</td></tr>",
         "<tr><td>Data center : règles de base, PRA</td><td>Consignes, traitement C</td><td>Redondance électrique et frigorifique ; le PRA complet est traité au point 15</td><td>3, 4</td></tr>",
         f"<tr><td>Continuité en cas de coupure longue {V21}</td><td>Client (pas de groupe sur le site)</td><td>Groupe électrogène {ge['esp']} kVA ESP + "
         "inverseur automatique ; étude BET de chaque local</td><td>3, BET</td></tr>",
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
             f"<p><b>Salle serveur : {fr(s['it_typ'] / 1000, 2)} kW en fonctionnement normal, {fr(s['it_pointe'] / 1000, 2)} kW en pointe réaliste.</b> "
             f"{V21} : l'enregistreur vidéo VS-NVR1 du lot sûreté (baie 2) est compté.</p>")
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
          "<li>Un tableau électrique informatique (TD-INFO) dans la salle serveur, alimenté par un <b>inverseur de source</b> (réseau ou groupe "
          f"électrogène) {V21}, avec deux départs 32 A, un par onduleur.</li>",
          "<li>Onduleurs <b>en ligne double conversion</b> (APC SRT 6 kVA / 6 kW) : les équipements ne voient jamais une coupure ni une perturbation du réseau.</li>",
          "<li>Équipements à deux alimentations : l'une sur l'onduleur A, l'autre sur l'onduleur B. Équipements à une seule alimentation (routeurs, switchs C9200L, "
          "Stormshield, contrôleurs Wi-Fi 9800-L) : ils vont par paires, le n°1 sur A et le n°2 sur B, donc la panne d'une voie laisse toujours un équipement "
          "de la paire en service.</li></ul>",
          "<table><tr><th>Situation</th><th class='n'>Charge d'un onduleur</th><th class='n'>Taux</th><th class='n'>Autonomie</th></tr>",
          f"<tr><td>Normale (les deux onduleurs se partagent la charge)</td><td class='n'>{num(ond['normal'])} W</td><td class='n'>{ond['taux_normal']} %</td>"
          f"<td class='n'>{ond['autonomie_normal']} min</td></tr>",
          f"<tr><td>Un onduleur en panne : l'autre porte tout</td><td class='n'>{num(ond['degrade'])} W</td><td class='n'>{round(100 * ond['degrade'] / 6000)} %</td>"
          f"<td class='n'>{ond['autonomie_degrade']} min</td></tr>",
          f"<tr><td>Un onduleur en panne, en pointe</td><td class='n'>{num(ond['degrade_pointe'])} W</td><td class='n'>{ond['taux_degrade']} %</td><td class='n'>—</td></tr></table>",
          f"<p>{'✔' if ond['ok'] else '✘'} Règle de dimensionnement : moins de {int(MARGE_NORMALE * 100)} % en marche normale "
          f"({ond['taux_normal']} %) et moins de {int(MARGE_SECOURS * 100)} % pour un onduleur seul en pointe ({ond['taux_degrade']} %), "
          "situation rare qui cumule une panne et une pointe. Des onduleurs de 8 kVA (≈ 2 800 € HT de plus) ne sont donc pas nécessaires. "
          + (f"Sans batterie supplémentaire, l'autonomie avec un seul onduleur ne serait que de {fr(ond['autonomie_interne'])} min : "
             f"on ajoute <b>un pack batterie par onduleur</b> pour dépasser l'objectif de {AUTONOMIE_VISEE:.0f} min : la séquence d'arrêt "
             f"ordonné (attente du groupe {bet.ARRET_GE_ABSENT_MIN} min puis {bet.FIN_ARRET_MIN - bet.ARRET_GE_ABSENT_MIN} min d'arrêt, voir plus bas) doit tenir avec "
             "une marge, même si un onduleur est en panne et que ses batteries sont en fin de vie." if ond["pack"] else "L'autonomie interne suffit.") + "</p>",
          "<h3>Locaux techniques : un onduleur 1,5 kVA chacun</h3><table><tr><th>Local</th><th class='n'>Charge max.</th><th class='n'>Taux</th><th class='n'>Autonomie</th></tr>"]
    for l in lt:
        H.append(f"<tr><td>{l['local']}</td><td class='n'>{l['charge_max']} W</td><td class='n'>{l['taux']} %</td><td class='n'>{l['autonomie']} min</td></tr>")
    H.append(f"</table><p>Chaque local a son départ 20 A dédié vers un petit coffret (différentiels 30 mA adaptés) {V21}. Les bornes, les téléphones et "
             "les badgeuses restent alimentés pendant une coupure : quelques minutes sur l'onduleur, puis par le groupe électrogène. "
             "Autonomies : courbes constructeur indicatives, à confirmer avec l'outil du fabricant.</p>")
    H.append(groupe_electrogene(ge, lt))
    H.append(arret_ordonne(ond))
    # 4. Clim
    H += ["<h2 class='saut'>4. Climatisation et ventilation</h2>", "<img src='schemas/salle_serveur.png' alt='Implantation de la salle serveur'>",
          "<h3>Salle serveur</h3>",
          f"<p>Toute l'électricité consommée devient de la chaleur. À évacuer : <b>{fr(clim['q_typ'], 2)} kW</b> en fonctionnement normal et "
          f"<b>{fr(clim['q_pointe'], 2)} kW</b> en pointe (équipements, pertes des onduleurs, auxiliaires de sécurité et tableau {V21}, éclairage, une personne).</p>",
          f"<ul><li><b>2 climatiseurs techniques de {fr(clim['unite_kw'])} kW</b> (fonctionnement 24 h/24) : un seul suffit, à {clim['taux']} % de sa capacité en "
          "marche normale. Le second est en secours et ils alternent chaque semaine (usure égale, test permanent du secours). Contrat de maintenance "
          f"avec dépannage 24 h/24 7 j/7 et rétablissement en 4 h {V21}.</li>",
          "<li><b>Allée froide</b> : les baies se font face côté froid ; obturateurs sur les U vides et rideaux aux extrémités, pour que l'air froid "
          "passe dans les équipements au lieu de contourner les baies.</li>",
          "<li><b>Consigne à 27 °C</b> à l'entrée des équipements, dans la plage recommandée (ASHRAE A1 : 18 à 27 °C) : la clim consomme moins.</li>",
          "<li>Sondes de température et d'humidité, détecteur de fuite d'eau (salle au sous-sol), alertes dans la supervision. "
          "L'humidité relative est tenue entre 40 et 60 % : plus sec, risque d'électricité statique ; plus humide, condensation pendant les épisodes "
          "pluvieux.</li></ul>"
          f"<h3>Risques propres à une salle en sous-sol {CH.badge('v2')}</h3>"
          "<p>La salle est au sous-sol, où une inondation (épisode méditerranéen, canalisation) est le premier risque, et un incendie de nuit le "
          "second (constat SYS-03 de l'audit). En v1, ces protections étaient des options écartées. Elles font maintenant partie du lot :</p><ul>"
          "<li><b>Eau</b> : plancher technique surélevé de 30 cm (baies, onduleurs et climatiseurs posés dessus) ; batardeau amovible à la porte ; "
          "clapet anti-retour sur l'évacuation des condensats ; câble de détection de fuite sous le plancher, relié à la supervision et à l'astreinte. "
          "Si l'eau monte quand même, l'alerte arrive tôt et l'arrêt ordonné protège les données.</li>"
          "<li><b>Feu</b> : détection précoce par aspiration (VESDA) et extinction automatique par gaz inerte (IG-541), sans danger pour le matériel. "
          "Report au SSI du bâtiment, temporisation et coupure de la climatisation avant le déclenchement, extincteurs CO2 en complément.</li>"
          "<li><b>Reprise</b> : si la salle est perdue malgré tout, les sauvegardes hors site permettent de reconstruire ailleurs (PRA, point 15).</li></ul>",
          f"<h3>Locaux techniques {V21}</h3><table><tr><th>Local</th><th class='n'>Surface</th><th class='n'>Chaleur typique</th><th class='n'>Pointe été</th>"
          "<th>Solution v2</th><th>Solution retenue</th><th class='n'>T été</th></tr>"]
    for l in lt:
        H.append(f"<tr><td>{l['local']}</td><td class='n'>{l['surface']:.0f} m²</td><td class='n'>{l['chaleur']} W</td><td class='n'>{l['chaleur_pointe']} W</td>"
                 f"<td>{e(l['ventilation_v2'])}</td><td>{e(l['ventilation'])}{'' if l['bet']['v2_ok'] else ' ' + V21}</td><td class='n'>{fr(l['t_ete'])} °C</td></tr>")
    H.append("</table><p>Les locaux dégagent peu de chaleur : la puissance PoE est dissipée par les bornes et caméras, pas dans le local ; seules les pertes "
             "de conversion des switchs et de l'onduleur y restent. Pointe été : tout au maximum, un technicien et l'éclairage, avec l'air des circulations à "
             f"{bet.T_AMB_ETE['N-1']:.0f} °C au sous-sol, {bet.T_AMB_ETE['N0']:.0f} °C au RDC et {bet.T_AMB_ETE['N1']:.0f} °C à l'étage sous la toiture. "
             f"Critère : {bet.T_MAX_LT:.0f} °C au plus (onduleurs limités à 40 °C). La v2 appliquait une règle forfaitaire ; le BET de la v2.1 a montré que "
             f"{sum(not l['bet']['v2_ok'] for l in lt)} locaux devenaient trop chauds l'été ("
             + ", ".join(f"{l['local']} : {l['bet']['solution_court']}" for l in lt if not l["bet"]["v2_ok"]) + "). Calcul complet : "
             "<code>bet_locaux_techniques.pdf</code>, section 3.</p>")
    # 5. Green IT
    H += ["<h2>5. Mesure, PUE et Green IT</h2>",
          "<p><b>PUE</b> (efficacité énergétique) = électricité totale de la salle ÷ électricité des équipements informatiques. 1,0 serait parfait.</p>",
          "<table><tr><th>Salle serveur</th><th class='n'>Salle classique (22 °C)</th><th class='n'>Notre proposition</th></tr>",
          f"<tr><td>Équipements informatiques</td><td class='n'>{fr(en['it_kw'], 2)} kW</td><td class='n'>{fr(en['it_kw'], 2)} kW</td></tr>",
          f"<tr><td>Climatisation, pertes onduleurs, auxiliaires, éclairage, réchauffeur du groupe {V21}</td><td class='n'>{fr(en['it_kw'] * (en['pue_usuel'] - 1), 2)} kW</td>"
          f"<td class='n'>{fr(en['salle_kw'] - en['it_kw'], 2)} kW</td></tr>",
          f"<tr><td><b>PUE</b></td><td class='n'><b>{fr(en['pue_usuel'], 2)}</b></td><td class='n'><b>{fr(en['pue'], 2)}</b></td></tr></table>",
          "<p><b>Mesure en continu :</b> les PDU métrées (par prise), les onduleurs et les sondes sont interrogés par la supervision déjà prévue "
          "(LibreNMS et Grafana, zone NM). Le PUE réel est suivi chaque mois : la valeur ci-dessus est une estimation à confirmer.</p>",
          "<h3>Mesures d'économie retenues</h3><table><tr><th>Mesure</th><th class='n'>kWh/an</th><th class='n'>€/an</th><th class='n'>CO₂/an</th>"
          "<th class='n'>Coût</th><th class='n'>Retour</th></tr>"]
    for g in gains:
        H.append(f"<tr><td>{e(g['mesure'])}</td><td class='n'>{num(g['kwh'])}</td><td class='n'>{eur(g['euros'])}</td><td class='n'>{num(g['co2_kg'])} kg</td>"
                 f"<td class='n'>{eur(g['cout']) if g['cout'] else '0 €'}</td><td class='n'>{g['retour']}</td></tr>")
    H.append(f"</table><p>Avec ces mesures, le réseau consomme <b>{num(en['kwh'])} kWh/an</b> au lieu de {num(en['kwh_usuel'])}, "
             f"soit <b>{eur(en['cout_usuel'] - en['cout'])} économisés chaque année</b>. Électricité française peu carbonée : "
             f"≈ {fr(en['co2_t'])} t de CO₂ par an.</p><h3>Pistes d'optimisation du chiffrage, côté énergie</h3>"
             "<table><tr><th>Piste</th><th class='n'>Puissance en moins</th><th class='n'>kWh/an</th><th class='n'>€/an</th></tr>")
    for o in optim:
        H.append(f"<tr><td>{e(o['piste'])}</td><td class='n'>{o['w']} W</td><td class='n'>{num(o['kwh'])}</td><td class='n'>{eur(o['euros'])}</td></tr>")
    H.append("</table><p class='sous'>Économies d'électricité en plus des économies d'achat déjà indiquées dans le chiffrage.</p>")
    # 6. Finances
    H += ["<h2 class='saut'>6. Finances du lot énergie et refroidissement</h2>", "<h3>Investissement (CAPEX, € HT)</h3>",
          "<table><tr><th>Élément</th><th>Où</th><th class='n'>Qté</th><th class='n'>Prix unitaire</th><th class='n'>Total</th><th>Remarque</th></tr>"]
    for l in fin["deja"] + fin["nouveaux"]:
        nv = (" " + V21 if "v2.1" in l["note"] else " <b>(ajouté)</b>") if l in fin["nouveaux"] else ""
        H.append(f"<tr><td>{e(l['solution'])}{nv}</td><td>{e(l['schema'])}</td><td class='n'>{l['quantite']}</td><td class='n'>{eur(l['pu_ht'])}</td>"
                 f"<td class='n'>{eur(l['total_ht'])}</td><td class='chemin'>{e(l['note'])}</td></tr>")
    H.append(f"<tr><td colspan='4'><b>Total du lot</b></td><td class='n'><b>{eur(fin['capex'])}</b></td><td></td></tr></table>"
             f"<p class='sous'>{V21} : le contrôle d'accès par badge (5 000 € en v2) n'est plus dans ce lot : il est chiffré avec le lot sûreté "
             "(caméras, enregistreur, badgeuses), catégorie « Sûreté » du chiffrage.</p>"
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
             f"<li>À vérifier sur site {V21} : réserve de puissance au TGBT du bâtiment ({etd['tableau']['reserve_kva']} kVA, un départ 4P 63 A), "
             "régime de neutre, emplacement exact du TGBT et du groupe électrogène (façade est, accès du camion de gazole, distance aux prises d'air) ; "
             "avis du bureau de contrôle.</li>"
             f"<li>Tranche optionnelle « plateforme d'IA locale » du CCTP lot 3 {V21} : un nœud de {ia['gpu']} GPU consomme environ "
             f"{fr(ia['kw'], 0)} kW, ce que la salle actuelle ne couvre pas (onduleurs, climatiseurs, groupe : voir la réserve de "
             f"<code>bet_locaux_techniques.pdf</code>, section 1). Étude spécifique avant de lever l'option.</li>"
             "<li>Emplacement des unités extérieures des climatiseurs (cour ou façade la plus proche du sous-sol) et passage des liaisons.</li>"
             "<li>Puissances des équipements : fiches constructeur, à affiner avec les configurateurs ; autonomies indicatives.</li>"
             f"<li>Électricité à {fr(PRIX_KWH, 2)} € HT/kWh, comme dans le chiffrage ; facteur carbone ≈ {CO2_KG_KWH * 1000:.0f} g CO₂/kWh.</li>"
             "<li>Le plan de reprise d'activité (PRA) relève du point 15. L'étude de l'extinction automatique (volume de la salle, étanchéité, "
             "évent de surpression) est à confier à un installateur certifié APSAD.</li>"
             "<li>Cote de crue et historique des remontées d'eau du sous-sol : à demander aux services techniques du campus.</li></ul>"
             f"<p class='sous'>Étude BET détaillée (inventaire par local, ventilation, circuits, groupe électrogène, vérifications) : "
             f"<code>bet_locaux_techniques.pdf</code> ({bet.REF}).</p>")
    H.append(CH.bloc_suivi(REF, changements="Étude BET (RLI-ETU-013), groupe électrogène et inverseur de source, pertes réelles des onduleurs, "
                                            "ventilation des L.TECH, VS-NVR1, contrôle d'accès sorti du lot, maintenance 4 h, charte commune."))
    page = CH.page(titre="Énergie et refroidissement", titre_court="Énergie et refroidissement", ref=REF, points="14", dossier=OUT,
                   chapo="Alimentation électrique, onduleurs, groupe électrogène, climatisation et ventilation des locaux techniques, "
                         "consommation et coûts de l'infrastructure réseau.",
                   corps="\n".join(H), css_extra=bet.CSS_BET)
    CH.ecrire_et_imprimer(page, OUT / "energie_refroidissement.html", OUT / "energie_refroidissement.pdf")


def main():
    lignes, baies, s, lt, ond, clim, en, gains, optim, n_vent = calculs()
    # v2.1 : étude BET (circuits, groupe électrogène, vérifications), avant les finances qui chiffrent le groupe
    ctx = dict(lignes=lignes, baies=baies, s=s, lt=lt, ond=ond, clim=clim, en=en, plan=PLAN)
    etd = bet.etude(ctx)
    ge = etd["ge"]
    fin = finances(ond, lt, en, ge)
    OUT.mkdir(parents=True, exist_ok=True)
    sauver(schema_electrique(ond, clim, ge, lt), "synoptique_electrique")
    sauver(schema_salle(clim), "salle_serveur")
    with open(OUT / "bilan_puissance.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(lignes[0].keys()))
        w.writeheader()
        w.writerows(lignes)
    locaux = [{k: v for k, v in l.items() if k != "bet"} for l in lt]
    resume = dict(version="2.1", date=CH.DATE_VERSION, reference=REF, salle=s, baies=baies, locaux=locaux, onduleurs=ond, clim=clim, energie=en, gains=gains,
                  optimisations=optim, capex_nouveaux=[{k: v for k, v in l.items() if k != "ge"} for l in fin["nouveaux"]], capex_lot=fin["capex"],
                  capex_groupe_electrogene=sum(l["total_ht"] for l in fin["nouveaux"] if l.get("ge")),
                  opex=[dict(poste=a, detail=b, montant=c) for a, b, c in fin["opex"]], opex_total=fin["opex_total"], cout_5ans=fin["cout_5ans"],
                  bet=bet.resume(etd, lt), v2=V2_REF)
    (OUT / "resume.json").write_text(json.dumps(resume, ensure_ascii=False, indent=1), encoding="utf-8")
    document(lignes, baies, s, lt, ond, clim, en, gains, optim, fin, etd)
    bet.produire(ctx, etd, fin)
    renf = [l["local"] for l in lt if not l["bet"]["v2_ok"]]
    lot_v2_hors_badge = V2_REF["capex_lot"] - 5000
    readme = [
        "# Énergie et refroidissement (point 14)",
        "<!-- onglet: Énergie -->", "",
        "Alimentation électrique, onduleurs, groupe électrogène, climatisation et ventilation des locaux techniques, consommation et coûts du lot "
        "énergie de l'infrastructure réseau, avec l'étude BET de chaque local technique.", "",
        "| Document | Réf. | Contenu |", "|---|---|---|",
        f"| **[energie_refroidissement.pdf](energie_refroidissement.pdf)** | {REF} | Document principal : bilan de puissance, onduleurs, groupe "
        "électrogène, arrêt ordonné, climatisation et ventilation, PUE et Green IT, finances du lot |",
        f"| **[bet_locaux_techniques.pdf](bet_locaux_techniques.pdf)** | {bet.REF} | Étude BET : inventaire, chaleur, ventilation et circuits de chaque "
        "local, tableau informatique, TGBT, groupe électrogène, vérifications, réserve sur la plateforme d'IA |",
        "| `bet_dissipation.csv`, `bilan_puissance.csv` | — | Une ligne par équipement et par local (W absorbés, W dissipés, BTU/h) ; bilan de la salle serveur |",
        "| `schemas/`, `resume.json` | — | Alimentation électrique, plan de la salle serveur, montée en température ; synthèse reprise par le chiffrage |", "",
        "| | |", "|---|---|",
        f"| Salle serveur | {md(s['it_typ'] / 1000, 2)} kW typique, {md(s['it_pointe'] / 1000, 2)} kW en pointe, 2 baies 42U (enregistreur vidéo VS-NVR1 "
        f"compris) ; chaleur {md(clim['q_typ'], 2)} kW (pointe {md(clim['q_pointe'], 2)} kW) |",
        f"| Onduleurs | 2 × APC SRT 6 kVA en ligne (voies A et B){' + 1 pack batterie chacun' if ond['pack'] else ''} : {ond['autonomie_degrade']} min "
        "même avec un onduleur en panne · 6 × 1,5 kVA dans les locaux techniques |",
        f"| Groupe électrogène (v2.1) | {ge['esp']} kVA ESP / {ge['prp']} kVA PRP diesel capoté, cuve {ge['cuve']} l ({ge['autonomie_moy']:.0f} h à la charge "
        f"moyenne), inverseur de source automatique en tête du TD-INFO ; arrêt ordonné NUT seulement si le groupe n'a pas repris à T0 + {bet.ARRET_GE_ABSENT_MIN} min |",
        f"| Climatisation | 2 climatiseurs techniques {md(clim['unite_kw'], 1)} kW (1 en secours), allée froide, consigne 27 °C · L.TECH : "
        + ", ".join(f"{l['local']} {l['bet']['solution_court'].replace(chr(160), ' ')}" for l in lt) + " |",
        f"| Électricité | {etd['tableau']['n_circuits']} départs au TD-INFO ; réserve au TGBT : {etd['tableau']['reserve_kva']} kVA (départ 4P 63 A), à vérifier sur site |",
        f"| Efficacité | PUE {md(en['pue'], 2)} (contre {md(en['pue_usuel'], 2)} pour une salle classique) · {md(en['kwh'])} kWh/an · "
        f"environ {md(en['co2_t'], 1)} t CO₂/an |",
        f"| Finances | Investissement {meur(fin['capex'])} HT (dont groupe électrogène {meur(resume['capex_groupe_electrogene'])}) · "
        f"{meur(fin['opex_total'])} HT/an · {meur(fin['cout_5ans'])} HT sur 5 ans |",
        "| Maintenance (v2.1) | Onduleurs et climatiseurs de la salle : dépannage 24 h/24 7 j/7, rétablissement en 4 h |", "",
        f"**Version 2.1 — {CH.DATE_VERSION}** : étude BET de chaque local ({bet.REF} : inventaire, chaleur, ventilation, circuits, vérifications). "
        f"Le client confirme qu'il n'y a pas de groupe électrogène sur le site : un groupe {ge['esp']} kVA ESP et un inverseur automatique sont intégrés "
        f"au lot. Ventilation renforcée de {', '.join(renf)} (trop chauds en été), pertes réelles des onduleurs à faible charge et auxiliaires comptés "
        f"(PUE {md(V2_REF['pue'], 2)} → {md(en['pue'], 2)}), différentiels adaptés (type B, F, A SI), batteries des L.TECH remplacées tous les "
        f"{DUREE_BATTERIE_SMT} ans, enregistreur vidéo VS-NVR1 au bilan, {BORNES_COUPEES} bornes coupées la nuit, maintenance en 4 h des onduleurs et "
        "des climatiseurs. Le contrôle d'accès par badge (5 000 € en v2) passe au lot sûreté. Lot : "
        f"{meur(V2_REF['capex_lot'])} (dont 5 000 € de contrôle d'accès, soit {meur(lot_v2_hors_badge)} à périmètre égal) → {meur(fin['capex'])} HT "
        f"d'investissement, {meur(V2_REF['opex_total'])} → {meur(fin['opex_total'])} par an. Repérés « v2.1 » dans les documents. Version précédente : "
        f"`{CH.ARCHIVE_PRECEDENTE}`.", "",
        "**Version 2 (15/11/2026, après l'audit)** : serveurs virtualisés (16 serveurs physiques → 9 : 6 hyperviseurs DM/DT/NM, 2 témoins, 1 serveur de "
        "sauvegarde), contrôleurs Wi-Fi physiques, plancher surélevé, batardeau, câble de détection de fuite et extinction automatique au gaz intégrés "
        "au lot (SYS-03), arrêt ordonné sur batterie par NUT. La v1 est archivée dans `livrables/archives/v1_2026-11-15/energie_refroidissement/` ; "
        "le traitement de l'audit est dans `livrables/audit/`. La toute première version (Gemini) est dans git (commit 1fbc1c1).", "",
        "Régénérer : `python3 energie/energie.py` (sources : `energie/energie.py`, qui appelle `energie/bet.py` ; lit `livrables/plan_cablage/` et "
        "les lignes de `chiffrage/estimation.py`), puis `python3 chiffrage/estimation.py`. Chaîne complète : `bash outils/ci/generer_tout.sh`.", ""]
    (OUT / "README.md").write_text("\n".join(readme), encoding="utf-8")
    print(f"Salle : {s['it_typ']} W typ., {s['it_pointe']} W pointe | onduleur seul {ond['degrade_pointe']} W ({ond['taux_degrade']} %), "
          f"autonomie {ond['autonomie_degrade']} min, pack={ond['pack']} | clim {clim['q_typ']}/{clim['q_pointe']} kW -> 2×{clim['unite_kw']} kW")
    print(f"PUE {en['pue']} (usuel {en['pue_usuel']}) | {en['kwh']} kWh/an = {en['cout']} € | CAPEX lot {fin['capex']} € | "
          f"OPEX {fin['opex_total']} €/an | 5 ans {fin['cout_5ans']} €")
    print("BET : L.TECH " + ", ".join(f"{l['local']} {l['bet']['solution_court']} {l['bet']['t_ete']:.1f}°C" for l in lt))
    print(f"GE {ge['esp']}/{ge['prp']} kVA (besoin {ge['besoin']:.1f}), charge max {ge['taux_max']:.0f} %, moy {ge['taux_moy']:.0f} %, cuve {ge['cuve']} l, "
          f"{ge['autonomie_moy']:.0f} h | réserve TGBT {etd['tableau']['reserve_kva']} kVA | vérifs "
          + ", ".join(f"{k}={sum(v['statut'] == k for v in etd['verifs'])}" for k in ("OK", "Corrigé v2.1", "OK avec parade", "À vérifier", "NOK")))


if __name__ == "__main__":
    main()
