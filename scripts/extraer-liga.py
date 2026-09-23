#!/usr/bin/env python3
"""
Extrae la data de la liga de Real Betits desde copafacil.com.

Fuente (NO oficial, es la API interna que usa la propia web de Copa Fácil):
  - Evento:      -hdryi        (Zapping Liga Premier)
  - División:    -hdryi@x7miv  (Sábado 2° DIV Zapping)

Endpoints usados (todos públicos, sin login):
  - https://copafacil.com/request/event?id=<evento>                -> info del torneo
  - https://copafacil-web.firebaseio.com/events/<evt>/matchs.json  -> todos los partidos
  - https://copafacil-web.firebaseio.com/events/<evt>/midia.json   -> galería/noticias
  - https://copafacil-storage.b-cdn.net/events%2F<evt>%2F<div>%2Fteams%2F<id>.png

Uso:   python3 scripts/extraer-liga.py
Salida: data/liga.json  +  data/logos/

RED DE SEGURIDAD: si la descarga falla o los datos nuevos salen incoherentes, el script
sale con código != 0 y **NO toca** el liga.json existente. Así el sitio (y el Action)
se quedan con el último dato bueno en vez de publicar basura.
"""
import json
import os
import re
import sys
import time
import collections
import subprocess
import datetime as dt

EVT = "-hdryi"
DIV = "-hdryi@x7miv"
BASE = "https://copafacil-web.firebaseio.com"
SITE = "https://copafacil.com"
STORAGE = "https://copafacil-storage.b-cdn.net"

# Rutas relativas al repo (funciona igual en local que en GitHub Actions)
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(REPO, "data")
OUT = os.path.join(DATA, "liga.json")
LOGO_DIR = os.path.join(DATA, "logos")
GAL_DIR = os.path.join(DATA, "galeria")

# IDs internos de equipo -> nombre (confirmado cruzando GF/GA/Pts con la tabla de la app)
MAPPING = {
    "-P-vTZa_rpCMQP2D0did": "BPC FC",
    "-P-vTZa_rpCMQP2D0die": "BÁRBAROS DE ÉLITE",
    "-P-vTZa_rpCMQP2D0dif": "DEPORTIVO RESACA",
    "-P-vTZa_rpCMQP2D0dir": "COLGATE",
    "-P-vVV84wjVYWeOQAvw5": "REALISTIC DREAMS",
    "-P-vVZdi2KlVJaVtO4SZ": "LOS NOTA LOKOS",
    "-P-vV_fyB7xeiWof2wXV": "LA SUTRONETA",
    "-P-vVbtxTNYsH0BgtFoh": "PICHULENSE FC",
    "-P-vVcrkzteEnZpBsC4F": "REAL BETITS",
    "-P-vVe5hVNeroNoA9en_": "AC WARISNAKE",
    "-P-vVfqNkFpq2RHdt1qP": "AC DEPORTES TE COJO",
    "-P-vVoipzeWzxI4lIusd": "ATLETICO CIRUJA",
}


def fail(msg):
    print(f"ERROR: {msg}", file=sys.stderr)
    print("NO se modificó data/liga.json — se conserva el último dato bueno.", file=sys.stderr)
    sys.exit(1)


def get_json(url, intentos=3):
    """Baja y parsea JSON, con reintentos. Devuelve None si no lo logra."""
    for i in range(intentos):
        r = subprocess.run(["curl", "-sS", "-m", "30", "-w", "\n%{http_code}", url],
                           capture_output=True, text=True)
        if r.returncode == 0 and r.stdout:
            cuerpo, _, code = r.stdout.rpartition("\n")
            if code.strip() == "200":
                try:
                    return json.loads(cuerpo)
                except json.JSONDecodeError:
                    pass
        if i < intentos - 1:
            time.sleep(2 * (i + 1))
    return None


def fdate(ms):
    if not ms:
        return None
    return dt.datetime.fromtimestamp(ms / 1000, dt.timezone(dt.timedelta(hours=-3))).strftime("%Y-%m-%d %H:%M")


def slug(name):
    for a, b in zip("áéíóúñÁÉÍÓÚÑ", "aeiounAEIOUN"):
        name = name.replace(a, b)
    return name.lower().replace(" ", "-")


def construir_tabla(sub):
    """Tabla POR GRUPO. Los grupos salen de las componentes conexas del grafo de partidos
    (dos equipos que se enfrentan comparten grupo), así que no hay que hardcodearlos."""
    todos = [(MAPPING.get(v["team1"], v["team1"]), MAPPING.get(v["team2"], v["team2"]))
             for v in sub.values()]
    jugados = [(MAPPING.get(v["team1"], v["team1"]), MAPPING.get(v["team2"], v["team2"]), v)
               for v in sub.values() if v.get("st") == 3]

    padre = {n: n for n in {x for par in todos for x in par}}

    def find(x):
        while padre[x] != x:
            padre[x] = padre[padre[x]]
            x = padre[x]
        return x

    for a, b in todos:
        ra, rb = find(a), find(b)
        if ra != rb:
            padre[ra] = rb

    grupos = collections.defaultdict(set)
    for n in padre:
        grupos[find(n)].add(n)

    def tabla_de(equipos):
        gf, ga, pj = collections.Counter(), collections.Counter(), collections.Counter()
        pts, W, D, L = (collections.Counter() for _ in range(4))
        for t1, t2, v in jugados:
            if t1 not in equipos:
                continue
            dtx = v.get("dt") or {}
            # OJO: un partido jugado puede traer solo un lado del marcador; el ausente es 0.
            g1, g2 = dtx.get("qt_g1", 0), dtx.get("qt_g2", 0)
            gf[t1] += g1; ga[t1] += g2; gf[t2] += g2; ga[t2] += g1
            pj[t1] += 1; pj[t2] += 1
            if g1 > g2:
                pts[t1] += 3; W[t1] += 1; L[t2] += 1
            elif g2 > g1:
                pts[t2] += 3; W[t2] += 1; L[t1] += 1
            else:
                pts[t1] += 1; pts[t2] += 1; D[t1] += 1; D[t2] += 1
        return [{"pos": i, "equipo": n, "pts": pts[n], "pj": pj[n], "w": W[n], "d": D[n],
                 "l": L[n], "gf": gf[n], "ga": ga[n], "gd": gf[n] - ga[n]}
                for i, n in enumerate(sorted(equipos, key=lambda n: (-pts[n], -(gf[n] - ga[n]), -gf[n])), 1)]

    # La LETRA (A/B) no se deduce de los datos: es orden interno de la app. Se ancla
    # a un equipo conocido de cada grupo (confirmado en la UI de copafacil).
    ANCLAS = {"A": "PICHULENSE FC", "B": "REAL BETITS"}
    ordenados = sorted(grupos.values(), key=lambda s: sorted(s)[0])
    table, usados = {}, []
    for letra, ancla in ANCLAS.items():
        for equipos in ordenados:
            if ancla in equipos:
                table[letra] = tabla_de(equipos)
                usados.append(id(equipos))
                break
    for equipos in ordenados:  # grupos extra, si algún día hubiera más de dos
        if id(equipos) not in usados:
            table[f"G{len(table) + 1}"] = tabla_de(equipos)
    return table


def descargar_logos():
    os.makedirs(LOGO_DIR, exist_ok=True)
    bajar = []
    for tid, name in MAPPING.items():
        for ext in ("png", "jpg"):
            url = f"{STORAGE}/events%2F{EVT}%2Fx7miv%2Fteams%2F{tid}.{ext}?alt=media&token=1"
            dest = os.path.join(LOGO_DIR, f"{slug(name)}.{ext}")
            if os.path.exists(dest) and os.path.getsize(dest) > 0:
                break  # ya lo tenemos, no re-descargar (evita diffs inútiles)
            r = subprocess.run(["curl", "-s", "-m", "20", "-o", dest, "-w", "%{http_code}", url],
                               capture_output=True, text=True)
            if r.stdout.strip() == "200" and os.path.exists(dest) and os.path.getsize(dest) > 0:
                bajar.append(name)
                break
            if os.path.exists(dest):
                os.remove(dest)  # 404 -> no dejar archivo vacío
    return bajar


def fecha_de_titulo(titulo):
    """'Fotos Fecha 1 ⚽️🔥2da Div 05/09' -> 1.  None si no se puede leer."""
    m = re.search(r"fecha\s*(\d+)", (titulo or "").lower())
    return int(m.group(1)) if m else None


def descargar_galeria(gallery):
    """Baja las portadas de los álbumes de NUESTRA división a data/galeria/.

    Nombre determinista (fecha-1.jpg) para que el sitio las resuelva por número
    de fecha, igual que los escudos se resuelven por nombre de equipo.

    Solo la de nuestra división: las demás galerías son de otras categorías y no
    nos representan. Si un álbum no se puede asociar a una fecha, se saltea.
    """
    os.makedirs(GAL_DIR, exist_ok=True)
    bajadas = []
    for g in gallery:
        if not g.get("es_mi_division") or not g.get("foto"):
            continue
        n = fecha_de_titulo(g.get("titulo"))
        if n is None:
            continue
        dest = os.path.join(GAL_DIR, f"fecha-{n}.jpg")
        if os.path.exists(dest) and os.path.getsize(dest) > 0:
            continue   # ya la tenemos: no re-descargar (evita diffs inútiles)
        r = subprocess.run(["curl", "-s", "-L", "-m", "30", "-o", dest, "-w", "%{http_code}", g["foto"]],
                           capture_output=True, text=True)
        if r.stdout.strip() == "200" and os.path.exists(dest) and os.path.getsize(dest) > 0:
            bajadas.append(f"fecha-{n}")
        elif os.path.exists(dest):
            os.remove(dest)   # no dejar un archivo vacío o a medio bajar
    return bajadas


def main():
    os.makedirs(DATA, exist_ok=True)

    matchs = get_json(f"{BASE}/events/{EVT}/matchs.json")
    if not isinstance(matchs, dict) or not matchs:
        fail("no se pudo descargar la lista de partidos (¿API caída o cambiada?)")

    midia = get_json(f"{BASE}/events/{EVT}/midia.json") or {}
    info = get_json(f"{SITE}/request/event?id={EVT}") or {}

    sub = {k: v for k, v in matchs.items() if v.get("evt") == DIV}
    if not sub:
        fail(f"la división {DIV} no devolvió ningún partido")

    # --- fixture ---
    fixture = []
    for k, v in sub.items():
        dtx = v.get("dt") or {}
        fixture.append({
            "id": k,
            "fecha": fdate(v.get("d_i")),
            "ronda_id": v.get("m_set"),
            "equipo1": MAPPING.get(v["team1"], v["team1"]),
            "equipo2": MAPPING.get(v["team2"], v["team2"]),
            "goles1": dtx.get("qt_g1"),
            "goles2": dtx.get("qt_g2"),
            "jugado": v.get("st") == 3,
        })
    fixture.sort(key=lambda x: (x["fecha"] or "9999", x["id"]))

    table = construir_tabla(sub)

    # --- galería ---
    gallery = []
    for v in midia.values():
        i = v.get("i") or {}
        gallery.append({"titulo": v.get("leg"), "division": v.get("evt"),
                        "foto": i.get("url"), "album": i.get("urlP"),
                        "es_mi_division": v.get("evt") == "x7miv"})
    gallery.sort(key=lambda x: (x["titulo"] or ""))

    # ---------- VALIDACIÓN: no degradar lo que ya teníamos ----------
    jugados_nuevos = sum(1 for x in fixture if x["jugado"])
    if os.path.exists(OUT):
        try:
            viejo = json.load(open(OUT))
            jugados_viejos = sum(1 for x in viejo.get("fixture", []) if x.get("jugado"))
            if jugados_nuevos < jugados_viejos:
                fail(f"regresión: ahora hay {jugados_nuevos} partidos jugados y antes había "
                     f"{jugados_viejos}. Los partidos jugados no deberían desaparecer.")
        except (json.JSONDecodeError, OSError):
            print("aviso: no se pudo leer el liga.json previo, se sobrescribe", file=sys.stderr)

    if not table or not any(table.values()):
        fail("la tabla de posiciones salió vacía")

    # --- logos y fotos de la galería ---
    nuevos_logos = descargar_logos()
    nuevas_fotos = descargar_galeria(gallery)

    # Sin timestamp a propósito: así el archivo solo cambia cuando cambian los DATOS,
    # y el Action no hace un commit diario vacío. La fecha queda en el historial de git.
    dataset = {
        "fuente": f"{SITE}/{DIV}",
        "torneo": info.get("info", {}),
        "mi_equipo": "REAL BETITS",
        "division_id": DIV,
        "tabla": table,
        "fixture": fixture,
        "galeria": gallery,
    }
    with open(OUT, "w") as f:
        json.dump(dataset, f, ensure_ascii=False, indent=1)
        f.write("\n")

    n_equipos = sum(len(rows) for rows in table.values())
    print(f"OK -> {os.path.relpath(OUT, REPO)}")
    print(f"  partidos: {len(fixture)} ({jugados_nuevos} jugados, {len(fixture) - jugados_nuevos} pendientes)")
    print(f"  tabla: {len(table)} grupos / {n_equipos} equipos | galería: {len(gallery)} items")
    for g, rows in table.items():
        mia = next((r for r in rows if r["equipo"] == "REAL BETITS"), None)
        if mia:
            print(f"  REAL BETITS: {mia['pos']}° del grupo {g} ({mia['pts']} pts)")
    print(f"  logos: {len(os.listdir(LOGO_DIR))} archivos"
          + (f" (nuevos: {', '.join(nuevos_logos)})" if nuevos_logos else ""))
    print(f"  fotos de galería: {len(os.listdir(GAL_DIR))} archivos"
          + (f" (nuevas: {', '.join(nuevas_fotos)})" if nuevas_fotos else ""))


if __name__ == "__main__":
    main()
