"""Construye el modelo estrella desde stg_contratos, lo valida y lo exporta.

Uso:
    python -m proyecto.modelo             # construir + validar + exportar
    python -m proyecto.modelo --sin-exportar

Ejecuta en orden los archivos de sql/modelo/ y deja en DuckDB:
int_contratos, dim_entidad, dim_proveedor, dim_modalidad, dim_fecha y
fct_contratos. Exporta las tablas del modelo a data/processed/*.parquet
para Power BI.
"""

import argparse
import logging

import duckdb

from proyecto.config import PROCESSED_DIR, SQL_DIR
from proyecto.db import conectar

log = logging.getLogger("modelo")

TABLAS_MODELO = [
    "dim_entidad",
    "dim_proveedor",
    "dim_modalidad",
    "dim_fecha",
    "fct_contratos",
]

# Cada validación es una consulta que debe devolver 0.
VALIDACIONES = {
    "id_contrato único en fct_contratos": """
        SELECT count(*) - count(DISTINCT id_contrato) FROM fct_contratos""",
    "fct_contratos tiene un contrato por id_contrato de staging": """
        SELECT (SELECT count(DISTINCT id_contrato) FROM stg_contratos)
             - (SELECT count(*) FROM fct_contratos)""",
    "clave única en dim_entidad": """
        SELECT count(*) - count(DISTINCT entidad_key) FROM dim_entidad""",
    "clave única en dim_proveedor": """
        SELECT count(*) - count(DISTINCT proveedor_key) FROM dim_proveedor""",
    "clave única en dim_modalidad": """
        SELECT count(*) - count(DISTINCT modalidad_key) FROM dim_modalidad""",
    "clave única en dim_fecha": """
        SELECT count(*) - count(DISTINCT fecha) FROM dim_fecha""",
    "toda entidad de los hechos existe en dim_entidad": """
        SELECT count(*) FROM fct_contratos f
        ANTI JOIN dim_entidad d USING (entidad_key)""",
    "todo proveedor de los hechos existe en dim_proveedor": """
        SELECT count(*) FROM fct_contratos f
        ANTI JOIN dim_proveedor d USING (proveedor_key)""",
    "toda modalidad de los hechos existe en dim_modalidad": """
        SELECT count(*) FROM fct_contratos f
        ANTI JOIN dim_modalidad d USING (modalidad_key)""",
    "toda fecha de firma existe en dim_fecha": """
        SELECT count(*) FROM fct_contratos f
        ANTI JOIN dim_fecha d ON f.fecha_firma = d.fecha""",
    "toda fecha de inicio y fin existe en dim_fecha": """
        SELECT count(*) FROM fct_contratos f
        WHERE (f.fecha_inicio IS NOT NULL
               AND f.fecha_inicio NOT IN (SELECT fecha FROM dim_fecha))
           OR (f.fecha_fin IS NOT NULL
               AND f.fecha_fin NOT IN (SELECT fecha FROM dim_fecha))""",
    "entidad_key sin nulos": """
        SELECT count(*) FROM fct_contratos WHERE entidad_key IS NULL""",
    "valor_analisis nulo solo si hay motivo": """
        SELECT count(*) FROM fct_contratos
        WHERE (valor_analisis IS NULL) <> (motivo_valor_excluido IS NOT NULL)""",
}


def construir(con: duckdb.DuckDBPyConnection) -> None:
    for archivo in sorted((SQL_DIR / "modelo").glob("*.sql")):
        log.info("Ejecutando %s", archivo.name)
        con.execute(archivo.read_text(encoding="utf-8"))


def validar(con: duckdb.DuckDBPyConnection) -> None:
    fallos = []
    for nombre, consulta in VALIDACIONES.items():
        resultado = con.sql(consulta).fetchone()[0]
        if resultado != 0:
            fallos.append(f"{nombre}: {resultado}")
    if fallos:
        raise AssertionError("Validaciones fallidas:\n" + "\n".join(fallos))
    log.info("%s validaciones correctas", len(VALIDACIONES))


def resumen(con: duckdb.DuckDBPyConnection) -> None:
    for tabla in ["int_contratos", *TABLAS_MODELO]:
        n = con.sql(f"SELECT count(*) FROM {tabla}").fetchone()[0]
        log.info("%-15s %12s filas", tabla, f"{n:,}")
    excluidos = con.sql(
        """
        SELECT coalesce(motivo_valor_excluido, 'Incluido en métricas') AS motivo,
               count(*) AS contratos
        FROM fct_contratos GROUP BY 1 ORDER BY 2 DESC
        """
    ).fetchall()
    for motivo, n in excluidos:
        log.info("  %-40s %10s", motivo, f"{n:,}")


def _columnas_exportacion(con: duckdb.DuckDBPyConnection, tabla: str) -> str:
    """Columnas de la tabla con los DECIMAL convertidos a DOUBLE.

    Power BI no admite DECIMAL(24,2) (su decimal fijo es de 19 dígitos y 4
    decimales); como DOUBLE los montos en pesos no pierden precisión práctica.
    """
    columnas = []
    for nombre, tipo, *_ in con.sql(f"DESCRIBE {tabla}").fetchall():
        if tipo.startswith("DECIMAL"):
            columnas.append(f'CAST("{nombre}" AS DOUBLE) AS "{nombre}"')
        else:
            columnas.append(f'"{nombre}"')
    return ", ".join(columnas)


def exportar(con: duckdb.DuckDBPyConnection) -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    for tabla in TABLAS_MODELO:
        destino = PROCESSED_DIR / f"{tabla}.parquet"
        columnas = _columnas_exportacion(con, tabla)
        con.execute(
            f"COPY (SELECT {columnas} FROM {tabla}) "
            f"TO '{destino.as_posix()}' (COMPRESSION zstd)"
        )
        log.info("Exportado %s", destino.name)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--sin-exportar", action="store_true")
    args = p.parse_args()

    con = conectar()
    construir(con)
    validar(con)
    resumen(con)
    if not args.sin_exportar:
        exportar(con)
    con.close()


if __name__ == "__main__":
    main()
