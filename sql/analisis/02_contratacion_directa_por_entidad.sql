-- 02. Contratación directa por entidad
-- Pregunta: ¿qué entidades mueven más dinero por contratación directa y qué
-- porcentaje de su contratación es directa frente a entidades de su mismo orden?
-- Técnica: FILTER, AVG por partición (orden) y PERCENT_RANK.
-- Solo entidades con al menos 100 contratos.
-- Resultado clave: de 1.449 entidades, Medellín (6,1 billones, 79,8 % de su
-- valor por directa) y MinMinas (5,8 billones, 99,3 %) encabezan; 16 de las 20
-- primeras superan en más de 20 pp el promedio de su orden.
-- Interpretación: en las entidades que más mueven, la directa es la norma y no
-- la excepción; muchos contratos directos no implican mucho valor (Barranquilla:
-- 98 % de sus contratos, 45 % de su valor).
WITH por_entidad AS (
    SELECT
        e.entidad_key,
        e.nombre_entidad,
        e.departamento,
        e.orden,
        count(*) AS contratos,
        count(*) FILTER (WHERE m.grupo_modalidad = 'Directa') AS contratos_directa,
        sum(f.valor_analisis) AS valor,
        coalesce(
            sum(f.valor_analisis) FILTER (WHERE m.grupo_modalidad = 'Directa'), 0
        ) AS valor_directa
    FROM fct_contratos AS f
    INNER JOIN dim_entidad AS e USING (entidad_key)
    INNER JOIN dim_modalidad AS m USING (modalidad_key)
    GROUP BY ALL
),

indicadores AS (
    SELECT
        *,
        contratos_directa / contratos AS pct_contratos_directa,
        valor_directa / nullif(valor, 0) AS pct_valor_directa
    FROM por_entidad
    WHERE contratos >= 100
),

comparado AS (
    SELECT
        *,
        avg(pct_valor_directa) OVER (PARTITION BY orden) AS promedio_orden,
        percent_rank() OVER (ORDER BY pct_valor_directa) AS percentil,
        rank() OVER (ORDER BY valor_directa DESC) AS puesto,
        count(*) OVER () AS entidades_analizadas
    FROM indicadores
)

SELECT
    puesto,
    nombre_entidad,
    departamento,
    orden,
    contratos,
    round(valor_directa / 1e9, 1) AS valor_directa_miles_millones,
    round(100 * pct_valor_directa, 1) AS pct_valor_directa,
    round(100 * pct_contratos_directa, 1) AS pct_contratos_directa,
    round(100 * (pct_valor_directa - promedio_orden), 1) AS dif_vs_promedio_orden_pp,
    round(100 * percentil) AS percentil_pct_directa,
    entidades_analizadas
FROM comparado
WHERE puesto <= 20
ORDER BY puesto;
