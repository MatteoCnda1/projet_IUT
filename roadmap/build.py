#!/usr/bin/env python3
"""Injecte le chiffrage, le référentiel ANSSI et les repères de version dans la roadmap -> roadmap/index.html.

Sources : chiffrage/estimation.json, docs/anssi/referentiel_anssi.md, livrables/plan_cablage/resume.json,
livrables/energie_refroidissement/resume.json, archives v1 et v2 (CAPEX), commun/charte.py (version du dossier).
Met aussi à jour les notes du point 14 dans roadmap/seed_points.json à partir de resume.json (chiffres jamais recopiés à la main).
"""
import json
import pathlib
import re
import sys

H = pathlib.Path(__file__).resolve().parent
ROOT = H.parent
sys.path.insert(0, str(ROOT))
from commun import charte as CH  # noqa: E402


def parse_anssi(md):
    """Découpe le Markdown en sections (tableaux ou listes)."""
    out = {"intro": [], "sections": []}
    cur = None
    for line in md.splitlines():
        s = line.strip()
        if s.startswith("## "):
            cur = {"title": s[3:].strip(), "kind": None, "head": [], "rows": [], "items": [], "ordered": False}
            out["sections"].append(cur)
        elif s.startswith("# ") or not s:
            continue
        elif cur is None:
            out["intro"].append(s)
        elif s.startswith("|"):
            cells = [c.strip() for c in s.strip("|").split("|")]
            if all(re.fullmatch(r":?-+:?", c) for c in cells):
                continue
            cur["kind"] = "table"
            (cur["rows"] if cur["head"] else cur["head"]).append(cells) if cur["head"] else cur.__setitem__("head", cells)
        elif re.match(r"(- |\d+\. )", s):
            cur["kind"] = "list"
            cur["ordered"] = bool(re.match(r"\d+\. ", s))
            cur["items"].append(re.sub(r"^(- |\d+\. )", "", s))
    for sec in out["sections"]:
        if sec["kind"] == "table":
            n = len(sec["head"])
            bad = [r for r in sec["rows"] if len(r) != n]
            assert not bad, f"colonnes incohérentes dans « {sec['title']} » : {bad[:1]}"
    return out


def lire(chemin):
    return json.loads((ROOT / chemin).read_text(encoding="utf-8"))


def notes_p14(nrj):
    """Notes du point 14, lues dans resume.json (format Markdown : espaces ordinaires, virgule décimale)."""
    n = lambda v, d=0: f"{v:,.{d}f}".replace(",", " ").replace(".", ",")
    ge = nrj.get("bet", {}).get("groupe_electrogene")
    ref_bet = nrj.get("bet", {}).get("reference", "BET")
    s, o, c, en = nrj["salle"], nrj["onduleurs"], nrj["clim"], nrj["energie"]
    txt = (f"Livré (energie_refroidissement.pdf, {CH.VERSION} du {CH.DATE_VERSION}) : salle {n(s['it_typ'] / 1000, 2)} kW "
           f"({n(s['it_pointe'] / 1000, 2)} kW en pointe), 2 onduleurs SRT 6 kVA A/B + packs ({o['autonomie_degrade']} min sur un seul), "
           f"2 clims {n(c['unite_kw'], 1)} kW N+1, allée froide, plancher surélevé, extinction IG-541, PUE {n(en['pue'], 2)}, {n(en['kwh'])} kWh/an.")
    if ge:
        txt += (f" Groupe électrogène dédié {ge['esp_kva']} kVA ESP et inverseur automatique ({ge['autonomie_h']} h à charge moyenne) : "
                f"le site n'en a pas (confirmé par le client). Étude BET des locaux techniques ({ref_bet}).")
    txt += (f" Lot {n(nrj['capex_lot'])} € HT, {n(nrj['opex_total'])} € HT/an. À vérifier sur site : réserve de puissance du TGBT, "
            "régime de neutre, emplacement du groupe ; à valider avec le client : unités extérieures des clims.")
    return txt


def maj_seed():
    """Réécrit les notes du point 14 dans seed_points.json (une ligne par point, comme le fichier d'origine)."""
    f = H / "seed_points.json"
    texte = f.read_text(encoding="utf-8")
    seed = json.loads(texte)
    notes = notes_p14(lire("livrables/energie_refroidissement/resume.json"))
    if seed["points/p14"]["notes"] == notes:
        return False
    seed["points/p14"]["notes"] = notes
    lignes = ",\n".join(f" {json.dumps(k, ensure_ascii=False)}: {json.dumps(v, ensure_ascii=False)}" for k, v in seed.items())
    f.write_text("{\n" + lignes + "\n}\n", encoding="utf-8")
    return True


def meta():
    cab = lire("livrables/plan_cablage/resume.json")
    nrj = lire("livrables/energie_refroidissement/resume.json")
    v1 = lire("livrables/archives/v1_2026-11-15/chiffrage/estimation.json")
    v2 = lire("livrables/archives/v2_2026-11-20/chiffrage/estimation.json")
    ge = nrj.get("bet", {}).get("groupe_electrogene", {})
    return {"version": CH.VERSION, "date": CH.DATE_VERSION, "mention": CH.MENTION, "capex_v1": v1["capex"], "capex_v2": v2["capex"],
            "prises": cab["prises"], "bornes": cab["par_type"]["wifi"], "locaux": len(cab["baies"]), "ge_kva": ge.get("esp_kva")}


def main():
    if maj_seed():
        print("seed_points.json : notes du point 14 mises à jour depuis resume.json")
    est = lire("chiffrage/estimation.json")
    anssi = parse_anssi((ROOT / "docs" / "anssi" / "referentiel_anssi.md").read_text(encoding="utf-8"))
    dump = lambda o: json.dumps(o, ensure_ascii=False).replace("</", "<\\/")
    tpl = (H / "roadmap.template.html").read_text(encoding="utf-8")
    assert "/*ESTIMATION*/null" in tpl and "/*ANSSI*/null" in tpl and "/*META*/null" in tpl
    out = tpl.replace("/*ESTIMATION*/null", dump(est)).replace("/*ANSSI*/null", dump(anssi)).replace("/*META*/null", dump(meta()))
    (H / "index.html").write_text(out, encoding="utf-8")
    n = sum(len(s["rows"]) for s in anssi["sections"])
    print(f"index.html {len(out)} octets, {len(anssi['sections'])} sections ANSSI, {n} guides")


if __name__ == "__main__":
    main()
