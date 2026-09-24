"""
Descarga el dataset real de morbilidad RIPS de Bogotá (Datos Abiertos),
lo limpia y lo carga a la tabla ips_red_salud.morbilidad_bogota_real.

"""

import pandas as pd
from google.cloud import bigquery

PROJECT_ID = "rutaxpress-analytics"  
DATASET_ID = "ips_red_salud"
TABLE_ID = "morbilidad_bogota_real"

URL = "https://datosabiertos.bogota.gov.co/dataset/3176e77f-0b57-4d1a-ade5-e85cd7516915/resource/a4df895a-06a0-4f78-abaa-da661d90eac6/download/descargable_rips_2025_180326.csv"

# Mapeo de nombres originales -> nombres del esquema que definimos
RENOMBRAR_COLUMNAS = {
    "ANO": "ano",
    "Sexo_Gen": "sexo",
    "Edad_Quiquenio": "grupo_edad",
    "tipo_usuario_afiliacion": "tipo_afiliacion",
    "prestador_localidad_codigo": "localidad_codigo",
    "prestador_localidad_nombre": "localidad_nombre",
    "tipo_atencion_nombre": "tipo_atencion",
    "dxPrincipal_agrupacion1_nombre": "diagnostico_grupo1",
    "dxPrincipal_agrupacion2_nombre": "diagnostico_grupo2",
    "administradora_consolidada": "eps",
    "sum_atenciones": "total_atenciones",
}


def main():
    print("Descargando y leyendo el CSV (puede tardar 1-2 minutos por el tamaño del archivo)...")

    df = pd.read_csv(URL, sep=None, engine="python", encoding="latin-1")
    print(f"Filas leídas: {len(df)}")

    # Renombrar columnas al esquema en español
    df = df.rename(columns=RENOMBRAR_COLUMNAS)

    # Asegurar que total_atenciones sea numérico limpio antes de cargar
    df["total_atenciones"] = pd.to_numeric(df["total_atenciones"], errors="coerce")
    filas_con_error = df["total_atenciones"].isna().sum()
    if filas_con_error > 0:
        print(f"Aviso: {filas_con_error} filas con total_atenciones no numérico, se eliminan.")
        df = df.dropna(subset=["total_atenciones"])
    df["total_atenciones"] = df["total_atenciones"].astype(int)

    # Cargar a BigQuery
    client = bigquery.Client(project=PROJECT_ID)
    table_ref = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"

    job_config = bigquery.LoadJobConfig(
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
    )

    print(f"Cargando {len(df)} filas a {table_ref}...")
    load_job = client.load_table_from_dataframe(df, table_ref, job_config=job_config)
    load_job.result()

    tabla = client.get_table(table_ref)
    print(f"\nListo. La tabla {table_ref} ahora tiene {tabla.num_rows} filas.")


if __name__ == "__main__":
    main()