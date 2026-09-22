import { useEffect, useRef } from 'react';
import Icono from './Icono';

// Qué es real, qué es ficticio y qué haría falta para usarlo con datos actuales.
export default function SobreDatos({ demo, onCerrar }) {
  const ref = useRef(null);

  useEffect(() => {
    const d = ref.current;
    d?.showModal();
    const cerrar = () => onCerrar();
    d?.addEventListener('close', cerrar);
    return () => d?.removeEventListener('close', cerrar);
  }, [onCerrar]);

  return (
    <dialog
      ref={ref}
      aria-labelledby="sobre-datos-titulo"
      className="w-[min(680px,calc(100vw-2rem))] rounded-2xl border border-arena-300 bg-arena-50 p-0 text-stone-700 shadow-panel backdrop:bg-stone-900/30 backdrop:backdrop-blur-[2px]"
      onClick={(e) => e.target === ref.current && ref.current.close()}
    >
      <div className="max-h-[80vh] overflow-y-auto p-6 sm:p-7">
        <div className="mb-5 flex items-start justify-between gap-4">
          <div className="flex items-center gap-2.5">
            <span className="grid h-9 w-9 place-items-center rounded-xl bg-sol-100 text-sol-700">
              <Icono nombre="database" className="h-5 w-5" />
            </span>
            <h2 id="sobre-datos-titulo" className="text-lg font-semibold text-stone-900">
              Sobre los datos
            </h2>
          </div>
          <button onClick={() => ref.current.close()} className="rounded-lg p-1 text-stone-400 hover:bg-arena-200 hover:text-stone-700" aria-label="Cerrar">
            <Icono nombre="close-circle" className="h-6 w-6" />
          </button>
        </div>

        <div className="space-y-5 text-sm leading-relaxed">
          {demo && (
            <section>
              <h3 className="mb-1.5 font-medium text-stone-900">Esta demo</h3>
              <ul className="space-y-1.5">
                <Punto real>Cantidad de avisos por comuna: del scraping de 2025.</Punto>
                <Punto real>Estaciones, colegios, supermercados, parques y hospitales: OpenStreetMap.</Punto>
                <Punto>Precios, superficies y coordenadas de los avisos: ficticios.</Punto>
                <Punto>Horas de sol: método real, pero calculado sobre edificios ficticios (las coordenadas también lo son).</Punto>
              </ul>
            </section>
          )}

          <section className="rounded-xl border border-sol-200 bg-sol-50 p-4">
            <h3 className="mb-1.5 flex items-center gap-2 font-medium text-sol-900">
              <Icono nombre="shield-check" className="h-5 w-5 text-sol-600" />
              Para usarlo con datos actuales
            </h3>
            <p className="text-sol-900/90">
              Hace falta una <strong>integración autorizada con Mercado Libre</strong> (dueño de PortalInmobiliario): su API
              oficial, con una aplicación registrada en su portal de desarrolladores y dentro de sus términos de uso. El
              scraper que trae el repositorio es un ejercicio de aprendizaje: los portales no permiten la extracción
              automatizada, y no está pensado para publicar datos ni para uso comercial.
            </p>
          </section>

          <section>
            <h3 className="mb-1.5 font-medium text-stone-900">Cómo se calcula</h3>
            <ul className="space-y-1.5">
              <Punto icono="tag-price">
                Precio vs. mercado: mediana de UF/m² de avisos comparables de la misma comuna, sin los que tienen precios
                imposibles o mal clasificados.
              </Punto>
              <Punto icono="sun">
                Sol: horas de sol directo el 21 de junio, con la posición solar de la NOAA y los edificios en 150 m. No
                considera cerros, árboles ni hacia dónde miran las ventanas.
              </Punto>
              <Punto icono="map-point">Cercanía: distancia en línea recta al lugar más cercano de cada tipo.</Punto>
            </ul>
          </section>

          <p className="text-xs text-stone-500">
            Mapas, edificios y lugares © colaboradores de OpenStreetMap (ODbL). Íconos Solar por 480 Design (CC BY 4.0).
          </p>
        </div>
      </div>
    </dialog>
  );
}

function Punto({ children, real, icono }) {
  return (
    <li className="flex gap-2.5">
      {icono ? (
        <Icono nombre={icono} className="mt-0.5 h-[18px] w-[18px] shrink-0 text-sol-600" />
      ) : (
        <span
          className={`mt-1.5 h-2 w-2 shrink-0 rounded-full ${real ? 'bg-emerald-600' : 'bg-arena-400'}`}
          aria-label={real ? 'real' : 'ficticio'}
          role="img"
        />
      )}
      <span>{children}</span>
    </li>
  );
}
