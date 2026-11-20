#!/usr/bin/env python3
"""BET fluides / courants forts : bilan thermique et électrique de chaque local technique (v2.1, 20/11/2026).

Module appelé par energie/energie.py, qui lui fournit le bilan de puissance (salle serveur, 6 locaux techniques).
  - fonctions de calcul utilisées par energie.py : pertes des onduleurs, charge thermique de la salle,
    inventaire et ventilation de chaque local technique ;
  - etude() : circuits électriques du tableau informatique, groupe électrogène, vérifications ;
  - produire() : livrables/energie_refroidissement/bet_locaux_techniques.html/.pdf, bet_dissipation.csv,
    schemas/montee_temperature.png.

Usage : python3 energie/energie.py (qui appelle ce module), ou python3 energie/bet.py (même effet).
Toutes les hypothèses sont en tête de fichier, avec leur justification.
"""
import csv
import html
import math
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "livrables" / "energie_refroidissement"
REF = "RLI-NRJ-002"
DATE_V21 = "20/11/2026"
V21 = "<span class='v21'>v2.1</span>"

# ---------------------------------------------------------------------------
# Hypothèses physiques
# ---------------------------------------------------------------------------
BTU = 3.412                  # 1 W = 3,412 BTU/h
RHO_CP = 1.2 * 1005.0        # J/(m³·K) : capacité thermique volumique de l'air
G = 9.81
T_CONSIGNE = 27.0            # °C, entrée des équipements (ASHRAE A1 recommandé : 18-27 °C)
T_ALARME, T_CRITIQUE, T_LIMITE = 30.0, 35.0, 40.0   # alarme, limite A2 (35 °C), limite de fonctionnement onduleurs/serveurs (40 °C)
T_MAX_LT = 35.0              # °C : critère de conception d'un local technique en été (onduleur 40 °C max, 5 K de marge)
CANICULE_K = 4.0             # K ajoutés à l'air des circulations en canicule (contrôle : rester sous 40 °C)
# Air des circulations voisines en été (bâtiment non climatisé, Marseille) : sous-sol enterré frais, étage sous toiture-terrasse chaud
T_AMB_ETE = {"N-1": 24.0, "N0": 27.0, "N1": 30.0}
HAUTEUR = {"N-1": 2.7, "N0": 2.8, "N1": 2.8}           # m sous plafond (plans : hauteur d'étage 3,5 m)
APPORT_PAROIS_W_M2 = {"N-1": 0.0, "N0": 0.0, "N1": 10.0}  # été : toiture-terrasse isolée (U ≈ 0,4 × écart soleil-air ≈ 25 K)
U_PAROI = 1.5                # W/(m²·K) : cloisons et plafond vers les volumes voisins (panne de ventilation)
FRACTION_MASSE = 0.3         # part de la masse des baies et équipements qui suit l'air en moins d'une heure
C_MASSE = 450.0              # J/(kg·K) : acier, cuivre, plomb, plastiques (moyenne)
ECLAIRAGE_W_M2 = 8.0         # LED
OCCUPANT_W = 100.0           # chaleur sensible d'un technicien en intervention
SURFACE_SALLE = 25.0
DIM_SALLE = (6.35, 3.94)
HAUTEUR_SALLE_UTILE = 2.4    # 2,7 m - plancher technique de 30 cm
SHR_CLIM = 0.9               # part sensible de la puissance frigorifique d'un climatiseur technique (salle sèche, reprise chaude)
DEBIT_CLIM_M3H = 1200.0      # débit d'air d'une unité intérieure de 7,1 kW (fiches constructeur : 1 100-1 300 m³/h)
DT_SERVEURS = 12.0           # K : échauffement de l'air à travers les serveurs et switchs (ventilateurs pilotés)
P_CLIM_MAX_KW = 2.7          # kW absorbés au maximum par une unité de 7,1 kW (compresseur inverter), intensité ≈ 12,5 A
EER_ETE = 2.8                # EER par 35 °C extérieur
RELANCE_CLIM_S = 240         # s sans froid à la reprise sur GE : 15 s (GE) + 45 s (temporisation) + 3 min (anti-court-cycle du compresseur)

# Onduleurs : pertes = fixe + proportionnelle (courbes de rendement constructeur, ordre de grandeur)
def pertes_srt(charge_w):
    """APC SRT 6 kVA en ligne double conversion : ≈ 100 W à vide + 3 % (92 % à 30 % de charge, 95 % à pleine charge)."""
    return 100.0 + 0.03 * charge_w


def pertes_smt(charge_w):
    """APC SMT 1500 line-interactive : ≈ 12 W (chargeur en floating, électronique) + 2 % (relais, autotransformateur)."""
    return 12.0 + 0.02 * charge_w


RECHARGE_SRT_W = 400.0       # W absorbés par le chargeur d'un SRT 6 kVA + pack après une décharge
RECHARGE_SMT_W = 60.0
VIEILLISSEMENT = 0.8         # capacité batterie en fin de vie (remplacement à 80 %)

# Locaux techniques : appareils alimentés par PoE (classe = puissance réservée par le switch, plan de câblage)
POE_APPAREILS = [  # (clé du plan, modèle, W typique, W classe)
    ("wifi", "Borne Wi-Fi 6E Cisco CW9164I", 13.0, 25.5),
    ("cameras", "Caméra IP (PoE 802.3af)", 6.0, 12.95),
    ("badges", "Lecteur de badge PoE", 4.0, 6.5),
    ("telephones", "Téléphone IP PoE", 4.0, 6.5),
]
MASSE_BAIE = {"24U murale": 35.0, "42U au sol": 90.0}
MASSE_SWITCH, MASSE_PANNEAU, MASSE_SMT = 5.0, 1.5, 26.0
# Ventilation des locaux techniques
GRILLE_M2, CD, H_GRILLES = 0.06, 0.6, 1.8   # 2 grilles 600×200 (section libre 50 %), basse en porte, haute en imposte, 1,8 m d'écart
EXTRACTEURS = [(150, 25), (300, 35)]         # m³/h, W : extracteurs de gaine thermostatés (rejet vers l'extérieur ou la reprise VMC)
SPLIT_KW, SPLIT_ELEC_KW, SPLIT_EER = 2.5, 0.9, 3.0   # mini-split mural froid seul, unité extérieure en toiture ou en façade
FUITE_SWITCH_MA, FUITE_ONDULEUR_MA = 1.0, 2.0         # courants de fuite permanents typiques (filtres CEM)

# ---------------------------------------------------------------------------
# Hypothèses électriques (NF C 15-100, IEC 60364-5-52)
# ---------------------------------------------------------------------------
RHO = 0.0225                 # Ω·mm²/m : cuivre en service (NF C 15-100)
LAMBDA = 0.00008             # Ω/m : réactance linéique
IZ = {  # A : câbles U1000 R2V (PR) sur chemin de câbles (méthode E), 2 ou 3 conducteurs chargés
    2: {1.5: 26, 2.5: 36, 4: 49, 6: 63, 10: 86, 16: 115, 25: 149},
    3: {1.5: 23, 2.5: 32, 4: 42, 6: 54, 10: 75, 16: 100, 25: 127},
}
K_POSE = 0.7                 # groupement sur chemin de câbles (0,8) × 35 °C ambiant (0,91), arrondi
CALIBRES = [10, 16, 20, 25, 32, 40, 50, 63, 80, 100]
DU_TERMINAL, DU_DISTRIBUTION = 3.0, 2.0   # % : chutes de tension admises (total ≤ 5 %, autres usages)
L_TGBT_TD = 50.0             # m : TGBT supposé au RDC (local PL.ELEC, 27 m²) → salle serveur, par la colonne nord
L_GE_TD = 60.0               # m : GE en façade est → salle, par le parking (chemin de l'adduction FAI 2)
L_SALLE = {"onduleur": 8.0, "clim": 20.0, "eclairage": 10.0, "prises": 12.0, "aux": 10.0}
TARIF_KVA_AN = 20.0          # € HT/kVA/an : ordre de grandeur de la part fixe d'un contrat BT > 36 kVA (TURPE + fourniture)

# ---------------------------------------------------------------------------
# Groupe électrogène (NF ISO 8528) : gamme type de groupes diesel capotés 400 V
# ---------------------------------------------------------------------------
GE_GAMME = [  # (PRP kVA, ESP kVA, l/h à 75 % PRP, prix fourni € HT, masse kg)
    (20, 22, 3.9, 14500, 800),
    (30, 33, 5.3, 17500, 950),
    (40, 44, 7.0, 21000, 1150),
    (60, 66, 10.2, 26000, 1500),
]
CUVES_L = [100, 150, 250, 400]
COS_GE = 0.8
K_ONDULEUR_GE = 1.5          # surdimensionnement pour les onduleurs (redresseur PFC, faible THDi : bas de la règle 1,5 à 2)
K_LT_GE = 1.25               # onduleurs line-interactive et alimentations à découpage
MARGE_EVOLUTION = 1.2
AUTONOMIE_GE_H, AUTONOMIE_GE_75_H = 48, 24
REMPLISSAGE, FOND = 0.75, 0.9   # cuve refaite à 75 % ; 10 % de fond non pompable
PRIX_GAZOLE = 1.40           # € HT/l (gazole non routier), ordre de grandeur 2026
ESSAIS_H = 12 * 1.0          # essai mensuel d'1 h sur la charge réelle
BANC_H = 2.0                 # essai annuel sur banc de charge à 75 %
COUPURES_H = 4.0             # heures de coupure réseau par an (hypothèse prudente)
GE_AUX_W = 120.0             # W moyens : réchauffeur de bloc 500 W thermostaté (~25 % du temps) + chargeur de batterie
ARRET_GE_ABSENT_MIN = 3      # min : sans retour du GE, NUT lance l'arrêt ordonné (v2 : 5 min, sans GE)
FIN_ARRET_MIN = 11           # min : fin de la séquence d'arrêt (v2 : 13 min)

e = html.escape


def fr(v, d=1):
    """Nombre au format français (virgule, espace des milliers)."""
    s = f"{v:,.{d}f}".replace(",", " ").replace(".", ",")
    return s


eur = lambda v: f"{v:,.0f} €".replace(",", " ")


def mono_courant(p_w, cos=0.95):
    return p_w / (230.0 * cos)


def chute(L, i, s, tri=False, cos=0.95):
    sin = math.sqrt(1 - cos ** 2)
    du = (math.sqrt(3) if tri else 2) * L * i * (RHO * cos / s + LAMBDA * sin)
    return 100 * du / (400 if tri else 230)


def section(In, i_b, L, tri=False, du_max=DU_TERMINAL, cos=0.95):
    """Plus petite section telle que Iz ≥ In et ΔU(I_B) ≤ du_max."""
    for s, iz in sorted(IZ[3 if tri else 2].items()):
        if iz * K_POSE >= In and chute(L, i_b, s, tri, cos) <= du_max:
            return s, iz * K_POSE, chute(L, i_b, s, tri, cos)
    raise ValueError("section introuvable")


def calibre(i):
    return next(c for c in CALIBRES if c >= i)


def montee(P, C, UA, T0, T_adj, seuil):
    """Minutes pour atteindre `seuil` sans refroidissement (modèle RC : C dT/dt = P - UA (T - T_adj)). None : jamais."""
    if T0 >= seuil:
        return 0.0
    T_inf = T_adj + P / UA
    if T_inf <= seuil:
        return None
    return -C / UA * math.log((T_inf - seuil) / (T_inf - T0)) / 60


def courbe(P, C, UA, T0, T_adj, minutes):
    T_inf = T_adj + P / UA
    return [T_inf + (T0 - T_inf) * math.exp(-m * 60 * UA / C) for m in minutes]


def duree(m):
    if m is None:
        return "jamais"
    if m == 0:
        return "déjà atteint"
    return f"{m:.0f} min" if m >= 10 else f"{fr(m)} min"


# ---------------------------------------------------------------------------
# Salle serveur : composantes de la charge thermique (utilisées par energie.py pour la clim et le PUE)
# ---------------------------------------------------------------------------
AUX_SALLE = [  # (repère, désignation, W)
    ("VESDA", "Détection précoce par aspiration (VESDA)", 30),
    ("EXT", "Centrale d'extinction IG-541 et déclencheurs", 15),
    ("ACC", "Lecteur de badge B1 et gâche de la porte", 10),
    ("SON", "Sondes T/H et centrale de détection de fuite", 10),
]
TD_PERTES_W = 40             # TD-INFO + inverseur : pertes Joule des appareillages (≈ 2 W par départ chargé) + électronique


def charge_salle(it_typ, it_pointe):
    aux = sum(w for *_, w in AUX_SALLE)
    ecl = SURFACE_SALLE * ECLAIRAGE_W_M2
    p_typ, p_pte = 2 * pertes_srt(it_typ / 2), 2 * pertes_srt(it_pointe / 2)
    q_typ = it_typ + p_typ + aux + TD_PERTES_W + 0.1 * ecl
    q_pte = it_pointe + p_pte + aux + TD_PERTES_W + ecl + OCCUPANT_W
    return dict(pertes_typ=p_typ, pertes_pointe=p_pte, aux=aux, td=TD_PERTES_W, eclairage=ecl, q_typ=q_typ, q_pointe=q_pte)


# ---------------------------------------------------------------------------
# Locaux techniques : inventaire, dissipation, ventilation
# ---------------------------------------------------------------------------
def k_grilles(t_amb):
    a_eff = GRILLE_M2 / math.sqrt(2)     # deux ouvertures en série
    return RHO_CP * CD * a_eff * math.sqrt(2 * G * H_GRILLES / (t_amb + 273.15))


def regime(solution, P, t_amb):
    """Température du local en régime établi (parois négligées : conservateur)."""
    nom, q = solution
    if nom == "grilles":
        return t_amb + (P / k_grilles(t_amb)) ** (2 / 3)
    if nom == "extracteur":
        return t_amb + P / (RHO_CP * q / 3600)
    return T_CONSIGNE if SPLIT_KW * 1000 >= 1.2 * P else 99.0


def libelle(solution):
    nom, q = solution
    return {"grilles": "grilles hautes et basses (ventilation naturelle)", "extracteur": f"extracteur thermostaté {q} m³/h",
            "split": f"mini-split {fr(SPLIT_KW)} kW froid"}[nom]


def court(solution):
    nom, q = solution
    return {"grilles": "grilles", "extracteur": f"extracteur {q} m³/h", "split": f"mini-split {fr(SPLIT_KW)} kW"}[nom]


def local_technique(b, sw_typ, sw_max, rend_poe):
    """Inventaire équipement par équipement, dissipation, choix et vérification de la ventilation d'un L.TECH."""
    n, niv, S = b["switchs_48p"], b["niveau"], b["surface_m2"]
    inv = []

    def ligne(rep, mod, q, wa_t, wa_m, wd_t, wd_m, alim, note=""):
        inv.append(dict(local=b["local"], repere=rep, modele=mod, quantite=q, w_abs_typ=round(wa_t, 1), w_abs_max=round(wa_m, 1),
                        w_dis_typ=round(wd_t, 1), w_dis_max=round(wd_m, 1), btu_typ=round(wd_t * BTU), btu_max=round(wd_m * BTU),
                        alimentation=alim, note=note))

    poe_t = sum(b[k] * t for k, _, t, _ in POE_APPAREILS)
    poe_m = float(b["poe_W"])
    ligne(f"SW1…SW{n}" if n > 1 else "SW1", "Cisco C9200L-48P-4X : électronique et ventilateurs (hors PoE)", n, n * sw_typ, n * sw_max,
          n * sw_typ, n * sw_max, "onduleur du local")
    ligne("PoE", f"PoE envoyé sur les câbles (alimentation + PSE, rendement {rend_poe:.0%})", 1, poe_t / rend_poe, poe_m / rend_poe,
          poe_t * (1 / rend_poe - 1), poe_m * (1 / rend_poe - 1), "onduleur du local", "seules les pertes restent dans le local")
    for k, mod, t, c in POE_APPAREILS:
        if b[k]:
            ligne(k.upper()[:3], mod, b[k], b[k] * t, b[k] * c, 0, 0, "PoE (hors local)",
                  "chaleur chez l'appareil ; énergie comptée dans la ligne PoE")
    charge_t, charge_m = n * sw_typ + poe_t / rend_poe, n * sw_max + poe_m / rend_poe
    ligne("OND", "APC Smart-UPS SMT 1500 RM 2U (line-interactive) : pertes", 1, pertes_smt(charge_t), pertes_smt(charge_m),
          pertes_smt(charge_t), pertes_smt(charge_m), "départ du TD-INFO", "≈ 12 W + 2 % de la charge")
    ligne("PB", "Panneaux de brassage, tiroir optique, passe-câbles", b["panneaux_24"] + 1, 0, 0, 0, 0, "—", "passifs")
    ecl = ECLAIRAGE_W_M2 * S
    ligne("ECL", "Éclairage LED (allumé pendant les interventions)", 1, 0, ecl, 0, ecl, "éclairage du bâtiment", "ponctuel")
    ligne("OCC", "Technicien en intervention (chaleur sensible)", 1, 0, OCCUPANT_W, 0, OCCUPANT_W, "—", "ponctuel")
    apport = APPORT_PAROIS_W_M2[niv] * S
    if apport:
        ligne("PAR", "Apports par la toiture-terrasse en été (local sous toiture)", 1, 0.4 * apport, apport, 0.4 * apport, apport, "—",
              f"{APPORT_PAROIS_W_M2[niv]:.0f} W/m² en été, 40 % en moyenne annuelle")
    perm_t = sum(l["w_dis_typ"] for l in inv)
    p_dim = sum(l["w_dis_max"] for l in inv)          # pointe : tout au maximum + technicien + éclairage
    perm_m = p_dim - ecl - OCCUPANT_W                 # permanent maximal (sans intervention)
    t_amb = T_AMB_ETE[niv]
    # Solution v2 (règle forfaitaire : extracteur si local « L.TECH » ou chaleur > 200 W ou surface < 4 m², sinon grilles)
    chaleur_v2 = n * sw_typ + poe_t * (1 / rend_poe - 1) + charge_t * 0.04
    v2 = ("extracteur", EXTRACTEURS[0][0]) if (b["salle"] == "L.TECH" or chaleur_v2 > 200 or S < 4) else ("grilles", 0)
    candidats = [("grilles", 0)] + [("extracteur", q) for q, _ in EXTRACTEURS] + [("split", 0)]
    ok = lambda sol: regime(sol, p_dim, t_amb) <= T_MAX_LT and regime(sol, p_dim, t_amb + CANICULE_K) <= T_LIMITE
    v2_ok = ok(v2)
    sol = v2 if v2_ok else next(c for c in candidats[candidats.index(v2) + 1:] if ok(c))
    t_ete, t_can = regime(sol, p_dim, t_amb), regime(sol, p_dim, t_amb + CANICULE_K)
    t_perm = regime(sol, perm_m, t_amb)
    # Panne de la ventilation (ou grilles obstruées) : montée en température depuis le régime permanent d'été
    H = HAUTEUR[niv]
    a_parois = 2 * (math.sqrt(1.5) + 1 / math.sqrt(1.5)) * math.sqrt(S) * H + S
    masse = MASSE_BAIE.get(b["baie"], 60) + n * MASSE_SWITCH + b["panneaux_24"] * MASSE_PANNEAU + MASSE_SMT
    c_air = S * H * RHO_CP
    C = c_air + FRACTION_MASSE * masse * C_MASSE
    UA = U_PAROI * a_parois
    t0 = t_perm
    panne = dict(t0=round(t0, 1), t_inf=round(t_amb + perm_m / UA, 1), C_kJ=round(C / 1000), UA=round(UA),
                 t35=montee(perm_m, C, UA, t0, t_amb, T_CRITIQUE), t40=montee(perm_m, C, UA, t0, t_amb, T_LIMITE),
                 t35_air=max(0.0, (T_CRITIQUE - t0) * c_air / perm_m / 60), t40_air=max(0.0, (T_LIMITE - t0) * c_air / perm_m / 60))
    debit_10k = perm_t * 3600 / (RHO_CP * 10)
    if sol[0] == "split":
        elec_vent_max, elec_vent_moy = SPLIT_ELEC_KW * 1000, perm_t / SPLIT_EER
    elif sol[0] == "extracteur":
        w = dict(EXTRACTEURS)[sol[1]]
        elec_vent_max, elec_vent_moy = w, 0.5 * w
    else:
        elec_vent_max = elec_vent_moy = 0.0
    fuite = n * FUITE_SWITCH_MA + FUITE_ONDULEUR_MA
    return dict(inventaire=inv, charge_typ=charge_t, charge_max=charge_m, pertes_ond_typ=pertes_smt(charge_t), pertes_ond_max=pertes_smt(charge_m),
                dissipation_typ=perm_t, dissipation_max=perm_m, p_dim=p_dim, t_amb=t_amb, solution=sol, solution_libelle=libelle(sol),
                solution_court=court(sol), v2=v2, v2_court=court(v2), v2_ok=v2_ok, t_v2=regime(v2, p_dim, t_amb),
                t_ete=t_ete, t_canicule=t_can, t_permanent=t_perm, panne=panne, masse=masse, debit_10k=debit_10k,
                elec_vent_max=elec_vent_max, elec_vent_moy=elec_vent_moy, fuite_ma=fuite,
                grilles_t=regime(("grilles", 0), p_dim, t_amb))


# ---------------------------------------------------------------------------
# Étude : salle serveur, tableau informatique, groupe électrogène, vérifications
# ---------------------------------------------------------------------------
def etude(ctx):
    lignes, s, lt, ond, clim, en, baies = ctx["lignes"], ctx["s"], ctx["lt"], ctx["ond"], ctx["clim"], ctx["en"], ctx["baies"]
    rocade = {}
    for r in ctx["plan"]["rocades"]:
        if r["voie"] == "A":
            rocade[r["local"]] = r["longueur"]
    cs = charge_salle(s["it_typ"], s["it_pointe"])
    # --- Salle serveur : inventaire
    inv = []
    for l in lignes:
        inv.append(dict(local="Salle serveur", repere=l["reperes"], modele=l["modele"], quantite=l["nombre"], w_abs_typ=l["total_typ"],
                        w_abs_max=l["total_max"], w_dis_typ=l["total_typ"], w_dis_max=l["total_max"], btu_typ=round(l["total_typ"] * BTU),
                        btu_max=round(l["total_max"] * BTU), alimentation=f"PDU A/B (baie {l['baie']})" if l["alimentations"] else "—",
                        note="" if l["total_typ"] else "passifs"))
    normal_u, pointe_u = s["it_typ"] / 2, s["it_pointe"] / 2
    extra = [("OND-A, OND-B", "APC SRT 6 kVA en ligne double conversion : pertes", 2, 2 * pertes_srt(normal_u), 2 * pertes_srt(pointe_u),
              "TD-INFO", f"100 W + 3 % chacun ; {100 * normal_u / (normal_u + pertes_srt(normal_u)):.0f} % à {100 * normal_u / 6000:.0f} % de charge"),
             ("TD", "Tableau TD-INFO et inverseur de source : pertes", 1, TD_PERTES_W, TD_PERTES_W, "—", "≈ 2 W par départ chargé + électronique")]
    extra += [(r, d, 1, w, w, "TD-INFO (auxiliaires)", "") for r, d, w in AUX_SALLE]
    extra += [("ECL", "Éclairage LED 8 W/m²", 1, 0.1 * cs["eclairage"], cs["eclairage"], "TD-INFO", "allumé 10 % du temps"),
              ("OCC", "Technicien en intervention", 1, 0, OCCUPANT_W, "—", "ponctuel"),
              ("PAR", "Apports par les parois", 1, 0, 0, "—", "sous-sol enterré : pertes vers le sol négligées")]
    for r, d, q, wt, wm, al, no in extra:
        inv.append(dict(local="Salle serveur", repere=r, modele=d, quantite=q, w_abs_typ=round(wt, 1), w_abs_max=round(wm, 1), w_dis_typ=round(wt, 1),
                        w_dis_max=round(wm, 1), btu_typ=round(wt * BTU), btu_max=round(wm * BTU), alimentation=al, note=no))
    # --- Salle serveur : thermique
    q_typ, q_pte = cs["q_typ"], cs["q_pointe"]
    sensible = clim["unite_kw"] * SHR_CLIM
    debit_it = s["it_typ"] * 3600 / (RHO_CP * DT_SERVEURS)
    dt_clim = q_pte * 3600 / (RHO_CP * DEBIT_CLIM_M3H)
    L, P = DIM_SALLE
    vol = SURFACE_SALLE * HAUTEUR_SALLE_UTILE
    c_air = vol * RHO_CP
    u_occ = sum(v["u"] for v in baies.values()) - 2 * 7
    masse = 2 * 130 + 12 * u_occ + 2 * (60 + 65)
    C = c_air + FRACTION_MASSE * masse * C_MASSE
    UA = U_PAROI * (2 * (L + P) * HAUTEUR_SALLE_UTILE + SURFACE_SALLE)
    t_adj = T_AMB_ETE["N-1"]
    th_salle = dict(q_typ=q_typ, q_pointe=q_pte, sensible=sensible, taux_unite=100 * q_pte / (1000 * sensible), debit_it=debit_it, dt_clim=dt_clim,
                    vol=vol, masse=masse, C_kJ=C / 1000, UA=UA, t_inf=t_adj + q_typ / UA,
                    t35=montee(q_typ, C, UA, T_CONSIGNE, t_adj, T_CRITIQUE), t40=montee(q_typ, C, UA, T_CONSIGNE, t_adj, T_LIMITE),
                    t35_air=(T_CRITIQUE - T_CONSIGNE) * c_air / q_pte / 60, t40_air=(T_LIMITE - T_CONSIGNE) * c_air / q_pte / 60,
                    t_relance=courbe(q_typ, C, UA, T_CONSIGNE, t_adj, [RELANCE_CLIM_S / 60])[0],
                    t_relance_air=T_CONSIGNE + q_pte * RELANCE_CLIM_S / c_air,
                    t_arret=courbe(q_typ, C, UA, T_CONSIGNE, t_adj, [FIN_ARRET_MIN])[0], c_air=c_air)
    # --- Circuits du tableau informatique (TD-INFO)
    circuits = []

    def circuit(rep, nom, phase, p_w, In, diff, i_b=None, L=10.0, cos=0.95, note=""):
        i_reel = mono_courant(p_w, cos)
        i_b = i_b if i_b is not None else i_reel
        sct, iz, du = section(In, i_b, L, cos=cos)
        circuits.append(dict(repere=rep, nom=nom, phase=phase, p_w=p_w, i_reel=i_reel, i_b=i_b, In=In, courbe="C", diff=diff, L=L,
                             section=sct, iz=iz, du=du, note=note))

    srt_reel = ond["degrade_pointe"] + pertes_srt(ond["degrade_pointe"]) + RECHARGE_SRT_W
    srt_nominal = mono_courant(6000 + pertes_srt(6000) + RECHARGE_SRT_W, 0.99)
    for k, ph in (("A", "L1"), ("B", "L2")):
        circuit(f"Q{1 if k == 'A' else 2}", f"Onduleur {k} (APC SRT 6 kVA, voie {k})", ph, srt_reel, 32, "300 mA type B sélectif",
                i_b=srt_nominal, L=L_SALLE["onduleur"], cos=0.99,
                note="I_B = entrée à 6 kW + recharge ; réel : l'onduleur seul en pointe, batteries en recharge")
    for k, ph in ((1, "L3"), (2, "L3")):
        circuit(f"Q{2 + k}", f"Climatiseur {k} ({clim['unite_kw']} kW, unité extérieure)", ph, P_CLIM_MAX_KW * 1000, 20, "30 mA type F",
                L=L_SALLE["clim"], note="compresseur inverter, calibre conseillé par le constructeur")
    phases_lt = {"N-1-LT01": "L1", "N0-LT01": "L1", "N-1-LT02": "L2", "N0-LT02": "L2", "N1-LT01": "L3", "N1-LT02": "L3"}
    for i, l in enumerate(lt):
        th = l["bet"]
        p = th["charge_max"] + th["pertes_ond_max"] + RECHARGE_SMT_W + th["elec_vent_max"]
        circuit(f"Q{5 + i}", f"{l['local']} : coffret du L.TECH (onduleur + {th['solution_court']})", phases_lt.get(l["local"], "L3"), p, 20,
                "300 mA type A sélectif", i_b=1.25 * mono_courant(p), L=rocade.get(l["local"], 60.0) + 5,
                note="dans le coffret : 30 mA type A SI (prise onduleur), 30 mA type F (ventilation)")
    circuit("Q11", "Éclairage de la salle serveur", "L1", cs["eclairage"], 10, "30 mA type A", L=L_SALLE["eclairage"])
    circuit("Q12", "Prises de service de la salle (non ondulées)", "L2", 2300, 16, "30 mA type A SI", i_b=10.0, L=L_SALLE["prises"],
            note="outillage, aspirateur : 10 A retenus")
    circuit("Q13", "Auxiliaires de sécurité (VESDA, extinction, badge, sondes)", "L1", cs["aux"], 10, "30 mA type A SI", L=L_SALLE["aux"])
    phases = {}
    for c in circuits:
        phases.setdefault(c["phase"], 0.0)
        phases[c["phase"]] += c["i_reel"] if c["repere"] != "Q12" else 0.5 * c["i_reel"]
    i_phase_max = max(phases.values())
    # Puissance appelée par le lot informatique
    ups_in_max = s["it_pointe"] + 2 * pertes_srt(s["it_pointe"] / 2) + 2 * RECHARGE_SRT_W
    lt_max = sum(l["bet"]["charge_max"] + l["bet"]["pertes_ond_max"] + RECHARGE_SMT_W + l["bet"]["elec_vent_max"] for l in lt)
    aux_max = cs["eclairage"] + cs["aux"] + 500
    p_max = ups_in_max + 2 * P_CLIM_MAX_KW * 1000 + lt_max + aux_max
    s_max = ups_in_max / 0.99 + 2 * P_CLIM_MAX_KW * 1000 / 0.95 + lt_max / 0.95 + aux_max / 0.95
    ups_in_typ = s["it_typ"] + cs["pertes_typ"]
    lt_typ = sum(l["bet"]["charge_typ"] + l["bet"]["pertes_ond_typ"] + l["bet"]["elec_vent_moy"] for l in lt)
    p_moy = ups_in_typ + q_typ / EER_ETE + lt_typ + cs["aux"] + 0.1 * cs["eclairage"]
    reserve_kva = math.ceil(s_max * MARGE_EVOLUTION / 1000)
    i_tri_max = max(i_phase_max * MARGE_EVOLUTION, s_max / (math.sqrt(3) * 400) * MARGE_EVOLUTION)
    sect_feeder, iz_f, du_f = section(63, i_tri_max, L_TGBT_TD, tri=True, du_max=DU_DISTRIBUTION)
    tableau = dict(phases=phases, i_phase_max=i_phase_max, desequilibre=100 * (max(phases.values()) - min(phases.values())) / max(phases.values()),
                   In_tete=63, selectivite=63 / max(c["In"] for c in circuits), feeder_section=sect_feeder, feeder_iz=iz_f, feeder_du=du_f,
                   feeder_i=i_tri_max, p_max=p_max, s_max=s_max, p_moy=p_moy, reserve_kva=reserve_kva, cout_kva=reserve_kva * TARIF_KVA_AN,
                   n_circuits=len(circuits), du_max=max(c["du"] for c in circuits))
    # --- Groupe électrogène
    ge = groupe_electrogene(ups_in_max, lt_max, aux_max, p_moy, ond, s)
    sect_ge, iz_ge, du_ge = section(63, ge["i_nominal"], L_GE_TD, tri=True, du_max=DU_DISTRIBUTION, cos=0.8)
    ge.update(cable_section=sect_ge, cable_iz=iz_ge, cable_du=du_ge, cable_L=L_GE_TD)
    # --- Onduleurs : vieillissement, pont
    ond_fin_vie = VIEILLISSEMENT * ond["autonomie_degrade"]
    lt_aut_min = min(l["autonomie"] for l in lt)
    lt_taux_max = max(l["taux"] for l in lt)
    verifs = verifications(ctx, th_salle, lt, tableau, ge, circuits, ond_fin_vie, lt_aut_min, lt_taux_max)
    return dict(salle=dict(inventaire=inv, thermique=th_salle, charge=cs), circuits=circuits, tableau=tableau, ge=ge, verifs=verifs,
                ond_fin_vie=ond_fin_vie, lt_aut_min=lt_aut_min, lt_taux_max=lt_taux_max)


def groupe_electrogene(ups_in_max, lt_max, aux_max, p_moy, ond, s):
    charges = [
        ("Onduleurs de la salle (2 × SRT 6 kVA, redresseur PFC)", ups_in_max, 0.99, K_ONDULEUR_GE,
         "pointe informatique + pertes + recharge des deux jeux de batteries après la coupure"),
        ("Climatiseurs de la salle (2 × 7,1 kW, compresseurs inverter)", 2 * P_CLIM_MAX_KW * 1000, 0.95, 1.0,
         "les deux en marche pour refroidir la salle après la reprise ; démarrage progressif, relance échelonnée"),
        ("Locaux techniques (6 onduleurs 1,5 kVA + ventilation)", lt_max, 0.95, K_LT_GE, "PoE au maximum de classe, recharge des batteries"),
        ("Auxiliaires de la salle (éclairage, sécurité, prises de service)", aux_max, 0.95, 1.0, "BAES autonomes : non comptés"),
    ]
    rows = [dict(nom=n, kw=p / 1000, cos=c, kva=p / 1000 / c, coef=k, kva_pond=p / 1000 / c * k, note=no) for n, p, c, k, no in charges]
    reel = sum(r["kva"] for r in rows)
    m1 = sum(r["kva_pond"] for r in rows) * MARGE_EVOLUTION
    m2 = K_ONDULEUR_GE * 2 * 6.0 + sum(r["kva"] for r in rows[1:])
    besoin = max(m1, m2)
    prp, esp, c75, prix, masse = next(g for g in GE_GAMME if g[0] >= besoin)
    kw_prp = prp * COS_GE
    conso = lambda kw: c75 * (0.2 + 0.8 * kw / (0.75 * kw_prp))
    c_moy = conso(p_moy / 1000)
    besoin_cuve = max(AUTONOMIE_GE_H * c_moy, AUTONOMIE_GE_75_H * c75) / (FOND * REMPLISSAGE)
    cuve = next(v for v in CUVES_L if v >= besoin_cuve)
    utile = cuve * FOND * REMPLISSAGE
    litres_an = ESSAIS_H * c_moy + BANC_H * c75 + COUPURES_H * c_moy
    return dict(charges=rows, reel_kva=reel, reel_kw=sum(r["kw"] for r in rows), m1=m1, m2=m2, besoin=besoin, prp=prp, esp=esp, kw_prp=kw_prp,
                prix=prix, masse=masse, c75=c75, c_moy=c_moy, p_moy_kw=p_moy / 1000, taux_max=100 * reel / prp,
                taux_moy=100 * (p_moy / 1000 / 0.95) / prp, cuve=cuve, autonomie_moy=utile / c_moy, autonomie_75=utile / c75,
                autonomie_pleine=cuve * FOND / c_moy, i_nominal=prp * 1000 / (math.sqrt(3) * 400), icc=3 * prp * 1000 / (math.sqrt(3) * 400),
                palier_kva=ups_in_max / 1000 / 0.99, palier_pct=100 * ups_in_max / 1000 / 0.99 / prp, litres_an=litres_an,
                thermique_kw=kw_prp / 0.33)


def verifications(ctx, th, lt, tab, ge, circuits, ond_fin_vie, lt_aut_min, lt_taux_max):
    ond = ctx["ond"]
    V = []

    def v(domaine, critere, valeur, seuil, statut, note=""):
        V.append(dict(domaine=domaine, critere=critere, valeur=valeur, seuil=seuil, statut=statut, note=note))

    ok = lambda c: "OK" if c else "NOK"
    v("Onduleurs salle", "Charge d'un onduleur en marche normale", f"{ond['taux_normal']} %", "≤ 80 %", ok(ond["taux_normal"] <= 80))
    v("Onduleurs salle", "Charge d'un onduleur seul, en pointe", f"{ond['taux_degrade']} %", "≤ 90 %", ok(ond["taux_degrade"] <= 90))
    v("Onduleurs salle", "Autonomie, un onduleur en panne, batteries en fin de vie (80 %)", f"{ond_fin_vie:.0f} min",
      f"≥ {ARRET_GE_ABSENT_MIN + FIN_ARRET_MIN} min (attente GE + arrêt ordonné)", ok(ond_fin_vie >= ARRET_GE_ABSENT_MIN + FIN_ARRET_MIN))
    v("Onduleurs L.TECH", "Charge maximale (PoE au maximum de classe)", f"{lt_taux_max} %", "≤ 80 %", ok(lt_taux_max <= 80))
    v("Onduleurs L.TECH", "Autonomie minimale (pont pendant le démarrage du GE)", f"{lt_aut_min} min", "≥ 5 min", ok(lt_aut_min >= 5))
    v("Clim salle", "Puissance sensible d'une unité / pointe", f"{fr(th['sensible'])} kW / {fr(th['q_pointe'] / 1000, 2)} kW",
      "unité ≥ 1,15 × pointe", ok(th["sensible"] * 1000 >= 1.15 * th["q_pointe"]))
    v("Clim salle", "Débit d'air d'une unité / besoin des équipements", f"{DEBIT_CLIM_M3H:.0f} / {th['debit_it']:.0f} m³/h", "≥ 1,1 × besoin",
      ok(DEBIT_CLIM_M3H >= 1.1 * th["debit_it"]), f"ΔT au soufflage {fr(th['dt_clim'])} K en pointe")
    v("Clim salle", "Panne des 2 climatiseurs : temps pour atteindre 40 °C", duree(th["t40"]), f"≥ {FIN_ARRET_MIN} min (arrêt ordonné)",
      ok(th["t40"] is None or th["t40"] >= FIN_ARRET_MIN), f"35 °C en {duree(th['t35'])} ; air seul (borne pessimiste) : {duree(th['t40_air'])}")
    v("Clim salle", f"Reprise sur GE : température après {RELANCE_CLIM_S // 60} min sans froid", f"{fr(th['t_relance'])} °C", "≤ 32 °C (ASHRAE A1)",
      ok(th["t_relance"] <= 32), f"borne pessimiste (air seul) {fr(th['t_relance_air'])} °C")
    for l in lt:
        b = l["bet"]
        st = "OK" if b["v2_ok"] else "Corrigé v2.1"
        v("L.TECH", f"{l['local']} : température d'été ({b['solution_court']})", f"{fr(b['t_ete'])} °C", f"≤ {T_MAX_LT:.0f} °C", st,
          "" if b["v2_ok"] else f"v2 ({b['v2_court']}) : {fr(b['t_v2'])} °C")
    v("L.TECH", "Canicule (+4 K) : local le plus chaud", f"{fr(max(l['bet']['t_canicule'] for l in lt))} °C", "≤ 40 °C",
      ok(max(l["bet"]["t_canicule"] for l in lt) <= 40))
    v("L.TECH", "Courant de fuite permanent sur le 30 mA le plus chargé", f"{max(l['bet']['fuite_ma'] for l in lt):.0f} mA", "≤ 9 mA (30 % de IΔn)",
      ok(max(l["bet"]["fuite_ma"] for l in lt) <= 9))
    v("Électricité", "Chute de tension maximale d'un départ du TD-INFO", f"{fr(tab['du_max'])} %", f"≤ {DU_TERMINAL:.0f} %", ok(tab["du_max"] <= DU_TERMINAL))
    v("Électricité", "Chute de tension TGBT → TD-INFO", f"{fr(tab['feeder_du'])} %", f"≤ {DU_DISTRIBUTION:.0f} %", ok(tab["feeder_du"] <= DU_DISTRIBUTION))
    v("Électricité", "Courant admissible ≥ calibre (tous les départs)", "oui", "Iz ≥ In", ok(all(c["iz"] >= c["In"] for c in circuits)))
    v("Électricité", "Courant de la phase la plus chargée / tête du TD-INFO", f"{tab['i_phase_max']:.0f} A / {tab['In_tete']} A", "≤ 80 %",
      ok(tab["i_phase_max"] <= 0.8 * tab["In_tete"]))
    v("Électricité", "Sélectivité ampèremétrique tête / plus gros départ", f"{fr(tab['selectivite'])}", "≥ 1,6",
      ok(tab["selectivite"] >= 1.6), "en court-circuit : tables du fabricant")
    v("Électricité", f"Réserve de puissance au TGBT ({tab['reserve_kva']} kVA, départ 4P 63 A)", "non connue", "à mesurer", "À vérifier",
      "relevé du disjoncteur général et des intensités du TGBT")
    v("Électricité", "Régime de neutre du bâtiment", "TN-S supposé", "à confirmer", "À vérifier", "les différentiels protègent les personnes dans tous les cas")
    v("Groupe électrogène", "Puissance PRP / besoin (règle onduleurs 1,5 × nominal)", f"{ge['prp']} / {fr(ge['besoin'])} kVA", "PRP ≥ besoin",
      ok(ge["prp"] >= ge["besoin"]))
    v("Groupe électrogène", "Charge réelle maximale", f"{ge['taux_max']:.0f} % PRP", "≤ 80 %", ok(ge["taux_max"] <= 80))
    v("Groupe électrogène", "Charge moyenne pendant une coupure", f"{ge['taux_moy']:.0f} % PRP", "≥ 30 % (encrassement)",
      "OK" if ge["taux_moy"] >= 30 else "OK avec parade", "essai annuel 2 h à 75 % sur banc de charge")
    v("Groupe électrogène", "Plus gros palier de charge (retour des onduleurs)", f"{ge['palier_pct']:.0f} % PRP", "≤ 60 % (classe G2)", ok(ge["palier_pct"] <= 60))
    v("Groupe électrogène", "Autonomie carburant à la charge moyenne (cuve à 75 %)", f"{ge['autonomie_moy']:.0f} h", f"≥ {AUTONOMIE_GE_H} h",
      ok(ge["autonomie_moy"] >= AUTONOMIE_GE_H))
    v("Groupe électrogène", "Autonomie carburant à 75 % de la PRP (cuve à 75 %)", f"{ge['autonomie_75']:.0f} h", f"≥ {AUTONOMIE_GE_75_H} h",
      ok(ge["autonomie_75"] >= AUTONOMIE_GE_75_H))
    v("Groupe électrogène", "Prise de charge / autonomie des onduleurs", f"≈ 15 s / {ond['autonomie_normal']} min", "15 s ≪ autonomie", "OK")
    v("Groupe électrogène", "Chute de tension GE → inverseur", f"{fr(ge['cable_du'])} %", f"≤ {DU_DISTRIBUTION:.0f} %", ok(ge["cable_du"] <= DU_DISTRIBUTION))
    v("Groupe électrogène", "Déclenchement des protections sur GE (Icc ≈ 3 In)", f"≈ {ge['icc']:.0f} A", "étude du fournisseur", "À vérifier",
      "AREP/PMG exigé au CCTP ; différentiels sur tous les départs")
    v("Groupe électrogène", "Emplacement (façade est, accès camion, distance aux prises d'air)", "proposé", "visite du site", "À vérifier")
    return V


# ---------------------------------------------------------------------------
# Production : CSV, figure, document
# ---------------------------------------------------------------------------
CSS_BET = """
.v21 { display: inline-block; padding: 0 1.2mm; border-radius: 1mm; background: #05893e; color: #fff; font-size: 6.8pt; font-weight: bold; vertical-align: 1px; }
.entete { display: flex; justify-content: space-between; align-items: flex-end; padding-bottom: 2.5mm; border-bottom: 1px solid #DEDAD1; margin-bottom: 5mm; }
.entete img { width: auto; height: 10mm; border: 0; margin: 0; }
.entete .ref { text-align: right; color: #6C6861; font-size: 7.6pt; line-height: 1.35; }
.cartouche { display: grid; grid-template-columns: 1.1fr 0.7fr 1fr 1.6fr; border: 1px solid #DEDAD1; margin: 3mm 0 4mm; }
.cartouche div { padding: 1.6mm 2.5mm; border-right: 1px solid #E8E5DE; font-size: 7.4pt; color: #6C6861; }
.cartouche div:last-child { border-right: 0; }
.cartouche b { display: block; color: #211F1C; font-size: 8.6pt; margin-top: .4mm; }
.statut { display: inline-block; padding: 0 1.4mm; border-radius: 1mm; font-size: 7pt; font-weight: bold; white-space: nowrap; color: #fff; }
.s-ok { background: #05893e; } .s-cor { background: #1F4E8C; } .s-av { background: #ab7400; } .s-nok { background: #c13c3b; } .s-par { background: #6C8C2C; }
.fiche { border: 1px solid #DEDAD1; border-top: 3px solid #1F4E8C; padding: 1mm 3mm 2mm; margin: 4mm 0; }
.fiche h3 { margin-top: 2mm; }
.verdict { border-left: 3px solid #05893e; background: #F1F8F3; padding: 1.8mm 3mm; margin: 2mm 0; }
.verdict.renf { border-left-color: #1F4E8C; background: #EAF0F8; }
.grille2 { display: grid; grid-template-columns: 1fr 1fr; gap: 4mm; }
td.tot, tr.tot td { font-weight: bold; background: #F6F4EF; }
.petit { font-size: 7.4pt; }
table.inv td, table.inv th { padding: 0.9mm 1.4mm; }
table.kv td { padding: 1mm 1.6mm; }
table.kv td:first-child { width: 52%; }
table.kv td.v { text-align: right; }
.fiche.court { break-inside: avoid; }
"""
STATUT_CLASSE = {"OK": "s-ok", "Corrigé v2.1": "s-cor", "À vérifier": "s-av", "NOK": "s-nok", "OK avec parade": "s-par"}


def statut(s_):
    return f"<span class='statut {STATUT_CLASSE[s_]}'>{e(s_)}</span>"


def ecrire_csv(etd, lt):
    lignes = list(etd["salle"]["inventaire"])
    for l in lt:
        lignes += l["bet"]["inventaire"]
    champs = ["local", "repere", "modele", "quantite", "w_abs_typ", "w_abs_max", "w_dis_typ", "w_dis_max", "btu_typ", "btu_max", "alimentation", "note"]
    with open(OUT / "bet_dissipation.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=champs)
        w.writeheader()
        for l in lignes:
            w.writerow({k: l[k] for k in champs})
        # une ligne de total par local (les appareils PoE ne sont pas additionnés : leur énergie est dans la ligne « PoE »)
        totaux = [("Salle serveur", etd["salle"]["inventaire"])] + [(l["local"], l["bet"]["inventaire"]) for l in lt]
        q_pte = etd["salle"]["thermique"]["q_pointe"]
        for nom, inv in totaux:
            loc = [x for x in inv if x["alimentation"] != "PoE (hors local)"]
            wt, wm = sum(x["w_dis_typ"] for x in loc), sum(x["w_dis_max"] for x in loc)
            w.writerow(dict(local=nom, repere="TOTAL", modele="Total dissipé dans le local (pointe : intervention, éclairage, été)", quantite="",
                            w_abs_typ=round(sum(x["w_abs_typ"] for x in loc), 1), w_abs_max=round(sum(x["w_abs_max"] for x in loc), 1),
                            w_dis_typ=round(wt, 1), w_dis_max=round(wm, 1), btu_typ=round(wt * BTU), btu_max=round(wm * BTU), alimentation="",
                            note=(f"somme des maxima ; pointe réaliste retenue pour la clim : {q_pte:.0f} W (informatique à 80 %)" if nom == "Salle serveur" else "")))


def figure_montee(etd, lt):
    import matplotlib.pyplot as plt
    th = etd["salle"]["thermique"]
    xmax, ymin, ymax = 30, 24, 48
    t = [i * 0.25 for i in range(0, 4 * xmax + 1)]
    fig, ax = plt.subplots(figsize=(9.6, 4.4))
    # Palette catégorielle validée (ordre fixe) ; contraste faible des teintes 3-4 compensé par les étiquettes directes et les tableaux
    serie = [("#2a78d6", "Salle serveur (2 climatiseurs à l'arrêt)", courbe(th["q_typ"], th["C_kJ"] * 1000, th["UA"], T_CONSIGNE, T_AMB_ETE["N-1"], t))]
    chauds = sorted(lt, key=lambda l: -l["bet"]["panne"]["t_inf"])[:3]
    for col, l in zip(("#eb6834", "#1baf7a", "#eda100"), chauds):
        b, p = l["bet"], l["bet"]["panne"]
        serie.append((col, f"{l['local']} ({b['solution_court']} à l'arrêt)", courbe(b["dissipation_max"], p["C_kJ"] * 1000, p["UA"], p["t0"], b["t_amb"], t)))
    etiquettes = []
    for col, nom, y in serie:
        ax.plot(t, y, color=col, lw=2, label=nom)
        ax.plot([t[-1]], [y[-1]], marker="o", ms=4, color=col)
        etiquettes.append([y[-1], nom, col])
    etiquettes.sort(key=lambda x: x[0])
    for i in range(1, len(etiquettes)):  # écarte les étiquettes qui se chevauchent
        etiquettes[i][0] = max(etiquettes[i][0], etiquettes[i - 1][0] + 1.1)
    for y, nom, col in etiquettes:
        ax.text(xmax + 0.6, y, nom, color="#3A3833", fontsize=7, va="center")
    for s_, lab in ((T_CRITIQUE, "35 °C : limite A2"), (T_LIMITE, "40 °C : limite de fonctionnement")):
        ax.axhline(s_, color="#8C8880", lw=0.9, ls=":")
        ax.text(0.3, s_ + 0.25, lab, fontsize=7, color="#6C6861", bbox=dict(fc="white", ec="none", pad=0.5))
    ax.axvline(FIN_ARRET_MIN, color="#8C8880", lw=0.9, ls=":")
    ax.text(FIN_ARRET_MIN + 0.3, ymin + 0.4, f"fin de l'arrêt ordonné (T0 + {FIN_ARRET_MIN} min)", fontsize=7, color="#6C6861")
    ax.legend(loc="upper left", fontsize=7, frameon=False)
    ax.set_xlim(0, xmax)
    ax.set_ylim(ymin, ymax)
    ax.set_xlabel("minutes après l'arrêt du refroidissement")
    ax.set_ylabel("température de l'air (°C)")
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    ax.spines["left"].set_color("#BDB8AE")
    ax.spines["bottom"].set_color("#BDB8AE")
    ax.grid(axis="y", color="#ECE9E2", lw=0.6)
    ax.set_title("Montée en température sans refroidissement (été, charge permanente)", loc="left", fontsize=10, weight="bold", family="DejaVu Serif")
    fig.subplots_adjust(right=0.7)
    (OUT / "schemas").mkdir(parents=True, exist_ok=True)
    for ext in ("png", "svg"):
        fig.savefig(OUT / "schemas" / f"montee_temperature.{ext}", dpi=170 if ext == "png" else None, bbox_inches="tight")
    plt.close(fig)


def tableau_inventaire(inv, pointe=None):
    H = ["<table class='petit inv'><colgroup><col style='width:10%'><col style='width:26%'><col style='width:4%'><col span='5' style='width:7.6%'>"
         "<col style='width:22%'></colgroup><tr><th>Repère</th><th>Équipement</th><th class='n'>Qté</th><th class='n'>Absorbé typ.</th><th class='n'>Absorbé max.</th>"
         "<th class='n'>Dissipé typ.</th><th class='n'>Dissipé max.</th><th class='n'>BTU/h max.</th><th>Remarque</th></tr>"]
    for l in inv:
        hors = l["alimentation"] == "PoE (hors local)"
        st = " style='color:#6C6861'" if hors else ""
        H.append(f"<tr{st}><td>{e(str(l['repere']))}</td><td>{e(l['modele'])}</td><td class='n'>{l['quantite']}</td>"
                 f"<td class='n'>{fr(l['w_abs_typ'], 0)} W</td><td class='n'>{fr(l['w_abs_max'], 0)} W</td>"
                 f"<td class='n'>{fr(l['w_dis_typ'], 0)} W</td><td class='n'>{fr(l['w_dis_max'], 0)} W</td><td class='n'>{fr(l['btu_max'], 0)}</td>"
                 f"<td class='chemin'>{e(l['note'])}</td></tr>")
    loc = [x for x in inv if x["alimentation"] != "PoE (hors local)"]
    wt, wm = sum(x["w_dis_typ"] for x in loc), sum(x["w_dis_max"] for x in loc)
    H.append(f"<tr class='tot'><td colspan='5'>Total dissipé dans le local (typique · pointe été avec intervention)</td>"
             f"<td class='n'>{fr(wt, 0)} W</td><td class='n'>{fr(wm, 0)} W</td><td class='n'>{fr(wm * BTU, 0)}</td><td></td></tr>")
    if pointe:
        H.append(f"<tr class='tot'><td colspan='6'>Pointe réaliste retenue pour la climatisation (informatique à 80 % des maxima, tout le reste au maximum)</td>"
                 f"<td class='n'>{fr(pointe, 0)} W</td><td class='n'>{fr(pointe * BTU, 0)}</td><td></td></tr>")
    H.append("</table>")
    return "".join(H)


def tableau_circuits(cs):
    H = ["<table class='petit'><tr><th>Départ</th><th>Circuit</th><th>Ph.</th><th class='n'>P max.</th><th class='n'>I réel</th><th class='n'>I<sub>B</sub></th>"
         "<th class='n'>Calibre</th><th>Différentiel</th><th class='n'>L</th><th class='n'>Section</th><th class='n'>I<sub>z</sub></th><th class='n'>ΔU</th></tr>"]
    for c in cs:
        H.append(f"<tr><td>{c['repere']}</td><td>{e(c['nom'])}</td><td>{c['phase']}</td><td class='n'>{fr(c['p_w'], 0)} W</td>"
                 f"<td class='n'>{fr(c['i_reel'])} A</td><td class='n'>{fr(c['i_b'])} A</td><td class='n'>{c['In']} A {c['courbe']}</td><td>{e(c['diff'])}</td>"
                 f"<td class='n'>{c['L']:.0f} m</td><td class='n'>{fr(c['section'])} mm²</td><td class='n'>{c['iz']:.0f} A</td><td class='n'>{fr(c['du'])} %</td></tr>")
    H.append("</table>")
    return "".join(H)


def document(ctx, etd, fin):
    lt, ond, clim, en, s = ctx["lt"], ctx["ond"], ctx["clim"], ctx["en"], ctx["s"]
    th, cs, tab, ge = etd["salle"]["thermique"], etd["salle"]["charge"], etd["tableau"], etd["ge"]
    css = ctx["css"] + CSS_BET
    V = etd["verifs"]
    n_ok = sum(v["statut"] in ("OK", "Corrigé v2.1", "OK avec parade") for v in V)
    n_av = sum(v["statut"] == "À vérifier" for v in V)
    n_nok = sum(v["statut"] == "NOK" for v in V)
    renf = [l for l in lt if not l["bet"]["v2_ok"]]
    circ = {c["repere"]: c for c in etd["circuits"]}
    lignes_ge = [l for l in fin["nouveaux"] if l.get("ge")]
    capex_ge = sum(l["total_ht"] for l in lignes_ge)
    opex_ge = sum(m for p, _, m in fin["opex"] if "électrogène" in p or "banc de charge" in p or "Gazole" in p)
    H = [f"<!doctype html><html lang='fr'><head><meta charset='utf-8'><title>BET des locaux techniques</title><style>{css}</style></head><body>",
         "<div class='entete'><img src='../communication/logo/rudylink-infrastructure-couleur.svg' alt='RudyLink Infrastructure'>"
         f"<div class='ref'>Note de calcul BET fluides et courants forts<br>{REF} · version 2.1 · {DATE_V21}</div></div>",
         "<h1>Bilan thermique et électrique des locaux techniques</h1>",
         f"<p class='sous'>Site de Marseille · IUT Génie Télécom, Luminy · RudyLink Infrastructure · {REF} · version 2.1 · {DATE_V21}<br>"
         "Salle serveur, 6 locaux techniques, tableau informatique, TGBT et groupe électrogène : inventaire, chaleur, ventilation, circuits, "
         "secours. Complète le document principal <code>energie_refroidissement.pdf</code> (point 14).</p>",
         "<div class='cartouche'><div>Référence<b>" + REF + "</b></div><div>Version<b>2.1</b></div><div>Statut<b>Pour validation client</b></div>"
         "<div>Rédigé par<b>BET fluides / courants forts, RudyLink Infrastructure</b></div></div>",
         "<div class='cles'>",
         f"<div class='cle'><b>{n_ok}/{len(V)}</b>vérifications conformes ({n_av} à vérifier sur site, {n_nok} non conforme)</div>",
         f"<div class='cle'><b>{len(renf)} L.TECH</b>renforcés en v2.1 (ventilation sous-dimensionnée en été)</div>",
         f"<div class='cle'><b>GE {ge['esp']} kVA</b>ESP ({ge['prp']} kVA PRP), {ge['autonomie_moy']:.0f} h d'autonomie</div>",
         f"<div class='cle'><b>{tab['reserve_kva']} kVA</b>à réserver au TGBT pour le lot informatique</div></div>"]
    # 1. Synthèse
    H += ["<h2>1. Synthèse : l'infrastructure énergétique tient-elle la route ?</h2>",
          f"<div class='verdict'><b>Oui, après les corrections de la v2.1.</b> Les onduleurs, la climatisation de la salle serveur et les circuits "
          f"électriques de la v2 étaient bien dimensionnés. Trois points ne tenaient pas : la ventilation de {len(renf)} locaux techniques en été "
          f"({', '.join(l['local'] for l in renf)}), les pertes réelles des onduleurs à faible charge (sous-estimées, PUE trop optimiste) et "
          f"l'absence de secours long (le client confirme qu'il n'y a pas de groupe électrogène sur le site). Ils sont corrigés dans les sources "
          f"et dans le chiffrage. Restent {n_av} points à vérifier sur site, surtout la réserve de puissance du TGBT et l'emplacement du groupe.</div>",
          "<h3>Les locaux en un tableau</h3><table><tr><th>Local</th><th>Niveau</th><th class='n'>Surface</th><th class='n'>Puissance élec. max.</th>"
          "<th class='n'>Dissipé typ.</th><th class='n'>Pointe été</th><th>Refroidissement retenu</th><th class='n'>T été</th><th>Verdict</th></tr>",
          f"<tr><td><b>Salle serveur</b></td><td>N-1</td><td class='n'>{SURFACE_SALLE:.0f} m²</td>"
          f"<td class='n'>{fr((s['it_pointe'] + cs['pertes_pointe'] + 2 * RECHARGE_SRT_W + cs['eclairage'] + cs['aux']) / 1000 + 2 * P_CLIM_MAX_KW, 1)} kW</td>"
          f"<td class='n'>{fr(th['q_typ'], 0)} W</td><td class='n'>{fr(th['q_pointe'], 0)} W</td><td>2 climatiseurs {fr(clim['unite_kw'])} kW (N+1), allée froide</td>"
          f"<td class='n'>{T_CONSIGNE:.0f} °C</td><td>{statut('OK')}</td></tr>"]
    for l in lt:
        b = l["bet"]
        p_el = (b["charge_max"] + b["pertes_ond_max"] + RECHARGE_SMT_W + b["elec_vent_max"]) / 1000
        H.append(f"<tr><td><b>{l['local']}</b> <span class='chemin'>{e(l['salle'])}</span></td><td>{l['local'].rsplit('-', 1)[0]}</td>"
                 f"<td class='n'>{fr(l['surface'])} m²</td><td class='n'>{fr(p_el, 2)} kW</td><td class='n'>{fr(b['dissipation_typ'], 0)} W</td>"
                 f"<td class='n'>{fr(b['p_dim'], 0)} W</td><td>{e(b['solution_court'])}{'' if b['v2_ok'] else ' ' + V21}</td>"
                 f"<td class='n'>{fr(b['t_ete'])} °C</td><td>{statut('OK') if b['v2_ok'] else statut('Corrigé v2.1')}</td></tr>")
    H.append(f"<tr><td><b>TD-INFO + inverseur</b></td><td>N-1</td><td class='n'>—</td><td class='n'>{fr(tab['s_max'] / 1000, 1)} kVA</td>"
             f"<td class='n'>{TD_PERTES_W} W</td><td class='n'>{TD_PERTES_W} W</td><td>dans la salle serveur (compté dans sa clim)</td><td class='n'>—</td><td>{statut('OK')}</td></tr>")
    H.append(f"<tr><td><b>Groupe électrogène</b> {V21}</td><td>extérieur</td><td class='n'>≈ 6 m²</td><td class='n'>{ge['prp']} kVA PRP</td>"
             f"<td class='n'>—</td><td class='n'>—</td><td>capot insonorisé, radiateur intégré (extérieur)</td><td class='n'>—</td>"
             f"<td>{statut('À vérifier')}</td></tr>")
    H.append(f"<tr><td><b>TGBT existant</b></td><td>N0</td><td class='n'>27 m²</td><td class='n'>+{tab['reserve_kva']} kVA</td><td class='n'>—</td>"
             f"<td class='n'>—</td><td>local électrique existant</td><td class='n'>—</td><td>{statut('À vérifier')}</td></tr></table>"
             "<p class='sous'>Puissance électrique maximale : tout au maximum (PoE à la classe, recharge des batteries, deux climatiseurs en marche après une coupure). "
             "Dissipé : chaleur restant dans le local (le PoE est dissipé chez les bornes et caméras). Pointe été : dissipé maximal + technicien + éclairage + toiture. "
             f"T été : température de l'air du local avec l'air des circulations à {T_AMB_ETE['N-1']:.0f} °C (sous-sol), {T_AMB_ETE['N0']:.0f} °C (RDC), "
             f"{T_AMB_ETE['N1']:.0f} °C (étage sous toiture).</p>")
    H += ["<h3>Corrections apportées en v2.1</h3><table><tr><th>Point</th><th>v2 (15/11/2026)</th><th>v2.1 (20/11/2026)</th><th>Pourquoi</th></tr>"]
    for l in renf:
        b = l["bet"]
        H.append(f"<tr><td>Ventilation {l['local']}</td><td>{e(b['v2_court'])} : {fr(b['t_v2'])} °C en été</td><td><b>{e(b['solution_court'])}</b> : "
                 f"{fr(b['t_ete'])} °C</td><td>{fr(b['p_dim'], 0)} W à évacuer avec de l'air à {b['t_amb']:.0f} °C : critère {T_MAX_LT:.0f} °C "
                 "(onduleur limité à 40 °C, batteries)</td></tr>")
    H += [f"<tr><td>Pertes des onduleurs de la salle</td><td>rendement fixe 95 %</td><td>{fr(cs['pertes_typ'], 0)} W (≈ 92 % à {ond['taux_normal']} % de charge)</td>"
          "<td>En 2N, chaque onduleur tourne au tiers de sa puissance, où son rendement est plus faible</td></tr>",
          f"<tr><td>Auxiliaires de la salle</td><td>non comptés</td><td>{cs['aux'] + TD_PERTES_W} W (VESDA, extinction, badge, sondes, tableau)</td>"
          "<td>Chaleur et consommation réelles, comptées dans la clim et le PUE</td></tr>",
          f"<tr><td>Secours long</td><td>aucun : arrêt ordonné à T0 + 5 min</td><td><b>GE {ge['esp']} kVA ESP + inverseur automatique</b> ; "
          f"arrêt ordonné seulement si le GE n'a pas repris à T0 + {ARRET_GE_ABSENT_MIN} min</td><td>Le client confirme qu'il n'y a pas de GE sur le site</td></tr>",
          "<tr><td>Protections différentielles</td><td>« protections différentielles »</td><td>type B (onduleurs en ligne), F (clim, ventilateurs), "
          "A SI (onduleurs des L.TECH), coffret par L.TECH</td><td>Redresseurs PFC et variateurs : fuites HF et composante continue</td></tr>",
          "<tr><td>Batteries des onduleurs des L.TECH</td><td>remplacement tous les 5 ans</td><td>tous les 4 ans</td>"
          "<td>Locaux à 28-33 °C l'été : la durée de vie d'une batterie plomb est divisée par 2 tous les +10 K au-dessus de 20-25 °C</td></tr></table>"]
    # 2. Hypothèses
    H += ["<h2 class='saut'>2. Hypothèses</h2><table><tr><th>Paramètre</th><th>Valeur</th><th>Justification</th></tr>",
          f"<tr><td>Consigne de la salle serveur</td><td>{T_CONSIGNE:.0f} °C à l'entrée des équipements</td><td>ASHRAE A1 recommandé 18-27 °C ; alarme {T_ALARME:.0f} °C, "
          f"arrêt ordonné {T_CRITIQUE:.0f} °C (limite A2), limite des onduleurs et de la plupart des équipements {T_LIMITE:.0f} °C</td></tr>",
          f"<tr><td>Air des circulations en été</td><td>N-1 {T_AMB_ETE['N-1']:.0f} °C · N0 {T_AMB_ETE['N0']:.0f} °C · N1 {T_AMB_ETE['N1']:.0f} °C ; canicule +{CANICULE_K:.0f} K</td>"
          "<td>Bâtiment non climatisé à Marseille ; sous-sol enterré frais ; étage sous toiture-terrasse plus chaud. Air repris par les grilles ou l'extracteur</td></tr>",
          f"<tr><td>Critère des locaux techniques</td><td>≤ {T_MAX_LT:.0f} °C en été, ≤ {T_LIMITE:.0f} °C en canicule</td><td>Onduleur SMT : 0-40 °C ; switch C9200L : "
          "jusqu'à 45 °C ; batteries : vieillissement accéléré au-delà de 25 °C</td></tr>",
          f"<tr><td>Apports par les parois</td><td>{APPORT_PAROIS_W_M2['N1']:.0f} W/m² sous toiture (N1), 0 ailleurs</td><td>Toiture-terrasse isolée (U ≈ 0,4) "
          "et écart soleil-air ≈ 25 K ; locaux intérieurs entourés de circulations à température voisine ; sous-sol : pertes vers le sol négligées</td></tr>",
          f"<tr><td>Éclairage, occupant</td><td>{ECLAIRAGE_W_M2:.0f} W/m² LED ; {OCCUPANT_W:.0f} W sensibles</td><td>Ponctuels (intervention) : comptés dans la pointe, "
          "pas dans le régime permanent</td></tr>",
          "<tr><td>Puissance des équipements</td><td>fiches constructeur (typique / maximale)</td><td>Pointe réaliste de la salle : 80 % de la somme des maxima ; "
          "switch des L.TECH 55 W typ. / 65 W max. hors PoE</td></tr>",
          "<tr><td>PoE</td><td>typique : Wi-Fi 13 W, caméra 6 W, badge 4 W, téléphone 4 W ; max. : classe réservée</td><td>La puissance PoE est dissipée chez "
          "l'appareil ; seules les pertes de conversion du switch (rendement 90 %) chauffent le local</td></tr>",
          "<tr><td>Pertes des onduleurs</td><td>SRT 6 kVA en ligne : 100 W + 3 % ; SMT 1500 line-interactive : 12 W + 2 %</td><td>Ordres de grandeur des courbes de "
          "rendement constructeur (92 % à 30 % de charge, 95 % à pleine charge pour le SRT)</td></tr>",
          f"<tr><td>Ventilation naturelle</td><td>2 grilles 600 × 200 mm (section libre 50 %), {H_GRILLES} m d'écart, C<sub>d</sub> {CD}</td>"
          "<td>Tirage thermique entre la grille basse (porte) et la grille haute (imposte)</td></tr>",
          f"<tr><td>Inertie en panne de refroidissement</td><td>air + {FRACTION_MASSE:.0%} de la masse des baies ({C_MASSE:.0f} J/kg·K), cloisons U = {U_PAROI} W/m²·K</td>"
          "<td>Borne pessimiste également donnée : air seul, parois adiabatiques, puissance de pointe</td></tr>",
          f"<tr><td>Climatiseurs de la salle</td><td>{fr(clim['unite_kw'])} kW, part sensible {SHR_CLIM:.0%}, {DEBIT_CLIM_M3H:.0f} m³/h, {P_CLIM_MAX_KW} kW absorbés max.</td>"
          "<td>Climatiseur technique (salle sèche) ; kit basse température pour fonctionner l'hiver</td></tr>",
          "<tr><td>Régime de neutre, TGBT</td><td>TN-S supposé ; TGBT au RDC (local PL.ELEC, 27 m²)</td><td>Bâtiment alimenté par un poste HTA/BT du campus : "
          "<b>à confirmer</b> avec les services techniques</td></tr>",
          f"<tr><td>Câbles</td><td>U1000 R2V sur chemin de câbles, méthode E, facteur {K_POSE}</td><td>NF C 15-100 / IEC 60364-5-52 ; ΔU ≤ {DU_TERMINAL:.0f} % par départ, "
          f"≤ {DU_DISTRIBUTION:.0f} % pour les liaisons de distribution (total ≤ 5 %)</td></tr>",
          f"<tr><td>Groupe électrogène</td><td>diesel 400 V, gamme {', '.join(str(g[0]) for g in GE_GAMME)} kVA PRP, {fr(PRIX_GAZOLE, 2)} € HT/l</td>"
          "<td>NF ISO 8528-1 (PRP : puissance continue à charge variable ; ESP : secours), prix et consommations : fiches et tarifs distributeurs, ordre de grandeur</td></tr></table>"]
    # 3. Fiches
    H += ["<h2 class='saut'>3. Fiches par local</h2>"]
    # 3.1 Salle serveur
    q1, q2 = circ["Q1"], circ["Q3"]
    H += ["<div class='fiche'><h3>3.1 Salle serveur (partie sud de J05, sous-sol, 25 m²)</h3>",
          "<p><b>Inventaire.</b> Tous les équipements sont dans la salle : 100 % de leur puissance devient chaleur dans la salle.</p>",
          tableau_inventaire(etd["salle"]["inventaire"], pointe=th["q_pointe"]),
          "<p><b>Bilan thermique.</b></p><table><tr><th>Grandeur</th><th class='n'>Valeur</th><th>Commentaire</th></tr>",
          f"<tr><td>Charge typique · pointe</td><td class='n'>{fr(th['q_typ'] / 1000, 2)} · {fr(th['q_pointe'] / 1000, 2)} kW</td>"
          f"<td>{fr(th['q_typ'] * BTU, 0)} · {fr(th['q_pointe'] * BTU, 0)} BTU/h</td></tr>",
          f"<tr><td>Puissance sensible d'un climatiseur</td><td class='n'>{fr(th['sensible'])} kW</td><td>une unité porte la pointe à {th['taux_unite']:.0f} % ; "
          "l'autre est en secours (N+1), alternance hebdomadaire</td></tr>",
          f"<tr><td>Débit d'air d'une unité · besoin des équipements</td><td class='n'>{DEBIT_CLIM_M3H:.0f} · {th['debit_it']:.0f} m³/h</td>"
          f"<td>besoin pour ΔT = {DT_SERVEURS:.0f} K à travers les serveurs ; écart soufflage-reprise {fr(th['dt_clim'])} K en pointe</td></tr>",
          f"<tr><td>Régime établi</td><td class='n'>{T_CONSIGNE:.0f} °C</td><td>allée froide confinée ; reprise chaude ≈ {T_CONSIGNE + DT_SERVEURS:.0f} °C</td></tr>",
          f"<tr><td>Panne des 2 climatiseurs : 35 °C · 40 °C</td><td class='n'>{duree(th['t35'])} · {duree(th['t40'])}</td>"
          f"<td>air {fr(th['vol'], 0)} m³ + {FRACTION_MASSE:.0%} de {th['masse']:.0f} kg de baies et d'équipements ; borne pessimiste (air seul) : "
          f"{duree(th['t35_air'])} · {duree(th['t40_air'])}</td></tr>",
          f"<tr><td>Coupure secteur avec GE : {RELANCE_CLIM_S // 60} min sans froid</td><td class='n'>{fr(th['t_relance'])} °C</td>"
          f"<td>borne pessimiste {fr(th['t_relance_air'])} °C ; les climatiseurs ne sont pas ondulés (inutile)</td></tr>",
          f"<tr><td>Coupure sans GE : à la fin de l'arrêt ordonné</td><td class='n'>{fr(th['t_arret'])} °C</td><td>T0 + {FIN_ARRET_MIN} min ; seuls les switchs "
          "et pare-feu restent ensuite en marche</td></tr></table>",
          "<p><b>Bilan électrique.</b> Deux onduleurs en ligne, deux voies A/B, deux climatiseurs, éclairage, prises et auxiliaires : 7 départs du TD-INFO.</p>",
          "<table><tr><th>Grandeur</th><th class='n'>Valeur</th><th>Seuil</th></tr>",
          f"<tr><td>Charge d'un onduleur, marche normale</td><td class='n'>{fr(ond['normal'], 0)} W · {ond['taux_normal']} %</td><td>≤ 80 %</td></tr>",
          f"<tr><td>Charge d'un onduleur seul, en pointe</td><td class='n'>{fr(ond['degrade_pointe'], 0)} W · {ond['taux_degrade']} %</td><td>≤ 90 %</td></tr>",
          f"<tr><td>Autonomie : 2 onduleurs · 1 onduleur · 1 onduleur en fin de vie</td><td class='n'>{ond['autonomie_normal']} · {ond['autonomie_degrade']} · "
          f"{etd['ond_fin_vie']:.0f} min</td><td>≥ {ARRET_GE_ABSENT_MIN + FIN_ARRET_MIN} min</td></tr>",
          f"<tr><td>Entrée d'un onduleur (I<sub>B</sub> nominal · réel)</td><td class='n'>{fr(q1['i_b'])} · {fr(q1['i_reel'])} A</td>"
          f"<td>départ {q1['In']} A C, {fr(q1['section'])} mm², {e(q1['diff'])}</td></tr>",
          f"<tr><td>Climatiseur (×2)</td><td class='n'>{fr(q2['p_w'] / 1000)} kW · {fr(q2['i_reel'])} A</td><td>départ {q2['In']} A C, {fr(q2['section'])} mm², "
          f"{e(q2['diff'])}</td></tr>",
          f"<tr><td>Puissance de la salle (pointe, recharge, 2 clims)</td><td class='n'>"
          f"{fr((s['it_pointe'] + cs['pertes_pointe'] + 2 * RECHARGE_SRT_W) / 1000 + 2 * P_CLIM_MAX_KW + (cs['eclairage'] + cs['aux']) / 1000, 1)} kW</td>"
          "<td>cos φ ≈ 0,97</td></tr></table>",
          "<div class='verdict'><b>Verdict : conforme.</b> Onduleurs, climatisation et débit d'air ont de la marge. Sans aucun froid, la salle atteint 35 °C en "
          f"{duree(th['t35'])} environ : d'où l'alternance des climatiseurs, l'alarme à {T_ALARME:.0f} °C et l'arrêt ordonné automatique à {T_CRITIQUE:.0f} °C. "
          "Les climatiseurs doivent redémarrer seuls après une coupure (redémarrage automatique activé, temporisations au tableau).</div></div>"]
    # 3.2 LT
    for i, l in enumerate(lt):
        b = l["bet"]
        p = b["panne"]
        c = circ[f"Q{5 + i}"]
        H += [f"<div class='fiche'><h3>3.{2 + i} {l['local']} ({e(l['salle'])}, {fr(l['surface'])} m², baie {e(l.get('baie', ''))})</h3>",
              f"<p><b>Inventaire.</b> {l['switchs']} switch{'s' if l['switchs'] > 1 else ''} PoE+, onduleur 1,5 kVA ; appareils PoE desservis en gris "
              "(leur chaleur n'est pas dans le local).</p>",
              tableau_inventaire(b["inventaire"]),
              "<div class='grille2'><div><p><b>Bilan thermique.</b></p><table class='kv'>",
              f"<tr><td>Dissipé typique · permanent max.</td><td class='v'>{fr(b['dissipation_typ'], 0)} · {fr(b['dissipation_max'], 0)} W</td></tr>",
              f"<tr><td>Pointe été (intervention)</td><td class='v'>{fr(b['p_dim'], 0)} W · {fr(b['p_dim'] * BTU, 0)} BTU/h</td></tr>",
              f"<tr><td>Air des circulations (été)</td><td class='v'>{b['t_amb']:.0f} °C</td></tr>",
              f"<tr><td>Grilles seules</td><td class='v'>{fr(b['grilles_t'])} °C</td></tr>",
              f"<tr><td>Solution v2 · v2.1</td><td class='v'>{e(b['v2_court'])} · <b>{e(b['solution_court'])}</b></td></tr>",
              f"<tr><td>Température été · canicule</td><td class='v'>{fr(b['t_ete'])} · {fr(b['t_canicule'])} °C</td></tr>",
              f"<tr><td>Débit pour ΔT = 10 K (typique)</td><td class='v'>{b['debit_10k']:.0f} m³/h</td></tr>",
              f"<tr><td>Sans ventilation : 35 °C · 40 °C</td><td class='v'>{duree(p['t35'])} · {duree(p['t40'])}</td></tr>",
              f"<tr><td>Température limite sans ventilation</td><td class='v'>{fr(p['t_inf'])} °C</td></tr></table></div>",
              "<div><p><b>Bilan électrique.</b></p><table class='kv'>",
              f"<tr><td>Charge onduleur typ. · max.</td><td class='v'>{fr(b['charge_typ'], 0)} · {fr(b['charge_max'], 0)} W</td></tr>",
              f"<tr><td>Taux de charge (1 000 W) · autonomie</td><td class='v'>{l['taux']} % · {l['autonomie']} min</td></tr>",
              f"<tr><td>Puissance du départ (max.)</td><td class='v'>{fr(c['p_w'] / 1000, 2)} kW · {fr(c['p_w'] / 1000 / 0.95, 2)} kVA</td></tr>",
              f"<tr><td>Courant réel · I<sub>B</sub> (+25 %)</td><td class='v'>{fr(c['i_reel'])} · {fr(c['i_b'])} A</td></tr>",
              f"<tr><td>Départ TD-INFO</td><td class='v'>{c['In']} A C, {c['phase']}, 300 mA A-S</td></tr>",
              f"<tr><td>Câble ({c['L']:.0f} m) · ΔU</td><td class='v'>{fr(c['section'])} mm² · {fr(c['du'])} %</td></tr>",
              f"<tr><td>Coffret du local</td><td class='v'>10 A 30 mA A SI" + (" + 10 A 30 mA F" if b["solution"][0] != "grilles" else "") + "</td></tr>",
              f"<tr><td>Fuite permanente sur le 30 mA</td><td class='v'>≈ {b['fuite_ma']:.0f} mA (≤ 9)</td></tr></table></div></div>"]
        if b["v2_ok"]:
            H.append(f"<div class='verdict'><b>Verdict : conforme.</b> {e(b['solution_libelle']).capitalize()} : {fr(b['t_ete'])} °C au plus chaud de l'été "
                     f"avec un technicien dans le local.</div></div>")
        else:
            H.append(f"<div class='verdict renf'><b>Verdict : à renforcer, corrigé en v2.1.</b> Avec la solution v2 ({e(b['v2_court'])}), le local monterait à "
                     f"{fr(b['t_v2'])} °C en été (critère {T_MAX_LT:.0f} °C). Correction : <b>{e(b['solution_libelle'])}</b>"
                     + (", unité extérieure sur la toiture-terrasse au-dessus du local, condensats vers une descente d'eaux pluviales" if b["solution"][0] == "split"
                        else ", rejet en gaine vers l'extérieur (ou la reprise de la VMC), grille basse dans la porte") + ".</div></div>")
    # 3.x TD-INFO
    H += [f"<div class='fiche saut'><h3>3.8 Tableau informatique TD-INFO et inverseur de source {V21}</h3>",
          "<p>Coffret mural dans la salle serveur, près de la porte, en partie haute (hors d'eau). En tête : l'<b>inverseur de source automatique</b> "
          "(TGBT ou groupe électrogène), puis un interrupteur général 4P 63 A et 13 départs. Ses pertes (≈ 40 W) sont comptées dans la clim de la salle.</p>",
          tableau_circuits(etd["circuits"]),
          "<p class='sous'>I réel : courant au maximum réel ; I<sub>B</sub> : courant d'emploi retenu pour la section (onduleurs : entrée à 6 kW + recharge ; "
          "L.TECH : +25 % de réserve). Section : plus petite section telle que I<sub>z</sub> ≥ calibre et ΔU ≤ 3 %. Iz : méthode E, facteur 0,7.</p>",
          "<table><tr><th>Phase</th>" + "".join(f"<th class='n'>{k}</th>" for k in sorted(tab["phases"])) + "<th>Commentaire</th></tr><tr><td>Courant max. réel</td>"
          + "".join(f"<td class='n'>{fr(v)} A</td>" for _, v in sorted(tab["phases"].items()))
          + f"<td>onduleurs comptés à leur charge maximale réelle (l'autre en panne) ; tête 63 A chargée à {100 * tab['i_phase_max'] / 63:.0f} %</td></tr></table>",
          "<p><b>Différentiels.</b> Onduleurs en ligne : <b>type B</b> 300 mA sélectif (le redresseur PFC peut produire un courant de défaut continu lissé, "
          "NF EN 62040-1 ; à confirmer sur la notice). Climatiseurs et ventilateurs à variateur : <b>type F</b> 30 mA. Onduleurs line-interactive et "
          "alimentations à découpage des L.TECH : <b>type A SI</b> (super-immunisé) 30 mA dans le coffret du local, 300 mA type A sélectif en tête du départ. "
          "Le type AC est exclu partout.</p>",
          f"<p><b>Sélectivité.</b> TGBT (départ 4P 63 A, disjoncteur réglable) → inverseur → interrupteur général 63 A → départs ≤ 32 A : rapport "
          f"{fr(tab['selectivite'])} en surcharge. En court-circuit, sélectivité totale à vérifier sur les tables du fabricant (amont courbe D ou boîtier moulé). "
          "Différentiels : 300 mA sélectifs (S) en amont, 30 mA instantanés en aval.</p>",
          "<div class='verdict'><b>Verdict : conforme</b>, sous réserve de l'étude de sélectivité du fabricant retenu.</div></div>"]
    # 3.x TGBT
    H += [f"<div class='fiche court'><h3>3.9 TGBT existant du bâtiment</h3>",
          f"<p>Le bâtiment existe : on ne remplace pas son tableau général, on lui demande <b>un départ 4P 63 A</b> et une <b>réserve de {tab['reserve_kva']} kVA</b> "
          f"(puissance maximale appelée {fr(tab['s_max'] / 1000)} kVA + {MARGE_EVOLUTION - 1:.0%} d'évolution ; puissance courante ≈ {fr(tab['p_moy'] / 1000)} kW).</p>",
          "<table><tr><th>Grandeur</th><th class='n'>Valeur</th><th>Commentaire</th></tr>",
          f"<tr><td>Liaison TGBT → inverseur</td><td class='n'>5G{tab['feeder_section']:g} mm², {L_TGBT_TD:.0f} m</td><td>I<sub>B</sub> {fr(tab['feeder_i'])} A, "
          f"ΔU {fr(tab['feeder_du'])} % (≤ 2 %)</td></tr>",
          f"<tr><td>Courant par phase (triphasé équilibré)</td><td class='n'>≈ {fr(tab['s_max'] / (math.sqrt(3) * 400))} A</td><td>phase la plus chargée "
          f"{fr(tab['i_phase_max'])} A (monophasés)</td></tr>",
          f"<tr><td>Impact sur l'abonnement</td><td class='n'>+{tab['reserve_kva']} kVA</td><td>hypothèse : puissance souscrite gérée au niveau du campus (contrat HTA "
          f"d'AMU), ajout négligeable devant un poste HTA/BT. Si le bâtiment avait son propre contrat BT &gt; 36 kVA : ≈ {eur(tab['cout_kva'])} HT/an de part fixe "
          f"({TARIF_KVA_AN:.0f} €/kVA/an, ordre de grandeur), non retenu au chiffrage</td></tr>",
          "<tr><td>Auxiliaires du GE (réchauffeur, chargeur)</td><td class='n'>16 A</td><td>départ du TGBT côté réseau normal (inutile en secours)</td></tr></table>",
          "<div class='verdict renf'><b>Verdict : à vérifier sur site.</b> Relever le calibre et le réglage du disjoncteur général, les intensités maximales "
          "mesurées et la place disponible ; confirmer le régime de neutre.</div></div>"]
    # 4. GE
    H += [f"<h2 class='saut'>4. Groupe électrogène {V21}</h2>",
          "<p>Le client confirme qu'il n'y a <b>pas de groupe électrogène</b> sur le site. En v2, une coupure de plus de 5 minutes arrêtait la salle serveur ; "
          f"les locaux techniques tombaient après {min(l['autonomie'] for l in lt)} min à {max(l['autonomie'] for l in lt) / 60:.0f} h selon leur charge. "
          "La v2.1 intègre un groupe dédié au lot informatique.</p>",
          "<h3>4.1 Périmètre secouru</h3><ul>",
          "<li><b>Secouru</b> (tout le TD-INFO, l'inverseur est en tête du tableau) : les 2 onduleurs de la salle, les 2 climatiseurs, les 6 locaux techniques "
          "(Wi-Fi, téléphonie IP, badgeuses et caméras restent en service), l'éclairage, les prises de service et les auxiliaires de sécurité de la salle.</li>",
          "<li><b>Non secouru</b> : le reste du bâtiment (postes, éclairage des salles, chauffage). Les blocs d'éclairage de sécurité (BAES) sont autonomes ; "
          "le système de sécurité incendie du bâtiment a sa propre source. Le groupe n'est donc <b>pas une source de sécurité</b> au sens du règlement ERP, "
          "mais une source de remplacement.</li></ul>",
          "<h3>4.2 Dimensionnement (NF ISO 8528)</h3><table><tr><th>Charge secourue</th><th class='n'>kW</th><th class='n'>cos φ</th><th class='n'>kVA</th>"
          "<th class='n'>Coef.</th><th class='n'>kVA pondérés</th><th>Remarque</th></tr>"]
    for r in ge["charges"]:
        H.append(f"<tr><td>{e(r['nom'])}</td><td class='n'>{fr(r['kw'], 2)}</td><td class='n'>{fr(r['cos'], 2)}</td><td class='n'>{fr(r['kva'], 2)}</td>"
                 f"<td class='n'>{fr(r['coef'], 2)}</td><td class='n'>{fr(r['kva_pond'], 2)}</td><td class='chemin'>{e(r['note'])}</td></tr>")
    H += [f"<tr class='tot'><td>Total réel (sans coefficient)</td><td class='n'>{fr(ge['reel_kw'], 1)}</td><td></td><td class='n'>{fr(ge['reel_kva'], 1)}</td>"
          f"<td></td><td class='n'>{fr(sum(r['kva_pond'] for r in ge['charges']), 1)}</td><td></td></tr></table>",
          "<table><tr><th>Méthode</th><th class='n'>Besoin</th><th>Détail</th></tr>",
          f"<tr><td>1. Charges réelles pondérées + {MARGE_EVOLUTION - 1:.0%} d'évolution</td><td class='n'>{fr(ge['m1'])} kVA</td><td>onduleurs × {K_ONDULEUR_GE} "
          f"(courant harmonique, reprise), L.TECH × {K_LT_GE}, clims × 1 (inverter, relance échelonnée)</td></tr>",
          f"<tr><td>2. Règle usuelle : {K_ONDULEUR_GE} × puissance nominale des onduleurs + autres charges</td><td class='n'>{fr(ge['m2'])} kVA</td>"
          f"<td>{K_ONDULEUR_GE} × 2 × 6 kVA = {fr(K_ONDULEUR_GE * 12)} kVA, + clims, L.TECH, auxiliaires</td></tr>",
          f"<tr class='tot'><td>Retenu : la plus contraignante, arrondie à la gamme</td><td class='n'>{ge['prp']} kVA PRP</td><td>soit {ge['esp']} kVA ESP, "
          f"{fr(ge['kw_prp'])} kW à cos φ 0,8, {fr(ge['i_nominal'])} A par phase</td></tr></table>",
          f"<p>Le groupe retenu : <b>diesel {ge['esp']} kVA ESP / {ge['prp']} kVA PRP, 400 V triphasé, capoté insonorisé, cuve double paroi de {ge['cuve']} l intégrée au "
          "châssis, démarrage automatique, régulation électronique (classe G2 de l'ISO 8528-5), excitation AREP ou PMG</b> (type gamme 30 kVA des grands constructeurs). "
          f"On le choisit sur sa puissance <b>PRP</b> (continue, sans limite d'heures) et non ESP (secours limité à ≈ 200 h/an) : une coupure peut durer plusieurs jours. "
          f"Charge réelle maximale {ge['taux_max']:.0f} % de la PRP, charge moyenne en coupure {ge['taux_moy']:.0f} %. "
          + ("Cette charge moyenne est un peu faible pour un diesel (risque d'encrassement si le groupe tourne longtemps à vide) : l'essai annuel de 2 h "
             "sur banc de charge à 75 % le nettoie. " if ge["taux_moy"] < 30 else "")
          + f"Le plus gros palier (retour des deux onduleurs sur le groupe) vaut {ge['palier_pct']:.0f} % de la PRP : acceptable en une fois.</p>",
          "<h3>4.3 Séquence de reprise</h3><table><tr><th>Moment</th><th>Événement</th></tr>",
          "<tr><td>T0</td><td>Coupure du réseau. Onduleurs de la salle (en ligne) : sur batterie sans aucune interruption. Onduleurs des L.TECH (line-interactive) : "
          "sur batterie en ≈ 4 ms. Les climatiseurs et l'éclairage normal s'arrêtent.</td></tr>",
          "<tr><td>T0 + 3 s</td><td>L'inverseur confirme l'absence de tension (temporisation contre les microcoupures) et donne l'ordre de démarrage au groupe.</td></tr>",
          "<tr><td>T0 + 10 à 15 s</td><td>Groupe préchauffé à tension et fréquence nominales : l'inverseur ouvre le réseau et ferme le secours (transfert ouvert).</td></tr>",
          "<tr><td>T0 + 15 à 30 s</td><td>Les onduleurs repassent progressivement sur leur redresseur (montée en charge) et rechargent leurs batteries. "
          "Les onduleurs des L.TECH repassent sur secteur (sensibilité réglée sur « basse » pour tolérer la fréquence du groupe).</td></tr>",
          "<tr><td>T0 + 60 s</td><td>Relance du climatiseur en service (contacteur temporisé) ; compresseur inverter : démarrage progressif.</td></tr>",
          "<tr><td>T0 + 90 s</td><td>Le climatiseur de secours est autorisé à démarrer si la salle dépasse 30 °C (refroidissement après la coupure).</td></tr>",
          f"<tr><td>T0 + {ARRET_GE_ABSENT_MIN} min</td><td>Contrôle : si l'onduleur est encore sur batterie (groupe en défaut, inverseur bloqué), "
          "NUT lance l'arrêt ordonné de la salle (section 4.6).</td></tr>",
          "<tr><td>Retour du réseau</td><td>Réseau stable pendant 2 min, puis retour sur le réseau (coupure de ≈ 0,3 s, couverte par les onduleurs) ; "
          "le groupe tourne 5 min à vide pour refroidir, puis se remet en veille.</td></tr></table>",
          "<h3>4.4 Carburant</h3><table><tr><th>Grandeur</th><th class='n'>Valeur</th><th>Commentaire</th></tr>",
          f"<tr><td>Consommation à 75 % de la PRP</td><td class='n'>{fr(ge['c75'])} l/h</td><td>fiche constructeur type (≈ 0,29 l/kWh)</td></tr>",
          f"<tr><td>Consommation à la charge moyenne ({fr(ge['p_moy_kw'])} kW)</td><td class='n'>{fr(ge['c_moy'])} l/h</td><td>été : informatique typique, "
          "1 climatiseur à pleine puissance, L.TECH</td></tr>",
          f"<tr><td>Cuve journalière double paroi</td><td class='n'>{ge['cuve']} l</td><td>besoin : max(48 h à la charge moyenne, 24 h à 75 %) ÷ "
          f"(90 % pompable × 75 % de remplissage)</td></tr>",
          f"<tr><td>Autonomie cuve à 75 % : charge moyenne · 75 % PRP</td><td class='n'>{ge['autonomie_moy']:.0f} h · {ge['autonomie_75']:.0f} h</td>"
          f"<td>cuve pleine, charge moyenne : {ge['autonomie_pleine']:.0f} h</td></tr>",
          f"<tr><td>Consommation annuelle</td><td class='n'>{ge['litres_an']:.0f} l</td><td>12 essais d'1 h, 2 h de banc de charge, {COUPURES_H:.0f} h de coupure</td></tr></table>",
          "<p>Gazole non routier, avec un <b>contrat de livraison prioritaire sous 24 h</b> (fournisseur local, astreinte). Analyse annuelle et traitement biocide "
          "du gazole (le biodiesel qu'il contient vieillit en cuve) ; les essais mensuels renouvellent le carburant. Jamais de jerricans.</p>",
          "<h3>4.5 Emplacement et raccordement</h3><table><tr><th>Emplacement</th><th>Avantages</th><th>Inconvénients</th><th>Choix</th></tr>",
          "<tr><td><b>Extérieur, façade est, sur dalle près de l'entrée du parking</b></td><td>Accès camion pour le gazole et le levage ; câble court "
          f"(≈ {L_GE_TD:.0f} m) par le chemin de l'adduction FAI 2 ; pas de local à créer</td><td>Bruit pour le voisinage ; capot, clôture et dalle à prévoir</td>"
          "<td><b>Retenu</b> (à valider sur site)</td></tr>",
          "<tr><td>Toiture-terrasse</td><td>Loin des passages</td><td>≈ 1,2 t avec le gazole sur une toiture non prévue pour (étude de structure), levage à la grue, "
          "livraison du gazole impossible, vibrations au-dessus des salles</td><td>Écarté</td></tr>",
          "<tr><td>Dans le parking du sous-sol</td><td>À l'abri, près de la salle</td><td>Local coupe-feu dédié, amenée et rejet d'air (≈ 3 000 m³/h), "
          "échappement à porter en toiture ; zone inondable</td><td>Écarté</td></tr>",
          "<tr><td>Extérieur, façade ouest, près de la chaufferie</td><td>Zone technique existante</td><td>Prises d'air de la chaufferie et chambre de tirage du FAI 1 "
          "voisines</td><td>Variante</td></tr></table>",
          "<ul><li>Dalle béton armé ≈ 3 × 2 m, capot insonorisé (≈ 65 dB(A) à 7 m), cuve double paroi avec détecteur de fuite (pas de rétention séparée), "
          "clôture et portillon fermé à clé.</li>",
          "<li>Échappement orienté à l'opposé des façades, à au moins 8 m des prises d'air neuf, des fenêtres ouvrantes et des unités extérieures de climatisation "
          "(règle de l'art, à confirmer par le bureau de contrôle).</li>",
          f"<li>Câble GE → inverseur : 5G{ge['cable_section']:g} mm² U1000 R2V en fourreau, {ge['cable_L']:.0f} m, ΔU {fr(ge['cable_du'])} % ; disjoncteur 4P 63 A "
          f"sur le groupe ; câble de commande (démarrage, défauts) et report d'état vers la supervision. Courant nominal {fr(ge['i_nominal'])} A.</li>",
          f"<li><b>Point de vigilance</b> : sur le groupe, le courant de court-circuit est faible (≈ 3 I<sub>n</sub> pendant 10 s avec AREP/PMG, soit ≈ {ge['icc']:.0f} A). "
          "Les déclencheurs magnétiques des départs ne sont pas garantis : les courts-circuits sont éliminés par les déclencheurs thermiques en quelques secondes "
          "et la protection des personnes est assurée par les différentiels présents sur tous les départs. À faire confirmer par le fournisseur du groupe.</li></ul>",
          "<h3>4.6 Effet sur l'arrêt ordonné (NUT)</h3>",
          f"<p>Avec le groupe, l'onduleur ne fait plus que le <b>pont</b> pendant les ≈ 15 s du démarrage. L'arrêt ordonné reste indispensable si le groupe ne démarre pas "
          f"(c'est sa panne la plus fréquente). Le seuil change : en v2, l'arrêt commençait à T0 + 5 min ; en v2.1, NUT attend {ARRET_GE_ABSENT_MIN} min "
          "(le temps de trois tentatives de démarrage) : si l'onduleur est revenu « en ligne », il n'y a rien à faire ; sinon, l'arrêt commence aussitôt et se termine à "
          f"T0 + {FIN_ARRET_MIN} min, avec {etd['ond_fin_vie']:.0f} min d'autonomie disponibles même avec un onduleur en panne et des batteries en fin de vie. "
          f"Deux déclencheurs de sécurité s'ajoutent : autonomie restante annoncée inférieure à 15 min, et température d'allée froide supérieure à {T_CRITIQUE:.0f} °C "
          "(climatiseurs non secourus si le groupe ne démarre pas).</p>",
          "<h3>4.7 Essais, maintenance, réglementation</h3><ul>",
          "<li><b>Essai mensuel automatique</b> (programmé dans le contrôleur du groupe, en journée) : 1 h sur la charge réelle par l'inverseur, journal des essais.</li>",
          "<li><b>Essai annuel sur banc de charge</b> : 2 h à 75 % de la PRP (nettoie le moteur d'un groupe peu chargé), contrôle des temps de démarrage et de transfert.</li>",
          "<li><b>Maintenance</b> : contrat de 2 visites par an (vidange, filtres, liquide de refroidissement, courroies, batterie de démarrage tous les 3 ans, "
          "contrôle de l'inverseur) ; alarmes du groupe et de l'inverseur reportées dans la supervision et à l'astreinte.</li>",
          "<li><b>Installations classées</b> : rubrique 2910 (combustion) non concernée, le seuil de déclaration étant de 1 MW thermique (groupe ≈ "
          f"{fr(ge['thermique_kw'] / 1000, 2)} MW) ; rubrique 4734 (produits pétroliers) non concernée sous 50 t ({ge['cuve']} l ≈ 0,2 t).</li>",
          "<li><b>Électricité</b> : NF C 15-100 (partie 5-55, groupes électrogènes BT) ; inverseur conforme à la NF EN 60947-6-1 ; vérification initiale "
          "par un organisme agréé.</li>",
          "<li><b>Bruit</b> : niveau de puissance acoustique garanti (directive 2000/14/CE) ; bruit de voisinage (Code de la santé publique) : émergence limitée "
          "à 5 dB(A) le jour et 3 dB(A) la nuit, d'où le capot insonorisé et des essais en journée.</li>",
          "<li><b>Urbanisme</b> : dalle, capot et clôture modifient l'aspect extérieur : à vérifier avec le service patrimoine du campus.</li></ul>",
          "<p class='sous'>Les textes réglementaires sont cités à titre indicatif : un bureau de contrôle doit valider l'installation.</p>",
          "<h3>4.8 Coûts</h3><table><tr><th>Élément</th><th class='n'>Qté</th><th class='n'>Prix unitaire</th><th class='n'>Total HT</th><th>Source</th></tr>"]
    for l in lignes_ge:
        H.append(f"<tr><td>{e(l['solution'])}</td><td class='n'>{l['quantite']}</td><td class='n'>{eur(l['pu_ht'])}</td><td class='n'>{eur(l['total_ht'])}</td>"
                 f"<td class='chemin'>{e(l['note'])}</td></tr>")
    H.append(f"<tr class='tot'><td colspan='3'>Investissement du groupe électrogène</td><td class='n'>{eur(capex_ge)}</td><td></td></tr></table>"
             "<table><tr><th>Coût annuel</th><th>Détail</th><th class='n'>Par an</th></tr>")
    for p, d, m in fin["opex"]:
        if "électrogène" in p or "banc de charge" in p or "Gazole" in p:
            H.append(f"<tr><td>{e(p)}</td><td class='chemin'>{e(d)}</td><td class='n'>{eur(m)}</td></tr>")
    H.append(f"<tr class='tot'><td colspan='2'>Fonctionnement du groupe (hors électricité du réchauffeur, comptée dans l'électricité du lot)</td>"
             f"<td class='n'>{eur(opex_ge)}</td></tr></table>"
             f"<p><b>Groupe électrogène sur 5 ans : {eur(capex_ge + 5 * opex_ge)} HT.</b> Prix : ordres de grandeur constatés chez les distributeurs et installateurs "
             "(groupe 30 kVA capoté 15 à 20 k€ HT fourni), à confirmer par devis.</p>")
    # 5. Vérifications
    H += ["<h2 class='saut'>5. Vérifications</h2><table><tr><th>Domaine</th><th>Critère</th><th class='n'>Valeur</th><th>Seuil</th><th>Statut</th><th>Remarque</th></tr>"]
    for v in V:
        H.append(f"<tr><td>{e(v['domaine'])}</td><td>{e(v['critere'])}</td><td class='n'>{e(v['valeur'])}</td><td>{e(v['seuil'])}</td>"
                 f"<td>{statut(v['statut'])}</td><td class='chemin'>{e(v['note'])}</td></tr>")
    H.append(f"</table><p>{n_ok} critères conformes (dont les corrections v2.1), {n_av} à vérifier sur site, {n_nok} non conforme.</p>")
    # 6. Annexes
    H += ["<h2 class='saut'>6. Annexes de calcul</h2>",
          "<img src='schemas/montee_temperature.png' alt='Montée en température sans refroidissement'>",
          "<p class='sous'>Salle serveur : charge typique, inertie de l'air et de 30 % de la masse des baies, échanges par les cloisons. La borne pessimiste "
          f"(air seul, pointe) atteint 40 °C en {duree(th['t40_air'])} : elle figure dans la fiche 3.1. L.TECH : les trois locaux dont la température limite "
          "sans ventilation est la plus haute, depuis leur température d'été. Valeurs détaillées dans les fiches de la section 3.</p>",
          "<h3>A. Formules</h3><ul>",
          "<li>Chaleur ↔ débit d'air : P = ρ·c<sub>p</sub>·Q·ΔT, avec ρ·c<sub>p</sub> = 1,2 × 1 005 ≈ 1 206 J/(m³·K) ; Q [m³/h] = P × 3 600 / (1 206 × ΔT). 1 W = 3,412 BTU/h.</li>",
          "<li>Ventilation naturelle (tirage) : Q = C<sub>d</sub>·A<sub>eff</sub>·√(2·g·H·ΔT/T) avec A<sub>eff</sub> = A/√2 (deux grilles en série) ; "
          "d'où ΔT = (P / K)<sup>2/3</sup>, K = ρ·c<sub>p</sub>·C<sub>d</sub>·A<sub>eff</sub>·√(2·g·H/T).</li>",
          "<li>Montée en température sans refroidissement : C·dT/dt = P − UA·(T − T<sub>voisin</sub>) ; T(t) = T<sub>∞</sub> + (T<sub>0</sub> − T<sub>∞</sub>)·e<sup>−t·UA/C</sup>, "
          "T<sub>∞</sub> = T<sub>voisin</sub> + P/UA ; C = air + 30 % de la masse × 450 J/(kg·K) ; UA = 1,5 W/(m²·K) × (cloisons + plafond). "
          "Borne pessimiste : t = (T<sub>seuil</sub> − T<sub>0</sub>)·C<sub>air</sub>/P.</li>",
          "<li>Chute de tension : ΔU = b·L·I<sub>B</sub>·(ρ·cos φ/S + λ·sin φ), b = 2 en monophasé, √3 en triphasé ; ρ = 0,0225 Ω·mm²/m, λ = 0,08 mΩ/m.</li>",
          "<li>Onduleurs : pertes SRT = 100 W + 3 % de la charge ; SMT = 12 W + 2 % ; autonomie interpolée en loi de puissance entre deux points constructeur ; "
          "fin de vie : 80 % de la capacité.</li>",
          f"<li>Groupe : consommation c(P) = c<sub>75</sub>·(0,2 + 0,8·P/(0,75·P<sub>PRP</sub>)) ; cuve ≥ max(48 h·c<sub>moy</sub>, 24 h·c<sub>75</sub>) / (0,9 × 0,75).</li></ul>",
          "<h3>B. Courant admissible (U1000 R2V, méthode E, avant facteur 0,7)</h3><table><tr><th>Section</th>"
          + "".join(f"<th class='n'>{fr(k)} mm²</th>" for k in IZ[2]) + "</tr><tr><td>2 conducteurs chargés</td>"
          + "".join(f"<td class='n'>{v} A</td>" for v in IZ[2].values()) + "</tr><tr><td>3 conducteurs chargés</td>"
          + "".join(f"<td class='n'>{v} A</td>" for v in IZ[3].values()) + "</tr></table>",
          "<h3>C. Locaux techniques : détail du calcul de ventilation</h3><table><tr><th>Local</th><th class='n'>P pointe</th><th class='n'>T air</th>"
          "<th class='n'>Grilles</th>" + "".join(f"<th class='n'>Extr. {q}</th>" for q, _ in EXTRACTEURS) + "<th class='n'>Split</th><th>Retenu</th></tr>"]
    for l in lt:
        b = l["bet"]
        cells = [regime(("grilles", 0), b["p_dim"], b["t_amb"])] + [regime(("extracteur", q), b["p_dim"], b["t_amb"]) for q, _ in EXTRACTEURS]
        H.append(f"<tr><td>{l['local']}</td><td class='n'>{fr(b['p_dim'], 0)} W</td><td class='n'>{b['t_amb']:.0f} °C</td>"
                 + "".join(f"<td class='n'{' style=\"color:#c13c3b\"' if t > T_MAX_LT else ''}>{fr(t)} °C</td>" for t in cells)
                 + f"<td class='n'>{T_CONSIGNE:.0f} °C</td><td>{e(b['solution_court'])}</td></tr>")
    H.append(f"</table><p class='sous'>En rouge : au-dessus de {T_MAX_LT:.0f} °C. On retient la première solution conforme dans l'ordre grilles → extracteur 150 → "
             "extracteur 300 → mini-split, en partant de la solution de la v2.</p>")
    H += ["<h2>7. Points à valider avec le client</h2><ul>",
          "<li>Réserve de puissance du TGBT, emplacement exact, régime de neutre, schéma de l'alimentation du bâtiment depuis le poste du campus.</li>",
          "<li>Emplacement du groupe électrogène (façade est), accès du camion de livraison, avis du service patrimoine et du bureau de contrôle.</li>",
          "<li>Passage d'une gaine de rejet pour les extracteurs des L.TECH du RDC et de l'étage ; place pour l'unité extérieure du mini-split en toiture.</li>",
          "<li>Notices définitives : courant d'entrée et différentiel préconisés pour les onduleurs, puissance absorbée des climatiseurs, Icc du groupe.</li></ul>",
          "</body></html>"]
    return "\n".join(H)


def produire(ctx, etd, fin):
    OUT.mkdir(parents=True, exist_ok=True)
    ecrire_csv(etd, ctx["lt"])
    figure_montee(etd, ctx["lt"])
    page = OUT / "bet_locaux_techniques.html"
    page.write_text(document(ctx, etd, fin), encoding="utf-8")
    chrome = shutil.which("google-chrome") or shutil.which("chromium")
    if chrome:
        with tempfile.TemporaryDirectory() as prof:
            subprocess.run([chrome, "--headless=new", "--no-sandbox", "--disable-gpu", f"--user-data-dir={prof}", "--no-pdf-header-footer",
                            f"--print-to-pdf={OUT / 'bet_locaux_techniques.pdf'}", page.as_uri()], check=True, capture_output=True, timeout=180)


def resume(etd, lt):
    """Synthèse reprise dans resume.json."""
    tab, ge, th = etd["tableau"], etd["ge"], etd["salle"]["thermique"]
    return dict(
        date=DATE_V21, reference=REF,
        locaux=[dict(local=l["local"], dissipation_typ_w=round(l["bet"]["dissipation_typ"]), pointe_ete_w=round(l["bet"]["p_dim"]),
                     solution=l["bet"]["solution_court"], solution_v2=l["bet"]["v2_court"], t_ete=round(l["bet"]["t_ete"], 1),
                     verdict="conforme" if l["bet"]["v2_ok"] else "corrigé v2.1") for l in lt],
        salle=dict(q_typ_w=round(th["q_typ"]), q_pointe_w=round(th["q_pointe"]), t35_min=th["t35"] and round(th["t35"], 1),
                   t40_min=th["t40"] and round(th["t40"], 1), t40_air_min=round(th["t40_air"], 1)),
        puissance_max_kva=round(tab["s_max"] / 1000, 1), reserve_tgbt_kva=tab["reserve_kva"], puissance_courante_kw=round(tab["p_moy"] / 1000, 1),
        verifications=dict(total=len(etd["verifs"]), ok=sum(v["statut"] in ("OK", "Corrigé v2.1", "OK avec parade") for v in etd["verifs"]),
                           a_verifier=sum(v["statut"] == "À vérifier" for v in etd["verifs"]), nok=sum(v["statut"] == "NOK" for v in etd["verifs"])),
        groupe_electrogene=dict(prp_kva=ge["prp"], esp_kva=ge["esp"], besoin_kva=round(ge["besoin"], 1), charge_max_pct=round(ge["taux_max"]),
                                charge_moy_pct=round(ge["taux_moy"]), cuve_l=ge["cuve"], autonomie_h=round(ge["autonomie_moy"]),
                                autonomie_75_h=round(ge["autonomie_75"]), conso_75_lh=ge["c75"], arret_nut_si_ge_absent_min=ARRET_GE_ABSENT_MIN,
                                fin_arret_min=FIN_ARRET_MIN))


if __name__ == "__main__":
    import energie  # noqa: E402  (même dossier)
    energie.main()
