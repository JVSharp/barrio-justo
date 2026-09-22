import { useCallback, useEffect, useMemo, useState } from 'react';
import { api, clp, num, uf } from '../api';
import { CERCANIA, PISOS, rankear } from '../puntaje';
import Segmentado from './Segmentado';
import MapaBuscador from './MapaBuscador';
import Icono from './Icono';

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
const ICONO_CRITERIO = {
  precio: 'tag-price',
  sol: 'sun',
  biotren: 'tram',
  universidad: 'square-academic-cap',
  colegio: 'backpack',
  salud: 'hospital',
  supermercado: 'cart-large-2',
  parque: 'leaf',
};
const CAMPO = 'mt-1 block w-full rounded-lg border border-arena-400 bg-arena-50 px-3 py-2 text-sm focus:border-sol-600 focus:outline-none focus:ring-1 focus:ring-sol-600';

function Titulo({ n, children }) {
  return (
    <h2 className="flex items-baseline gap-2 text-base font-semibold text-stone-900">
      <span className="marca-num">{n}</span>
      {children}
    </h2>
  );
}

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
    <div className="grid gap-8 lg:grid-cols-[340px_1fr]">
      {/* ---------------- Perfil ---------------- */}
      <aside className="space-y-5 lg:sticky lg:top-4 lg:self-start">
        <section className="space-y-3 rounded-2xl border border-arena-300 bg-arena-50 p-5 shadow-suave">
          <Titulo n="01">Qué buscas</Titulo>
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
              className={`num ${CAMPO}`}
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
                      on ? 'border-stone-900 bg-stone-900 text-arena-50' : 'border-arena-400 bg-arena-50 text-stone-600 hover:bg-arena-200'
                    }`}
                  >
                    {c}
                  </button>
                );
              })}
            </div>
          </div>
        </section>

        <section className="space-y-3 rounded-2xl border border-arena-300 bg-arena-50 p-5 shadow-suave">
          <Titulo n="02">Qué te importa</Titulo>
          <Criterio icono="tag-price" etiqueta="Precio bajo el mercado" valor={pesos.precio} onChange={(v) => setPesos((p) => ({ ...p, precio: v }))} />
          <Criterio icono="sun" etiqueta="Sol en invierno" valor={pesos.sol} onChange={(v) => setPesos((p) => ({ ...p, sol: v }))}>
            {pesos.sol > 0 && (
              <div className="mt-2 flex items-center gap-2 text-xs text-stone-500">
                Mirando desde
                <select
                  value={piso}
                  onChange={(e) => setPiso(e.target.value)}
                  className="rounded-md border border-arena-400 bg-arena-50 px-1.5 py-0.5 text-xs text-stone-700"
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
          <p className="border-t border-arena-300 pt-3 text-xs font-medium uppercase tracking-wide text-stone-400">Cerca de</p>
          {CERCANIA.map((c) => (
            <Criterio
              key={c.clave}
              icono={ICONO_CRITERIO[c.clave]}
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
          <p className="flex gap-2 rounded-xl border border-sol-200 bg-sol-50 px-4 py-3 text-sm text-sol-900">
            <Icono nombre="info-circle" className="mt-0.5 h-[18px] w-[18px] shrink-0 text-sol-600" />
            <span>
            Todavía no hay datos de cercanía ni de sol para estos avisos: el ranking usa solo el precio. Se calculan con{' '}
            <code className="rounded bg-sol-100 px-1">scripts/descargar_osm.py</code> y{' '}
            <code className="rounded bg-sol-100 px-1">scripts/enriquecer_geo.py</code>.
            </span>
          </p>
        )}

        {solDemo && (
          <p className="flex gap-1.5 text-xs text-stone-500">
            <Icono nombre="info-circle" className="h-4 w-4 shrink-0 text-stone-400" />
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
          <div className="rounded-2xl border border-dashed border-arena-400 px-6 py-12 text-center text-sm text-stone-600">
            <Icono nombre="home-smile" className="mx-auto mb-2 h-8 w-8 text-arena-400" />
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
            className="w-full rounded-xl border border-arena-400 bg-arena-50 py-2 text-sm text-stone-700 shadow-suave hover:bg-arena-200"
          >
            Ver {Math.min(POR_PAGINA, ranking.length - mostrar)} más
          </button>
        )}
      </section>
    </div>
  );
}

function Criterio({ etiqueta, icono, valor, onChange, children }) {
  return (
    <div>
      <div className="flex items-center justify-between gap-3">
        <span className="flex min-w-0 items-center gap-2 text-sm text-stone-700">
          {icono && <Icono nombre={icono} className={`h-[18px] w-[18px] shrink-0 ${valor > 0 ? 'text-sol-600' : 'text-stone-400'}`} />}
          {etiqueta}
        </span>
        <div role="radiogroup" aria-label={etiqueta} className="inline-flex shrink-0 rounded-lg border border-arena-400 bg-arena-100 p-0.5 text-xs">
          {IMPORTANCIA.map((o) => (
            <button
              key={o.valor}
              role="radio"
              aria-checked={valor === o.valor}
              onClick={() => onChange(o.valor)}
              className={`rounded-md px-2 py-0.5 ${valor === o.valor ? (o.valor === 0 ? 'bg-arena-50 text-stone-700 shadow-suave' : 'bg-sol-600 text-white shadow-suave') : 'text-stone-500 hover:text-stone-800'}`}
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
    if (p == null) return { icono: 'tag-price', texto: 'Sin referencia de precio en su comuna' };
    return { icono: 'tag-price', texto: p === 0 ? `Igual a la mediana de ${a.comuna}` : `${p > 0 ? '+' : '−'}${Math.abs(p)} % vs. la mediana de ${a.comuna}` };
  }
  if (clave === 'sol') {
    const h = a[`sol_${piso}`];
    if (h == null) return { icono: 'sun', texto: 'Sin dato de sol' };
    const cal = a.sol_calidad;
    const nota =
      a.sol_fuente === 'demo'
        ? 'edificios de demostración'
        : cal == null
          ? 'sin edificios mapeados cerca'
          : `${Math.round(cal * 100)} % de alturas conocidas`;
    return { icono: 'sun', texto: `${num(h, 1)} h de sol el 21 de junio (${ETIQUETA_PISO[piso]}) · ${nota}` };
  }
  const d = a[`dist_${clave}`];
  const etiqueta = CERCANIA.find((c) => c.clave === clave)?.etiqueta.toLowerCase();
  if (d == null) return { icono: ICONO_CRITERIO[clave], texto: `Sin ${etiqueta} a menos de 5 km` };
  const nombre = a[`cerca_${clave}`];
  return { icono: ICONO_CRITERIO[clave], texto: `A ${num(d)} m de ${nombre || etiqueta}` };
}

function Resultado({ r, lugar, piso, activo, onClick }) {
  const a = r.aviso;
  const arriendo = a.tipo_operacion === 'arriendo';
  const pct = r.total != null ? Math.round(r.total * 100) : null;
  return (
    <li
      id={`r-${a.url}`}
      onClick={onClick}
      className={`cursor-pointer rounded-2xl border bg-arena-50 p-4 shadow-suave transition-colors ${activo ? 'border-sol-400 ring-1 ring-sol-300' : 'border-arena-300 hover:border-arena-400'}`}
    >
      <div className="flex gap-4">
        <div className="w-16 shrink-0 rounded-xl bg-arena-100 px-1 py-2 text-center ring-1 ring-inset ring-arena-300">
          <p className="marca-num">#{String(lugar).padStart(2, '0')}</p>
          {pct != null && <p className="num text-2xl font-semibold leading-tight text-sol-700">{pct}</p>}
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
                const { icono, texto } = explicar(p.clave, a, piso);
                return (
                  <li key={p.clave} className="flex items-center gap-2 text-xs text-stone-600">
                    <Icono nombre={icono} className="h-4 w-4 shrink-0 text-sol-600/80" />
                    <span className="min-w-0 flex-1 truncate">{texto}</span>
                    <span className="h-1.5 w-16 shrink-0 overflow-hidden rounded-full bg-arena-200" aria-hidden>
                      <span
                        className={`block h-full ${p.valor == null ? 'bg-arena-400' : 'bg-sol-500'}`}
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
