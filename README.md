# 🔌 ESIOS API Tester — Streamlit + FastAPI + python-esios

Aplicación web para explorar y descargar datos del mercado eléctrico español
en tiempo real a través de la API pública de **Red Eléctrica de España (REE / ESIOS)**.

---

## Arquitectura

```
frontend_streamlit.py   (Streamlit — puerto 8501)
         │  HTTP + JSON  (httpx)
         ▼
backend.py              (FastAPI — puerto 8000)
         │  python-esios (ESIOSClient)
         ▼
api.esios.ree.es        (API pública REE)
```

Cada capa tiene una responsabilidad única:

| Capa        | Tecnología            | Responsabilidad                                             |
| ----------- | ---------------------- | ----------------------------------------------------------- |
| Frontend    | Streamlit              | Interfaz de usuario, visualización, descarga de CSV        |
| Backend     | FastAPI + python-esios | Autenticación, peticiones a ESIOS, normalización de datos |
| API externa | ESIOS / REE            | Fuente de datos del mercado eléctrico español             |

---

## Requisitos

- Python **3.10** o superior (requerido por python-esios)
- Token personal de la API ESIOS (ver sección [Obtener el token](#obtener-el-token))

---

## Instalación

```bash
# 1. Clona el repositorio o copia los archivos en una carpeta
mkdir esios_app && cd esios_app

# 2. Crea un entorno virtual (recomendado)
python -m venv .venv
source .venv/bin/activate        # Linux / Mac
.venv\Scripts\activate           # Windows PowerShell

# 3. Instala las dependencias
pip install -r requirements.txt
```

### `requirements.txt`

```
fastapi==0.115.5
uvicorn[standard]==0.32.1
python-esios==2.2.0
pandas==2.2.3
matplotlib==3.9.3
streamlit==1.45.0
httpx==0.27.2
```

---

## Arranque

Necesitas **dos terminales** abiertas en paralelo.

**Terminal 1 — Backend FastAPI:**

```bash
uvicorn backend:app --reload --port 8000
```

Documentación interactiva disponible en:

- Swagger UI → `http://localhost:8000/docs`
- ReDoc → `http://localhost:8000/redoc`

**Terminal 2 — Frontend Streamlit:**

```bash
.venv\Scripts\activate           # Windows PowerShell
streamlit run frontend.py
```

Abre el navegador en → `http://localhost:8501`

---

## Obtener el token

La API de ESIOS requiere un token personal y gratuito:

1. Envía un correo a **consultasios@ree.es** solicitando acceso a la API
2. En el asunto indica: _"Solicitud de token API ESIOS"_
3. Recibirás el token en **1–2 días laborables**

Alternativamente puedes registrarte directamente en `https://api.esios.ree.es`

Una vez obtenido, el token se introduce en la **barra lateral** de la app. No se almacena en disco; se guarda en memoria de sesión mientras la app esté abierta.

---

## Funcionalidades

### Sidebar — Token y estado del backend

- Campo de contraseña para introducir el token ESIOS
- Botón de validación: verifica el token contra el backend sin consumir cuota
- Indicador del estado del backend (verde / rojo según disponibilidad)

### Pestaña 1 — Indicadores comunes

Lista curada de los indicadores más relevantes del mercado eléctrico español. No requiere token.

| ID    | Nombre                         | Unidad |
| ----- | ------------------------------ | ------ |
| 600   | Precio mercado spot (OMIE)     | €/MWh |
| 10211 | Precio PVPC                    | €/MWh |
| 1001  | Demanda real                   | MW     |
| 1293  | Generación eólica            | MW     |
| 1292  | Generación solar fotovoltaica | MW     |
| 1161  | Generación hidráulica        | MW     |
| 1163  | Generación nuclear            | MW     |

### Pestaña 2 — Buscar indicadores

Búsqueda de texto libre en el catálogo completo de ESIOS (más de 1.000 indicadores).
Los resultados muestran ID, nombre completo y nombre corto.

### Pestaña 3 — Serie temporal

Descarga y visualización de la serie temporal de cualquier indicador:

- **Selector de indicador** por ID numérico o desde el desplegable de comunes
- **Presets de rango** de fechas: Últimas 48 h, Última semana, Último mes, Últimos 3 meses, Año pasado
- **Granularidades disponibles:** `five_minutes`, `ten_minutes`, `fifteen_minutes`, `hour`, `day`, `week`, `month`
- **Tarjetas de resumen:** nombre del indicador, unidad, granularidad y número de registros
- **Gráfico matplotlib** con área sombreada (una línea por zona geográfica cuando hay varias)
- **Tabla interactiva** con tipos de columna nativos de Streamlit
- **Descarga directa en CSV** con nombre de fichero dinámico

---

## Endpoints del backend

Todos los endpoints excepto `/health` e `/indicators/common` requieren el header `x-esios-token`.

| Método  | Ruta                        | Descripción                                                  |
| -------- | --------------------------- | ------------------------------------------------------------- |
| `GET`  | `/health`                 | Estado del servidor y versión de python-esios                |
| `POST` | `/validate-token`         | Verifica que el token es válido                              |
| `GET`  | `/indicators/common`      | Lista curada (sin token)                                      |
| `GET`  | `/indicators`             | Catálogo completo con búsqueda opcional (`?search=texto`) |
| `GET`  | `/indicators/{id}`        | Metadatos de un indicador                                     |
| `GET`  | `/indicators/{id}/values` | Serie temporal                                                |

### Parámetros de `/indicators/{id}/values`

| Parámetro     | Tipo   | Default       | Descripción                                        |
| -------------- | ------ | ------------- | --------------------------------------------------- |
| `start_date` | string | últimas 48 h | `YYYY-MM-DD` o ISO-8601                           |
| `end_date`   | string | hoy           | `YYYY-MM-DD` o ISO-8601                           |
| `time_trunc` | string | `hour`      | Granularidad temporal                               |
| `geo_ids`    | string | —            | IDs geográficos separados por coma, e.g.`3,8741` |

### Ejemplo con `curl`

```bash
curl -X GET "http://localhost:8000/indicators/600/values?start_date=2024-01-01&end_date=2024-01-07&time_trunc=hour" \
     -H "x-esios-token: TU_TOKEN_AQUI"
```

### Ejemplo con `requests`

```python
import requests

r = requests.get(
    "http://localhost:8000/indicators/600/values",
    headers={"x-esios-token": "TU_TOKEN_AQUI"},
    params={
        "start_date": "2024-01-01",
        "end_date":   "2024-01-07",
        "time_trunc": "hour",
    },
)
data = r.json()
print(f"{data['count']} registros — {data['name']} ({data['unit']})")
```

---

## Estructura del proyecto

```
esios_app/
├── backend.py               # FastAPI + python-esios
├── frontend_streamlit.py    # Interfaz Streamlit
├── frontend.py              # Interfaz Gradio (alternativa)
└── requirements.txt         # Dependencias
```

---

## Decisiones de diseño

### Por qué FastAPI como backend

El frontend (Streamlit o Gradio) se comunica con el backend vía HTTP en lugar de llamar a `python-esios` directamente. Esto permite:

- Cambiar el frontend sin tocar la lógica de datos
- Usar el mismo backend desde scripts, notebooks o cualquier otro cliente HTTP
- Gestionar el token en un único punto (el header `x-esios-token`)

### Por qué python-esios en el backend

La librería `python-esios` sustituye las llamadas HTTP manuales a `api.esios.ree.es` y aporta:

- **Chunking automático** de rangos largos (>3 semanas) sin código extra
- **Reintentos con backoff exponencial** ante errores de red
- **Cliente tipado** con excepciones propias (`AuthenticationError`, `NetworkError`, etc.)
- **Caché en disco** opcional (desactivada en el backend para garantizar datos frescos)

### Por qué `ThreadPoolExecutor` en el backend

`ESIOSClient` es un cliente síncrono. Los endpoints de FastAPI son `async`, por lo que el cliente se ejecuta en un pool de hilos para no bloquear el event loop:

```python
_executor = ThreadPoolExecutor(max_workers=8)

async def _run(fn, *args, **kwargs):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(_executor, partial(fn, *args, **kwargs))
```

### Streamlit vs Gradio

Ambos frontends son equivalentes en funcionalidad. Las diferencias principales son:

| Aspecto                    | Gradio                             | Streamlit                                            |
| -------------------------- | ---------------------------------- | ---------------------------------------------------- |
| Estado entre interacciones | Implícito en componentes          | Explícito en `session_state`                      |
| Token global               | `gr.Textbox` en zona principal   | Sidebar persistente                                  |
| Presets de fechas          | Eventos con `outputs` declarados | Botones que mutan `session_state` + `st.rerun()` |
| Exportación CSV           | Manual                             | `st.download_button` nativo                        |
| Tarjetas métricas         | No disponible                      | `st.metric` nativo                                 |

---

## Solución de problemas

**El backend no arranca**

Verifica que los puertos 8000 y 8501 estén libres:

```bash
lsof -i :8000
lsof -i :8501
```

**Error 401 — Token inválido**

- Comprueba que no hay espacios al inicio o final del token
- Verifica que el token no ha caducado contactando con consultasios@ree.es

**Sin datos para el rango seleccionado**

Algunos indicadores tienen cobertura histórica limitada o no están disponibles con todas las granularidades. El indicador 600 (precio spot) tiene cobertura horaria completa desde 2014 y es el más fiable para pruebas.

**Streamlit no recarga al cambiar un preset**

La app usa `st.rerun()` para refrescar los campos de fecha tras aplicar un preset. Si el botón no responde, recarga la página manualmente.

---

## Licencia

Este proyecto es de uso educativo. Los datos provienen de la API pública de REE/ESIOS y están sujetos a sus [condiciones de uso](https://www.ree.es/es/aviso-legal).
