#!/usr/bin/env python3
"""Injecte le chiffrage et le référentiel ANSSI dans la roadmap -> roadmap/index.html
Sources : chiffrage/estimation.json, docs/anssi/referentiel_anssi.md"""
import json, pathlib, re
H = pathlib.Path(__file__).parent
ROOT = H.parent


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


est = json.loads((ROOT / "chiffrage" / "estimation.json").read_text(encoding="utf-8"))
anssi = parse_anssi((ROOT / "docs" / "anssi" / "referentiel_anssi.md").read_text(encoding="utf-8"))
dump = lambda o: json.dumps(o, ensure_ascii=False).replace("</", "<\\/")
tpl = (H / "roadmap.template.html").read_text(encoding="utf-8")
assert "/*ESTIMATION*/null" in tpl and "/*ANSSI*/null" in tpl
out = tpl.replace("/*ESTIMATION*/null", dump(est)).replace("/*ANSSI*/null", dump(anssi))
(H / "index.html").write_text(out, encoding="utf-8")
n = sum(len(s["rows"]) for s in anssi["sections"])
print(f"index.html {len(out)} octets, {len(anssi['sections'])} sections ANSSI, {n} guides")
