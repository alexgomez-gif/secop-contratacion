-- 06. Departamentos frente al promedio nacional
-- Pregunta: ¿qué departamentos contratan más por vía directa que el promedio
-- del país?
-- Técnica: participación y diferencia frente al total con SUM OVER (), RANK.
-- Nota: el departamento es el de la entidad. Bogotá incluye a las entidades
-- nacionales con sede allí.
-- Resultado clave: en el país, el 51,6 % del valor va por directa. Antioquia
-- lidera con 71,7 % (+20,1 pp) y Valle sigue con 58,9 %; Chocó (18,9 %) y Cesar
-- (22,9 %) son los más bajos. 25 de los 33 departamentos están bajo el promedio.
-- Interpretación: el promedio nacional casi coincide con Bogotá (42 % del valor)
-- y Antioquia lo sube; en la mayoría de departamentos la directa pesa menos.
WITH por_departamento AS (
    SELECT
        e.departamento,
        count(*) AS contratos,
        count(DISTINCT f.entidad_key) AS entidades,
        sum(f.valor_analisis) AS valor,
        coalesce(
            sum(f.valor_analisis) FILTER (WHERE m.grupo_modalidad = 'Directa'), 0
        ) AS valor_directa
    FROM fct_contratos AS f
    INNER JOIN dim_entidad AS e USING (entidad_key)
    INNER JOIN dim_modalidad AS m USING (modalidad_key)
    GROUP BY ALL
)

SELECT
    departamento,
    entidades,
    contratos,
    round(valor / 1e9, 1) AS valor_miles_millones,
    round(100 * valor / sum(valor) OVER (), 1) AS pct_valor_nacional,
    round(100 * valor_directa / valor, 1) AS pct_valor_directa,
    round(
        100 * (valor_directa / valor - sum(valor_directa) OVER () / sum(valor) OVER ()),
        1
    ) AS dif_vs_nacional_pp,
    rank() OVER (ORDER BY valor_directa / valor DESC) AS puesto_pct_directa
FROM por_departamento
ORDER BY valor DESC;
