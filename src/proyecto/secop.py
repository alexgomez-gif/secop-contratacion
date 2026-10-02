"""Descarga de un año de SECOP II - Contratos Electrónicos y carga a DuckDB.

Uso:
    python -m proyecto.secop --anio 2025              # descarga + carga
    python -m proyecto.secop --anio 2025 --solo-carga # recarga desde el crudo

El crudo se guarda tal cual lo devuelve la API, en páginas JSON Lines
comprimidas (data/raw/secop2_contratos/<anio>/), con un manifest.json que
registra la consulta, la fecha de descarga y el número de filas esperado.
La descarga se puede interrumpir y retomar: las páginas ya guardadas se omiten.
"""

import argparse
import gzip
import json
import logging
import os
import time
from collections import deque
from datetime import UTC, datetime

import requests
from dotenv import load_dotenv
from sodapy import Socrata

from proyecto.config import RAW_DIR, leer_sql
from proyecto.db import conectar

DOMINIO = "www.datos.gov.co"
DATASET = "jbjy-vk9h"  # SECOP II - Contratos Electrónicos
PAGINA = 50_000

log = logging.getLogger("secop")


def cliente() -> Socrata:
    load_dotenv()
    return Socrata(DOMINIO, os.getenv("SOCRATA_APP_TOKEN"), timeout=600)


def filtro_anio(anio: int) -> str:
    return f"fecha_de_firma between '{anio}-01-01T00:00:00' and '{anio}-12-31T23:59:59'"


def carpeta_crudo(anio: int):
    return RAW_DIR / "secop2_contratos" / str(anio)


def _con_reintentos(funcion, *args, intentos: int = 5, **kwargs):
    for i in range(intentos):
        try:
            return funcion(*args, **kwargs)
        except requests.RequestException as error:
            estado = getattr(error.response, "status_code", None)
            # Errores de la consulta (4xx) no se arreglan reintentando
            reintentable = estado is None or estado == 429 or estado >= 500
            if not reintentable or i == intentos - 1:
                raise
            espera = 2 ** (i + 2)
            log.warning("Fallo (%s). Reintento en %ss", error, espera)
            time.sleep(espera)
    return None


def _contar_lineas(ruta) -> int:
    with gzip.open(ruta, "rt", encoding="utf-8") as f:
        return sum(1 for _ in f)


def _ultimo_id(ruta) -> str:
    with gzip.open(ruta, "rt", encoding="utf-8") as f:
        ultima = deque(f, maxlen=1)[0]
    return json.loads(ultima)[":id"]


def descargar(anio: int) -> int:
    """Descarga los contratos firmados en `anio`. Devuelve filas en disco."""
    carpeta = carpeta_crudo(anio)
    carpeta.mkdir(parents=True, exist_ok=True)
    where = filtro_anio(anio)

    with cliente() as c:
        esperado = int(
            _con_reintentos(c.get, DATASET, select="count(*) as n", where=where)[0]["n"]
        )
        columnas = [":id"] + [
            col["fieldName"]
            for col in _con_reintentos(c.get_metadata, DATASET)["columns"]
            if not col["fieldName"].startswith(":")
        ]
        paginas = -(-esperado // PAGINA)
        log.info("%s filas esperadas en %s páginas", f"{esperado:,}", paginas)

        # Paginación por clave (:id > último): cada página tarda lo mismo,
        # a diferencia de $offset, que se vuelve más lento al avanzar.
        ultimo_id = None
        for n in range(paginas):
            destino = carpeta / f"pagina_{n:04d}.jsonl.gz"
            if destino.exists():
                ultimo_id = _ultimo_id(destino)
                continue
            inicio = time.time()
            filtro = where if ultimo_id is None else f"{where} AND :id > '{ultimo_id}'"
            filas = _con_reintentos(
                c.get,
                DATASET,
                select="*, :id",
                where=filtro,
                order=":id",
                limit=PAGINA,
            )
            if not filas:
                break
            ultimo_id = filas[-1][":id"]
            temporal = destino.with_suffix(".tmp")
            with gzip.open(temporal, "wt", encoding="utf-8") as f:
                for fila in filas:
                    f.write(json.dumps(fila, ensure_ascii=False) + "\n")
            temporal.rename(destino)
            log.info(
                "Página %s/%s: %s filas en %.0fs",
                n + 1,
                paginas,
                f"{len(filas):,}",
                time.time() - inicio,
            )

    en_disco = sum(_contar_lineas(p) for p in carpeta.glob("pagina_*.jsonl.gz"))
    manifest = {
        "dominio": DOMINIO,
        "dataset": DATASET,
        "where": where,
        "order": ":id",
        "paginacion": "por clave (:id > último de la página anterior)",
        "pagina": PAGINA,
        "columnas": columnas,
        "filas_esperadas": esperado,
        "filas_descargadas": en_disco,
        "descargado_en": datetime.now(UTC).isoformat(timespec="seconds"),
    }
    (carpeta / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    if en_disco != esperado:
        log.warning("Filas en disco (%s) != esperadas (%s)", en_disco, esperado)
    return en_disco


def cargar(anio: int) -> None:
    """Carga el crudo a DuckDB: raw_contratos (texto) y stg_contratos (tipado)."""
    carpeta = carpeta_crudo(anio)
    manifest = json.loads((carpeta / "manifest.json").read_text(encoding="utf-8"))
    tipos = ", ".join(f"'{c}': 'VARCHAR'" for c in manifest["columnas"])
    patron = (carpeta / "pagina_*.jsonl.gz").as_posix()

    con = conectar()
    con.execute(
        f"""
        CREATE OR REPLACE TABLE raw_contratos AS
        SELECT *, {anio} AS anio_descarga
        FROM read_ndjson('{patron}', columns = {{{tipos}}})
        """
    )
    con.execute(leer_sql("stg_contratos.sql"))
    for tabla in ("raw_contratos", "stg_contratos"):
        n = con.sql(f"SELECT count(*) FROM {tabla}").fetchone()[0]
        log.info("%s: %s filas", tabla, f"{n:,}")
    con.close()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--anio", type=int, default=2025)
    p.add_argument("--solo-carga", action="store_true")
    args = p.parse_args()
    if not args.solo_carga:
        descargar(args.anio)
    cargar(args.anio)


if __name__ == "__main__":
    main()
