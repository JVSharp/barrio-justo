import React from 'react';
import { Filter, X } from 'lucide-react';

const Filters = ({ filters, setFilters, comunas, tiposInmueble, tiposOperacion }) => {
    const handleChange = (e) => {
        const { name, value } = e.target;
        setFilters(prev => ({ ...prev, [name]: value }));
    };

    const hasActiveFilters = filters.comuna || filters.tipo_operacion || filters.tipo_inmueble;

    return (
        <div className="bg-white p-6 rounded-2xl shadow-lg border-2 border-gray-100 mb-8">
            <div className="flex items-center justify-between mb-5">
                <div className="flex items-center gap-2">
                    <div className="bg-gradient-to-br from-indigo-600 to-purple-600 p-2 rounded-lg">
                        <Filter className="w-5 h-5 text-white" />
                    </div>
                    <h2 className="text-xl font-bold text-gray-800">Filtrar Propiedades</h2>
                </div>
                {hasActiveFilters && (
                    <span className="text-xs bg-indigo-100 text-indigo-700 px-3 py-1 rounded-full font-semibold">
                        Filtros activos
                    </span>
                )}
            </div>

            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div>
                    <label className="block text-sm font-bold text-gray-700 mb-2">Comuna</label>
                    <select
                        name="comuna"
                        value={filters.comuna}
                        onChange={handleChange}
                        className="w-full rounded-xl border-2 border-gray-200 p-3 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-all bg-gray-50 hover:bg-white font-medium text-gray-700"
                    >
                        <option value="">Todas las comunas</option>
                        {comunas.map(c => (
                            <option key={c} value={c}>{c}</option>
                        ))}
                    </select>
                </div>

                <div>
                    <label className="block text-sm font-bold text-gray-700 mb-2">Operación</label>
                    <select
                        name="tipo_operacion"
                        value={filters.tipo_operacion}
                        onChange={handleChange}
                        className="w-full rounded-xl border-2 border-gray-200 p-3 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-all bg-gray-50 hover:bg-white font-medium text-gray-700"
                    >
                        <option value="">Todas</option>
                        {tiposOperacion.map(op => (
                            <option key={op} value={op}>{op.charAt(0).toUpperCase() + op.slice(1)}</option>
                        ))}
                    </select>
                </div>

                <div>
                    <label className="block text-sm font-bold text-gray-700 mb-2">Tipo Inmueble</label>
                    <select
                        name="tipo_inmueble"
                        value={filters.tipo_inmueble}
                        onChange={handleChange}
                        className="w-full rounded-xl border-2 border-gray-200 p-3 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-all bg-gray-50 hover:bg-white font-medium text-gray-700"
                    >
                        <option value="">Todos</option>
                        {tiposInmueble.map(tipo => (
                            <option key={tipo} value={tipo}>{tipo.charAt(0).toUpperCase() + tipo.slice(1)}</option>
                        ))}
                    </select>
                </div>

                <div className="flex items-end">
                    <button
                        onClick={() => setFilters({ comuna: '', tipo_operacion: '', tipo_inmueble: '' })}
                        disabled={!hasActiveFilters}
                        className="w-full px-4 py-3 border-2 border-gray-300 shadow-sm text-sm font-bold rounded-xl text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-40 disabled:cursor-not-allowed transition-all flex items-center justify-center gap-2"
                    >
                        <X className="w-4 h-4" />
                        Limpiar Filtros
                    </button>
                </div>
            </div>
        </div>
    );
};

export default Filters;
