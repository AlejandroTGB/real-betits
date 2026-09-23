/**
 * Los álbumes de fotos de NUESTRA división, resueltos por número de fecha.
 *
 * De dónde salen las fotos (dos capas distintas):
 *
 *   data/galeria/fecha-N.jpg      -> la portada que publica la app de Copa Fácil.
 *                                    Se usa de fondo en /partidos (el camino).
 *   data/galeria/fecha-N/NN.jpg   -> las fotos del partido, bajadas del Drive del
 *                                    torneo por scripts/extraer-liga.py.
 *
 * Se importan SIN `?url` a propósito: así Astro recibe los metadatos (ancho, alto,
 * formato) y puede optimizarlas con <Image>. Los originales pesan ~175 kB cada
 * uno; servirlos crudos sería tirar ancho de banda a la basura (en las portadas
 * medimos 929 kB -> 24 kB).
 *
 * El crédito NO se inventa: las fotos son de la fotografía oficial de la liga,
 * que es la que las publica en su Drive. El sitio las muestra y enlaza al álbum
 * completo, que es donde están en tamaño grande.
 */
import type { ImageMetadata } from 'astro';
import liga from '../../data/liga.json';

const PORTADAS = import.meta.glob('../../data/galeria/*.{jpg,jpeg,png}', {
  eager: true,
  import: 'default',
}) as Record<string, ImageMetadata>;

const DEL_PARTIDO = import.meta.glob('../../data/galeria/fecha-*/*.{jpg,jpeg,png}', {
  eager: true,
  import: 'default',
}) as Record<string, ImageMetadata>;

/** Las fotos de una fecha, en orden: 01, 02, 03… */
function fotosDe(n: number): ImageMetadata[] {
  const patron = new RegExp(`/fecha-${n}/\\d+\\.(jpe?g|png)$`, 'i');
  return Object.entries(DEL_PARTIDO)
    .filter(([ruta]) => patron.test(ruta))
    // alfabético, y funciona porque los nombres van con cero adelante
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([, img]) => img);
}

/** La portada de una fecha (la que usa el camino como fondo). */
export function fotoDeFecha(n: number): ImageMetadata | null {
  for (const [ruta, img] of Object.entries(PORTADAS)) {
    const m = (ruta.split('/').pop() ?? '').match(/^fecha-(\d+)\.(jpe?g|png)$/i);
    if (m && Number(m[1]) === n) return img;
  }
  return null;
}

/**
 * Una entrada de `galeria` en liga.json, tal como la publica la app.
 *
 * `carpeta` y `fotos_en_nuestra_carpeta` los agrega el script, y solo están en
 * los álbumes de nuestra división que tengan turno resuelto en
 * data/galeria-carpetas.json. Por eso son opcionales: el sitio tiene que saber
 * funcionar sin ellos.
 */
interface EntradaGaleria {
  titulo: string | null;
  division: string | null;
  foto: string | null;
  album: string | null;
  es_mi_division: boolean;
  carpeta?: string | null;
  fotos_en_nuestra_carpeta?: number | null;
}

export interface Album {
  /** Número de fecha (1, 2, 3…), para cruzarlo con JORNADAS en lib/liga.ts. */
  fecha: number;
  titulo: string;
  /** Link al álbum completo, en el Drive del torneo. */
  album: string | null;
  /** Portada que publica la app. */
  portada: ImageMetadata | null;
  /** Las fotos del partido que tenemos en el repo. */
  fotos: ImageMetadata[];
  /** Cuántas fotos tiene la carpeta nuestra en Drive (para el botón). */
  total: number | null;
}

/**
 * Los álbumes de nuestra división, del más viejo al más nuevo.
 *
 * Solo los nuestros: las otras 9 galerías son de otras categorías y no nos
 * representan (la app las publica todas juntas en la misma lista).
 */
export const ALBUMES: Album[] = (liga.galeria as EntradaGaleria[])
  .filter((g) => g.es_mi_division)
  .map((g) => {
    const m = (g.titulo ?? '').match(/fecha\s*(\d+)/i);
    return {
      fecha: m ? Number(m[1]) : 0,
      titulo: (g.titulo ?? '').trim(),
      album: g.album,
      portada: m ? fotoDeFecha(Number(m[1])) : null,
      fotos: m ? fotosDe(Number(m[1])) : [],
      total: g.fotos_en_nuestra_carpeta ?? null,
    };
  })
  .filter((a) => a.fecha > 0)
  .sort((a, b) => a.fecha - b.fecha);
