-- 01. Concentración en los 10 mayores proveedores
-- Pregunta: ¿qué parte del valor contratado se llevan los 10 proveedores más grandes?
-- Técnica: RANK y SUM acumulada (ventana con ROWS UNBOUNDED PRECEDING).
-- Los nombres de personas naturales se ocultan.
-- Resultado clave: los 10 mayores proveedores, de 585.950, suman el 12,2 % del
-- valor (20,0 billones). Los 3 primeros son contratos únicos (Gecelca, UT
-- logística electoral 2026, Zona Franca Barranquilla) y ya suman el 6,3 %.
-- Interpretación: a escala nacional la concentración es baja y la arrastran
-- pocos contratos gigantes; la concentración relevante se mide por entidad (05).
WITH por_proveedor AS (
    SELECT
        p.proveedor_key,
        CASE
            WHEN p.tipo_persona = 'Natural' THEN '(persona natural)'
            ELSE p.nombre_proveedor
        END AS nombre_proveedor,
        p.tipo_persona,
        count(*) AS contratos,
        count(DISTINCT f.entidad_key) AS entidades,
        sum(f.valor_analisis) AS valor
    FROM fct_contratos AS f
    INNER JOIN dim_proveedor AS p USING (proveedor_key)
    WHERE f.proveedor_key <> -1
    GROUP BY ALL
    HAVING sum(f.valor_analisis) IS NOT NULL
),

ranking AS (
    SELECT
        *,
        rank() OVER (ORDER BY valor DESC) AS puesto,
        valor / sum(valor) OVER () AS pct_valor,
        sum(valor) OVER (ORDER BY valor DESC ROWS UNBOUNDED PRECEDING)
        / sum(valor) OVER () AS pct_acumulado,
        count(*) OVER () AS total_proveedores
    FROM por_proveedor
)

SELECT
    puesto,
    nombre_proveedor,
    tipo_persona,
    contratos,
    entidades,
    round(valor / 1e9, 1) AS valor_miles_millones,
    round(100 * pct_valor, 2) AS pct_valor,
    round(100 * pct_acumulado, 2) AS pct_acumulado,
    total_proveedores
FROM ranking
WHERE puesto <= 10
ORDER BY puesto;
