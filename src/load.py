"""
Etapa de CARGA.

Guarda el resultado final en un Excel de tres hojas, tal como describe la
Parte 1 del TCO:
  - Supuestos: todos los parámetros del modelo.
  - Detalle: los pagos individuales con sus componentes de costo.
  - Resumen: totales agregados por región (Norteamérica y Europa).
"""

import pandas as pd

from src import extract, transform as tr


def construir_hoja_supuestos(intercepto: float, pendiente: float) -> pd.DataFrame:
    filas = [
        ("seed", extract.SEED, "Semilla aleatoria fija (reproducibilidad)"),
        ("n_pagos_por_region", 40, "Pagos sintéticos por región (80 en total)"),
        ("comision_envio_usd", tr.COMISION_ENVIO_USD, "Componente 1: comisión de envío"),
        ("comision_intermediaria_usd", tr.COMISION_INTERMEDIARIA_USD, "Componente 2: comisiones intermediarias"),
        ("comision_recepcion_usd", tr.COMISION_RECEPCION_USD, "Componente 3: comisión de recepción"),
        ("costo_operativo_interno_usd", tr.COSTO_OPERATIVO_INTERNO_USD, "Componente 6: costo operativo interno"),
        ("tasa_diaria_oportunidad", tr.TASA_DIARIA_OPORTUNIDAD, "Componente 5: costo del tiempo (tasa diaria)"),
        ("cripto_pct_max", tr.CRIPTO_PCT_MAX, "Ruta cripto: % de conversión máximo (montos chicos)"),
        ("cripto_pct_min", tr.CRIPTO_PCT_MIN, "Ruta cripto: % de conversión mínimo (montos grandes)"),
        ("cripto_comision_red_usd", tr.CRIPTO_COMISION_RED_USD, "Ruta cripto: comisión de red"),
        ("funcion_calibrada_intercepto_usd", round(intercepto, 2), "Costo fijo calibrado (ruta tradicional)"),
        ("funcion_calibrada_pendiente_pct", round(pendiente * 100, 4), "% variable calibrado (ruta tradicional)"),
        ("referencia_tco", "159.91 + 0.95%·monto", "Función reportada en TCO Parte 3 (misma metodología)"),
    ]
    return pd.DataFrame(filas, columns=["parametro", "valor", "descripcion"])


def construir_hoja_resumen(df_t: pd.DataFrame) -> pd.DataFrame:
    resumen = (
        df_t.groupby("region")
        .agg(
            n_pagos=("id_pago", "count"),
            monto_total_usd=("monto_usd", "sum"),
            costo_total_tradicional_usd=("costo_total_tradicional_usd", "sum"),
            costo_total_cripto_usd=("costo_total_cripto_usd", "sum"),
            ahorro_total_usd=("ahorro_usd", "sum"),
            costo_promedio_tradicional_bps=("costo_total_tradicional_bps", "mean"),
            costo_promedio_cripto_bps=("costo_total_cripto_bps", "mean"),
        )
        .reset_index()
        .round(2)
    )
    return resumen


def guardar_excel(df_t: pd.DataFrame, intercepto: float, pendiente: float, ruta_salida: str):
    supuestos = construir_hoja_supuestos(intercepto, pendiente)
    resumen = construir_hoja_resumen(df_t)

    with pd.ExcelWriter(ruta_salida, engine="openpyxl") as writer:
        supuestos.to_excel(writer, sheet_name="Supuestos", index=False)
        df_t.to_excel(writer, sheet_name="Detalle", index=False)
        resumen.to_excel(writer, sheet_name="Resumen", index=False)


if __name__ == "__main__":
    # Ejecutar como módulo desde la raíz del repo: python -m src.load
    df_t = pd.read_csv("data/02_transformacion_pagos_con_costos.csv")
    intercepto, pendiente = tr.calibrar_funcion_tradicional(df_t)
    ruta_salida = "data/03_linea_base_reproducible.xlsx"
    guardar_excel(df_t, intercepto, pendiente, ruta_salida)
    print(f"Cargado -> {ruta_salida} (hojas: Supuestos, Detalle, Resumen)")
