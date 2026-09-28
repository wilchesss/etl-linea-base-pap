# ETL — Línea base de costos (proceso reproducible)

Proceso de **extracción, transformación y carga** que genera la línea base de
costos usada para comparar la ruta bancaria tradicional contra la ruta con
criptoactivos, siguiendo la metodología documentada en la **Parte 1** del
documento de Modelo de Costo Total de Propiedad por Ruta (Entrega 2).

## Por qué existe este repo

El proyecto no tiene todavía una empresa cliente real, así que no hay un
histórico de pagos que extraer de un banco o sistema contable. Este proceso
genera un histórico **sintético pero reproducible** que sustituye ese dato
real, aplicando la misma lógica de extracción → transformación → carga que se
usaría si el dato viniera de una fuente real. El día que exista un histórico
real, solo se sustituye la etapa de extracción (`src/extract.py`) por la
lectura del archivo del cliente — el resto del pipeline no cambia, porque
opera sobre el mismo esquema de columnas.

## Estructura del repositorio

```
etl-linea-base/
├── run_pipeline.py          # punto de entrada único (extracción → transformación → carga)
├── src/
│   ├── extract.py           # ETAPA 1: genera 80 pagos sintéticos (40 Norteamérica, 40 Europa), semilla fija
│   ├── transform.py         # ETAPA 2: aplica los 6 componentes de costo (Entrega 1) + ruta cripto
│   └── load.py               # ETAPA 3: escribe el Excel final de 3 hojas
├── tests/
│   └── test_pipeline.py     # pruebas de reproducibilidad y sanidad del cálculo
├── data/                     # salidas generadas (csv/xlsx); no se versiona, se regenera al correr el pipeline
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── README.md                 (este archivo)
```

## Los 6 componentes de costo (ruta tradicional)

Definidos en la Entrega 1 y aplicados en `src/transform.py`:

1. Comisión de envío
2. Comisiones intermediarias (bancos corresponsales)
3. Comisión de recepción
4. Diferencial cambiario (spread entre el tipo de cambio del banco y el de referencia)
5. Costo del tiempo (costo de oportunidad mientras el pago está en tránsito)
6. Costo operativo interno (personal, captura, conciliación)

La ruta cripto usa el supuesto de la Parte 3 del TCO: comisión de conversión
declinante entre 0.3% y 0.8% según el monto, más una comisión de red de
prácticamente cero.

## Reproducibilidad

Todo el proceso usa una **semilla aleatoria fija** (`SEED = 42` en
`src/extract.py`). Correr el pipeline dos veces, en cualquier momento y en
cualquier máquina, produce exactamente el mismo archivo de salida —
verificado en `tests/test_pipeline.py::test_reproducibilidad_misma_semilla`.

**Nota importante:** los componentes de costo aquí implementados (montos
fijos, tasa de oportunidad, etc.) son un supuesto propio de este repo para
poder demostrar el proceso de forma reproducible — no son el dataset exacto
que el equipo usó para calibrar la cifra de 159.91 + 0.95%·monto reportada en
la Parte 3. Al correr este pipeline se obtiene una función calibrada del
mismo orden de magnitud, siguiendo la misma metodología (regresión del costo
total contra el monto). Cuando el equipo comparta el dataset/fórmulas
originales, se puede sustituir directamente en `src/transform.py` sin tocar
`extract.py` ni `load.py`.

## Cómo correrlo

### Opción A — entorno local (Python 3.12)

```bash
python -m venv .venv
source .venv/bin/activate        # En Windows: .venv\Scripts\activate
pip install -r requirements.txt

python run_pipeline.py
python -m pytest tests/ -v
```

### Opción B — Docker (entorno documentado, sin instalar nada localmente)

```bash
docker compose up --build
```

Esto genera los archivos en `data/` (montado como volumen), incluyendo
`data/03_linea_base_reproducible.xlsx` con las 3 hojas: **Supuestos**,
**Detalle** y **Resumen**.

## Salidas

| Archivo | Etapa | Contenido |
|---|---|---|
| `data/01_extraccion_pagos_sinteticos.csv` | Extracción | 80 pagos crudos (id, región, monto, días de proceso, tipos de cambio) |
| `data/02_transformacion_pagos_con_costos.csv` | Transformación | Los mismos pagos + los 6 componentes de costo + costo total (USD y bps) de ambas rutas |
| `data/03_linea_base_reproducible.xlsx` | Carga | Excel de 3 hojas: Supuestos / Detalle / Resumen (agregado por región) |
