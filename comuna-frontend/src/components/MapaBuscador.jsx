import { useEffect, useRef } from 'react';
import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import { MapboxOverlay } from '@deck.gl/mapbox';
import { ScatterplotLayer } from '@deck.gl/layers';
import { num } from '../api';

const ESTILO = 'https://tiles.openfreemap.org/styles/positron';

// Del puntaje al color: gris (bajo) → teal oscuro (alto), en el mismo tono del sistema.
function colorPuntaje(p) {
  const a = [214, 211, 209];
  const b = [15, 84, 79];
  const t = p ?? 0;
  return a.map((v, i) => Math.round(v + (b[i] - v) * t));
}

export default function MapaBuscador({ resultados, lugares, categorias, seleccionado, onSeleccionar }) {
  const cont = useRef(null);
  const mapa = useRef(null);
  const overlay = useRef(null);

  useEffect(() => {
    const m = new maplibregl.Map({ container: cont.current, style: ESTILO, center: [-73.06, -36.83], zoom: 11 });
    m.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'top-right');
    const o = new MapboxOverlay({ interleaved: false, layers: [] });
    m.addControl(o);
    mapa.current = m;
    overlay.current = o;
    return () => m.remove();
  }, []);

  // Encuadra los mejores resultados cuando cambian.
  useEffect(() => {
    const m = mapa.current;
    const pts = resultados.slice(0, 40).filter((r) => r.aviso.latitud != null);
    if (!m || !pts.length) return;
    const b = new maplibregl.LngLatBounds();
    pts.forEach((r) => b.extend([r.aviso.longitud, r.aviso.latitud]));
    m.fitBounds(b, { padding: 50, maxZoom: 14.5, duration: 600 });
  }, [resultados]);

  useEffect(() => {
    if (!overlay.current) return;
    const avisos = resultados.filter((r) => r.aviso.latitud != null).slice(0, 300);
    const puntos = Object.entries(lugares || {}).flatMap(([cat, lista]) =>
      categorias.includes(cat) ? lista.map((p) => ({ lat: p[0], lon: p[1], nombre: p[2], cat })) : [],
    );
    overlay.current.setProps({
      layers: [
        new ScatterplotLayer({
          id: 'lugares',
          data: puntos,
          getPosition: (p) => [p.lon, p.lat],
          getRadius: 28,
          radiusMinPixels: 3,
          getFillColor: [41, 37, 36, 220],
          getLineColor: [255, 255, 255],
          lineWidthMinPixels: 1,
          stroked: true,
          pickable: true,
        }),
        new ScatterplotLayer({
          id: 'resultados',
          data: [...avisos].reverse(), // los mejores se dibujan encima
          getPosition: (r) => [r.aviso.longitud, r.aviso.latitud],
          getRadius: (r) => (r.aviso.url === seleccionado ? 95 : 55),
          radiusMinPixels: 4,
          getFillColor: (r) => [...colorPuntaje(r.total), 235],
          getLineColor: (r) => (r.aviso.url === seleccionado ? [245, 158, 11] : [255, 255, 255]),
          lineWidthMinPixels: 1.5,
          stroked: true,
          pickable: true,
          onClick: ({ object }) => object && onSeleccionar?.(object.aviso.url),
          updateTriggers: { getRadius: seleccionado, getLineColor: seleccionado },
        }),
      ],
      getTooltip: ({ object: o }) => {
        if (!o) return null;
        if (o.cat) return { text: o.nombre || 'Sin nombre' };
        const a = o.aviso;
        return {
          html: `<strong>${a.titulo || ''}</strong><br>${num(a.precio_uf)} UF${
            o.total != null ? ` · ${Math.round(o.total * 100)} % de calce` : ''
          }`,
          style: { fontSize: '12px', padding: '6px 8px', borderRadius: '6px' },
        };
      },
    });
  }, [resultados, lugares, categorias, seleccionado, onSeleccionar]);

  return <div ref={cont} className="h-[380px] w-full rounded-lg border border-stone-200 bg-stone-100" />;
}
