import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
from datetime import datetime
from s3_manager import S3Manager
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Inicializar S3 Manager
s3_manager = S3Manager()

# Colores Yupii
YUPII_BLUE = "#185E8D"
YUPII_CYAN = "#00AEEF"
YUPII_BLACK = "#000000"
YUPII_GRADIENT = f"linear-gradient(90deg, {YUPII_BLUE} 0%, {YUPII_CYAN} 100%)"

st.set_page_config(
    page_title="Dashboard Global Yupii",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Aplicar estilos corporativos
st.markdown(f"""
    <style>
    .main {{
        background: {YUPII_GRADIENT};
        color: white;
    }}
    .stApp {{
        background: {YUPII_GRADIENT};
    }}
    .stButton>button {{
        background-color: {YUPII_CYAN};
        color: {YUPII_BLACK};
        font-weight: bold;
        border-radius: 8px;
        border: none;
    }}
    .metric-card {{
        background-color: rgba(255, 255, 255, 0.1);
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid {YUPII_CYAN};
    }}
    .s3-status {{
        padding: 0.5rem;
        border-radius: 5px;
        margin-bottom: 1rem;
    }}
    .s3-connected {{
        background-color: rgba(0, 255, 0, 0.1);
        color: #00ff00;
        border: 1px solid #00ff00;
    }}
    .s3-disconnected {{
        background-color: rgba(255, 0, 0, 0.1);
        color: #ff6b6b;
        border: 1px solid #ff6b6b;
    }}
    </style>
""", unsafe_allow_html=True)

# Verificar conexión S3
s3_connected = s3_manager.test_connection()

# Mostrar estado de conexión S3
if s3_connected:
    st.markdown("""
    <div class="s3-status s3-connected">
        ✅ Conectado a AWS S3 - Dataset global disponible desde la nube
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <div class="s3-status s3-disconnected">
        ❌ Sin conexión a AWS S3 - Verificar credenciales y configuración
    </div>
    """, unsafe_allow_html=True)

# Emojis de reparto
EMOJI_MOTO = "🏍️"
EMOJI_PAQUETE = "📦"
EMOJI_COMIDA = "🍔"
EMOJI_ENTREGA = "🛵"
EMOJI_REPARTIDOR = "🧑🏾‍🦱‍🛵"
EMOJI_GLOBAL = "🌍"
EMOJI_CALENDARIO = "📅"

# Función global para limpiar establecimientos
def limpiar_establecimientos(establecimiento):
    """
    Limpia nombres de establecimientos removiendo valores no válidos.
    
    Args:
        establecimiento (str): Nombre del establecimiento a limpiar
        
    Returns:
        str or None: Nombre limpio del establecimiento o None si no es válido
    """
    establecimiento = str(establecimiento).strip()
    if establecimiento.lower() in ["donde sea", "DONDE SEA", "-", "", "nan", "NaN"]:
        return None
    return establecimiento

# Función para normalizar y unificar nombres de establecimientos similares
def normalizar_establecimiento(establecimiento):
    """
    Normaliza nombres de establecimientos para unificar variaciones del mismo negocio.
    
    Args:
        establecimiento (str): Nombre del establecimiento a normalizar
        
    Returns:
        str: Nombre normalizado del establecimiento
    """
    if not establecimiento or pd.isna(establecimiento):
        return establecimiento
    
    # Convertir a string y limpiar
    nombre = str(establecimiento).strip().lower()
    
    # Diccionario de normalizaciones - agregar más según sea necesario
    normalizaciones = {
        # Tacomarin y variaciones
        "tacomarin": ["tacomarin centro", "taco marin", "taco marin centro", "tacomarin", "taco-marin"],
        
        # McDonald's y variaciones
        "mcdonalds": ["mc donalds", "mc donald's", "mcdonald's", "macdonalds", "mac donalds"],
        
        # KFC y variaciones
        "kfc": ["kentucky fried chicken", "k.f.c", "kfc", "kentucky"],
        
        # Burger King y variaciones
        "burger king": ["burger king", "burgerking", "bk", "burger-king"],
        
        # Pizza Hut y variaciones
        "pizza hut": ["pizza hut", "pizzahut", "pizza-hut"],
        
        # Domino's y variaciones
        "dominos": ["domino's", "dominos", "domino", "dominos pizza"],
        
        # Subway y variaciones
        "subway": ["subway", "sub way", "sub-way"],
        
        # Starbucks y variaciones
        "starbucks": ["starbucks", "star bucks", "star-bucks"],
        
        # Agregar más establecimientos comunes aquí...
    }
    
    # Buscar coincidencias y normalizar
    for nombre_unificado, variaciones in normalizaciones.items():
        for variacion in variaciones:
            if variacion in nombre:
                return nombre_unificado.title()
    
    # Normalizaciones adicionales para casos comunes
    # Remover palabras comunes que pueden variar
    palabras_a_remover = [" centro", " local", " sucursal", " principal", " #1", " no. 1", " numero 1"]
    nombre_limpio = nombre
    for palabra in palabras_a_remover:
        nombre_limpio = nombre_limpio.replace(palabra, "")
    
    # Remover espacios dobles y caracteres especiales
    import re
    nombre_limpio = re.sub(r'\s+', ' ', nombre_limpio)  # Espacios múltiples a uno solo
    nombre_limpio = re.sub(r'[^\w\s]', '', nombre_limpio)  # Remover caracteres especiales
    nombre_limpio = nombre_limpio.strip()
    
    # Si después de la limpieza encontramos una coincidencia, usarla
    for nombre_unificado, variaciones in normalizaciones.items():
        for variacion in variaciones:
            if variacion.replace(" ", "").replace("-", "") in nombre_limpio.replace(" ", ""):
                return nombre_unificado.title()
    
    # Si no hay coincidencia, devolver el nombre original con formato título
    return establecimiento.strip().title()

st.title(f"{EMOJI_GLOBAL} Dashboard Global Yupii - Análisis Consolidado de Repartidores {EMOJI_MOTO}")
st.markdown(f"""
{EMOJI_ENTREGA} Este dashboard muestra estadísticas agregadas de repartidores. 
Carga el dataset global desde S3 y selecciona un rango de fechas para obtener métricas específicas del período. {EMOJI_PAQUETE}
""")

# Sidebar para selección de dataset
st.sidebar.header(f"{EMOJI_PAQUETE} Configuración del Análisis")

# Selector de dataset
df_global = pd.DataFrame()
dataset_seleccionado = "No seleccionado"

st.sidebar.subheader(f"{EMOJI_CALENDARIO} Selección de Dataset")

if s3_connected:
    opcion_dataset = st.sidebar.radio(
        "Elige el dataset a analizar:",
        ["Dataset global desde S3", "Cargar archivo personalizado"],
        help="Selecciona la fuente de datos para el análisis"
    )
    
    if opcion_dataset == "Dataset global desde S3":
        # Cargar dataset desde S3
        df_global = s3_manager.load_dataset("dataset_global.csv")
        
        if df_global is not None and not df_global.empty:
            # Mejorar el parseo de fechas para manejar múltiples formatos
            df_global["fecha"] = pd.to_datetime(df_global["fecha"], 
                                              infer_datetime_format=True, 
                                              errors='coerce')
            
            dataset_seleccionado = "dataset_global.csv (desde S3)"
            st.sidebar.success(f"✅ Dataset cargado desde S3: {len(df_global)} registros")
        else:
            st.sidebar.warning("📁 No se pudo cargar el dataset desde S3")
            df_global = pd.DataFrame()
    
    elif opcion_dataset == "Cargar archivo personalizado":
        archivo_personalizado = st.sidebar.file_uploader(
            "Sube tu archivo CSV personalizado",
            type=["csv"],
            help="Archivo debe contener columnas: fecha, establecimiento, producto, costo_envio, repartidor"
        )
        
        if archivo_personalizado:
            try:
                df_global = pd.read_csv(archivo_personalizado)
                df_global["fecha"] = pd.to_datetime(df_global["fecha"], 
                                                  infer_datetime_format=True, 
                                                  errors='coerce')
                dataset_seleccionado = archivo_personalizado.name
                st.sidebar.success(f"✅ Archivo cargado: {len(df_global)} registros")
            except Exception as e:
                st.sidebar.error(f"❌ Error al cargar archivo: {str(e)}")
                df_global = pd.DataFrame()
else:
    # Fallback: carga local si S3 no está disponible
    st.sidebar.warning("🔴 Sin conexión S3 - Usando carga local")
    
    archivo_personalizado = st.sidebar.file_uploader(
        "Sube tu archivo CSV (fallback local)",
        type=["csv"],
        help="Archivo debe contener columnas: fecha, establecimiento, producto, costo_envio, repartidor"
    )
    
    if archivo_personalizado:
        try:
            df_global = pd.read_csv(archivo_personalizado)
            df_global["fecha"] = pd.to_datetime(df_global["fecha"], 
                                              infer_datetime_format=True, 
                                              errors='coerce')
            dataset_seleccionado = archivo_personalizado.name
            st.sidebar.success(f"✅ Archivo cargado: {len(df_global)} registros")
        except Exception as e:
            st.sidebar.error(f"❌ Error al cargar archivo: {str(e)}")
            df_global = pd.DataFrame()

# Mostrar información del dataset cargado
if not df_global.empty:
    st.sidebar.info(f"📊 Dataset: {dataset_seleccionado}")
    st.sidebar.info(f"📝 Registros: {len(df_global):,}")
    
    # Estadísticas básicas del dataset
    fechas_validas = df_global["fecha"].dropna()
    if not fechas_validas.empty:
        st.sidebar.info(f"📅 Rango: {fechas_validas.min().strftime('%d/%m/%Y')} - {fechas_validas.max().strftime('%d/%m/%Y')}")
        
        # Mostrar repartidores únicos
        if "repartidor" in df_global.columns:
            repartidores_unicos = df_global["repartidor"].nunique()
            st.sidebar.info(f"👥 Repartidores: {repartidores_unicos}")
    
    # Aplicar limpieza y normalización de establecimientos
    df_global["establecimiento_limpio"] = df_global["establecimiento"].apply(limpiar_establecimientos)
    df_global["establecimiento_normalizado"] = df_global["establecimiento_limpio"].apply(normalizar_establecimiento)
    
    # Remover filas con establecimientos no válidos
    df_global = df_global.dropna(subset=["establecimiento_normalizado"])
    
    if len(df_global) > 0:
        st.sidebar.success(f"🧹 Limpieza aplicada: {len(df_global)} registros válidos")
    else:
        st.sidebar.warning("⚠️ No quedaron registros válidos después de la limpieza")

# Selección de rango de fechas
if not df_global.empty and "fecha" in df_global.columns:
    fechas_validas = df_global["fecha"].dropna().sort_values().unique()
    
    if len(fechas_validas) >= 1:
        min_date = fechas_validas[0].date()
        max_date = fechas_validas[-1].date()
        hoy = datetime.now().date()
        
        # Configurar fechas por defecto (últimos 30 días o rango completo si es menor)
        if (max_date - min_date).days <= 30:
            default_inicio = min_date
            default_fin = max_date
        else:
            default_inicio = max(min_date, max_date - pd.Timedelta(days=30))
            default_fin = max_date
        
        st.sidebar.subheader(f"{EMOJI_CALENDARIO} Filtros de Análisis")
        
        fecha_inicio = st.sidebar.date_input(
            "Fecha de inicio",
            value=default_inicio,
            min_value=min_date,
            max_value=max_date,
            format="DD/MM/YYYY"
        )
        fecha_fin = st.sidebar.date_input(
            "Fecha de fin", 
            value=default_fin,
            min_value=min_date,
            max_value=max_date,
            format="DD/MM/YYYY"
        )
        
        # Filtro por repartidor
        if "repartidor" in df_global.columns:
            repartidores_disponibles = sorted(df_global["repartidor"].dropna().unique())
            repartidores_seleccionados = st.sidebar.multiselect(
                f"{EMOJI_REPARTIDOR} Repartidores",
                options=repartidores_disponibles,
                default=repartidores_disponibles,
                help="Selecciona uno o más repartidores para analizar"
            )
        else:
            repartidores_seleccionados = []
        
        # Botón para ejecutar análisis
        analizar_global = st.sidebar.button(
            "🚀 Ejecutar Análisis Global",
            type="primary",
            help="Procesar datos con los filtros seleccionados"
        )
        
    else:
        analizar_global = False
        st.warning("❌ No hay fechas válidas en el dataset")
else:
    analizar_global = False

# Ejecutar análisis si se presiona el botón
if analizar_global and not df_global.empty:
    # Validar fechas
    if fecha_fin < fecha_inicio:
        st.error("❌ La fecha de fin no puede ser menor a la fecha de inicio.")
    else:
        # Filtrar datos por rango de fechas
        fecha_inicio_dt = datetime.combine(fecha_inicio, datetime.min.time())
        fecha_fin_dt = datetime.combine(fecha_fin, datetime.max.time())
        
        df_filtrado = df_global[
            (df_global["fecha"] >= fecha_inicio_dt) & 
            (df_global["fecha"] <= fecha_fin_dt)
        ]
        
        # Filtrar por repartidores seleccionados
        if repartidores_seleccionados and "repartidor" in df_global.columns:
            df_filtrado = df_filtrado[df_filtrado["repartidor"].isin(repartidores_seleccionados)]
        
        if df_filtrado.empty:
            st.warning("⚠️ No hay datos en el rango de fechas y filtros seleccionados.")
        else:
            # === ANÁLISIS GLOBAL ===
            st.header(f"{EMOJI_GLOBAL} Análisis Global del Período")
            st.markdown(f"**Período:** {fecha_inicio.strftime('%d/%m/%Y')} - {fecha_fin.strftime('%d/%m/%Y')}")
            
            # KPIs Globales
            total_envios = len(df_filtrado)
            total_ingresos = df_filtrado["costo_envio"].sum()
            promedio_por_envio = df_filtrado["costo_envio"].mean()
            dias_activos = df_filtrado["fecha"].dt.date.nunique()
            
            # Mostrar KPIs principales
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    label="🚛 Total Envíos",
                    value=f"{total_envios:,}",
                    help="Número total de envíos en el período"
                )
            
            with col2:
                st.metric(
                    label="💰 Ingresos Totales",
                    value=f"${total_ingresos:,.2f}",
                    help="Suma de todos los costos de envío"
                )
            
            with col3:
                st.metric(
                    label="📊 Promedio por Envío",
                    value=f"${promedio_por_envio:.2f}",
                    help="Costo promedio por envío"
                )
            
            with col4:
                st.metric(
                    label="📅 Días Activos",
                    value=f"{dias_activos}",
                    help="Número de días con actividad"
                )

            # === ANÁLISIS POR REPARTIDOR ===
            if "repartidor" in df_filtrado.columns:
                st.header(f"{EMOJI_REPARTIDOR} Rendimiento por Repartidor")
                
                # Agrupar por repartidor
                stats_repartidor = df_filtrado.groupby("repartidor").agg({
                    "costo_envio": ["count", "sum", "mean"],
                    "fecha": lambda x: x.dt.date.nunique()
                }).round(2)
                
                # Aplanar nombres de columnas
                stats_repartidor.columns = ["Envíos", "Ingresos_Total", "Promedio_Envío", "Días_Activos"]
                stats_repartidor = stats_repartidor.reset_index()
                
                # Calcular métricas adicionales
                stats_repartidor["Pago_Repartidor_70%"] = (stats_repartidor["Ingresos_Total"] * 0.7).round(2)
                stats_repartidor["Promedio_Diario"] = (stats_repartidor["Ingresos_Total"] / stats_repartidor["Días_Activos"]).round(2)
                
                # Ordenar por ingresos totales
                stats_repartidor = stats_repartidor.sort_values("Ingresos_Total", ascending=False)
                
                # Mostrar tabla de rendimiento
                st.subheader("📊 Tabla de Rendimiento")
                
                # Formatear para mostrar
                stats_display = stats_repartidor.copy()
                stats_display["Ingresos_Total"] = stats_display["Ingresos_Total"].apply(lambda x: f"${x:,.2f}")
                stats_display["Promedio_Envío"] = stats_display["Promedio_Envío"].apply(lambda x: f"${x:.2f}")
                stats_display["Pago_Repartidor_70%"] = stats_display["Pago_Repartidor_70%"].apply(lambda x: f"${x:,.2f}")
                stats_display["Promedio_Diario"] = stats_display["Promedio_Diario"].apply(lambda x: f"${x:.2f}")
                
                # Renombrar columnas para display
                stats_display.columns = [
                    "Repartidor", "Envíos", "Ingresos Totales", 
                    "Promedio por Envío", "Días Activos", 
                    "Pago al Repartidor (70%)", "Promedio Diario"
                ]
                
                st.dataframe(stats_display, use_container_width=True)
                
                # Gráficas de rendimiento
                col_graf1, col_graf2 = st.columns(2)
                
                with col_graf1:
                    st.subheader("📈 Envíos por Repartidor")
                    fig1, ax1 = plt.subplots(figsize=(10, 6))
                    
                    bars = ax1.bar(stats_repartidor["repartidor"], stats_repartidor["Envíos"], 
                                  color=YUPII_BLUE, alpha=0.8)
                    
                    ax1.set_xlabel("Repartidor", fontsize=12, color=YUPII_BLACK)
                    ax1.set_ylabel("Número de Envíos", fontsize=12, color=YUPII_BLACK)
                    ax1.set_title("Envíos por Repartidor", fontsize=14, color=YUPII_BLACK, fontweight='bold')
                    ax1.tick_params(axis='x', rotation=45)
                    
                    # Agregar valores en las barras
                    for bar in bars:
                        height = bar.get_height()
                        ax1.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                                f'{int(height)}',
                                ha='center', va='bottom', fontsize=10, color=YUPII_BLACK)
                    
                    plt.tight_layout()
                    st.pyplot(fig1)
                    plt.close(fig1)
                
                with col_graf2:
                    st.subheader("💰 Ingresos por Repartidor")
                    fig2, ax2 = plt.subplots(figsize=(10, 6))
                    
                    bars = ax2.bar(stats_repartidor["repartidor"], stats_repartidor["Ingresos_Total"], 
                                  color=YUPII_CYAN, alpha=0.8)
                    
                    ax2.set_xlabel("Repartidor", fontsize=12, color=YUPII_BLACK)
                    ax2.set_ylabel("Ingresos Totales ($)", fontsize=12, color=YUPII_BLACK)
                    ax2.set_title("Ingresos por Repartidor", fontsize=14, color=YUPII_BLACK, fontweight='bold')
                    ax2.tick_params(axis='x', rotation=45)
                    
                    # Agregar valores en las barras
                    for bar in bars:
                        height = bar.get_height()
                        ax2.text(bar.get_x() + bar.get_width()/2., height + max(stats_repartidor["Ingresos_Total"])*0.01,
                                f'${int(height)}',
                                ha='center', va='bottom', fontsize=10, color=YUPII_BLACK)
                    
                    plt.tight_layout()
                    st.pyplot(fig2)
                    plt.close(fig2)

            # === ANÁLISIS TEMPORAL ===
            st.header(f"{EMOJI_CALENDARIO} Análisis Temporal")
            
            # Tendencia diaria
            df_filtrado["fecha_solo"] = df_filtrado["fecha"].dt.date
            tendencia_diaria = df_filtrado.groupby("fecha_solo").agg({
                "costo_envio": ["count", "sum"]
            })
            tendencia_diaria.columns = ["Envíos", "Ingresos"]
            tendencia_diaria = tendencia_diaria.reset_index()
            
            # Gráfica de tendencia temporal
            fig3, (ax3, ax4) = plt.subplots(2, 1, figsize=(14, 10))
            
            # Envíos por día
            ax3.plot(tendencia_diaria["fecha_solo"], tendencia_diaria["Envíos"], 
                    marker='o', linewidth=2, color=YUPII_BLUE, markersize=4)
            ax3.set_ylabel("Número de Envíos", fontsize=12, color=YUPII_BLUE)
            ax3.set_title("Tendencia Diaria de Envíos", fontsize=14, color=YUPII_BLACK, fontweight='bold')
            ax3.grid(True, alpha=0.3)
            ax3.tick_params(axis='x', rotation=45)
            
            # Ingresos por día
            ax4.plot(tendencia_diaria["fecha_solo"], tendencia_diaria["Ingresos"], 
                    marker='s', linewidth=2, color=YUPII_CYAN, markersize=4)
            ax4.set_xlabel("Fecha", fontsize=12, color=YUPII_BLACK)
            ax4.set_ylabel("Ingresos ($)", fontsize=12, color=YUPII_CYAN)
            ax4.set_title("Tendencia Diaria de Ingresos", fontsize=14, color=YUPII_BLACK, fontweight='bold')
            ax4.grid(True, alpha=0.3)
            ax4.tick_params(axis='x', rotation=45)
            
            plt.tight_layout()
            st.pyplot(fig3)
            plt.close(fig3)

            # === ANÁLISIS POR ESTABLECIMIENTO ===
            if "establecimiento_normalizado" in df_filtrado.columns:
                st.header(f"🏪 Top Establecimientos")
                
                # Top 10 establecimientos
                top_establecimientos = df_filtrado.groupby("establecimiento_normalizado").agg({
                    "costo_envio": ["count", "sum"]
                }).round(2)
                top_establecimientos.columns = ["Envíos", "Ingresos_Total"]
                top_establecimientos = top_establecimientos.reset_index()
                top_establecimientos = top_establecimientos.sort_values("Envíos", ascending=False).head(10)
                
                # Mostrar top 10
                col_top1, col_top2 = st.columns(2)
                
                with col_top1:
                    st.subheader("📊 Top 10 por Número de Envíos")
                    top_display = top_establecimientos.copy()
                    top_display["Ingresos_Total"] = top_display["Ingresos_Total"].apply(lambda x: f"${x:,.2f}")
                    top_display.columns = ["Establecimiento", "Envíos", "Ingresos Totales"]
                    st.dataframe(top_display, use_container_width=True)
                
                with col_top2:
                    st.subheader("📈 Gráfica Top Establecimientos")
                    fig4, ax5 = plt.subplots(figsize=(10, 8))
                    
                    # Crear gráfica horizontal para mejor legibilidad
                    y_pos = range(len(top_establecimientos))
                    bars = ax5.barh(y_pos, top_establecimientos["Envíos"], color=YUPII_BLUE, alpha=0.8)
                    
                    ax5.set_yticks(y_pos)
                    ax5.set_yticklabels(top_establecimientos["establecimiento_normalizado"], fontsize=10)
                    ax5.set_xlabel("Número de Envíos", fontsize=12, color=YUPII_BLACK)
                    ax5.set_title("Top 10 Establecimientos por Envíos", fontsize=14, color=YUPII_BLACK, fontweight='bold')
                    
                    # Agregar valores en las barras
                    for i, bar in enumerate(bars):
                        width = bar.get_width()
                        ax5.text(width + 0.5, bar.get_y() + bar.get_height()/2,
                                f'{int(width)}',
                                ha='left', va='center', fontsize=9, color=YUPII_BLACK)
                    
                    plt.tight_layout()
                    st.pyplot(fig4)
                    plt.close(fig4)

            # === EXPORTAR RESULTADOS ===
            st.header(f"📁 Exportar Resultados")
            
            # Botón para exportar análisis completo
            if "repartidor" in df_filtrado.columns:
                # Preparar datos para exportar
                csv_export = stats_repartidor.copy()
                csv_export.columns = [
                    "repartidor", "envios", "ingresos_total", 
                    "promedio_envio", "dias_activos", 
                    "pago_repartidor_70", "promedio_diario"
                ]
                
                csv_data = csv_export.to_csv(index=False).encode("utf-8")
                
                st.download_button(
                    label="📊 Descargar análisis por repartidor (CSV)",
                    data=csv_data,
                    file_name=f"analisis_repartidores_{fecha_inicio.strftime('%Y%m%d')}_{fecha_fin.strftime('%Y%m%d')}.csv",
                    mime="text/csv",
                    help="Descarga el análisis completo en formato CSV"
                )
            
            # Exportar datos filtrados
            csv_filtered = df_filtrado.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📋 Descargar datos filtrados (CSV)",
                data=csv_filtered,
                file_name=f"datos_filtrados_{fecha_inicio.strftime('%Y%m%d')}_{fecha_fin.strftime('%Y%m%d')}.csv",
                mime="text/csv",
                help="Descarga los datos filtrados en formato CSV"
            )

elif not analizar_global:
    # Pantalla inicial sin análisis
    st.info(f"""
    {EMOJI_ENTREGA} **Instrucciones de uso:**
    
    1. **Conexión S3**: Asegúrate de que las credenciales AWS estén configuradas
    2. **Dataset**: El dataset global se carga automáticamente desde S3
    3. **Filtros**: Selecciona el rango de fechas y repartidores en la barra lateral
    4. **Análisis**: Presiona el botón "🚀 Ejecutar Análisis Global" para ver resultados
    
    📊 **Métricas disponibles:**
    - KPIs globales del período
    - Rendimiento por repartidor 
    - Análisis temporal (tendencias diarias)
    - Top establecimientos más frecuentes
    - Exportación de resultados en CSV
    """)

# Footer
st.markdown("""
---
### Manual de uso - Dashboard Global con S3

#### Variables de entorno requeridas
```bash
AWS_ACCESS_KEY_ID=tu_access_key
AWS_SECRET_ACCESS_KEY=tu_secret_key
AWS_DEFAULT_REGION=us-east-1
S3_BUCKET_NAME=yupii-data-bucket
```

#### Ejecución con Docker
```bash
# Construir imagen
docker build -t yupii-global-dashboard .

# Ejecutar contenedor
docker run -p 8502:8501 \
  -e AWS_ACCESS_KEY_ID=tu_access_key \
  -e AWS_SECRET_ACCESS_KEY=tu_secret_key \
  -e AWS_DEFAULT_REGION=us-east-1 \
  -e S3_BUCKET_NAME=yupii-data-bucket \
  yupii-global-dashboard
```

**Colores corporativos Yupii:** {YUPII_BLUE}, {YUPII_CYAN}, {YUPII_BLACK}
""")
