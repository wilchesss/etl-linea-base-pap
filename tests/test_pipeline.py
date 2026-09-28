"""Pruebas de reproducibilidad y sanidad básica del pipeline."""

import numpy as np

from src.extract import generar_pagos_sinteticos
from src.transform import calcular_componentes, calibrar_funcion_tradicional


def test_reproducibilidad_misma_semilla():
    """Correr dos veces con la misma semilla debe dar exactamente lo mismo."""
    df1 = generar_pagos_sinteticos(seed=42)
    df2 = generar_pagos_sinteticos(seed=42)
    assert df1.equals(df2)


def test_semillas_distintas_dan_datos_distintos():
    df1 = generar_pagos_sinteticos(seed=42)
    df2 = generar_pagos_sinteticos(seed=99)
    assert not df1["monto_usd"].equals(df2["monto_usd"])


def test_numero_de_pagos_y_regiones():
    df = generar_pagos_sinteticos()
    assert len(df) == 80
    assert set(df["region"].unique()) == {"Norteamerica", "Europa"}
    assert (df["region"].value_counts() == 40).all()


def test_montos_dentro_de_rango_esperado():
    df = generar_pagos_sinteticos()
    assert df["monto_usd"].min() >= 500
    assert df["monto_usd"].max() <= 95_000


def test_transformacion_no_genera_costos_negativos():
    df = generar_pagos_sinteticos()
    df_t = calcular_componentes(df)
    assert (df_t["costo_total_tradicional_usd"] > 0).all()
    assert (df_t["costo_total_cripto_usd"] > 0).all()


def test_ruta_cripto_mas_barata_en_todos_los_montos():
    """Coincide con el hallazgo de la Parte 3 del TCO: no hay monto probado
    donde la ruta tradicional resulte más barata que la ruta cripto."""
    df = generar_pagos_sinteticos()
    df_t = calcular_componentes(df)
    assert (df_t["costo_total_cripto_usd"] < df_t["costo_total_tradicional_usd"]).all()


def test_calibracion_cercana_a_la_reportada_en_tco():
    """El intercepto calibrado debe quedar en un rango razonable del 159.91
    reportado en la Parte 3 (no se espera exactitud porque los componentes
    sintéticos de este repo son un supuesto propio, no el dataset original)."""
    df = generar_pagos_sinteticos()
    df_t = calcular_componentes(df)
    intercepto, pendiente = calibrar_funcion_tradicional(df_t)
    assert 50 < intercepto < 300
    assert 0 < pendiente < 0.03
