import { clp, num, uf } from '../api';
import Icono from './Icono';

const esDemo = (url) => !url || url.includes('example.invalid');

// "2026-09-01" con new Date() se interpreta como medianoche UTC, y en Chile
// (UTC-3/-4) se muestra como el día anterior. Se formatea a mano.
function fecha(iso) {
  const [a, m, d] = String(iso).slice(0, 10).split('-');
  return a && m && d ? `${d}-${m}-${a}` : '';
}

const plural = (n, uno, varios) => `${n} ${Number(n) === 1 ? uno : varios}`;

// Bajo el mercado es la buena noticia para quien busca: color de acento.
// Sobre el mercado se marca, pero sin alarma (no es un error del aviso).
const ESTILO_POSICION = {
  bajo: 'bg-sol-50 text-sol-800 ring-sol-200',
  en_rango: 'bg-arena-200 text-stone-600 ring-arena-300',
  sobre: 'bg-stone-100 text-stone-700 ring-stone-300',
};

function Posicion({ posicion, comuna }) {
  if (!posicion || posicion.codigo === 'sin_referencia') return null;
  const pct = posicion.vs_mediana_pct;
  const detalle =
    pct === 0 ? `igual a la mediana de ${comuna}` : `${pct > 0 ? '+' : '−'}${Math.abs(pct)} % vs. la mediana de ${comuna}`;
  return (
    <p className="mt-3 flex flex-wrap items-center gap-x-2 gap-y-1 text-xs">
      <span className={`rounded px-1.5 py-0.5 font-medium ring-1 ring-inset ${ESTILO_POSICION[posicion.codigo]}`}>
        {posicion.etiqueta}
      </span>
      <span className="num text-stone-500">{detalle}</span>
    </p>
  );
}

function Historial({ dias, cambio }) {
  if (dias == null && cambio == null) return null;
  const partes = [];
  if (dias != null) partes.push(dias === 0 ? 'Publicado hoy' : `${plural(dias, 'día', 'días')} publicado`);
  return (
    <p className="num mt-1.5 flex items-center gap-1 text-xs text-stone-500">
      {partes.join(' · ')}
      {cambio != null && (
        <span className={`inline-flex items-center gap-0.5 ${cambio < 0 ? 'text-sol-700' : 'text-stone-600'}`}>
          {partes.length > 0 && <span className="mx-1 text-stone-300">·</span>}
          <Icono nombre={cambio < 0 ? 'graph-down' : 'graph-up'} className="h-3.5 w-3.5" />
          {cambio < 0 ? 'bajó' : 'subió'} {num(Math.abs(cambio), 1)} %
        </span>
      )}
    </p>
  );
}

export default function TarjetaAviso({ aviso }) {
  const {
    titulo, comuna, tipo_operacion, tipo_inmueble, precio_uf, precio_clp,
    superficie_m2, dormitorios, url, uf_m2, motivo_exclusion, fecha_ultima_vista,
    posicion, dias_publicado, cambio_precio_pct,
  } = aviso;
  const banos = aviso.banos ?? aviso['baños'];
  const arriendo = tipo_operacion === 'arriendo';
  const detalles = [
    superficie_m2 && { icono: 'ruler-angular', texto: String(superficie_m2) },
    dormitorios && { icono: 'bed', texto: `${dormitorios} dorm.` },
    banos && { icono: 'bath', texto: plural(banos, 'baño', 'baños') },
  ].filter(Boolean);

  return (
    <article
      className={`flex flex-col rounded-2xl border bg-arena-50 p-4 shadow-suave ${
        motivo_exclusion ? 'border-sol-300' : 'border-arena-300'
      }`}
    >
      <p className="text-xs text-stone-500">
        {comuna} · {tipo_inmueble} en {tipo_operacion}
      </p>
      <h3 className="mt-1 line-clamp-2 font-medium text-stone-900">{titulo || 'Sin título'}</h3>

      <p className="num mt-3 text-xl font-semibold text-stone-900">
        {uf(precio_uf, arriendo ? 1 : 0)}
        {arriendo && <span className="text-sm font-normal text-stone-500"> /mes</span>}
      </p>
      <p className="num text-sm text-stone-500">
        {clp(precio_clp)}
        {uf_m2 != null && ` · ${num(uf_m2, arriendo ? 2 : 1)} UF/m²`}
      </p>

      {detalles.length > 0 && (
        <ul className="mt-3 flex flex-wrap gap-x-3 gap-y-1 text-sm text-stone-600">
          {detalles.map((d) => (
            <li key={d.icono} className="inline-flex items-center gap-1">
              <Icono nombre={d.icono} className="h-4 w-4 text-stone-400" />
              {d.texto}
            </li>
          ))}
        </ul>
      )}

      <Posicion posicion={posicion} comuna={comuna} />
      <Historial dias={dias_publicado} cambio={cambio_precio_pct} />

      {motivo_exclusion && (
        <p className="mt-3 flex gap-1.5 text-xs text-sol-800">
          <Icono nombre="danger-triangle" className="h-4 w-4 shrink-0 text-sol-600" />
          Fuera del análisis: {motivo_exclusion.toLowerCase()}
        </p>
      )}

      <div className="mt-auto flex items-center justify-between pt-4 text-xs text-stone-400">
        <span>{fecha_ultima_vista && `Visto el ${fecha(fecha_ultima_vista)}`}</span>
        {esDemo(url) ? (
          <span>aviso de demo</span>
        ) : (
          <a href={url} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1 font-medium text-sol-700 hover:underline">
            Ver aviso <Icono nombre="arrow-right-up" className="h-3.5 w-3.5" />
          </a>
        )}
      </div>
    </article>
  );
}
