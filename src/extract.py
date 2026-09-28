"""
Etapa de EXTRACCIÓN.

No existe todavía un histórico de pagos real de una empresa cliente, por lo que
esta etapa genera un histórico sintético de pagos internacionales usando una
semilla aleatoria fija. La semilla fija es lo que garantiza reproducibilidad:
correr este script de nuevo, en cualquier momento y en cualquier máquina,
produce exactamente el mismo resultado.

Cuando exista un histórico real, esta es la ÚNICA etapa que se sustituye
(por la lectura del archivo real del cliente) — transform.py y load.py no
cambian, porque ambos operan sobre el mismo esquema de columnas.
"""

import numpy as np
import pandas as pd

SEED = 42
N_POR_REGION = 40
REGIONES = ("Norteamerica", "Europa")

COLUMNAS = [
    "id_pago", "region", "monto_usd", "dias_proceso_banco",
    "tipo_cambio_pago", "tipo_cambio_referencia",
]


def generar_pagos_sinteticos(seed: int = SEED, n_por_region: int = N_POR_REGION) -> pd.DataFrame:
    """Genera `n_por_region` pagos por cada región, con distribución log-normal
    de montos (realista para pagos B2B: muchos montos chicos, pocos grandes)."""
    rng = np.random.default_rng(seed)

    filas = []
    id_pago = 1
    for region in REGIONES:
        # Montos entre ~500 y ~90,000 USD, concentrados en el rango medio-bajo.
        montos = rng.lognormal(mean=8.2, sigma=1.1, size=n_por_region)
        montos = np.clip(montos, 500, 95_000).round(2)

        # Días que tarda el banco en procesar el pago (afecta el costo del tiempo).
        dias_proceso = rng.integers(low=1, high=6, size=n_por_region)

        # Tipo de cambio USD/MXN al momento de pagar vs. el de referencia (Banxico)
        # del mismo día: la diferencia es el "diferencial cambiario".
        tc_referencia = rng.normal(loc=18.50, scale=0.35, size=n_por_region).round(4)
        # El banco siempre cobra un poco más caro que el de referencia.
        tc_pago = (tc_referencia * (1 + rng.uniform(0.005, 0.02, size=n_por_region))).round(4)

        for i in range(n_por_region):
            filas.append({
                "id_pago": id_pago,
                "region": region,
                "monto_usd": float(montos[i]),
                "dias_proceso_banco": int(dias_proceso[i]),
                "tipo_cambio_pago": float(tc_pago[i]),
                "tipo_cambio_referencia": float(tc_referencia[i]),
            })
            id_pago += 1

    df = pd.DataFrame(filas, columns=COLUMNAS)
    return df


if __name__ == "__main__":
    df = generar_pagos_sinteticos()
    df.to_csv("data/01_extraccion_pagos_sinteticos.csv", index=False)
    print(f"Generados {len(df)} pagos sintéticos (seed={SEED}) -> data/01_extraccion_pagos_sinteticos.csv")
