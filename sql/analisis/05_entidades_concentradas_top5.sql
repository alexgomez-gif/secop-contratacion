-- 05. Entidades con la contratación concentrada en 5 proveedores
-- Pregunta: ¿qué entidades entregan más del 50 % de su valor a sus 5
-- principales proveedores, pese a contratar con al menos 20?
-- Técnica: ROW_NUMBER y SUM por partición (entidad).
-- No muestra nombres de proveedores: pueden ser personas naturales.
-- Resultado clave: 824 de las 1.988 entidades con 20 o más proveedores (41 %)
-- dan más del 50 % de su valor a sus 5 mayores. Entre las grandes: MinMinas
-- 89,4 % (72,0 % a uno solo), RNEC 95,4 % y MinCIT 98,7 %.
-- Interpretación: la concentración alta es frecuente y en las entidades
-- nacionales suele venir de un solo contrato enorme, que hay que leer con su objeto.
WITH entidad_proveedor AS (
    SELECT
        f.entidad_key,
        f.proveedor_key,
        p.tipo_persona,
        sum(f.valor_analisis) AS valor
    FROM fct_contratos AS f
    INNER JOIN dim_proveedor AS p USING (proveedor_key)
    WHERE f.proveedor_key <> -1 AND f.valor_analisis > 0
    GROUP BY ALL
),

posiciones AS (
    SELECT
        *,
        row_number() OVER (PARTITION BY entidad_key ORDER BY valor DESC) AS posicion,
        sum(valor) OVER (PARTITION BY entidad_key) AS valor_entidad,
        count(*) OVER (PARTITION BY entidad_key) AS proveedores
    FROM entidad_proveedor
),

concentracion AS (
    SELECT
        entidad_key,
        any_value(valor_entidad) AS valor_entidad,
        any_value(proveedores) AS proveedores,
        sum(valor) FILTER (WHERE posicion <= 5) / any_value(valor_entidad) AS pct_top5,
        max(valor) / any_value(valor_entidad) AS pct_top1,
        any_value(tipo_persona) FILTER (WHERE posicion = 1) AS tipo_persona_top1
    FROM posiciones
    GROUP BY entidad_key
),

seleccion AS (
    SELECT
        *,
        count(*) OVER () AS entidades_que_cumplen,
        rank() OVER (ORDER BY valor_entidad DESC) AS puesto
    FROM concentracion
    WHERE pct_top5 > 0.5 AND proveedores >= 20
)

SELECT
    s.puesto,
    e.nombre_entidad,
    e.departamento,
    e.orden,
    s.proveedores,
    round(s.valor_entidad / 1e9, 1) AS valor_miles_millones,
    round(100 * s.pct_top5, 1) AS pct_top5,
    round(100 * s.pct_top1, 1) AS pct_mayor_proveedor,
    s.tipo_persona_top1 AS tipo_mayor_proveedor,
    s.entidades_que_cumplen
FROM seleccion AS s
INNER JOIN dim_entidad AS e USING (entidad_key)
WHERE s.puesto <= 20
ORDER BY s.puesto;
