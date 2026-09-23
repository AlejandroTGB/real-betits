/**
 * Lógica de la liga: leer data/liga.json y sacar cosas útiles.
 *
 * OJO con las fechas: en liga.json vienen como texto local de Chile
 * ("2026-09-26 19:00"). Si las paso por `new Date("2026-09-26 19:00")` el
 * resultado depende de la zona horaria de la máquina que compila — y el
 * servidor de Cloudflare compila en UTC. Por eso las desarmo a mano y formateo
 * con timeZone 'UTC': así la fecha que se muestra es SIEMPRE la misma, sin
 * importar dónde se construya el sitio.
 */
import liga from '../../data/liga.json';

export interface Partido {
  id: string;
  fecha: string | null;
  ronda_id: string | null;
  equipo1: string;
  equipo2: string;
  goles1: number | null;
  goles2: number | null;
  jugado: boolean;
}

/** Una fila de la tabla de posiciones. */
export interface FilaTabla {
  pos: number;
  equipo: string;
  pts: number;
  pj: number;
  w: number;
  d: number;
  l: number;
  gf: number;
  ga: number;
  gd: number;
}

const PARTIDOS = liga.fixture as Partido[];
const TABLA = liga.tabla as Record<string, FilaTabla[]>;

const MESES = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
  'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre'];
const DIAS = ['domingo', 'lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado'];

function trozos(fecha: string) {
  const m = fecha.match(/(\d{4})-(\d{2})-(\d{2})[ T](\d{2}):(\d{2})/);
  if (!m) return null;
  return { y: +m[1], mes: +m[2], dia: +m[3], hora: +m[4], min: +m[5] };
}

/** "2026-09-26 19:00" -> "sábado 26 de septiembre · 19:00" */
export function fechaLarga(fecha: string | null): string {
  const t = fecha ? trozos(fecha) : null;
  if (!t) return 'fecha por confirmar';
  const d = new Date(Date.UTC(t.y, t.mes - 1, t.dia));
  return `${DIAS[d.getUTCDay()]} ${t.dia} de ${MESES[t.mes - 1]} · ${String(t.hora).padStart(2, '0')}:${String(t.min).padStart(2, '0')}`;
}

/** Solo la fecha corta: "26/09" */
export function fechaCorta(fecha: string | null): string {
  const t = fecha ? trozos(fecha) : null;
  return t ? `${String(t.dia).padStart(2, '0')}/${String(t.mes).padStart(2, '0')}` : '—';
}

/** Partes sueltas, para el talón del ticket: "26" / "SEP" / 2026 */
export function fechaPartes(fecha: string | null) {
  const t = fecha ? trozos(fecha) : null;
  if (!t) return { dia: '–', mes: 'S/F', anio: null as number | null, hora: null as string | null };
  return {
    dia: String(t.dia).padStart(2, '0'),
    mes: MESES[t.mes - 1].slice(0, 3).toUpperCase(),
    anio: t.y as number | null,
    hora: `${String(t.hora).padStart(2, '0')}:${String(t.min).padStart(2, '0')}` as string | null,
  };
}

export const MI_EQUIPO = liga.mi_equipo;

/** ¿Juega Real Betits este partido? */
export const esMio = (p: Partido) => p.equipo1 === MI_EQUIPO || p.equipo2 === MI_EQUIPO;

/** El rival de un partido nuestro. */
export const rival = (p: Partido) => (p.equipo1 === MI_EQUIPO ? p.equipo2 : p.equipo1);

/**
 * ¿Real Betits aparece PRIMERO en el listado del partido?
 *
 * ⚠️ Esto NO significa "local". En esta liga se juega siempre en la misma cancha
 * y el fixture lista los equipos en un orden cualquiera: local y visita no
 * existen. Sirve solo para saber cuál de los dos marcadores es el nuestro.
 */
export const soyEquipo1 = (p: Partido) => p.equipo1 === MI_EQUIPO;

/** Nuestros goles. `null` si ese lado del marcador no está cargado. */
export const golesNuestros = (p: Partido) => (soyEquipo1(p) ? p.goles1 : p.goles2);

/** Goles del rival. `null` si ese lado del marcador no está cargado. */
export const golesRival = (p: Partido) => (soyEquipo1(p) ? p.goles2 : p.goles1);

/**
 * Resultado visto desde nuestro lado: 'G' ganado, 'E' empatado, 'P' perdido.
 *
 * Devuelve `null` en dos casos distintos que quien lo use debe tratar igual de
 * bien: el partido todavía no se jugó, O se jugó pero falta un lado del
 * marcador. En la liga hay 2 partidos jugados con `null` de un lado (los de
 * ATLETICO CIRUJA), así que no es un caso teórico.
 */
export function resultado(p: Partido): 'G' | 'E' | 'P' | null {
  if (!p.jugado) return null;
  const a = golesNuestros(p);
  const b = golesRival(p);
  if (a === null || b === null) return null;
  return a > b ? 'G' : a === b ? 'E' : 'P';
}

/** Nuestro marcador, "5-3". "—" si falta jugar, "s/d" si falta el dato. */
export function marcadorTexto(p: Partido): string {
  if (!p.jugado) return '—';
  const a = golesNuestros(p);
  const b = golesRival(p);
  if (a === null || b === null) return 's/d';
  return `${a}-${b}`;
}

/** Marcador de cualquier partido, tal cual está. Ej: "4 - s/d" */
export function marcadorDe(p: Partido): string {
  if (!p.jugado) return '—';
  return `${p.goles1 ?? 's/d'} - ${p.goles2 ?? 's/d'}`;
}

/**
 * Próximo partido NUESTRO: el pendiente con fecha más cercana en el que juega
 * Real Betits.
 *
 * OJO: hay que filtrar por nuestro equipo. Una fecha tiene 6 partidos en
 * horarios distintos; si no se filtra, devuelve el primero de la fecha
 * (ej: "BÁRBAROS DE ÉLITE vs COLGATE" a las 18:00) en vez del nuestro.
 */
export function proximoPartido(): Partido | null {
  const pendientes = PARTIDOS
    .filter((p) => !p.jugado && p.fecha && esMio(p))
    .sort((a, b) => (a.fecha! < b.fecha! ? -1 : 1));
  return pendientes[0] ?? null;
}

/** Nuestros resultados: los jugados, del más reciente al más viejo. */
export function ultimosResultados(): Partido[] {
  return PARTIDOS
    .filter((p) => p.jugado && esMio(p))
    .sort((a, b) => (a.fecha! > b.fecha! ? -1 : 1));
}

/**
 * Nuestros 5 partidos, en orden cronológico.
 *
 * No hace falta reordenar: el script ya deja el fixture ordenado por fecha y
 * empuja al final los que no tienen fecha, así que el orden del archivo ES el
 * orden del calendario.
 */
export const NUESTROS = PARTIDOS.filter(esMio);

export interface Jornada {
  /** 1, 2, 3… en orden de calendario. */
  n: number;
  nuestro: Partido;
  rival: string;
  /** Los otros 5 partidos del grupo en la misma jornada. */
  resto: Partido[];
}

export const JORNADAS: Jornada[] = NUESTROS.map((p, i) => ({
  n: i + 1,
  nuestro: p,
  rival: rival(p),
  resto: PARTIDOS.filter((q) => q.ronda_id === p.ronda_id && q.id !== p.id),
}));

/** La fila de CUALQUIER equipo en la tabla. Sirve para la del rival. */
export function filaDe(equipo: string) {
  for (const [grupo, filas] of Object.entries(TABLA)) {
    const f = filas.find((x) => x.equipo === equipo);
    if (f) return { grupo, ...f };
  }
  return null;
}

/** La fila de Real Betits en la tabla, con su grupo. */
export function miFila() {
  return filaDe(MI_EQUIPO);
}
