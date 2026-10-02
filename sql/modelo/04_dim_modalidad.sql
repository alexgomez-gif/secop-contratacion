-- Dimensión modalidad de contratación. Grano: modalidad.
-- grupo_modalidad responde la pregunta de negocio (¿cuánto es directo?):
--   Directa          sin competencia (Ley 1150 de 2007, art. 2 num. 4)
--   Régimen especial entidades con reglas propias (ESE, universidades,
--                    empresas industriales y comerciales del Estado)
--   Competitiva      licitación, selección abreviada, concurso, mínima cuantía
--   Enajenación      venta de bienes del Estado (no es compra)
CREATE OR REPLACE TABLE dim_modalidad AS
WITH modalidades AS (
    SELECT DISTINCT modalidad_de_contratacion AS modalidad
    FROM int_contratos
    WHERE modalidad_de_contratacion IS NOT NULL
)

SELECT
    row_number() OVER (ORDER BY modalidad)::INTEGER AS modalidad_key,
    modalidad,
    CASE
        WHEN modalidad ILIKE 'Contratación directa%' THEN 'Directa'
        WHEN modalidad ILIKE 'Contratación régimen especial%' THEN 'Régimen especial'
        WHEN modalidad ILIKE 'Enajenación%' THEN 'Enajenación'
        ELSE 'Competitiva'
    END AS grupo_modalidad,
    modalidad ILIKE '%con ofertas%' AS con_ofertas
FROM modalidades
UNION ALL
SELECT -1, 'Sin información', 'Sin información', FALSE;
