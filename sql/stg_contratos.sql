-- Capa staging: tipos correctos, nulos explícitos y nombres claros.
-- No elimina filas ni corrige valores atípicos: eso va en la capa de limpieza.
-- L4 (docs/decisiones_limpieza.md): textos que significan "sin dato" -> NULL.
CREATE OR REPLACE MACRO nulo_si_vacio(x) AS
    CASE
        WHEN trim(x) IN ('', 'No Definido', 'No definido', 'NO DEFINIDO', 'No Aplica')
            THEN NULL
        ELSE trim(x)
    END;

CREATE OR REPLACE TABLE stg_contratos AS
SELECT
    ":id" AS socrata_id,
    id_contrato,
    referencia_del_contrato,
    proceso_de_compra,
    -- Entidad
    nombre_entidad,
    nit_entidad,
    codigo_entidad,
    nulo_si_vacio(departamento) AS departamento,
    nulo_si_vacio(ciudad) AS ciudad,
    nulo_si_vacio(orden) AS orden,
    nulo_si_vacio(sector) AS sector,
    nulo_si_vacio(rama) AS rama,
    entidad_centralizada = 'Centralizada' AS entidad_centralizada,
    -- Contrato
    nulo_si_vacio(estado_contrato) AS estado_contrato,
    nulo_si_vacio(tipo_de_contrato) AS tipo_de_contrato,
    nulo_si_vacio(modalidad_de_contratacion) AS modalidad_de_contratacion,
    nulo_si_vacio(justificacion_modalidad_de) AS justificacion_modalidad,
    nulo_si_vacio(codigo_de_categoria_principal) AS codigo_categoria_unspsc,
    objeto_del_contrato,
    descripcion_del_proceso,
    nulo_si_vacio(duraci_n_del_contrato) AS duracion_texto,
    TRY_CAST(fecha_de_firma AS TIMESTAMP)::DATE AS fecha_firma,
    TRY_CAST(fecha_de_inicio_del_contrato AS TIMESTAMP)::DATE AS fecha_inicio,
    TRY_CAST(fecha_de_fin_del_contrato AS TIMESTAMP)::DATE AS fecha_fin,
    TRY_CAST(dias_adicionados AS INTEGER) AS dias_adicionados,
    -- Proveedor
    nulo_si_vacio(tipodocproveedor) AS tipo_doc_proveedor,
    nulo_si_vacio(documento_proveedor) AS documento_proveedor,
    nulo_si_vacio(proveedor_adjudicado) AS proveedor,
    es_grupo = 'Si' AS proveedor_es_grupo,
    es_pyme = 'Si' AS proveedor_es_pyme,
    -- Valores (COP)
    TRY_CAST(valor_del_contrato AS DECIMAL(24, 2)) AS valor_contrato,
    TRY_CAST(valor_pagado AS DECIMAL(24, 2)) AS valor_pagado,
    TRY_CAST(valor_facturado AS DECIMAL(24, 2)) AS valor_facturado,
    TRY_CAST(valor_pendiente_de_ejecucion AS DECIMAL(24, 2)) AS valor_pendiente_ejecucion,
    nulo_si_vacio(origen_de_los_recursos) AS origen_recursos,
    TRY_CAST(presupuesto_general_de_la_nacion_pgn AS DECIMAL(24, 2)) AS recursos_pgn,
    TRY_CAST(sistema_general_de_participaciones AS DECIMAL(24, 2)) AS recursos_sgp,
    TRY_CAST(sistema_general_de_regal_as AS DECIMAL(24, 2)) AS recursos_regalias,
    TRY_CAST(recursos_propios AS DECIMAL(24, 2)) AS recursos_propios,
    -- Enlace al proceso en SECOP
    coalesce(json_extract_string(urlproceso, '$.url'), urlproceso) AS url_proceso,
    TRY_CAST(ultima_actualizacion AS TIMESTAMP)::DATE AS ultima_actualizacion
FROM raw_contratos;
