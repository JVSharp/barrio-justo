import React from 'react';

const Filters = ({ filters, setFilters, comunas, tiposInmueble, tiposOperacion }) => {
    const handleChange = (e) => {
        const { name, value } = e.target;
        setFilters(prev => ({ ...prev, [name]: value }));
    };

    return (
        <div className="bg-white p-4 rounded-xl shadow-sm border border-gray-100 mb-6">
            <h2 className="text-lg font-semibold text-gray-800 mb-4">Filtrar Propiedades</h2>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Comuna</label>
                    <select
                        name="comuna"
                        value={filters.comuna}
                        onChange={handleChange}
                        className="w-full rounded-lg border-gray-300 border p-2 focus:ring-indigo-500 focus:border-indigo-500"
                    >
                        <option value="">Todas</option>
                        {comunas.map(c => (
                            <option key={c} value={c}>{c}</option>
                        ))}
                    </select>
                </div>

                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Operación</label>
                    <select
                        name="tipo_operacion"
                        value={filters.tipo_operacion}
                        onChange={handleChange}
                        className="w-full rounded-lg border-gray-300 border p-2 focus:ring-indigo-500 focus:border-indigo-500"
                    >
                        <option value="">Todas</option>
                        {tiposOperacion.map(op => (
                            <option key={op} value={op}>{op}</option>
                        ))}
                    </select>
                </div>

                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Tipo Inmueble</label>
                    <select
                        name="tipo_inmueble"
                        value={filters.tipo_inmueble}
                        onChange={handleChange}
                        className="w-full rounded-lg border-gray-300 border p-2 focus:ring-indigo-500 focus:border-indigo-500"
                    >
                        <option value="">Todos</option>
                        {tiposInmueble.map(tipo => (
                            <option key={tipo} value={tipo}>{tipo}</option>
                        ))}
                    </select>
                </div>

                <div className="flex items-end">
                    <button
                        onClick={() => setFilters({ comuna: '', tipo_operacion: '', tipo_inmueble: '' })}
                        className="w-full px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-lg text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                    >
                        Limpiar Filtros
                    </button>
                </div>
            </div>
        </div>
    );
};

export default Filters;
