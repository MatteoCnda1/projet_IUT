"""Règles communes à l'étude Wi-Fi et au plan de câblage.

Décisions de l'équipe (12/11/2026) :
  - salle serveur : partie sud de la SALLE J05 (sous-sol), ~25 m², contre le L.TECH 01 du sous-sol ;
  - répartiteurs d'étage : les 6 L.TECH des plans (2 par niveau) ;
  - logement de fonction (étage 1, aile nord-est) : hors périmètre ;
  - densité de prises : hypothèse du chiffrage (bureau 2 par poste, salle TP 1 par poste + 2,
    salle TD/cours/réunion 3) ;
  - bornes Wi-Fi : nombre fixé par l'étude RSSI (etude_rssi.py) ;
  - 14 caméras (v2.1 : plus de caméra au foyer des étudiants, lieu de pause, CNIL), 11 badgeuses (salle serveur,
    6 L.TECH, entrée, hall, 2 salles réseaux) : listes CAMERAS et BADGEUSES de plan_cablage.py ;
  - téléphones IP : 1 par bureau d'enseignant + l'accueil (secrétariat), sur la 2e prise du bureau.
"""
import re

# Type de chaque salle, d'après son nom sur le plan. L'ordre compte : première règle qui correspond.
TYPES = [
    # Logement de fonction (étage 1, aile nord-est) : hors périmètre
    ("hors", r"^(CHAMBRE|SDB|SEJOUR|CUISINE|RGMT CHAMBRE|ESC L\.FONCTION|PL\.TECH)", "N1"),
    ("hors", r"^(PL 01|PL 02|CIRC|WC|PALIER|TERRASSE 01|TERRASSE 02)$", "N1"),
    ("exterieur", r"^(ESC EXT|PASSERELLE EXT|TOIT|PALIER EXT|03 EXT|VIDE|SOUS AMPHI|TERRASSE)", None),
    ("sanitaire", r"^(WC|SAN|DOUCHE|SALLE D EAU)", None),
    ("tp", r"^(S\.INFORMATIQUE|S\.INFO|S\.TP|S\.RESEAUX|S RESEAUX|S\.ELECTRO)", None),
    ("projet", r"^S\.PROJET", None),
    ("cours", r"^(S\.TD|S\.ANGLAIS|S\.COURS|S\.REUNION|SALLE J0[2-5])", None),
    ("accueil", r"^SECRETARIAT", None),
    ("bureau", r"^(BUREAU|ADMIN/RES)", None),
    ("atelier", r"^ATELIER", None),
    ("prepa", r"^S\.PREPA", None),
    ("vie", r"^(FOYER|HALL)", None),
    ("amphi", r"^(AMPHITHEATRE|ESTRADE|S\.TECH)", None),
    ("technique", r"^(L\.TECH|RANGEMENT|RESERVE|RGMT|ARCHIVES|PL\.ELEC|CHAUFFERIE|L\.SERVICE|ASC|PL\b|PL \d)", None),
    ("parking", r"^PARKING", None),
    ("circulation", r"^(CIRC|CIRCULATION|DGMT|PASSERELLE|SOUS-PASSERELLE|PALIER|ENTREE|SAS|ESC)", None),
]


def type_salle(nom, niveau):
    for t, motif, niv in TYPES:
        if (niv is None or niv == niveau) and re.search(motif, nom):
            return t
    return "autre"


# Zones à couvrir en Wi-Fi (objectif RSSI ci-dessous)
TYPES_WIFI = {"tp", "projet", "cours", "accueil", "bureau", "atelier", "prepa", "vie", "amphi", "circulation"}
# Escaliers, sas et paliers : couverts par débordement, sans objectif
SANS_OBJECTIF = re.compile(r"^(ESC|SAS|PALIER)")

# ---------------------------------------------------------------------------
# Hypothèses radio (5 GHz)
# ---------------------------------------------------------------------------
FREQ_MHZ = 5500
PIRE_DBM = 18.0          # puissance de conception (≈ 50 % du maximum de la CW9164I) + gain d'antenne
EXPOSANT = 2.2           # affaiblissement en distance (intérieur meublé), en plus des parois
AFFAIBLISSEMENT = {1: 12.0, 2: 5.0, 3: 3.0}  # dB à 5 GHz : mur porteur, cloison, vitrage
OBJECTIF_DBM = -67.0     # voix/vidéo, meilleur serveur
ROAMING_DBM = -70.0      # deuxième borne pour l'itinérance
SEUIL_CO_CANAL = -82.0   # deux bornes plus fortes que ça l'une chez l'autre ne partagent pas un canal
PLANCHER_DB = 18.0       # affaiblissement d'une dalle béton entre deux niveaux
CANAUX_40 = [36, 44, 52, 60, 100, 108, 116, 124, 132, 140, 149, 157]


def bornes_capacite(t, nom, surface):
    """Bornes imposées par la capacité (clients simultanés), avant l'étude de couverture."""
    if t == "amphi" and nom.startswith("AMPHI"):
        return 2
    if t == "cours" and (surface or 0) > 100:
        return 2
    if t in ("tp", "cours", "projet") and (surface or 0) >= 20:
        return 1
    if t == "vie" and nom.startswith("FOYER"):
        return 1
    return 0


# ---------------------------------------------------------------------------
# Prises RJ45 (hypothèse du chiffrage)
# ---------------------------------------------------------------------------
M2_PAR_POSTE_TP = 2.5    # surface par poste en salle de TP
POSTES_TP_MAX = 24


def prises_utilisateurs(t, nom, surface):
    """Nombre de prises RJ45 pour les usagers (hors bornes, caméras, badgeuses)."""
    s = surface or 0
    if t == "tp":
        postes = min(POSTES_TP_MAX, int(s // M2_PAR_POSTE_TP))
        return postes + 2, f"{postes} postes + 2 pour l'enseignant"
    if t == "cours":
        return 3, "vidéoprojecteur, enseignant, réserve"
    if t == "projet":
        return 8, "4 îlots de 2 prises"
    if t == "bureau":
        postes = 1 if s < 18 else 2
        return 2 * postes, f"{postes} poste{'s' if postes > 1 else ''} × 2 prises (PC, téléphone ou réserve)"
    if t == "accueil":
        return 6, "2 postes × 2 + imprimante + réserve"
    if t == "atelier":
        return 4, "établis"
    if t == "prepa":
        return 4, "préparation des TP"
    if t == "vie":
        return 2, "affichage, borne d'information"
    if t == "amphi":
        return {"ESTRADE": (4, "pupitre enseignant, captation"), "S.TECH": (2, "régie")}.get(nom, (0, ""))
    return 0, ""


TELEPHONE = re.compile(r"^(BUREAU|SECRETARIAT)")  # bureaux d'enseignants + accueil
