# Guía: armar el cuaderno compartido en Google Drive

> **Objetivo:** que los tres (vos + los dos maquetadores) vean **el mismo registro de aulas** en el Maquetador. Para eso, en vez de que cada uno guarde en su compu, todos van a guardar en **una sola carpeta compartida de Google Drive**.

Esta es la parte que se prepara en Drive (la **Parte B**). Cuando termines esto, hacemos el cambio en la app (la **Parte A**) para que use esta carpeta.

---

## Antes de empezar

Necesitás:
- Que los tres tengan cuenta de Google (la de `@ucc.edu.ar` o la que usen).
- Unos 15 minutos.

---

## Paso 1 — Instalar "Google Drive para Escritorio" en las 3 computadoras

Esto hace que Google Drive aparezca como una **carpeta/unidad dentro de la compu** (no solo en la web). Es lo que permite que la app guarde ahí.

En **cada una de las 3 computadoras**:

1. Entrar a **https://www.google.com/drive/download/**
2. Descargar **"Google Drive para escritorio"** e instalarlo.
3. Abrirlo e **iniciar sesión** con la cuenta de Google del equipo.
4. Cuando termina, en el explorador de archivos aparece una unidad nueva (en Windows suele ser **`G:`** y dice "Google Drive"; en Mac aparece en el Finder).

> ✅ Listo este paso cuando los tres ven la unidad de Google Drive en su compu.

---

## Paso 2 — Crear el espacio compartido (una sola vez, lo hacés vos)

Hay dos formas. **Recomiendo la primera** si la cuenta `@ucc.edu.ar` lo permite.

### Opción recomendada: "Unidad compartida"

Una *Unidad compartida* pertenece al **equipo**, no a una persona. Si mañana alguien se va, los datos quedan.

1. Entrar a **https://drive.google.com** (en el navegador).
2. En el menú de la izquierda, buscar **"Unidades compartidas"**.
3. Click derecho → **"Nueva unidad compartida"** (o el botón **+ Nueva**).
4. Nombrarla: **`Maquetador UCC`**.

> Si **no te aparece** "Unidades compartidas", usá la opción de abajo.

### Opción alternativa: carpeta compartida normal

1. En **https://drive.google.com**, dentro de **"Mi unidad"**, crear una carpeta nueva: **`Maquetador UCC`**.

---

## Paso 3 — Crear la carpeta de datos adentro

Dentro de **`Maquetador UCC`** (la unidad o carpeta del paso anterior), creá una carpeta llamada:

```
output
```

Esa carpeta `output` va a ser el "cuaderno compartido" donde se guardan las aulas procesadas.

> No hace falta poner nada adentro: la app la va a ir llenando sola.

---

## Paso 4 — Compartir con los dos maquetadores

1. Click derecho sobre **`Maquetador UCC`** → **"Compartir"** (o "Administrar miembros" si es Unidad compartida).
2. Agregar el **mail de los dos maquetadores**.
3. Darles permiso de **"Editor"** (que puedan crear y modificar, no solo ver).
4. Enviar.

> ✅ Listo cuando los dos maquetadores reciben el acceso y ven la carpeta `Maquetador UCC` en su Drive.

---

## Paso 5 — Confirmar que la carpeta se ve en las 3 compus

En **cada compu**, abrir el explorador de archivos y entrar a la unidad de Google Drive. Tienen que poder llegar hasta la carpeta `output`.

La ruta se ve más o menos así (puede cambiar la letra de la unidad en cada compu):

- Si usaron **Unidad compartida**:
  `G:\Unidades compartidas\Maquetador UCC\output`
- Si usaron **carpeta en Mi unidad**:
  `G:\Mi unidad\Maquetador UCC\output`

> ⚠️ **Importante:** la letra (`G:`, `H:`, etc.) **puede ser distinta en cada compu**. Eso es normal. Por eso, en la Parte A, cada uno le va a decir a la app *su* ruta.

---

## Paso 6 — Anotar la ruta de cada compu (esto me sirve para la Parte A)

En cada una de las 3 computadoras, anotá la ruta completa hasta la carpeta `output`. La forma fácil:

1. Entrar a la carpeta `output` en el explorador.
2. Click en la barra de direcciones de arriba → se selecciona la ruta completa → **copiarla** (Ctrl+C).
3. Pegarla en un bloc de notas, anotando de qué compu es. Ejemplo:

```
Compu de Gonzalo:   G:\Unidades compartidas\Maquetador UCC\output
Compu maquetador 1: H:\Unidades compartidas\Maquetador UCC\output
Compu maquetador 2: G:\Unidades compartidas\Maquetador UCC\output
```

> Con esas 3 rutas, en la Parte A configuramos cada app para que apunte ahí.

---

## Dos cosas para tener en cuenta (cómo funciona Drive)

- **No es instantáneo.** Cuando alguien procesa un aula, los otros la ven cuando Drive termina de sincronizar (segundos o algún minuto). Para un registro está perfecto.
- **Evitar editar el *mismo* aula al mismo tiempo.** Si dos tocan el mismo aula a la vez, Drive puede crear "copias en conflicto". Como cada uno suele trabajar aulas distintas, el riesgo es bajo — pero mejor coordinarse.
- **Drive tiene que estar prendido y sincronizando** en cada compu para que funcione (el programa "Google Drive para escritorio" abierto).

---

## Cuando termines

Avisame y pasamos a la **Parte A**: hago el cambio en la app para que use la carpeta `output` de Drive. Para eso necesito las **3 rutas** que anotaste en el Paso 6.
