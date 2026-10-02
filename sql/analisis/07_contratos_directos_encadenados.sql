-- 07. Contratos directos encadenados con la misma empresa
-- Pregunta: ¿qué parejas entidad–empresa firman muchos contratos directos
-- seguidos, a menos de 30 días uno del otro? Es un patrón a revisar (puede
-- indicar fraccionamiento), no una prueba de irregularidad.
-- Técnica: LAG por pareja (PARTITION BY entidad, proveedor) y COUNT OVER ().
-- Solo personas jurídicas, para no exponer datos de personas naturales.
-- Resultado clave: 933 parejas tienen 3 o más contratos directos encadenados.
-- El top 20 son casi todos municipios antioqueños con su empresa de desarrollo
-- o entidad descentralizada; muchas parejas firman por última vez el 7-nov-2025.
-- Interpretación: domina el convenio interadministrativo, que se corta cuando
-- empieza la ley de garantías (4 meses antes de las legislativas del 8-mar-2026).
WITH directos AS (
    SELECT
        f.entidad_key,
        f.proveedor_key,
        f.id_contrato,
        f.fecha_firma,
        f.valor_analisis
    FROM fct_contratos AS f
    INNER JOIN dim_modalidad AS m USING (modalidad_key)
    INNER JOIN dim_proveedor AS p USING (proveedor_key)
    WHERE m.grupo_modalidad = 'Directa' AND p.tipo_persona = 'Jurídica'
),

secuencia AS (
    SELECT
        *,
        fecha_firma
        - lag(fecha_firma) OVER (
            PARTITION BY entidad_key, proveedor_key ORDER BY fecha_firma, id_contrato
        ) AS dias_desde_anterior
    FROM directos
),

parejas AS (
    SELECT
        entidad_key,
        proveedor_key,
        count(*) AS contratos,
        count(*) FILTER (WHERE dias_desde_anterior <= 30) AS seguidos_menos_30_dias,
        median(dias_desde_anterior) AS mediana_dias_entre_firmas,
        sum(valor_analisis) AS valor,
        min(fecha_firma) AS primera_firma,
        max(fecha_firma) AS ultima_firma
    FROM secuencia
    GROUP BY ALL
),

seleccion AS (
    SELECT
        *,
        count(*) OVER () AS parejas_que_cumplen,
        rank() OVER (ORDER BY seguidos_menos_30_dias DESC, valor DESC) AS puesto
    FROM parejas
    WHERE seguidos_menos_30_dias >= 3
)

SELECT
    s.puesto,
    e.nombre_entidad,
    p.nombre_proveedor,
    s.contratos,
    s.seguidos_menos_30_dias,
    s.mediana_dias_entre_firmas,
    round(s.valor / 1e6, 0) AS valor_millones,
    s.primera_firma,
    s.ultima_firma,
    s.parejas_que_cumplen
FROM seleccion AS s
INNER JOIN dim_entidad AS e USING (entidad_key)
INNER JOIN dim_proveedor AS p USING (proveedor_key)
WHERE s.puesto <= 20
ORDER BY s.puesto;
