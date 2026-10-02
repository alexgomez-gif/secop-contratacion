-- Dimensión fecha (calendario). Grano: un día.
-- Cubre años completos desde la fecha más antigua del modelo hasta la más
-- lejana. Las fechas ya vienen acotadas a 2000–2060 por la regla L8.
-- Se usa en tres roles: fecha de firma, de inicio y de fin.
-- en_periodo_analisis: años con contratos firmados. Power BI filtra el
-- informe por esta columna para que la inteligencia de tiempo (acumulado del
-- año, mes anterior) no se evalúe sobre años vacíos del calendario.
CREATE OR REPLACE TABLE dim_fecha AS
WITH rango AS (
    SELECT
        date_trunc(
            'year', least(min(fecha_firma), min(fecha_inicio), min(fecha_fin))
        )::DATE AS desde,
        (
            date_trunc(
                'year', greatest(max(fecha_firma), max(fecha_inicio), max(fecha_fin))
            )
            + INTERVAL 1 YEAR - INTERVAL 1 DAY
        )::DATE AS hasta,
        year(min(fecha_firma)) AS primer_anio_firma,
        year(max(fecha_firma)) AS ultimo_anio_firma
    FROM int_contratos
),

dias AS (
    SELECT
        unnest(generate_series(desde, hasta, INTERVAL 1 DAY))::DATE AS fecha,
        primer_anio_firma,
        ultimo_anio_firma
    FROM rango
)

SELECT
    fecha,
    year(fecha) AS anio,
    quarter(fecha) AS trimestre,
    month(fecha) AS mes,
    [
        'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio',
        'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
    ][month(fecha)] AS nombre_mes,
    strftime(fecha, '%Y-%m') AS anio_mes,
    day(fecha) AS dia,
    isodow(fecha) AS dia_semana,
    ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'][
        isodow(fecha)
    ] AS nombre_dia,
    isodow(fecha) >= 6 AS es_fin_de_semana,
    weekofyear(fecha) AS semana_iso,
    coalesce(year(fecha) BETWEEN primer_anio_firma AND ultimo_anio_firma, FALSE)
        AS en_periodo_analisis
FROM dias;
