/**
 * Escudos de los equipos, resueltos por nombre.
 *
 * Los escudos viven en data/logos/ con el nombre del equipo en formato slug
 * (ej: "ATLETICO CIRUJA" -> atletico-ciruja.png). Acá se buscan por nombre para
 * no tener que mantener un diccionario a mano.
 *
 * OJO: no todos los equipos tienen escudo subido en Copa Fácil. Si no hay,
 * devuelve null y quien lo use decide qué hacer (nosotros reservamos el espacio
 * igual, para que la fila no quede desbalanceada).
 */
import propio from '../assets/escudo.png';

const ARCHIVOS = import.meta.glob('../../data/logos/*.{png,jpg}', {
  eager: true,
  query: '?url',
  import: 'default',
}) as Record<string, string>;

/** "BÁRBAROS DE ÉLITE" -> "barbaros-de-elite" */
export function slugEquipo(nombre: string): string {
  return nombre
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')   // saca los acentos
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-|-$/g, '');
}

/**
 * Nuestro escudo: el asset LOCAL, el mismo que usan el navbar, el hero y las
 * cartas de jugador.
 *
 * ⚠️ Para Real Betits NO usar `escudoDe(MI_EQUIPO)`. Copa Fácil tiene su propia
 * versión subida (data/logos/real-betits.png, 200x240) y NO es la buena: la
 * nuestra está recortada del Instagram del equipo, en alta. Usar la de la liga
 * hace que el escudo se vea distinto según la página.
 */
export const escudoPropio: string = propio.src;

export function escudoDe(nombre: string): string | null {
  const buscado = slugEquipo(nombre);
  for (const [ruta, url] of Object.entries(ARCHIVOS)) {
    const archivo = ruta.split('/').pop() ?? '';
    if (archivo === `${buscado}.png` || archivo === `${buscado}.jpg`) return url;
  }
  return null;
}
