import { test } from 'node:test';
import assert from 'node:assert/strict';
import { puntuar, rankear, subCercania, subPrecio, subSol } from './puntaje.js';

test('cercanía: completa hasta 300 m, cero desde 1,5 km, lineal entremedio', () => {
  assert.equal(subCercania(120), 1);
  assert.equal(subCercania(300), 1);
  assert.equal(subCercania(900), 0.5);
  assert.equal(subCercania(2000), 0);
  assert.equal(subCercania(null), null);
});

test('precio: −20 % → 1, mediana → 0,5, +20 % → 0', () => {
  assert.equal(subPrecio(-20), 1);
  assert.equal(subPrecio(0), 0.5);
  assert.equal(subPrecio(35), 0);
});

test('sol: horas sobre horas de luz', () => {
  assert.equal(subSol(4.75, 9.5), 0.5);
  assert.equal(subSol(null, 9.5), null);
});

test('el total pondera por importancia', () => {
  const aviso = { posicion: { vs_mediana_pct: -20 }, dist_biotren: 2000 };
  // precio "mucho" (2) = 1, biotren "algo" (1) = 0 → (2·1 + 1·0) / 3
  const { total } = puntuar(aviso, { precio: 2, cerca: { biotren: 1 } });
  assert.ok(Math.abs(total - 2 / 3) < 1e-9);
});

test('un dato que falta es neutro, no cero', () => {
  const { total, partes } = puntuar({}, { sol: 1 }, 'p6');
  assert.equal(total, 0.5);
  assert.equal(partes[0].valor, null);
});

test('el piso elegido cambia el sol que se usa', () => {
  const a = { sol_calle: 0, sol_p10: 9.5, sol_horas_luz: 9.5 };
  assert.equal(puntuar(a, { sol: 1 }, 'calle').total, 0);
  assert.equal(puntuar(a, { sol: 1 }, 'p10').total, 1);
});

test('sin pesos, ordena por precio', () => {
  const r = rankear([{ precio_uf: 5000 }, { precio_uf: 3000 }], {}, 'calle');
  assert.deepEqual(r.map((x) => x.aviso.precio_uf), [3000, 5000]);
});

test('con pesos, ordena por puntaje', () => {
  const cerca = { dist_parque: 100, precio_uf: 9000 };
  const lejos = { dist_parque: 3000, precio_uf: 1000 };
  const r = rankear([lejos, cerca], { cerca: { parque: 2 } }, 'calle');
  assert.equal(r[0].aviso, cerca);
});
