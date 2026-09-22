# PRD v5 — Buscador por perfil: presupuesto, cercanía y sol en invierno

**Estado:** aprobado por John (2026-09-22). Decisiones: seguir con el scraper
actual (sin API de ML ni sitios nuevos), cercanía a transporte, educación,
salud, supermercados y parques; sol = horas de sol el 21 de junio con piso
elegible; construir primero el buscador sobre la demo.

## Problema

El dashboard responde preguntas de mercado ("cuánto cuesta el m² en
Concepción"), pero quien busca casa pregunta otra cosa: **"con 4.000 UF, un
depto de 2 dormitorios, cerca del Biotren y que no quede tapado del sol todo
el invierno: ¿qué hay?"**. Hoy eso no se puede contestar sin revisar aviso por
aviso.

## Criterios de éxito

1. Pestaña **Buscador**: la persona indica operación, tipo, presupuesto,
   dormitorios mínimos y comunas (filtros duros), y qué le importa (cercanía
   a cada categoría, precio bajo mercado, sol) con un peso.
2. El resultado es un **ranking con explicación**: puntaje total y el aporte
   de cada criterio ("a 350 m del Biotren", "−9 % vs. mediana", "4,5 h de sol
   el 21 de junio en un 5° piso").
3. Los pesos se mueven y el ranking se reordena al instante (en el navegador).
4. **Horas de sol** por aviso para el día más corto del año, a nivel de calle
   y en pisos 3, 6 y 10, considerando los edificios de OpenStreetMap en 150 m.
   Cada valor trae un indicador de calidad (qué % de esos edificios tiene
   altura conocida).
5. **Distancias** en línea recta a lo más cercano de cada categoría.
6. Funciona igual en la demo en vivo que con la API.
7. **Actualización semanal** del scraper en el Mac de John (launchd).

## Método del sol (lo que mide y lo que no)

- Posición solar con el algoritmo de la NOAA, cada 10 minutos entre salida y
  puesta del sol del 21 de junio.
- Para cada aviso se arma un "horizonte" de 360°: para cada dirección, el
  ángulo de elevación más alto que tapa un edificio cercano. Hay sol directo
  cuando el sol está por sobre ese horizonte.
- Edificios sin altura en OSM: se asume la de sus pisos (`building:levels` ×
  3 m) o, si tampoco hay, 2 pisos. Eso baja el indicador de calidad.
- **No mide:** la orientación de las ventanas ni el piso real del aviso (los
  portales no lo informan de forma confiable), árboles, ni cerros. En
  Concepción los cerros (Caracol, Chepe) quitan sol de mañana o de tarde en
  algunas zonas: queda como limitación explícita.
- Coordenadas de los avisos: las del portal, que a veces son aproximadas
  (centro de la manzana o del barrio). En la demo son inventadas.

## Alcance

**Entra:** `backend/sol.py`, `backend/geo.py`, `scripts/descargar_osm.py`
(Overpass), `scripts/enriquecer_geo.py` (demo CSV y MongoDB), endpoint
`/buscador`, pestaña Buscador, plist de launchd para correr el scraper los
domingos.

**No entra:** API de Mercado Libre, sitios nuevos, tiempo de viaje real en
transporte (solo distancia), sombra de cerros, alertas.

## Decisiones

- **El puntaje se calcula en el navegador.** El backend entrega candidatos con
  sus métricas; la persona mueve los pesos sin volver a pedir datos.
- **Sin dependencias nuevas en el backend.** El cálculo geométrico es simple y
  cabe en Python puro (coordenadas locales en metros).
- **Subpuntajes de 0 a 1, explicables:** cercanía = 1 hasta 300 m y baja
  lineal hasta 0 a 1,5 km; precio = según diferencia con la mediana de su
  comuna (−20 % o menos → 1, +20 % o más → 0); sol = horas / horas de luz del
  día.
- **Paradas de bus quedan fuera:** están en todas las cuadras y la distancia no
  distingue nada. Transporte = estaciones de Biotren y terminales.

## Riesgos

1. No tengo acceso a Overpass desde mi entorno: la descarga corre en el Mac de
   John y la revisión visual se hace en su Chrome.
2. La cobertura de alturas en OSM puede ser baja fuera del centro: por eso el
   indicador de calidad es parte del resultado, no un detalle.
3. El archivo de edificios del Gran Concepción puede pesar decenas de MB: se
   guarda fuera de git; en el repo quedan solo los resultados por aviso.
4. Los datos reales siguen sin validar (`scripts/resumen.py`).

## Registro de construcción

**2026-09-22 · construido y publicado** (repo renombrado a `barrio-justo`, demo en jvsharp.github.io/barrio-justo)

- `sol.py` (NOAA + horizonte por azimut) y `geo.py` (índice en grilla, cercanía, sol por piso). Sin dependencias nuevas.
- `descargar_osm.py` con caché por tesela, reanudable, 3 servidores Overpass y solo teselas con avisos (121 → 46). Lugares de interés reales descargados completos; edificios reales pendientes (Overpass saturado).
- Demo: cercanía con lugares reales de OSM; sol calculado sobre una ciudad ficticia (`generar_edificios_demo.py`) y rotulado así en la interfaz (`sol_fuente = "demo"`).
- Buscador: filtros duros en backend (`/buscador`), puntaje en el navegador (`puntaje.js`, tests con `node:test`), mapa con resultados y lugares.
- Bugs encontrados en el camino: índice 360 en `horizonte()`; `sol_fuente` leído como número; la demo en Pages servía `datos.json` en caché tras un deploy (ahora lleva marca de build).
- Tests: 61 → 79 backend + 8 frontend.

