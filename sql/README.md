# Consultas SQL

Todas las consultas corren en DuckDB sobre `data/proyecto.duckdb`. Cada
archivo empieza con un encabezado comentado: qué hace, su grano o la pregunta
que responde y, en las de análisis, el resultado clave y su interpretación.

## Estructura

| Carpeta / archivo | Capa | Qué contiene |
|---|---|---|
| `stg_contratos.sql` | Staging | Tipos, nulos explícitos y nombres claros sobre `raw_contratos` |
| `stg_modificaciones.sql` | Staging | Modificaciones publicadas a contratos (para la consulta 03) |
| `modelo/01_int_contratos.sql` | Intermedia | Reglas de limpieza L1–L9 ([decisiones](../docs/decisiones_limpieza.md)) |
| `modelo/02`–`06` | Modelo estrella | `dim_entidad`, `dim_proveedor`, `dim_modalidad`, `dim_fecha`, `fct_contratos` ([modelo](../docs/modelo_datos.md)) |
| `analisis/01`–`10` | Análisis | Consultas de negocio con funciones de ventana |
| `ejemplo.sql` | — | Consulta mínima que usan los tests |

```bash
python -m proyecto.modelo      # staging + limpieza + modelo estrella
python -m proyecto.analisis    # consultas de análisis -> reports/consultas/*.csv
```

## Hallazgos

Contratos de SECOP II firmados en 2025 (1.050.857 contratos, 177,6 billones
de pesos corrientes). Las sumas usan `valor_analisis`; un billón es un millón
de millones. "Directa" es el grupo de modalidad de `dim_modalidad`.

| # | Pregunta | Resultado clave | Interpretación |
|---|---|---|---|
| [01](analisis/01_concentracion_top10_proveedores.sql) | ¿Qué parte del valor se llevan los 10 mayores proveedores? | 12,2 % del valor (20,0 billones) entre 585.950 proveedores. Los 3 primeros son un solo contrato cada uno y suman el 6,3 %. | A escala nacional la concentración es baja y la arrastran pocos contratos gigantes; tiene más sentido medirla por entidad (05). |
| [02](analisis/02_contratacion_directa_por_entidad.sql) | ¿Qué entidades mueven más dinero por contratación directa? | Medellín (6,1 billones, 79,8 % de su valor por directa) y MinMinas (5,8 billones, 99,3 %) encabezan. 16 de las 20 primeras superan en más de 20 pp el promedio de su orden. | En las entidades que más mueven, la directa es la norma. Muchos contratos directos no implican mucho valor: Barranquilla tiene el 98 % de sus contratos por directa, pero solo el 45 % de su valor. |
| [03](analisis/03_adiciones_de_valor.sql) | ¿Cuántos contratos reciben adiciones de valor y por cuánto? | **Pendiente**: la descarga de modificaciones está incompleta. | — |
| [04](analisis/04_picos_de_firma.sql) | ¿Se concentra la firma de contratos en algunos meses? | Diciembre: el mes con menos contratos (índice 0,57) y con más valor (27,4 billones, índice 1,85). Enero y febrero concentran el número de contratos (índices 1,72 y 1,89). | Dos picos distintos: muchos contratos pequeños al arrancar el año y pocos contratos grandes antes del cierre de la vigencia. |
| [05](analisis/05_entidades_concentradas_top5.sql) | ¿Qué entidades dan más del 50 % de su valor a 5 proveedores? | 824 de las 1.988 entidades con 20 o más proveedores (41 %). MinMinas: 89,4 %, con el 72 % en un solo proveedor. | La concentración alta es frecuente; en las entidades nacionales suele venir de un solo contrato enorme, que hay que leer junto con su objeto. |
| [06](analisis/06_departamentos_vs_nacional.sql) | ¿Qué departamentos contratan más por directa que el país? | Nacional: 51,6 % del valor. Antioquia: 71,7 % (+20,1 pp); Chocó: 18,9 %. 25 de los 33 departamentos quedan por debajo del promedio nacional. | El promedio nacional casi coincide con Bogotá (42 % del valor) y Antioquia lo sube; en la mayoría de departamentos la directa pesa menos. |
| [07](analisis/07_contratos_directos_encadenados.sql) | ¿Qué parejas entidad–empresa firman contratos directos seguidos (menos de 30 días entre uno y otro)? | 933 parejas con 3 o más. El top 20 son casi todos municipios antioqueños con su empresa de desarrollo; muchas parejas firman por última vez el 7-nov-2025. | Predomina el convenio interadministrativo. El corte coincide con el inicio de la ley de garantías antes de las legislativas del 8-mar-2026. Es un patrón a revisar, no una prueba de irregularidad. |
| [08](analisis/08_pymes_por_sector.sql) | ¿Qué parte del valor contratado con empresas va a pymes? | 52,5 % de los contratos, pero solo el 22,6 % del valor. Ley de Justicia: 38,9 %; Minas y Energía: 4,0 %. | Las pymes ganan muchos contratos de bajo monto y casi no llegan a los grandes contratos de energía, industria y hacienda. |
| [09](analisis/09_evolucion_mensual_por_modalidad.sql) | ¿Cambia en el año el peso de la directa frente a la competitiva? | La directa lleva la mayor parte del valor en 11 de 12 meses. Su máximo es noviembre: 69 % del valor del mes (13,2 billones, +75 %). | Las entidades adelantan la contratación directa antes de la ley de garantías (8-nov-2025) y cierran el año con procesos competitivos. |
| [10](analisis/10_contratos_simultaneos_personas.sql) | ¿Cuántas personas tienen contratos de servicios simultáneos? | 57.326 de 520.424 personas (11,0 %) tuvieron 2 o más a la vez, casi siempre con entidades distintas; 1.546 tuvieron 4 o más. | Dos contratos a la vez es común; con 4 o más vale la pena verificar dedicación y cumplimiento. |

### Límites

- Un solo año (2025) y valores en pesos corrientes: no hay comparación entre años.
- El departamento es el de la entidad contratante. Bogotá incluye las entidades nacionales con sede allí.
- Los nombres de personas naturales no se muestran (01, 05, 07 y 10).
- Las consultas 05, 07 y 10 señalan patrones para revisar, no irregularidades.
