import { lazy, Suspense, useEffect, useState } from 'react';
import { api, ESTATICO } from './api';
import Mercado from './components/Mercado';
import Avisos from './components/Avisos';
import Icono from './components/Icono';
import SobreDatos from './components/SobreDatos';

// El mapa trae MapLibre y deck.gl (~2 MB): solo se descarga al abrir su pestaña.
const Mapa = lazy(() => import('./components/Mapa'));
const Buscador = lazy(() => import('./components/Buscador'));

const VISTAS = [
  { id: 'buscador', etiqueta: 'Buscador', icono: 'magnifer' },
  { id: 'mercado', etiqueta: 'Mercado', icono: 'chart-2' },
  { id: 'mapa', etiqueta: 'Mapa 3D', icono: 'map-point-wave' },
  { id: 'avisos', etiqueta: 'Avisos', icono: 'documents' },
];

function vistaInicial() {
  const h = window.location.hash.replace('#', '');
  return VISTAS.some((v) => v.id === h) ? h : 'buscador';
}

function Marca() {
  return (
    <svg viewBox="0 0 32 32" className="h-9 w-9 shrink-0" aria-hidden>
      <rect width="32" height="32" rx="9" fill="#2F2A25" />
      <circle cx="21.5" cy="10.5" r="4.5" fill="#EE913B" />
      <path d="M6 25V16.2l7-5.4 7 5.4V25h-4.6v-5.2h-4.8V25z" fill="#FDFBF7" />
    </svg>
  );
}

export default function App() {
  const [vista, setVista] = useState(vistaInicial);
  const [salud, setSalud] = useState(null);
  const [error, setError] = useState(null);
  const [sobreDatos, setSobreDatos] = useState(false);

  useEffect(() => {
    api('/salud').then(setSalud).catch((e) => setError(e.message));
  }, []);

  const cambiar = (id) => {
    setVista(id);
    window.history.replaceState(null, '', `#${id}`);
  };
  const demo = salud?.fuente === 'demo';

  return (
    <div className="min-h-screen px-3 py-3 sm:px-5 sm:py-5">
      {/* Marco principal: una sola superficie cálida que contiene toda la app. */}
      <div className="mx-auto max-w-7xl overflow-hidden rounded-3xl border border-arena-300 bg-arena-100 shadow-panel">
        <header className="border-b border-arena-300 bg-arena-50/80 backdrop-blur">
          <div className="flex flex-wrap items-center justify-between gap-x-6 gap-y-3 px-5 py-4 sm:px-8">
            <div className="flex items-center gap-3">
              <Marca />
              <div>
                <h1 className="text-lg font-semibold tracking-tight text-stone-900">Barrio Justo</h1>
                <p className="text-[13px] text-stone-500">Dónde vivir en el Biobío: a precio justo, cerca de lo que importa y con sol</p>
              </div>
            </div>
            <nav aria-label="Vistas" className="flex flex-wrap items-center gap-1 rounded-xl border border-arena-300 bg-arena-100 p-1">
              {VISTAS.map((v) => {
                const activa = vista === v.id;
                return (
                  <button
                    key={v.id}
                    onClick={() => cambiar(v.id)}
                    aria-current={activa ? 'page' : undefined}
                    className={`inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm transition-colors ${
                      activa ? 'bg-arena-50 font-medium text-stone-900 shadow-suave' : 'text-stone-500 hover:text-stone-800'
                    }`}
                  >
                    <Icono nombre={v.icono} className={`h-[18px] w-[18px] ${activa ? 'text-sol-600' : 'text-stone-400'}`} />
                    {v.etiqueta}
                  </button>
                );
              })}
            </nav>
          </div>

          {demo && (
            <div className="flex flex-wrap items-center gap-x-3 gap-y-1 border-t border-arena-300 bg-sol-50/70 px-5 py-2 text-[13px] text-sol-900 sm:px-8">
              <span className="inline-flex items-center gap-1.5 font-medium">
                <span className="h-1.5 w-1.5 rounded-full bg-sol-500" aria-hidden />
                Datos de demostración
              </span>
              <span className="text-sol-800/80">
                Los precios son ficticios. Para datos actuales hace falta una integración autorizada con Mercado Libre.
              </span>
              <button onClick={() => setSobreDatos(true)} className="font-medium text-sol-700 underline decoration-sol-300 underline-offset-2 hover:text-sol-900">
                Sobre los datos
              </button>
            </div>
          )}
        </header>

        <main className="px-5 py-7 sm:px-8">
          {error ? (
            <div className="rounded-xl border border-red-200 bg-red-50 p-5 text-sm text-red-900">
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

        <footer className="flex flex-wrap items-center justify-between gap-3 border-t border-arena-300 px-5 py-4 text-xs text-stone-500 sm:px-8">
          <p className="num">
            {salud && `${salud.avisos.toLocaleString('es-CL')} avisos · fuente: ${salud.fuente}`}
            {ESTATICO && ' · versión estática, sin backend'}
          </p>
          <p className="flex flex-wrap items-center gap-x-3 gap-y-1">
            <button onClick={() => setSobreDatos(true)} className="inline-flex items-center gap-1 hover:text-stone-800">
              <Icono nombre="database" className="h-4 w-4 text-stone-400" />
              Sobre los datos
            </button>
            <span>Mapas y lugares © OpenStreetMap</span>
            <span>Íconos Solar (CC BY 4.0)</span>
            <a href="https://github.com/JVSharp/barrio-justo" className="underline decoration-arena-400 underline-offset-2 hover:text-stone-800">
              Código en GitHub
            </a>
          </p>
        </footer>
      </div>

      {sobreDatos && <SobreDatos demo={demo} onCerrar={() => setSobreDatos(false)} />}
    </div>
  );
}
