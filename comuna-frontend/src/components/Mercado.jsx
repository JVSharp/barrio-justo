import { useEffect, useState } from 'react';
import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { api, INMUEBLES, num, OPERACIONES, uf } from '../api';
import Segmentado from './Segmentado';

const MUESTRA_MINIMA = 10; // bajo esto la mediana es poco confiable

export default function Mercado() {
  const [operacion, setOperacion] = useState('venta');
  const [inmueble, setInmueble] = useState('departamento');
  const [datos, setDatos] = useState(null);
  const [calidad, setCalidad] = useState(null);
  const [renta, setRenta] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    api('/resumen', { tipo_operacion: operacion, tipo_inmueble: inmueble })
      .then((d) => {
        setDatos(d);
        setError(null);
      })
      .catch((e) => setError(e.message));
  }, [operacion, inmueble]);

  useEffect(() => {
    api('/calidad').then(setCalidad).catch(() => {});
    api('/rentabilidad').then(setRenta).catch(() => {});
  }, []);

  const decimales = operacion === 'arriendo' ? 1 : 0;
  const decM2 = operacion === 'arriendo' ? 2 : 1;
  const filas = datos?.comunas ?? [];
  const grafico = filas
    .filter((f) => f.mediana_uf_m2 != null && f.con_superficie >= MUESTRA_MINIMA)
    .sort((a, b) => b.mediana_uf_m2 - a.mediana_uf_m2);
  const region = datos?.region;

  return (
    <div className="space-y-10">
      <div className="flex flex-wrap items-center gap-3">
        <Segmentado opciones={OPERACIONES} valor={operacion} onChange={setOperacion} etiqueta="Operación" />
        <Segmentado opciones={INMUEBLES} valor={inmueble} onChange={setInmueble} etiqueta="Tipo de inmueble" />
      </div>

      {error && <p className="text-sm text-red-700">No se pudo cargar el resumen: {error}</p>}

      {region?.cantidad > 0 && (
        <dl className="grid grid-cols-2 gap-x-8 gap-y-5 sm:grid-cols-4">
          <Dato titulo="Mediana en la región" valor={uf(region.mediana_uf, decimales)} />
          <Dato titulo="Mediana por m²" valor={uf(region.mediana_uf_m2, decM2)} />
          <Dato titulo="Avisos analizados" valor={num(region.cantidad)} />
          <Dato
            titulo="Fuera del análisis"
            valor={num(datos.excluidos)}
            nota="precios imposibles o mal clasificados"
          />
        </dl>
      )}

      {grafico.length > 0 && (
        <section>
          <h2 className="text-base font-semibold text-stone-900"><span className="marca-num mr-2">01</span>UF por m² según comuna</h2>
          <p className="mb-4 text-sm text-stone-500">
            Mediana de {inmueble === 'casa' ? 'casas' : 'departamentos'} en {operacion}. Solo comunas con al
            menos {MUESTRA_MINIMA} avisos con superficie.
          </p>
          <div style={{ height: Math.max(180, grafico.length * 34) }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={grafico} layout="vertical" margin={{ left: 8, right: 48 }}>
                <CartesianGrid horizontal={false} stroke="#E6DED1" />
                <XAxis type="number" tick={{ fontSize: 12, fill: '#78716c' }} axisLine={false} tickLine={false} />
                <YAxis
                  type="category"
                  dataKey="comuna"
                  width={150}
                  tick={{ fontSize: 13, fill: '#44403c' }}
                  axisLine={false}
                  tickLine={false}
                />
                <Tooltip
                  cursor={{ fill: '#F1EBE1' }}
                  formatter={(v) => [uf(v, decM2), 'Mediana por m²']}
                  labelStyle={{ fontWeight: 600 }}
                />
                <Bar
                  dataKey="mediana_uf_m2"
                  radius={[0, 3, 3, 0]}
                  isAnimationActive={false}
                  label={{ position: 'right', fontSize: 12, fill: '#57534e', formatter: (v) => num(v, decM2) }}
                >
                  {grafico.map((f, i) => (
                    <Cell key={f.comuna} fill={i === 0 ? '#C45F14' : '#F7C48A'} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </section>
      )}

      {filas.length > 0 && (
        <section>
          <h2 className="mb-3 text-base font-semibold text-stone-900"><span className="marca-num mr-2">02</span>Detalle por comuna</h2>
          <div className="overflow-x-auto rounded-2xl border border-arena-300 bg-arena-50 shadow-suave">
            <table className="num w-full text-sm">
              <thead className="border-b border-arena-300 text-left text-xs uppercase tracking-wide text-stone-500">
                <tr>
                  <th className="px-4 py-2.5 font-medium">Comuna</th>
                  <th className="px-4 py-2.5 text-right font-medium">Avisos</th>
                  <th className="px-4 py-2.5 text-right font-medium">Mediana</th>
                  <th className="px-4 py-2.5 text-right font-medium">Rango típico (p25–p75)</th>
                  <th className="px-4 py-2.5 text-right font-medium">UF/m²</th>
                  <th className="px-4 py-2.5 text-right font-medium">Excluidos</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-stone-100">
                {filas.map((f) => {
                  const chica = (f.cantidad ?? 0) < MUESTRA_MINIMA;
                  return (
                    <tr key={f.comuna} className={chica ? 'text-stone-400' : ''}>
                      <td className="px-4 py-2.5">
                        {f.comuna}
                        {chica && <span className="ml-2 text-xs">muestra chica</span>}
                      </td>
                      <td className="px-4 py-2.5 text-right">{num(f.cantidad)}</td>
                      <td className="px-4 py-2.5 text-right font-medium">{uf(f.mediana_uf, decimales)}</td>
                      <td className="px-4 py-2.5 text-right">
                        {f.cantidad ? `${num(f.p25_uf, decimales)} – ${num(f.p75_uf, decimales)}` : '—'}
                      </td>
                      <td className="px-4 py-2.5 text-right">{num(f.mediana_uf_m2, decM2)}</td>
                      <td className="px-4 py-2.5 text-right">{f.excluidos || ''}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </section>
      )}

      {renta?.filas?.length > 0 && (
        <section>
          <h2 className="text-base font-semibold text-stone-900"><span className="marca-num mr-2">03</span>Rentabilidad bruta estimada</h2>
          <p className="mb-3 max-w-3xl text-sm text-stone-500">
            Arriendo anual por m² dividido por el precio de venta por m², con las medianas de cada comuna. Es una
            estimación gruesa: no descuenta gastos comunes, contribuciones ni meses sin arrendatario, y compara
            avisos distintos. Solo aparecen comunas con al menos {renta.minimo_por_lado} avisos de cada lado.
          </p>
          <div className="overflow-x-auto rounded-2xl border border-arena-300 bg-arena-50 shadow-suave">
            <table className="num w-full text-sm">
              <thead className="border-b border-arena-300 text-left text-xs uppercase tracking-wide text-stone-500">
                <tr>
                  <th className="px-4 py-2.5 font-medium">Comuna</th>
                  <th className="px-4 py-2.5 font-medium">Tipo</th>
                  <th className="px-4 py-2.5 text-right font-medium">Venta UF/m²</th>
                  <th className="px-4 py-2.5 text-right font-medium">Arriendo UF/m² al mes</th>
                  <th className="px-4 py-2.5 text-right font-medium">Rentabilidad bruta</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-stone-100">
                {renta.filas.map((f) => (
                  <tr key={`${f.comuna}-${f.tipo_inmueble}`}>
                    <td className="px-4 py-2.5">{f.comuna}</td>
                    <td className="px-4 py-2.5 text-stone-500">{f.tipo_inmueble === 'casa' ? 'Casas' : 'Departamentos'}</td>
                    <td className="px-4 py-2.5 text-right">{num(f.venta_uf_m2, 1)}</td>
                    <td className="px-4 py-2.5 text-right">{num(f.arriendo_uf_m2_mes, 3)}</td>
                    <td className="px-4 py-2.5 text-right font-medium">{num(f.rentabilidad_bruta_pct, 1)} %</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}

      {calidad?.excluidos > 0 && (
        <section className="max-w-2xl">
          <h2 className="text-base font-semibold text-stone-900"><span className="marca-num mr-2">04</span>Qué quedó fuera y por qué</h2>
          <p className="mb-3 text-sm text-stone-500">
            De {num(calidad.total)} avisos, {num(calidad.excluidos)} no entran a las estadísticas. No se borran:
            siguen visibles en la pestaña Avisos, marcados.
          </p>
          <ul className="num space-y-1.5 text-sm">
            {calidad.por_motivo.map((m) => (
              <li key={m.motivo} className="flex justify-between gap-4 border-b border-dashed border-arena-300 pb-1.5">
                <span>{m.descripcion}</span>
                <span className="text-stone-500">{num(m.cantidad)}</span>
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}

function Dato({ titulo, valor, nota }) {
  return (
    <div>
      <dt className="text-sm text-stone-500">{titulo}</dt>
      <dd className="num mt-0.5 text-2xl font-semibold text-stone-900">{valor}</dd>
      {nota && <dd className="text-xs text-stone-400">{nota}</dd>}
    </div>
  );
}
