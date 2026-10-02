# Decisiones de limpieza

Datos: SECOP II Contratos Electrónicos, contratos firmados en 2025
(1.050.953 filas descargadas el 2026-10-01). Las cifras de impacto son de
esa descarga y se recalculan con `python -m proyecto.modelo`.

Principio general: **no se borra información salvo duplicados exactos**.
Un dato dudoso se marca y se excluye solo de la métrica que distorsiona,
de modo que cada contrato sigue contando y el filtro se puede revertir en
Power BI.

## Resumen

| Regla | Problema | Decisión | Contratos afectados |
|---|---|---|---|
| L1 | Filas duplicadas | Conservar una por `id_contrato` | 96 filas eliminadas |
| L2 | Documento de proveedor con formatos distintos | Normalizar a solo dígitos; inválidos a "Sin identificar" | 2.251 reescritos, 2.609 sin identificar |
| L3 | Un proveedor con varios nombres | Nombre más frecuente, en mayúsculas | 471 proveedores |
| L4 | "No Definido" como texto | Convertir en nulo | 21.008 sin departamento, 2.250 sin documento |
| L5 | Mayúsculas inconsistentes | Primera letra en mayúscula | 150.290 estados, 101.162 sectores |
| L6 | No hay tipo de persona | Derivarlo del tipo de documento | 588.304 proveedores |
| L7 | Valores imposibles o atípicos | Excluir de métricas de valor (`valor_analisis` nulo) | 7.024 (0,67 %) |
| L8 | Fechas imposibles o incoherentes | Nulo fuera de 2000–2060; sin duración si fin < inicio | 14 y 599 |
| L9 | Una entidad con varios nombres o ubicaciones | Datos del contrato más reciente | 26 entidades |

## Detalle

### L1 · Duplicados exactos

**Evidencia.** 96 valores de `id_contrato` aparecen dos veces. Las dos
filas son idénticas en las 95 columnas; solo cambia el `:id` interno de
la plataforma.

**Decisión.** Conservar una fila por `id_contrato`: la de
`ultima_actualizacion` más reciente y, si empatan, la de menor `:id`
(para que el resultado sea siempre el mismo).

**Alternativa descartada.** Deduplicar por todas las columnas: daría el
mismo resultado hoy, pero no protege si en una descarga futura dos
versiones del mismo contrato difieren en algún campo.

**Dónde.** `sql/modelo/01_int_contratos.sql` (CTE `dedup`).

### L2 · Documento del proveedor

**Evidencia.** El mismo número aparece escrito de muchas formas:
`13.853.963`, `1088249252.`, `32738740-`, `900123456-7` (NIT con dígito de
verificación), `|1044429284`, `1083023992*`. Hay además textos que no son
documentos: nombres, fechas (`04/09/1980`), `N/A`, `0`, `000000000`.

**Decisión.**
1. Quitar puntos, espacios y los símbolos `| * , ; ' "`.
2. Quitar un dígito de verificación final (`-7`) o un guion suelto.
3. Quitar ceros a la izquierda.
4. Si el resultado no son entre 5 y 15 dígitos, el documento es inválido.

Los contratos con documento vacío o inválido se asignan al proveedor
`-1` "Sin identificar": siguen contando en totales, pero no en rankings
de proveedores.

**Impacto.** 2.251 documentos reescritos; 359 inválidos + 2.250 vacíos =
2.609 contratos sin proveedor identificado (0,25 %).

**Limitación conocida.** Un NIT escrito con el dígito de verificación
pegado (`8600024001` en lugar de `860002400`) no se puede distinguir de
otro número y queda como proveedor distinto.

### L3 · Nombre del proveedor

**Evidencia.** El mismo documento aparece con nombres distintos
("diana paola ferrereira rojas" / "DIANA PAOLA FERREREIRA ROJAS", razones
sociales con y sin "S.A.S.").

**Decisión.** Poner los nombres en mayúsculas con espacios simples y,
para cada documento, quedarse con el nombre más frecuente (desempate: el
del contrato más reciente). Igual con el tipo de documento.

**Impacto.** 471 proveedores tenían más de un nombre después de la
normalización; `dim_proveedor.nombres_distintos` lo registra.

### L4 · Nulos escritos como texto

**Evidencia.** La API reporta 0 % de nulos en columnas de texto porque
los vacíos vienen como "No Definido", "No definido" o "No Aplica".

**Decisión.** Convertirlos en nulos reales en la capa staging, para que
los conteos de faltantes sean ciertos.

**Impacto.** 21.008 contratos sin departamento ni ciudad, 2.250 sin
documento de proveedor.

**Dónde.** `sql/stg_contratos.sql` (macro `nulo_si_vacio`).

### L5 · Mayúsculas en categorías

**Evidencia.** Conviven "Cerrado" y "terminado", "Salud y Protección
Social" y "defensa", lo que crea categorías separadas en los gráficos.

**Decisión.** Primera letra en mayúscula en `estado_contrato` y `sector`.

**Impacto.** 150.290 estados ("terminado", "cedido") y 101.162 sectores
("deportes", "defensa", "agricultura", "interior").

### L6 · Tipo de persona del proveedor

**Evidencia.** No existe la columna, pero se necesita para separar
contratos con personas naturales (casi siempre prestación de servicios
personales) de los contratos con empresas.

**Decisión.** NIT → Jurídica; cédula, cédula de extranjería, tarjeta de
identidad, pasaporte, registro civil, PPT y PEP → Natural; "Otro" o vacío
→ Sin clasificar.

**Impacto.** 540.871 proveedores naturales, 46.757 jurídicos, 677 sin
clasificar.

### L7 · Valores fuera de métricas

**Evidencia.**
- 6.920 contratos con valor 0 o negativo.
- 1 contrato de prestación de servicios de apoyo por 944 billones de COP:
  por sí solo vale 5 veces la suma de los otros 1.043.845 contratos
  (183 billones) y casi el doble del Presupuesto General de la Nación de
  2025 (unos 511 billones).
- Contratos de prestación de servicios con personas naturales de más de
  1.000 millones de COP: la mediana de ese grupo es 19 millones y el
  percentil 99,9 es 245 millones. Casos revisados: un contrato de
  18.600 millones con 18,6 millones pagados (error de tres ceros) y un
  "médico general" por 120 días a 28.022 millones.
- Valores de exactamente 1.000 veces lo pagado (tres ceros de más): una
  persona natural con un suministro de 2.385.618 millones a la Gobernación
  de Boyacá, del que se pagaron 2.385,6 millones; 225.000 millones en
  carnes frías para la Agencia Logística con 225 millones pagados.
- Contratos que valen más de 10 veces todo lo demás que firmó la entidad en
  el año y casi no tienen pagos: 998.000 millones para "adecuar una cancha
  de fútbol" en Sitionuevo (el resto de su contratación suma 38.500
  millones); 92.400 millones en seguros para el municipio de Ansermanuevo.
  Se detectaron al revisar los resultados de las consultas 01 y 05.

**Decisión.** El contrato se conserva y cuenta en número de contratos,
pero su `valor_analisis` queda nulo y `motivo_valor_excluido` explica por
qué. `valor_contrato` mantiene el dato original.

| Motivo | Contratos | Valor original excluido |
|---|---|---|
| Valor cero o negativo | 6.920 | 0 |
| Valor imposible (>= 100 billones) | 1 | 944,19 billones |
| Persona natural en servicios > 1.000 M | 91 | 0,97 billones |
| Error de tres ceros (valor = 1.000 x pagado) | 3 | 2,79 billones |
| Desproporcionado para la entidad | 9 | 2,52 billones |

Las reglas se evalúan en ese orden y cada contrato recibe el primer motivo
que cumple. "Desproporcionado" se calcula contra los demás contratos que
quedan después de las reglas anteriores.

**Por qué estos umbrales.** 100 billones es una cota física: ningún
contrato individual puede valer una quinta parte del presupuesto
nacional. 1.000 millones para servicios de personas naturales es unas 4
veces el percentil 99,9 del grupo; deja fuera errores claros y conserva
casos legítimos altos. Contratos grandes con empresas (por ejemplo,
3,3 billones de la Registraduría por una "solución integral") son plausibles y se
conservan.

"Error de tres ceros" exige que el cociente valor / pagado esté entre 999 y
1.001: una coincidencia así no ocurre por azar. "Desproporcionado" exige
tres condiciones a la vez (al menos 50.000 millones, más de 10 veces el
resto de la entidad y menos del 10 % pagado). El pago es la salvaguarda:
un contrato grande que sí se pagó, como 409.000 millones de servicios de
salud de la Dirección de Sanidad Militar, se conserva aunque supere 28
veces el resto de esa entidad.

**Limitación conocida.** Un error de digitación en un contrato con una
empresa que no cumpla ninguna de estas condiciones no se detecta. El valor
que queda en métricas es 177,6 billones de COP.

### L8 · Fechas

**Evidencia.** 5 contratos con inicio en 1899 (la "fecha cero" de Excel),
4 con fin anterior a 2000, 5 con fin después de 2060 (hasta el año 5025)
y 599 con fin anterior al inicio.

**Decisión.**
- Fechas de inicio o fin fuera de [2000-01-01, 2060-12-31] → nulas, con
  `fecha_fuera_de_rango = true` (14 contratos).
- Fin anterior al inicio → se conservan las fechas, `fechas_inconsistentes
  = true` y `duracion_dias` queda nula (599 contratos).
- La fecha de firma no se toca: es el filtro de la descarga y está
  completa.

### L9 · Atributos de la entidad

**Evidencia.** `codigo_entidad` es único y siempre tiene el mismo NIT,
pero 26 entidades aparecen con más de un nombre (cambios de nombre,
abreviaturas) y 7 con más de una ubicación o sector.

**Decisión.** La entidad se identifica por `codigo_entidad` (no por NIT:
un NIT agrupa varias unidades, 3.433 NIT para 4.067 códigos). Cada
atributo toma el valor del contrato firmado más reciente, ignorando
nulos. Así, si un contrato trae el departamento vacío, se usa el de otro
contrato de la misma entidad.

**Impacto.** 406 entidades siguen sin departamento ("Sin información"):
ninguno de sus contratos lo informa.

## Lo que no se limpió (todavía)

- `objeto_del_contrato` es texto libre; no se clasifica.
- No se cruzan proveedores con el RUES para unificar empresas del mismo grupo.
- Las ciudades con y sin tilde ("Paez" / "Páez") existen en
  departamentos distintos y no se unifican.
