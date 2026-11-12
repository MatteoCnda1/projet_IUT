#!/usr/bin/env python3
"""Injecte chiffrage/estimation.json dans la roadmap -> roadmap/index.html"""
import json, pathlib
H = pathlib.Path(__file__).parent
est = json.loads((H.parent / "chiffrage" / "estimation.json").read_text(encoding="utf-8"))
tpl = (H / "roadmap.template.html").read_text(encoding="utf-8")
out = tpl.replace("/*ESTIMATION*/null", json.dumps(est, ensure_ascii=False).replace("</", "<\\/"))
(H / "index.html").write_text(out, encoding="utf-8")
print("index.html", len(out), "octets")
