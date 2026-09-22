import { lazy, Suspense, useEffect, useState } from 'react';
import { api, ESTATICO } from './api';
import Mercado from './components/Mercado';
import Avisos from './components/Avisos';

// El mapa trae MapLibre y deck.gl (~1 MB): solo se descarga al abrir su pestaña.
const Mapa = lazy(() => import('./components/Mapa'));
const Buscador = lazy(() => import('./components/Buscador'));

const VISTAS = [
  { id: 'buscador', etiqueta: 'Buscador' },
  { id: 'mercado', etiqueta: 'Mercado por comuna' },
  { id: 'mapa', etiqueta: 'Mapa 3D' },
  { id: 'avisos', etiqueta: 'Avisos' },
];

function vistaInicial() {
  const h = window.location.hash.replace('#', '');
  return VISTAS.some((v) => v.id === h) ? h : 'buscador';
}

export default function App() {
  const [vista, setVista] = useState(vistaInicial);
  const [salud, setSalud] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    api('/salud').then(setSalud).catch((e) => setError(e.message));
  }, []);

  const cambiar = (id) => {
    setVista(id);
    window.history.replaceState(null, '', `#${id}`);
  };

  return (
    <div className="min-h-screen">
      <header className="border-b border-stone-200 bg-white">
        <div className="mx-auto flex max-w-6xl flex-wrap items-end justify-between gap-4 px-5 pt-6">
          <div className="pb-4">
            <h1 className="text-xl font-semibold tracking-tight text-stone-900">Barrio Justo</h1>
            <p className="text-sm text-stone-500">Dónde vivir en el Biobío: a precio justo, cerca de lo que importa y con sol</p>
          </div>
          <nav className="flex gap-6 text-sm" aria-label="Vistas">
            {VISTAS.map((v) => (
              <button
                key={v.id}
                onClick={() => cambiar(v.id)}
                aria-current={vista === v.id ? 'page' : undefined}
                className={`-mb-px border-b-2 pb-3 transition-colors ${
                  vista === v.id
                    ? 'border-teal-700 font-medium text-stone-900'
                    : 'border-transparent text-stone-500 hover:text-stone-800'
                }`}
              >
                {v.etiqueta}
              </button>
            ))}
          </nav>
        </div>
      </header>

      {salud?.fuente === 'demo' && (
        <div className="border-b border-amber-200 bg-amber-50">
          <p className="mx-auto max-w-6xl px-5 py-2 text-sm text-amber-900">
            Estás viendo <strong>datos de demostración</strong>: la cantidad de avisos por comuna es
            real (snapshot de 2025), pero precios y superficies son ficticios.
          </p>
        </div>
      )}

      <main className="mx-auto max-w-6xl px-5 py-8">
        {error ? (
          <div className="rounded-lg border border-red-200 bg-red-50 p-5 text-sm text-red-900">
            <p className="font-medium">
              {ESTATICO ? `No se pudieron cargar los datos de la demo (${error}).` : `No se pudo conectar con la API (${error}).`}
            </p>
            <p className={ESTATICO ? 'hidden' : 'mt-1'}>
              Levántala con <code className="rounded bg-red-100 px-1">uvicorn main:app</code> desde{' '}
              <code className="rounded bg-red-100 px-1">backend/</code> y recarga.
            </p>
          </div>
        ) : vista === 'buscador' ? (
          <Suspense fallback={<p className="text-sm text-stone-500">Cargando el buscador…</p>}>
            <Buscador />
          </Suspense>
        ) : vista === 'mercado' ? (
          <Mercado />
        ) : vista === 'mapa' ? (
          <Suspense fallback={<p className="text-sm text-stone-500">Cargando el mapa…</p>}>
            <Mapa />
          </Suspense>
        ) : (
          <Avisos />
        )}
      </main>

      <footer className="mx-auto max-w-6xl px-5 pb-10 text-xs text-stone-400">
        {salud && `${salud.avisos.toLocaleString('es-CL')} avisos · fuente: ${salud.fuente}`}
        {ESTATICO && ' · versión estática, sin backend · '}
        {ESTATICO && (
          <a href="https://github.com/JVSharp/barrio-justo" className="underline hover:text-stone-600">
            código en GitHub
          </a>
        )}
      </footer>
    </div>
  );
}
