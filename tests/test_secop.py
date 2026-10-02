from proyecto.config import leer_sql
from proyecto.db import conectar
from proyecto.secop import filtro_anio

COLUMNAS_RAW = [
    ":id",
    "id_contrato",
    "referencia_del_contrato",
    "proceso_de_compra",
    "nombre_entidad",
    "nit_entidad",
    "codigo_entidad",
    "departamento",
    "ciudad",
    "orden",
    "sector",
    "rama",
    "entidad_centralizada",
    "estado_contrato",
    "tipo_de_contrato",
    "modalidad_de_contratacion",
    "justificacion_modalidad_de",
    "codigo_de_categoria_principal",
    "objeto_del_contrato",
    "descripcion_del_proceso",
    "duraci_n_del_contrato",
    "fecha_de_firma",
    "fecha_de_inicio_del_contrato",
    "fecha_de_fin_del_contrato",
    "dias_adicionados",
    "tipodocproveedor",
    "documento_proveedor",
    "proveedor_adjudicado",
    "es_grupo",
    "es_pyme",
    "valor_del_contrato",
    "valor_pagado",
    "valor_facturado",
    "valor_pendiente_de_ejecucion",
    "origen_de_los_recursos",
    "presupuesto_general_de_la_nacion_pgn",
    "sistema_general_de_participaciones",
    "sistema_general_de_regal_as",
    "recursos_propios",
    "urlproceso",
    "ultima_actualizacion",
]


def test_filtro_anio():
    f = filtro_anio(2025)
    assert "'2025-01-01T00:00:00'" in f
    assert "'2025-12-31T23:59:59'" in f


def test_stg_tipa_y_normaliza_nulos():
    con = conectar(":memory:")
    columnas = ", ".join(f'"{c}" VARCHAR' for c in COLUMNAS_RAW)
    con.execute(f"CREATE TABLE raw_contratos ({columnas})")
    con.execute(
        """
        INSERT INTO raw_contratos (
            id_contrato, documento_proveedor, departamento, es_pyme,
            fecha_de_firma, valor_del_contrato, urlproceso
        ) VALUES (
            'CO1.PCCNTR.1', 'No Definido', ' Antioquia ', 'Si',
            '2025-03-14T00:00:00.000', '1500000.5',
            '{"url": "https://community.secop.gov.co/x"}'
        )
        """
    )
    con.execute(leer_sql("stg_contratos.sql"))
    fila = con.sql(
        "SELECT documento_proveedor, departamento, proveedor_es_pyme, "
        "fecha_firma::VARCHAR, valor_contrato::DOUBLE, url_proceso "
        "FROM stg_contratos"
    ).fetchone()
    assert fila == (
        None,
        "Antioquia",
        True,
        "2025-03-14",
        1500000.5,
        "https://community.secop.gov.co/x",
    )
