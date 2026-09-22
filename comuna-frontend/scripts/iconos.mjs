// Extrae de @iconify-json/solar solo los íconos que usa la app y los deja en
// src/iconos-solar.json (unos pocos KB). Así los íconos funcionan sin red y el
// build no arrastra las 7.000 variantes del set.
//
//   node scripts/iconos.mjs      (se corre al agregar un ícono nuevo)

import { readFileSync, writeFileSync } from 'node:fs';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
const set = JSON.parse(readFileSync(require.resolve('@iconify-json/solar/icons.json'), 'utf8'));

export const USADOS = [
  'magnifer', 'chart-2', 'map-point-wave', 'documents', 'tag-price', 'sun', 'tram', 'square-academic-cap',
  'backpack', 'hospital', 'cart-large-2', 'leaf', 'ruler-angular', 'bed', 'bath', 'calendar', 'graph-down',
  'graph-up', 'info-circle', 'danger-triangle', 'arrow-right-up', 'buildings-2', 'database', 'close-circle',
  'home-smile', 'wallet-money', 'layers', 'shield-check', 'sort-vertical', 'map-point', 'city',
];

const icons = {};
for (const nombre of USADOS) {
  const clave = `${nombre}-bold-duotone`;
  if (!set.icons[clave]) throw new Error(`No existe solar:${clave}`);
  icons[nombre] = set.icons[clave].body;
}
writeFileSync(
  new URL('../src/iconos-solar.json', import.meta.url),
  JSON.stringify({ ancho: set.width ?? 24, alto: set.height ?? 24, icons }, null, 0) + '\n',
);
console.log(`✓ src/iconos-solar.json · ${USADOS.length} íconos Solar Duotone Bold (licencia CC BY 4.0, 480 Design)`);
