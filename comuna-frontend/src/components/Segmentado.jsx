export default function Segmentado({ opciones, valor, onChange, etiqueta }) {
  return (
    <div role="radiogroup" aria-label={etiqueta} className="inline-flex rounded-md border border-stone-300 bg-white p-0.5 text-sm">
      {opciones.map((o) => {
        const activo = o.valor === valor;
        return (
          <button
            key={o.valor}
            role="radio"
            aria-checked={activo}
            onClick={() => onChange(o.valor)}
            className={`rounded px-3 py-1.5 transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-teal-700 ${
              activo ? 'bg-stone-900 text-white' : 'text-stone-600 hover:bg-stone-100'
            }`}
          >
            {o.etiqueta}
          </button>
        );
      })}
    </div>
  );
}
