# Contratación pública en SECOP II

> ¿Qué entidades y sectores concentran la contratación directa, y qué tan
> concentrada está en pocos proveedores? Proyecto 1 del portafolio: análisis
> en Python + DuckDB e informe en Power BI.

## Objetivo

Medir el peso de la contratación directa en el Estado colombiano y la
concentración de proveedores por entidad, con los contratos de SECOP II.

Preguntas secundarias:

- ¿Qué porcentaje del valor y del número de contratos va por contratación directa, por año y departamento?
- ¿Qué entidades tienen más del 50 % de su valor en sus 5 principales proveedores?
- ¿Hay picos de contratación antes de la ley de garantías o en diciembre?
- ¿Qué parte del valor va a pymes?

## Datos

| | |
|---|---|
| Fuente | [SECOP II - Contratos Electrónicos](https://www.datos.gov.co/d/jbjy-vk9h), Colombia Compra Eficiente |
| Acceso | API Socrata de datos.gov.co con [sodapy](https://github.com/afeld/sodapy) |
| Alcance actual | Contratos con `fecha_de_firma` en 2025: 1.050.953 filas (descargadas el 2026-10-01) |
| Crudo | `data/raw/secop2_contratos/<año>/pagina_*.jsonl.gz` + `manifest.json` |
| Base analítica | `data/proyecto.duckdb` |

Los datos no se versionan en git; se regeneran con el script.

## Cómo reproducirlo

```bash
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt && pip install -e .
cp .env.example .env        # opcional: pega tu token de datos.gov.co

python -m proyecto.secop --anio 2025              # descarga + carga (~16 min, 447 MB de crudo)
python -m proyecto.secop --anio 2025 --solo-carga # recarga desde el crudo
python -m proyecto.modelo                         # limpieza + modelo estrella + Parquet (~15 s)
```

La descarga es reanudable: si se interrumpe, vuelve a ejecutar el mismo
comando y continúa desde la última página guardada.

## Pipeline

1. **Descarga** (`src/proyecto/secop.py`): consulta SoQL filtrada por año,
   paginada por clave (`:id > último`) en páginas de 50.000 filas. Cada
   página se guarda tal cual la devuelve la API (JSON Lines comprimido).
   `manifest.json` registra la consulta, la fecha de descarga y compara
   filas esperadas con descargadas.
2. **`raw_contratos`** (DuckDB): el crudo con las 95 columnas de la API más `:id`, todo como texto.
3. **`stg_contratos`** (`sql/stg_contratos.sql`): 41 columnas con tipos
   (fechas, decimales, booleanos), nombres claros y los "No Definido"
   convertidos en nulos. No elimina filas ni corrige atípicos.
4. **Limpieza y modelo estrella** (`src/proyecto/modelo.py`, `sql/modelo/`):
   `int_contratos` aplica las reglas L1–L9 y de ahí salen `fct_contratos`
   (un contrato por fila) y las dimensiones `dim_entidad`, `dim_proveedor`,
   `dim_modalidad` y `dim_fecha`. 13 validaciones automáticas detienen el
   proceso si algo falla. Se exportan a `data/processed/*.parquet` para
   Power BI.

Documentación:

- [Modelo de datos](docs/modelo_datos.md): diagrama, decisiones de diseño y diccionario.
- [Decisiones de limpieza](docs/decisiones_limpieza.md): cada regla con su evidencia e impacto.

```python
from proyecto.db import conectar

con = conectar()
con.sql("""
    SELECT m.grupo_modalidad, count(*) AS contratos, sum(f.valor_analisis) AS valor
    FROM fct_contratos f JOIN dim_modalidad m USING (modalidad_key)
    GROUP BY 1 ORDER BY 2 DESC
""")
```

## Calidad conocida de la fuente

- Valores de contrato absurdos (hasta 8,8·10²⁰ COP en el histórico; 944
  billones en 2025): sumar siempre `valor_analisis`, no `valor_contrato`.
- Nulos escritos como texto ("No Definido") en proveedor, género, duración.
- ~7 % de los contratos del dataset no tienen fecha de firma y quedan
  fuera de un filtro por año.
- Contiene datos personales (nombres, documentos, cuentas): no republicar el crudo.

## Resultados

Pendiente.

## Autoría

Alex Gómez — [GitHub](https://github.com/alexgomez-gif)
