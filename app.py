# app.py
# Plantilla base para apps en Streamlit (Python 3.12+)
# Ejecuta:  streamlit run app.py

import time
from datetime import date
import numpy as np
import pandas as pd
import altair as alt
import streamlit as st
import plotly.express as px

# ---------------- Configuración general ----------------
st.set_page_config(
    page_title="Resultados PTIES - UdeA",
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
def load_example_data(filepath='Calificaciones.xlsx') -> pd.DataFrame:
    """Carga los datos desde Excel y los cachea para mejorar el rendimiento."""
    df = pd.read_excel(filepath)
    return df

# ---------------- Carga de datos ----------------
df = load_example_data()

# ---------------- Título principal ----------------
t1,t2 = st.columns([0.55,0.45])
with t1:
    st.title("🧩 Calificaciones PTIES")
    col1, col2,col3 = st.columns([0.1,0.3,0.6])
    col1.image('Escudo-UdeA.png', width=150)
    col2.markdown("**Universidad de Antioquia**")
t2.image('PTT.png', width=600)



st.info("📊 **Notas de las evaluaciones:** Las pruebas de **Matemáticas** y **Lenguaje** se califican de **0 a 30 puntos cada una**. "
    "Cuando se combinan ambas, la calificación total va de **0 a 60 puntos**.")

# ---------------- Pestañas ----------------
tabs = st.tabs(['Resultados IEMs', 'Resultados Individuales'])

# --------------------- PESTAÑA RESULTADOS IEMS ---------------------
with tabs[0]:
    st.markdown(
    "⚡ **Filtros globales:** Todos los filtros que selecciones (IEM, municipio, grado, género y evaluación) afectan **toda la información mostrada en los gráficos y tablas a continuación**. "
    "Esto te permite analizar de manera consistente los resultados según tus criterios de selección."
    )
    # ---------------- Filtros ----------------
    f1, f2, f3, f4, f5 = st.columns(5)

    selected_iem = f1.selectbox('IEMs', ['Todas'] + list(df['NOMBRE IEM'].unique()))
    selected_municipio = f2.selectbox('Municipios', ['Todos'] + list(df['MUNICIPIO'].unique()))
    selected_grado = f3.selectbox('Grado', ['Todos', 10, 11])
    selected_evaluacion = f4.selectbox('Evaluación', ['Todas'] + list(df['EVALUACION'].unique()))
    selected_genero = f5.selectbox('Género', ['Todos', 'Masculino', 'Femenino'])

    # Filtrado de datos según selección
    df_filtered = df.copy()

    materias = '(Matemáticas y Lenguaje)'

    if selected_iem != 'Todas':
        df_filtered = df_filtered[df_filtered['NOMBRE IEM'] == selected_iem]
    if selected_municipio != 'Todos':
        df_filtered = df_filtered[df_filtered['MUNICIPIO'] == selected_municipio]
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
    if selected_iem == 'Todas' and selected_municipio == 'Todos':
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

    fig_stack = px.bar(
        df_percent,
        x='COMPETENCIA',
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
        "💡 Este gráfico muestra la proporción de estudiantes por nivel de desempeño en cada competencia. "
        "Las barras están apiladas y representan el 100% de los estudiantes por competencia."
    )

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





# --------------------- PESTAÑA RESULTADOS INDIVIDUALES ---------------------
with tabs[1]:
    st.header("👤 Resultados Individuales")
    st.markdown(
        "Esta sección mostrará los resultados detallados de cada estudiante. "
        "Actualmente está en construcción."
    )

