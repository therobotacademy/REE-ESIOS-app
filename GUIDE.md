# Manual de Usuario — ESIOS / REE API Tester

## Descripción general

**ESIOS / REE API Tester** es una herramienta web construida con Streamlit que permite explorar la API pública de Red Eléctrica de España (REE) a través de ESIOS.

Facilita la consulta, búsqueda y descarga de indicadores del mercado eléctrico español sin necesidad de programar.

- **URL de acceso:** `http://localhost:8501/`
- **Backend:** `python-esios v2.0.0`
- **API base:** [https://api.esios.ree.es](https://api.esios.ree.es)

---

## Estructura de la interfaz

La aplicación se divide en dos zonas principales:

- **Panel lateral izquierdo:** Gestión del token de autenticación y estado del sistema.
- **Área principal central:** Tres pestañas funcionales para consultar y descargar datos.

---

## Panel lateral — Configuración del Token

### ¿Qué es el token ESIOS?

El token es una credencial personal que autentica las peticiones a la API de ESIOS/REE. Algunas funcionalidades (como la búsqueda libre de indicadores) lo requieren, mientras que otras (como la lista de indicadores comunes) no.

### Cómo obtener el token

Hay dos formas de conseguir un token:

1. **Por correo:** Escribe a [consultasios@ree.es](mailto:consultasios@ree.es) solicitando acceso.
2. **Por registro web:** Regístrate en [api.esios.ree.es](https://api.esios.ree.es).

En ambos casos recibirás respuesta en 1–2 días hábiles.

### Introducir y validar el token

1. Localiza el campo **"Token"** en el panel izquierdo bajo el título 🔑 **Token ESIOS**.
2. Pega tu token personal en el campo de texto (el texto se oculta por defecto; puedes pulsar el icono 👁 para mostrarlo).
3. Haz clic en el botón **✅ Validar token**.
4. Si el token es correcto, aparecerá el mensaje **"✅ Token correcto ✓"** en verde.
5. Si el token es inválido, se mostrará un mensaje de error.

### Estado del backend

Bajo la sección del token se muestra el estado del servicio:

- **Backend OK · python-esios vX.X.X** — El servicio funciona correctamente.
- Si hay un problema de conexión, aparecerá un mensaje de error en rojo.

---

## Pestañas principales

La aplicación tiene tres pestañas en el área central:

| Pestaña            | Ícono | Requiere token |
| ------------------- | ------ | -------------- |
| Indicadores comunes | 📋     | No             |
| Buscar indicadores  | 🔍     | Sí            |
| Serie temporal      | 📈     | Sí            |

---

## Pestaña 1 — Indicadores comunes

**Título:** Indicadores del mercado eléctrico español

Esta pestaña muestra una lista curada de los indicadores más relevantes del mercado eléctrico. **No requiere token** para funcionar.

### Cómo usar

1. Haz clic en el botón rojo **"Cargar lista"**.
2. La aplicación consultará el backend y mostrará una tabla con dos columnas:
   - **ID:** Número identificador del indicador en ESIOS.
   - **Descripción:** Nombre descriptivo del indicador con su unidad de medida.

### Indicadores disponibles

| ID    | Descripción                         |
| ----- | ------------------------------------ |
| 600   | Precio mercado spot (OMIE) — €/MWh |
| 10211 | Precio PVPC — €/MWh                |
| 1001  | Demanda real — MW                   |
| 1293  | Generación eólica — MW            |
| 1292  | Generación solar fotovoltaica — MW |
| 1161  | Generación hidráulica — MW        |
| 1163  | Generación nuclear — MW            |
| 545   | CO₂ evitado por renovables — tCO₂ |
| 776   | Potencia instalada solar FV — MW    |

> **Tip:** El ID de cada indicador puede copiarse y usarse directamente en la pestaña **Serie temporal** para descargar sus datos.

---

## Pestaña 2 — Buscar indicadores

**Título:** Búsqueda en el catálogo ESIOS

Permite buscar indicadores de forma libre por texto en el nombre. **Requiere token válido.**

### Cómo usar

1. Asegúrate de haber validado tu token en el panel lateral.
2. Escribe un término de búsqueda en el campo de texto (ejemplos: `solar`, `eólica`, `precio`, `demanda`, `nuclear`).
3. Haz clic en el botón rojo **"Buscar"**.
4. La tabla de resultados se actualizará mostrando los indicadores encontrados.

### Tabla de resultados

La tabla muestra tres columnas:

- **ID:** Identificador numérico del indicador.
- **Nombre:** Nombre completo del indicador.
- **Nombre corto:** Nombre abreviado o categoría.

Encima de la tabla se indica el número total de resultados encontrados (por ejemplo: *"52 resultados"*).

### Opciones de la tabla de resultados

En la esquina superior derecha de la tabla aparecen cuatro iconos de control:

| Icono                | Función                                 |
| -------------------- | ---------------------------------------- |
| 👁 Show/hide columns | Muestra u oculta columnas de la tabla    |
| ⬇ Download as CSV   | Descarga los resultados como archivo CSV |
| 🔍 Search            | Filtra dentro de la tabla ya cargada     |
| ⛶ Fullscreen        | Amplía la tabla a pantalla completa     |

---

## Pestaña 3 — Serie temporal

**Título:** Descarga y visualización de series temporales

Es la pestaña más completa. Permite descargar datos históricos de cualquier indicador ESIOS y visualizarlos como gráfico y tabla. **Requiere token válido.**

### Campos de configuración

#### Selección del indicador

Existen dos formas alternativas de especificar el indicador a consultar:

- **ID del indicador** (campo de texto libre): Introduce directamente el número identificador del indicador (por ejemplo: `600`).
- **O elige un indicador común** (desplegable): Selecciona uno de los indicadores predefinidos de la lista curada. Al seleccionarlo, el campo "ID del indicador" se autocompleta automáticamente.

#### Rango de fechas

Puedes establecer el período de consulta de dos maneras:

**Atajos rápidos** (botones):

| Botón            | Rango                          |
| ----------------- | ------------------------------ |
| Últimas 48 horas | Desde hace 2 días hasta hoy   |
| Última semana    | Desde hace 7 días hasta hoy   |
| Último mes       | Desde hace 30 días hasta hoy  |
| Últimos 3 meses  | Desde hace 90 días hasta hoy  |
| Año pasado       | Desde hace 365 días hasta hoy |

**Fechas manuales** (campos de texto):

- **Fecha inicio (YYYY-MM-DD):** Fecha de inicio del período.
- **Fecha fin (YYYY-MM-DD):** Fecha de fin del período.

El formato requerido es `YYYY-MM-DD` (por ejemplo: `2026-03-22`).

#### Granularidad

Selector desplegable que define la resolución temporal de los datos descargados:

| Valor               | Descripción                  |
| ------------------- | ----------------------------- |
| `hour`            | Datos cada hora (por defecto) |
| `day`             | Datos diarios                 |
| `week`            | Datos semanales               |
| `month`           | Datos mensuales               |
| `five_minutes`    | Datos cada 5 minutos          |
| `ten_minutes`     | Datos cada 10 minutos         |
| `fifteen_minutes` | Datos cada 15 minutos         |

### Ejecutar la descarga

Una vez configurados todos los parámetros, haz clic en el botón rojo **⬇️ Descargar serie**. La aplicación realizará la consulta a la API y presentará los resultados.

### Resultados de la descarga

Tras la consulta exitosa se muestran:

#### Métricas resumen

Cuatro tarjetas informativas en la parte superior:

- **Indicador:** Nombre del indicador consultado.
- **Unidad:** Unidad de medida de los valores (por ejemplo: €/MWh, MW).
- **Granularidad:** Resolución temporal seleccionada.
- **Registros:** Número total de filas de datos descargadas.

#### Gráfico de líneas

Representación visual de la serie temporal. Si el indicador incluye datos por zonas geográficas (como el precio SPOT), el gráfico muestra una línea por zona con leyenda incluida (por ejemplo: Alemania, Bélgica, España, Francia, Países Bajos, Portugal).

El eje X representa la **Fecha/hora** y el eje Y el **valor** del indicador.

#### Tabla de datos

Tabla con los datos en bruto descargados, con las columnas:

- **Fecha:** Marca temporal del registro.
- **Zona:** Zona geográfica o tipo (cuando aplique).
- **Valor:** Valor numérico del indicador en la unidad correspondiente.

La tabla también cuenta con los iconos de control (👁, ⬇, 🔍, ⛶) para gestionar columnas, buscar y ampliar la vista.

#### Botón Descargar CSV

A la derecha de la tabla aparece el botón **📥 Descargar CSV**, que permite exportar todos los datos descargados en formato CSV para su uso en Excel, Python u otras herramientas.

---

## Flujos de uso recomendados

### Consulta rápida de un indicador conocido

1. Ir a la pestaña **📈 Serie temporal**.
2. Introducir el ID del indicador directamente (por ejemplo: `1293` para eólica).
3. Seleccionar el rango de fechas con los botones rápidos (por ejemplo: **Última semana**).
4. Elegir granularidad `hour`.
5. Pulsar **⬇️ Descargar serie**.

### Descubrir indicadores disponibles

1. Ir a **🔍 Buscar indicadores** (requiere token).
2. Escribir una palabra clave relacionada con el indicador buscado.
3. Pulsar **Buscar** y revisar la tabla de resultados.
4. Anotar el ID del indicador de interés.
5. Ir a **📈 Serie temporal** y usar ese ID para descargar datos.

### Exportar datos para análisis externo

1. Descargar la serie en **📈 Serie temporal**.
2. Una vez generados los resultados, pulsar **📥 Descargar CSV**.
3. Importar el archivo CSV en Excel, pandas u otro entorno de análisis.

---

## Preguntas frecuentes

**¿Qué pasa si no tengo token?**
Puedes usar la pestaña **📋 Indicadores comunes** sin token. Para usar las pestañas de búsqueda y descarga de series necesitas token.

**¿El token tiene fecha de caducidad?**
Los tokens de ESIOS pueden tener vigencia limitada. Si el validador muestra error, solicita uno nuevo a REE.

**¿Cuántos datos puedo descargar de una vez?**
Depende del indicador y la granularidad. Con granularidad horaria y un rango de 48 horas, se obtienen típicamente 72 registros por zona (48h × 6 zonas en el caso del precio SPOT).

**¿Qué formato tienen las fechas en los campos manuales?**
El formato es `YYYY-MM-DD`, por ejemplo `2026-01-15`.

**¿Puedo buscar con términos parciales?**
