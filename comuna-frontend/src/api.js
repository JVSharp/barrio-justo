const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

export async function api(ruta, params = {}) {
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
