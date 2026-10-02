-- Staging de modificaciones publicadas a contratos.
-- Cada modificación (identificador_modificacion) pasa por varios estados
-- (en edición, enviada, publicada); la descarga ya trae solo "Publicado".
-- valor_modificacion es el VALOR TOTAL del contrato después de la
-- modificación, no el monto adicionado.
CREATE OR REPLACE TABLE stg_modificaciones AS
SELECT
    ":id" AS socrata_id,
    id_contrato,
    identificador_modificacion,
    TRY_CAST(version_anterior_del_contrato AS INTEGER) AS version_anterior,
    TRY_CAST(numero_version AS INTEGER) AS numero_version,
    TRY_CAST(valor_modificacion AS DECIMAL(24, 2)) AS valor_total_tras_modificacion,
    TRY_CAST(dias_extendidos AS INTEGER) AS dias_extendidos,
    TRY_CAST(fecha_creacion AS TIMESTAMP)::DATE AS fecha_creacion,
    TRY_CAST(fecha_de_aprobacion AS TIMESTAMP)::DATE AS fecha_aprobacion,
    nullif(trim(proposito_modificacion), 'No definido') AS proposito
FROM raw_modificaciones
-- Una fila por modificación: si hay varias publicadas, la última versión.
QUALIFY row_number() OVER (
    PARTITION BY id_contrato, identificador_modificacion
    ORDER BY numero_version DESC NULLS LAST, socrata_id
) = 1;
