// @ts-check
import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';

// https://astro.build/config
export default defineConfig({
  // URL pública del sitio. Se usa para las URLs canónicas y el sitemap.
  // No hace falta `base` porque Cloudflare Pages sirve en la raíz del dominio
  // (esto es lo que nos ahorramos al no usar GitHub Pages, donde el sitio
  // quedaría en /real-betits/ y todos los assets tendrían que llevar prefijo).
  site: 'https://real-betits.pages.dev',

  // El sitio es 100% estático: no hay servidor, no hay base de datos.
  output: 'static',

  // Al pasar el mouse por un enlace, el router ya trae la pagina siguiente por
  // atras. Medido: el clic tardaba 63-121 ms en tener la pagina lista; con esto
  // el HTML ya esta en memoria y solo queda el fade de la transicion.
  prefetch: { prefetchAll: true, defaultStrategy: 'hover' },

  // Genera /sitemap.xml con la lista de páginas y su última modificación.
  // El filtro deja fuera las páginas de trabajo (/cancha, /estilo), el diagrama
  // y la 404: no son contenido público. Las tres primeras, además, están
  // desautorizadas en public/robots.txt — el sitemap y el robots.txt dicen lo
  // mismo, que es justo lo que un buscador espera encontrar.
  integrations: [sitemap({ filter: (url) => !/\/(cancha|estilo|diagrama)\/|\/404/.test(url) })],
});
