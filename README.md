# Real Betits 🟢⚪

Sitio web del equipo **Real Betits** (parodia cariñosa del Real Betis), que juega en la
**Zapping Liga Premier — Sábado 2° DIV** organizada por [Liga Premier](https://copafacil.com/ligapremier-zapping)
y gestionada en Copa Fácil.

## Qué contiene

- **Home** con cartas de jugador estilo FIFA Ultimate Team (efecto hover con CSS puro).
- **Partidos**: resultados jugados y fixture por jugar (fecha, hora, rival).
- **Galería**: fotos de los partidos.

Todo **estático** (Astro, sin JS en el cliente salvo lo imprescindible).

## Estructura

```
.
├── data/
│   ├── liga.json        # tabla, fixture y galería (generado, versionado)
│   └── logos/           # escudos de los equipos de la división
├── scripts/
│   └── extraer-liga.py  # scraping de la liga desde Copa Fácil
└── (próximamente: src/, public/, astro.config.mjs …)
```

## Actualizar los datos

```bash
python3 scripts/extraer-liga.py
```

Reescribe `data/liga.json` y `data/logos/`. Solo usa la librería estándar de Python + `curl`.

### De dónde salen los datos

La web de Copa Fácil es una app **Flutter Web** (canvas), así que no se puede leer el HTML.
Los datos se obtienen de su API interna, que es pública y sin login:

| Qué | Endpoint |
|---|---|
| Info del torneo | `https://copafacil.com/request/event?id=-hdryi` |
| Partidos | `https://copafacil-web.firebaseio.com/events/-hdryi/matchs.json` |
| Galería | `https://copafacil-web.firebaseio.com/events/-hdryi/midia.json` |
| Escudos | `https://copafacil-storage.b-cdn.net/events%2F-hdryi%2Fx7miv%2Fteams%2F<id>.png` |

> ⚠️ Es una API **no oficial ni documentada**. Puede cambiar sin aviso. Los datos y escudos
> pertenecen a Copa Fácil y a los equipos de la liga; este repo solo los muestra.

## La liga

- **Torneo**: Zapping Liga Premier · Torneos Clausura
- **División**: Sábado 2° DIV Zapping (12 equipos, 2 grupos de 6)
- **Grupo de Real Betits**: B
- **Fechas**: 05/09/2026 → 28/11/2026
