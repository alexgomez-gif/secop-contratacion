"""Figuras de los tres hallazgos del README a partir de reports/consultas/*.csv.

Uso:
    python -m proyecto.figuras

Lee los CSV que genera `python -m proyecto.analisis` (versionados en el repo),
así que no necesita la base de DuckDB. Guarda los PNG en docs/figuras/.
"""

import logging
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.ticker import FuncFormatter

from proyecto.config import RAIZ, REPORTS_DIR

log = logging.getLogger("figuras")
CARPETA_CONSULTAS = REPORTS_DIR / "consultas"
CARPETA_SALIDA = RAIZ / "docs" / "figuras"

# Paleta validada (lightness, CVD y contraste) con la skill de visualización.
SUPERFICIE = "#fcfcfb"
TINTA = "#0b0b0b"
TINTA_SECUNDARIA = "#52514e"
TINTA_TENUE = "#898781"
REJILLA = "#e1e0d9"
EJE = "#c3c2b7"
AZUL = "#2a78d6"
AZUL_OSCURO = "#184f95"
AZUL_CLARO = "#86b6ef"
GRIS_BARRA = "#c3c2b7"
COLORES_MODALIDAD = {
    "Directa": "#2a78d6",
    "Competitiva": "#eb6834",
    "Régimen especial": "#1baf7a",
}
MESES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun"]
MESES += ["Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]

# Nombres cortos para las entidades del hallazgo 2 (el SECOP trae siglas y sufijos).
NOMBRES_CORTOS = {
    "MINISTERIO DE MINAS Y ENERGIA": "Ministerio de Minas y Energía",
    "RNEC": "Registraduría Nacional",
    "MINISTERIO DE COMERCIO INDUSTRIA Y TURISMO - MINCIT": "Ministerio de Comercio",
    "MINSALUD": "Ministerio de Salud",
    "SANTIAGO DE CALI DISTRITO ESPECIAL - DEPARTAMENTO ADMINISTRATIVO DE HACIENDA": (
        "Hacienda de Cali"
    ),
    "ALCALDÍA DISTRITAL DE SANTA MARTA": "Alcaldía de Santa Marta",
    "UNP": "Unidad Nacional de Protección",
    "EJERCITO DIRECCION DE ADQUISICIONES": "Ejército (adquisiciones)",
    "FONDO FINANCIERO DISTRITAL DE SALUD.": "Fondo Distrital de Salud",
    "DEPARTAMENTO DE SANTANDER": "Gobernación de Santander",
}


def numero(valor: float, decimales: int = 1) -> str:
    """Formato colombiano: punto de miles y coma decimal (1.234,5)."""
    texto = f"{valor:,.{decimales}f}"
    return texto.replace(",", "_").replace(".", ",").replace("_", ".")


def leer(nombre: str) -> pd.DataFrame:
    return pd.read_csv(CARPETA_CONSULTAS / f"{nombre}.csv")


def _estilo() -> None:
    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.size": 10,
            "figure.facecolor": SUPERFICIE,
            "axes.facecolor": SUPERFICIE,
            "axes.edgecolor": EJE,
            "axes.labelcolor": TINTA_SECUNDARIA,
            "axes.titlecolor": TINTA,
            "xtick.color": TINTA_TENUE,
            "ytick.color": TINTA_SECUNDARIA,
            "grid.color": REJILLA,
            "grid.linewidth": 1,
            "savefig.facecolor": SUPERFICIE,
        }
    )


def _ejes_limpios(ax, eje_valor: str = "x") -> None:
    for lado in ("top", "right", "left" if eje_valor == "x" else "bottom"):
        ax.spines[lado].set_visible(False)
    ax.grid(axis=eje_valor)
    ax.set_axisbelow(True)
    ax.tick_params(length=0)


def _titulo(fig, titulo: str, subtitulo: str) -> None:
    alto = fig.get_figheight()  # posiciones en pulgadas desde el borde superior
    fig.text(0.02, 1 - 0.18 / alto, titulo, fontsize=14, weight="bold", va="top")
    fig.text(
        0.02, 1 - 0.5 / alto, subtitulo, fontsize=10, color=TINTA_SECUNDARIA, va="top"
    )


def _fuente(fig, texto: str) -> None:
    fig.text(0.02, 0.012, texto, fontsize=8, color=TINTA_TENUE, va="bottom")


def _guardar(fig, nombre: str, carpeta: Path) -> Path:
    carpeta.mkdir(parents=True, exist_ok=True)
    ruta = carpeta / nombre
    fig.savefig(ruta, dpi=150)
    plt.close(fig)
    log.info("Figura en %s", ruta)
    return ruta


def hallazgo_1(carpeta: Path = CARPETA_SALIDA) -> Path:
    """Porcentaje del valor por contratación directa en cada departamento."""
    df = leer("06_departamentos_vs_nacional")
    df = df[df["departamento"] != "Sin información"]
    df = df.sort_values("pct_valor_directa")
    nacional = (df["pct_valor_directa"] - df["dif_vs_nacional_pp"]).iloc[0]
    df["departamento"] = df["departamento"].replace(
        {
            "Distrito Capital de Bogotá": "Bogotá D.C.",
            "San Andrés, Providencia y Santa Catalina": "San Andrés",
        }
    )

    fig, ax = plt.subplots(figsize=(8, 9.5))
    fig.subplots_adjust(left=0.2, right=0.94, top=0.915, bottom=0.07)
    colores = [AZUL if d == "Antioquia" else GRIS_BARRA for d in df["departamento"]]
    ax.barh(df["departamento"], df["pct_valor_directa"], height=0.62, color=colores)
    ax.axvline(nacional, color=TINTA_SECUNDARIA, linewidth=1)
    ax.text(
        nacional + 0.8,
        -1.4,
        f"Promedio nacional: {numero(nacional)} %",
        color=TINTA_SECUNDARIA,
        fontsize=9,
        va="center",
    )
    for _, fila in df[df["departamento"].isin(["Antioquia", "Chocó"])].iterrows():
        ax.text(
            fila["pct_valor_directa"] + 0.8,
            fila["departamento"],
            f"{numero(fila['pct_valor_directa'])} %",
            color=TINTA,
            fontsize=9,
            weight="bold" if fila["departamento"] == "Antioquia" else "normal",
            va="center",
        )
    ax.set_xlim(0, 100)
    ax.set_ylim(-2, len(df))
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:.0f} %"))
    ax.tick_params(axis="y", labelsize=9)
    _ejes_limpios(ax, "x")
    debajo = int((df["dif_vs_nacional_pp"] < 0).sum())
    antioquia = df.set_index("departamento").loc["Antioquia", "pct_valor_directa"]
    _titulo(
        fig,
        f"Antioquia asigna el {numero(antioquia)} % de su valor por contratación "
        "directa",
        f"% del valor contratado por contratación directa, por departamento. "
        f"{debajo} de {len(df)} están por debajo del promedio.",
    )
    _fuente(
        fig,
        "Fuente: SECOP II, contratos firmados en 2025. Consulta "
        "sql/analisis/06_departamentos_vs_nacional.sql",
    )
    return _guardar(fig, "hallazgo_1_directa_departamentos.png", carpeta)


def hallazgo_2(carpeta: Path = CARPETA_SALIDA) -> Path:
    """Peso de los 5 mayores proveedores en las entidades concentradas más grandes."""
    top10 = leer("01_concentracion_top10_proveedores")
    nacional = top10["pct_acumulado"].iloc[-1]
    total_proveedores = int(top10["total_proveedores"].iloc[0])
    df = leer("05_entidades_concentradas_top5").head(10)
    df["entidad"] = (
        df["nombre_entidad"].map(NOMBRES_CORTOS).fillna(df["nombre_entidad"])
    )
    df["resto_top5"] = df["pct_top5"] - df["pct_mayor_proveedor"]
    df = df.iloc[::-1]
    concentradas = int(df["entidades_que_cumplen"].iloc[0])

    fig, ax = plt.subplots(figsize=(8, 5.8))
    fig.subplots_adjust(left=0.29, right=0.94, top=0.8, bottom=0.11)
    ax.barh(
        df["entidad"],
        df["pct_mayor_proveedor"],
        height=0.62,
        color=AZUL_OSCURO,
        label="Mayor proveedor",
    )
    ax.barh(
        df["entidad"],
        df["resto_top5"],
        left=df["pct_mayor_proveedor"] + 0.4,
        height=0.62,
        color=AZUL_CLARO,
        label="Proveedores 2.º a 5.º",
    )
    for _, fila in df.iterrows():
        ax.text(
            fila["pct_top5"] + 1.2,
            fila["entidad"],
            f"{numero(fila['pct_top5'], 0)} %",
            color=TINTA_SECUNDARIA,
            fontsize=9,
            va="center",
        )
    for x, texto in [
        (50, "50 %: umbral de concentración"),
        (nacional, f"Top 10 del país: {numero(nacional)} %"),
    ]:
        ax.axvline(x, color=TINTA_SECUNDARIA, linewidth=1)
        ax.text(x + 0.8, len(df) - 0.35, texto, color=TINTA_SECUNDARIA, fontsize=8.5)
    ax.set_xlim(0, 105)
    ax.set_ylim(-0.6, len(df) + 0.2)
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:.0f} %"))
    ax.legend(
        loc="lower left",
        bbox_to_anchor=(-0.02, 1.0),
        ncols=2,
        frameon=False,
        fontsize=9,
        labelcolor=TINTA_SECUNDARIA,
        handlelength=1,
    )
    _ejes_limpios(ax, "x")
    _titulo(
        fig,
        "La concentración está dentro de cada entidad, no en el país",
        f"% del valor en los 5 mayores proveedores: las 10 entidades de más valor "
        f"entre las {concentradas} que pasan del 50 %.",
    )
    _fuente(
        fig,
        f"Fuente: SECOP II 2025, entidades con 20 o más proveedores. El top 10 "
        f"nacional se mide sobre {numero(total_proveedores, 0)} proveedores. "
        "Consultas 01 y 05.",
    )
    return _guardar(fig, "hallazgo_2_concentracion_entidades.png", carpeta)


def hallazgo_3(carpeta: Path = CARPETA_SALIDA) -> Path:
    """Valor contratado por mes y grupo de modalidad."""
    df = leer("09_evolucion_mensual_por_modalidad")
    tabla = df.pivot_table(
        index="mes", columns="grupo_modalidad", values="valor_miles_millones"
    )
    tabla = tabla[list(COLORES_MODALIDAD)] / 1000  # billones de pesos
    pct_directa = df[df["grupo_modalidad"] == "Directa"].set_index("mes")[
        "pct_valor_del_mes"
    ]
    meses = leer("04_picos_de_firma").set_index("mes")

    fig, ax = plt.subplots(figsize=(8, 5.2))
    fig.subplots_adjust(left=0.08, right=0.97, top=0.78, bottom=0.12)
    tope = pd.Series(0.0, index=tabla.index)
    for i, (modalidad, color) in enumerate(COLORES_MODALIDAD.items()):
        inicio = tope + (0.08 if i else 0)  # hueco de ~2 px entre segmentos
        ax.bar(
            tabla.index,
            tabla[modalidad],
            bottom=inicio,
            width=0.62,
            color=color,
            label=modalidad,
        )
        tope = inicio + tabla[modalidad]
    for mes, texto in [
        (12, f"{numero(meses.loc[12, 'valor_miles_millones'] / 1000)} billones"),
        (11, f"{numero(pct_directa.loc[11], 0)} % directa"),
    ]:
        ax.text(
            mes,
            tope.loc[mes] + 0.5,
            texto,
            ha="center",
            fontsize=9,
            weight="bold",
            color=TINTA,
        )
    ax.set_xticks(tabla.index, MESES)
    ax.set_ylim(0, 30)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:.0f}"))
    ax.set_ylabel("Billones de pesos")
    ax.legend(
        loc="lower left",
        bbox_to_anchor=(-0.01, 1.0),
        ncols=3,
        frameon=False,
        fontsize=9,
        labelcolor=TINTA_SECUNDARIA,
        handlelength=1,
    )
    _ejes_limpios(ax, "y")
    indice = meses.loc[12, "indice_valor"]
    _titulo(
        fig,
        "Diciembre concentra el valor; noviembre, la contratación directa",
        f"Valor contratado por mes y modalidad. Diciembre suma {numero(indice, 2)} "
        "veces el valor de un mes promedio.",
    )
    _fuente(
        fig,
        "Fuente: SECOP II, contratos firmados en 2025, pesos corrientes. "
        "Consultas 04 y 09.",
    )
    return _guardar(fig, "hallazgo_3_valor_mensual_modalidad.png", carpeta)


def generar(carpeta: Path = CARPETA_SALIDA) -> list[Path]:
    _estilo()
    return [hallazgo_1(carpeta), hallazgo_2(carpeta), hallazgo_3(carpeta)]


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    generar()


if __name__ == "__main__":
    main()
