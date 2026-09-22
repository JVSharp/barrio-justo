# PRD v4 — Mapa 3D de precios (+ sombras, experimental)

**Estado:** aprobado por John (2026-09-22: "Mapa 3D de precios + sombras experimental").

## Problema

La comuna es una unidad demasiado gruesa: el centro de Concepción y Lomas de
San Andrés tienen la misma "mediana de Concepción". El scraper ya guarda
latitud y longitud de cada aviso, pero nada lo muestra en el espacio.

John además preguntó por "dónde llega mejor el sol". Eso no se puede
responder por aviso con los datos disponibles: los avisos no traen piso ni
orientación de forma confiable, y las alturas de edificios de OpenStreetMap
en Concepción están incompletas.

## Criterios de éxito

1. Pestaña **Mapa 3D**: la ciudad dividida en celdas de ~500 m; cada celda es
   una columna cuya **altura = cantidad de avisos** y **color = mediana de UF/m²**
   (mediana, no promedio, igual que el resto del proyecto).
2. Filtros de operación y tipo; tooltip con mediana, rango y n; leyenda.
3. Celdas con menos de 3 avisos no se dibujan (una celda con 1 aviso no es un
   precio de zona).
4. **Modo sombras (experimental):** edificios 3D de OpenStreetMap con la sombra
   del sol para una fecha y hora elegidas. Rotulado como ilustrativo, **sin
   puntaje de sol por aviso**.
5. Funciona igual en la demo en vivo (sin backend) que con la API.
6. No engorda la carga inicial: el mapa se carga solo al abrir su pestaña.

## Alcance

**Entra:** endpoint `/mapa` (celdas ya agregadas), coordenadas sintéticas en la
demo (alrededor del centro urbano de cada comuna, rotuladas como ficticias),
vista con MapLibre + deck.gl, mapa base y edificios de OpenFreeMap (gratis,
sin llave).

**No entra:** puntaje de asoleamiento por aviso, orientación de ventanas,
scraping de fichas individuales (más carga sobre el portal), referencia de
precio por celda en las tarjetas (siguiente ronda: primero ver si las celdas
reales tienen muestra suficiente).

## Decisiones

- **La agregación se hace en el backend** (`analisis.celdas()`), con la misma
  mediana que el resto. El frontend solo dibuja. En la demo estática las
  celdas se exportan ya calculadas, así que no hay dos implementaciones.
- **Grilla lat/lon de 0,005°** (~550 m × 450 m en Concepción). Simple de
  explicar; H3 sería más prolijo pero agrega dependencia sin cambiar la lectura.
- **Sombras con deck.gl `_SunLight`** sobre edificios en tiles vectoriales.
  Es una API marcada experimental en deck.gl: si falla en algún navegador, el
  modo se apaga y el mapa de precios sigue funcionando.

## Riesgos

1. **No puedo ver WebGL desde mi entorno.** La verificación visual se hace
   abriendo el dashboard en el Chrome de John.
2. **Coordenadas de la demo son inventadas:** algunas celdas pueden caer en
   zonas sin viviendas (o en el mar en comunas costeras). Se rotula.
3. **OpenFreeMap es un servicio gratuito de terceros:** si cae, el mapa base no
   carga. Las columnas de deck.gl se siguen dibujando.

## Registro de construcción

**2026-09-22 · construido y revisado en el Chrome de John**

- `analisis.celdas()`: grilla de 0,005°, mediana/p25/p75 de UF/m² y n por celda; descarta sin coordenadas, fuera de la región y excluidos; mínimo 3 por celda.
- API `/mapa`; exportado en la demo estática por operación × tipo.
- Demo: coordenadas ficticias por comuna (deptos más concentrados que casas) y un gradiente de precio hacia el centro para que el mapa tenga lectura.
- `repositorio`: lat/long se leen con `float()` (`numero()` perdía el signo negativo; lo atrapó un test).
- Frontend: pestaña Mapa 3D cargada con `React.lazy` (2 MB solo al abrirla), columnas hexagonales, leyenda, tooltip, modo sombras con fecha y hora de Chile, vuelo automático al acercarse.
- Tests: 55 → 61.

**Revisión visual (Chrome, localhost en modo estático):**

- Mapa de precios: columnas sobre la ciudad correcta (Concepción al este del Biobío, San Pedro al oeste, Talcahuano, Hualpén, Penco), tooltip y leyenda OK.
- Encontrado y corregido 1: con sombras, las columnas de ~1,4 km tapaban los edificios → en modo sombras los precios se aplanan como hexágonos translúcidos en el suelo.
- Encontrado y corregido 2: fachadas casi negras → más luz ambiente y material más claro.
- Encontrado y corregido 3: al mover la hora, todo el suelo quedaba en sombra (mapa de sombras desactualizado en capas ya compiladas de deck.gl). Las capas con sombra llevan el instante en su id y se recrean con la luz; el control de hora aplica con 200 ms de respiro.
- Comprobado: 10:00 → sombras hacia el suroeste; 16:00 → hacia el este-sureste; 19:00 → largas hacia el este. Coincide con el recorrido del sol en Concepción a fines de septiembre.
