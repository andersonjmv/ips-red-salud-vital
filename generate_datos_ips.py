"""
Genera los datos sintéticos de operación interna de "Red de Salud Vital"
(la IPS ficticia): pacientes, citas, atenciones y facturación/glosas.

Diseñado para conectar temáticamente con los hallazgos reales de la Capa 1
(morbilidad de Bogotá): las especialidades y diagnósticos reflejan las
causas de atención más frecuentes que ya se encontraron en el dato real.

Incluye inconsistencias y patrones INYECTADOS A PROPÓSITO:
- Oportunidad de citas (días de espera) que varía por especialidad
- Una EPS con tasa de glosa desproporcionadamente alta (causa raíz a investigar)
- Glosas más frecuentes en atenciones de mayor costo
- Datos faltantes/inconsistentes típicos de un sistema real (localidad nula,
  motivo de glosa vacío en algunos casos, fechas de cita canceladas sin
  fecha de atención)

Genera 4 CSVs en data/raw/:
    pacientes.csv, citas.csv, atenciones.csv, facturacion_glosas.csv
"""

import random
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
from faker import Faker

fake = Faker("es_CO")
random.seed(42)
np.random.seed(42)
Faker.seed(42)

OUTPUT_DIR = "data/raw"

N_PACIENTES = 600
N_CITAS = 3000

LOCALIDADES_BOGOTA = [
    "Usaquén", "Chapinero", "Santa Fe", "San Cristóbal", "Usme",
    "Tunjuelito", "Bosa", "Kennedy", "Fontibón", "Engativá",
    "Suba", "Barrios Unidos", "Teusaquillo", "Los Mártires",
    "Antonio Nariño", "Puente Aranda", "La Candelaria", "Rafael Uribe Uribe",
]

# EPS reales tomadas de la Capa 1 (dataset real de morbilidad)
EPS_LIST = [
    "E.P.S. SANITAS", "FAMISANAR E.P.S. LTDA", "NUEVA EPS S.A.",
    "COMPENSAR E.P.S.", "CAPITAL SALUD E.P.S.", "SALUD TOTAL S.A.",
    "MEDIMAS EPS S.A.S.", "EPS Y MEDICINA PREPAGADA SURAMERICANA S.A.",
    "PARTICULAR",
]

# Especialidades, con su código CUPS de consulta representativo (simplificado)
# y el diagnóstico_grupo1 real de la Capa 1 con el que conecta temáticamente
ESPECIALIDADES = {
    "Medicina General": {
        "cups": "890201",
        "diagnosticos": [
            "Sintomas Y Signos Generales",
            "Infecciones Agudas De Las Vias Respiratorias Superiores",
            "Asignacion Provisoria De Nuevas Afecciones De Etiologia Incierta",
        ],
        "oportunidad_dias_min": 1, "oportunidad_dias_max": 5,
    },
    "Odontología": {
        "cups": "890281",
        "diagnosticos": [
            "Enfermedades De La Cavidad Bucal De Las Glandulas Salivales Y De Los Maxilares",
        ],
        "oportunidad_dias_min": 10, "oportunidad_dias_max": 45,
    },
    "Medicina Interna": {
        "cups": "890301",
        "diagnosticos": ["Enfermedades Hipertensivas", "Diabetes Mellitus", "Trastornos De La Glandula Tiroides"],
        "oportunidad_dias_min": 5, "oportunidad_dias_max": 20,
    },
    "Ginecología y Obstetricia": {
        "cups": "890302",
        "diagnosticos": [
            "Personas En Contacto Con Los Servicios De Salud En Circunstancias Relacionadas Con La Reproduccion",
        ],
        "oportunidad_dias_min": 3, "oportunidad_dias_max": 15,
    },
    "Pediatría": {
        "cups": "890303",
        "diagnosticos": ["Infecciones Agudas De Las Vias Respiratorias Superiores", "Sintomas Y Signos Generales"],
        "oportunidad_dias_min": 2, "oportunidad_dias_max": 10,
    },
    "Ortopedia": {
        "cups": "890304",
        "diagnosticos": ["Otras Dorsopatias", "Trastornos Episodicos Y Paroxisticos"],
        "oportunidad_dias_min": 8, "oportunidad_dias_max": 30,
    },
}

# EPS con tasa de glosa desproporcionadamente alta — la "causa raíz" a descubrir,
# igual que hicimos con SU+ Pay en Soy Holística
EPS_PROBLEMATICA = "CAPITAL SALUD E.P.S."


def generar_pacientes():
    pacientes = []
    for pid in range(1, N_PACIENTES + 1):
        pacientes.append({
            "paciente_id": pid,
            "sexo": random.choice(["Mujer", "Hombre"]),
            "grupo_edad": random.choice([
                "00-04", "05-09", "10-14", "15-19", "20-24", "25-29",
                "30-34", "35-39", "40-44", "45-49", "50-54", "55-59",
                "60-64", "65-69", "70-74", "75-79", "80 Y MAS",
            ]),
            # ~3% sin localidad registrada, inconsistencia real de sistemas administrativos
            "localidad": random.choice(LOCALIDADES_BOGOTA) if random.random() > 0.03 else None,
            "eps": random.choice(EPS_LIST),
            "fecha_afiliacion": fake.date_between(start_date="-5y", end_date="-2m"),
        })
    return pd.DataFrame(pacientes)


def generar_citas(pacientes_df):
    citas = []
    paciente_ids = pacientes_df["paciente_id"].tolist()
    inicio = datetime.now() - timedelta(days=365)
    especialidades = list(ESPECIALIDADES.keys())

    for cid in range(1, N_CITAS + 1):
        especialidad = random.choice(especialidades)
        config = ESPECIALIDADES[especialidad]

        fecha_solicitud = inicio + timedelta(days=random.randint(0, 340))
        dias_espera = random.randint(config["oportunidad_dias_min"], config["oportunidad_dias_max"])
        fecha_cita_programada = fecha_solicitud + timedelta(days=dias_espera)

        # Distribución de estados: la mayoría se atiende, algunas se cancelan o no asisten
        estado = random.choices(
            ["atendida", "cancelada", "no_asistio"], weights=[0.78, 0.12, 0.10]
        )[0]

        citas.append({
            "cita_id": cid,
            "paciente_id": random.choice(paciente_ids),
            "especialidad": especialidad,
            "fecha_solicitud": fecha_solicitud,
            "fecha_cita_programada": fecha_cita_programada,
            "dias_espera_oportunidad": dias_espera,
            "estado": estado,
        })
    return pd.DataFrame(citas)


def generar_atenciones(citas_df):
    atenciones = []
    aid = 1

    for _, cita in citas_df.iterrows():
        if cita["estado"] != "atendida":
            continue  # solo las citas efectivamente atendidas generan una atención

        config = ESPECIALIDADES[cita["especialidad"]]
        diagnostico = random.choice(config["diagnosticos"])

        # Costo con variación realista por especialidad
        costo_base = {
            "Medicina General": 45000, "Odontología": 85000, "Medicina Interna": 120000,
            "Ginecología y Obstetricia": 110000, "Pediatría": 60000, "Ortopedia": 130000,
        }[cita["especialidad"]]
        costo = round(costo_base * random.uniform(0.7, 2.2), -2)

        atenciones.append({
            "atencion_id": aid,
            "cita_id": cita["cita_id"],
            "paciente_id": cita["paciente_id"],
            "especialidad": cita["especialidad"],
            "cups": config["cups"],
            "diagnostico": diagnostico,
            "fecha_atencion": cita["fecha_cita_programada"],
            "costo_atencion": costo,
        })
        aid += 1
    return pd.DataFrame(atenciones)


def generar_facturacion_glosas(atenciones_df, pacientes_df):
    facturas = []
    fid = 1
    eps_por_paciente = dict(zip(pacientes_df["paciente_id"], pacientes_df["eps"]))

    motivos_glosa = [
        "soporte_incompleto", "tarifa_no_pactada", "diagnostico_no_justificado",
        "servicio_no_autorizado", "duplicidad_de_cobro",
    ]

    for _, atencion in atenciones_df.iterrows():
        eps = eps_por_paciente.get(atencion["paciente_id"], "PARTICULAR")
        valor_facturado = atencion["costo_atencion"]

        # PARTICULAR nunca tiene glosa (paga directo, no hay reclamación a aseguradora)
        if eps == "PARTICULAR":
            facturas.append({
                "factura_id": fid, "atencion_id": atencion["atencion_id"], "eps": eps,
                "valor_facturado": valor_facturado, "valor_glosado": 0,
                "motivo_glosa": None, "estado_factura": "pagada",
            })
            fid += 1
            continue

        # Probabilidad base de glosa, más alta para la EPS "problemática"
        # y creciente con el valor facturado (mismo patrón que Soy Holística)
        prob_base = 0.35 if eps == EPS_PROBLEMATICA else 0.15
        factor_valor = min(valor_facturado / 200000, 1.5)  # a mayor valor, mayor probabilidad
        prob_glosa = min(prob_base * factor_valor, 0.9)

        tiene_glosa = random.random() < prob_glosa

        if tiene_glosa:
            # Glosa total o parcial
            es_total = random.random() < 0.4
            valor_glosado = valor_facturado if es_total else round(valor_facturado * random.uniform(0.2, 0.7), -2)
            motivo = random.choice(motivos_glosa)
            estado = "glosada_total" if es_total else "glosada_parcial"
        else:
            valor_glosado = 0
            motivo = None
            estado = "pagada"

        facturas.append({
            "factura_id": fid, "atencion_id": atencion["atencion_id"], "eps": eps,
            "valor_facturado": valor_facturado, "valor_glosado": valor_glosado,
            "motivo_glosa": motivo, "estado_factura": estado,
        })
        fid += 1

    return pd.DataFrame(facturas)


def main():
    import os
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("Generando pacientes...")
    pacientes_df = generar_pacientes()
    print("Generando citas...")
    citas_df = generar_citas(pacientes_df)
    print("Generando atenciones...")
    atenciones_df = generar_atenciones(citas_df)
    print("Generando facturación y glosas...")
    facturas_df = generar_facturacion_glosas(atenciones_df, pacientes_df)

    pacientes_df.to_csv(f"{OUTPUT_DIR}/pacientes.csv", index=False)
    citas_df.to_csv(f"{OUTPUT_DIR}/citas.csv", index=False)
    atenciones_df.to_csv(f"{OUTPUT_DIR}/atenciones.csv", index=False)
    facturas_df.to_csv(f"{OUTPUT_DIR}/facturacion_glosas.csv", index=False)

    print(f"\nListo. Archivos generados en {OUTPUT_DIR}/:")
    print(f"- pacientes.csv          ({len(pacientes_df)} filas)")
    print(f"- citas.csv              ({len(citas_df)} filas)")
    print(f"- atenciones.csv         ({len(atenciones_df)} filas)")
    print(f"- facturacion_glosas.csv ({len(facturas_df)} filas)")

    tasa_glosa_global = (facturas_df["valor_glosado"] > 0).mean() * 100
    print(f"\nTasa de glosa global (referencia, no la reveles antes de investigarla): {tasa_glosa_global:.1f}%")


if __name__ == "__main__":
    main()