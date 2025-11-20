import React, { useState, useEffect } from 'react';
import axios from 'axios';
import PropertyCard from './PropertyCard';
import Filters from './Filters';
import { Building2, Loader2 } from 'lucide-react';

const API_URL = 'http://127.0.0.1:8000';

const Dashboard = () => {
    const [properties, setProperties] = useState([]);
    const [loading, setLoading] = useState(true);
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
                const params = {};
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

        // Debounce fetching
        const timeoutId = setTimeout(() => {
            fetchProperties();
        }, 300);

        return () => clearTimeout(timeoutId);
    }, [filters]);

    return (
        <div className="min-h-screen bg-gray-50">
            {/* Header */}
            <header className="bg-white shadow-sm sticky top-0 z-10">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                        <div className="bg-indigo-600 p-2 rounded-lg">
                            <Building2 className="w-6 h-6 text-white" />
                        </div>
                        <h1 className="text-2xl font-bold text-gray-900">Comuna Dash</h1>
                    </div>
                    <div className="text-sm text-gray-500">
                        {properties.length} propiedades encontradas
                    </div>
                </div>
            </header>

            <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                <Filters
                    filters={filters}
                    setFilters={setFilters}
                    comunas={metadata.comunas}
                    tiposInmueble={metadata.tiposInmueble}
                    tiposOperacion={metadata.tiposOperacion}
                />

                {loading ? (
                    <div className="flex justify-center items-center h-64">
                        <Loader2 className="w-12 h-12 text-indigo-600 animate-spin" />
                    </div>
                ) : (
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                        {properties.map((property) => (
                            <PropertyCard key={property.id_aviso || property.url} property={property} />
                        ))}
                    </div>
                )}

                {!loading && properties.length === 0 && (
                    <div className="text-center py-12">
                        <p className="text-gray-500 text-lg">No se encontraron propiedades con estos filtros.</p>
                    </div>
                )}
            </main>
        </div>
    );
};

export default Dashboard;
