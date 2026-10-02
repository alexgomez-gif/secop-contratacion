-- 10. Personas naturales con contratos de servicios simultáneos
-- Pregunta: ¿cuántas personas tienen dos o más contratos de prestación de
-- servicios vigentes al mismo tiempo, y con cuántas entidades?
-- Técnica: barrido de eventos. Cada contrato suma 1 el día que inicia y
-- resta 1 el día después de terminar; la SUM acumulada por persona
-- (ventana ordenada por fecha) da cuántos contratos tiene vigentes cada día.
-- Resultado agregado, sin nombres (son personas naturales).
-- Resultado clave: de 520.424 personas, 57.326 (11,0 %) tuvieron 2 o más
-- contratos simultáneos, casi siempre con entidades distintas; 1.546 llegaron
-- a 4 o más y 445 a 5 o más.
-- Interpretación: dos contratos a la vez es común; con 4 o más vale la pena
-- verificar dedicación y cumplimiento de obligaciones.
WITH contratos_pn AS (
    SELECT
        f.proveedor_key,
        f.entidad_key,
        f.fecha_inicio,
        f.fecha_fin
    FROM fct_contratos AS f
    INNER JOIN dim_proveedor AS p USING (proveedor_key)
    WHERE
        p.tipo_persona = 'Natural'
        AND f.tipo_de_contrato = 'Prestación de servicios'
        AND f.estado_contrato NOT IN ('Cancelado', 'Borrador')
        AND f.fecha_inicio IS NOT NULL
        AND f.fecha_fin IS NOT NULL
        AND NOT f.fechas_inconsistentes
),

eventos AS (
    SELECT proveedor_key, fecha_inicio AS fecha, 1 AS cambio FROM contratos_pn
    UNION ALL
    SELECT proveedor_key, fecha_fin + 1, -1 FROM contratos_pn
),

vigentes AS (
    SELECT
        proveedor_key,
        sum(cambio) OVER (
            PARTITION BY proveedor_key
            ORDER BY fecha, cambio
            ROWS UNBOUNDED PRECEDING
        ) AS contratos_vigentes
    FROM eventos
),

por_persona AS (
    SELECT
        v.proveedor_key,
        max(v.contratos_vigentes) AS max_simultaneos,
        any_value(c.entidades) AS entidades
    FROM vigentes AS v
    INNER JOIN (
        SELECT proveedor_key, count(DISTINCT entidad_key) AS entidades
        FROM contratos_pn
        GROUP BY proveedor_key
    ) AS c USING (proveedor_key)
    GROUP BY v.proveedor_key
)

SELECT
    CASE WHEN max_simultaneos >= 5 THEN '5 o más' ELSE max_simultaneos::VARCHAR END
        AS max_contratos_simultaneos,
    count(*) AS personas,
    round(100 * count(*) / sum(count(*)) OVER (), 2) AS pct_personas,
    count(*) FILTER (WHERE entidades >= 2) AS personas_con_2_o_mas_entidades,
    round(avg(entidades), 2) AS entidades_promedio
FROM por_persona
GROUP BY 1
ORDER BY min(max_simultaneos);
