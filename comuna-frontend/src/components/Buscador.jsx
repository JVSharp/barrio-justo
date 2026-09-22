import { useCallback, useEffect, useMemo, useState } from 'react';
import { Sun, MapPin, Tag } from 'lucide-react';
import { api, clp, num, uf } from '../api';
import { CERCANIA, PISOS, rankear } from '../puntaje';
import Segmentado from './Segmentado';
import MapaBuscador from './MapaBuscador';

const IMPORTANCIA = [
  { valor: 0, etiqueta: 'No' },
  { valor: 1, etiqueta: 'Algo' },
  { valor: 2, etiqueta: 'Mucho' },
];
const DORMITORIOS = [0, 1, 2, 3, 4].map((n) => ({ valor: n, etiqueta: n === 0 ? 'Todos' : `${n}+` }));
const TIPOS = [
  { valor: '', etiqueta: 'Todos' },
  { valor: 'departamento', etiqueta: 'Depto' },
  { valor: 'casa', etiqueta: 'Casa' },
];
const OPERACIONES = [
  { valor: 'venta', etiqueta: 'Comprar' },
  { valor: 'arriendo', etiqueta: 'Arrendar' },
];
const POR_PAGINA = 20;

export default function Buscador() {
  const [perfil, setPerfil] = useState({ operacion: 'venta', tipo: '', presupuesto: '', dorm: 0, comunas: [] });
  const [pesos, setPesos] = useState({ precio: 1, sol: 1, cerca: { biotren: 1 } });
  const [piso, setPiso] = useState('p3');
  const [datos, setDatos] = useState(null);
  const [comunas, setComunas] = useState([]);
  const [lugares, setLugares] = useState(null);
  const [error, setError] = useState(null);
  const [mostrar, setMostrar] = useState(POR_PAGINA);
  const [seleccionado, setSeleccionado] = useState(null);

  useEffect(() => {
    api('/comunas').then(setComunas).catch(() => {});
    api('/lugares').then((d) => setLugares(d.lugares)).catch(() => {});
  }, []);

  useEffect(() => {
    const t = setTimeout(() => {
      api('/buscador', {
        tipo_operacion: perfil.operacion,
        tipo_inmueble: perfil.tipo,
        presupuesto_max_uf: perfil.presupuesto,
        dormitorios_min: perfil.dorm || '',
        comunas: perfil.comunas.join(','),
      })
        .then((d) => {
          setDatos(d);
          setError(null);
          setMostrar(POR_PAGINA);
        })
        .catch((e) => setError(e.message));
    }, 250);
    return () => clearTimeout(t);
  }, [perfil]);

  const ranking = useMemo(() => rankear(datos?.items ?? [], pesos, piso), [datos, pesos, piso]);
  const conGeo = useMemo(() => (datos?.items ?? []).some((a) => 'sol_calle' in a || 'dist_biotren' in a), [datos]);
  const solDemo = useMemo(() => (datos?.items ?? []).some((a) => a.sol_fuente === 'demo'), [datos]);
  const categoriasActivas = CERCANIA.filter((c) => pesos.cerca[c.clave]).map((c) => c.clave);
  const set = (campo) => (v) => setPerfil((p) => ({ ...p, [campo]: v }));
  const seleccionar = useCallback((url) => {
    setSeleccionado(url);
    document.getElementById(`r-${url}`)?.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }, []);

  const toggleComuna = (c) =>
    setPerfil((p) => ({ ...p, comunas: p.comunas.includes(c) ? p.comunas.filter((x) => x !== c) : [...p.comunas, c] }));

  return (
    <div className="grid gap-8 lg:grid-cols-[320px_1fr]">
      {/* ---------------- Perfil ---------------- */}
      <aside className="space-y-6 lg:sticky lg:top-4 lg:self-start">
        <section className="space-y-3">
          <h2 className="text-base font-semibold text-stone-900">Qué buscas</h2>
          <Segmentado opciones={OPERACIONES} valor={perfil.operacion} onChange={set('operacion')} etiqueta="Operación" />
          <Segmentado opciones={TIPOS} valor={perfil.tipo} onChange={set('tipo')} etiqueta="Tipo" />
          <label className="block text-sm text-stone-600">
            Presupuesto máximo {perfil.operacion === 'arriendo' ? '(UF al mes)' : '(UF)'}
            <input
              type="number"
              inputMode="decimal"
              min="0"
              placeholder={perfil.operacion === 'arriendo' ? 'ej. 18' : 'ej. 4500'}
              value={perfil.presupuesto}
              onChange={(e) => set('presupuesto')(e.target.value)}
              className="num mt-1 block w-full rounded-md border border-stone-300 bg-white px-3 py-2 text-sm focus:border-teal-700 focus:outline-none focus:ring-1 focus:ring-teal-700"
            />
          </label>
          <div className="text-sm text-stone-600">
            <p className="mb-1">Dormitorios</p>
            <Segmentado opciones={DORMITORIOS} valor={perfil.dorm} onChange={set('dorm')} etiqueta="Dormitorios mínimos" />
          </div>
          <div className="text-sm text-stone-600">
            <p className="mb-1.5">Comunas {perfil.comunas.length === 0 && <span className="text-stone-400">(todas)</span>}</p>
            <div className="flex flex-wrap gap-1.5">
              {comunas.map((c) => {
                const on = perfil.comunas.includes(c);
                return (
                  <button
                    key={c}
                    onClick={() => toggleComuna(c)}
                    aria-pressed={on}
                    className={`rounded-full border px-2.5 py-1 text-xs transition-colors ${
                      on ? 'border-stone-900 bg-stone-900 text-white' : 'border-stone-300 bg-white text-stone-600 hover:bg-stone-100'
                    }`}
                  >
                    {c}
                  </button>
                );
              })}
            </div>
          </div>
        </section>

        <section className="space-y-3">
          <h2 className="text-base font-semibold text-stone-900">Qué te importa</h2>
          <Criterio etiqueta="Precio bajo el mercado" valor={pesos.precio} onChange={(v) => setPesos((p) => ({ ...p, precio: v }))} />
          <Criterio etiqueta="Sol en invierno" valor={pesos.sol} onChange={(v) => setPesos((p) => ({ ...p, sol: v }))}>
            {pesos.sol > 0 && (
              <div className="mt-2 flex items-center gap-2 text-xs text-stone-500">
                Mirando desde
                <select
                  value={piso}
                  onChange={(e) => setPiso(e.target.value)}
                  className="rounded border border-stone-300 bg-white px-1.5 py-0.5 text-xs text-stone-700"
                >
                  {PISOS.map((p) => (
                    <option key={p.valor} value={p.valor}>
                      {p.etiqueta}
                    </option>
                  ))}
                </select>
              </div>
            )}
          </Criterio>
          <p className="pt-1 text-xs font-medium uppercase tracking-wide text-stone-400">Cerca de</p>
          {CERCANIA.map((c) => (
            <Criterio
              key={c.clave}
              etiqueta={c.etiqueta}
              valor={pesos.cerca[c.clave] || 0}
              onChange={(v) => setPesos((p) => ({ ...p, cerca: { ...p.cerca, [c.clave]: v } }))}
            />
          ))}
          <p className="text-xs leading-relaxed text-stone-400">
            Cerca = hasta 300 m en línea recta; desde 1,5 km ya no suma. Sol = horas de sol directo el 21 de junio,
            considerando los edificios en 150 m.
          </p>
        </section>
      </aside>

      {/* ---------------- Resultados ---------------- */}
      <section className="min-w-0 space-y-4">
        {error && <p className="text-sm text-red-700">No se pudo buscar: {error}</p>}
        {datos && !conGeo && (
          <p className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
            Todavía no hay datos de cercanía ni de sol para estos avisos: el ranking usa solo el precio. Se calculan con{' '}
            <code className="rounded bg-amber-100 px-1">scripts/descargar_osm.py</code> y{' '}
            <code className="rounded bg-amber-100 px-1">scripts/enriquecer_geo.py</code>.
          </p>
        )}

        {solDemo && (
          <p className="text-xs text-stone-500">
            Lugares cercanos: reales, de OpenStreetMap. Sol: calculado con el método real, pero sobre una ciudad de
            edificios ficticios, porque las coordenadas de la demo también lo son.
          </p>
        )}

        <MapaBuscador
          resultados={ranking}
          lugares={lugares}
          categorias={categoriasActivas}
          seleccionado={seleccionado}
          onSeleccionar={seleccionar}
        />

        <p className="num text-sm text-stone-500" aria-live="polite">
          {datos ? `${num(datos.total)} avisos cumplen lo que pediste` : 'Buscando…'}
          {datos?.total > 0 && ' · ordenados por calce con lo que te importa'}
        </p>

        {datos?.total === 0 && (
          <div className="rounded-lg border border-dashed border-stone-300 px-6 py-12 text-center text-sm text-stone-600">
            Nada con esos filtros. Prueba subir el presupuesto o sumar comunas.
          </div>
        )}

        <ol className="space-y-3">
          {ranking.slice(0, mostrar).map((r, i) => (
            <Resultado key={r.aviso.url} r={r} lugar={i + 1} piso={piso} activo={seleccionado === r.aviso.url} onClick={() => setSeleccionado(r.aviso.url)} />
          ))}
        </ol>
        {ranking.length > mostrar && (
          <button
            onClick={() => setMostrar((m) => m + POR_PAGINA)}
            className="w-full rounded-md border border-stone-300 bg-white py-2 text-sm hover:bg-stone-100"
          >
            Ver {Math.min(POR_PAGINA, ranking.length - mostrar)} más
          </button>
        )}
      </section>
    </div>
  );
}

function Criterio({ etiqueta, valor, onChange, children }) {
  return (
    <div>
      <div className="flex items-center justify-between gap-3">
        <span className="text-sm text-stone-700">{etiqueta}</span>
        <div role="radiogroup" aria-label={etiqueta} className="inline-flex rounded border border-stone-300 bg-white p-0.5 text-xs">
          {IMPORTANCIA.map((o) => (
            <button
              key={o.valor}
              role="radio"
              aria-checked={valor === o.valor}
              onClick={() => onChange(o.valor)}
              className={`rounded-sm px-2 py-0.5 ${valor === o.valor ? 'bg-teal-700 text-white' : 'text-stone-500 hover:bg-stone-100'}`}
            >
              {o.etiqueta}
            </button>
          ))}
        </div>
      </div>
      {children}
    </div>
  );
}

const ETIQUETA_PISO = Object.fromEntries(PISOS.map((p) => [p.valor, p.etiqueta.toLowerCase()]));

function explicar(clave, a, piso) {
  if (clave === 'precio') {
    const p = a.posicion?.vs_mediana_pct;
    if (p == null) return { icono: Tag, texto: 'Sin referencia de precio en su comuna' };
    return { icono: Tag, texto: p === 0 ? `Igual a la mediana de ${a.comuna}` : `${p > 0 ? '+' : '−'}${Math.abs(p)} % vs. la mediana de ${a.comuna}` };
  }
  if (clave === 'sol') {
    const h = a[`sol_${piso}`];
    if (h == null) return { icono: Sun, texto: 'Sin dato de sol' };
    const cal = a.sol_calidad;
    const nota =
      a.sol_fuente === 'demo'
        ? 'edificios de demostración'
        : cal == null
          ? 'sin edificios mapeados cerca'
          : `${Math.round(cal * 100)} % de alturas conocidas`;
    return { icono: Sun, texto: `${num(h, 1)} h de sol el 21 de junio (${ETIQUETA_PISO[piso]}) · ${nota}` };
  }
  const d = a[`dist_${clave}`];
  const etiqueta = CERCANIA.find((c) => c.clave === clave)?.etiqueta.toLowerCase();
  if (d == null) return { icono: MapPin, texto: `Sin ${etiqueta} a menos de 5 km` };
  const nombre = a[`cerca_${clave}`];
  return { icono: MapPin, texto: `A ${num(d)} m de ${nombre || etiqueta}` };
}

function Resultado({ r, lugar, piso, activo, onClick }) {
  const a = r.aviso;
  const arriendo = a.tipo_operacion === 'arriendo';
  const pct = r.total != null ? Math.round(r.total * 100) : null;
  return (
    <li
      id={`r-${a.url}`}
      onClick={onClick}
      className={`cursor-pointer rounded-lg border bg-white p-4 transition-colors ${activo ? 'border-amber-400 ring-1 ring-amber-300' : 'border-stone-200 hover:border-stone-300'}`}
    >
      <div className="flex gap-4">
        <div className="w-14 shrink-0 text-center">
          <p className="num text-xs text-stone-400">#{lugar}</p>
          {pct != null && <p className="num text-2xl font-semibold text-teal-800">{pct}</p>}
          {pct != null && <p className="text-[10px] uppercase tracking-wide text-stone-400">calce</p>}
        </div>
        <div className="min-w-0 flex-1">
          <p className="text-xs text-stone-500">
            {a.comuna} · {a.tipo_inmueble}
            {a.superficie_m2 && ` · ${a.superficie_m2}`}
            {a.dormitorios && ` · ${a.dormitorios} dorm.`}
          </p>
          <h3 className="truncate font-medium text-stone-900">{a.titulo}</h3>
          <p className="num mt-0.5 text-sm">
            <span className="font-semibold text-stone-900">{uf(a.precio_uf, arriendo ? 1 : 0)}</span>
            {arriendo && <span className="text-stone-500"> /mes</span>}
            <span className="text-stone-400"> · {clp(a.precio_clp)}</span>
          </p>
          {r.partes.length > 0 && (
            <ul className="mt-3 space-y-1.5">
              {r.partes.map((p) => {
                const { icono: Icono, texto } = explicar(p.clave, a, piso);
                return (
                  <li key={p.clave} className="flex items-center gap-2 text-xs text-stone-600">
                    <Icono className="h-3.5 w-3.5 shrink-0 text-stone-400" aria-hidden />
                    <span className="min-w-0 flex-1 truncate">{texto}</span>
                    <span className="h-1.5 w-16 shrink-0 overflow-hidden rounded-full bg-stone-100" aria-hidden>
                      <span
                        className={`block h-full ${p.valor == null ? 'bg-stone-300' : 'bg-teal-600'}`}
                        style={{ width: `${Math.round((p.valor ?? 0.5) * 100)}%` }}
                      />
                    </span>
                  </li>
                );
              })}
            </ul>
          )}
        </div>
      </div>
    </li>
  );
}
