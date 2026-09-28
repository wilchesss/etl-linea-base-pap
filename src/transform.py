"""
Etapa de TRANSFORMACIÓN.

Aplica a cada pago la metodología de los 6 componentes de costo definida en la
Entrega 1 (comisión de envío, comisiones intermediarias, comisión de recepción,
diferencial cambiario, costo del tiempo y costo operativo interno), y calcula
el costo total de la ruta tradicional y de la ruta cripto, en USD y en puntos
base (bps), tal como describe la Parte 1 y la Parte 3 del documento de TCO.
"""

import numpy as np
import pandas as pd

# --- Parámetros del modelo (ver hoja "Supuestos" en la salida) ---
COMISION_ENVIO_USD = 45.00
COMISION_INTERMEDIARIA_USD = 35.00
COMISION_RECEPCION_USD = 25.00
COSTO_OPERATIVO_INTERNO_USD = 29.91
TASA_DIARIA_OPORTUNIDAD = 0.00015  # ~5.5% anual, prorrateada por día de tránsito

CRIPTO_PCT_MAX = 0.008   # 0.8% para montos chicos
CRIPTO_PCT_MIN = 0.003   # 0.3% para montos grandes
CRIPTO_PCT_PENDIENTE = 0.005 / 100_000  # declive lineal simple entre los dos extremos
CRIPTO_COMISION_RED_USD = 0.01


def calcular_componentes(df: pd.DataFrame) -> pd.DataFrame:
    d = df.copy()

    # 1. Comisión de envío (banco emisor)
    d["comision_envio_usd"] = COMISION_ENVIO_USD
    # 2. Comisiones intermediarias (bancos corresponsales / red SWIFT)
    d["comision_intermediaria_usd"] = COMISION_INTERMEDIARIA_USD
    # 3. Comisión de recepción (banco del proveedor)
    d["comision_recepcion_usd"] = COMISION_RECEPCION_USD
    # 4. Diferencial cambiario: spread entre el TC que cobra el banco y el de referencia
    d["diferencial_cambiario_usd"] = (
        (d["tipo_cambio_pago"] - d["tipo_cambio_referencia"]) / d["tipo_cambio_referencia"]
    ) * d["monto_usd"]
    # 5. Costo del tiempo: costo de oportunidad del efectivo detenido en tránsito
    d["costo_tiempo_usd"] = d["monto_usd"] * TASA_DIARIA_OPORTUNIDAD * d["dias_proceso_banco"]
    # 6. Costo operativo interno (personal, captura, conciliación)
    d["costo_operativo_interno_usd"] = COSTO_OPERATIVO_INTERNO_USD

    d["costo_total_tradicional_usd"] = (
        d["comision_envio_usd"]
        + d["comision_intermediaria_usd"]
        + d["comision_recepcion_usd"]
        + d["diferencial_cambiario_usd"]
        + d["costo_tiempo_usd"]
        + d["costo_operativo_interno_usd"]
    )
    d["costo_total_tradicional_bps"] = (d["costo_total_tradicional_usd"] / d["monto_usd"]) * 10_000

    # --- Ruta cripto (supuesto propio del equipo, Parte 3 del TCO) ---
    pct = np.clip(CRIPTO_PCT_MAX - d["monto_usd"] * CRIPTO_PCT_PENDIENTE, CRIPTO_PCT_MIN, CRIPTO_PCT_MAX)
    d["pct_conversion_cripto"] = pct
    d["costo_total_cripto_usd"] = d["monto_usd"] * pct + CRIPTO_COMISION_RED_USD
    d["costo_total_cripto_bps"] = (d["costo_total_cripto_usd"] / d["monto_usd"]) * 10_000

    d["ahorro_usd"] = d["costo_total_tradicional_usd"] - d["costo_total_cripto_usd"]
    d["ahorro_bps"] = d["costo_total_tradicional_bps"] - d["costo_total_cripto_bps"]

    return d


def calibrar_funcion_tradicional(df: pd.DataFrame) -> tuple[float, float]:
    """Regresión lineal simple costo_total_usd ~ monto_usd, para reproducir la
    función 'costo fijo + % del monto' que reporta la Parte 3 del TCO
    (calibrada ahí como 159.91 + 0.95%*monto sobre los mismos 80 pagos)."""
    x = df["monto_usd"].to_numpy()
    y = df["costo_total_tradicional_usd"].to_numpy()
    pendiente, intercepto = np.polyfit(x, y, 1)
    return intercepto, pendiente


if __name__ == "__main__":
    df = pd.read_csv("data/01_extraccion_pagos_sinteticos.csv")
    df_t = calcular_componentes(df)
    df_t.to_csv("data/02_transformacion_pagos_con_costos.csv", index=False)

    intercepto, pendiente = calibrar_funcion_tradicional(df_t)
    print(f"Transformados {len(df_t)} pagos -> data/02_transformacion_pagos_con_costos.csv")
    print(f"Función calibrada (ruta tradicional): costo_usd ≈ {intercepto:.2f} + {pendiente*100:.2f}% · monto")
    print("(la Parte 3 del TCO reporta 159.91 + 0.95%·monto sobre esta misma metodología)")
