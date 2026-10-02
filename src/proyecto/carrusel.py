"""Carrusel en PDF para LinkedIn (6 láminas de 1080 × 1350 px).

Uso:
    python -m proyecto.figuras     # primero, si cambiaron los CSV
    python -m proyecto.carrusel

Usa las figuras de docs/figuras/. Si existen capturas del dashboard en
docs/capturas/ (01_resumen.png, 02_entidades.png, 03_alertas.png), la lámina del
dashboard las muestra; si no, describe sus tres páginas.
"""

import logging
import textwrap
from pathlib import Path

import matplotlib.image as mpimg
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import FancyBboxPatch, Rectangle

from proyecto.config import RAIZ
from proyecto.figuras import (
    AZUL,
    REJILLA,
    SUPERFICIE,
    TINTA,
    TINTA_SECUNDARIA,
    TINTA_TENUE,
)
from proyecto.figuras import (
    CARPETA_SALIDA as CARPETA_FIGURAS,
)

log = logging.getLogger("carrusel")
CARPETA_CAPTURAS = RAIZ / "docs" / "capturas"
SALIDA = RAIZ / "docs" / "publicacion" / "carrusel_linkedin.pdf"
ENLACE = "github.com/alexgomez-gif/secop-contratacion"
AUTOR = "Alex Gómez"
TOTAL = 6

ANCHO, ALTO = 7.2, 9.0  # pulgadas; a 150 ppp son 1080 × 1350 px (4:5)


def _lamina(numero: int, etiqueta: str):
    fig = plt.figure(figsize=(ANCHO, ALTO), dpi=150)
    fig.patch.set_facecolor(SUPERFICIE)
    fig.add_artist(
        Rectangle((0, 0.985), 1, 0.015, color=AZUL, transform=fig.transFigure)
    )
    fig.text(
        0.07, 0.94, etiqueta.upper(), fontsize=10, weight="bold", color=TINTA_TENUE
    )
    fig.text(0.07, 0.035, f"{AUTOR} · SECOP II 2025", fontsize=9, color=TINTA_TENUE)
    fig.text(
        0.93, 0.035, f"{numero}/{TOTAL}", fontsize=9, color=TINTA_TENUE, ha="right"
    )
    return fig


def _texto(fig, y: float, texto: str, ancho: int, **kwargs) -> None:
    fig.text(0.07, y, textwrap.fill(texto, ancho), va="top", linespacing=1.3, **kwargs)


def _imagen(fig, ruta: Path, caja: tuple[float, float, float, float]) -> None:
    ax = fig.add_axes(caja)
    ax.imshow(mpimg.imread(ruta))
    ax.axis("off")


def portada():
    fig = _lamina(1, "Proyecto de datos · Contratación pública")
    _texto(
        fig,
        0.8,
        "¿Cuánto contrata el Estado colombiano sin competencia?",
        20,
        fontsize=34,
        weight="bold",
        color=TINTA,
    )
    _texto(
        fig,
        0.43,
        "Analicé 1,05 millones de contratos firmados en 2025 en SECOP II con "
        "Python, SQL y Power BI.",
        38,
        fontsize=16,
        color=TINTA_SECUNDARIA,
    )
    _texto(fig, 0.25, "3 hallazgos  →", 30, fontsize=18, weight="bold", color=TINTA)
    return fig


def hallazgo(numero: int, cifra: str, mensaje: str, figura: str, caja):
    fig = _lamina(numero, f"Hallazgo {numero - 1} de 3")
    fig.text(0.07, 0.905, cifra, fontsize=44, weight="bold", color=TINTA, va="top")
    _texto(fig, 0.81, mensaje, 46, fontsize=14, color=TINTA_SECUNDARIA)
    _imagen(fig, CARPETA_FIGURAS / figura, caja)
    return fig


def dashboard():
    fig = _lamina(5, "Dashboard en Power BI")
    capturas = sorted(CARPETA_CAPTURAS.glob("0[1-3]_*.png"))
    if capturas:
        _texto(
            fig,
            0.9,
            "Tres páginas con filtros sincronizados",
            40,
            fontsize=22,
            weight="bold",
            color=TINTA,
        )
        alto = 0.72 / len(capturas)
        for i, ruta in enumerate(capturas):
            _imagen(fig, ruta, (0.07, 0.8 - (i + 1) * alto, 0.86, alto - 0.015))
        return fig

    _texto(
        fig,
        0.9,
        "Tres páginas con filtros sincronizados",
        30,
        fontsize=26,
        weight="bold",
        color=TINTA,
    )
    _texto(
        fig,
        0.765,
        "Departamento, modalidad y mes filtran todas las páginas a la vez.",
        46,
        fontsize=13,
        color=TINTA_SECUNDARIA,
    )
    paginas = [
        (
            "Resumen",
            "Valor, contratos y % directa. Valor mensual con media móvil "
            "de 3 meses y % directa por departamento.",
        ),
        (
            "Entidades",
            "Qué entidades contratan más por vía directa frente a las de "
            "su mismo orden y cuánto pesan sus 5 mayores proveedores.",
        ),
        (
            "Alertas",
            "Entidades concentradas, contratos directos encadenados a menos "
            "de 30 días y el índice de valor mensual.",
        ),
    ]
    for i, (titulo, detalle) in enumerate(paginas):
        y = 0.55 - i * 0.165
        fig.add_artist(
            FancyBboxPatch(
                (0.07, y),
                0.86,
                0.14,
                boxstyle="round,pad=0,rounding_size=0.015",
                transform=fig.transFigure,
                facecolor="white",
                edgecolor=REJILLA,
                linewidth=1,
            )
        )
        fig.add_artist(
            Rectangle((0.07, y), 0.012, 0.14, color=AZUL, transform=fig.transFigure)
        )
        fig.text(
            0.11, y + 0.115, titulo, fontsize=15, weight="bold", color=TINTA, va="top"
        )
        fig.text(
            0.11,
            y + 0.075,
            textwrap.fill(detalle, 52),
            fontsize=11,
            color=TINTA_SECUNDARIA,
            va="top",
            linespacing=1.3,
        )
    fig.text(
        0.07,
        0.09,
        "33 medidas DAX · modelo estrella · inteligencia de tiempo",
        fontsize=11,
        color=TINTA_TENUE,
    )
    return fig


def cierre():
    fig = _lamina(6, "Código, datos y método")
    _texto(
        fig,
        0.86,
        "Todo el proyecto es reproducible",
        24,
        fontsize=30,
        weight="bold",
        color=TINTA,
    )
    pasos = [
        "Descarga de la API de datos.gov.co con Python",
        "Limpieza documentada y modelo estrella en DuckDB/SQL",
        "10 consultas con funciones de ventana",
        "Dashboard en Power BI con 33 medidas DAX",
        "48 pruebas automáticas con pytest",
    ]
    for i, paso in enumerate(pasos):
        fig.text(
            0.07, 0.66 - i * 0.055, f"—  {paso}", fontsize=14, color=TINTA_SECUNDARIA
        )
    fig.text(0.07, 0.3, ENLACE, fontsize=17, weight="bold", color=TINTA)
    _texto(
        fig,
        0.24,
        "Son patrones para priorizar la revisión, no pruebas de irregularidad. "
        "¿Qué otra pregunta le harías a estos datos?",
        48,
        fontsize=12,
        color=TINTA_TENUE,
    )
    return fig


def generar(salida: Path = SALIDA) -> Path:
    laminas = [
        portada(),
        hallazgo(
            2,
            "51,6 %",
            "del valor contratado en 2025 fue por contratación directa. "
            "En Antioquia llega al 71,7 %.",
            "hallazgo_1_directa_departamentos.png",
            (0.07, 0.08, 0.86, 0.62),
        ),
        hallazgo(
            3,
            "12,2 % vs. 824",
            "Los 10 mayores proveedores del país suman solo el 12,2 %, pero 824 "
            "entidades entregan más de la mitad de su valor a 5 proveedores.",
            "hallazgo_2_concentracion_entidades.png",
            (0.04, 0.1, 0.92, 0.66),
        ),
        hallazgo(
            4,
            "27,4 billones",
            "se firmaron en diciembre, 1,85 veces un mes promedio. En noviembre, "
            "antes de la ley de garantías, el 69 % fue directa.",
            "hallazgo_3_valor_mensual_modalidad.png",
            (0.04, 0.1, 0.92, 0.66),
        ),
        dashboard(),
        cierre(),
    ]
    salida.parent.mkdir(parents=True, exist_ok=True)
    with PdfPages(salida) as pdf:
        for fig in laminas:
            pdf.savefig(fig, facecolor=SUPERFICIE)
            plt.close(fig)
    log.info("Carrusel en %s", salida)
    return salida


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    generar()


if __name__ == "__main__":
    main()
