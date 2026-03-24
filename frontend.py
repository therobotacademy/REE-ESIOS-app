"""
frontend_streamlit.py — Interfaz Streamlit para probar la API de ESIOS (REE)

Equivalente funcional de frontend.py (Gradio), con el mismo backend FastAPI.

Pestañas:
  1. 📋 Indicadores comunes  — lista curada, sin token
  2. 🔍 Buscar indicadores   — búsqueda libre en el catálogo
  3. 📈 Serie temporal        — descarga + gráfico interactivo

Arranque:
  streamlit run frontend_streamlit.py
"""

import httpx
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta

# ---------------------------------------------------------------------------
# Configuración de página — DEBE ser la primera llamada Streamlit
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="ESIOS API Tester",
    page_icon="🔌",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------
BACKEND_URL = "http://localhost:8000"

INDICADORES_COMUNES = {
    600:   "600 — Precio mercado spot (OMIE) — €/MWh",
    10211: "10211 — Precio PVPC — €/MWh",
    1001:  "1001 — Demanda real — MW",
    1293:  "1293 — Generación eólica — MW",
    1292:  "1292 — Generación solar fotovoltaica — MW",
    1161:  "1161 — Generación hidráulica — MW",
    1163:  "1163 — Generación nuclear — MW",
}

TIME_TRUNC_OPTIONS = ["hour", "day", "week", "month", "five_minutes", "ten_minutes", "fifteen_minutes"]

DATE_PRESETS = {
    "Últimas 48 horas": (timedelta(hours=48), "hour"),
    "Última semana":    (timedelta(days=7),   "day"),
    "Último mes":       (timedelta(days=30),  "day"),
    "Últimos 3 meses":  (timedelta(days=90),  "week"),
    "Año pasado":       (timedelta(days=365), "week"),
}

RED_REE = "#E31E24"

# ---------------------------------------------------------------------------
# Session state — inicializar claves la primera vez
# ---------------------------------------------------------------------------
_DEFAULTS = {
    "token":         "",
    "token_status":  "",           # mensaje de validación
    "start_date":    (datetime.utcnow() - timedelta(hours=48)).strftime("%Y-%m-%d"),
    "end_date":      datetime.utcnow().strftime("%Y-%m-%d"),
    "time_trunc":    "hour",
    "indicator_id":  "600",
    "series_df":     None,         # DataFrame con la serie descargada
    "series_meta":   {},           # metadatos de la última descarga
}
for k, v in _DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ---------------------------------------------------------------------------
# Helpers HTTP
# ---------------------------------------------------------------------------
def _headers() -> dict:
    return {"x-esios-token": st.session_state.token.strip()}


def _get(path: str, params: dict | None = None, timeout: int = 30) -> dict:
    r = httpx.get(f"{BACKEND_URL}{path}", headers=_headers(), params=params, timeout=timeout)
    r.raise_for_status()
    return r.json()


# ---------------------------------------------------------------------------
# Helpers de gráfico
# ---------------------------------------------------------------------------
def _build_figure(df: pd.DataFrame, meta: dict) -> plt.Figure:
    """Construye la figura matplotlib a partir del DataFrame de la serie."""
    name    = meta.get("Indicador", "Indicador")
    unit    = meta.get("Unidad", "")
    records = meta.get("Registros", len(df))

    if "Zona" in df.columns and df["Zona"].nunique() > 1:
        pivot = df.pivot_table(index="Fecha", columns="Zona", values="Valor", aggfunc="mean")
        fig, ax = plt.subplots(figsize=(12, 4))
        pivot.plot(ax=ax, linewidth=1.2)
        ax.legend(fontsize=8, loc="upper right")
    else:
        fig, ax = plt.subplots(figsize=(12, 4))
        ax.plot(df["Fecha"], df["Valor"], linewidth=1.5, color=RED_REE)
        ax.fill_between(df["Fecha"], df["Valor"], alpha=0.08, color=RED_REE)

    ax.set_title(f"{name}  ({records:,} registros)", fontsize=13, fontweight="bold")
    ax.set_ylabel(unit, fontsize=10)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m\n%H:%M"))
    ax.grid(alpha=0.3, linestyle="--")
    fig.autofmt_xdate(rotation=0)
    fig.tight_layout()
    return fig


def _parse_series(data: dict) -> tuple[pd.DataFrame, dict]:
    """Convierte la respuesta JSON del backend en (DataFrame, meta)."""
    values = data.get("values", [])
    if not values:
        return pd.DataFrame(), {}

    df = pd.DataFrame(values)
    date_col = "datetime" if "datetime" in df.columns else "datetime_utc"
    df[date_col] = pd.to_datetime(df[date_col], utc=True, errors="coerce")
    df = df.sort_values(date_col).reset_index(drop=True)

    cols = [c for c in [date_col, "geo_name", "value"] if c in df.columns]
    df = df[cols].rename(columns={date_col: "Fecha", "geo_name": "Zona", "value": "Valor"})

    meta = {
        "Indicador":   data.get("name", ""),
        "Unidad":      data.get("unit", ""),
        "Granularidad": data.get("time_trunc", ""),
        "Desde":       data.get("start_date", ""),
        "Hasta":       data.get("end_date", ""),
        "Registros":   data.get("count", 0),
    }
    return df, meta


# ---------------------------------------------------------------------------
# CSS mínimo
# ---------------------------------------------------------------------------
st.markdown("""
<style>
    /* Cabecera roja */
    .ree-header {
        background: #1A1A2E;
        border-bottom: 4px solid #E31E24;
        padding: 1rem 1.5rem 0.75rem;
        border-radius: 6px;
        margin-bottom: 1rem;
    }
    .ree-header h1 { color: white; margin: 0; font-size: 1.6rem; }
    .ree-header p  { color: #aaa;   margin: 0.2rem 0 0; font-size: 0.9rem; }

    /* Tarjeta de métrica */
    .metric-card {
        background: #f0f4ff;
        border-left: 4px solid #2E5FA3;
        padding: 0.5rem 0.8rem;
        border-radius: 4px;
        margin-bottom: 0.4rem;
        font-size: 0.9rem;
    }
    .metric-card strong { color: #2E5FA3; }

    /* Reducir padding de tabs */
    .stTabs [data-baseweb="tab-panel"] { padding-top: 1rem; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Cabecera principal
# ---------------------------------------------------------------------------
st.markdown("""
<div class="ree-header">
  <h1>🔌 ESIOS / REE API Tester</h1>
  <p>Herramienta para explorar la API pública de Red Eléctrica de España (REE) a través de ESIOS.</p>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Sidebar — Token global
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("🔑 Token ESIOS")
    st.caption("Introduce tu token personal de [api.esios.ree.es](https://api.esios.ree.es)")

    token_input = st.text_input(
        "Token",
        value=st.session_state.token,
        type="password",
        placeholder="Pega aquí tu token...",
        label_visibility="collapsed",
    )
    st.session_state.token = token_input

    if st.button("✅ Validar token", use_container_width=True):
        if not token_input.strip():
            st.session_state.token_status = "⚠️ Introduce tu token primero."
        else:
            with st.spinner("Validando..."):
                try:
                    r = httpx.post(
                        f"{BACKEND_URL}/validate-token",
                        headers={"x-esios-token": token_input.strip()},
                        timeout=15,
                    )
                    data = r.json()
                    icon = "✅" if data.get("valid") else "❌"
                    st.session_state.token_status = f"{icon} {data.get('message', '')}"
                except Exception as e:
                    st.session_state.token_status = f"❌ Error: {e}"

    if st.session_state.token_status:
        st.info(st.session_state.token_status)

    st.divider()

    # Estado del backend
    st.caption("**Estado del backend**")
    try:
        health = httpx.get(f"{BACKEND_URL}/health", timeout=3).json()
        st.success(f"Backend OK · {health.get('esios_library', '')}")
    except Exception:
        st.error("Backend no disponible en localhost:8000")

    st.divider()
    st.caption(
        "💡 **Cómo obtener el token**: escribe a consultasios@ree.es "
        "o regístrate en api.esios.ree.es. Recibirás respuesta en 1–2 días."
    )

# ---------------------------------------------------------------------------
# Pestañas principales
# ---------------------------------------------------------------------------
tab_common, tab_search, tab_series = st.tabs([
    "📋 Indicadores comunes",
    "🔍 Buscar indicadores",
    "📈 Serie temporal",
])

# ────────────────────────────────────────────────────────────────────────────
# Pestaña 1 — Indicadores comunes
# ────────────────────────────────────────────────────────────────────────────
with tab_common:
    st.subheader("Indicadores del mercado eléctrico español")
    st.caption("Lista curada de los indicadores más relevantes. No requiere token.")

    if st.button("Cargar lista", type="primary", key="btn_common"):
        with st.spinner("Cargando..."):
            try:
                data = httpx.get(f"{BACKEND_URL}/indicators/common", timeout=10).json()
                rows = [
                    {"ID": ind["id"], "Descripción": ind["description"]}
                    for ind in data.get("indicators", [])
                ]
                st.dataframe(
                    pd.DataFrame(rows),
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "ID": st.column_config.NumberColumn("ID", width="small"),
                        "Descripción": st.column_config.TextColumn("Descripción", width="large"),
                    },
                )
            except Exception as e:
                st.error(f"Error: {e}")

# ────────────────────────────────────────────────────────────────────────────
# Pestaña 2 — Buscar indicadores
# ────────────────────────────────────────────────────────────────────────────
with tab_search:
    st.subheader("Búsqueda en el catálogo ESIOS")
    st.caption("Filtra por texto en el nombre del indicador. Requiere token.")

    col_txt, col_btn = st.columns([4, 1])
    with col_txt:
        search_text = st.text_input(
            "Texto a buscar",
            placeholder="solar, eólica, precio, demanda...",
            label_visibility="collapsed",
        )
    with col_btn:
        search_btn = st.button("Buscar", type="primary", use_container_width=True, key="btn_search")

    if search_btn:
        if not st.session_state.token.strip():
            st.warning("Introduce tu token ESIOS en la barra lateral.")
        else:
            with st.spinner("Buscando..."):
                try:
                    params = {}
                    if search_text.strip():
                        params["search"] = search_text.strip()
                    data = _get("/indicators", params=params, timeout=25)
                    rows = [
                        {
                            "ID":           ind.get("id"),
                            "Nombre":       ind.get("name", ""),
                            "Nombre corto": ind.get("short_name", ""),
                        }
                        for ind in data.get("indicators", [])
                    ]
                    if rows:
                        st.caption(f"{data.get('count', len(rows))} resultados")
                        st.dataframe(
                            pd.DataFrame(rows),
                            use_container_width=True,
                            hide_index=True,
                            column_config={
                                "ID": st.column_config.NumberColumn("ID", width="small"),
                                "Nombre": st.column_config.TextColumn("Nombre", width="large"),
                                "Nombre corto": st.column_config.TextColumn("Nombre corto"),
                            },
                        )
                    else:
                        st.info("Sin resultados para esa búsqueda.")
                except httpx.HTTPStatusError as e:
                    st.error(f"Error {e.response.status_code}: {e.response.json().get('detail', str(e))}")
                except Exception as e:
                    st.error(f"Error: {e}")

# ────────────────────────────────────────────────────────────────────────────
# Pestaña 3 — Serie temporal
# ────────────────────────────────────────────────────────────────────────────
with tab_series:
    st.subheader("Descarga y visualización de series temporales")

    # ── Selector de indicador ────────────────────────────────────────────────
    col_id, col_preset_ind = st.columns([1, 3])
    with col_id:
        indicator_id = st.text_input(
            "ID del indicador",
            value=st.session_state.indicator_id,
            key="indicator_id_input",
        )
        st.session_state.indicator_id = indicator_id

    with col_preset_ind:
        opciones = ["(selecciona un indicador común)"] + list(INDICADORES_COMUNES.values())
        sel = st.selectbox("O elige un indicador común", opciones, label_visibility="visible")
        if sel != opciones[0]:
            # Extrae el ID de la cadena "600 — Precio..."
            st.session_state.indicator_id = sel.split(" — ")[0].strip()
            st.rerun()

    st.divider()

    # ── Presets de fechas ────────────────────────────────────────────────────
    st.caption("**Rango de fechas rápido:**")
    preset_cols = st.columns(len(DATE_PRESETS))
    for col, (label, (delta, trunc)) in zip(preset_cols, DATE_PRESETS.items()):
        with col:
            if st.button(label, use_container_width=True, key=f"preset_{label}"):
                now = datetime.utcnow()
                st.session_state.start_date = (now - delta).strftime("%Y-%m-%d")
                st.session_state.end_date   = now.strftime("%Y-%m-%d")
                st.session_state.time_trunc = trunc
                st.rerun()

    # ── Controles de fecha y granularidad ────────────────────────────────────
    col_start, col_end, col_trunc = st.columns([2, 2, 1])
    with col_start:
        start_date = st.text_input(
            "Fecha inicio (YYYY-MM-DD)",
            value=st.session_state.start_date,
            key="start_date_input",
        )
        st.session_state.start_date = start_date

    with col_end:
        end_date = st.text_input(
            "Fecha fin (YYYY-MM-DD)",
            value=st.session_state.end_date,
            key="end_date_input",
        )
        st.session_state.end_date = end_date

    with col_trunc:
        trunc_idx = TIME_TRUNC_OPTIONS.index(st.session_state.time_trunc) \
                    if st.session_state.time_trunc in TIME_TRUNC_OPTIONS else 0
        time_trunc = st.selectbox(
            "Granularidad",
            TIME_TRUNC_OPTIONS,
            index=trunc_idx,
            key="time_trunc_input",
        )
        st.session_state.time_trunc = time_trunc

    # ── Botón de descarga ────────────────────────────────────────────────────
    fetch_btn = st.button("⬇️  Descargar serie", type="primary", use_container_width=True)

    if fetch_btn:
        if not st.session_state.token.strip():
            st.warning("Introduce tu token ESIOS en la barra lateral.")
        elif not st.session_state.indicator_id.strip():
            st.warning("Introduce un ID de indicador.")
        else:
            try:
                iid = int(st.session_state.indicator_id.strip())
            except ValueError:
                st.error("El ID del indicador debe ser un número entero.")
                st.stop()

            params = {
                "start_date": st.session_state.start_date,
                "end_date":   st.session_state.end_date,
                "time_trunc": st.session_state.time_trunc,
            }
            with st.spinner(f"Descargando indicador {iid}..."):
                try:
                    data = _get(f"/indicators/{iid}/values", params=params, timeout=60)
                    df, meta = _parse_series(data)
                    st.session_state.series_df   = df
                    st.session_state.series_meta = meta
                except httpx.HTTPStatusError as e:
                    detail = e.response.json().get("detail", str(e))
                    st.error(f"Error {e.response.status_code}: {detail}")
                    st.session_state.series_df   = None
                    st.session_state.series_meta = {}
                except Exception as e:
                    st.error(f"Error: {e}")
                    st.session_state.series_df   = None
                    st.session_state.series_meta = {}

    # ── Resultados ───────────────────────────────────────────────────────────
    df   = st.session_state.series_df
    meta = st.session_state.series_meta

    if df is not None and not df.empty:

        # Métricas de resumen
        st.divider()
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Indicador",   meta.get("Indicador", "—"))
        m2.metric("Unidad",      meta.get("Unidad", "—"))
        m3.metric("Granularidad", meta.get("Granularidad", "—"))
        m4.metric("Registros",   f"{meta.get('Registros', 0):,}")

        # Gráfico
        st.pyplot(_build_figure(df, meta), use_container_width=True)

        # Tabla + descarga
        col_table, col_export = st.columns([4, 1])
        with col_table:
            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Fecha": st.column_config.DatetimeColumn("Fecha", format="DD/MM/YYYY HH:mm"),
                    "Zona":  st.column_config.TextColumn("Zona"),
                    "Valor": st.column_config.NumberColumn("Valor", format="%.4f"),
                },
            )
        with col_export:
            st.download_button(
                label="⬇️ Descargar CSV",
                data=df.to_csv(index=False).encode("utf-8"),
                file_name=f"esios_{st.session_state.indicator_id}_{st.session_state.start_date}_{st.session_state.end_date}.csv",
                mime="text/csv",
                use_container_width=True,
            )

    elif df is not None and df.empty:
        st.info("Sin datos para ese rango de fechas y granularidad.")
