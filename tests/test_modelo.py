"""Pruebas de las reglas de limpieza (L1–L9) y del modelo estrella."""

import pytest
from test_secop import COLUMNAS_RAW

from proyecto.config import leer_sql
from proyecto.db import conectar
from proyecto.modelo import _columnas_exportacion, construir, validar

BASE = {
    "codigo_entidad": "100",
    "nombre_entidad": "ALCALDIA DE PRUEBA",
    "nit_entidad": "800000001",
    "departamento": "Antioquia",
    "ciudad": "Medellín",
    "estado_contrato": "En ejecución",
    "sector": "Educación Nacional",
    "tipo_de_contrato": "Prestación de servicios",
    "modalidad_de_contratacion": "Contratación directa",
    "fecha_de_firma": "2025-03-01T00:00:00.000",
    "fecha_de_inicio_del_contrato": "2025-03-02T00:00:00.000",
    "fecha_de_fin_del_contrato": "2025-12-31T00:00:00.000",
    "tipodocproveedor": "Cédula de Ciudadanía",
    "documento_proveedor": "1000000001",
    "proveedor_adjudicado": "ANA PEREZ",
    "es_pyme": "No",
    "valor_del_contrato": "20000000",
    "ultima_actualizacion": "2025-06-01T00:00:00.000",
}


def _modelo(filas: list[dict]):
    """Construye el modelo completo en memoria a partir de filas crudas."""
    con = conectar(":memory:")
    columnas = ", ".join(f'"{c}" VARCHAR' for c in COLUMNAS_RAW)
    con.execute(f"CREATE TABLE raw_contratos ({columnas})")
    for i, cambios in enumerate(filas):
        fila = {":id": f"row-{i:04d}", "id_contrato": f"CO1.PCCNTR.{i}"}
        fila |= BASE | cambios
        nombres = ", ".join(f'"{c}"' for c in fila)
        con.execute(
            f"INSERT INTO raw_contratos ({nombres}) VALUES "
            f"({', '.join('?' * len(fila))})",
            list(fila.values()),
        )
    con.execute(leer_sql("stg_contratos.sql"))
    construir(con)
    validar(con)
    return con


@pytest.mark.parametrize(
    ("documento", "esperado"),
    [
        ("13.853.963", "13853963"),
        ("1088249252.", "1088249252"),
        ("900123456-7", "900123456"),
        ("32738740-", "32738740"),
        ("|1044429284", "1044429284"),
        ("0012345678", "12345678"),
        ("04/09/1980", None),
        ("000000", None),
        ("1", None),
        ("N/A", None),
        ("MELIZA CARDOZO", None),
    ],
)
def test_l2_normalizar_documento(documento, esperado):
    con = _modelo([{"documento_proveedor": documento}])
    assert con.sql("SELECT documento_proveedor_norm FROM int_contratos").fetchone()[
        0
    ] == (esperado)


def test_l1_duplicados_exactos_se_conservan_una_vez():
    con = _modelo([{"id_contrato": "CO1.X"}, {"id_contrato": "CO1.X"}])
    assert con.sql("SELECT count(*) FROM fct_contratos").fetchone()[0] == 1


def test_l3_proveedor_toma_el_nombre_mas_frecuente():
    con = _modelo(
        [
            {
                "documento_proveedor": "1.000.000.001",
                "proveedor_adjudicado": "ana  perez",
            },
            {"proveedor_adjudicado": "ANA PEREZ"},
            {"proveedor_adjudicado": "ANA MARIA PEREZ"},
        ]
    )
    fila = con.sql(
        "SELECT nombre_proveedor, nombres_distintos FROM dim_proveedor "
        "WHERE proveedor_key <> -1"
    ).fetchall()
    assert fila == [("ANA PEREZ", 2)]


def test_proveedor_invalido_va_a_sin_identificar():
    con = _modelo([{"documento_proveedor": "No Definido"}])
    assert con.sql("SELECT proveedor_key FROM fct_contratos").fetchone()[0] == -1


def test_l5_capitaliza_estado_y_sector():
    con = _modelo([{"estado_contrato": "terminado", "sector": "defensa"}])
    assert con.sql("SELECT estado_contrato, sector FROM int_contratos").fetchone() == (
        "Terminado",
        "Defensa",
    )


@pytest.mark.parametrize(
    ("cambios", "motivo"),
    [
        ({"valor_del_contrato": "0"}, "Valor cero o negativo"),
        ({"valor_del_contrato": "-5"}, "Valor cero o negativo"),
        (
            {"valor_del_contrato": "944187311000000"},
            "Valor imposible (>= 100 billones)",
        ),
        (
            {"valor_del_contrato": "2000000000"},
            "Persona natural en servicios > 1.000 M",
        ),
        ({"valor_del_contrato": "2000000000", "tipodocproveedor": "NIT"}, None),
        ({"valor_del_contrato": "2000000000", "tipo_de_contrato": "Obra"}, None),
        ({}, None),
    ],
)
def test_l7_valores_excluidos_de_metricas(cambios, motivo):
    con = _modelo([cambios])
    fila = con.sql(
        "SELECT motivo_valor_excluido, valor_analisis IS NULL FROM fct_contratos"
    ).fetchone()
    assert fila == (motivo, motivo is not None)


def test_l7_error_de_tres_ceros():
    con = _modelo(
        [
            {
                "valor_del_contrato": "18600000000",
                "valor_pagado": "18600000",
                "tipodocproveedor": "NIT",
            }
        ]
    )
    assert (
        con.sql("SELECT motivo_valor_excluido FROM fct_contratos").fetchone()[0]
        == "Error de tres ceros (valor = 1.000 x pagado)"
    )


def test_l7_contrato_desproporcionado_sin_pagos():
    normales = [{"valor_del_contrato": "1000000000"} for _ in range(3)]
    gigante = {"valor_del_contrato": "998000000000", "tipodocproveedor": "NIT"}
    con = _modelo([*normales, gigante])
    motivos = con.sql(
        "SELECT motivo_valor_excluido, count(*) FROM fct_contratos "
        "GROUP BY 1 ORDER BY 1"
    ).fetchall()
    assert motivos == [("Desproporcionado para la entidad", 1), (None, 3)]


def test_l7_contrato_grande_pagado_se_conserva():
    normales = [{"valor_del_contrato": "1000000000"} for _ in range(3)]
    gigante = {
        "valor_del_contrato": "409000000000",
        "valor_pagado": "408990000000",
        "tipodocproveedor": "NIT",
    }
    con = _modelo([*normales, gigante])
    assert (
        con.sql(
            "SELECT count(*) FROM fct_contratos WHERE motivo_valor_excluido IS NOT NULL"
        ).fetchone()[0]
        == 0
    )


def test_l8_fechas_fuera_de_rango_quedan_nulas():
    con = _modelo(
        [
            {
                "fecha_de_inicio_del_contrato": "1899-12-31T00:00:00.000",
                "fecha_de_fin_del_contrato": "5025-12-20T00:00:00.000",
            }
        ]
    )
    fila = con.sql(
        "SELECT fecha_inicio, fecha_fin, fecha_fuera_de_rango, duracion_dias "
        "FROM fct_contratos"
    ).fetchone()
    assert fila == (None, None, True, None)


def test_l8_fin_antes_de_inicio_no_calcula_duracion():
    con = _modelo([{"fecha_de_fin_del_contrato": "2025-01-01T00:00:00.000"}])
    fila = con.sql(
        "SELECT fechas_inconsistentes, duracion_dias FROM fct_contratos"
    ).fetchone()
    assert fila == (True, None)


def test_l9_entidad_toma_datos_del_contrato_mas_reciente():
    con = _modelo(
        [
            {
                "nombre_entidad": "ALCALDIA VIEJA",
                "fecha_de_firma": "2025-01-01T00:00:00",
            },
            {
                "nombre_entidad": "ALCALDIA NUEVA",
                "fecha_de_firma": "2025-09-01T00:00:00",
                "departamento": "No Definido",
            },
        ]
    )
    assert con.sql(
        "SELECT nombre_entidad, departamento, nombres_distintos FROM dim_entidad"
    ).fetchone() == ("ALCALDIA NUEVA", "Antioquia", 2)


@pytest.mark.parametrize(
    ("modalidad", "grupo"),
    [
        ("Contratación directa", "Directa"),
        ("Contratación Directa (con ofertas)", "Directa"),
        ("Contratación régimen especial", "Régimen especial"),
        ("Mínima cuantía", "Competitiva"),
        ("Licitación pública", "Competitiva"),
        ("Enajenación de bienes con subasta", "Enajenación"),
    ],
)
def test_grupo_modalidad(modalidad, grupo):
    con = _modelo([{"modalidad_de_contratacion": modalidad}])
    assert (
        con.sql(
            "SELECT grupo_modalidad FROM fct_contratos JOIN dim_modalidad "
            "USING (modalidad_key)"
        ).fetchone()[0]
        == grupo
    )


def _directo_juridica(fecha: str, **cambios) -> dict:
    return {
        "tipodocproveedor": "NIT",
        "documento_proveedor": "900123456",
        "proveedor_adjudicado": "EMPRESA SAS",
        "fecha_de_firma": f"{fecha}T00:00:00.000",
    } | cambios


def test_encadenado_30d_cuenta_dias_desde_el_directo_anterior():
    con = _modelo(
        [
            _directo_juridica("2025-01-01"),
            _directo_juridica("2025-01-20"),
            _directo_juridica("2025-03-31"),
            # Competitivo con la misma empresa: no cuenta ni corta la secuencia
            _directo_juridica(
                "2025-01-25", modalidad_de_contratacion="Licitación pública"
            ),
        ]
    )
    filas = con.sql(
        "SELECT fecha_firma::VARCHAR, dias_desde_directo_anterior, encadenado_30d "
        "FROM fct_contratos ORDER BY fecha_firma"
    ).fetchall()
    assert filas == [
        ("2025-01-01", None, False),
        ("2025-01-20", 19, True),
        ("2025-01-25", None, False),
        ("2025-03-31", 70, False),
    ]


def test_encadenado_30d_excluye_personas_naturales():
    con = _modelo([{}, {"fecha_de_firma": "2025-03-05T00:00:00.000"}])
    assert (
        con.sql("SELECT count(*) FROM fct_contratos WHERE encadenado_30d").fetchone()[0]
        == 0
    )


def test_max_contratos_simultaneos_de_persona_natural():
    con = _modelo(
        [
            {},  # 2025-03-02 a 2025-12-31
            {"fecha_de_inicio_del_contrato": "2025-06-01T00:00:00.000"},
            {
                "fecha_de_inicio_del_contrato": "2026-01-01T00:00:00.000",
                "fecha_de_fin_del_contrato": "2026-06-30T00:00:00.000",
            },
            # Una empresa no recibe el indicador
            {"tipodocproveedor": "NIT", "documento_proveedor": "900123456"},
        ]
    )
    filas = con.sql(
        "SELECT tipo_persona, max_contratos_simultaneos FROM dim_proveedor "
        "WHERE proveedor_key <> -1 ORDER BY 1"
    ).fetchall()
    assert filas == [("Jurídica", None), ("Natural", 2)]


def test_etiqueta_entidad_distingue_nombres_repetidos():
    con = _modelo(
        [
            {"codigo_entidad": "1", "nombre_entidad": "PERSONERIA", "ciudad": "Tunja"},
            {"codigo_entidad": "2", "nombre_entidad": "PERSONERIA", "ciudad": "Pasto"},
            {"codigo_entidad": "3", "nombre_entidad": "ALCALDIA DE PRUEBA"},
        ]
    )
    etiquetas = con.sql(
        "SELECT etiqueta_entidad FROM dim_entidad ORDER BY entidad_key"
    ).fetchall()
    assert etiquetas == [
        ("PERSONERIA (Tunja)",),
        ("PERSONERIA (Pasto)",),
        ("ALCALDIA DE PRUEBA",),
    ]


def test_dim_fecha_marca_los_anios_con_firmas():
    con = _modelo([{"fecha_de_fin_del_contrato": "2026-03-31T00:00:00.000"}])
    filas = con.sql(
        "SELECT anio, bool_and(en_periodo_analisis), count(*) FROM dim_fecha "
        "GROUP BY anio ORDER BY anio"
    ).fetchall()
    assert filas == [(2025, True, 365), (2026, False, 365)]


def test_exportacion_convierte_decimales_a_double():
    con = _modelo([{}])
    columnas = _columnas_exportacion(con, "fct_contratos")
    assert 'CAST("valor_analisis" AS DOUBLE) AS "valor_analisis"' in columnas
    assert '"id_contrato"' in columnas
