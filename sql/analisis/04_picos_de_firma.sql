-- 04. Picos de firma a lo largo del año
-- Pregunta: ¿se concentra la firma de contratos en algunos meses, en
-- particular a fin de año?
-- Técnica: índice frente al promedio mensual (AVG OVER ()), LAG para la
-- variación frente al mes anterior y RANK.
-- Índice 1,00 = mes promedio; 2,00 = el doble del promedio.
-- Resultado clave: diciembre es el mes con menos contratos (50.299, índice
-- 0,57) pero con más valor (27,4 billones, índice 1,85); enero y febrero
-- concentran el número de contratos (índices 1,72 y 1,89).
-- Interpretación: hay dos picos distintos: muchos contratos pequeños al
-- arrancar el año y pocos contratos grandes antes del cierre de la vigencia.
WITH mensual AS (
    SELECT
        d.mes,
        d.nombre_mes,
        count(*) AS contratos,
        sum(f.valor_analisis) AS valor,
        count(*) FILTER (WHERE d.dia >= 15) AS contratos_segunda_quincena
    FROM fct_contratos AS f
    INNER JOIN dim_fecha AS d ON f.fecha_firma = d.fecha
    GROUP BY ALL
)

SELECT
    mes,
    nombre_mes,
    contratos,
    round(valor / 1e9, 1) AS valor_miles_millones,
    round(contratos / avg(contratos) OVER (), 2) AS indice_contratos,
    round(valor / avg(valor) OVER (), 2) AS indice_valor,
    round(100 * (contratos / lag(contratos) OVER (ORDER BY mes) - 1), 1)
        AS var_contratos_vs_mes_anterior_pct,
    round(100 * contratos_segunda_quincena / contratos, 1) AS pct_segunda_quincena,
    rank() OVER (ORDER BY valor DESC) AS puesto_por_valor
FROM mensual
ORDER BY mes;
