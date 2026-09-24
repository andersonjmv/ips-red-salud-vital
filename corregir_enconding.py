import pandas as pd

URL = "https://datosabiertos.bogota.gov.co/dataset/3176e77f-0b57-4d1a-ade5-e85cd7516915/resource/a4df895a-06a0-4f78-abaa-da661d90eac6/download/descargable_rips_2025_180326.csv"

for enc in ["utf-8-sig", "cp1252", "latin-1"]:
    try:
        muestra = pd.read_csv(URL, nrows=50, sep=None, engine="python", encoding=enc)
        print(f"--- Probando encoding: {enc} ---")
        print(muestra["administradora_consolidada"].unique()[:10])
    except Exception as e:
        print(f"{enc} falló: {e}")