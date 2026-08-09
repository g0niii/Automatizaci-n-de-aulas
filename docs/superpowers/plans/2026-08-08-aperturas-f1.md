# Sistema de Aperturas — Fase 1: Fuente única + Tablero con semáforo

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Base de datos única con los datos migrados de las dos planillas y el tablero del jefe, más una web (solo equipo SIED) que muestra por período qué asignaturas abren y su semáforo de producción, con edición de estados.

**Architecture:** App Next.js (App Router, server components + server actions) con Prisma sobre SQLite en desarrollo (se cambia a Postgres/Supabase al desplegar — un cambio de una línea + migración). La lógica pura (semáforo, normalización de estados/fechas, inferencia de períodos, parsers de migración) vive en `src/lib/` con tests de vitest. La migración es un script CLI que lee los .xlsx exportados de Google Sheets y el JSON del tablero, y deja un reporte de lo que no pudo mapear.

**Tech Stack:** Next.js 15 (TypeScript, App Router), Prisma, SQLite (dev) → Supabase Postgres (deploy), vitest, SheetJS (`xlsx`) para parsear los exports.

**Spec:** `docs/superpowers/specs/2026-08-08-gestion-aperturas-design.md` (en el repo de maquetación).

## Global Constraints

- Toda la interfaz en **español** (es-AR). Fechas mostradas como `dd/mm/aaaa`.
- Proyecto NUEVO en `C:\Users\g0nii\Desktop\sistema-aperturas` con su propio repo git — NO dentro del repo de maquetación.
- Estados del pipeline (exactos, en este orden): `sin_novedad`, `contratacion`, `validacion_docente`, `contrato`, `construccion`, `revision`, `maquetacion`, `finalizacion`.
- Unidades: `posgrado` y `educacion`. Tipos de período: `mensual`, `bimestral`, `cuatrimestral`.
- La clave de asignatura es el **código** (`EP01392`, `1210131`); una asignatura existe UNA vez aunque esté en varias carreras (transversales).
- Una apertura es única por `(asignaturaCodigo, periodoId)`.
- Semáforo: `verde` = finalizacion; `amarillo` = maquetacion/revision con inscripción a ≤30 días; `rojo` = estados anteriores a maquetacion con inscripción a ≤30 días; `gris` = sin fecha o inscripción a >30 días (sin riesgo todavía).
- Sin dependencias más allá de: `next react react-dom @prisma/client xlsx` y dev: `prisma vitest typescript @types/*`.
- Node 18+. Comandos npm (funcionan igual en Git Bash y PowerShell).

**Prerrequisitos de datos (los provee Goni, no bloquean las tareas 1-8):** en `sistema-aperturas/migracion/input/` poner `posgrado.xlsx` y `educacion.xlsx` (Archivo → Descargar → Microsoft Excel desde cada Google Sheet) y `tablero.json` (respaldo exportado del artefacto del jefe).

---

### Task 1: Scaffold del proyecto

**Files:**
- Create: `C:\Users\g0nii\Desktop\sistema-aperturas\` (proyecto Next.js completo)
- Create: `vitest.config.ts`
- Modify: `package.json` (scripts)

**Interfaces:**
- Produces: proyecto compilable con `npm run dev`, tests corren con `npm test`.

- [ ] **Step 1: Crear la app**

```bash
cd /c/Users/g0nii/Desktop
npx create-next-app@latest sistema-aperturas --ts --app --no-tailwind --no-eslint --src-dir --import-alias "@/*" --use-npm --yes
cd sistema-aperturas
```

Expected: carpeta creada con `src/app/`, `git init` ya hecho por create-next-app (verificar con `git status`; si no, `git init`).

- [ ] **Step 2: Instalar dependencias de datos y test**

```bash
npm install @prisma/client xlsx
npm install -D prisma vitest
```

- [ ] **Step 3: Configurar vitest**

Crear `vitest.config.ts`:

```ts
import { defineConfig } from 'vitest/config'
import path from 'path'

export default defineConfig({
  test: { environment: 'node' },
  resolve: { alias: { '@': path.resolve(__dirname, 'src') } },
})
```

En `package.json`, agregar a `"scripts"`:

```json
"test": "vitest run",
"migrar": "tsx migracion/migrar.ts"
```

(`tsx` se instala en la Task 9; el script queda declarado ya.)

- [ ] **Step 4: Verificar que compila**

```bash
npm run build
```

Expected: `✓ Compiled successfully` (o similar, sin errores).

- [ ] **Step 5: Commit**

```bash
git add -A && git commit -m "chore: scaffold Next.js + vitest para sistema de aperturas"
```

---

### Task 2: Esquema Prisma y cliente

**Files:**
- Create: `prisma/schema.prisma`
- Create: `src/lib/db.ts`
- Create: `src/lib/estados.ts`
- Create: `.env` (DATABASE_URL)
- Test: `tests/db.test.ts`

**Interfaces:**
- Produces: `prisma` (PrismaClient singleton) desde `@/lib/db`; constantes `ESTADOS`, `ESTADO_LABELS`, tipo `Estado` desde `@/lib/estados`. Modelos: `Unidad`, `Carrera`, `Asignatura`, `PlanItem`, `Cohorte`, `Periodo`, `Apertura`, `AperturaCohorte` (campos abajo — los consumen las tareas 9-13).

- [ ] **Step 1: Escribir el esquema**

`prisma/schema.prisma`:

```prisma
datasource db {
  provider = "sqlite"
  url      = env("DATABASE_URL")
}

generator client {
  provider = "prisma-client-js"
}

model Unidad {
  id       String    @id // "posgrado" | "educacion"
  nombre   String
  carreras Carrera[]
  periodos Periodo[]
}

model Carrera {
  id        Int        @id @default(autoincrement())
  nombre    String
  unidadId  String
  unidad    Unidad     @relation(fields: [unidadId], references: [id])
  planItems PlanItem[]
  cohortes  Cohorte[]
  @@unique([unidadId, nombre])
}

model Asignatura {
  codigo       String     @id
  nombre       String
  catedra      String?
  cargaHoraria Int?
  docente      String?
  asesor       String?
  estado       String     @default("sin_novedad")
  planItems    PlanItem[]
  aperturas    Apertura[]
}

model PlanItem {
  id               Int        @id @default(autoincrement())
  carreraId        Int
  carrera          Carrera    @relation(fields: [carreraId], references: [id])
  asignaturaCodigo String
  asignatura       Asignatura @relation(fields: [asignaturaCodigo], references: [codigo])
  orden            Int?
  @@unique([carreraId, asignaturaCodigo])
}

model Cohorte {
  id        Int               @id @default(autoincrement())
  nombre    String
  carreraId Int
  carrera   Carrera           @relation(fields: [carreraId], references: [id])
  aperturas AperturaCohorte[]
  @@unique([carreraId, nombre])
}

model Periodo {
  id                  Int        @id @default(autoincrement())
  nombre              String
  tipo                String // mensual | bimestral | cuatrimestral
  unidadId            String
  unidad              Unidad     @relation(fields: [unidadId], references: [id])
  inicioCursado       DateTime
  aperturaInscripcion DateTime?
  cierreInscripcion   DateTime?
  aperturas           Apertura[]
  @@unique([unidadId, nombre])
}

model Apertura {
  id                  Int               @id @default(autoincrement())
  asignaturaCodigo    String
  asignatura          Asignatura        @relation(fields: [asignaturaCodigo], references: [codigo])
  periodoId           Int
  periodo             Periodo           @relation(fields: [periodoId], references: [id])
  inicioCursado       DateTime?
  aperturaInscripcion DateTime?
  cierreInscripcion   DateTime?
  finCursado          DateTime?
  aperturaAfi         DateTime?
  cierreAfi           DateTime?
  cierreAsignatura    DateTime?
  actas               DateTime?
  cohortes            AperturaCohorte[]
  @@unique([asignaturaCodigo, periodoId])
}

model AperturaCohorte {
  id                  Int      @id @default(autoincrement())
  aperturaId          Int
  apertura            Apertura @relation(fields: [aperturaId], references: [id])
  cohorteId           Int
  cohorte             Cohorte  @relation(fields: [cohorteId], references: [id])
  cursaEnEstaApertura Boolean  @default(true)
  @@unique([aperturaId, cohorteId])
}
```

`.env`:

```
DATABASE_URL="file:./dev.db"
```

- [ ] **Step 2: Constantes de estados**

`src/lib/estados.ts`:

```ts
export const ESTADOS = [
  'sin_novedad', 'contratacion', 'validacion_docente', 'contrato',
  'construccion', 'revision', 'maquetacion', 'finalizacion',
] as const

export type Estado = (typeof ESTADOS)[number]

export const ESTADO_LABELS: Record<Estado, string> = {
  sin_novedad: 'Sin novedad',
  contratacion: 'Contratación',
  validacion_docente: 'Validación docente',
  contrato: 'Contrato',
  construccion: 'Construcción de contenido',
  revision: 'Revisión',
  maquetacion: 'Maquetación',
  finalizacion: 'Finalizada',
}
```

`src/lib/db.ts`:

```ts
import { PrismaClient } from '@prisma/client'

const globalForPrisma = globalThis as unknown as { prisma?: PrismaClient }
export const prisma = globalForPrisma.prisma ?? new PrismaClient()
if (process.env.NODE_ENV !== 'production') globalForPrisma.prisma = prisma
```

- [ ] **Step 3: Crear la migración**

```bash
npx prisma migrate dev --name init
```

Expected: `Your database is now in sync with your schema.` y carpeta `prisma/migrations/..._init/`.

- [ ] **Step 4: Test de humo de la base**

`tests/db.test.ts`:

```ts
import { describe, it, expect, afterAll } from 'vitest'
import { prisma } from '@/lib/db'

describe('base de datos', () => {
  afterAll(async () => {
    await prisma.carrera.deleteMany({ where: { nombre: '__TEST__' } })
    await prisma.unidad.deleteMany({ where: { id: '__test__' } })
    await prisma.$disconnect()
  })

  it('crea y lee una carrera con su unidad', async () => {
    await prisma.unidad.upsert({
      where: { id: '__test__' },
      update: {},
      create: { id: '__test__', nombre: 'Test' },
    })
    const c = await prisma.carrera.create({
      data: { nombre: '__TEST__', unidadId: '__test__' },
    })
    const leida = await prisma.carrera.findUnique({ where: { id: c.id } })
    expect(leida?.nombre).toBe('__TEST__')
  })
})
```

- [ ] **Step 5: Correr tests**

```bash
npm test
```

Expected: `1 passed`.

- [ ] **Step 6: Commit**

```bash
git add -A && git commit -m "feat: esquema de datos (unidades, carreras, asignaturas, periodos, aperturas)"
```

---

### Task 3: Semáforo

**Files:**
- Create: `src/lib/semaforo.ts`
- Test: `tests/semaforo.test.ts`

**Interfaces:**
- Consumes: tipo `Estado` de `@/lib/estados`.
- Produces: `semaforo(estado: Estado, aperturaInscripcion: Date | null, hoy: Date): 'verde' | 'amarillo' | 'rojo' | 'gris'` y `DIAS_ALERTA = 30`. La consumen las tareas 11 y 13.

- [ ] **Step 1: Test que falla**

`tests/semaforo.test.ts`:

```ts
import { describe, it, expect } from 'vitest'
import { semaforo } from '@/lib/semaforo'

const hoy = new Date('2026-08-08')
const en15dias = new Date('2026-08-23')
const en60dias = new Date('2026-10-07')

describe('semaforo', () => {
  it('finalizada es verde siempre', () => {
    expect(semaforo('finalizacion', en15dias, hoy)).toBe('verde')
    expect(semaforo('finalizacion', null, hoy)).toBe('verde')
  })
  it('maquetacion/revision con inscripción cerca es amarillo', () => {
    expect(semaforo('maquetacion', en15dias, hoy)).toBe('amarillo')
    expect(semaforo('revision', en15dias, hoy)).toBe('amarillo')
  })
  it('etapas tempranas con inscripción cerca es rojo', () => {
    expect(semaforo('sin_novedad', en15dias, hoy)).toBe('rojo')
    expect(semaforo('contratacion', en15dias, hoy)).toBe('rojo')
    expect(semaforo('construccion', en15dias, hoy)).toBe('rojo')
  })
  it('lejos de la inscripción o sin fecha es gris', () => {
    expect(semaforo('construccion', en60dias, hoy)).toBe('gris')
    expect(semaforo('maquetacion', null, hoy)).toBe('gris')
  })
  it('inscripción ya pasada cuenta como cerca', () => {
    expect(semaforo('construccion', new Date('2026-08-01'), hoy)).toBe('rojo')
  })
})
```

- [ ] **Step 2: Verificar que falla**

```bash
npm test
```

Expected: FAIL — `Cannot find module '@/lib/semaforo'`.

- [ ] **Step 3: Implementar**

`src/lib/semaforo.ts`:

```ts
import type { Estado } from './estados'

export const DIAS_ALERTA = 30
export type Semaforo = 'verde' | 'amarillo' | 'rojo' | 'gris'

export function semaforo(
  estado: Estado,
  aperturaInscripcion: Date | null,
  hoy: Date,
): Semaforo {
  if (estado === 'finalizacion') return 'verde'
  if (!aperturaInscripcion) return 'gris'
  const dias = (aperturaInscripcion.getTime() - hoy.getTime()) / 86_400_000
  if (dias > DIAS_ALERTA) return 'gris'
  return estado === 'maquetacion' || estado === 'revision' ? 'amarillo' : 'rojo'
}
```

- [ ] **Step 4: Verificar que pasa**

```bash
npm test
```

Expected: todos PASS.

- [ ] **Step 5: Commit**

```bash
git add -A && git commit -m "feat: semaforo de riesgo por estado y cercanía de inscripción"
```

---

### Task 4: Normalizadores de estado y fecha

**Files:**
- Create: `src/lib/normalizar.ts`
- Test: `tests/normalizar.test.ts`

**Interfaces:**
- Produces: `mapEstado(origen: string): Estado` y `parseFecha(s: string): Date | null`. Las consumen los parsers (tareas 6-8) y el loader (tarea 9).

- [ ] **Step 1: Test que falla** — con los valores REALES de las planillas y el tablero:

`tests/normalizar.test.ts`:

```ts
import { describe, it, expect } from 'vitest'
import { mapEstado, parseFecha } from '@/lib/normalizar'

describe('mapEstado', () => {
  it('mapea los estados de las planillas', () => {
    expect(mapEstado('5.FINALIZADA')).toBe('finalizacion')
    expect(mapEstado('5. (OM) FINALIZADA')).toBe('finalizacion')
    expect(mapEstado('3.MAQUETACIÓN')).toBe('maquetacion')
    expect(mapEstado('2.CONSTRUCCIÓN DE CONTENIDOS')).toBe('construccion')
    expect(mapEstado('1.CONTRATACIÓN')).toBe('contratacion')
    expect(mapEstado('0- NO INICIADO')).toBe('sin_novedad')
    expect(mapEstado('0. PROXIMAMENTE')).toBe('sin_novedad')
    expect(mapEstado('')).toBe('sin_novedad')
    expect(mapEstado('Requiere ajuste y revisión')).toBe('revision')
  })
  it('acepta los slugs del tablero tal cual', () => {
    expect(mapEstado('validacion_docente')).toBe('validacion_docente')
    expect(mapEstado('finalizacion')).toBe('finalizacion')
  })
})

describe('parseFecha', () => {
  it('dd/mm/yy y dd/mm/yyyy', () => {
    expect(parseFecha('07/05/25')).toEqual(new Date(2025, 4, 7))
    expect(parseFecha('22/08/2025')).toEqual(new Date(2025, 7, 22))
    expect(parseFecha('4/3/2026')).toEqual(new Date(2026, 2, 4))
  })
  it('vacío o basura da null', () => {
    expect(parseFecha('')).toBeNull()
    expect(parseFecha('—')).toBeNull()
  })
})
```

- [ ] **Step 2: Verificar que falla**

```bash
npm test
```

Expected: FAIL — módulo inexistente.

- [ ] **Step 3: Implementar**

`src/lib/normalizar.ts`:

```ts
import { ESTADOS, type Estado } from './estados'

export function mapEstado(origen: string): Estado {
  const s = origen.trim().toLowerCase()
  if ((ESTADOS as readonly string[]).includes(s)) return s as Estado
  if (s.includes('finalizada')) return 'finalizacion'
  if (s.includes('maquetaci')) return 'maquetacion'
  if (s.includes('construcci')) return 'construccion'
  if (s.includes('contrataci')) return 'contratacion'
  if (s.includes('revisi') || s.includes('ajuste')) return 'revision'
  if (s.includes('validaci')) return 'validacion_docente'
  if (s.includes('contrato')) return 'contrato'
  return 'sin_novedad'
}

export function parseFecha(s: string): Date | null {
  const m = s.trim().match(/^(\d{1,2})\/(\d{1,2})\/(\d{2,4})$/)
  if (!m) return null
  const [, d, mes, a] = m
  const anio = a.length === 2 ? 2000 + Number(a) : Number(a)
  return new Date(anio, Number(mes) - 1, Number(d))
}
```

- [ ] **Step 4: Verificar que pasa** — `npm test` → PASS.

- [ ] **Step 5: Commit**

```bash
git add -A && git commit -m "feat: normalización de estados y fechas de las fuentes originales"
```

---

### Task 5: Inferencia de período por fecha (Educación)

**Files:**
- Create: `src/lib/inferir-periodo.ts`
- Test: `tests/inferir-periodo.test.ts`

**Interfaces:**
- Consumes: nada externo.
- Produces: `inferirPeriodo(inicioCursado: Date, periodos: { id: number; inicioCursado: Date }[], toleranciaDias?: number): number | null` — devuelve el `id` del período cuyo inicio de cursado esté a ≤10 días (el más cercano), o `null`. La consume la tarea 9.

- [ ] **Step 1: Test que falla**

`tests/inferir-periodo.test.ts`:

```ts
import { describe, it, expect } from 'vitest'
import { inferirPeriodo } from '@/lib/inferir-periodo'

const periodos = [
  { id: 1, inicioCursado: new Date(2025, 4, 7) },   // 07/05/25
  { id: 2, inicioCursado: new Date(2025, 7, 6) },   // 06/08/25
  { id: 3, inicioCursado: new Date(2025, 9, 8) },   // 08/10/25
]

describe('inferirPeriodo', () => {
  it('empareja fecha exacta', () => {
    expect(inferirPeriodo(new Date(2025, 7, 6), periodos)).toBe(2)
  })
  it('empareja fecha cercana (06/05 vs 07/05)', () => {
    expect(inferirPeriodo(new Date(2025, 4, 6), periodos)).toBe(1)
  })
  it('devuelve null si nada está a menos de la tolerancia', () => {
    expect(inferirPeriodo(new Date(2025, 0, 15), periodos)).toBeNull()
  })
  it('elige el más cercano si hay dos candidatos', () => {
    const juntos = [
      { id: 1, inicioCursado: new Date(2026, 2, 1) },
      { id: 2, inicioCursado: new Date(2026, 2, 9) },
    ]
    expect(inferirPeriodo(new Date(2026, 2, 3), juntos)).toBe(1)
  })
})
```

- [ ] **Step 2: Verificar que falla** — `npm test` → FAIL.

- [ ] **Step 3: Implementar**

`src/lib/inferir-periodo.ts`:

```ts
export function inferirPeriodo(
  inicioCursado: Date,
  periodos: { id: number; inicioCursado: Date }[],
  toleranciaDias = 10,
): number | null {
  let mejor: { id: number; dist: number } | null = null
  for (const p of periodos) {
    const dist = Math.abs(p.inicioCursado.getTime() - inicioCursado.getTime()) / 86_400_000
    if (dist <= toleranciaDias && (!mejor || dist < mejor.dist)) mejor = { id: p.id, dist }
  }
  return mejor?.id ?? null
}
```

- [ ] **Step 4: Verificar que pasa** — `npm test` → PASS.

- [ ] **Step 5: Commit**

```bash
git add -A && git commit -m "feat: inferencia de período por fecha de inicio de cursado"
```

---

### Task 6: Parser del export de Posgrado

**Files:**
- Create: `migracion/parsers/posgrado.ts`
- Create: `migracion/parsers/tipos.ts`
- Test: `tests/parser-posgrado.test.ts`

**Interfaces:**
- Consumes: `mapEstado`, `parseFecha` de `@/lib/normalizar`.
- Produces (`migracion/parsers/tipos.ts`, lo consumen las tareas 7-9):

```ts
export type FilaAsignatura = {
  unidad: 'posgrado' | 'educacion'
  carrera: string
  cohorte: string | null
  codigo: string | null
  nombre: string
  catedra: string | null
  cargaHoraria: number | null
  orden: number | null
  estadoOrigen: string
  periodoNombre: string | null      // "Mensual_Agosto_2026" o null (educación)
  fechas: {
    inicioCursado: Date | null
    aperturaInscripcion: Date | null
    cierreInscripcion: Date | null
    finCursado: Date | null
    aperturaAfi: Date | null
    cierreAfi: Date | null
    cierreAsignatura: Date | null
    actas: Date | null
  }
}
```

  y `parsePosgrado(buffer: Buffer): FilaAsignatura[]` que lee las hojas de datos por programa (encabezado `COHORTE | ORDEN | CATEDRA | ASIGNATURA | CÓDIGO...`), tolerando columnas en distinto orden — mapear por NOMBRE de encabezado, no por índice.

- [ ] **Step 1: Test que falla** — construye un xlsx en memoria con la estructura real:

`tests/parser-posgrado.test.ts`:

```ts
import { describe, it, expect } from 'vitest'
import * as XLSX from 'xlsx'
import { parsePosgrado } from '../migracion/parsers/posgrado'

function fixture(): Buffer {
  const wb = XLSX.utils.book_new()
  const hoja = XLSX.utils.aoa_to_sheet([
    ['COHORTE', 'ORDEN', 'CATEDRA', 'ASIGNATURA', 'CÓDIGO DE LA ASIGNATURA', 'Transveralidad', 'Carga Horaria', 'ESTADO LA ASIGNATURA', 'PERIODO', 'INICIO DE CURSADO', 'APERTURA DE INSCRIPCIÓN', 'CIERRE DE INSCRIPCIÓN', 'LIMITES DE ENTREGA DE ACTIVIDADES OBLIGATORIAS - FINALIZACIÓN DE CURSADO', 'APERTURA DE AFI', 'CIERRE DE AFI ', 'CIERRE DE ASIGNATURA'],
    ['COHORTE  2025', '1', 'DA', 'REFLEXIÓN Y ANÁLISIS ESTRATÉGICO', 'EP00878', 'I7 - 23', '24', '5.FINALIZADA', 'Mensual_Marzo_2026', '04/03/26', '22/02/26', '01/03/26', '04/04/26', '05/04/26', '26/04/26', '04/05/26'],
    ['COHORTE  2025', '19', 'DA', 'INSTRUMENTOS DEL SISTEMA FINANCIERO', 'EP01396', '-', '21', '3.MAQUETACIÓN', 'Mensual_Agosto_2026', '05/08/26', '26/07/26', '02/08/26', '05/09/26', '06/09/26', '27/09/26', '05/10/26'],
    ['COHORTE  2025', '2', 'DA', 'SIN CÓDIGO TODAVÍA', '', '-', '', '', '', '', '', '', '', '', '', ''],
  ])
  XLSX.utils.book_append_sheet(wb, hoja, 'DIRECCION DE EMPRESAS')
  return XLSX.write(wb, { type: 'buffer', bookType: 'xlsx' }) as Buffer
}

describe('parsePosgrado', () => {
  it('extrae filas con código, período y fechas', () => {
    const filas = parsePosgrado(fixture())
    const f = filas.find((x) => x.codigo === 'EP00878')!
    expect(f.carrera).toBe('DIRECCION DE EMPRESAS')
    expect(f.cohorte).toBe('COHORTE  2025')
    expect(f.orden).toBe(1)
    expect(f.cargaHoraria).toBe(24)
    expect(f.estadoOrigen).toBe('5.FINALIZADA')
    expect(f.periodoNombre).toBe('Mensual_Marzo_2026')
    expect(f.fechas.inicioCursado).toEqual(new Date(2026, 2, 4))
    expect(f.fechas.cierreAsignatura).toEqual(new Date(2026, 4, 4))
  })
  it('conserva filas sin código (para el reporte)', () => {
    const filas = parsePosgrado(fixture())
    expect(filas.some((x) => x.codigo === null && x.nombre === 'SIN CÓDIGO TODAVÍA')).toBe(true)
  })
  it('ignora hojas sin el encabezado esperado', () => {
    const wb = XLSX.utils.book_new()
    XLSX.utils.book_append_sheet(wb, XLSX.utils.aoa_to_sheet([['PANEL DE CONTROL'], ['otra cosa']]), 'Dashboard')
    const buf = XLSX.write(wb, { type: 'buffer', bookType: 'xlsx' }) as Buffer
    expect(parsePosgrado(buf)).toEqual([])
  })
})
```

- [ ] **Step 2: Verificar que falla** — `npm test` → FAIL.

- [ ] **Step 3: Implementar**

`migracion/parsers/tipos.ts`: (el bloque de Interfaces de arriba, literal).

`migracion/parsers/posgrado.ts`:

```ts
import * as XLSX from 'xlsx'
import { parseFecha } from '../../src/lib/normalizar'
import type { FilaAsignatura } from './tipos'

const CAMPOS_FECHA: [keyof FilaAsignatura['fechas'], string][] = [
  ['inicioCursado', 'INICIO DE CURSADO'],
  ['aperturaInscripcion', 'APERTURA DE INSCRIPCIÓN'],
  ['cierreInscripcion', 'CIERRE DE INSCRIPCIÓN'],
  ['finCursado', 'LIMITES DE ENTREGA'],
  ['aperturaAfi', 'APERTURA DE AFI'],
  ['cierreAfi', 'CIERRE DE AFI'],
  ['cierreAsignatura', 'CIERRE DE ASIGNATURA'],
  ['actas', 'ACTAS'],
]

function celda(fila: Record<string, unknown>, claves: string[], contiene?: string): string {
  for (const k of Object.keys(fila)) {
    const kn = k.trim().toUpperCase()
    if (claves.some((c) => kn === c) || (contiene && kn.includes(contiene))) {
      return String(fila[k] ?? '').trim()
    }
  }
  return ''
}

export function parsePosgrado(buffer: Buffer): FilaAsignatura[] {
  const wb = XLSX.read(buffer, { type: 'buffer' })
  const filas: FilaAsignatura[] = []
  for (const nombreHoja of wb.SheetNames) {
    const json = XLSX.utils.sheet_to_json<Record<string, unknown>>(wb.Sheets[nombreHoja], { defval: '' })
    for (const fila of json) {
      const nombre = celda(fila, ['ASIGNATURA'])
      const tieneEncabezado = Object.keys(fila).some((k) => k.trim().toUpperCase() === 'ASIGNATURA')
      if (!tieneEncabezado || !nombre) continue
      const codigo = celda(fila, ['CÓDIGO DE LA ASIGNATURA', 'CODIGO DE LA ASIGNATURA'])
      const orden = celda(fila, ['ORDEN'])
      const carga = celda(fila, ['CARGA HORARIA'])
      const fechas = {} as FilaAsignatura['fechas']
      for (const [campo, encabezado] of CAMPOS_FECHA) {
        fechas[campo] = parseFecha(celda(fila, [encabezado], encabezado))
      }
      filas.push({
        unidad: 'posgrado',
        carrera: nombreHoja.trim(),
        cohorte: celda(fila, ['COHORTE']) || null,
        codigo: codigo || null,
        nombre,
        catedra: celda(fila, ['CATEDRA']) || null,
        cargaHoraria: carga ? Number(carga) || null : null,
        orden: orden ? Number(orden) || null : null,
        estadoOrigen: celda(fila, ['ESTADO LA ASIGNATURA', 'ESTADO DE LA ASIGNATURA']),
        periodoNombre: celda(fila, ['PERIODO']) || null,
        fechas,
      })
    }
  }
  return filas
}
```

- [ ] **Step 4: Verificar que pasa** — `npm test` → PASS. Si `sheet_to_json` duplica encabezados (`CIERRE DE AFI ` con espacio), el matcheo por `trim().toUpperCase()` lo cubre.

- [ ] **Step 5: Commit**

```bash
git add -A && git commit -m "feat: parser del export xlsx de posgrado"
```

---

### Task 7: Parser del export de Educación

**Files:**
- Create: `migracion/parsers/educacion.ts`
- Test: `tests/parser-educacion.test.ts`

**Interfaces:**
- Consumes: `FilaAsignatura`, `celda`-style matching (duplicado local, los parsers no comparten helpers todavía — DRY recién a la tercera repetición), `parseFecha`.
- Produces: `parseEducacion(buffer: Buffer): FilaAsignatura[]` — igual que posgrado pero `unidad: 'educacion'`, `periodoNombre: null` siempre, y tolera: hojas con/sin `DURACIÓN`, variantes `APERTURA DE AFI`/`Vencimiento del AFI`/`CIERRE DE AFI`, columna `ACTAS` presente/ausente.

- [ ] **Step 1: Test que falla**

`tests/parser-educacion.test.ts`:

```ts
import { describe, it, expect } from 'vitest'
import * as XLSX from 'xlsx'
import { parseEducacion } from '../migracion/parsers/educacion'

function fixture(): Buffer {
  const wb = XLSX.utils.book_new()
  // Hoja variante 1: sin DURACIÓN, con Vencimiento del AFI y ACTAS
  XLSX.utils.book_append_sheet(wb, XLSX.utils.aoa_to_sheet([
    ['COHORTE', 'CATEDRA', 'ASIGNATURA', 'CÓDIGO DE LA ASIGNATURA', 'ESTADO LA ASIGNATURA', 'INICIO DE CURSADO', 'APERTURA DE INSCRIPCIÓN', 'CIERRE DE INSCRIPCIÓN', 'LIMITES DE ENTREGA DE ACTIVIDADES OBLIGATORIAS - FINALIZACIÓN DE CURSADO', 'APERTURA DE AFI', 'Vencimiento del AFI', 'CIERRE DE ASIGNATURA', 'ACTAS'],
    ['COHORTE  3', '', 'CORRIENTES PEDAGÓGICAS CONTEMPORÁNEAS', '1210132', '5.FINALIZADA', '07/05/25', '28/04/25', '04/05/25', '28/06/25', '12/06/25', '26/06/25', '02/07/25', '05/07/25'],
  ]), 'Ed Inicial')
  // Hoja variante 2: con DURACIÓN
  XLSX.utils.book_append_sheet(wb, XLSX.utils.aoa_to_sheet([
    ['COHORTE', 'CATEDRA', 'ASIGNATURA', 'CÓDIGO DE LA ASIGNATURA', 'DURACIÓN', 'ESTADO LA ASIGNATURA', 'INICIO DE CURSADO', 'APERTURA DE INSCRIPCIÓN', 'CIERRE DE INSCRIPCIÓN', 'LIMITES DE ENTREGA DE ACTIVIDADES OBLIGATORIAS - FINALIZACIÓN DE CURSADO', 'APERTURA DE AFI', 'Vencimiento del AFI', 'CIERRE DE ASIGNATURA', 'ACTAS'],
    ['COHORTE  3', '', 'GESTIÓN CURRICULAR I', '1220084', 'Cuatrimestral', '5.FINALIZADA', '06/08/25', '28/07/25', '03/08/25', '22/11/25', '06/11/25', '20/11/25', '26/11/25', '29/11/25'],
  ]), 'Ciencias de la Educación')
  return XLSX.write(wb, { type: 'buffer', bookType: 'xlsx' }) as Buffer
}

describe('parseEducacion', () => {
  it('lee ambas variantes de hoja', () => {
    const filas = parseEducacion(fixture())
    expect(filas).toHaveLength(2)
    const a = filas.find((x) => x.codigo === '1210132')!
    expect(a.carrera).toBe('Ed Inicial')
    expect(a.unidad).toBe('educacion')
    expect(a.periodoNombre).toBeNull()
    expect(a.fechas.inicioCursado).toEqual(new Date(2025, 4, 7))
    expect(a.fechas.actas).toEqual(new Date(2025, 6, 5))
    const b = filas.find((x) => x.codigo === '1220084')!
    expect(b.duracion).toBe('Cuatrimestral')
  })
})
```

Nota: agrega `duracion?: string | null` a `FilaAsignatura` en `tipos.ts`.

- [ ] **Step 2: Verificar que falla** — `npm test` → FAIL.

- [ ] **Step 3: Implementar** — `migracion/parsers/educacion.ts`, misma mecánica que posgrado (matcheo de columnas por nombre con `trim().toUpperCase()`; `Vencimiento del AFI` → `cierreAfi`; `unidad: 'educacion'`; `periodoNombre: null`; `duracion` desde `DURACIÓN` si existe):

```ts
import * as XLSX from 'xlsx'
import { parseFecha } from '../../src/lib/normalizar'
import type { FilaAsignatura } from './tipos'

function celda(fila: Record<string, unknown>, exactas: string[], contiene?: string): string {
  for (const k of Object.keys(fila)) {
    const kn = k.trim().toUpperCase()
    if (exactas.some((c) => kn === c.toUpperCase()) || (contiene && kn.includes(contiene.toUpperCase()))) {
      return String(fila[k] ?? '').trim()
    }
  }
  return ''
}

export function parseEducacion(buffer: Buffer): FilaAsignatura[] {
  const wb = XLSX.read(buffer, { type: 'buffer' })
  const filas: FilaAsignatura[] = []
  for (const nombreHoja of wb.SheetNames) {
    const json = XLSX.utils.sheet_to_json<Record<string, unknown>>(wb.Sheets[nombreHoja], { defval: '' })
    for (const fila of json) {
      const nombre = celda(fila, ['ASIGNATURA'])
      if (!nombre) continue
      filas.push({
        unidad: 'educacion',
        carrera: nombreHoja.trim(),
        cohorte: celda(fila, ['COHORTE']) || null,
        codigo: celda(fila, ['CÓDIGO DE LA ASIGNATURA', 'CODIGO DE LA ASIGNATURA']) || null,
        nombre,
        catedra: celda(fila, ['CATEDRA']) || null,
        cargaHoraria: null,
        orden: celda(fila, ['ORDEN']) ? Number(celda(fila, ['ORDEN'])) || null : null,
        duracion: celda(fila, ['DURACIÓN', 'DURACION']) || null,
        estadoOrigen: celda(fila, ['ESTADO LA ASIGNATURA', 'ESTADO DE LA ASIGNATURA']),
        periodoNombre: null,
        fechas: {
          inicioCursado: parseFecha(celda(fila, ['INICIO DE CURSADO'])),
          aperturaInscripcion: parseFecha(celda(fila, ['APERTURA DE INSCRIPCIÓN'])),
          cierreInscripcion: parseFecha(celda(fila, ['CIERRE DE INSCRIPCIÓN'])),
          finCursado: parseFecha(celda(fila, [], 'LIMITES DE ENTREGA')),
          aperturaAfi: parseFecha(celda(fila, ['APERTURA DE AFI'])),
          cierreAfi: parseFecha(celda(fila, ['VENCIMIENTO DEL AFI', 'CIERRE DE AFI'])),
          cierreAsignatura: parseFecha(celda(fila, ['CIERRE DE ASIGNATURA'])),
          actas: parseFecha(celda(fila, ['ACTAS'])),
        },
      })
    }
  }
  return filas
}
```

- [ ] **Step 4: Verificar que pasa** — `npm test` → PASS.

- [ ] **Step 5: Commit**

```bash
git add -A && git commit -m "feat: parser del export xlsx de educación (columnas variables por hoja)"
```

---

### Task 8: Parser del respaldo del tablero del jefe

**Files:**
- Create: `migracion/parsers/tablero.ts`
- Test: `tests/parser-tablero.test.ts`

**Interfaces:**
- Produces: `parseTablero(json: string): { codigo: string; carrera: string; docente: string | null; asesor: string | null; estado: Estado }[]` — descarta entradas `PLAN-*` (sin código real). La consume la tarea 9 para completar docente/asesor/estado.

- [ ] **Step 1: Test que falla**

`tests/parser-tablero.test.ts`:

```ts
import { describe, it, expect } from 'vitest'
import { parseTablero } from '../migracion/parsers/tablero'

const respaldo = JSON.stringify({
  'Cooperación Internacional': [
    { codigo: 'EP01819', asignatura: 'GESTIÓN DE RIESGO...', catedra: 'DA', cohorte: 'COHORTE  2025', docente: 'Silvia Fontana/ Virginia Escañuela', asesor: 'Marcelo Hangshel Pentimalli', estado: 'maquetacion', estado_origen: '3.MAQUETACIÓN', numero: 5 },
    { codigo: 'PLAN-12', asignatura: 'TRABAJO FINAL INTEGRADOR', catedra: '', cohorte: '', docente: '', asesor: '', estado: 'sin_novedad', estado_origen: '', numero: 12 },
  ],
})

describe('parseTablero', () => {
  it('extrae docente, asesor y estado por código', () => {
    const filas = parseTablero(respaldo)
    expect(filas).toHaveLength(1)
    expect(filas[0]).toMatchObject({
      codigo: 'EP01819',
      carrera: 'Cooperación Internacional',
      docente: 'Silvia Fontana/ Virginia Escañuela',
      asesor: 'Marcelo Hangshel Pentimalli',
      estado: 'maquetacion',
    })
  })
})
```

- [ ] **Step 2: Verificar que falla** — `npm test` → FAIL.

- [ ] **Step 3: Implementar**

`migracion/parsers/tablero.ts`:

```ts
import { mapEstado } from '../../src/lib/normalizar'
import type { Estado } from '../../src/lib/estados'

type EntradaTablero = { codigo: string; docente?: string; asesor?: string; estado?: string; estado_origen?: string }

export function parseTablero(json: string) {
  const data = JSON.parse(json) as Record<string, EntradaTablero[]>
  const filas: { codigo: string; carrera: string; docente: string | null; asesor: string | null; estado: Estado }[] = []
  for (const [carrera, entradas] of Object.entries(data)) {
    for (const e of entradas) {
      if (!e.codigo || e.codigo.startsWith('PLAN-')) continue
      filas.push({
        codigo: e.codigo,
        carrera,
        docente: e.docente?.trim() || null,
        asesor: e.asesor?.trim() || null,
        estado: mapEstado(e.estado || e.estado_origen || ''),
      })
    }
  }
  return filas
}
```

- [ ] **Step 4: Verificar que pasa** — `npm test` → PASS.

- [ ] **Step 5: Commit**

```bash
git add -A && git commit -m "feat: parser del respaldo JSON del tablero de contratación"
```

---

### Task 9: Cargador de migración + reporte

**Files:**
- Create: `migracion/migrar.ts`
- Create: `migracion/cargar.ts`
- Test: `tests/cargar.test.ts`

**Interfaces:**
- Consumes: los tres parsers, `mapEstado`, `inferirPeriodo`, `prisma`.
- Produces: `cargar(filas: FilaAsignatura[], tablero: FilaTablero[], db: PrismaClient): Promise<Reporte>` con `Reporte = { asignaturas: number; aperturas: number; sinCodigo: string[]; sinPeriodo: string[]; nombresEnConflicto: string[] }`. CLI `npm run migrar` que lee `migracion/input/`, corre `cargar` y escribe `migracion/reporte-migracion.md`.

Reglas de carga (en este orden):
1. Upsert de unidades (`posgrado`, `educacion`) y carreras (por nombre de hoja).
2. Upsert de asignaturas por código; si dos filas del mismo código traen nombres distintos, gana el más largo y el conflicto va al reporte. Filas sin código: al reporte, no se cargan.
3. PlanItems (carrera×código, con orden) y cohortes.
4. Períodos: los de posgrado desde `periodoNombre` distintos (tipo `mensual`, `inicioCursado` = mínima fecha de inicio de sus filas). Los de educación se **generan**: se agrupan los `inicioCursado` distintos (tolerancia de `inferirPeriodo`) y cada grupo es un período `bimestral` o `cuatrimestral` según la `duracion` mayoritaria de sus filas, nombre `Bimestre dd/mm/aaaa` / `Cuatrimestre dd/mm/aaaa`.
5. Aperturas: upsert por (código, período) con las fechas de la fila; filas de educación sin período inferible van al reporte (`sinPeriodo`). AperturaCohorte por cada cohorte de la fila.
6. Datos del tablero: pisan docente/asesor; el estado del tablero solo pisa si el de la planilla es `sin_novedad` (la planilla de aperturas es más específica sobre finalizadas).

- [ ] **Step 1: Test que falla** — integración con la base real de dev (SQLite):

`tests/cargar.test.ts`:

```ts
import { describe, it, expect, beforeAll, afterAll } from 'vitest'
import { prisma } from '@/lib/db'
import { cargar } from '../migracion/cargar'
import type { FilaAsignatura } from '../migracion/parsers/tipos'

const fila = (extra: Partial<FilaAsignatura>): FilaAsignatura => ({
  unidad: 'posgrado', carrera: 'TEST CARRERA', cohorte: 'COHORTE  2025',
  codigo: 'TST001', nombre: 'ASIGNATURA TEST', catedra: null, cargaHoraria: null,
  orden: 1, duracion: null, estadoOrigen: '5.FINALIZADA', periodoNombre: 'Mensual_Test_2026',
  fechas: { inicioCursado: new Date(2026, 7, 5), aperturaInscripcion: new Date(2026, 6, 26),
    cierreInscripcion: null, finCursado: null, aperturaAfi: null, cierreAfi: null,
    cierreAsignatura: null, actas: null },
  ...extra,
})

describe('cargar', () => {
  beforeAll(async () => {
    await prisma.aperturaCohorte.deleteMany({}); await prisma.apertura.deleteMany({})
    await prisma.planItem.deleteMany({}); await prisma.cohorte.deleteMany({})
    await prisma.periodo.deleteMany({}); await prisma.asignatura.deleteMany({})
    await prisma.carrera.deleteMany({})
  })
  afterAll(async () => { await prisma.$disconnect() })

  it('carga asignaturas, períodos y aperturas, y reporta filas sin código', async () => {
    const reporte = await cargar(
      [fila({}), fila({ codigo: null, nombre: 'HUERFANA' })],
      [{ codigo: 'TST001', carrera: 'TEST CARRERA', docente: 'Doc Test', asesor: 'Ase Test', estado: 'maquetacion' }],
      prisma,
    )
    expect(reporte.asignaturas).toBe(1)
    expect(reporte.aperturas).toBe(1)
    expect(reporte.sinCodigo).toEqual(['HUERFANA (TEST CARRERA)'])
    const a = await prisma.asignatura.findUnique({ where: { codigo: 'TST001' } })
    expect(a?.docente).toBe('Doc Test')
    expect(a?.estado).toBe('finalizacion') // la planilla dice finalizada; el tablero no pisa
    const ap = await prisma.apertura.findFirst({ where: { asignaturaCodigo: 'TST001' }, include: { periodo: true } })
    expect(ap?.periodo.nombre).toBe('Mensual_Test_2026')
  })

  it('es idempotente (correr dos veces no duplica)', async () => {
    await cargar([fila({})], [], prisma)
    expect(await prisma.apertura.count()).toBe(1)
  })
})
```

- [ ] **Step 2: Verificar que falla** — `npm test` → FAIL.

- [ ] **Step 3: Implementar `migracion/cargar.ts`** siguiendo las 6 reglas. Esqueleto de las partes no obvias:

```ts
import type { PrismaClient } from '@prisma/client'
import { mapEstado } from '../src/lib/normalizar'
import { inferirPeriodo } from '../src/lib/inferir-periodo'
import type { FilaAsignatura } from './parsers/tipos'
import type { Estado } from '../src/lib/estados'

export type FilaTablero = { codigo: string; carrera: string; docente: string | null; asesor: string | null; estado: Estado }
export type Reporte = { asignaturas: number; aperturas: number; sinCodigo: string[]; sinPeriodo: string[]; nombresEnConflicto: string[] }

export async function cargar(filas: FilaAsignatura[], tablero: FilaTablero[], db: PrismaClient): Promise<Reporte> {
  const reporte: Reporte = { asignaturas: 0, aperturas: 0, sinCodigo: [], sinPeriodo: [], nombresEnConflicto: [] }

  await db.unidad.upsert({ where: { id: 'posgrado' }, update: {}, create: { id: 'posgrado', nombre: 'Posgrado' } })
  await db.unidad.upsert({ where: { id: 'educacion' }, update: {}, create: { id: 'educacion', nombre: 'Educación' } })

  const conCodigo = filas.filter((f) => {
    if (f.codigo) return true
    reporte.sinCodigo.push(`${f.nombre} (${f.carrera})`)
    return false
  })

  // 2. Asignaturas (nombre más largo gana; conflicto al reporte)
  const porCodigo = new Map<string, FilaAsignatura[]>()
  for (const f of conCodigo) {
    porCodigo.set(f.codigo!, [...(porCodigo.get(f.codigo!) ?? []), f])
  }
  for (const [codigo, grupo] of porCodigo) {
    const nombres = [...new Set(grupo.map((g) => g.nombre))]
    if (nombres.length > 1) reporte.nombresEnConflicto.push(`${codigo}: ${nombres.join(' / ')}`)
    const nombre = nombres.sort((a, b) => b.length - a.length)[0]
    const estado = grupo.map((g) => mapEstado(g.estadoOrigen)).sort(
      (a, b) => ordenEstado(b) - ordenEstado(a))[0] // el más avanzado
    await db.asignatura.upsert({
      where: { codigo },
      update: { nombre, estado },
      create: { codigo, nombre, estado, catedra: grupo[0].catedra, cargaHoraria: grupo[0].cargaHoraria },
    })
    reporte.asignaturas++
  }
  // ... 3. carreras/planItems/cohortes: upsert por @@unique correspondientes
  // ... 4. períodos posgrado por nombre; períodos educación agrupando inicioCursado con inferirPeriodo
  // ... 5. aperturas upsert por (codigo, periodoId); educación sin match → reporte.sinPeriodo
  // ... 6. tablero: update docente/asesor siempre; estado solo si el actual es 'sin_novedad'
  return reporte
}

function ordenEstado(e: Estado): number {
  return ['sin_novedad','contratacion','validacion_docente','contrato','construccion','revision','maquetacion','finalizacion'].indexOf(e)
}
```

Los `...` numerados son las reglas 3-6 escritas arriba de este task — implementarlas completas (cada una son upserts directos con los `@@unique` del esquema; la 4 para educación: recorrer fechas de inicio únicas ordenadas, crear período si `inferirPeriodo` sobre los ya creados da null).

- [ ] **Step 4: Verificar que pasa** — `npm test` → PASS.

- [ ] **Step 5: CLI `migracion/migrar.ts`**

```ts
import { readFileSync, writeFileSync, existsSync } from 'fs'
import { prisma } from '../src/lib/db'
import { parsePosgrado } from './parsers/posgrado'
import { parseEducacion } from './parsers/educacion'
import { parseTablero } from './parsers/tablero'
import { cargar } from './cargar'

async function main() {
  const dir = 'migracion/input'
  const filas = [
    ...(existsSync(`${dir}/posgrado.xlsx`) ? parsePosgrado(readFileSync(`${dir}/posgrado.xlsx`)) : []),
    ...(existsSync(`${dir}/educacion.xlsx`) ? parseEducacion(readFileSync(`${dir}/educacion.xlsx`)) : []),
  ]
  const tablero = existsSync(`${dir}/tablero.json`) ? parseTablero(readFileSync(`${dir}/tablero.json`, 'utf8')) : []
  if (!filas.length) { console.error('No hay archivos en migracion/input/'); process.exit(1) }
  const r = await cargar(filas, tablero, prisma)
  const md = [
    `# Reporte de migración — ${new Date().toLocaleString('es-AR')}`,
    `- Asignaturas cargadas: ${r.asignaturas}`, `- Aperturas cargadas: ${r.aperturas}`,
    `\n## Filas sin código (no cargadas)`, ...r.sinCodigo.map((s) => `- ${s}`),
    `\n## Educación sin período inferible (revisar a mano)`, ...r.sinPeriodo.map((s) => `- ${s}`),
    `\n## Códigos con nombres en conflicto`, ...r.nombresEnConflicto.map((s) => `- ${s}`),
  ].join('\n')
  writeFileSync('migracion/reporte-migracion.md', md)
  console.log(md)
  await prisma.$disconnect()
}
main()
```

```bash
npm install -D tsx
```

- [ ] **Step 6: Commit**

```bash
git add -A && git commit -m "feat: migración completa con reporte de casos a revisar"
```

---

### Task 10: Layout y página de períodos

**Files:**
- Modify: `src/app/layout.tsx`, `src/app/globals.css`
- Create: `src/app/page.tsx` (redirige a /periodos), `src/app/periodos/page.tsx`
- Create: `src/lib/formato.ts`

**Interfaces:**
- Consumes: `prisma`.
- Produces: `fmtFecha(d: Date | null): string` en `@/lib/formato` (dd/mm/aaaa o '—'); nav con enlaces `/periodos`, `/asignaturas`, `/produccion` que usan las tareas 11-13.

- [ ] **Step 1: Formato de fechas**

`src/lib/formato.ts`:

```ts
export function fmtFecha(d: Date | null | undefined): string {
  return d ? d.toLocaleDateString('es-AR', { day: '2-digit', month: '2-digit', year: 'numeric' }) : '—'
}
```

- [ ] **Step 2: Layout con navegación**

`src/app/layout.tsx` — html `lang="es"`, header con título "Aperturas SIED" y nav (`/periodos` Períodos, `/asignaturas` Asignaturas, `/produccion` Producción). `globals.css`: estilos sobrios (tabla con bordes suaves, badges `.sem-verde/.sem-amarillo/.sem-rojo/.sem-gris` con fondos #1fa971/#fcb815/#d9534f/#9aa3b5, texto blanco salvo amarillo).

`src/app/page.tsx`:

```tsx
import { redirect } from 'next/navigation'
export default function Home() { redirect('/periodos') }
```

- [ ] **Step 3: Página de períodos**

`src/app/periodos/page.tsx`:

```tsx
import Link from 'next/link'
import { prisma } from '@/lib/db'
import { fmtFecha } from '@/lib/formato'

export const dynamic = 'force-dynamic'

export default async function Periodos() {
  const periodos = await prisma.periodo.findMany({
    include: { unidad: true, _count: { select: { aperturas: true } } },
    orderBy: { inicioCursado: 'asc' },
  })
  const unidades = [...new Set(periodos.map((p) => p.unidad.nombre))]
  return (
    <main>
      <h1>Períodos</h1>
      {unidades.map((u) => (
        <section key={u}>
          <h2>{u}</h2>
          <table>
            <thead><tr><th>Período</th><th>Inicio de cursado</th><th>Aperturas</th></tr></thead>
            <tbody>
              {periodos.filter((p) => p.unidad.nombre === u).map((p) => (
                <tr key={p.id}>
                  <td><Link href={`/periodos/${p.id}`}>{p.nombre}</Link></td>
                  <td>{fmtFecha(p.inicioCursado)}</td>
                  <td>{p._count.aperturas}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      ))}
    </main>
  )
}
```

- [ ] **Step 4: Verificar a mano**

```bash
npm run dev
```

Abrir `http://localhost:3000` → redirige a `/periodos`; si ya se corrió la migración con datos reales, listan los períodos por unidad; si no, tablas vacías sin error.

- [ ] **Step 5: Commit**

```bash
git add -A && git commit -m "feat: layout y listado de períodos por unidad"
```

---

### Task 11: Tablero del período con semáforo

**Files:**
- Create: `src/app/periodos/[id]/page.tsx`
- Create: `src/components/SemaforoBadge.tsx`

**Interfaces:**
- Consumes: `semaforo` (tarea 3), `fmtFecha`, `ESTADO_LABELS`, `prisma`.
- Produces: `SemaforoBadge({ valor }: { valor: Semaforo })` — la reusa la tarea 13.

- [ ] **Step 1: Badge**

`src/components/SemaforoBadge.tsx`:

```tsx
import type { Semaforo } from '@/lib/semaforo'
const TEXTO: Record<Semaforo, string> = { verde: 'Lista', amarillo: 'En riesgo', rojo: 'No llega', gris: 'Sin riesgo aún' }
export function SemaforoBadge({ valor }: { valor: Semaforo }) {
  return <span className={`sem-${valor}`}>{TEXTO[valor]}</span>
}
```

- [ ] **Step 2: Página del período**

`src/app/periodos/[id]/page.tsx`:

```tsx
import Link from 'next/link'
import { notFound } from 'next/navigation'
import { prisma } from '@/lib/db'
import { semaforo } from '@/lib/semaforo'
import { fmtFecha } from '@/lib/formato'
import { ESTADO_LABELS, type Estado } from '@/lib/estados'
import { SemaforoBadge } from '@/components/SemaforoBadge'

export const dynamic = 'force-dynamic'

export default async function Periodo({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  const periodo = await prisma.periodo.findUnique({
    where: { id: Number(id) },
    include: {
      aperturas: {
        include: {
          asignatura: { include: { planItems: { include: { carrera: true } } } },
          cohortes: { include: { cohorte: { include: { carrera: true } } } },
        },
      },
    },
  })
  if (!periodo) notFound()
  const hoy = new Date()
  // agrupar por carrera (via cohortes; transversales aparecen en cada carrera que las comparte)
  const porCarrera = new Map<string, typeof periodo.aperturas>()
  for (const ap of periodo.aperturas) {
    const carreras = ap.cohortes.length
      ? [...new Set(ap.cohortes.map((c) => c.cohorte.carrera.nombre))]
      : [...new Set(ap.asignatura.planItems.map((p) => p.carrera.nombre))]
    for (const c of carreras.length ? carreras : ['(sin carrera)']) {
      porCarrera.set(c, [...(porCarrera.get(c) ?? []), ap])
    }
  }
  return (
    <main>
      <h1>{periodo.nombre}</h1>
      <p>Inicio de cursado: {fmtFecha(periodo.inicioCursado)}</p>
      {[...porCarrera.entries()].sort().map(([carrera, aps]) => (
        <section key={carrera}>
          <h2>{carrera}</h2>
          <table>
            <thead><tr><th>Semáforo</th><th>Asignatura</th><th>Estado</th><th>Docente</th><th>Asesor</th><th>Inscripción</th><th>Cohortes</th></tr></thead>
            <tbody>
              {aps.map((ap) => (
                <tr key={ap.id}>
                  <td><SemaforoBadge valor={semaforo(ap.asignatura.estado as Estado, ap.aperturaInscripcion, hoy)} /></td>
                  <td><Link href={`/asignaturas/${ap.asignatura.codigo}`}>{ap.asignatura.nombre}</Link> <small>{ap.asignatura.codigo}</small></td>
                  <td>{ESTADO_LABELS[ap.asignatura.estado as Estado]}</td>
                  <td>{ap.asignatura.docente ?? '—'}</td>
                  <td>{ap.asignatura.asesor ?? '—'}</td>
                  <td>{fmtFecha(ap.aperturaInscripcion)}</td>
                  <td>{ap.cohortes.map((c) => c.cohorte.nombre).join(', ') || '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      ))}
    </main>
  )
}
```

- [ ] **Step 3: Verificar a mano** — `npm run dev`, entrar a un período con datos: filas agrupadas por carrera con badge de color. Una transversal debe aparecer bajo cada carrera que la comparte.

- [ ] **Step 4: Commit**

```bash
git add -A && git commit -m "feat: tablero del período con semáforo por carrera"
```

---

### Task 12: Ficha de asignatura con cambio de estado

**Files:**
- Create: `src/app/asignaturas/[codigo]/page.tsx`
- Create: `src/app/asignaturas/[codigo]/actions.ts`

**Interfaces:**
- Consumes: `prisma`, `ESTADOS`, `ESTADO_LABELS`, `fmtFecha`.
- Produces: server action `actualizarAsignatura(codigo: string, formData: FormData)` que actualiza `estado`, `docente`, `asesor` y revalida.

- [ ] **Step 1: Server action**

`src/app/asignaturas/[codigo]/actions.ts`:

```ts
'use server'
import { revalidatePath } from 'next/cache'
import { prisma } from '@/lib/db'
import { ESTADOS } from '@/lib/estados'

export async function actualizarAsignatura(codigo: string, formData: FormData) {
  const estado = String(formData.get('estado') ?? '')
  if (!(ESTADOS as readonly string[]).includes(estado)) throw new Error('Estado inválido')
  await prisma.asignatura.update({
    where: { codigo },
    data: {
      estado,
      docente: String(formData.get('docente') ?? '').trim() || null,
      asesor: String(formData.get('asesor') ?? '').trim() || null,
    },
  })
  revalidatePath('/', 'layout')
}
```

- [ ] **Step 2: Ficha**

`src/app/asignaturas/[codigo]/page.tsx` — datos de la asignatura, formulario (select de estado con `ESTADO_LABELS`, inputs docente/asesor, botón Guardar que llama la action con `bind`), y dos tablas: planes donde figura (carrera + orden) y aperturas (período + fechas + link). Usar `notFound()` si el código no existe.

```tsx
import { notFound } from 'next/navigation'
import Link from 'next/link'
import { prisma } from '@/lib/db'
import { ESTADOS, ESTADO_LABELS, type Estado } from '@/lib/estados'
import { fmtFecha } from '@/lib/formato'
import { actualizarAsignatura } from './actions'

export const dynamic = 'force-dynamic'

export default async function Asignatura({ params }: { params: Promise<{ codigo: string }> }) {
  const { codigo } = await params
  const a = await prisma.asignatura.findUnique({
    where: { codigo },
    include: {
      planItems: { include: { carrera: true } },
      aperturas: { include: { periodo: true }, orderBy: { inicioCursado: 'asc' } },
    },
  })
  if (!a) notFound()
  const accion = actualizarAsignatura.bind(null, a.codigo)
  return (
    <main>
      <h1>{a.nombre} <small>{a.codigo}</small></h1>
      {a.planItems.length > 1 && <p className="aviso">⚠ Transversal: compartida por {a.planItems.map((p) => p.carrera.nombre).join(', ')}. Al abrirse queda disponible para todas.</p>}
      <form action={accion}>
        <label>Estado
          <select name="estado" defaultValue={a.estado}>
            {ESTADOS.map((e) => <option key={e} value={e}>{ESTADO_LABELS[e as Estado]}</option>)}
          </select>
        </label>
        <label>Docente <input name="docente" defaultValue={a.docente ?? ''} /></label>
        <label>Asesor <input name="asesor" defaultValue={a.asesor ?? ''} /></label>
        <button type="submit">Guardar</button>
      </form>
      <h2>Aperturas</h2>
      <table>
        <thead><tr><th>Período</th><th>Inscripción</th><th>Inicio cursado</th><th>Cierre</th></tr></thead>
        <tbody>
          {a.aperturas.map((ap) => (
            <tr key={ap.id}>
              <td><Link href={`/periodos/${ap.periodoId}`}>{ap.periodo.nombre}</Link></td>
              <td>{fmtFecha(ap.aperturaInscripcion)}</td>
              <td>{fmtFecha(ap.inicioCursado)}</td>
              <td>{fmtFecha(ap.cierreAsignatura)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </main>
  )
}
```

- [ ] **Step 3: Verificar a mano** — cambiar el estado de una asignatura, guardar, volver al tablero del período: el semáforo refleja el cambio. Verificar el aviso de transversal en una compartida (ej. EP00461).

- [ ] **Step 4: Commit**

```bash
git add -A && git commit -m "feat: ficha de asignatura con edición de estado, docente y asesor"
```

---

### Task 13: Catálogo con búsqueda y vista de producción

**Files:**
- Create: `src/app/asignaturas/page.tsx`
- Create: `src/app/produccion/page.tsx`

**Interfaces:**
- Consumes: `prisma`, `ESTADO_LABELS`, `SemaforoBadge`, `semaforo`.

- [ ] **Step 1: Catálogo con búsqueda**

`src/app/asignaturas/page.tsx` — server component con `searchParams` `?q=`; filtra por `codigo` o `nombre` (`contains`); tabla con código, nombre, estado, docente, asesor, carreras; form GET con un input de búsqueda.

```tsx
import Link from 'next/link'
import { prisma } from '@/lib/db'
import { ESTADO_LABELS, type Estado } from '@/lib/estados'

export const dynamic = 'force-dynamic'

export default async function Asignaturas({ searchParams }: { searchParams: Promise<{ q?: string }> }) {
  const { q = '' } = await searchParams
  const asignaturas = await prisma.asignatura.findMany({
    where: q ? { OR: [{ codigo: { contains: q } }, { nombre: { contains: q } }] } : undefined,
    include: { planItems: { include: { carrera: true } } },
    orderBy: { nombre: 'asc' },
    take: 200,
  })
  return (
    <main>
      <h1>Asignaturas</h1>
      <form><input name="q" defaultValue={q} placeholder="Buscar por nombre o código..." /><button>Buscar</button></form>
      <table>
        <thead><tr><th>Código</th><th>Asignatura</th><th>Estado</th><th>Docente</th><th>Carreras</th></tr></thead>
        <tbody>
          {asignaturas.map((a) => (
            <tr key={a.codigo}>
              <td>{a.codigo}</td>
              <td><Link href={`/asignaturas/${a.codigo}`}>{a.nombre}</Link></td>
              <td>{ESTADO_LABELS[a.estado as Estado]}</td>
              <td>{a.docente ?? '—'}</td>
              <td>{a.planItems.map((p) => p.carrera.nombre).join(', ')}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </main>
  )
}
```

- [ ] **Step 2: Vista de producción** — `src/app/produccion/page.tsx`: las asignaturas agrupadas por estado (columnas del pipeline en orden de `ESTADOS`), cada una con su próxima apertura (mínima `aperturaInscripcion` futura) y el semáforo. Misma mecánica de query que el catálogo + `aperturas: { include: { periodo: true } }`; agrupar en memoria.

- [ ] **Step 3: Verificar a mano** — buscar "EP00461" en catálogo; en producción, ver los ocho grupos con contadores.

- [ ] **Step 4: Commit**

```bash
git add -A && git commit -m "feat: catálogo con búsqueda y vista de pipeline de producción"
```

---

### Task 14: Acceso básico y preparación para deploy

**Files:**
- Create: `src/middleware.ts`
- Create: `README.md`

**Interfaces:**
- Consumes: env vars `ACCESO_USUARIO`, `ACCESO_CLAVE`.

- [ ] **Step 1: Middleware de Basic Auth** (suficiente para F1 — F2 lo reemplaza por Google OAuth):

`src/middleware.ts`:

```ts
import { NextResponse, type NextRequest } from 'next/server'

export function middleware(req: NextRequest) {
  const user = process.env.ACCESO_USUARIO
  const pass = process.env.ACCESO_CLAVE
  if (!user || !pass) return NextResponse.next() // sin credenciales configuradas (dev local), no bloquea
  const auth = req.headers.get('authorization')
  if (auth?.startsWith('Basic ')) {
    const [u, p] = Buffer.from(auth.slice(6), 'base64').toString().split(':')
    if (u === user && p === pass) return NextResponse.next()
  }
  return new NextResponse('Acceso restringido', { status: 401, headers: { 'WWW-Authenticate': 'Basic realm="Aperturas SIED"' } })
}

export const config = { matcher: ['/((?!_next/static|_next/image|favicon.ico).*)'] }
```

- [ ] **Step 2: Verificar a mano** — con `ACCESO_USUARIO=sied ACCESO_CLAVE=algo npm run dev`, el navegador pide usuario/clave; sin las vars, entra directo.

- [ ] **Step 3: README con pasos de deploy** — documentar exactamente:
  1. Crear proyecto gratuito en supabase.com → copiar `DATABASE_URL` (connection pooling, puerto 6543) y `DIRECT_URL`.
  2. En `prisma/schema.prisma`: `provider = "postgresql"` + agregar `directUrl = env("DIRECT_URL")`; borrar `prisma/migrations/` (eran de sqlite) y `npx prisma migrate dev --name init` contra Supabase.
  3. `npm run migrar` con los archivos de `migracion/input/` para poblar producción.
  4. Subir el repo a GitHub, importar en vercel.com, setear env vars `DATABASE_URL`, `DIRECT_URL`, `ACCESO_USUARIO`, `ACCESO_CLAVE`. Deploy.
  5. Compartir la URL con el equipo.

- [ ] **Step 4: Verificación final de la fase**

```bash
npm test && npm run build
```

Expected: todos los tests PASS y build sin errores.

- [ ] **Step 5: Commit**

```bash
git add -A && git commit -m "feat: acceso básico por credenciales y guía de deploy"
```

---

## Self-Review (hecha al escribir el plan)

- **Cobertura de spec F1**: fuente única (Tasks 2, 9), migración con reporte (9), períodos de Educación generados desde fechas (5, 9), tablero de períodos con semáforo (10, 11), edición de estados (12), acceso simple del equipo (14). Transversales: modelo por código único (2), aviso en ficha (12), aparecen en todas sus carreras en el tablero (11). Pipeline de producción como vista simple (13).
- **Fuera de F1 (consciente)**: roles por usuario, reordenamiento por directores, historial, reglas de fechas automáticas, dashboard de consulta, exportación — Fases 2 y 3.
- **Consistencia de tipos**: `FilaAsignatura` definida en Task 6 y extendida con `duracion` en Task 7; `cargar(filas, tablero, db)` consume ambas; `semaforo(estado, fecha, hoy)` usada igual en 11 y 13.
