"""Descarga de un año de SECOP II (contratos y modificaciones) y carga a DuckDB.

Uso:
    python -m proyecto.secop --anio 2025                 # contratos
    python -m proyecto.secop --anio 2025 --fuente modificaciones
    python -m proyecto.secop --anio 2025 --solo-carga    # recarga desde el crudo

Fuentes:
    contratos       SECOP II - Contratos Electrónicos, firmados en el año.
    modificaciones  SECOP II - Modificaciones a contratos, publicadas desde
                    el 1 de enero del año (incluye las del año siguiente).

El crudo se guarda tal cual lo devuelve la API, en páginas JSON Lines
comprimidas (data/raw/<fuente>/<anio>/), con un manifest.json que registra
la consulta, la fecha de descarga y el número de filas. La descarga se puede
interrumpir y retomar: las páginas ya guardadas se omiten.
"""

import argparse
import gzip
import json
import logging
import os
import time
from collections import deque
from dataclasses import dataclass
from datetime import UTC, datetime

import requests
from dotenv import load_dotenv
from sodapy import Socrata

from proyecto.config import RAW_DIR, leer_sql
from proyecto.db import conectar

DOMINIO = "www.datos.gov.co"
PAGINA = 50_000

log = logging.getLogger("secop")


@dataclass(frozen=True)
class Fuente:
    dataset: str
    carpeta: str
    tabla_raw: str
    sql_staging: str
    contar: bool  # el conteo previo hace timeout en datasets sin índice

    def where(self, anio: int) -> str:
        raise NotImplementedError


class Contratos(Fuente):
    def where(self, anio: int) -> str:
        return filtro_anio(anio)


class Modificaciones(Fuente):
    def where(self, anio: int) -> str:
        return (
            "estado_modificacion = 'Publicado' "
            f"AND fecha_creacion >= '{anio}-01-01T00:00:00'"
        )


FUENTES = {
    "contratos": Contratos(
        "jbjy-vk9h", "secop2_contratos", "raw_contratos", "stg_contratos.sql", True
    ),
    "modificaciones": Modificaciones(
        "u8cx-r425",
        "secop2_modificaciones",
        "raw_modificaciones",
        "stg_modificaciones.sql",
        False,
    ),
}


def cliente() -> Socrata:
    load_dotenv()
    return Socrata(DOMINIO, os.getenv("SOCRATA_APP_TOKEN"), timeout=600)


def filtro_anio(anio: int) -> str:
    return f"fecha_de_firma between '{anio}-01-01T00:00:00' and '{anio}-12-31T23:59:59'"


def carpeta_crudo(anio: int, fuente: str = "contratos"):
    return RAW_DIR / FUENTES[fuente].carpeta / str(anio)


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


def descargar(anio: int, fuente: str = "contratos") -> int:
    """Descarga una fuente para `anio`. Devuelve filas en disco."""
    f = FUENTES[fuente]
    carpeta = carpeta_crudo(anio, fuente)
    carpeta.mkdir(parents=True, exist_ok=True)
    where = f.where(anio)

    with cliente() as c:
        esperado = None
        if f.contar:
            esperado = int(
                _con_reintentos(c.get, f.dataset, select="count(*) as n", where=where)[
                    0
                ]["n"]
            )
            log.info("%s filas esperadas", f"{esperado:,}")
        columnas = [":id"] + [
            col["fieldName"]
            for col in _con_reintentos(c.get_metadata, f.dataset)["columns"]
            if not col["fieldName"].startswith(":")
        ]

        # Paginación por clave (:id > último): cada página tarda lo mismo,
        # a diferencia de $offset, que se vuelve más lento al avanzar.
        # Termina cuando una página llega incompleta.
        ultimo_id, n = None, 0
        while True:
            destino = carpeta / f"pagina_{n:04d}.jsonl.gz"
            if destino.exists():
                ultimo_id = _ultimo_id(destino)
                n += 1
                if _contar_lineas(destino) < PAGINA:
                    break
                continue
            inicio = time.time()
            filtro = where if ultimo_id is None else f"{where} AND :id > '{ultimo_id}'"
            filas = _con_reintentos(
                c.get,
                f.dataset,
                select="*, :id",
                where=filtro,
                order=":id",
                limit=PAGINA,
            )
            if not filas:
                break
            ultimo_id = filas[-1][":id"]
            temporal = destino.with_suffix(".tmp")
            with gzip.open(temporal, "wt", encoding="utf-8") as salida:
                for fila in filas:
                    salida.write(json.dumps(fila, ensure_ascii=False) + "\n")
            temporal.rename(destino)
            log.info(
                "Página %s: %s filas en %.0fs",
                n + 1,
                f"{len(filas):,}",
                time.time() - inicio,
            )
            n += 1
            if len(filas) < PAGINA:
                break

    en_disco = sum(_contar_lineas(p) for p in carpeta.glob("pagina_*.jsonl.gz"))
    manifest = {
        "dominio": DOMINIO,
        "dataset": f.dataset,
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
    if esperado is not None and en_disco != esperado:
        log.warning("Filas en disco (%s) != esperadas (%s)", en_disco, esperado)
    return en_disco


def cargar(anio: int, fuente: str = "contratos") -> None:
    """Carga el crudo a DuckDB: tabla raw (texto) y su staging (tipada)."""
    f = FUENTES[fuente]
    carpeta = carpeta_crudo(anio, fuente)
    manifest = json.loads((carpeta / "manifest.json").read_text(encoding="utf-8"))
    tipos = ", ".join(f"'{c}': 'VARCHAR'" for c in manifest["columnas"])
    patron = (carpeta / "pagina_*.jsonl.gz").as_posix()

    con = conectar()
    con.execute(
        f"""
        CREATE OR REPLACE TABLE {f.tabla_raw} AS
        SELECT *, {anio} AS anio_descarga
        FROM read_ndjson('{patron}', columns = {{{tipos}}})
        """
    )
    con.execute(leer_sql(f.sql_staging))
    staging = f.sql_staging.removesuffix(".sql")
    for tabla in (f.tabla_raw, staging):
        n = con.sql(f"SELECT count(*) FROM {tabla}").fetchone()[0]
        log.info("%s: %s filas", tabla, f"{n:,}")
    con.close()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--anio", type=int, default=2025)
    p.add_argument("--fuente", choices=FUENTES, default="contratos")
    p.add_argument("--solo-carga", action="store_true")
    args = p.parse_args()
    if not args.solo_carga:
        descargar(args.anio, args.fuente)
    cargar(args.anio, args.fuente)


if __name__ == "__main__":
    main()
