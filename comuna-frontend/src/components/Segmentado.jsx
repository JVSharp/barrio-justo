export default function Segmentado({ opciones, valor, onChange, etiqueta }) {
  return (
    <div role="radiogroup" aria-label={etiqueta} className="inline-flex rounded-lg border border-arena-400 bg-arena-100 p-0.5 text-sm">
      {opciones.map((o) => {
        const activo = o.valor === valor;
        return (
          <button
            key={o.valor}
            role="radio"
            aria-checked={activo}
            onClick={() => onChange(o.valor)}
            className={`rounded-md px-3 py-1.5 transition-colors ${
              activo ? 'bg-stone-900 text-arena-50 shadow-suave' : 'text-stone-600 hover:text-stone-900'
            }`}
          >
            {o.etiqueta}
          </button>
        );
      })}
    </div>
  );
}
