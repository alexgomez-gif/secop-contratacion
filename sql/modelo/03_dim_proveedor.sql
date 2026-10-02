-- Dimensión proveedor. Grano: documento normalizado (L2).
-- L3: un documento con varios nombres o tipos toma el más frecuente;
-- si empatan, el del contrato más reciente.
-- Clave -1: proveedor sin documento válido.
-- max_contratos_simultaneos: solo personas naturales; el mayor número de
-- contratos de prestación de servicios vigentes el mismo día (barrido de
-- eventos, como en sql/analisis/10). Alimenta la página Alertas de Power BI.
CREATE OR REPLACE TABLE dim_proveedor AS
WITH conteos AS (
    SELECT
        documento_proveedor_norm,
        proveedor,
        tipo_doc_proveedor,
        tipo_persona,
        count(*) AS n,
        max(fecha_firma) AS ultima_firma
    FROM int_contratos
    WHERE documento_proveedor_norm IS NOT NULL
    GROUP BY ALL
),

proveedores AS (
    SELECT
        documento_proveedor_norm AS documento,
        arg_max(proveedor, (n, ultima_firma)) AS nombre_proveedor,
        arg_max(tipo_doc_proveedor, (n, ultima_firma)) AS tipo_documento,
        arg_max(tipo_persona, (n, ultima_firma)) AS tipo_persona,
        count(DISTINCT proveedor) AS nombres_distintos
    FROM conteos
    GROUP BY documento_proveedor_norm
),

servicios_pn AS (
    SELECT
        c.documento_proveedor_norm AS documento,
        c.fecha_inicio,
        c.fecha_fin
    FROM int_contratos AS c
    INNER JOIN proveedores AS p ON c.documento_proveedor_norm = p.documento
    WHERE
        p.tipo_persona = 'Natural'
        AND c.tipo_de_contrato = 'Prestación de servicios'
        AND c.estado_contrato NOT IN ('Cancelado', 'Borrador')
        AND c.fecha_inicio IS NOT NULL
        AND c.fecha_fin IS NOT NULL
        AND NOT coalesce(c.fechas_inconsistentes, FALSE)
),

eventos AS (
    SELECT documento, fecha_inicio AS fecha, 1 AS cambio FROM servicios_pn
    UNION ALL
    SELECT documento, fecha_fin + 1, -1 FROM servicios_pn
),

simultaneos AS (
    SELECT
        documento,
        max(vigentes)::INTEGER AS max_contratos_simultaneos
    FROM (
        SELECT
            documento,
            sum(cambio) OVER (
                PARTITION BY documento
                ORDER BY fecha, cambio
                ROWS UNBOUNDED PRECEDING
            ) AS vigentes
        FROM eventos
    )
    GROUP BY documento
)

SELECT
    row_number() OVER (ORDER BY p.documento)::BIGINT AS proveedor_key,
    p.*,
    s.max_contratos_simultaneos
FROM proveedores AS p
LEFT JOIN simultaneos AS s USING (documento)
UNION ALL
SELECT -1, NULL, 'Sin identificar', NULL, 'Sin clasificar', 0, NULL;
