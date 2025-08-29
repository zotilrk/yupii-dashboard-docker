import streamlit as st

# Configuración de la página
st.set_page_config(
    page_title="Yupii Dashboard Hub",
    page_icon="🎯",
    layout="wide"
)

# Título principal
st.title("🎯 Yupii Dashboard Hub")
st.markdown("---")

# Crear columnas para los dashboards
col1, col2 = st.columns(2)

with col1:
    st.header("📊 Dashboard Principal")
    st.markdown("""
    **Análisis de Datos Individual**
    - Carga de archivos desde S3
    - Análisis exploratorio de datos
    - Visualizaciones interactivas
    - Estadísticas descriptivas
    """)
    
    if st.button("🚀 Abrir Dashboard Principal", key="main_dash"):
        st.switch_page("pages/main_dashboard.py")

with col2:
    st.header("🌍 Dashboard Global")
    st.markdown("""
    **Análisis de Datos Global**
    - Vista consolidada de datos
    - Análisis comparativo
    - Métricas globales
    - Tendencias generales
    """)
    
    if st.button("🚀 Abrir Dashboard Global", key="global_dash"):
        st.switch_page("pages/global_dashboard.py")

# Información adicional
st.markdown("---")
st.info("📡 **Estado de Conexión S3:** ✅ Conectado al bucket `xideralaws-curso-carlos`")
