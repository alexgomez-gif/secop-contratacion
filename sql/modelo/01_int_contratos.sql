-- Capa intermedia: aplica las reglas de limpieza L1–L9.
-- Cada regla está explicada en docs/decisiones_limpieza.md.
-- Grano: un contrato (id_contrato).

-- L5: primera letra en mayúscula ("terminado" -> "Terminado").
CREATE OR REPLACE MACRO capitalizar(x) AS upper(x[1]) || x[2:];

-- L3: nombres de proveedor en mayúsculas y con espacios simples.
CREATE OR REPLACE MACRO limpiar_nombre(x) AS
    nullif(upper(regexp_replace(trim(x), '\s+', ' ', 'g')), '');

-- L2: documento solo con dígitos: sin puntos, espacios, símbolos sueltos
-- (| * , ; ' "), dígito de verificación ("-7") ni ceros a la izquierda.
-- Si quedan letras u otros símbolos (nombres, fechas como 04/09/1980) o
-- menos de 5 dígitos ("0", "000000"), el documento no es válido.
CREATE OR REPLACE MACRO documento_base(doc) AS
    ltrim(
        regexp_replace(regexp_replace(doc, '[.\s|*,;''"]', '', 'g'), '-\d?$', ''),
        '0'
    );

-- L8: fechas fuera de [2000-01-01, 2060-12-31] son errores de captura
-- (1899-12-31 es la "fecha cero" de Excel; hay fines en el año 5025).
CREATE OR REPLACE MACRO fecha_valida(f) AS
    CASE WHEN f BETWEEN DATE '2000-01-01' AND DATE '2060-12-31' THEN f END;

CREATE OR REPLACE MACRO normalizar_documento(doc) AS
    CASE
        WHEN regexp_full_match(documento_base(doc), '[0-9]{5,15}')
            THEN documento_base(doc)
    END;

CREATE OR REPLACE TABLE int_contratos AS
WITH
-- L1: filas duplicadas. Se conserva una por id_contrato: la de
-- actualización más reciente y, si empatan, la de menor :id (estable).
dedup AS (
    SELECT *
    FROM stg_contratos
    QUALIFY row_number() OVER (
        PARTITION BY id_contrato
        ORDER BY ultima_actualizacion DESC NULLS LAST, socrata_id
    ) = 1
),

normalizado AS (
    SELECT
        * REPLACE (
            capitalizar(estado_contrato) AS estado_contrato,
            capitalizar(sector) AS sector,
            limpiar_nombre(proveedor) AS proveedor,
            fecha_valida(fecha_inicio) AS fecha_inicio,
            fecha_valida(fecha_fin) AS fecha_fin
        ),
        (fecha_inicio IS NOT NULL AND fecha_valida(fecha_inicio) IS NULL)
            OR (fecha_fin IS NOT NULL AND fecha_valida(fecha_fin) IS NULL)
            AS fecha_fuera_de_rango,
        TRY_CAST(codigo_entidad AS BIGINT) AS entidad_key,
        normalizar_documento(documento_proveedor) AS documento_proveedor_norm,
        -- L6: tipo de persona según el tipo de documento.
        CASE
            WHEN tipo_doc_proveedor = 'NIT' THEN 'Jurídica'
            WHEN tipo_doc_proveedor IN (
                'Cédula de Ciudadanía', 'Cédula de Extranjería',
                'Tarjeta de Identidad', 'Pasaporte', 'Registro Civil',
                'Permiso por Protección Temporal',
                'Permiso especial de permanencia'
            ) THEN 'Natural'
            ELSE 'Sin clasificar'
        END AS tipo_persona
    FROM dedup
)

SELECT
    *,
    -- L7: valores que no se usan en métricas de valor. La fila se conserva
    -- (cuenta como contrato), pero valor_analisis queda en NULL.
    CASE
        WHEN valor_contrato IS NULL THEN 'Sin valor'
        WHEN valor_contrato <= 0 THEN 'Valor cero o negativo'
        WHEN valor_contrato >= 1e14 THEN 'Valor imposible (>= 100 billones)'
        WHEN tipo_persona = 'Natural'
            AND tipo_de_contrato = 'Prestación de servicios'
            AND valor_contrato > 1e9
            THEN 'Persona natural en servicios > 1.000 M'
    END AS motivo_valor_excluido,
    -- L8: fin antes del inicio. Se conservan, pero no se calcula duración.
    fecha_fin < fecha_inicio AS fechas_inconsistentes
FROM normalizado;
