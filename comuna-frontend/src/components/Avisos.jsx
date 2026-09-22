import { useEffect, useState } from 'react';
import { api, num } from '../api';
import Filtros from './Filtros';
import TarjetaAviso from './TarjetaAviso';

const POR_PAGINA = 24;
const VACIO = { comuna: '', tipo_operacion: '', tipo_inmueble: '', posicion: '', orden: 'reciente' };

export default function Avisos() {
  const [filtros, setFiltros] = useState(VACIO);
  const [pagina, setPagina] = useState(0);
  const [resp, setResp] = useState(null);
  const [cargando, setCargando] = useState(true);
  const [comunas, setComunas] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    api('/comunas').then(setComunas).catch(() => {});
  }, []);

  useEffect(() => {
    const t = setTimeout(() => {
      setCargando(true);
      setError(null);
      api('/propiedades', { ...filtros, skip: pagina * POR_PAGINA, limit: POR_PAGINA })
        .then(setResp)
        .catch((e) => setError(e.message))
        .finally(() => setCargando(false));
    }, 150);
    return () => clearTimeout(t);
  }, [filtros, pagina]);

  const cambiarFiltros = (f) => {
    setFiltros(f);
    setPagina(0);
  };

  const total = resp?.total ?? 0;
  const paginas = Math.max(1, Math.ceil(total / POR_PAGINA));
  const ir = (p) => {
    setPagina(p);
    window.scrollTo({ top: 0 });
  };

  return (
    <div>
      <Filtros filtros={filtros} onChange={cambiarFiltros} comunas={comunas} vacio={VACIO} />

      <p className="num mb-4 mt-6 text-sm text-stone-500" aria-live="polite">
        {cargando ? 'Cargando…' : `${num(total)} avisos`}
        {!cargando && total > POR_PAGINA && ` · página ${pagina + 1} de ${paginas}`}
      </p>

      {error && <p className="text-sm text-red-700">No se pudieron cargar los avisos: {error}</p>}

      {!cargando && !error && total === 0 && (
        <div className="rounded-2xl border border-dashed border-arena-400 px-6 py-14 text-center">
          <p className="font-medium text-stone-700">No hay avisos con esos filtros.</p>
          <button onClick={() => cambiarFiltros(VACIO)} className="mt-2 text-sm text-sol-700 underline">
            Quitar filtros
          </button>
        </div>
      )}

      <div className={`grid gap-4 sm:grid-cols-2 lg:grid-cols-3 ${cargando ? 'opacity-50' : ''}`}>
        {resp?.items.map((a) => (
          <TarjetaAviso key={a.url || a.id_aviso} aviso={a} />
        ))}
      </div>

      {paginas > 1 && (
        <nav className="mt-8 flex items-center justify-center gap-3 text-sm" aria-label="Paginación">
          <button
            onClick={() => ir(pagina - 1)}
            disabled={pagina === 0}
            className="rounded-lg border border-arena-400 bg-arena-50 px-4 py-2 shadow-suave hover:bg-arena-200 disabled:opacity-40"
          >
            Anterior
          </button>
          <span className="num text-stone-500">
            {pagina + 1} / {paginas}
          </span>
          <button
            onClick={() => ir(pagina + 1)}
            disabled={pagina + 1 >= paginas}
            className="rounded-lg border border-arena-400 bg-arena-50 px-4 py-2 shadow-suave hover:bg-arena-200 disabled:opacity-40"
          >
            Siguiente
          </button>
        </nav>
      )}
    </div>
  );
}
