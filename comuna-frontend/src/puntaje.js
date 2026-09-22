// Puntaje del buscador. Funciones puras: se prueban con `npm test` (node:test).
//
// Cada criterio da un subpuntaje de 0 a 1 que se puede explicar en una frase.
// El total es el promedio ponderado por lo que la persona dijo que le importa.
// Un dato que falta vale 0,5 (neutro): no premia ni castiga no saber.

export const PISOS = [
  { valor: 'calle', etiqueta: 'Calle' },
  { valor: 'p3', etiqueta: '3° piso' },
  { valor: 'p6', etiqueta: '6° piso' },
  { valor: 'p10', etiqueta: '10° piso' },
];

export const CERCANIA = [
  { clave: 'biotren', etiqueta: 'Biotren o terminal' },
  { clave: 'universidad', etiqueta: 'Universidad' },
  { clave: 'colegio', etiqueta: 'Colegio' },
  { clave: 'salud', etiqueta: 'Hospital o clínica' },
  { clave: 'supermercado', etiqueta: 'Supermercado' },
  { clave: 'parque', etiqueta: 'Parque o plaza' },
];

export const CERCA_M = 300; // hasta acá, puntaje completo
export const LEJOS_M = 1500; // desde acá, cero
const NEUTRO = 0.5;

const acotar = (v) => Math.max(0, Math.min(1, v));

export function subPrecio(vsMedianaPct) {
  if (vsMedianaPct == null) return null;
  return acotar((20 - vsMedianaPct) / 40); // −20 % o menos → 1 · +20 % o más → 0
}

export function subCercania(distM) {
  if (distM == null) return null;
  if (distM <= CERCA_M) return 1;
  return acotar(1 - (distM - CERCA_M) / (LEJOS_M - CERCA_M));
}

export function subSol(horas, horasLuz) {
  if (horas == null || !horasLuz) return null;
  return acotar(horas / horasLuz);
}

/**
 * pesos: { precio: 0|1|2, sol: 0|1|2, cerca: { biotren: 0|1|2, ... } }
 * Devuelve { total (0–1 o null si no hay pesos), partes: [{ clave, peso, valor, dato }] }.
 */
export function puntuar(aviso, pesos, piso = 'calle') {
  const partes = [];
  if (pesos.precio) {
    partes.push({ clave: 'precio', peso: pesos.precio, valor: subPrecio(aviso.posicion?.vs_mediana_pct) });
  }
  if (pesos.sol) {
    partes.push({ clave: 'sol', peso: pesos.sol, valor: subSol(aviso[`sol_${piso}`], aviso.sol_horas_luz) });
  }
  for (const { clave } of CERCANIA) {
    const peso = pesos.cerca?.[clave];
    if (peso) partes.push({ clave, peso, valor: subCercania(aviso[`dist_${clave}`]) });
  }
  const sumaPesos = partes.reduce((s, p) => s + p.peso, 0);
  if (!sumaPesos) return { total: null, partes };
  const total = partes.reduce((s, p) => s + p.peso * (p.valor ?? NEUTRO), 0) / sumaPesos;
  return { total, partes };
}

export function rankear(avisos, pesos, piso) {
  const puntuados = avisos.map((a) => ({ aviso: a, ...puntuar(a, pesos, piso) }));
  const hayPesos = puntuados.some((p) => p.total != null);
  return puntuados.sort((x, y) =>
    hayPesos ? y.total - x.total : (x.aviso.precio_uf ?? Infinity) - (y.aviso.precio_uf ?? Infinity),
  );
}
