import React from 'react';
import { MapPin, Bed, Bath, Ruler, ExternalLink } from 'lucide-react';

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
        tipo_inmueble
    } = property;

    const formatPrice = (price) => {
        return new Intl.NumberFormat('es-CL', { style: 'currency', currency: 'CLP' }).format(price);
    };

    return (
        <div className="bg-white rounded-xl shadow-md overflow-hidden hover:shadow-lg transition-shadow duration-300 border border-gray-100">
            <div className="p-5">
                <div className="flex justify-between items-start mb-2">
                    <span className="inline-block px-2 py-1 text-xs font-semibold tracking-wide text-indigo-500 uppercase bg-indigo-50 rounded-full">
                        {tipo_operacion}
                    </span>
                    <span className="text-xs text-gray-400 font-medium">{source || 'PortalInmobiliario'}</span>
                </div>

                <h3 className="text-lg font-bold text-gray-900 mb-1 line-clamp-2 h-14" title={titulo}>
                    {titulo}
                </h3>

                <div className="flex items-center text-gray-500 text-sm mb-4">
                    <MapPin className="w-4 h-4 mr-1" />
                    <span className="truncate">{direccion}, {comuna}</span>
                </div>

                <div className="flex items-end justify-between mb-4">
                    <div>
                        <p className="text-2xl font-bold text-gray-900">UF {precio_uf.toLocaleString('es-CL')}</p>
                        <p className="text-sm text-gray-500">{formatPrice(precio_clp)}</p>
                    </div>
                </div>

                <div className="grid grid-cols-3 gap-2 py-3 border-t border-gray-100 text-sm text-gray-600">
                    <div className="flex flex-col items-center justify-center">
                        <Ruler className="w-4 h-4 mb-1 text-indigo-400" />
                        <span>{superficie_m2 || '-'} m²</span>
                    </div>
                    <div className="flex flex-col items-center justify-center border-l border-gray-100">
                        <Bed className="w-4 h-4 mb-1 text-indigo-400" />
                        <span>{dormitorios || '-'} dorm</span>
                    </div>
                    <div className="flex flex-col items-center justify-center border-l border-gray-100">
                        <Bath className="w-4 h-4 mb-1 text-indigo-400" />
                        <span>{baños || '-'} baños</span>
                    </div>
                </div>

                <a
                    href={url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="mt-4 w-full flex items-center justify-center px-4 py-2 border border-transparent text-sm font-medium rounded-lg text-white bg-indigo-600 hover:bg-indigo-700 transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                >
                    Ver Publicación <ExternalLink className="ml-2 w-4 h-4" />
                </a>
            </div>
        </div>
    );
};

export default PropertyCard;
