"""Rendu par Chrome sans interface : HTML -> PDF, SVG -> PNG (fond transparent)."""
import pathlib, re, shutil, subprocess, tempfile

CHROME = shutil.which("google-chrome") or shutil.which("chromium")
ICI = pathlib.Path(__file__).parent


def _chrome(*args):
    if not CHROME:
        raise SystemExit("Chrome ou Chromium est nécessaire pour produire les PDF et les PNG.")
    with tempfile.TemporaryDirectory() as prof:
        subprocess.run([CHROME, "--headless=new", "--no-sandbox", "--disable-gpu", f"--user-data-dir={prof}",
                        "--hide-scrollbars", *args], check=True, capture_output=True, timeout=180)


def pdf(page_html, sortie):
    _chrome("--no-pdf-header-footer", "--virtual-time-budget=5000", f"--print-to-pdf={sortie}",
            pathlib.Path(page_html).resolve().as_uri())


def png(svg, sortie, largeur):
    """Exporte un SVG en PNG de `largeur` px, hauteur au prorata, fond transparent."""
    svg = pathlib.Path(svg).resolve()
    w, h = map(float, re.search(r'viewBox="0 0 ([\d.]+) ([\d.]+)"', svg.read_text()).groups())
    hauteur = round(largeur * h / w)
    with tempfile.TemporaryDirectory() as t:
        page = pathlib.Path(t) / "p.html"
        page.write_text(f"<html><body style='margin:0;background:transparent'>"
                        f"<img src='{svg.as_uri()}' style='display:block;width:{largeur}px;height:{hauteur}px'></body></html>")
        _chrome("--default-background-color=00000000", f"--window-size={largeur},{hauteur}",
                f"--screenshot={pathlib.Path(sortie).resolve()}", page.as_uri())


def copier_polices(dest):
    dest = pathlib.Path(dest)
    dest.mkdir(parents=True, exist_ok=True)
    for f in (ICI / "fonts").glob("*.woff*"):
        shutil.copy2(f, dest / f.name)
