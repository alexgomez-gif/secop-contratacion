# Dashboard de Power BI

Informe de tres páginas (**Resumen**, **Entidades** y **Alertas**) sobre el
modelo estrella del proyecto. Está guardado como proyecto de Power BI (PBIP):
el modelo en TMDL y el informe en PBIR, todo en texto, para versionarlo en git.
Los datos no se guardan aquí; se cargan desde `data/processed/*.parquet`.

```text
powerbi/
├── SECOP.pbip                 ← abrir este archivo
├── SECOP.SemanticModel/       modelo: tablas, relaciones y 33 medidas DAX (TMDL)
└── SECOP.Report/              informe: páginas y visuales (PBIR)
```

## Cómo abrirlo

Requiere **Power BI Desktop de noviembre de 2025 o posterior** (Windows).

1. Genera los Parquet: `python -m proyecto.modelo` (ver el [README](../README.md)).
   Si Power BI está en otro equipo, copia la carpeta `data/processed/`.
2. Abre `powerbi/SECOP.pbip`.
3. En **Transformar datos → Editar parámetros**, cambia `RutaDatos` por la
   carpeta de los Parquet, terminada en `\` (por defecto
   `C:\secop-contratacion\data\processed\`).
4. **Actualizar**. La carga de 1,05 millones de contratos tarda alrededor de un minuto.

Si Desktop no reconoce el formato, activa en *Archivo → Opciones → Características
de vista previa*: "Opción de guardar proyecto de Power BI (.pbip)", "Almacenar
el modelo semántico en formato TMDL" y "Almacenar informes en formato PBIR".

### Comprobación

Sin filtros, las tarjetas deben mostrar (mismas cifras que `sql/analisis/`):

| Medida | Valor esperado |
|---|---|
| Valor contratado | 177,63 billones de pesos |
| Contratos firmados | 1.050.857 |
| % valor directa | 51,6 % |
| Var. % último mes vs anterior | +43,2 % (diciembre frente a noviembre) |
| Entidades / Proveedores | 4.067 / 588.304 |
| Entidades concentradas | 824 |
| Parejas con contratos encadenados | 933 |
| Valor encadenado | 16,99 billones (10.235 contratos) |
| Personas con 4+ contratos simultáneos | 1.546 |

## Páginas

Las tres páginas comparten cuatro segmentadores sincronizados: **Departamento**,
**Grupo de modalidad**, **Modalidad** y **Mes**.

| Página | Contenido |
|---|---|
| **Resumen** | Tarjetas (valor, contratos, % directa, acumulado del año, variación del último mes). Valor mensual con media móvil de 3 meses, acumulado del año, valor por mes y grupo de modalidad, y % directa por departamento. |
| **Entidades** | Tarjetas (entidades, valor directo, % directa, proveedores, valor promedio). Tabla de entidades con % directa, diferencia frente a su orden y % de los 5 mayores proveedores; top 15 por valor directo; % directa por sector. |
| **Alertas** | Tarjetas de las tres alertas. Tabla de entidades concentradas (más del 50 % del valor en 5 proveedores, con 20 o más), tabla de parejas entidad–empresa con 3 o más contratos directos encadenados, índice de valor mensual y contratos encadenados por mes. |

Las alertas son patrones para revisar, no pruebas de irregularidad.

## Modelo

| Tabla | Origen | Notas |
|---|---|---|
| `Contratos` | `fct_contratos` | Hechos; contiene las medidas |
| `Entidad` | `dim_entidad` | `Entidad` usa `etiqueta_entidad` (nombre único) |
| `Proveedor` | `dim_proveedor` | Los nombres de personas naturales se cargan como "(persona natural)" |
| `Modalidad` | `dim_modalidad` | |
| `Calendario` | `dim_fecha` | Marcada como tabla de fechas |

Relaciones de varios a uno desde `Contratos`. La fecha de firma es la relación
activa con `Calendario`; inicio y fin son inactivas y se usan con
`USERELATIONSHIP`. El informe tiene un filtro oculto
`Calendario[En periodo de análisis] = Verdadero`, para que la inteligencia de
tiempo no se evalúe sobre años sin contratos (el calendario llega a 2057).

### Medidas

| Carpeta | Medidas |
|---|---|
| 1. Base | Valor contratado, Contratos firmados, Valor promedio por contrato, Entidades, Proveedores |
| 2. Modalidad | Valor directa, Contratos directa, % valor directa, % contratos directa, % valor directa de su orden, Dif. vs su orden (pp), % valor pyme |
| 3. Inteligencia de tiempo | Valor acumulado del año (`TOTALYTD`), Valor del último mes, Valor del mes anterior, Var. % último mes vs anterior, Valor año anterior (`SAMEPERIODLASTYEAR`), Var. % interanual, Media móvil 3 meses (`DATESINPERIOD`), Índice de valor mensual, Valor por fecha de inicio (`USERELATIONSHIP`) |
| 4. Concentración | Valor con proveedor identificado, Proveedores con valor, Valor 5 mayores proveedores (`TOPN`), % 5 mayores proveedores, % mayor proveedor |
| 5. Alertas | Entidad concentrada, Entidades concentradas, Contratos encadenados, Valor encadenado, Parejas con contratos encadenados, Personas con servicios, Personas con 4+ contratos simultáneos |

Cada medida tiene su descripción en el modelo. Las que filtran una modalidad
usan `KEEPFILTERS`, para respetar lo que el usuario elija en los segmentadores.

**Limitación:** el pipeline carga un año a la vez, así que *Valor año anterior*
y *Var. % interanual* quedan vacías hasta que el modelo tenga dos años.

## Diseño

- Color fijo por grupo de modalidad, asignado por valor y no por posición:
  Directa azul, Competitiva naranja, Régimen especial aguamarina, Enajenación
  amarillo y Sin información gris. Los gráficos de una sola serie usan el azul.
- Ningún gráfico tiene dos ejes Y.
- El tema (`StaticResources/RegisteredResources/secop.json`) define la paleta, las líneas de cuadrícula continuas y los fondos.
