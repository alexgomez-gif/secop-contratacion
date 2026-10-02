-- 03. Contratos con adiciones de valor
-- Pregunta: ¿cuántos contratos se modificaron, cuántos recibieron adiciones de
-- valor y cuánto se adicionó, por grupo de modalidad?
-- Técnica: LAG sobre las versiones de cada contrato y ROW_NUMBER.
--
-- Fuente: stg_modificaciones (SECOP II - Modificaciones a contratos). Cada
-- modificación publicada trae el VALOR TOTAL del contrato tras el cambio.
-- La adición de una modificación = su valor - el de la modificación anterior.
-- La primera modificación no tiene versión anterior publicada (el dataset no
-- trae el valor original), así que su adición no se puede medir: el monto
-- adicionado es un LÍMITE INFERIOR ("adición observable").
--
-- Resultado clave: PENDIENTE. stg_modificaciones aún no está en la base: la
-- descarga de modificaciones se detuvo en la página 51 (2026-10-01).
-- Interpretación: pendiente hasta completar la descarga y ejecutar la consulta.
WITH versiones AS (
    SELECT
        m.id_contrato,
        m.valor_total_tras_modificacion AS valor_version,
        m.dias_extendidos,
        lag(m.valor_total_tras_modificacion) OVER w AS valor_version_previa,
        row_number() OVER w AS n_modificacion
    FROM stg_modificaciones AS m
    INNER JOIN fct_contratos AS f USING (id_contrato)
    WHERE f.valor_analisis IS NOT NULL
    WINDOW w AS (
        PARTITION BY m.id_contrato
        ORDER BY m.fecha_aprobacion, m.version_anterior, m.identificador_modificacion
    )
),

por_contrato AS (
    SELECT
        id_contrato,
        max(n_modificacion) AS modificaciones,
        count(*) FILTER (WHERE valor_version > valor_version_previa) AS adiciones,
        sum(greatest(valor_version - valor_version_previa, 0)) AS adicion_observable,
        sum(dias_extendidos) FILTER (WHERE dias_extendidos > 0) AS dias_extendidos
    FROM versiones
    GROUP BY id_contrato
),

por_grupo AS (
    SELECT
        m.grupo_modalidad,
        count(*) AS contratos,
        count(pc.id_contrato) AS contratos_modificados,
        count(*) FILTER (WHERE pc.dias_extendidos > 0) AS con_prorroga,
        count(*) FILTER (WHERE pc.adiciones > 0) AS con_adicion_observable,
        sum(pc.adicion_observable) AS adicion_observable,
        sum(f.valor_analisis) AS valor,
        avg(pc.modificaciones) AS modificaciones_promedio
    FROM fct_contratos AS f
    INNER JOIN dim_modalidad AS m USING (modalidad_key)
    LEFT JOIN por_contrato AS pc USING (id_contrato)
    WHERE f.valor_analisis IS NOT NULL
    GROUP BY ROLLUP (m.grupo_modalidad)
)

SELECT
    coalesce(grupo_modalidad, 'Total') AS grupo_modalidad,
    contratos,
    contratos_modificados,
    round(100 * contratos_modificados / contratos, 1) AS pct_modificados,
    round(100 * con_prorroga / contratos, 1) AS pct_con_prorroga,
    con_adicion_observable,
    round(100 * con_adicion_observable / contratos, 1) AS pct_con_adicion,
    round(adicion_observable / 1e9, 1) AS adicion_observable_miles_millones,
    round(100 * adicion_observable / valor, 2) AS adicion_pct_del_valor,
    round(modificaciones_promedio, 1) AS modificaciones_por_contrato_modificado
FROM por_grupo
ORDER BY grupo_modalidad IS NULL, contratos DESC;
