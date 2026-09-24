import pandas as pd

url = "https://datosabiertos.bogota.gov.co/dataset/3176e77f-0b57-4d1a-ade5-e85cd7516915/resource/a4df895a-06a0-4f78-abaa-da661d90eac6/download/descargable_rips_2025_180326.csv"

muestra = pd.read_csv(url, nrows=20, sep=None, engine="python", encoding="latin-1")
print(muestra.columns.tolist())
print(muestra.head())