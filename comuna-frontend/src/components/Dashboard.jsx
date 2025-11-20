import React, { useState, useEffect } from 'react';
import axios from 'axios';
import PropertyCard from './PropertyCard';
import Filters from './Filters';
import { Building2, Loader2, ChevronLeft, ChevronRight, TrendingUp } from 'lucide-react';

const API_URL = 'http://127.0.0.1:8000';

const Dashboard = () => {
    const [properties, setProperties] = useState([]);
    const [loading, setLoading] = useState(true);
    const [page, setPage] = useState(1);
    const [filters, setFilters] = useState({
        comuna: '',
        tipo_operacion: '',
        tipo_inmueble: ''
    });
    const [metadata, setMetadata] = useState({
        comunas: [],
        tiposInmueble: [],
        tiposOperacion: []
    });

    const ITEMS_PER_PAGE = 12;

    useEffect(() => {
        const fetchMetadata = async () => {
            try {
                const [comunasRes, tiposInmRes, tiposOpRes] = await Promise.all([
                    axios.get(`${API_URL}/comunas`),
                    axios.get(`${API_URL}/tipos_inmueble`),
                    axios.get(`${API_URL}/tipos_operacion`)
                ]);
                setMetadata({
                    comunas: comunasRes.data,
                    tiposInmueble: tiposInmRes.data,
                    tiposOperacion: tiposOpRes.data
                });
            } catch (error) {
                console.error("Error fetching metadata:", error);
            }
        };
        fetchMetadata();
    }, []);

    useEffect(() => {
        const fetchProperties = async () => {
            setLoading(true);
            try {
                const params = {
                    skip: (page - 1) * ITEMS_PER_PAGE,
                    limit: ITEMS_PER_PAGE
                };
                if (filters.comuna) params.comuna = filters.comuna;
                if (filters.tipo_operacion) params.tipo_operacion = filters.tipo_operacion;
                if (filters.tipo_inmueble) params.tipo_inmueble = filters.tipo_inmueble;

                const response = await axios.get(`${API_URL}/propiedades/`, { params });
                setProperties(response.data);
            } catch (error) {
                console.error("Error fetching properties:", error);
            } finally {
                setLoading(false);
            }
        };

        const timeoutId = setTimeout(() => {
            fetchProperties();
        }, 300);

        return () => clearTimeout(timeoutId);
    }, [filters, page]);

    const handleFilterChange = (newFilters) => {
        setFilters(newFilters);
        setPage(1);
    };

    const handlePrevPage = () => {
        if (page > 1) {
            setPage(page - 1);
            window.scrollTo({ top: 0, behavior: 'smooth' });
        }
    };

    const handleNextPage = () => {
        if (properties.length === ITEMS_PER_PAGE) {
            setPage(page + 1);
            window.scrollTo({ top: 0, behavior: 'smooth' });
        }
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
            {/* Header */}
            <header className="bg-white shadow-md sticky top-0 z-20 border-b-4 border-indigo-600">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-5">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-4">
                            <div className="bg-gradient-to-br from-indigo-600 via-purple-600 to-pink-600 p-3 rounded-2xl shadow-lg transform hover:scale-110 transition-transform">
                                <Building2 className="w-7 h-7 text-white" />
                            </div>
                            <div>
                                <h1 className="text-3xl font-black text-transparent bg-clip-text bg-gradient-to-r from-indigo-600 to-purple-600">
                                    Comuna Dash
                                </h1>
                                <p className="text-sm text-gray-500 font-medium">Encuentra tu propiedad ideal</p>
                            </div>
                        </div>
                        <div className="flex items-center gap-4">
                            <div className="hidden sm:flex items-center gap-2 bg-gradient-to-r from-indigo-50 to-purple-50 px-4 py-2 rounded-xl border-2 border-indigo-200">
                                <TrendingUp className="w-4 h-4 text-indigo-600" />
                                <span className="text-sm font-bold text-gray-700">Página {page}</span>
                            </div>
                            <div className="bg-gradient-to-r from-emerald-50 to-teal-50 px-4 py-2 rounded-xl border-2 border-emerald-200">
                                <span className="text-sm font-bold text-emerald-700">{properties.length} propiedades</span>
                            </div>
                        </div>
                    </div>
                </div>
            </header>

            <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
                <Filters
                    filters={filters}
                    setFilters={handleFilterChange}
                    comunas={metadata.comunas}
                    tiposInmueble={metadata.tiposInmueble}
                    tiposOperacion={metadata.tiposOperacion}
                />

                {loading ? (
                    <div className="flex flex-col justify-center items-center h-96">
                        <Loader2 className="w-16 h-16 text-indigo-600 animate-spin mb-4" />
                        <p className="text-gray-500 font-medium">Cargando propiedades...</p>
                    </div>
                ) : (
                    <>
                        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-8">
                            {properties.map((property) => (
                                <PropertyCard key={property.id_aviso || property.url} property={property} />
                            ))}
                        </div>

                        {/* Pagination */}
                        {properties.length > 0 && (
                            <div className="mt-12 flex justify-center items-center gap-4">
                                <button
                                    onClick={handlePrevPage}
                                    disabled={page === 1}
                                    className="flex items-center px-6 py-3 border-2 border-indigo-300 rounded-xl text-sm font-bold text-indigo-700 bg-white hover:bg-indigo-50 disabled:opacity-40 disabled:cursor-not-allowed transition-all shadow-md hover:shadow-lg"
                                >
                                    <ChevronLeft className="w-5 h-5 mr-1" />
                                    Anterior
                                </button>
                                <div className="bg-gradient-to-r from-indigo-600 to-purple-600 text-white px-6 py-3 rounded-xl shadow-lg">
                                    <span className="text-sm font-bold">Página {page}</span>
                                </div>
                                <button
                                    onClick={handleNextPage}
                                    disabled={properties.length < ITEMS_PER_PAGE}
                                    className="flex items-center px-6 py-3 border-2 border-indigo-300 rounded-xl text-sm font-bold text-indigo-700 bg-white hover:bg-indigo-50 disabled:opacity-40 disabled:cursor-not-allowed transition-all shadow-md hover:shadow-lg"
                                >
                                    Siguiente
                                    <ChevronRight className="w-5 h-5 ml-1" />
                                </button>
                            </div>
                        )}
                    </>
                )}

                {!loading && properties.length === 0 && (
                    <div className="text-center py-20 bg-white rounded-2xl shadow-lg border-2 border-gray-100">
                        <div className="max-w-md mx-auto">
                            <div className="bg-gray-100 w-20 h-20 rounded-full flex items-center justify-center mx-auto mb-4">
                                <Building2 className="w-10 h-10 text-gray-400" />
                            </div>
                            <h3 className="text-xl font-bold text-gray-800 mb-2">No se encontraron propiedades</h3>
                            <p className="text-gray-500">Intenta ajustar los filtros para ver más resultados.</p>
                        </div>
                    </div>
                )}
            </main>

            {/* Footer */}
            <footer className="bg-white border-t-2 border-gray-200 mt-16">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
                    <p className="text-center text-sm text-gray-500">
                        © 2025 Comuna Dash - Agregador de propiedades de Biobío
                    </p>
                </div>
            </footer>
        </div>
    );
};

export default Dashboard;
