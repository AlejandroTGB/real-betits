#!/usr/bin/env python3
"""Genera las fuentes subseteadas que sirve el sitio.

QUE HACE
  1. Baja de Google Fonts los .woff2 (subset latin) de los pesos que usa el
     diseno, a un directorio temporal.
  2. Los recorta a los caracteres que el sitio realmente usa: los que aparecen
     en dist/**/*.html mas un rango de seguridad (ASCII + Latin-1 completo, que
     cubre el espanol: a e i o u u n ? ! y todas sus mayusculas acentuadas).
  3. Escribe el resultado en public/fuentes/.

POR QUE
  Inter trae ~700 glifos por peso y el sitio usa ~70 caracteres distintos.
  Medido: 228 KB de fuentes en el repo pasan a ~20 KB, y el home baja de 114 KB
  de fuentes a ~15 KB.

COMO SE CORRE
  Requiere fonttools + brotli. Sin tocar el sistema:
    python3 -m venv ~/.venvs/fuentes
    ~/.venvs/fuentes/bin/pip install fonttools brotli
    ~/.venvs/fuentes/bin/python scripts/subsetear-fuentes.py

  Se corre DESPUES de `npm run build` (lee los HTML ya construidos para saber
  que caracteres se usan de verdad).

MANTENIMIENTO
  Si el CSS empieza a usar un peso nuevo, agregarlo a PESOS; si no, el navegador
  lo sintetiza y se ve distinto.
  El rango de seguridad cubre el espanol completo. Un nombre con caracteres
  fuera de Latin-1 (polaco, turco...) cae a la tipografia del sistema: se ve
  distinto, pero no se rompe nada.
"""
import glob
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DESTINO = os.path.join(REPO, "public", "fuentes")
DIST = os.path.join(REPO, "dist")

PESOS = {
    "Barlow Condensed": ["500", "600", "700", "800"],
    "Inter": ["400", "500", "600"],
}
UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")

# Base de seguridad: el alfabeto espanol completo + los signos que usa el
# diseno. Se le SUMAN los caracteres que aparecen en las paginas construidas.
#
# Medido (por que no alcanza con "todo Latin-1"): pedir U+00A0-00FF entero deja
# a Inter en 32,6 KB; recortar a los caracteres que el sitio usa de verdad
# (86) mas el espanol (100 en total) lo deja en 17,3 KB. La diferencia son
# glifos que nunca se dibujan.
# Solo caracteres que pueden APARECER EN UN TEXTO. Los de marcado (,<>{}\|^~`)
# no se dibujan nunca y engordan el recorte (~8 KB por peso medido).
BASE = ("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
        "0123456789 .,:;!?()[]/@#$%&*+-=_\"'\u00b4"
        "\u00a1\u00bf\u00e1\u00e9\u00ed\u00f3\u00fa\u00fc\u00f1\u00c1\u00c9\u00cd\u00d3\u00da\u00dc\u00d1"
        "\u00b0\u00ba\u00aa\u00b7\u2013\u2014\u2018\u2019\u201c\u201d\u2026\u2022\u2192")

BLOQUE = re.compile(r"/\*\s*([a-z0-9\-\[\]]+)\s*\*/\s*@font-face\s*\{(.*?)\}", re.S)
FAMILIA = re.compile(r"font-family:\s*'([^']+)'")
PESO = re.compile(r"font-weight:\s*(\d+)")
WOFF = re.compile(r"url\((https://[^)]+\.woff2)\)")


def caracteres_del_sitio():
    """Los caracteres que aparecen en el texto de las paginas construidas."""
    if not os.path.isdir(DIST):
        sys.exit("no hay dist/: corre `npm run build` primero")
    texto = ""
    for ruta in glob.glob(os.path.join(DIST, "**", "*.html"), recursive=True):
        html = open(ruta, encoding="utf-8").read()
        html = re.sub(r"(?s)<(script|style)[^>]*>.*?</\1>", " ", html)
        texto += re.sub(r"(?s)<[^>]+>", " ", html)
    return sorted(set(texto))


def url_css():
    fam = "&".join(
        "family=" + nombre.replace(" ", "+") + ":wght@" + ";".join(pesos)
        for nombre, pesos in PESOS.items()
    )
    return f"https://fonts.googleapis.com/css2?{fam}&display=swap"


def bajar(url):
    return urllib.request.urlopen(
        urllib.request.Request(url, headers={"User-Agent": UA}), timeout=40
    ).read()


def main():
    usados = caracteres_del_sitio()
    conjunto = sorted(set(usados) | set(BASE))
    unicodes = ",".join(f"U+{ord(c):04X}" for c in conjunto)
    print(f"  caracteres en las paginas: {len(usados)} -> se recortan {len(conjunto)}")

    css = bajar(url_css()).decode("utf-8")
    os.makedirs(DESTINO, exist_ok=True)
    antes = 0
    despues = 0
    with tempfile.TemporaryDirectory() as tmp:
        for subset, cuerpo in BLOQUE.findall(css):
            if subset != "latin":
                continue
            familia = FAMILIA.search(cuerpo).group(1)
            peso = PESO.search(cuerpo).group(1)
            if peso not in PESOS.get(familia, []):
                continue
            nombre = f"{familia.lower().replace(' ', '-')}-{peso}.woff2"
            entero = os.path.join(tmp, "completo-" + nombre)
            with open(entero, "wb") as f:
                f.write(bajar(WOFF.search(cuerpo).group(1)))
            salida = os.path.join(DESTINO, nombre)
            subprocess.run(
                [os.path.join(os.path.dirname(sys.executable), "pyftsubset"), entero,
                 "--unicodes=" + unicodes, "--flavor=woff2",
                 "--layout-features=kern,liga,calt,ccmp",
                 "--output-file=" + salida],
                check=True, capture_output=True,
            )
            a, d = os.path.getsize(entero), os.path.getsize(salida)
            antes += a
            despues += d
            print(f"  {nombre:<28} {a/1024:6.1f} KB -> {d/1024:5.1f} KB")
    print(f"  {'TOTAL':<28} {antes/1024:6.1f} KB -> {despues/1024:5.1f} KB")


if __name__ == "__main__":
    main()
