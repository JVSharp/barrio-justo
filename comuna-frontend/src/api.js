const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

// Modo estático (demo en GitHub Pages): no hay backend. Se carga una vez el
// JSON que exporta scripts/exportar_estatico.py con las mismas funciones de
// la API, y el filtrado/orden/paginación de avisos se hace aquí.
export const ESTATICO = import.meta.env.VITE_MODO === 'estatico';

let datosEstaticos;
function cargarEstatico() {
  datosEstaticos ??= fetch(`${import.meta.env.BASE_URL}demo/datos.json`).then((r) => {
    if (!r.ok) throw new Error(`${r.status} al cargar la demo`);
    return r.json();
  });
  return datosEstaticos;
}

const INF = Number.POSITIVE_INFINITY;
const ORDENES = {
  reciente: (a, b) => (b.fecha_ultima_vista || '').localeCompare(a.fecha_ultima_vista || ''),
  precio_asc: (a, b) => (a.precio_uf || INF) - (b.precio_uf || INF),
  precio_desc: (a, b) => (b.precio_uf || 0) - (a.precio_uf || 0),
  uf_m2_asc: (a, b) => (a.uf_m2 ?? INF) - (b.uf_m2 ?? INF),
  vs_mediana_asc: (a, b) => (a.posicion?.vs_mediana_pct ?? INF) - (b.posicion?.vs_mediana_pct ?? INF),
};

export function responderEstatico(d, ruta, p) {
  switch (ruta) {
    case '/salud':
      return d.salud;
    case '/comunas':
    case '/tipos_inmueble':
    case '/tipos_operacion':
    case '/calidad':
    case '/rentabilidad':
      return d[ruta.slice(1)];
    case '/resumen':
      return d.resumen[`${p.tipo_operacion || 'venta'}|${p.tipo_inmueble || 'departamento'}`];
    case '/propiedades': {
      let items = d.avisos.filter(
        (a) =>
          (!p.comuna || a.comuna === p.comuna) &&
          (!p.tipo_operacion || a.tipo_operacion === p.tipo_operacion) &&
          (!p.tipo_inmueble || a.tipo_inmueble === p.tipo_inmueble) &&
          (!p.posicion || a.posicion?.codigo === p.posicion),
      );
      items = [...items].sort(ORDENES[p.orden] || ORDENES.reciente); // sort es estable, como sorted()
      const skip = Number(p.skip) || 0;
      const limit = Number(p.limit) || 24;
      return { total: items.length, skip, limit, items: items.slice(skip, skip + limit) };
    }
    default:
      throw new Error(`${ruta} no está disponible en la demo estática`);
  }
}

export async function api(ruta, params = {}) {
  if (ESTATICO) return responderEstatico(await cargarEstatico(), ruta, params);
  const url = new URL(ruta, API_URL);
  Object.entries(params).forEach(([k, v]) => {
    if (v !== '' && v !== null && v !== undefined) url.searchParams.set(k, v);
  });
  const r = await fetch(url);
  if (!r.ok) throw new Error(`${r.status} en ${ruta}`);
  return r.json();
}

const nf = (d) => new Intl.NumberFormat('es-CL', { maximumFractionDigits: d });

export const uf = (v, d = 0) => (v == null ? '—' : `${nf(d).format(v)} UF`);
export const num = (v, d = 0) => (v == null ? '—' : nf(d).format(v));
export const clp = (v) =>
  v == null
    ? '—'
    : new Intl.NumberFormat('es-CL', { style: 'currency', currency: 'CLP', maximumFractionDigits: 0 }).format(v);

export const OPERACIONES = [
  { valor: 'venta', etiqueta: 'Venta' },
  { valor: 'arriendo', etiqueta: 'Arriendo' },
];
export const INMUEBLES = [
  { valor: 'departamento', etiqueta: 'Departamentos' },
  { valor: 'casa', etiqueta: 'Casas' },
];
