/**
 * Lógica y datos de la plantilla, compartidos entre la home y /cancha.
 *
 * Regla del proyecto:
 *   src/lib/        -> lógica y datos (no sabe nada de cómo se ve)
 *   src/components/ -> piezas visuales reutilizables
 *   src/layouts/    -> moldes de página completa
 *   src/pages/      -> una URL por archivo
 *
 * Este archivo existe para NO repetir la lista de titulares en dos páginas.
 */
import datos from '../data/plantilla.json';

/** Stats de las cartas: todos 67 a propósito hasta que se definan de verdad. */
export const NOTA = 67;
export const STATS = { rit: 67, tir: 67, pas: 67, reg: 67, def: 67, fis: 67 };

/** Iniciales del nombre (las dos primeras palabras). */
export const iniciales = (nombre: string) =>
  nombre
    .split(/\s+/)
    .slice(0, 2)
    .map((p) => p[0])
    .join('')
    .toUpperCase()
    .replace(/[^A-ZÁÉÍÓÚÑ]/g, '');

export interface Puesto {
  nombre: string;
  /** Etiqueta corta: DEL, MED, DEF, ARQ */
  pos: string;
  /** % horizontal del centro de la carta sobre la cancha */
  left: number;
  /** % vertical medido desde el arco propio (abajo) */
  bottom: number;
}

/**
 * Los 7 puestos de la 1-2-3-1, según las posiciones reales que indicó el equipo.
 *
 * Ordenados de lejos a cerca (delantero -> arquero) para que el apilado en 3D
 * salga natural: las cartas de adelante se dibujan primero y las de atrás
 * quedan encima, como en una cancha vista desde atrás del arco propio.
 *
 * Nota: el arquero y el delantero no se eligieron a gusto — Jose Ignacio Pineda
 * es el ÚNICO arquero del plantel y Roberto Fica el ÚNICO delantero, según la
 * posición que cada uno tiene registrada en Copa Fácil.
 */
export const TITULARES: Puesto[] = [
  // delantero
  { nombre: 'Roberto Fica', pos: 'DEL', left: 50, bottom: 80 },
  // medios: izquierda, centro, derecha
  { nombre: 'Cristóbal Zecchetto', pos: 'MED', left: 17, bottom: 52 },
  { nombre: 'Alejandro Torres', pos: 'MED', left: 50, bottom: 52 },
  { nombre: 'Francisco Pizarro', pos: 'MED', left: 83, bottom: 52 },
  // centrales: izquierdo y derecho
  { nombre: 'Diego Toledo', pos: 'DEF', left: 27, bottom: 24 },
  { nombre: 'Pablo García', pos: 'DEF', left: 73, bottom: 24 },
  // arco propio
  { nombre: 'Jose Ignacio Pineda (A)', pos: 'ARQ', left: 50, bottom: 4 },
];

/** Nombres de los 7 titulares, para saber rápido quién está en el equipo. */
export const ES_TITULAR = new Set(TITULARES.map((t) => t.nombre));

/** Todo el plantel registrado en la liga. */
export const PLANTEL = datos.jugadores;

/** Los que no están en el equipo titular. */
export const BANCA = PLANTEL.filter((j) => !ES_TITULAR.has(j.nombre));

/** Posición larga de la liga -> etiqueta corta de la carta. */
const ETIQUETA: Record<string, string> = {
  arquero: 'ARQ',
  defensa: 'DEF',
  medio: 'MED',
  delantero: 'DEL',
};

export const etiquetaPosicion = (pos: string | null) =>
  ETIQUETA[pos ?? ''] ?? 'S/P';

/** Líneas del plantel, en el orden en que se lee una lista de buena fe. */
const ORDEN_LINEAS = ['arquero', 'defensa', 'medio', 'delantero'];

const pesoLinea = (pos: string | null) => {
  const i = ORDEN_LINEAS.indexOf(pos ?? '');
  return i === -1 ? ORDEN_LINEAS.length : i;   // los "sin puesto" al final
};

/**
 * Los 16 ordenados por línea. El sort de JS es estable, así que dentro de cada
 * línea se conserva el orden original del archivo.
 */
export const PLANTEL_ORDENADO = [...PLANTEL].sort(
  (a, b) => pesoLinea(a.posicion) - pesoLinea(b.posicion)
);

/**
 * Los que quedan fuera del equipo titular, en el mismo orden por línea.
 *
 * ⚠️ Es FÚTBOL 7: el equipo titular son 7 jugadores (1-2-3-1), no 11. Por eso
 * acá quedan 9 y no 5. Hablar de "el once" en este proyecto está mal.
 */
export const BANCA_ORDENADA = PLANTEL_ORDENADO.filter(
  (j) => !ES_TITULAR.has(j.nombre)
);
