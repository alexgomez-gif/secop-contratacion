-- Dimensión proveedor. Grano: documento normalizado (L2).
-- L3: un documento con varios nombres o tipos toma el más frecuente;
-- si empatan, el del contrato más reciente.
-- Clave -1: proveedor sin documento válido.
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
)

SELECT
    row_number() OVER (ORDER BY documento)::BIGINT AS proveedor_key,
    *
FROM proveedores
UNION ALL
SELECT -1, NULL, 'Sin identificar', NULL, 'Sin clasificar', 0;
