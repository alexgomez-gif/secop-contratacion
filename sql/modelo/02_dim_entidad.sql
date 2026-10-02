-- Dimensión entidad contratante. Grano: codigo_entidad.
-- L9: si una entidad aparece con nombres o ubicaciones distintas, se toma
-- el valor del contrato firmado más reciente (sin contar nulos).
CREATE OR REPLACE TABLE dim_entidad AS
SELECT
    entidad_key,
    arg_max(nombre_entidad, fecha_firma) AS nombre_entidad,
    arg_max(nit_entidad, fecha_firma) AS nit_entidad,
    coalesce(
        arg_max(departamento, fecha_firma) FILTER (departamento IS NOT NULL),
        'Sin información'
    ) AS departamento,
    coalesce(
        arg_max(ciudad, fecha_firma) FILTER (ciudad IS NOT NULL),
        'Sin información'
    ) AS ciudad,
    coalesce(arg_max(orden, fecha_firma) FILTER (orden IS NOT NULL), 'Sin información')
        AS orden,
    coalesce(arg_max(rama, fecha_firma) FILTER (rama IS NOT NULL), 'Sin información')
        AS rama,
    coalesce(arg_max(sector, fecha_firma) FILTER (sector IS NOT NULL), 'Sin información')
        AS sector,
    arg_max(entidad_centralizada, fecha_firma) AS entidad_centralizada,
    count(DISTINCT nombre_entidad) AS nombres_distintos
FROM int_contratos
GROUP BY entidad_key;
