import { Icon } from '@iconify/react';
import iconos from '../iconos-solar.json';

// Íconos Solar Duotone Bold (offline; ver scripts/iconos.mjs). Decorativos por
// defecto: siempre van junto a un texto, así que se ocultan al lector de pantalla.
export default function Icono({ nombre, className = 'h-5 w-5', titulo }) {
  const body = iconos.icons[nombre];
  if (!body) return null;
  return (
    <Icon
      icon={{ body, width: iconos.ancho, height: iconos.alto }}
      className={className}
      aria-hidden={titulo ? undefined : true}
      aria-label={titulo}
      role={titulo ? 'img' : undefined}
    />
  );
}
