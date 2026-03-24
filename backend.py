"""
backend.py — FastAPI wrapper para la API de ESIOS (REE)
Usa la librería python-esios (pip install python-esios) en lugar de llamadas
HTTP manuales.

Endpoints:
  GET  /health                     → estado del servidor y versión de la librería
  POST /validate-token             → verificar si el token es válido
  GET  /indicators/common          → lista curada de indicadores (sin token)
  GET  /indicators                 → búsqueda en el catálogo (texto libre)
  GET  /indicators/{id}            → metadatos de un indicador
  GET  /indicators/{id}/values     → serie temporal con rango de fechas
"""

from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from functools import partial
from typing import Optional

import pandas as pd
from fastapi import FastAPI, HTTPException, Query, Header
from fastapi.middleware.cors import CORSMiddleware

from esios import ESIOSClient, __version__ as ESIOS_VERSION
from esios.exceptions import AuthenticationError, APIResponseError, NetworkError, ESIOSError

# ---------------------------------------------------------------------------
# Threadpool para ejecutar el cliente síncrono desde endpoints async
# ---------------------------------------------------------------------------
_executor = ThreadPoolExecutor(max_workers=8, thread_name_prefix="esios")


async def _run(fn, *args, **kwargs):
    """Ejecuta una función síncrona en el threadpool sin bloquear el event loop."""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(_executor, partial(fn, *args, **kwargs))


# ---------------------------------------------------------------------------
# Indicadores curados
# ---------------------------------------------------------------------------
INDICADORES_COMUNES = {
    600:   "Precio mercado spot (OMIE) — €/MWh",
    10211: "Precio PVPC — €/MWh",
    1001:  "Demanda real — MW",
    1293:  "Generación eólica — MW",
    1292:  "Generación solar fotovoltaica — MW",
    1161:  "Generación hidráulica — MW",
    1163:  "Generación nuclear — MW",
    545:   "CO₂ evitado por renovables — tCO₂",
    776:   "Potencia instalada solar FV — MW",
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _client(token: str) -> ESIOSClient:
    """Crea un ESIOSClient con el token dado. Sin caché para peticiones web."""
    return ESIOSClient(token=token.strip(), cache=False)


def _esios_error_to_http(exc: ESIOSError) -> HTTPException:
    """Convierte excepciones de python-esios en HTTPException de FastAPI."""
    if isinstance(exc, AuthenticationError):
        return HTTPException(status_code=401, detail="Token ESIOS inválido o expirado.")
    if isinstance(exc, APIResponseError):
        return HTTPException(status_code=exc.status_code, detail=str(exc))
    if isinstance(exc, NetworkError):
        return HTTPException(status_code=503, detail=f"Error de red: {exc}")
    return HTTPException(status_code=500, detail=str(exc))


def _df_to_records(df: pd.DataFrame) -> list[dict]:
    """Serializa un DataFrame wide (DatetimeIndex, columnas = geo_name) a lista de dicts."""
    if df.empty:
        return []
    df = df.copy()
    df.index = df.index.astype(str)
    records = []
    for col in df.columns:
        for dt_str, value in df[col].items():
            if pd.notna(value):
                records.append({
                    "datetime": dt_str,
                    "geo_name": col,
                    "value": round(float(value), 4),
                })
    records.sort(key=lambda r: (r["datetime"], r["geo_name"]))
    return records


# ---------------------------------------------------------------------------
# App FastAPI
# ---------------------------------------------------------------------------
app = FastAPI(
    title="ESIOS REE API Tester",
    description=(
        "Backend para la app ESIOS API Tester. "
        f"Usa python-esios v{ESIOS_VERSION} como cliente."
    ),
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/health")
def health():
    return {
        "status": "ok",
        "backend_version": "2.0.0",
        "esios_library": f"python-esios v{ESIOS_VERSION}",
    }


@app.post("/validate-token")
async def validate_token(token: str = Header(..., alias="x-esios-token")):
    """Verifica que el token ESIOS es válido haciendo una petición autenticada
    mínima (1 día de datos del indicador 1001 — Demanda real)."""
    def _check(tok: str) -> dict:
        yesterday = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")
        today     = datetime.utcnow().strftime("%Y-%m-%d")
        with _client(tok) as c:
            handle = c.indicators.get(1001)
            handle.historical(yesterday, today, time_trunc="day")
        return {"valid": True, "message": "Token correcto ✓"}

    try:
        return await _run(_check, token)
    except AuthenticationError:
        return {"valid": False, "message": "Token ESIOS inválido o expirado."}
    except ESIOSError as e:
        return {"valid": False, "message": str(e)}


@app.get("/indicators/common")
def indicators_common():
    """Devuelve la lista curada de indicadores relevantes. No requiere token."""
    return {
        "count": len(INDICADORES_COMUNES),
        "indicators": [
            {"id": k, "description": v} for k, v in INDICADORES_COMUNES.items()
        ],
    }


@app.get("/indicators")
async def list_indicators(
    token: str = Header(..., alias="x-esios-token"),
    search: Optional[str] = Query(None, description="Texto a buscar en el nombre"),
):
    """
    Devuelve el catálogo de indicadores ESIOS.
    Con search filtra por nombre (substring, insensible a mayúsculas).
    La librería cachea el catálogo en disco para acelerar llamadas sucesivas.
    """
    def _fetch(tok: str, query: Optional[str]) -> list[dict]:
        with _client(tok) as c:
            if query:
                df = c.indicators.search(query)
            else:
                df = c.indicators.list()
        if df.empty:
            return []
        df = df.reset_index()
        keep = [col for col in ["id", "name", "short_name"] if col in df.columns]
        return df[keep].fillna("").to_dict(orient="records")

    try:
        rows = await _run(_fetch, token, search)
    except ESIOSError as e:
        raise _esios_error_to_http(e) from e

    return {"query": search or "", "count": len(rows), "indicators": rows}


@app.get("/indicators/{indicator_id}")
async def get_indicator_metadata(
    indicator_id: int,
    token: str = Header(..., alias="x-esios-token"),
):
    """Devuelve los metadatos de un indicador usando IndicatorHandle."""
    def _fetch(tok: str, iid: int) -> dict:
        with _client(tok) as c:
            handle = c.indicators.get(iid)
        meta = handle.metadata
        return {
            "id": handle.id,
            "name": handle.name,
            "short_name": meta.get("short_name", ""),
            "description": meta.get("description", ""),
            "unit": meta.get("unit", {}).get("name", "") if isinstance(meta.get("unit"), dict) else "",
            "step_type": meta.get("step_type", ""),
            "time_agg": meta.get("time_agg", ""),
            "geos": handle.geos,
        }

    try:
        return await _run(_fetch, token, indicator_id)
    except ESIOSError as e:
        raise _esios_error_to_http(e) from e


@app.get("/indicators/{indicator_id}/values")
async def get_indicator_values(
    indicator_id: int,
    token: str = Header(..., alias="x-esios-token"),
    start_date: str = Query(
        default=None,
        description="Fecha inicio YYYY-MM-DD o ISO-8601",
    ),
    end_date: str = Query(
        default=None,
        description="Fecha fin YYYY-MM-DD o ISO-8601",
    ),
    time_trunc: str = Query(
        default="hour",
        description="Granularidad: five_minutes | ten_minutes | fifteen_minutes | hour | day | week | month | year",
    ),
    geo_ids: Optional[str] = Query(
        default=None,
        description="IDs geográficos separados por coma, e.g. '3,8741'",
    ),
):
    """
    Descarga la serie temporal de un indicador con ESIOSClient.indicators.get().historical().

    La librería python-esios:
      - Divide automáticamente rangos largos en chunks de ~3 semanas.
      - Devuelve un DataFrame con DatetimeIndex y una columna por zona geográfica.
      - Gestiona reintentos automáticos ante errores de red.
    """
    now = datetime.utcnow()
    start = start_date or (now - timedelta(hours=48)).strftime("%Y-%m-%d")
    end   = end_date   or now.strftime("%Y-%m-%d")

    geo_list: Optional[list[int]] = None
    if geo_ids:
        try:
            geo_list = [int(g.strip()) for g in geo_ids.split(",") if g.strip()]
        except ValueError:
            raise HTTPException(status_code=422, detail="geo_ids debe ser una lista de enteros separados por coma.")

    def _fetch(tok, iid, s, e, trunc, geos):
        with _client(tok) as c:
            handle = c.indicators.get(iid)
            df = handle.historical(s, e, time_trunc=trunc, geo_ids=geos)
        meta = handle.metadata
        unit = meta.get("unit", {}).get("name", "") if isinstance(meta.get("unit"), dict) else ""
        return {
            "indicator_id": iid,
            "name": handle.name or "",
            "unit": unit,
            "time_trunc": trunc,
            "start_date": s,
            "end_date": e,
            "count": len(df),
            "values": _df_to_records(df),
        }

    try:
        return await _run(_fetch, token, indicator_id, start, end, time_trunc, geo_list)
    except ESIOSError as e:
        raise _esios_error_to_http(e) from e
