const ORDENES = [
  { valor: 'reciente', etiqueta: 'Más recientes' },
  { valor: 'precio_asc', etiqueta: 'Precio: menor a mayor' },
  { valor: 'precio_desc', etiqueta: 'Precio: mayor a menor' },
  { valor: 'uf_m2_asc', etiqueta: 'UF/m²: menor a mayor' },
  { valor: 'vs_mediana_asc', etiqueta: 'Más bajo vs. su comuna' },
];

export default function Filtros({ filtros, onChange, comunas, vacio }) {
  const set = (campo) => (e) => onChange({ ...filtros, [campo]: e.target.value });
  const activos = filtros.comuna || filtros.tipo_operacion || filtros.tipo_inmueble || filtros.posicion;

  return (
    <div className="flex flex-wrap items-end gap-3">
      <Campo etiqueta="Comuna">
        <select value={filtros.comuna} onChange={set('comuna')} className={SELECT}>
          <option value="">Todas</option>
          {comunas.map((c) => (
            <option key={c} value={c}>
              {c}
            </option>
          ))}
        </select>
      </Campo>
      <Campo etiqueta="Operación">
        <select value={filtros.tipo_operacion} onChange={set('tipo_operacion')} className={SELECT}>
          <option value="">Todas</option>
          <option value="venta">Venta</option>
          <option value="arriendo">Arriendo</option>
        </select>
      </Campo>
      <Campo etiqueta="Tipo">
        <select value={filtros.tipo_inmueble} onChange={set('tipo_inmueble')} className={SELECT}>
          <option value="">Todos</option>
          <option value="departamento">Departamento</option>
          <option value="casa">Casa</option>
        </select>
      </Campo>
      <Campo etiqueta="Precio vs. su comuna">
        <select value={filtros.posicion} onChange={set('posicion')} className={SELECT}>
          <option value="">Todos</option>
          <option value="bajo">Bajo el mercado</option>
          <option value="en_rango">En rango</option>
          <option value="sobre">Sobre el mercado</option>
          <option value="sin_referencia">Sin referencia</option>
        </select>
      </Campo>
      <Campo etiqueta="Ordenar por">
        <select value={filtros.orden} onChange={set('orden')} className={SELECT}>
          {ORDENES.map((o) => (
            <option key={o.valor} value={o.valor}>
              {o.etiqueta}
            </option>
          ))}
        </select>
      </Campo>
      {activos && (
        <button onClick={() => onChange({ ...vacio, orden: filtros.orden })} className="pb-2 text-sm text-sol-700 underline">
          Limpiar
        </button>
      )}
    </div>
  );
}

const SELECT =
  'mt-1 block w-full min-w-40 rounded-lg border border-arena-400 bg-arena-50 px-3 py-2 text-sm focus:border-sol-600 focus:outline-none focus:ring-1 focus:ring-sol-600';

function Campo({ etiqueta, children }) {
  return (
    <label className="block text-xs font-medium text-stone-500">
      {etiqueta}
      {children}
    </label>
  );
}
