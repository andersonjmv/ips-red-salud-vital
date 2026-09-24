import pandas as pd
from scipy.stats import chi2_contingency
from google.cloud import bigquery

client = bigquery.Client(project="rutaxpress-analytics")  # ajusta tu Project ID

query = """
SELECT
    eps,
    CASE WHEN valor_glosado > 0 THEN 'con_glosa' ELSE 'sin_glosa' END AS resultado
FROM ips_red_salud.facturacion_glosas
WHERE eps != 'PARTICULAR'
"""

df = client.query(query).to_dataframe()

# Tabla de contingencia: EPS x resultado (con_glosa / sin_glosa)
tabla_contingencia = pd.crosstab(df["eps"], df["resultado"])
print(tabla_contingencia)

chi2, p_valor, gl, esperado = chi2_contingency(tabla_contingencia)

print(f"\nEstadístico chi-cuadrado: {chi2:.2f}")
print(f"P-valor: {p_valor:.6f}")
print(f"Grados de libertad: {gl}")

if p_valor < 0.05:
    print("\n✅ La diferencia entre EPS es estadísticamente significativa (p < 0.05).")
else:
    print("\n⚠️ No hay evidencia suficiente para afirmar que la diferencia es real (p >= 0.05).")