# PRD v3 — Comuna Dash: de "precios por comuna" a "¿este aviso está caro?"

**Estado:** aprobado por John para construir (2026-09-22, "haz el PRD y procede").
**Autor:** Claude, para John Sharp.

---

## 1. Problema

La v2 responde bien una pregunta agregada: cuánto cuesta el m² en cada comuna.
Pero quien mira un aviso concreto quiere saber otra cosa:

- **¿Este precio es normal para la zona, o está caro / barato?** Hoy hay que
  ir a la pestaña Mercado, buscar la comuna y comparar a ojo.
- **¿Conviene comprar para arrendar?** El dato existe (medianas de venta y de
  arriendo), pero nadie lo cruza.
- **¿Este aviso lleva mucho tiempo publicado o bajó de precio?** El scraper
  ya guarda la primera y la última fecha en que vio cada aviso, pero no el
  precio anterior.

Y para el portafolio, dos huecos:

- **No hay demo en vivo.** Para ver el proyecto hay que clonarlo e instalar
  Python y Node. La mayoría de quienes revisan un perfil no lo va a hacer.
- **No hay CI.** Los 39 tests existen, pero nada prueba que siguen pasando.

## 2. Criterios de éxito

| # | Criterio | Cómo se mide |
|---|---|---|
| 1 | Cada aviso muestra si su UF/m² está bajo, en rango o sobre el mercado de su comuna | Etiqueta en la tarjeta + filtro en Avisos; test sobre casos de borde |
| 2 | La vista Mercado muestra rentabilidad bruta estimada por comuna | Tabla con n mínimo por lado; test del cálculo |
| 3 | El scraper guarda el historial de precio de cada aviso | Test: un segundo guardado con otro precio agrega una entrada; con el mismo precio, no |
| 4 | La tarjeta muestra días publicado y cambio de precio | Visible en la demo |
| 5 | Demo en vivo en `jvsharp.github.io/comuna-dash` sin backend | Build estático pasa en CI; misma UI que la versión con API |
| 6 | CI corre tests, lint y build en cada push | Badge verde en el README |

## 3. Alcance

**Entra (esta ronda):**

1. **Posición de precio por aviso.** Referencia = p25, mediana y p75 de UF/m² de
   su grupo (comuna × operación × tipo), solo con avisos válidos y al menos 10
   con superficie. Si el grupo no llega a 10, la etiqueta es "sin referencia" en
   vez de inventar una.
2. **Rentabilidad bruta estimada** = (mediana arriendo UF/m² mensual × 12) /
   mediana venta UF/m², por comuna y tipo. Solo si ambos lados tienen n ≥ 10.
   Se presenta como estimación gruesa, con la fórmula a la vista.
3. **Historial de precio.** En cada guardado, si el precio cambió, se agrega
   `{fecha, precio_uf}` a `historial_precios`. La API calcula `dias_publicado` y
   `cambio_precio_pct`.
4. **Demo estática.** Un script exporta los datos de demo ya procesados a JSON
   y el frontend, en modo estático, filtra/ordena/pagina en el navegador. Se
   publica con GitHub Actions en Pages.
5. **CI** con GitHub Actions: pytest, eslint, build.

**Queda fuera (siguiente ronda, ver §7):** mapa, alertas, scraping programado,
más regiones, modelo de precio.

## 4. Restricciones

- **Nada de datos reales en la demo pública.** Pages publica solo la demo
  (precios ficticios). Los datos del scraper se quedan en tu MongoDB local.
- **Sin dependencias nuevas pesadas.** Todo con lo que ya está (FastAPI,
  React, Recharts). CI y Pages son gratis para repos públicos.
- **La API y el modo estático deben dar los mismos números.** El modo
  estático no recalcula estadística: consume lo que exportó el backend.
- **Mongo existente sigue funcionando.** Los avisos guardados antes de esta
  versión no tienen historial; la API los trata como "sin historial".

## 5. Plan

| Paso | Qué | Verificación |
|---|---|---|
| 1 | `analisis.py`: referencias por grupo, `posicion()`, `rentabilidad()` | Tests unitarios |
| 2 | `scrapers/base.py`: historial de precio en el upsert | Test con un Mongo simulado |
| 3 | API: campos nuevos en `/propiedades`, filtro `posicion`, endpoint `/rentabilidad` | Tests de API |
| 4 | Demo: historial sintético en ~15 % de los avisos | Se ve en tarjetas |
| 5 | Frontend: etiqueta y filtro de posición, historial en tarjeta, tabla de rentabilidad | Lint + build + capturas |
| 6 | `scripts/exportar_estatico.py` + adaptador estático en `api.js` | Build estático; mismas cifras que la API |
| 7 | `.github/workflows/ci.yml` y `pages.yml` | Corre en GitHub tras el push |
| 8 | README: link a la demo, badge CI, sección nueva | Revisión visual |

## 6. Preguntas abiertas / riesgos

1. **Validación con datos reales pendiente.** Todavía no vimos `scripts/resumen.py`
   con los 2.734 avisos reales. Si las reglas de limpieza no calzan (por ejemplo,
   si "proyecto nuevo" saca demasiados), la posición y la rentabilidad heredan el
   problema. **Hay que correrlo antes de confiar en los números.**
2. **La rentabilidad bruta ignora gastos,** contribuciones, vacancia y que los
   departamentos en arriendo y en venta no son los mismos. Se rotula como
   "estimación bruta" y el README lo explica.
3. **GitHub Pages requiere un paso tuyo:** Settings → Pages → Source: GitHub
   Actions. Sin eso el workflow corre pero no publica.
4. **La mediana por comuna mezcla barrios muy distintos** (centro de Concepción
   vs. Lomas de San Andrés). Con lat/long ya guardados se puede afinar por zona
   más adelante.

## 7. Ideas para después (no se construyen ahora)

| Idea | Valor | Costo | Nota |
|---|---|---|---|
| Mapa con los avisos (lat/long ya se guardan) | Alto, muy visual | Medio | Leaflet + OpenStreetMap; necesita coordenadas también en la demo |
| Referencia por barrio en vez de comuna | Alto | Medio | Agrupar por celdas de ~1 km con lat/long |
| Tiempo en el mercado por comuna | Medio | Bajo | Requiere varias corridas del scraper en el tiempo |
| Avisos que desaparecen (probable venta/arriendo) | Medio | Bajo | Avisos no vistos en la última corrida |
| Alertas ("avisame si aparece un depto bajo mercado en Penco") | Alto para uso propio | Medio | Implica correr el scraper programado: ojo con los términos del portal |
| Modelo de precio (regresión por m², dormitorios, comuna) | Alto para portafolio | Medio | Explica *por qué* un aviso está caro, no solo *que* lo está |

## 8. Registro de construcción

_(se completa a medida que se avanza)_

**2026-09-22 · construido**

- `analisis.py`: `referencias()`, `posicion()`, `rentabilidad()`, `historial()`, `enriquecer()`. Grupos con menos de 10 avisos con m² → "sin referencia".
- `scrapers/base.py`: historial de precio en el upsert (solo agrega si el precio cambió; siembra historial en avisos anteriores a v3). Colección inyectable para tests.
- API: `/propiedades` con `posicion`, `dias_publicado`, `cambio_precio_pct`, filtro `posicion` y orden `vs_mediana_asc`; nuevo `/rentabilidad`.
- Demo: ~15 % de los avisos con historial sintético (mayoría a la baja).
- Frontend: etiqueta de posición y línea de historial en la tarjeta; filtro "Precio vs. su comuna"; tabla de rentabilidad con la fórmula explicada.
- Modo estático: `scripts/exportar_estatico.py` (fuerza demo, aborta si no) + adaptador en `api.js`. **Paridad verificada: 25/25 combinaciones de filtro × orden dan el mismo total y el mismo orden en la página 2 que la API.**
- CI (`ci.yml`) y Pages (`pages.yml`).
- Tests: 39 → 55.

**Pendiente de John:** activar Pages (Settings → Pages → Source: GitHub Actions); regenerar capturas; correr `scripts/resumen.py` con los datos reales (riesgo #1).
