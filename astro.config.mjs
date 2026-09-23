// @ts-check
import { defineConfig } from 'astro/config';

// https://astro.build/config
export default defineConfig({
  // URL pública del sitio. Se usa para las URLs canónicas y el sitemap.
  // No hace falta `base` porque Cloudflare Pages sirve en la raíz del dominio
  // (esto es lo que nos ahorramos al no usar GitHub Pages, donde el sitio
  // quedaría en /real-betits/ y todos los assets tendrían que llevar prefijo).
  site: 'https://real-betits.pages.dev',

  // El sitio es 100% estático: no hay servidor, no hay base de datos.
  output: 'static',
});
