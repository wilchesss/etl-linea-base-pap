"""
Punto de entrada único del pipeline ETL: Extracción -> Transformación -> Carga.

Uso:
    python run_pipeline.py

Reproducibilidad: usa una semilla aleatoria fija (ver src/extract.py), por lo
que correrlo dos veces produce exactamente el mismo archivo de salida.
"""

import os

from src.extract import generar_pagos_sinteticos
from src.load import guardar_excel
from src.transform import calcular_componentes, calibrar_funcion_tradicional

DATA_DIR = "data"


def main():
    os.makedirs(DATA_DIR, exist_ok=True)

    # 1. Extracción
    df = generar_pagos_sinteticos()
    ruta_extraccion = f"{DATA_DIR}/01_extraccion_pagos_sinteticos.csv"
    df.to_csv(ruta_extraccion, index=False)
    print(f"[1/3] Extracción -> {ruta_extraccion} ({len(df)} pagos)")

    # 2. Transformación
    df_t = calcular_componentes(df)
    ruta_transformacion = f"{DATA_DIR}/02_transformacion_pagos_con_costos.csv"
    df_t.to_csv(ruta_transformacion, index=False)
    intercepto, pendiente = calibrar_funcion_tradicional(df_t)
    print(f"[2/3] Transformación -> {ruta_transformacion}")
    print(f"      Función calibrada (ruta tradicional): {intercepto:.2f} + {pendiente*100:.2f}%·monto")

    # 3. Carga
    ruta_final = f"{DATA_DIR}/03_linea_base_reproducible.xlsx"
    guardar_excel(df_t, intercepto, pendiente, ruta_final)
    print(f"[3/3] Carga -> {ruta_final} (hojas: Supuestos, Detalle, Resumen)")

    print("\nPipeline completo y reproducible.")


if __name__ == "__main__":
    main()
