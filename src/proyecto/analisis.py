"""Ejecuta las consultas de negocio de sql/analisis/ y guarda los resultados.

Uso:
    python -m proyecto.analisis            # todas
    python -m proyecto.analisis 03 07      # solo las que empiezan por 03 y 07

Cada consulta se guarda en reports/consultas/<nombre>.csv y todas juntas en
reports/consultas.md (pregunta, técnica y resultado).
"""

import argparse
import logging
import time

import pandas as pd

from proyecto.config import REPORTS_DIR, SQL_DIR
from proyecto.db import conectar

log = logging.getLogger("analisis")
CARPETA_SQL = SQL_DIR / "analisis"
CARPETA_SALIDA = REPORTS_DIR / "consultas"


def encabezado(sql: str) -> list[str]:
    """Líneas de comentario iniciales de la consulta, sin el '-- '."""
    lineas = []
    for linea in sql.splitlines():
        if not linea.startswith("--"):
            break
        lineas.append(linea.removeprefix("--").strip())
    return lineas


def _tabla_markdown(df: pd.DataFrame) -> str:
    def celda(v) -> str:
        if pd.isna(v):
            return ""
        if isinstance(v, float):
            return f"{v:,.2f}".rstrip("0").rstrip(".")
        if isinstance(v, int):
            return f"{v:,}"
        return str(v).replace("|", "/")

    filas = [
        "| " + " | ".join(df.columns) + " |",
        "|" + "---|" * len(df.columns),
    ]
    filas += [
        "| " + " | ".join(celda(v) for v in fila) + " |"
        for fila in df.itertuples(index=False)
    ]
    return "\n".join(filas)


def ejecutar(prefijos: list[str] | None = None) -> None:
    CARPETA_SALIDA.mkdir(parents=True, exist_ok=True)
    con = conectar()
    secciones = [
        "# Consultas de negocio — SECOP II 2025\n",
        "Generado con `python -m proyecto.analisis` sobre el modelo estrella "
        "(`fct_contratos` y dimensiones). Valores en pesos colombianos "
        "corrientes; las sumas usan `valor_analisis` (ver "
        "[decisiones de limpieza](../docs/decisiones_limpieza.md)).\n",
    ]
    for archivo in sorted(CARPETA_SQL.glob("*.sql")):
        if prefijos and not any(archivo.name.startswith(p) for p in prefijos):
            continue
        sql = archivo.read_text(encoding="utf-8")
        inicio = time.time()
        df = con.sql(sql).df()
        log.info("%s: %s filas en %.1fs", archivo.name, len(df), time.time() - inicio)
        df.to_csv(CARPETA_SALIDA / f"{archivo.stem}.csv", index=False)

        titulo, *descripcion = encabezado(sql)
        ruta = f"sql/analisis/{archivo.name}"
        secciones += [
            f"## {titulo}\n",
            "\n".join(descripcion).strip() + "\n",
            f"Consulta: [`{ruta}`](../{ruta})\n",
            _tabla_markdown(df) + "\n",
        ]
    con.close()
    if not prefijos:
        (REPORTS_DIR / "consultas.md").write_text(
            "\n".join(secciones), encoding="utf-8"
        )
        log.info("Informe en reports/consultas.md")


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("prefijos", nargs="*")
    ejecutar(p.parse_args().prefijos or None)


if __name__ == "__main__":
    main()
