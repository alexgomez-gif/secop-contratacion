-- 08. Participación de pymes por sector
-- Pregunta: ¿qué parte del valor contratado con empresas va a pymes, y en qué
-- sectores administrativos están por encima o por debajo del promedio?
-- Técnica: FILTER, diferencia frente al total con SUM OVER () y RANK.
-- Solo personas jurídicas: "pyme" es una declaración de la empresa en SECOP.
-- Resultado clave: las pymes firman el 52,5 % de los contratos con empresas
-- pero reciben solo el 22,6 % del valor. Ley de Justicia (38,9 %) y Ambiente
-- (38,6 %) están arriba; Interior (4,9 %) y Minas y Energía (4,0 %), abajo.
-- Interpretación: las pymes ganan muchos contratos de bajo monto y casi no
-- llegan a los grandes contratos de energía, industria y hacienda.
WITH por_sector AS (
    SELECT
        e.sector,
        count(*) AS contratos,
        count(*) FILTER (WHERE f.proveedor_es_pyme) AS contratos_pyme,
        sum(f.valor_analisis) AS valor,
        coalesce(sum(f.valor_analisis) FILTER (WHERE f.proveedor_es_pyme), 0)
            AS valor_pyme
    FROM fct_contratos AS f
    INNER JOIN dim_entidad AS e USING (entidad_key)
    INNER JOIN dim_proveedor AS p USING (proveedor_key)
    WHERE p.tipo_persona = 'Jurídica'
    GROUP BY ALL
)

SELECT
    rank() OVER (ORDER BY valor_pyme / valor DESC) AS puesto,
    sector,
    contratos,
    round(valor / 1e9, 1) AS valor_empresas_miles_millones,
    round(100 * contratos_pyme / contratos, 1) AS pct_contratos_pyme,
    round(100 * valor_pyme / valor, 1) AS pct_valor_pyme,
    round(
        100 * (valor_pyme / valor - sum(valor_pyme) OVER () / sum(valor) OVER ()), 1
    ) AS dif_vs_promedio_pp
FROM por_sector
ORDER BY puesto;
