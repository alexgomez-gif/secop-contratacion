"""Pruebas de las figuras del README, generadas desde reports/consultas/*.csv."""

from proyecto.figuras import generar, numero


def test_numero_formato_colombiano():
    assert numero(51.63) == "51,6"
    assert numero(585950, 0) == "585.950"
    assert numero(27435.7 / 1000) == "27,4"


def test_generar_tres_figuras(tmp_path):
    rutas = generar(tmp_path)
    assert [r.name for r in rutas] == [
        "hallazgo_1_directa_departamentos.png",
        "hallazgo_2_concentracion_entidades.png",
        "hallazgo_3_valor_mensual_modalidad.png",
    ]
    for ruta in rutas:
        assert ruta.read_bytes().startswith(b"\x89PNG")
