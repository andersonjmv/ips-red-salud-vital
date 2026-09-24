"""
Carga los 4 CSVs de data/raw/ (pacientes, citas, atenciones,
facturacion_glosas) a sus respectivas tablas en BigQuery.

"""

from google.cloud import bigquery
import pandas as pd

PROJECT_ID = "rutaxpress-analytics"  
DATASET_ID = "ips_red_salud"

TABLAS = {
    "pacientes": "data/raw/pacientes.csv",
    "citas": "data/raw/citas.csv",
    "atenciones": "data/raw/atenciones.csv",
    "facturacion_glosas": "data/raw/facturacion_glosas.csv",
}

client = bigquery.Client(project=PROJECT_ID)

for tabla, path_csv in TABLAS.items():
    print(f"\nCargando {tabla} desde {path_csv}...")
    df = pd.read_csv(path_csv)

    table_ref = f"{PROJECT_ID}.{DATASET_ID}.{tabla}"
    job_config = bigquery.LoadJobConfig(
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
    )

    load_job = client.load_table_from_dataframe(df, table_ref, job_config=job_config)
    load_job.result()

    tabla_info = client.get_table(table_ref)
    print(f"  -> {tabla_info.num_rows} filas cargadas en {table_ref}")

print("\nTodas las tablas cargadas correctamente.")