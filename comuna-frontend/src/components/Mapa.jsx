import { useEffect, useMemo, useRef, useState } from 'react';
import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import { MapboxOverlay } from '@deck.gl/mapbox';
import { AmbientLight, LightingEffect, _SunLight as SunLight } from '@deck.gl/core';
import { ColumnLayer, SolidPolygonLayer } from '@deck.gl/layers';
import { MVTLayer } from '@deck.gl/geo-layers';
import { api, INMUEBLES, num, OPERACIONES } from '../api';
import Segmentado from './Segmentado';

// Mapa base y edificios: OpenFreeMap (gratis, sin llave, datos de OpenStreetMap).
const ESTILO = 'https://tiles.openfreemap.org/styles/positron';
const TILES_OSM = 'https://tiles.openfreemap.org/planet';
const VISTA_INICIAL = { center: [-73.06, -36.84], zoom: 11.3, pitch: 52, bearing: -18 };
const ZOOM_EDIFICIOS = 13.5;

// Escala secuencial de un solo tono (ámbar del sistema): claro = barato, oscuro = caro.
const PALETA = [
  [252, 229, 196],
  [247, 196, 138],
  [238, 145, 59],
  [196, 95, 20],
  [127, 60, 20],
];

function cuantiles(valores, k) {
  const s = [...valores].sort((a, b) => a - b);
  return Array.from({ length: k - 1 }, (_, i) => s[Math.floor(((i + 1) * s.length) / k)]);
}

// Chile continental: UTC-3 entre septiembre y abril (horario de verano), UTC-4 el resto.
// Aproximación suficiente para posicionar el sol; no pretende exactitud al minuto.
function instanteChile(fecha, hora) {
  const mes = Number(fecha.slice(5, 7));
  const offset = mes >= 9 || mes <= 3 ? '-03:00' : '-04:00';
  const hh = String(Math.floor(hora)).padStart(2, '0');
  const mm = String(Math.round((hora % 1) * 60)).padStart(2, '0');
  return new Date(`${fecha}T${hh}:${mm}:00${offset}`).getTime();
}

const hoyISO = () => new Date().toISOString().slice(0, 10);

export default function Mapa() {
  const contenedor = useRef(null);
  const mapa = useRef(null);
  const overlay = useRef(null);
  const [operacion, setOperacion] = useState('venta');
  const [inmueble, setInmueble] = useState('departamento');
  const [datos, setDatos] = useState(null);
  const [error, setError] = useState(null);
  const [sombras, setSombras] = useState(false);
  const [fecha, setFecha] = useState(hoyISO);
  const [hora, setHora] = useState(16);
  const [zoom, setZoom] = useState(VISTA_INICIAL.zoom);
  // El instante que se aplica al sol va con un respiro: arrastrar el control
  // de hora no debe recrear los edificios en cada paso.
  const [instante, setInstante] = useState(() => instanteChile(hoyISO(), 16));
  const [falloSombras, setFalloSombras] = useState(false);

  // Mapa: se crea una sola vez.
  useEffect(() => {
    const m = new maplibregl.Map({ container: contenedor.current, style: ESTILO, ...VISTA_INICIAL, maxPitch: 70 });
    m.addControl(new maplibregl.NavigationControl({ visualizePitch: true }), 'top-right');
    m.on('zoomend', () => setZoom(m.getZoom()));
    // Si la luz experimental falla en este navegador, se apaga y queda el mapa de precios.
    const o = new MapboxOverlay({ interleaved: false, layers: [], onError: () => setFalloSombras(true) });
    m.addControl(o);
    mapa.current = m;
    overlay.current = o;
    if (import.meta.env.DEV) window.__mapa = m; // para depurar desde la consola
    return () => m.remove();
  }, []);

  useEffect(() => {
    api('/mapa', { tipo_operacion: operacion, tipo_inmueble: inmueble })
      .then((d) => {
        setDatos(d);
        setError(null);
      })
      .catch((e) => setError(e.message));
  }, [operacion, inmueble]);

  useEffect(() => {
    const t = setTimeout(() => setInstante(instanteChile(fecha, hora)), 200);
    return () => clearTimeout(t);
  }, [fecha, hora]);

  const celdas = useMemo(() => datos?.celdas ?? [], [datos]);
  const cortes = useMemo(
    () => (celdas.length >= PALETA.length ? cuantiles(celdas.map((c) => c.mediana_uf_m2), PALETA.length) : []),
    [celdas],
  );
  const decM2 = operacion === 'arriendo' ? 2 : 1;

  // Capas y luz: se recalculan cuando cambia cualquier control.
  useEffect(() => {
    if (!overlay.current) return;
    const maxN = Math.max(1, ...celdas.map((c) => c.n));
    const color = (v) => PALETA[cortes.filter((c) => v >= c).length] ?? PALETA[0];

    // Con la luz experimental de deck.gl, cambiar la hora sobre capas ya
    // compiladas deja el mapa de sombras desactualizado y oscurece todo el suelo
    // (visto en Chrome). Por eso las capas con sombra llevan el instante en el
    // id: al cambiar la hora se recrean junto con la luz.
    const clave = sombras ? `-${instante}` : '';

    const columnas = new ColumnLayer({
      id: `celdas${clave}`,
      data: celdas,
      diskResolution: 6, // hexágonos
      radius: 210,
      // Con sombras, los precios se aplanan: pasan a ser un "piso" de color bajo
      // los edificios. Columnas de 1 km taparían justamente lo que se quiere ver.
      extruded: !sombras,
      pickable: true,
      getPosition: (c) => [c.lon, c.lat],
      getElevation: (c) => c.n,
      elevationScale: 1400 / maxN,
      getFillColor: (c) => [...color(c.mediana_uf_m2), sombras ? 85 : 235],
      material: { ambient: 0.55, diffuse: 0.6, shininess: 12 },
      updateTriggers: { getFillColor: [cortes, sombras], getElevation: [maxN, sombras] },
    });

    const capas = [columnas];
    let efectos = [];
    if (sombras && !falloSombras) {
      const sol = new SunLight({ timestamp: instante, color: [255, 250, 240], intensity: 1.6, _shadow: true });
      efectos = [
        new LightingEffect({ ambient: new AmbientLight({ color: [255, 255, 255], intensity: 1.3 }), sol }),
      ];
      // Suelo transparente: no tapa el mapa base, pero recibe la sombra.
      const suelo = new SolidPolygonLayer({
        id: `suelo${clave}`,
        data: [[[-73.6, -37.6], [-72.5, -37.6], [-72.5, -36.4], [-73.6, -36.4]]],
        getPolygon: (p) => p,
        getFillColor: [0, 0, 0, 0],
      });
      const edificios = new MVTLayer({
        id: `edificios${clave}`,
        data: TILES_OSM,
        minZoom: 13,
        maxZoom: 14,
        loadOptions: { mvt: { layers: ['building'] } },
        extruded: true,
        getElevation: (f) => f.properties.render_height || 6,
        getFillColor: [236, 233, 228, 255],
        // Ambiente alto: las fachadas a la sombra se ven grises, no negras.
        material: { ambient: 0.7, diffuse: 0.55, shininess: 4 },
        visible: zoom >= ZOOM_EDIFICIOS,
        onTileError: () => {},
      });
      capas.unshift(suelo, edificios);
    }
    const o = overlay.current;
    o.setProps({
      layers: capas,
      effects: efectos,
      getTooltip: ({ object: c }) =>
        c && {
          html: `<strong>${c.comuna}</strong><br>Mediana: ${num(c.mediana_uf_m2, decM2)} UF/m²<br>Rango típico: ${num(
            c.p25_uf_m2,
            decM2,
          )} – ${num(c.p75_uf_m2, decM2)}<br>${c.n} avisos en la celda`,
          style: { fontSize: '12px', padding: '6px 8px', borderRadius: '6px' },
        },
    });
  }, [celdas, cortes, sombras, instante, zoom, decM2, falloSombras]);

  const activarSombras = (on) => {
    setSombras(on);
    const m = mapa.current;
    if (on && m && m.getZoom() < ZOOM_EDIFICIOS) {
      m.flyTo({ center: [-73.049, -36.826], zoom: 15, pitch: 60, bearing: -25, duration: 1800 });
    }
  };

  const horaTxt = `${String(Math.floor(hora)).padStart(2, '0')}:${String(Math.round((hora % 1) * 60)).padStart(2, '0')}`;

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-3">
        <Segmentado opciones={OPERACIONES} valor={operacion} onChange={setOperacion} etiqueta="Operación" />
        <Segmentado opciones={INMUEBLES} valor={inmueble} onChange={setInmueble} etiqueta="Tipo de inmueble" />
        <label className="ml-auto inline-flex cursor-pointer items-center gap-2 text-sm text-stone-700">
          <input
            type="checkbox"
            checked={sombras}
            onChange={(e) => activarSombras(e.target.checked)}
            className="h-4 w-4 rounded border-stone-300 text-sol-600 focus:ring-sol-600"
          />
          Sombras <span className="text-xs text-stone-400">(experimental)</span>
        </label>
      </div>

      {sombras && (
        <div className="flex flex-wrap items-center gap-4 rounded-2xl border border-arena-300 bg-arena-50 px-4 py-3 text-sm shadow-suave">
          <label className="flex items-center gap-2 text-stone-600">
            Fecha
            <input
              type="date"
              value={fecha}
              onChange={(e) => e.target.value && setFecha(e.target.value)}
              className="rounded-md border border-stone-300 px-2 py-1 text-sm"
            />
          </label>
          <label className="flex flex-1 items-center gap-3 text-stone-600">
            Hora
            <input
              type="range"
              min={7}
              max={20.5}
              step={0.25}
              value={hora}
              onChange={(e) => setHora(Number(e.target.value))}
              className="w-full max-w-sm accent-sol-600"
              aria-valuetext={horaTxt}
            />
            <span className="num w-12 font-medium text-stone-900">{horaTxt}</span>
          </label>
          <p className="w-full text-xs text-stone-500">
            {falloSombras
              ? 'Tu navegador no pudo calcular las sombras; el mapa de precios sigue disponible.'
              : zoom < ZOOM_EDIFICIOS
                ? 'Acércate para ver los edificios.'
                : 'Alturas de OpenStreetMap, incompletas en muchas zonas: la sombra es ilustrativa, no una medición de asoleamiento por aviso.'}
          </p>
        </div>
      )}

      {error && <p className="text-sm text-red-700">No se pudo cargar el mapa: {error}</p>}

      <div className="relative overflow-hidden rounded-2xl border border-arena-300 shadow-suave">
        <div ref={contenedor} className="h-[620px] w-full bg-stone-100" />

        {cortes.length > 0 && (
          <div className="pointer-events-none absolute bottom-3 left-3 rounded-lg bg-arena-50/95 px-3 py-2 text-xs shadow-suave ring-1 ring-arena-300">
            <p className="mb-1.5 font-medium text-stone-700">Mediana UF/m² por celda</p>
            <div className="flex">
              {PALETA.map((c, i) => (
                <span key={i} className="h-2.5 w-9" style={{ background: `rgb(${c.join(',')})` }} />
              ))}
            </div>
            <div className="num mt-1 flex justify-between text-stone-500">
              <span>{num(Math.min(...celdas.map((c) => c.mediana_uf_m2)), decM2)}</span>
              <span>{num(Math.max(...celdas.map((c) => c.mediana_uf_m2)), decM2)}</span>
            </div>
            <p className="mt-1.5 text-stone-500">
              {sombras ? 'Color en el suelo = mediana de la celda' : 'Altura = cantidad de avisos'}
            </p>
          </div>
        )}
      </div>

      {datos && (
        <p className="num text-xs text-stone-500">
          {num(celdas.length)} celdas de ~500 m con al menos {datos.minimo_por_celda} avisos ·{' '}
          {num(datos.avisos_con_coordenadas)} de {num(datos.avisos_validos)} avisos válidos tienen coordenadas
          {' · '}Mapa © OpenStreetMap, OpenFreeMap
        </p>
      )}
    </div>
  );
}
