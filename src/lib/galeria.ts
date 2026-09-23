/**
 * Fotos de la galería de NUESTRA división, resueltas por número de fecha.
 *
 * El script las baja a data/galeria/ como fecha-1.jpg, fecha-2.jpg… así que acá
 * se buscan por número de fecha, sin diccionario que mantener (mismo criterio
 * que los escudos en escudos.ts).
 *
 * Se importan SIN `?url` a propósito: así Astro recibe los metadatos (ancho,
 * alto, formato) y puede optimizarlas con <Image>. Los originales de Copa Fácil
 * pesan ~1 MB cada uno y de fondo se ven al ~15%: mandarlos crudos sería tirar
 * ancho de banda a la basura.
 */
import type { ImageMetadata } from 'astro';

const FOTOS = import.meta.glob('../../data/galeria/*.{jpg,jpeg,png}', {
  eager: true,
  import: 'default',
}) as Record<string, ImageMetadata>;

export function fotoDeFecha(n: number): ImageMetadata | null {
  for (const [ruta, img] of Object.entries(FOTOS)) {
    const m = (ruta.split('/').pop() ?? '').match(/^fecha-(\d+)\.(jpe?g|png)$/i);
    if (m && Number(m[1]) === n) return img;
  }
  return null;
}
