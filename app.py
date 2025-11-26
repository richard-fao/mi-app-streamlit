# app.py
# Plantilla base para apps en Streamlit (Python 3.12+)
# Ejecuta:  streamlit run app.py

import time
from datetime import date
import numpy as np
import pandas as pd
import openpyxl
#import altair as alt
import streamlit as st
import plotly.express as px
import base64

# ---------------- Configuración general ----------------
st.set_page_config(
    page_title="Calificaciones PTIES - UdeA",
    page_icon="🧩",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get help": "https://docs.streamlit.io",
        "Report a bug": "https://github.com/streamlit/streamlit/issues",
        "About": "Página que muestra los resultados de las evaluaciones del proyecto PTIES"
    },
)

# ---------------- Función para cargar datos ----------------
@st.cache_data(show_spinner=False)
def load_example_data(filepath='Calificaciones_.xlsx') -> pd.DataFrame:
    """Carga los datos desde Excel y los cachea para mejorar el rendimiento."""
    df = pd.read_excel(filepath)
    return df

# ---------------- Carga de datos ----------------
df = load_example_data()

# ---------------- Título principal ----------------
t1,t2 = st.columns([0.55,0.45])
with t1:
    st.title("🧩 Calificaciones PTIES")
    col1, col2,col3 = st.columns([0.1,0.3,0.7])
    col1.image('IMAGENES/Escudo-UdeA.png', width=150)
    col2.markdown("**Universidad de Antioquia**")
t2.image('IMAGENES/PTT.png', width=600)



st.info("📊 **Notas de las evaluaciones:** Las pruebas de **Matemáticas** y **Lenguaje** se califican de **0 a 30 puntos cada una**. "
    "Cuando se combinan ambas, la calificación total va de **0 a 60 puntos**.")

# ---------------- Pestañas ----------------
tabs = st.tabs(['Resultados IEMs', 'Resultados Individuales'])

# --------------------- PESTAÑA RESULTADOS IEMS ---------------------
with tabs[0]:
    st.markdown(
    "⚡ **Filtros globales:** Todos los filtros que selecciones (región, IEM, grado, género y evaluación) afectan **toda la información mostrada en los gráficos y tablas a continuación**. "
    "Esto te permite analizar de manera consistente los resultados según tus criterios de selección."
    )
    # ---------------- Filtros ----------------
    f1, f2, f3, f4, f5 = st.columns(5)

    selected_region = f1.selectbox('Región', ['Todas'] + list(df['REGION'].unique()))
    selected_iem = f2.selectbox('IEM', ['Todas'] + list(df['NOMBRE IEM'].unique()))
    selected_grado = f3.selectbox('Grado', ['Todos', 10, 11])
    selected_evaluacion = f4.selectbox('Evaluación', ['Todas'] + list(df['EVALUACION'].unique()))
    selected_genero = f5.selectbox('Género', ['Todos', 'Masculino', 'Femenino'])

    # Filtrado de datos según selección
    df_filtered = df.copy()

    materias = '(Matemáticas y Lenguaje)'

    if selected_iem != 'Todas':
        df_filtered = df_filtered[df_filtered['NOMBRE IEM'] == selected_iem]
    if selected_region != 'Todos':
        df_filtered = df_filtered[df_filtered['REGION'] == selected_region]
    if selected_grado != 'Todos':
        df_filtered = df_filtered[df_filtered['GRADO'] == selected_grado]
    if selected_genero != 'Todos':
        df_filtered = df_filtered[df_filtered['GENERO'] == selected_genero]
    if selected_evaluacion != 'Todas':
        df_filtered = df_filtered[df_filtered['EVALUACION'] == selected_evaluacion]
        materias = f'({selected_evaluacion})'

    st.markdown("---")  # Separador visual

    # ---------------- Métricas ----------------
    m1, m2, m3 = st.columns(3)

    filtro_mat = df_filtered['EVALUACION'] == 'MATEMATICAS'
    filtro_len = df_filtered['EVALUACION'] == 'LENGUAJE'

    m1.metric("👨‍🎓 Estudiantes", f"{df_filtered['NUM_DOCUMENTO'].nunique():,}")
    m2.metric(
        "📐 Puntaje promedio Matemáticas",
        f"{df_filtered[filtro_mat]['CALIFICACION'].sum() / max(df_filtered[filtro_mat]['NUM_DOCUMENTO'].nunique(),1):.2f}"
    )
    m3.metric(
        "✍️ Puntaje promedio Lenguaje",
        f"{df_filtered[filtro_len]['CALIFICACION'].sum() / max(df_filtered[filtro_len]['NUM_DOCUMENTO'].nunique(),1):.2f}"
    )

    

    # ---------------- Gráfico de caja por IEM o municipio ----------------
    if selected_iem == 'Todas' and (selected_region == 'Todos' or selected_region == 'ANDINA'):
        df_box = df_filtered.groupby(['MUNICIPIO', 'NUM_DOCUMENTO', 'GRADO'])['CALIFICACION'].sum().reset_index()
        fig_box = px.box(
            df_box, x='MUNICIPIO', y='CALIFICACION', color='MUNICIPIO', points='all',
            title=f'Distribución de puntajes por IEM {materias}'
        )
        fig_box.update_layout(title_font=dict(size=20))
        st.plotly_chart(fig_box, use_container_width=True)
        st.markdown(
            "💡 Este gráfico muestra la distribución de puntajes por municipio. "
            "Cada punto representa a un estudiante y la caja muestra la dispersión de los puntajes."
        )

        # ---------------- Histograma promedio por grado ----------------
        fig_hist = px.histogram(
            df_box, x='MUNICIPIO', y='CALIFICACION', color='GRADO', barmode='group',
            title=f'Puntaje Promedio por IEM y Grado {materias}', histfunc='avg'
        )
        fig_hist.update_layout(title_font=dict(size=20))
        st.plotly_chart(fig_hist, use_container_width=True)

        st.divider()

        # ---------------- Tabla pivote con desempeño por competencia ----------------
        df_pivot = df_filtered.pivot_table(
            index='NOMBRE IEM', columns='COMPETENCIA', values='CALIFICACION',
            aggfunc=lambda x: np.round(x.mean() * 100, 2)
        )

        st.subheader("📊 Desempeño Promedio por Competencia (0-100)")
        st.dataframe(
            df_pivot.style.background_gradient(cmap='RdYlGn', text_color_threshold=0.5).format("{:.2f}"),
            use_container_width=True
        )

    else:
        # ---------------- Caso de un IEM o municipio específico ----------------
        df_box = df_filtered.groupby(['MUNICIPIO', 'NUM_DOCUMENTO', 'GRADO', 'EVALUACION'])['CALIFICACION'].sum().reset_index()
        fig_box = px.box(
            df_box, x='GRADO', y='CALIFICACION', color='EVALUACION', points='all',
            title='Distribución de puntajes por grado'
        )
        fig_box.update_layout(title_font=dict(size=20))
        st.plotly_chart(fig_box, use_container_width=True)
        
        # ------------ Desempeño Promedio por Competencia ---------------
        
        df_pivot = df_filtered.pivot_table(
            index='NOMBRE IEM', columns='COMPETENCIA', values='CALIFICACION',
            aggfunc=lambda x: np.round(x.mean() * 100, 2)
        )
        st.subheader("📊 Desempeño Promedio por Competencia (0-100)")
        st.dataframe(df_pivot, use_container_width=True)

    # ---------------- Gráfico de barras apiladas ----------------
    st.subheader("📊 Distribución porcentual por Competencia y Nivel de Desempeño")

    df_percent = df_filtered.groupby(['COMPETENCIA', 'NIVEL_DE_DESEMPENO']).size().reset_index(name='frecuencia')
    df_percent['porcentaje'] = df_percent.groupby('COMPETENCIA')['frecuencia'].apply(lambda x: 100 * x / x.sum()).values
    
    df_percent['COMPETENCIA_WRAP'] = df_percent['COMPETENCIA'].apply(
        lambda x: x.replace("-", "<br>", 1)  # solo primer salto; ajusta según necesites
    )
        
    fig_stack = px.bar(
        df_percent,
        x='COMPETENCIA_WRAP',
        y='porcentaje',
        color='NIVEL_DE_DESEMPENO',
        text='porcentaje',
        category_orders={'NIVEL_DE_DESEMPENO': ['BAJO', 'MEDIO', 'ALTO']},
        color_discrete_map={'BAJO':'#d62728', 'MEDIO':'#1f77b4', 'ALTO':'#2ca02c'}
    )
    fig_stack.update_traces(texttemplate='%{text:.1f}%', textposition='inside')
    fig_stack.update_layout(yaxis=dict(title='Porcentaje', range=[0, 100]), barmode='stack')
    st.plotly_chart(fig_stack)

    st.markdown(
        "💡 Este gráfico muestra la proporción de respuestas por nivel de desempeño en cada competencia. "
        "Las barras están apiladas y representan el 100% de las respuestas por competencia."
    )
    st.markdown("---")  # Separador visual
    # ---------------- Selección de competencia para evidencias ----------------
    st.info("Selecciona una competencia para ver información más detallada de lo que se está evaluando.")
    selected_competencia = st.selectbox('Competencia',
                                        ['Todas'] + list(df_filtered['COMPETENCIA'].unique()))

    if selected_competencia != 'Todas':
        df_filtered = df_filtered[df_filtered['COMPETENCIA'] == selected_competencia]

    st.subheader("📄 Competencias PTIES")
    st.dataframe(df_filtered['COMPETENCIA_PTIES'].value_counts().index, use_container_width=True)

    st.subheader("📄 Evidencias por Competencia")
    st.dataframe(df_filtered['EVIDENCIA'].value_counts().index, use_container_width=True)


    ###### PDFs SOCIOE  ###########
    st.markdown("---")  # Separador visual
    # Función para cargar el PDF
    def load_pdf(pdf_file):
        with open(pdf_file, "rb") as f:
            pdf_data = f.read()
        return pdf_data
    
    #st.markdown("## 💫 Expectativas, Intereses y Competencias Socioemocionales")
    st.markdown(
    """
    <h2 style='text-align: center; color: #2C3E50;'>
        <span style='font-size: 1.5em;'>💫</span> 
        Expectativas, Intereses y Competencias Socioemocionales
    </h2>
    """,
    unsafe_allow_html=True
)

    sel_municipio = st.selectbox('Municipios', ['Selección'] + list(set(df['MUNICIPIO'].unique())-{'TIBU','ANORI'}))
    if sel_municipio =='Selección':
        pass
    else:
        with open(f'SOCIOE/{sel_municipio}.pdf', "rb") as f:
            pdf_bytes = f.read()
            st.download_button(label="Abrir PDF",
                               data=pdf_bytes,
                               file_name=f"{sel_municipio}.pdf",
                               mime="application/pdf")


        # Cargar el PDF desde un archivo
        #pdf_data = load_pdf(f'SOCIOE/{sel_municipio}.pdf')
        
        #pdf_base64 = base64.b64encode(pdf_data).decode()
        
        #href = f'<a href="data:application/pdf;base64,{pdf_base64}" target="_blank">Abrir PDF en nueva pestaña</a>'
        
        #st.markdown(href, unsafe_allow_html=True)



# --------------------- PESTAÑA RESULTADOS INDIVIDUALES ---------------------
with tabs[1]:
    st.header("👤 Resultados Individuales")
    st.markdown(
        "Esta sección mostrará los resultados detallados de cada estudiante. "
    )
    selected_cod = st.text_input("Ingrese el código asociado al estudiante:")

    if selected_cod in df['NUM_DOCUMENTO'].unique():
        df_cod = df[df['NUM_DOCUMENTO']==selected_cod].copy()

        r1, r2, r3 = st.columns(3) 

        r1.metric(
            "Código",
            selected_cod
        )

        r2.metric(
            "📐 Puntaje Matemáticas",
            f"{df_cod[df_cod['EVALUACION']=='MATEMATICAS']['CALIFICACION'].sum():.2f}"
        )
        r3.metric(
            "✍️ Puntaje Lenguaje",
            f"{df_cod[df_cod['EVALUACION']=='LENGUAJE']['CALIFICACION'].sum():.2f}"
        )

        # ------------ Desempeño Promedio por Competencia ---------------
        
        df_pivot = df_cod.pivot_table(
            index='COMPETENCIA', columns='NUM_DOCUMENTO', values='CALIFICACION',
            aggfunc=lambda x: np.round(x.mean() * 100, 2)
        )
        st.subheader("📊 Desempeño Promedio por Competencia (0-100)")
        st.dataframe(df_pivot, use_container_width=True)


        # ---------------- Gráfico de barras apiladas ----------------
        st.subheader("📊 Distribución porcentual por Competencia y Nivel de Desempeño")

        df_percent = df_cod.groupby(['COMPETENCIA', 'NIVEL_DE_DESEMPENO']).size().reset_index(name='frecuencia')
        df_percent['porcentaje'] = df_percent.groupby('COMPETENCIA')['frecuencia'].apply(lambda x: 100 * x / x.sum()).values

        df_percent['COMPETENCIA_WRAP'] = df_percent['COMPETENCIA'].apply(
        lambda x: x.replace("-", "<br>", 1)  # solo primer salto; ajusta según necesites
        )
        
        fig_stack = px.bar(
            df_percent,
            x='COMPETENCIA_WRAP',
            y='porcentaje',
            color='NIVEL_DE_DESEMPENO',
            text='porcentaje',
            category_orders={'NIVEL_DE_DESEMPENO': ['BAJO', 'MEDIO', 'ALTO']},
            color_discrete_map={'BAJO':'#d62728', 'MEDIO':'#1f77b4', 'ALTO':'#2ca02c'}
        )
        fig_stack.update_traces(texttemplate='%{text:.1f}%', textposition='inside')
        fig_stack.update_layout(yaxis=dict(title='Porcentaje', range=[0, 100]), barmode='stack')
        st.plotly_chart(fig_stack)

        st.markdown(
            "💡 Este gráfico muestra la proporción de preguntas por nivel de desempeño en cada competencia. "
            "Las barras están apiladas y representan el 100% de las preguntas por competencia."
        )
        st.markdown("---")
        # Separador visual
        # ---------------- Selección de competencia para evidencias ----------------
        st.info("Selecciona una competencia para ver información más detallada de lo que se está evaluando.")
        selected_competencia_IND = st.selectbox('* Competencia',
                                            ['Todas'] + list(df_cod['COMPETENCIA'].unique()))

        if selected_competencia_IND != 'Todas':
            df_cod = df_cod[df_cod['COMPETENCIA'] == selected_competencia_IND]

        st.subheader("📄 Competencias PTIES")
        st.dataframe(df_cod['COMPETENCIA_PTIES'].value_counts().index, use_container_width=True)

        st.subheader("📄 Evidencias por Competencia")
        st.dataframe(df_cod['EVIDENCIA'].value_counts().index, use_container_width=True)

    elif selected_cod:
        st.markdown("⚠️ ¡Código no encontrado!")





# Please replace `use_container_width` with `width`.
# `use_container_width` will be removed after 2025-12-31.
# For `use_container_width=True`, use `width='stretch'`.
# For `use_container_width=False`, use `width='content'`.



### Codigo para dos graficos lado a lado

# Gráfico 1
# fig1 = px.bar(df, x='Grupo', y='Valor', color='Categoria', barmode='stack', title='Gráfico 1')
# fig1.update_layout(height=400)

# # Gráfico 2 (por ejemplo, otro tipo de gráfico)
# fig2 = px.pie(df, names='Categoria', values='Valor', title='Gráfico 2')
# fig2.update_layout(height=400)

# # Crear dos columnas
# col1, col2 = st.columns(2)

# with col1:
#     st.plotly_chart(fig1, use_container_width=True)

# with col2:
#     st.plotly_chart(fig2, use_container_width=True)






# # Aplica filtros globales
# if st.session_state.filtro_region != "Todas":
#     df = df[df["region"] == st.session_state.filtro_region]

# if isinstance(rango_fechas, tuple) and len(rango_fechas) == 2:
#     inicio, fin = pd.to_datetime(rango_fechas[0]), pd.to_datetime(rango_fechas[1])
#     df = df[(df["fecha"] >= inicio) & (df["fecha"] <= fin)]

# # ---------- Secciones ----------
# if page == "Inicio":
#     st.title("Resultados PTIES")
#     st.write('Universidad de Antioquia')

#     m1, m2, m3, m4 = st.columns(4)
#     m1.metric("Filas", f"{len(df):,}")
#     m2.metric("Valor promedio", f"{df['valor'].mean():.2f}")
#     m3.metric("Mínimo", f"{df['valor'].min():.2f}")
#     m4.metric("Máximo", f"{df['valor'].max():.2f}")

#     st.divider()

#     t1, t2 = st.tabs(["Gráfico (Altair)", "Tabla"])
#     with t1:
#         chart = (
#             alt.Chart(df)
#             .mark_line(point=True)
#             .encode(
#                 x="fecha:T",
#                 y=alt.Y("mean(valor):Q", title="Valor promedio"),
#                 color="categoria:N",
#                 tooltip=["fecha:T", "categoria:N", alt.Tooltip("valor:Q", format=".2f")]
#             )
#             .properties(height=360)
#             .interactive()
#         )
#         st.altair_chart(chart, use_container_width=True)

#     with t2:
#         st.dataframe(df, use_container_width=True, height=380)

# elif page == "Exploración":
#     st.title("🔎 Exploración")
#     st.write("Controles interactivos para explorar el dataset.")

#     c1, c2, c3 = st.columns([1, 1, 2])
#     with c1:
#         cat_sel = st.multiselect("Categorías", ["A", "B", "C"], default=["A", "B", "C"])
#     with c2:
#         agg = st.selectbox("Agregación", ["mean", "sum", "median"], index=0)
#     with c3:
#         st.write("")

#     df_f = df[df["categoria"].isin(cat_sel)] if cat_sel else df.head(0)

#     # Pivot simple
#     df_piv = df_f.groupby(["fecha", "categoria"], as_index=False)["valor"].agg(agg)
#     st.dataframe(df_piv, use_container_width=True, height=300)

#     st.divider()
#     # Barras por región
#     chart_bar = (
#         alt.Chart(df)
#         .mark_bar()
#         .encode(
#             x=alt.X("region:N", title="Región"),
#             y=alt.Y("mean(valor):Q", title=f"{agg.capitalize()} de valor"),
#             color="region:N",
#             column="categoria:N",
#             tooltip=[
#                 "region:N",
#                 "categoria:N",
#                 alt.Tooltip("valor:Q", aggregate=agg, title=f"{agg} valor", format=".2f"),
#             ],
#         )
#         .resolve_scale(y="independent")
#         .properties(height=280)
#     )
#     st.altair_chart(chart_bar, use_container_width=True)

# elif page == "Cargar datos":
#     st.title("📁 Cargar datos")
#     st.write("Carga un CSV para visualizarlo y validarlo.")

#     upl = st.file_uploader("Selecciona un archivo CSV", type=["csv"])
#     if upl is not None:
#         try:
#             df_up = pd.read_csv(upl)
#         except UnicodeDecodeError:
#             upl.seek(0)
#             df_up = pd.read_csv(upl, encoding="latin-1")
#         st.success(f"Archivo cargado con {len(df_up):,} filas y {len(df_up.columns)} columnas.")
#         st.dataframe(df_up.head(200), use_container_width=True, height=400)

#         with st.expander("Resumen rápido"):
#             col_a, col_b, col_c = st.columns(3)
#             col_a.write(df_up.describe(include="number"))
#             col_b.write(df_up.select_dtypes(exclude="number").describe())
#             col_c.write(pd.DataFrame({
#                 "nulos_total": df_up.isna().sum(),
#                 "% nulos": (df_up.isna().mean()*100).round(2)
#             }))

#         if st.button("Guardar CSV limpio (ejemplo)"):
#             with st.spinner("Procesando..."):
#                 time.sleep(0.8)
#                 # Aquí podrías aplicar limpieza real; este es un placeholder:
#                 path = "datos_limpios.csv"
#                 df_up.to_csv(path, index=False)
#             st.download_button("Descargar datos_limpios.csv", data=open(path, "rb"), file_name="datos_limpios.csv")
#     else:
#         st.info("Carga un CSV para continuar.")

# elif page == "Formulario":
#     st.title("📝 Formulario")
#     st.write("Ejemplo de formulario con validación y uso de estado.")

#     with st.form("demo_form"):
#         nombre = st.text_input("Nombre", placeholder="Tu nombre")
#         email = st.text_input("Email", placeholder="tu@correo.com")
#         fecha_ref = st.date_input("Fecha de referencia", value=date.today())
#         valor_num = st.number_input("Valor numérico", min_value=0.0, max_value=1000.0, value=100.0, step=1.0)
#         aceptar = st.checkbox("Acepto términos y condiciones")
#         enviado = st.form_submit_button("Enviar")

#     if enviado:
#         if not nombre or not email or not aceptar:
#             st.error("Completa *Nombre*, *Email* y acepta los términos.")
#         else:
#             st.success("Envío exitoso.")
#             st.json({"nombre": nombre, "email": email, "fecha": str(fecha_ref), "valor": valor_num})

# elif page == "Acerca de":
#     st.title("ℹ️ Acerca de")
#     st.markdown(
#         """
# **Secciones incluidas:**
# - Sidebar con navegación y filtros globales.
# - Cache de datos con `@st.cache_data`.
# - Estado con `st.session_state`.
# - Gráficos con Altair.
# - Carga y previsualización de CSV.
# - Formulario con validación.
# """
#     )
#     st.caption("Personaliza estilos con un archivo `.streamlit/config.toml` (tema). Ver docs de Streamlit.")

# # ---------- Footer sutil ----------
# st.write("")
# st.caption("Hecho con ❤️ + Streamlit")
