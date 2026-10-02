-- 09. Evolución mensual por grupo de modalidad
-- Pregunta: ¿cambia a lo largo del año el peso de la contratación directa
-- frente a la competitiva?
-- Técnica: participación dentro del mes (SUM OVER PARTITION BY mes), media
-- móvil de 3 meses (AVG OVER ROWS 2 PRECEDING) y LAG por grupo.
-- Resultado clave: la directa es la mayor parte del valor en 11 de 12 meses
-- (solo en julio la supera la competitiva). Su máximo es noviembre: 69,0 % del
-- valor del mes (13,2 billones, +75,2 %); en diciembre crece la competitiva.
-- Interpretación: las entidades adelantan la contratación directa antes de la
-- ley de garantías (8-nov-2025) y cierran el año con procesos competitivos.
WITH mensual AS (
    SELECT
        d.mes,
        m.grupo_modalidad,
        count(*) AS contratos,
        sum(f.valor_analisis) AS valor
    FROM fct_contratos AS f
    INNER JOIN dim_fecha AS d ON f.fecha_firma = d.fecha
    INNER JOIN dim_modalidad AS m USING (modalidad_key)
    WHERE m.grupo_modalidad IN ('Directa', 'Régimen especial', 'Competitiva')
    GROUP BY ALL
)

SELECT
    mes,
    grupo_modalidad,
    contratos,
    round(valor / 1e9, 1) AS valor_miles_millones,
    round(100 * valor / sum(valor) OVER (PARTITION BY mes), 1) AS pct_valor_del_mes,
    round(
        avg(valor) OVER (
            PARTITION BY grupo_modalidad ORDER BY mes ROWS 2 PRECEDING
        ) / 1e9,
        1
    ) AS media_movil_3m_miles_millones,
    round(
        100 * (valor / lag(valor) OVER (PARTITION BY grupo_modalidad ORDER BY mes) - 1),
        1
    ) AS var_vs_mes_anterior_pct
FROM mensual
ORDER BY mes, grupo_modalidad;
