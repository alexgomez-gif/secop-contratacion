-- Tabla de hechos. Grano: un contrato (id_contrato).
-- Atributos propios del contrato (tipo, estado, objeto) quedan aquí como
-- dimensiones degeneradas: tienen pocos valores o uno distinto por fila.
CREATE OR REPLACE TABLE fct_contratos AS
SELECT
    c.id_contrato,
    c.socrata_id,
    c.proceso_de_compra,
    c.referencia_del_contrato,
    -- Claves a dimensiones
    c.entidad_key,
    coalesce(p.proveedor_key, -1) AS proveedor_key,
    coalesce(m.modalidad_key, -1) AS modalidad_key,
    c.fecha_firma,
    c.fecha_inicio,
    c.fecha_fin,
    -- Dimensiones degeneradas
    c.tipo_de_contrato,
    c.estado_contrato,
    c.justificacion_modalidad,
    c.codigo_categoria_unspsc,
    c.origen_recursos,
    c.proveedor_es_pyme,
    c.objeto_del_contrato,
    c.url_proceso,
    -- Medidas (COP)
    c.valor_contrato,
    CASE WHEN c.motivo_valor_excluido IS NULL THEN c.valor_contrato END
        AS valor_analisis,
    c.motivo_valor_excluido,
    c.valor_pagado,
    c.valor_facturado,
    c.valor_pendiente_ejecucion,
    c.recursos_pgn,
    c.recursos_sgp,
    c.recursos_regalias,
    c.recursos_propios,
    -- Duración
    c.dias_adicionados,
    CASE WHEN NOT c.fechas_inconsistentes THEN c.fecha_fin - c.fecha_inicio END
        AS duracion_dias,
    coalesce(c.fechas_inconsistentes, FALSE) AS fechas_inconsistentes,
    c.fecha_fuera_de_rango
FROM int_contratos AS c
LEFT JOIN dim_proveedor AS p
    ON c.documento_proveedor_norm = p.documento
LEFT JOIN dim_modalidad AS m
    ON c.modalidad_de_contratacion = m.modalidad;
