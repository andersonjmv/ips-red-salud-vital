
# Diagnóstico operativo — Red de Salud Vital (IPS)

## Contexto

Red de Salud Vital es una IPS ambulatoria ficticia que opera en Bogotá,
diseñada para reflejar patrones reales del sistema de salud colombiano.
El proyecto combina dos capas de datos con propósitos distintos:

- **Capa 1 (real)**: dataset oficial de morbilidad atendida en Bogotá,
  identificada por RIPS (Datos Abiertos Bogotá, año 2020, ~1.02M de registros
  agregados), usado como contexto epidemiológico real de la ciudad.
- **Capa 2 (sintética)**: operación interna de la IPS ficticia (pacientes,
  citas, atenciones, facturación y glosas), generada para permitir análisis
  a nivel de caso individual que el dato público agregado no permite.

**Nota metodológica importante**: los patrones de oportunidad de citas por
especialidad y de tasa de glosa por EPS en la Capa 2 fueron parcialmente
diseñados en el generador de datos, informados por conocimiento real del
funcionamiento del sistema de salud colombiano (mayor demora en agenda de
especialistas, mayor escrutinio de aseguradoras en atenciones de alto costo).
Esto se documenta con transparencia: el ejercicio valida que el análisis
recupera correctamente un patrón conocido del dominio, no que se trate de
un descubrimiento inédito. La interacción específica entre EPS, especialidad
y motivo de glosa sí produjo resultados no calculados de antemano.

## Hallazgo 1 (Capa 1 — real): panorama epidemiológico de Bogotá, 2020

- Total de atenciones analizadas: 14,054,292 en 18 localidades, 257 grupos
  diagnósticos, 62 EPS.
- Las 3 principales causas de atención:
  1. Contacto con servicios de salud para investigación y exámenes (10.28%)
  2. Enfermedades hipertensivas (6.77%)
  3. Enfermedades de la cavidad bucal (6.20%)
- Sumando las 3 categorías de "contacto con servicios de salud" (exámenes,
  reproducción, otras circunstancias), casi 1 de cada 5 atenciones (~18%)
  no corresponde a una enfermedad puntual sino a contacto preventivo o
  administrativo con el sistema.
- El 10.23% de las atenciones son de pacientes particulares (sin EPS),
  una categoría separada de las 62 aseguradoras del dataset.
- Una hipótesis plausible es la ausencia de una cultura arraigada de prevención y cuidado bucal, lo que llevaría a que la población busque atención odontológica reactivamente (cuando ya hay dolor o daño) en lugar de preventivamente (chequeos y limpiezas de rutina). Esto es consistente con que la categoría "personas en contacto con servicios de salud para investigación y exámenes" — que sí captura el comportamiento preventivo — representa un porcentaje menor (10.28%) frente a la atención reactiva. Validar esta hipótesis requeriría cruzar el diagnóstico con datos de frecuencia de visitas por paciente, que el dataset agregado actual no permite.

## Hallazgo 2 (Capa 1 — calidad de datos): limitación de la fuente oficial

El archivo público contenía un error de codificación de caracteres en el
nombre de una EPS ("MEDIMÁS" aparecía como "MEDIMµS"), presente en el
archivo original independientemente del encoding de lectura probado
(utf-8-sig, cp1252, latin-1). Se verificó que era un caso aislado (no hay
otras EPS afectadas de las 62 en el dataset) y se corrigió mediante
`CREATE OR REPLACE TABLE ... AS SELECT` (el entorno sandbox de BigQuery no
permite sentencias DML como UPDATE sin cuenta de facturación activa).

## Hallazgo 3 (Capa 2 — sintética): oportunidad de citas por especialidad

| Especialidad               | Espera promedio (días) | Rango |
| -------------------------- | ----------------------- | ----- |
| Odontología               | 28.0                    | 10-45 |
| Ortopedia                  | 18.4                    | 8-30  |
| Medicina Interna           | 12.5                    | 5-20  |
| Ginecología y Obstetricia | 9.0                     | 3-15  |
| Pediatría                 | 6.0                     | 2-10  |
| Medicina General           | 3.0                     | 1-5   |


**Plan de acción gerencial: Mitigación de glosas y conciliación con la aseguradora**
El rechazo de 1 de cada 4 facturas (25%) concentrado en especialidades de alto costo (Ortopedia y Medicina Interna) y con causales dispersas ("servicio no autorizado", "diagnóstico no justificado", "soporte incompleto") evidencia una combinación de desalineación operativa interna y ambigüedad en los criterios contractuales con la EPS.

El plan de intervención se estructura en tres frentes:

1. Control interno: Filtro de pre-radicación y auditoría médica concurrente
   Comité de facturación para alto costo: Implementar una auditoría de concurrencia y pre-radicación para el 100% de las cuentas médicas de Ortopedia y Medicina Interna. Ninguna factura de estas especialidades debe enviarse a cobro sin una lista de chequeo física o digital verificada (anexos completos, pertinencia y autorización vigente).

Control en el punto de admisión/atención: Establecer un punto de control obligatorio donde el personal valide el código de autorización emitido por la EPS antes de habilitar la atención o el procedimiento. (Nota de honestidad de alcance: si bien la mejor práctica de la industria es parametrizar bloqueos automáticos en el software de historia clínica/admisiones para impedir el cierre sin autorización, dicha solución asume la existencia de un sistema de información clínica parametrizable, no verificado en el alcance de los datos actuales de este análisis; de no contarse con dicha infraestructura, la validación se ejecutará mediante protocolo manual y lista de verificación operativa).

Pertinencia médica del registro: Retroalimentar al equipo médico tratante sobre la congruencia del diagnóstico principal y secundarios (CIE-10) respecto a la conducta médica y paraclínicos anexos, mitigando la causal de "diagnóstico no justificado".

2. Gestión contractual y técnica con la EPS (Mesa bilateral)
   Mesa técnica de conciliación extraordinaria: Citar a la dirección médica y de auditoría de la aseguradora para dirimir las causales dispersas. Cuando los motivos no se concentran en una sola falla, usualmente existen interpretaciones divergentes sobre los manuales de glosa aplicados.

Estandarización de canastas y soportes documentales: Formalizar mediante acta bilateral el listado taxativo de soportes mínimos requeridos para radicación en Ortopedia y Medicina Interna, cerrando la brecha de discrecionalidad del auditor externo.

Canal preferencial de autorizaciones: Acordar un flujo de validación ágil para contingencias o autorizaciones pendientes, asegurando que no se generen demoras administrativas que deriven en atenciones no reconocidas.

3. Auditoría de causas raíz y seguimiento continuo
   Realizar seguimiento semanal al porcentaje de glosa inicial versus glosa levantada por motivo y por profesional tratante, identificando omisiones documentales recurrentes antes de cada cierre contable mensual.

## Hallazgo 4 (Capa 2 — interacción no diseñada explícitamente): concentración de glosas

| EPS               | Tasa de glosa | Facturas analizadas |
| ----------------- | ------------- | ------------------- |
| Capital Salud EPS | 24.09%        | 220                 |
| Resto de EPS      | 8.7% - 13.1%  | 214-341 c/u         |

Dentro de Capital Salud EPS, el problema no es uniforme por especialidad:

| Especialidad               | Tasa de glosa (solo Capital Salud) |
| -------------------------- | ---------------------------------- |
| Ortopedia                  | 37.84%                             |
| Medicina Interna           | 33.33%                             |
| Ginecología y Obstetricia | 28.13%                             |
| Odontología               | 19.57%                             |
| Pediatría                 | 17.86%                             |
| Medicina General           | 12.77%                             |

La concentración en Ortopedia y Medicina Interna (las especialidades de
mayor costo base: $130,000 y $120,000 respectivamente) es consistente con
mayor escrutinio de la aseguradora en atenciones de alto valor.

El motivo de glosa está distribuido de forma relativamente pareja entre las
5 categorías (servicio no autorizado, duplicidad de cobro, diagnóstico no
justificado, soporte incompleto, tarifa no pactada) — sin una causa
administrativa dominante, lo que sugiere un patrón sistemático de la EPS
más que un error puntual de proceso identificable y corregible de forma
simple.

**Validación estadística** : se aplicó una prueba de chi-cuadrado de independencia entre EPS y resultado de facturación (glosada/no glosada). El resultado (χ² = 32.27, p = 0.000036, gl = 7) confirma que la diferencia observada es estadísticamente significativa, descartando que se deba al azar.

## Recomendación

1. Fortalecimiento del control interno y filtro de pre-radicación

Implementar auditoría concurrente en servicios de alto costo: Establecer una lista de chequeo obligatoria previa a la radicación que audite el 100% de las cuentas de Ortopedia y Medicina Interna, asegurando la concordancia entre el diagnóstico clínico (CIE-10), la conducta médica adoptada y los anexos de soporte.

Control estricto de autorizaciones en el punto de atención: Blindar el ingreso de pacientes exigiendo la validación y registro de la autorización vigente emitida por la EPS antes de la ejecución del procedimiento. (Nota de honestidad de alcance: se propone idealmente la parametrización de bloqueos automáticos en el software de admisiones/historia clínica; no obstante, esto asume la existencia de un sistema de información clínica configurable que no ha sido verificado en el alcance de los datos actuales de este análisis. De no contar con dicha infraestructura, la validación deberá ejecutarse mediante protocolo operativo y lista de verificación manual).

2. Gestión técnica y contractual con la aseguradora

Instalar una mesa técnica bilateral de conciliación: Convocar a las áreas médicas y de auditoría de la aseguradora para unificar criterios de pertinencia médica y revisar los manuales de glosas aplicados, resolviendo la dispersión de causales de rechazo observada.

Pactar el listado taxativo de soportes por procedimiento: Formalizar mediante acta de acuerdo la documentación mínima requerida para facturar servicios ortopédicos e internistas, reduciendo la discrecionalidad del auditor externo y asegurando canales ágiles para trámites de autorizaciones complejas o atenciones prioritarias.

3. Monitoreo continuo y trazabilidad del ciclo de ingresos

Establecer un tablero de control de glosas: Monitorear periódicamente los indicadores de glosa inicial versus glosa aceptada/levantada por cada causal y profesional tratante, permitiendo retroalimentar al equipo clínico y administrativo antes de los cierres contables mensuales.

## Limitaciones conocidas

- La Capa 1 es un dato agregado (no transaccional): no permite seguimiento
  de un mismo paciente a través de varias atenciones.
- La Capa 1 corresponde únicamente al año 2020 — no se incorporó serie de
  tiempo multi-año por alcance del proyecto; queda como extensión posible.
- Los patrones de oportunidad de citas y tasa de glosa por EPS en la Capa 2
  fueron parcialmente diseñados en el generador de datos sintéticos,
  informados por conocimiento del dominio real — no son un hallazgo
  descubierto de un dataset neutral.
- El motivo de glosa se asignó de forma aleatoria en el generador; su
  distribución pareja es esperada por diseño, no un hallazgo a interpretar.

## Próximos pasos de análisis

- [ ] Cruzar diagnóstico real (Capa 1) con grupo etario y sexo.
- [X] Prueba de significancia estadística (chi-cuadrado) para la diferencia
  de tasa de glosa de Capital Salud vs. el resto (pendiente para la
  fase de Python/estadística del roadmap).
- [ ] Analizar tasa de "no asistió"/cancelación de citas por especialidad,
  cruzada con oportunidad de espera (¿a mayor espera, mayor abandono?).
- [ ] Dashboard ejecutivo consolidando ambas capas.
