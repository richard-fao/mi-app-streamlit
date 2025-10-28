# app.py
# Plantilla base para apps en Streamlit (Python 3.12+)
# Ejecuta:  streamlit run app.py

import time
from datetime import date
import numpy as np
import pandas as pd
import altair as alt
import streamlit as st

# ---------- Configuración general ----------
st.set_page_config(
    page_title="Plantilla Streamlit",
    page_icon="🧩",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get help": "https://docs.streamlit.io",
        "Report a bug": "https://github.com/streamlit/streamlit/issues",
        "About": "Plantilla minimal para iniciar proyectos en Streamlit."
    },
)

# ---------- Utilidades (cache, estado, helpers) ----------
@st.cache_data(show_spinner=False)
def load_example_data(rows: int = 200) -> pd.DataFrame:
    rng = np.random.default_rng(42)
    df = pd.DataFrame({
        "fecha": pd.date_range("2024-01-01", periods=rows, freq="D"),
        "categoria": rng.choice(["A", "B", "C"], size=rows),
        "valor": rng.normal(loc=100, scale=20, size=rows).round(2),
        "region": rng.choice(["Norte", "Centro", "Sur"], size=rows)
    })
    return df

def ensure_state_defaults():
    st.session_state.setdefault("filtro_region", "Todas")
    st.session_state.setdefault("contador_clicks", 0)

ensure_state_defaults()

# ---------- Sidebar ----------
with st.sidebar:
    st.header("⚙️ Configuración")
    st.caption("Ajusta los parámetros de la demo.")

    page = st.radio(
        "Secciones",
        ["Inicio", "Exploración", "Cargar datos", "Formulario", "Acerca de"],
        index=0,
        help="Navega por la app."
    )

    st.divider()

    st.subheader("Filtros globales")
    regiones = ["Todas", "Norte", "Centro", "Sur"]
    st.session_state.filtro_region = st.selectbox("Región", regiones, index=0)
    rango_fechas = st.date_input(
        "Rango de fechas",
        value=(date(2024, 1, 1), date(2024, 6, 30)),
        help="Filtra la ventana temporal."
    )

    st.divider()
    st.caption("💾 Estado")
    cols_btn = st.columns(2)
    if cols_btn[0].button("➕ Incrementar contador"):
        st.session_state.contador_clicks += 1
    if cols_btn[1].button("🔄 Reiniciar contador"):
        st.session_state.contador_clicks = 0
    st.write(f"Contador actual: **{st.session_state.contador_clicks}**")

# ---------- Datos base ----------
df = load_example_data()

# Aplica filtros globales
if st.session_state.filtro_region != "Todas":
    df = df[df["region"] == st.session_state.filtro_region]

if isinstance(rango_fechas, tuple) and len(rango_fechas) == 2:
    inicio, fin = pd.to_datetime(rango_fechas[0]), pd.to_datetime(rango_fechas[1])
    df = df[(df["fecha"] >= inicio) & (df["fecha"] <= fin)]

# ---------- Secciones ----------
if page == "Inicio":
    st.title("🧩 Plantilla Streamlit")
    st.write(
        "Usa esta plantilla como punto de partida: filtros globales en el sidebar, "
        "secciones con radio, cache de datos, estado de sesión y componentes comunes."
    )

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Filas", f"{len(df):,}")
    m2.metric("Valor promedio", f"{df['valor'].mean():.2f}")
    m3.metric("Mínimo", f"{df['valor'].min():.2f}")
    m4.metric("Máximo", f"{df['valor'].max():.2f}")

    st.divider()

    t1, t2 = st.tabs(["Gráfico (Altair)", "Tabla"])
    with t1:
        chart = (
            alt.Chart(df)
            .mark_line(point=True)
            .encode(
                x="fecha:T",
                y=alt.Y("mean(valor):Q", title="Valor promedio"),
                color="categoria:N",
                tooltip=["fecha:T", "categoria:N", alt.Tooltip("valor:Q", format=".2f")]
            )
            .properties(height=360)
            .interactive()
        )
        st.altair_chart(chart, use_container_width=True)

    with t2:
        st.dataframe(df, use_container_width=True, height=380)

elif page == "Exploración":
    st.title("🔎 Exploración")
    st.write("Controles interactivos para explorar el dataset.")

    c1, c2, c3 = st.columns([1, 1, 2])
    with c1:
        cat_sel = st.multiselect("Categorías", ["A", "B", "C"], default=["A", "B", "C"])
    with c2:
        agg = st.selectbox("Agregación", ["mean", "sum", "median"], index=0)
    with c3:
        st.write("")

    df_f = df[df["categoria"].isin(cat_sel)] if cat_sel else df.head(0)

    # Pivot simple
    df_piv = df_f.groupby(["fecha", "categoria"], as_index=False)["valor"].agg(agg)
    st.dataframe(df_piv, use_container_width=True, height=300)

    st.divider()
    # Barras por región
    chart_bar = (
        alt.Chart(df)
        .mark_bar()
        .encode(
            x=alt.X("region:N", title="Región"),
            y=alt.Y("mean(valor):Q", title=f"{agg.capitalize()} de valor"),
            color="region:N",
            column="categoria:N",
            tooltip=[
                "region:N",
                "categoria:N",
                alt.Tooltip("valor:Q", aggregate=agg, title=f"{agg} valor", format=".2f"),
            ],
        )
        .resolve_scale(y="independent")
        .properties(height=280)
    )
    st.altair_chart(chart_bar, use_container_width=True)

elif page == "Cargar datos":
    st.title("📁 Cargar datos")
    st.write("Carga un CSV para visualizarlo y validarlo.")

    upl = st.file_uploader("Selecciona un archivo CSV", type=["csv"])
    if upl is not None:
        try:
            df_up = pd.read_csv(upl)
        except UnicodeDecodeError:
            upl.seek(0)
            df_up = pd.read_csv(upl, encoding="latin-1")
        st.success(f"Archivo cargado con {len(df_up):,} filas y {len(df_up.columns)} columnas.")
        st.dataframe(df_up.head(200), use_container_width=True, height=400)

        with st.expander("Resumen rápido"):
            col_a, col_b, col_c = st.columns(3)
            col_a.write(df_up.describe(include="number"))
            col_b.write(df_up.select_dtypes(exclude="number").describe())
            col_c.write(pd.DataFrame({
                "nulos_total": df_up.isna().sum(),
                "% nulos": (df_up.isna().mean()*100).round(2)
            }))

        if st.button("Guardar CSV limpio (ejemplo)"):
            with st.spinner("Procesando..."):
                time.sleep(0.8)
                # Aquí podrías aplicar limpieza real; este es un placeholder:
                path = "datos_limpios.csv"
                df_up.to_csv(path, index=False)
            st.download_button("Descargar datos_limpios.csv", data=open(path, "rb"), file_name="datos_limpios.csv")
    else:
        st.info("Carga un CSV para continuar.")

elif page == "Formulario":
    st.title("📝 Formulario")
    st.write("Ejemplo de formulario con validación y uso de estado.")

    with st.form("demo_form"):
        nombre = st.text_input("Nombre", placeholder="Tu nombre")
        email = st.text_input("Email", placeholder="tu@correo.com")
        fecha_ref = st.date_input("Fecha de referencia", value=date.today())
        valor_num = st.number_input("Valor numérico", min_value=0.0, max_value=1000.0, value=100.0, step=1.0)
        aceptar = st.checkbox("Acepto términos y condiciones")
        enviado = st.form_submit_button("Enviar")

    if enviado:
        if not nombre or not email or not aceptar:
            st.error("Completa *Nombre*, *Email* y acepta los términos.")
        else:
            st.success("Envío exitoso.")
            st.json({"nombre": nombre, "email": email, "fecha": str(fecha_ref), "valor": valor_num})

elif page == "Acerca de":
    st.title("ℹ️ Acerca de")
    st.markdown(
        """
**Secciones incluidas:**
- Sidebar con navegación y filtros globales.
- Cache de datos con `@st.cache_data`.
- Estado con `st.session_state`.
- Gráficos con Altair.
- Carga y previsualización de CSV.
- Formulario con validación.
"""
    )
    st.caption("Personaliza estilos con un archivo `.streamlit/config.toml` (tema). Ver docs de Streamlit.")

# ---------- Footer sutil ----------
st.write("")
st.caption("Hecho con ❤️ + Streamlit")
