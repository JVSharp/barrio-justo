import React from 'react';
import { MapPin, Bed, Bath, Ruler, ExternalLink, Calendar, Tag } from 'lucide-react';

const PropertyCard = ({ property }) => {
    const {
        titulo,
        precio_uf,
        precio_clp,
        direccion,
        comuna,
        superficie_m2,
        dormitorios,
        baños,
        url,
        source,
        tipo_operacion,
        tipo_inmueble,
        fecha_scraping
    } = property;

    const formatPrice = (price) => {
        return new Intl.NumberFormat('es-CL', { style: 'currency', currency: 'CLP' }).format(price);
    };

    const formatDate = (dateString) => {
        if (!dateString) return '';
        const date = new Date(dateString);
        return date.toLocaleDateString('es-CL', { year: 'numeric', month: 'short', day: 'numeric' });
    };

    // Determine source badge color
    const getSourceColor = () => {
        if (source === 'Yapo') return 'bg-purple-50 text-purple-600 border-purple-200';
        if (source === 'PortalInmobiliario') return 'bg-blue-50 text-blue-600 border-blue-200';
        return 'bg-gray-50 text-gray-600 border-gray-200';
    };

    // Helper to check if value exists
    const hasValue = (val) => val && val !== '' && val !== '0' && val !== 0;

    return (
        <div className="bg-white rounded-2xl shadow-lg overflow-hidden hover:shadow-2xl transition-all duration-300 border-2 border-gray-100 group hover:border-indigo-200">
            <div className="p-6">
                {/* Header with badges */}
                <div className="flex justify-between items-start mb-3">
                    <div className="flex gap-2 flex-wrap">
                        <span className="inline-block px-3 py-1.5 text-xs font-bold tracking-wide text-indigo-700 uppercase bg-gradient-to-r from-indigo-50 to-indigo-100 rounded-full border border-indigo-200">
                            {tipo_operacion}
                        </span>
                        <span className="inline-block px-3 py-1.5 text-xs font-bold tracking-wide text-emerald-700 uppercase bg-gradient-to-r from-emerald-50 to-emerald-100 rounded-full border border-emerald-200">
                            {tipo_inmueble}
                        </span>
                    </div>
                    <span className={`text-xs font-semibold px-3 py-1.5 rounded-full border ${getSourceColor()}`}>
                        {source || 'PortalInmobiliario'}
                    </span>
                </div>

                {/* Title */}
                <h3 className="text-xl font-bold text-gray-900 mb-3 line-clamp-2 h-14 group-hover:text-indigo-700 transition-colors leading-tight" title={titulo}>
                    {titulo}
                </h3>

                {/* Location */}
                <div className="flex items-center text-gray-600 text-sm mb-4 bg-gray-50 rounded-lg px-3 py-2">
                    <MapPin className="w-4 h-4 mr-2 flex-shrink-0 text-indigo-500" />
                    <span className="truncate font-medium">{direccion}, {comuna}</span>
                </div>

                {/* Price */}
                <div className="flex items-end justify-between mb-4 pb-4 border-b-2 border-gray-100">
                    <div>
                        <p className="text-3xl font-black text-transparent bg-clip-text bg-gradient-to-r from-indigo-600 to-purple-600">
                            UF {precio_uf.toLocaleString('es-CL')}
                        </p>
                        <p className="text-sm text-gray-600 font-medium mt-1">{formatPrice(precio_clp)}</p>
                    </div>
                    {fecha_scraping && (
                        <div className="flex items-center text-xs text-gray-400 bg-gray-50 px-2 py-1 rounded-md">
                            <Calendar className="w-3 h-3 mr-1" />
                            <span>{formatDate(fecha_scraping)}</span>
                        </div>
                    )}
                </div>

                {/* Property details - only show if at least one value exists */}
                {(hasValue(superficie_m2) || hasValue(dormitorios) || hasValue(baños)) ? (
                    <div className="grid grid-cols-3 gap-3 py-3 text-sm text-gray-700">
                        {hasValue(superficie_m2) && (
                            <div className="flex flex-col items-center justify-center bg-gradient-to-br from-indigo-50 to-indigo-100 rounded-xl py-3 border border-indigo-200">
                                <Ruler className="w-5 h-5 mb-1.5 text-indigo-600" />
                                <span className="font-bold text-gray-900">{superficie_m2}</span>
                                <span className="text-xs text-gray-500 font-medium">m²</span>
                            </div>
                        )}
                        {hasValue(dormitorios) && (
                            <div className="flex flex-col items-center justify-center bg-gradient-to-br from-purple-50 to-purple-100 rounded-xl py-3 border border-purple-200">
                                <Bed className="w-5 h-5 mb-1.5 text-purple-600" />
                                <span className="font-bold text-gray-900">{dormitorios}</span>
                                <span className="text-xs text-gray-500 font-medium">dorm</span>
                            </div>
                        )}
                        {hasValue(baños) && (
                            <div className="flex flex-col items-center justify-center bg-gradient-to-br from-blue-50 to-blue-100 rounded-xl py-3 border border-blue-200">
                                <Bath className="w-5 h-5 mb-1.5 text-blue-600" />
                                <span className="font-bold text-gray-900">{baños}</span>
                                <span className="text-xs text-gray-500 font-medium">baños</span>
                            </div>
                        )}
                    </div>
                ) : (
                    <div className="py-3 text-center">
                        <p className="text-sm text-gray-400 italic">Detalles no disponibles</p>
                    </div>
                )}

                {/* CTA Button */}
                <a
                    href={url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="mt-4 w-full flex items-center justify-center px-5 py-3.5 border-2 border-transparent text-sm font-bold rounded-xl text-white bg-gradient-to-r from-indigo-600 via-indigo-700 to-purple-600 hover:from-indigo-700 hover:via-indigo-800 hover:to-purple-700 transition-all shadow-lg hover:shadow-xl focus:outline-none focus:ring-4 focus:ring-indigo-300 transform hover:scale-105"
                >
                    Ver Publicación <ExternalLink className="ml-2 w-4 h-4" />
                </a>
            </div>
        </div>
    );
};

export default PropertyCard;
