# Sistema de Gestión de Aperturas de Aulas — SIED UCC

**Fecha:** 2026-08-08
**Estado:** Borrador para revisión
**Autores:** Goni (Tecnología Educativa SIED) + Claude

---

## 1. Contexto y problema

El SIED gestiona aperturas de aulas en Canvas LMS con períodos establecidos:

- **Posgrado**: períodos mensuales (ej. `Mensual_Agosto_2026`).
- **Educación**: períodos bimestrales y cuatrimestrales.

Hoy esa gestión vive en tres fuentes desincronizadas que se mantienen a mano:

1. **Planilla de Posgrado** (Google Sheets): panel de control por programa (9 programas, ~321 asignaturas) + listado maestro por período/cohorte + una hoja de datos por programa con orden del plan de estudios, transversalidad, carga horaria y ciclo de fechas. Datos en formatos mezclados (códigos vs. nombres, fechas sueltas en la columna de período).
2. **Planilla de Educación** (Google Sheets): ~5 hojas (una por carrera) con ciclo completo de fechas por asignatura y cohorte (inscripción, cursado, entregas, AFI, cierre, actas). Columnas inconsistentes entre hojas.
3. **Tablero de contratación** (artefacto HTML del jefe de área): pipeline de producción por asignatura (docente, asesor, 8 estados). Guarda en localStorage del navegador de una sola persona, con respaldo JSON manual.

Problemas concretos:

- Los directores de carrera **definen qué abre en cada período**, pero no editan las planillas porque se rompen. El equipo SIED les pregunta por mail/reunión y transcribe.
- El orden de apertura **cambia sobre la marcha** según cómo viene la producción de las aulas (el área va por detrás de las aperturas hasta completar todas las asignaturas), y cada cambio hay que replicarlo a mano en varias fuentes.
- La misma asignatura transversal figura duplicada en varias hojas y puede quedar con estados contradictorios.
- Nadie tiene la foto única de "qué debería abrir y si está listo".

## 2. Objetivo

Un **sistema web único** donde el SIED y los directores de carrera gestionan las aperturas de aulas por período, reemplazando a las planillas y al tablero como **única fuente de verdad**.

El corazón del sistema es el **cruce entre lo planificado y lo real**: para cada período, ver qué asignaturas deberían abrir y en qué estado de producción está cada aula (semáforo), de modo que las decisiones de apertura se tomen viendo la realidad de la producción.

## 3. Usuarios y roles

| Rol | Quién | Qué puede hacer |
|---|---|---|
| **SIED** | Goni, jefe de área, equipo de tecnología educativa | Todo: catálogo, planes, períodos, estados de producción, fechas, usuarios |
| **Director** | Directores/coordinadores de carrera | Ver su(s) carrera(s); decidir y **reordenar el orden de apertura** de sus asignaturas entre períodos; no puede tocar otras carreras, estados de producción ni datos del catálogo |
| **Consulta** | Dirección SIED, administración, otras áreas | Solo lectura: dashboards y listados |

Autenticación con cuenta Google institucional (`@ucc.edu.ar`), sin contraseñas propias.

## 4. Alcances (qué hace)

1. **Planificación de aperturas**: asignar asignaturas a períodos por carrera y cohorte. El orden del plan de estudios (columna ORDEN de las planillas) es el punto de partida; los directores reordenan arrastrando asignaturas entre períodos, viendo el semáforo en tiempo real. Todo cambio queda registrado (quién, cuándo, qué).
2. **Seguimiento de producción**: pipeline por asignatura — sin novedad → contratación → validación docente → contrato → construcción → revisión → maquetación → finalizada — con docente y asesor. Reemplaza el tablero del jefe: mismos estados, pero compartido y persistente.
3. **Cruce y alertas (prioridad nº1)**: por período, cada asignatura planificada con su semáforo:
   - 🟢 Lista (finalizada)
   - 🟡 En riesgo (en maquetación/revisión con la apertura de inscripción cerca)
   - 🔴 No llega (en contratación/construcción con la apertura encima)
   Con avisos de las asignaturas comprometidas del período próximo.
4. **Calendario automático de fechas**: reglas por tipo de período (mensual / bimestral / cuatrimestral) definidas una vez — desplazamientos relativos al inicio de cursado para apertura/cierre de inscripción, fin de cursado/límite de entregas, apertura/vencimiento-cierre de AFI, cierre de asignatura y actas. Al asignar período, el sistema genera todas las fechas; cualquier fecha es editable a mano para excepciones.
5. **Transversales**: una asignatura (código) existe una sola vez en el catálogo y puede pertenecer a varios planes de estudio. Su estado de producción es único y se refleja en todas las carreras. La apertura también es única: como comparten código, **al abrirse queda disponible para todas las carreras a la vez** (Canvas no lo limita). Por eso el sistema:
   - Registra **una sola apertura por código y período**, sin importar desde qué carrera se planificó.
   - **Avisa automáticamente a los directores de las demás carreras** que comparten la asignatura: "va a estar disponible en el período X".
   - Permite que cada director registre si su cohorte **la cursa en esa apertura o más adelante** (para poder informar a los alumnos que, aunque el aula esté visible, no se cursa en ese momento).
6. **Dashboard de consulta**: % de avance por programa/carrera, aperturas del período, asignaturas en riesgo (reemplaza el panel de control de la planilla de Posgrado).
7. **Exportación** de cualquier vista a Excel para quien siga necesitando planilla.
8. **Historial** de cambios (auditoría simple: quién cambió qué y cuándo).

## 5. Límites (qué NO hace)

- **No toca Canvas**: no crea aulas, no configura fechas ni publica vía API. El sistema dice *qué* hay que hacer; ejecutarlo en Canvas sigue siendo tarea del equipo. Posible fase futura.
- **No gestiona inscripciones ni alumnos**: nada de matrícula, listas de estudiantes, Autogestión/SIUCC.
- **No gestiona la contratación en sí** (contratos, legajos, pagos): solo registra la etapa.
- **No reemplaza el flujo de maquetación** (proyecto maquetador IMSCC): son sistemas separados; a futuro el maquetador podría informar estado, pero no es parte de este alcance.
- **Sin sincronización permanente con Google Sheets**: migración inicial única; las planillas quedan congeladas como histórico.

## 6. Modelo de datos (entidades principales)

- **Unidad**: Posgrado, Educación (extensible).
- **Carrera/Programa**: pertenece a una unidad; tiene director(es) asignado(s).
- **Asignatura** (catálogo, clave = código, ej. `EP00461`, `1210131`): nombre, cátedra, carga horaria, docente, asesor, estado de producción. Es transversal si figura en más de un plan de estudios.
- **Plan de estudios**: relación carrera ↔ asignatura con ORDEN (posición en el plan).
- **Cohorte**: por carrera (ej. `COHORTE 2025`, `COHORTE 2026 - 2`, `COHORTE 3`).
- **Período**: por unidad y tipo (mensual/bimestral/cuatrimestral), con fecha de inicio de cursado de referencia (ej. `Mensual_Agosto_2026` → 05/08/2026). El SIED define el calendario de períodos una vez por año.
- **Apertura**: asignatura + período, con sus fechas del ciclo (generadas por regla, editables) y su historial. Es **única por código**: en transversales, la misma apertura aplica a todas las carreras que la comparten. Cada carrera/cohorte asociada registra si **cursa en esa apertura o después**.
- **Regla de fechas**: por tipo de período, desplazamientos en días para cada hito del ciclo.
- **Usuario**: mail institucional, rol, carreras asignadas (para directores).

## 7. Pantallas principales

1. **Tablero de períodos** (SIED): seleccionar período → asignaturas planificadas agrupadas por carrera/cohorte con semáforo, docente, asesor, fechas. Acciones rápidas: cambiar estado, mover de período.
2. **Planificador de carrera** (director): línea de períodos con las asignaturas de su carrera; arrastrar entre períodos; semáforo visible. Las transversales están marcadas: si otra carrera ya la planificó, el director ve el aviso de disponibilidad y decide si su cohorte cursa en esa apertura o después; si la mueve él, se les avisa a los demás.
3. **Ficha de asignatura**: datos completos + historial + en qué planes/períodos está.
4. **Pipeline de producción** (SIED): vista tipo tablero por estado, filtrable por carrera/asesor/docente (reemplaza el artefacto del jefe).
5. **Dashboard** (consulta): métricas de avance y riesgo.
6. **Administración** (SIED): períodos del año, reglas de fechas, usuarios, carreras.

## 8. Arquitectura propuesta

- **Frontend + backend**: Next.js (una sola app).
- **Base de datos**: PostgreSQL gestionado gratuito (Supabase; alternativa Neon).
- **Auth**: Google OAuth restringido al dominio `ucc.edu.ar`, roles en la base.
- **Hosting**: Vercel (gratuito, URL estable, HTTPS). Si la UCC luego ofrece servidor institucional, la app se muda sin cambios de fondo.
- **Migración**: script único que lee los exports de las dos planillas + el JSON de respaldo del tablero, normaliza (códigos como clave, resolución de duplicados y de inconsistencias de columnas) y carga la base. Se corre en un entorno de prueba primero, se valida contra las planillas, y recién ahí en producción.
  - **Períodos de Educación**: la planilla de Posgrado ya tiene el período como dato (`Mensual_Agosto_2026`); la de Educación no — solo tiene fechas por fila (quedó pendiente hacerle esa hoja). La migración crea el calendario de períodos bimestrales/cuatrimestrales y asocia cada fila existente a su período por la fecha de inicio de cursado, dejando reporte de las que no encajen para revisarlas a mano.

## 9. Fases

| Fase | Contenido | Resultado utilizable |
|---|---|---|
| **F1 — Fuente única + cruce** | Base de datos, migración, tablero de períodos con semáforo, edición de estados y aperturas (solo SIED, un solo login compartido o lista blanca simple) | Se dejan de mantener las tres fuentes; el cruce apertura/estado existe |
| **F2 — Directores** | Roles y login por usuario, planificador de carrera con reordenamiento, historial de cambios | Los directores deciden el orden adentro del sistema |
| **F3 — Fechas + consulta** | Reglas de calendario por tipo de período, generación automática de fechas, dashboard de consulta, exportación a Excel | Ciclo completo de fechas sin carga manual; Dirección ve todo sin pedir reportes |

Cada fase queda usable por sí sola.

## 10. Criterios de éxito

1. Una sola fuente de verdad: las planillas y el tablero dejan de actualizarse.
2. Para cualquier período, ver en menos de un minuto qué abre y qué no llega.
3. Los directores hacen sus cambios de orden sin intervención del SIED y sin romper datos.
4. Las fechas del ciclo se generan solas al asignar período (cero carga manual salvo excepciones).
5. Cualquier cambio tiene autor y fecha.

## 11. Supuestos y pendientes a confirmar

- **Confirmado**: Posgrado y Educación funcionan igual — los períodos tienen fechas predefinidas, y en ambos casos la unidad académica (directores) debe decirle al SIED **qué abre en cada período**. Ese es exactamente el flujo que el planificador de carrera resuelve: la decisión se toma dentro del sistema en vez de por mail.
- **Pendiente**: extraer de las planillas las reglas exactas de desplazamiento de fechas por tipo de período (se hará al construir F3; los datos ya están en los exports).
- **Pendiente**: definir con el jefe el momento de migración/congelamiento de su tablero.
- **Pendiente**: lista definitiva de carreras/directores y sus mails institucionales para los accesos de F2.
