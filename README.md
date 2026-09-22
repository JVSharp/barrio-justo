<div align="center">

# Barrio Justo

**Dónde vivir en el Biobío: a precio justo, cerca de lo que te importa y con sol en invierno.**

Buscador de casas y departamentos que ordena los avisos según tu presupuesto, lo que quieres tener cerca y cuántas horas de sol reciben el día más corto del año. Detrás: scraper, API y un análisis de precios que no se deja engañar por los avisos mal cargados.

**[→ Ver la demo en vivo](https://jvsharp.github.io/barrio-justo/)** · sin instalar nada, con datos de demostración

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-18-61DAFB?style=flat-square&logo=react&logoColor=black)
![MongoDB](https://img.shields.io/badge/MongoDB-opcional-47A248?style=flat-square&logo=mongodb&logoColor=white)
[![CI](https://github.com/JVSharp/barrio-justo/actions/workflows/ci.yml/badge.svg)](https://github.com/JVSharp/barrio-justo/actions/workflows/ci.yml)
![Tests](https://img.shields.io/badge/tests-86-15803D?style=flat-square)

<img src="docs/img/dashboard-mercado.png" alt="Vista de mercado: mediana de UF por m² por comuna" width="860">

</div>

---

## De qué se trata

Quería saber cuánto sale de verdad un departamento en Concepción comparado con San Pedro, Chiguayante o Talcahuano, y los portales no te muestran eso: te muestran avisos uno por uno. Así que armé esto.

El scraper recorre las 33 comunas de la región y guarda cada aviso (casas y departamentos, en venta y en arriendo). La API los limpia y calcula por comuna la mediana, el rango típico y el precio por m². El dashboard lo muestra en dos vistas: una para comparar comunas y otra para revisar los avisos uno a uno.

## Lo más interesante: no confiar en el promedio

La primera versión calculaba promedios, y los números salían raros. Casas en Chiguayante a casi 14.000 UF de promedio, o departamentos *en arriendo* en Los Ángeles a 3.250 UF al mes. Bastaban un par de avisos mal cargados (una venta publicada como arriendo, un precio con ceros de menos) para mover la comuna entera.

Así que ahora el análisis hace tres cosas:

1. **Revisa cada aviso contra reglas simples de plausibilidad.** Un arriendo de más de 300 UF casi siempre es una venta mal clasificada, y una venta bajo 300 UF casi siempre es un error de tipeo. Esos avisos no se borran: quedan fuera de las estadísticas, marcados y con el motivo a la vista.
2. **Usa mediana y percentiles (p25–p75) en vez de promedio.** Un solo valor absurdo no los mueve.
3. **Calcula la UF/m² solo cuando la superficie es creíble.** Nada de avisos con "2 m²".

<img src="docs/img/promedio-vs-mediana.png" alt="Promedio de los datos crudos vs mediana después de limpiar" width="760">

Las reglas están todas en [`backend/analisis.py`](backend/analisis.py), con sus tests.

## Buscador: lo que tú buscas, ordenado por calce

La pestaña **Buscador** parte de la persona y no del mercado. Indicas si compras o arriendas, el tipo, tu presupuesto, dormitorios y comunas (esos son filtros duros), y después **qué te importa**, con tres niveles (no, algo, mucho):

- **Precio bajo el mercado**: cuánto se aleja el aviso de la mediana de UF/m² de su comuna.
- **Sol en invierno**: horas de sol directo el 21 de junio, el día más corto del año, mirando desde la calle o desde un 3°, 6° o 10° piso.
- **Cerca de**: Biotren o terminal, universidad, colegio, hospital o clínica, supermercado, parque.

El resultado es un ranking con explicación: cada aviso muestra su **porcentaje de calce** y el aporte de cada criterio ("a 350 m de Estación Concepción", "4,5 h de sol el 21 de junio desde un 6° piso", "−9 % vs. la mediana"). Los pesos se mueven y el ranking se reordena al instante, porque el puntaje se calcula en el navegador ([`src/puntaje.js`](comuna-frontend/src/puntaje.js), con tests).

### Cómo se calcula el sol

1. Posición del sol cada 10 minutos del 21 de junio, con las ecuaciones de la NOAA ([`backend/sol.py`](backend/sol.py)). Los tests la contrastan con valores conocidos: el sol culmina al norte a ~29,7° en Concepción.
2. Para cada aviso se arma el "horizonte" de edificios en 150 m, con footprints y alturas de OpenStreetMap: para cada grado de azimut, el ángulo que tapa el edificio más alto.
3. Hay sol cuando el sol está sobre ese horizonte. Se repite a la altura de la calle y de los pisos 3, 6 y 10.

Lo que **no** mide: la orientación de las ventanas, árboles ni cerros (el Caracol le quita sol de mañana a parte del centro). Cada valor trae la calidad del dato: qué porcentaje de los edificios cercanos tiene altura conocida en OSM; el resto se asume de 2 pisos.

### Datos de OpenStreetMap

```bash
python scripts/descargar_osm.py     # lugares y edificios (~10 min, una vez)
python scripts/enriquecer_geo.py    # distancias y horas de sol por aviso
```

Lugares y edificios © colaboradores de OpenStreetMap, [ODbL](https://www.openstreetmap.org/copyright).

## ¿Este aviso está caro?

Cada aviso se compara con los de su misma comuna, operación y tipo. Si su UF/m² cae bajo el cuartil inferior, queda como **bajo el mercado**; sobre el superior, **sobre el mercado**; entremedio, **en rango**. Además muestra cuánto se aleja de la mediana (por ejemplo, "−12 % vs. la mediana de Concepción").

Si la comuna tiene menos de 10 avisos comparables, no se inventa una referencia: el aviso queda como **sin referencia**.

En la pestaña Avisos se puede filtrar por posición y ordenar por "más bajo vs. su comuna", que en la práctica es una lista de oportunidades.

### Historial de precio

Cada vez que el scraper vuelve a ver un aviso, compara el precio con el último que tenía guardado. Si cambió, agrega un punto al historial. La tarjeta muestra cuántos días lleva publicado y si bajó o subió de precio desde que apareció.

### Rentabilidad bruta estimada

La vista Mercado cruza las medianas de venta y de arriendo por m² de cada comuna:

```
rentabilidad bruta ≈ (arriendo UF/m² al mes × 12) / venta UF/m²
```

Es una cifra gruesa (no descuenta gastos, contribuciones ni meses vacíos, y compara avisos distintos), pero sirve para ver de un vistazo en qué comunas arrendar rinde más respecto de lo que cuesta comprar.

## Mapa 3D

La comuna es una unidad demasiado gruesa: el centro de Concepción y Lomas de San Andrés no cuestan lo mismo por m². La pestaña **Mapa 3D** divide la ciudad en celdas de ~500 m. Cada celda es una columna hexagonal: la **altura** es cuántos avisos tiene y el **color**, su mediana de UF/m². Las celdas con menos de 3 avisos no se dibujan.

La agregación se hace en el backend (`analisis.celdas()`, con la misma mediana del resto del proyecto); el navegador solo dibuja, con MapLibre y deck.gl sobre mapas de OpenFreeMap.

<img src="docs/img/dashboard-mapa.png" alt="Mapa 3D: columnas hexagonales por celda de ~500 m" width="860">

**Sombras (experimental).** Al activarlas aparecen los edificios de OpenStreetMap en 3D con la sombra del sol para la fecha y hora que elijas. Es ilustrativo: las alturas de OSM están incompletas y los avisos no dicen en qué piso ni hacia dónde miran las ventanas, así que el proyecto **no** asigna un puntaje de asoleamiento por aviso.

> En la demo, las coordenadas de los avisos son inventadas alrededor del centro de cada comuna. El scraper guarda las reales.

## Cómo se ve

<table>
<tr>
<td width="50%"><img src="docs/img/dashboard-avisos.png" alt="Vista de avisos con filtros"><br>
<sub><b>Avisos.</b> Filtros por comuna, operación y tipo, orden por precio o UF/m². Los que quedaron fuera del análisis aparecen marcados y dicen por qué.</sub></td>
<td width="50%"><img src="docs/img/uf-m2-por-comuna.png" alt="UF por m² según comuna"><br>
<sub><b>Precio por m².</b> El punto es la mediana y la barra, el rango donde cae la mitad de los avisos.</sub></td>
</tr>
</table>

Y este es con datos reales, del scraping que hice en 2025:

<img src="docs/img/avisos-por-comuna.png" alt="Avisos capturados por comuna, datos reales" width="620">

> Las imágenes del dashboard y los gráficos de precios usan la **demo**: la cantidad de avisos por comuna viene del scraping real, pero los precios y superficies son inventados. Cada gráfico lo dice en el pie.

## Probarlo

La forma más rápida es la **[demo en vivo](https://jvsharp.github.io/barrio-justo/)**: es el mismo dashboard, compilado en modo estático y publicado en GitHub Pages. No tiene backend; los datos se exportan con las mismas funciones de la API (`scripts/exportar_estatico.py`), así que muestra exactamente las mismas cifras.

### En tu máquina, sin MongoDB

El repo trae un set de avisos de demo, así que no necesitas instalar nada más que Python y Node.

```bash
git clone https://github.com/JVSharp/barrio-justo.git
cd barrio-justo

# API
cd backend
python -m venv .venv && source .venv/bin/activate    # en Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload                            # http://127.0.0.1:8000/docs

# Dashboard (en otra terminal)
cd comuna-frontend
npm install
npm run dev                                          # http://localhost:5173
```

## Con datos reales

> **Para usarlo con datos actuales hace falta una integración legal con Mercado Libre** (ver [Sobre los datos](#sobre-los-datos)). Los pasos de abajo sirven para aprender y probar en local.

Necesitas MongoDB corriendo en local (o una URI de Atlas).

```bash
cp .env.example .env          # y cambia FUENTE_DATOS=mongo
cd backend
python scraper.py                        # las 33 comunas (demora: pide una página por segundo)
python scraper.py concepcion penco       # o solo algunas
uvicorn main:app --reload
```

Cada aviso se guarda una vez por URL. Si vuelves a correr el scraper se actualiza el precio y la fecha en que se vio por última vez, y se conserva la fecha en que apareció. Con eso queda la base lista para medir cuánto dura publicado un aviso o cómo cambia su precio.

## Datos al día

`scripts/actualizar.sh` corre el scraper y calcula cercanía y sol de los avisos nuevos. Para que corra solo los domingos a las 04:00 en tu Mac:

```bash
# edita RUTA_DEL_REPO en el archivo y luego:
cp scripts/launchd/cl.jvsharp.barrio-justo.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/cl.jvsharp.barrio-justo.plist
```

## API

| Ruta | Qué devuelve |
|---|---|
| `GET /propiedades` | Avisos filtrados (`comuna`, `tipo_operacion`, `tipo_inmueble`, `posicion`), ordenados (`orden`) y paginados. Cada aviso trae su UF/m², su posición frente a la comuna, días publicado, cambio de precio y, si quedó fuera del análisis, el motivo. |
| `GET /resumen` | Mediana, p25–p75 y UF/m² por comuna, para una operación y un tipo. |
| `GET /resumen/{comuna}` | Todas las combinaciones de una comuna. |
| `GET /calidad` | Cuántos avisos quedaron fuera del análisis y por qué. |
| `GET /rentabilidad` | Rentabilidad bruta estimada por comuna y tipo. |
| `GET /buscador` | Candidatos que cumplen presupuesto, tipo, dormitorios y comunas, con sus métricas de precio, cercanía y sol. |
| `GET /lugares` | Lugares de interés de OpenStreetMap por categoría. |
| `GET /mapa` | Celdas de ~500 m con mediana de UF/m² y cantidad de avisos. |
| `GET /comunas` · `/tipos_inmueble` · `/tipos_operacion` | Valores para los filtros. |
| `GET /salud` | Qué fuente de datos está usando (demo o mongo). |

Documentación interactiva en `/docs` apenas levantas la API.

## Estructura

```
backend/
  main.py            API (FastAPI)
  analisis.py        limpieza y estadística
  repositorio.py     acceso a datos: MongoDB o la demo en CSV
  scrapers/          scraper de PortalInmobiliario
  tests/             pytest
comuna-frontend/     React + Vite + Tailwind + Recharts
data/
  comunas_biobio.csv                    las 33 comunas, con provincia
  snapshot_2025_resumen_por_comuna.csv  resumen del scraping real
  demo/avisos.csv                       datos ficticios para la demo
scripts/
  generar_demo.py · graficos.py · capturas.py · exportar_estatico.py
  resumen.py · check_db.py · diagnostico_portal.py
.github/workflows/
  ci.yml (tests, lint, build) · pages.yml (demo en vivo)
```

## Tests

```bash
cd backend
pip install -r requirements-dev.txt
pytest -q
```

Cubren las reglas de limpieza, la estadística, los endpoints y el scraper sin red. Varios existen por problemas reales:

- La paginación de la primera versión agregaba `#2` a la URL, y como lo que va después de `#` nunca llega al servidor, cada página devolvía los mismos resultados.
- En 2026 el portal cambió el formato de su respuesta: cada aviso ahora viene envuelto en una "polycard" con el precio y los atributos dentro de componentes. El scraper seguía corriendo sin errores y guardaba cero avisos. Ahora lee el formato nuevo (y el antiguo), y si llega algo que no reconoce, se detiene con un mensaje en vez de fallar en silencio.
- Los proyectos inmobiliarios nuevos publican "desde X UF". Ese no es el precio de ninguna unidad, así que quedan fuera de las medianas.

## Regenerar imágenes

```bash
python scripts/generar_demo.py     # datos de demo
python scripts/graficos.py         # gráficos de docs/img
python scripts/capturas.py         # capturas del dashboard (necesita Playwright)
```

## Sobre los datos

**La demo en vivo no usa datos reales de avisos.** Precios, superficies y coordenadas son ficticios; la cantidad de avisos por comuna viene del scraping de 2025, y los lugares cercanos (Biotren, colegios, salud, supermercados, parques) son reales, de OpenStreetMap. El sol se calcula con el método real, pero sobre edificios ficticios.

**Para que funcione con datos actuales se necesita una fuente legal.** PortalInmobiliario es de Mercado Libre, y la vía correcta es su [API oficial](https://developers.mercadolibre.cl/): registrar una aplicación en su portal de desarrolladores, autenticarse con OAuth y respetar sus términos de uso y límites. Esa integración todavía no está hecha; el repositorio deja preparada la capa (`backend/scrapers/base.py` guarda en MongoDB con historial de precios) para enchufar un cliente de la API en vez del scraper.

El scraper que trae el repositorio es un ejercicio de aprendizaje: pide una página por segundo, se identifica como `barrio-justo` y no guarda datos personales de quienes publican. La mayoría de los portales no permiten la extracción automatizada, así que no está pensado para publicar datos ni para uso comercial.

Créditos: mapas, edificios y lugares © colaboradores de [OpenStreetMap](https://www.openstreetmap.org/copyright) (ODbL); mapa base de [OpenFreeMap](https://openfreemap.org); íconos [Solar](https://github.com/480-Design/Solar-Icon-Set) de 480 Design (CC BY 4.0).

## Lo que viene

- **Integración con la API de Mercado Libre** para tener datos actuales de forma legal.
- Edificios reales de OpenStreetMap para el cálculo del sol (hoy la demo usa una ciudad ficticia).
- Referencia por barrio en vez de por comuna: el centro de Concepción y Lomas de San Andrés no deberían compararse entre sí.
- Un modelo de precio que explique *por qué* un aviso está caro, no solo *que* lo está.

---

<sub>Hecho por <a href="https://jvsharp.dev">John Sharp</a> en Concepción.</sub>
