#!/usr/bin/env python3
"""
Extrae la data de la liga de Real Betits desde copafacil.com.

Fuente (NO oficial, es la API interna que usa la propia web de Copa Fácil):
  - Evento:      -hdryi        (Zapping Liga Premier)
  - División:    -hdryi@x7miv  (Sábado 2° DIV Zapping)

Endpoints usados (todos públicos, sin login):
  - https://copafacil.com/request/event?id=<evento>          -> info del torneo
  - https://copafacil-web.firebaseio.com/events/<evt>/matchs.json  -> todos los partidos
  - https://copafacil-web.firebaseio.com/events/<evt>/midia.json   -> galería/noticias
  - https://copafacil-storage.b-cdn.net/events%2F<evt>%2F<div>%2Fteams%2F<id>.png

Uso:  python3 extraer-liga.py
Salida: ~/real-betits/data/liga.json  + ~/real-betits/data/logos/
"""
import json, os, subprocess, collections, datetime as dt

EVT = "-hdryi"
DIV = "-hdryi@x7miv"
BASE = "https://copafacil-web.firebaseio.com"
SITE = "https://copafacil.com"
DATA = os.path.expanduser("~/real-betits/data")

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


def get_json(url):
    r = subprocess.run(["curl", "-s", "-m", "30", url], capture_output=True, text=True)
    try:
        return json.loads(r.stdout)
    except Exception:
        return None


def fdate(ms):
    if not ms:
        return None
    return dt.datetime.fromtimestamp(ms / 1000, dt.timezone(dt.timedelta(hours=-3))).strftime("%Y-%m-%d %H:%M")


def slug(name):
    for a, b in zip("áéíóúñÁÉÍÓÚÑ", "aeiounAEIOUN"):
        name = name.replace(a, b)
    return name.lower().replace(" ", "-")


def main():
    os.makedirs(DATA, exist_ok=True)

    matchs = get_json(f"{BASE}/events/{EVT}/matchs.json") or {}
    midia = get_json(f"{BASE}/events/{EVT}/midia.json") or {}
    info = get_json(f"{SITE}/request/event?id={EVT}") or {}

    sub = {k: v for k, v in matchs.items() if v.get("evt") == DIV}

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

    # --- tabla, POR GRUPO ---
    # El torneo tiene grupos (A, B) y la app muestra una tabla por grupo, no una global.
    # Los grupos se descubren por componentes conexas del grafo de partidos: dos equipos
    # que se enfrentan están en el mismo grupo. Así no hay que hardcodear los grupos.
    jugados = [(MAPPING.get(v["team1"], v["team1"]), MAPPING.get(v["team2"], v["team2"]), v)
               for v in sub.values() if v.get("st") == 3]
    todos = [(MAPPING.get(v["team1"], v["team1"]), MAPPING.get(v["team2"], v["team2"]))
             for v in sub.values()]

    padre = {n: n for n in set(sum([list(p) for p in todos], []))}
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
            g1, g2 = dtx.get("qt_g1", 0), dtx.get("qt_g2", 0)
            gf[t1] += g1; ga[t1] += g2; gf[t2] += g2; ga[t2] += g1
            pj[t1] += 1; pj[t2] += 1
            if g1 > g2:
                pts[t1] += 3; W[t1] += 1; L[t2] += 1
            elif g2 > g1:
                pts[t2] += 3; W[t2] += 1; L[t1] += 1
            else:
                pts[t1] += 1; pts[t2] += 1; D[t1] += 1; D[t2] += 1
        rows = []
        for i, n in enumerate(sorted(equipos, key=lambda n: (-pts[n], -(gf[n] - ga[n]), -gf[n])), 1):
            rows.append({"pos": i, "equipo": n, "pts": pts[n], "pj": pj[n], "w": W[n],
                         "d": D[n], "l": L[n], "gf": gf[n], "ga": ga[n], "gd": gf[n] - ga[n]})
        return rows

    # El nombre de la letra (A/B) NO se puede derivar de los datos: la app lo tiene por orden
    # de creación del grupo. Se ancla a un equipo conocido de cada grupo (confirmado en la UI).
    ANCLAS = {"A": "PICHULENSE FC", "B": "REAL BETITS"}
    ordenados = sorted(grupos.values(), key=lambda s: sorted(s)[0])
    table = {}
    usados = []
    for letra, ancla in ANCLAS.items():
        for equipos in ordenados:
            if ancla in equipos:
                table[letra] = tabla_de(equipos)
                usados.append(id(equipos))
                break
    for equipos in ordenados:  # grupos extra, si algún día hubiera más
        if id(equipos) in usados:
            continue
        table[f"G{len(table)+1}"] = tabla_de(equipos)

    # --- galería ---
    gallery = []
    for v in midia.values():
        i = v.get("i") or {}
        gallery.append({"titulo": v.get("leg"), "division": v.get("evt"),
                        "foto": i.get("url"), "album": i.get("urlP"),
                        "es_mi_division": v.get("evt") == "x7miv"})
    gallery.sort(key=lambda x: (x["titulo"] or ""))

    # --- logos ---
    logo_dir = os.path.join(DATA, "logos")
    os.makedirs(logo_dir, exist_ok=True)
    for tid, name in MAPPING.items():
        for ext in ("png", "jpg"):
            url = f"https://copafacil-storage.b-cdn.net/events%2F{EVT}%2Fx7miv%2Fteams%2F{tid}.{ext}?alt=media&token=1"
            p = os.path.join(logo_dir, f"{slug(name)}.{ext}")
            r = subprocess.run(["curl", "-s", "-m", "20", "-o", p, "-w", "%{http_code}", url],
                               capture_output=True, text=True)
            if r.stdout.strip() == "200" and os.path.getsize(p) > 0:
                break
            if os.path.exists(p):
                os.remove(p)

    dataset = {
        "fuente": f"{SITE}/-hdryi@x7miv",
        "torneo": info.get("info", {}),
        "mi_equipo": "REAL BETITS",
        "division_id": DIV,
        "tabla": table,
        "fixture": fixture,
        "galeria": gallery,
    }
    out = os.path.join(DATA, "liga.json")
    json.dump(dataset, open(out, "w"), ensure_ascii=False, indent=1)

    jug = sum(1 for x in fixture if x["jugado"])
    n_equipos = sum(len(rows) for rows in table.values())
    print(f"OK -> {out}")
    print(f"  partidos: {len(fixture)} ({jug} jugados, {len(fixture)-jug} pendientes)")
    print(f"  tabla: {len(table)} grupos / {n_equipos} equipos | galería: {len(gallery)} items")
    for g, rows in table.items():
        mia = next((r for r in rows if r["equipo"] == "REAL BETITS"), None)
        if mia:
            print(f"  REAL BETITS: {mia['pos']}° del grupo {g} ({mia['pts']} pts)")
    print(f"  logos: {len(os.listdir(logo_dir))}/12 descargados")


if __name__ == "__main__":
    main()
