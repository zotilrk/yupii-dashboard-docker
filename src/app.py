import streamlit as st
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from datetime import datetime
import io
import base64
import os
import re
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
    page_title="Dashboard Yupii",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(f"""
    <style>
    .main {{
        background: {YUPII_GRADIENT};
        color: white;
    }}
    .stApp {{
        background: {YUPII_GRADIENT};
    }}
    .css-1d391kg {{
        background: {YUPII_GRADIENT};
    }}
    .css-18e3th9 {{
        background: {YUPII_GRADIENT};
    }}
    .css-1v0mbdj {{
        background: {YUPII_GRADIENT};
    }}
    .stButton>button {{
        background-color: {YUPII_CYAN};
        color: {YUPII_BLACK};
        font-weight: bold;
        border-radius: 8px;
        border: none;
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
        ✅ Conectado a AWS S3 - Archivos disponibles desde la nube
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <div class="s3-status s3-disconnected">
        ❌ Sin conexión a AWS S3 - Verificar credenciales y configuración
    </div>
    """, unsafe_allow_html=True)

# Sidebar para seleccionar archivo desde S3 y nombre del repartidor
st.sidebar.header("Carga de datos desde S3")
repartidor = st.sidebar.text_input("Nombre del repartidor", value="Nombre", key="nombre_repartidor")

# Selector de archivos desde S3
archivo_seleccionado = None
nombre_repartidor_archivo = "Nombre no detectado"

if s3_connected:
    files_list = s3_manager.list_files("pedidos/")
    
    if files_list:
        st.sidebar.subheader("📁 Archivos disponibles en S3")
        
        # Crear lista de opciones para el selectbox
        file_options = ["Seleccionar archivo..."] + [f[0] for f in files_list]
        selected_file = st.sidebar.selectbox(
            "Selecciona un archivo de pedidos:",
            options=file_options,
            key="file_selector"
        )
        
        if selected_file != "Seleccionar archivo...":
            # Encontrar la key completa del archivo seleccionado
            selected_key = next((f[1] for f in files_list if f[0] == selected_file), None)
            if selected_key:
                # Descargar contenido del archivo
                file_content = s3_manager.download_file(selected_key)
                if file_content:
                    archivo_seleccionado = file_content
                    nombre_repartidor_archivo = selected_file.replace(".txt", "")
                    st.sidebar.success(f"✅ Archivo cargado: {selected_file}")
        
        # Mostrar información adicional
        st.sidebar.info(f"📊 {len(files_list)} archivos disponibles")
    else:
        st.sidebar.warning("📁 No se encontraron archivos en S3")
        st.sidebar.info("Sube archivos .txt a la carpeta 'pedidos/' en tu bucket S3")
else:
    st.sidebar.error("🔴 Sin conexión a S3")
    st.sidebar.info("Configura las variables de entorno AWS para conectar")

# Fallback: permitir carga local si S3 no está disponible
if not s3_connected:
    st.sidebar.subheader("📁 Carga local (fallback)")
    archivo_upload = st.sidebar.file_uploader("Carga tu archivo de pedidos (.txt)", type=["txt"])
    if archivo_upload:
        archivo_seleccionado = archivo_upload.read().decode("utf-8")
        nombre_repartidor_archivo = archivo_upload.name.replace(".txt", "")

# Emojis de reparto
EMOJI_MOTO = "🏍️"
EMOJI_PAQUETE = "📦"
EMOJI_COMIDA = "🍔"
EMOJI_ENTREGA = "🛵"
EMOJI_REPARTIDOR = "🧑🏾‍🦱‍🛵"

st.title(f"{EMOJI_ENTREGA} Dashboard Yupii para Repartidores {EMOJI_MOTO}")
st.markdown(f"## {EMOJI_REPARTIDOR} {nombre_repartidor_archivo}")
st.markdown(f"""
{EMOJI_COMIDA} Este dashboard te permite analizar tus pedidos, ingresos y pagos semanales. Exporta tu reporte y tu data limpia fácilmente. {EMOJI_PAQUETE}
""")

# Función para detectar si un producto es válido
def es_producto_valido(producto):
    """
    Determina si un texto representa un producto real o es una instrucción de envío.
    
    Returns:
        bool: True si es un producto válido, False si es instrucción/basura
    """
    if not producto or isinstance(producto, float):
        return False
    
    producto = str(producto).strip()
    
    # 1. Filtros de exclusión directa (instrucciones de envío)
    instrucciones_envio = [
        "tiene un envio", "tienen un envio", "tiene un envío", "tienen un envío",
        "a nombre de yupii", "a nombre de", "donde sea", "sin producto",
        "no aplica", "efectivo", "transferencia", "pago", "deposito",
        "-", "", "nan", "null", "none"
    ]
    
    producto_lower = producto.lower()
    for instruccion in instrucciones_envio:
        if instruccion in producto_lower and len(producto) < 25:
            return False
    
    # 2. Si es muy corto (menos de 3 caracteres), probablemente no es un producto
    if len(producto) < 3:
        return False
    
    # 3. Detectar patrones de productos válidos
    # Palabras clave que indican productos reales
    productos_keywords = [
        # Comida
        "pizza", "hamburguesa", "burger", "pollo", "carne", "pescado",
        "pasta", "espagueti", "lasaña", "ensalada", "sopa", "sandwich",
        "taco", "burrito", "quesadilla", "empanada", "arepa", "hot dog",
        "papas", "patatas", "french fries", "combo", "menu", "menú",
        "desayuno", "almuerzo", "cena", "bebida", "refresco", "jugo",
        "cerveza", "agua", "café", "té", "smoothie", "milkshake",
        "helado", "postre", "torta", "pastel", "galleta", "donut",
        "pan", "bread", "arroz", "frijoles", "beans", "verdura",
        
        # Servicios/Pagos
        "recarga", "pago de", "servicio", "factura", "bill", "cuenta",
        "deposito", "retiro", "giro", "remesa", "envio de dinero",
        
        # Retail/Productos
        "producto", "articulo", "item", "medicamento", "medicina",
        "shampoo", "jabon", "crema", "perfume", "maquillaje",
        "ropa", "zapatos", "accesorio", "libro", "revista",
        "electronico", "telefono", "cargador", "cable",
        
        # Marcas conocidas
        "coca cola", "pepsi", "sprite", "fanta", "mcdonalds", "kfc",
        "burger king", "subway", "dominos", "pizza hut", "starbucks"
    ]
    
    # 4. Verificar si contiene palabras clave de productos
    for keyword in productos_keywords:
        if keyword in producto_lower:
            return True
    
    # 5. Detectar patrones típicos de productos
    # Productos con números/códigos (ej: "Combo #1", "Menu 2", "Item 123")
    if any(char.isdigit() for char in producto) and any(word in producto_lower for word in ["combo", "menu", "menú", "#", "no.", "item"]):
        return True
    
    # 6. Si tiene ingredientes/descripción culinaria (contiene "con", "de", "y")
    conectores_culinarios = ["con", "de", "y", "sin", "extra", "adicional"]
    if any(conector in producto_lower for conector in conectores_culinarios) and len(producto) > 10:
        return True
    
    # 7. Si parece una descripción de comida (más de 8 caracteres y no es instrucción)
    if len(producto) > 8 and not any(word in producto_lower for word in ["envio", "entregar", "recoger", "cliente", "direccion"]):
        # Verificar que no sea solo mayúsculas (que suelen ser instrucciones)
        if not producto.isupper() or len(producto) > 15:
            return True
    
    # 8. Por defecto, si llegó hasta aquí y es texto largo, probablemente es producto
    if len(producto) > 15:
        return True
    
    return False

# Función para normalizar nombres de establecimientos
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

# Procesamiento de datos
if archivo_seleccionado:
    text = archivo_seleccionado
else:
    text = "_chat_2.txt no cargado.\n_*Recoger en*_\n📍Establecimiento\n_*Pedido*_\nProducto\n_*Cobrar*_\n$0\n[01/01/25, 00:00:00]"

# Separar pedidos
pedidos_raw = text.split("_*Recoger en*_")

# Extraer datos con filtrado de productos válidos y normalización de establecimientos
data = []
productos_filtrados = []  # Para mostrar estadísticas
establecimientos_normalizados = {}  # Para mostrar estadísticas de normalización

for pedido in pedidos_raw[1:]:
    est_match = re.search(r"📍(.*?)(?:\n|$)", pedido)
    establecimiento_raw = est_match.group(1).strip() if est_match else "-"
    
    # Normalizar establecimiento
    establecimiento_normalizado = normalizar_establecimiento(establecimiento_raw)
    
    # Rastrear normalizaciones para estadísticas
    if establecimiento_raw.lower() != establecimiento_normalizado.lower():
        if establecimiento_normalizado not in establecimientos_normalizados:
            establecimientos_normalizados[establecimiento_normalizado] = []
        establecimientos_normalizados[establecimiento_normalizado].append(establecimiento_raw)
    
    prod_match = re.search(r"_\*Pedido\*_\n(.+?)_\*Entregar en\*_", pedido, re.S)
    producto_raw = prod_match.group(1).strip().replace("▪️","").replace("◼️","") if prod_match else "-"
    
    # Filtrar producto - solo agregar si es válido
    if es_producto_valido(producto_raw):
        producto = producto_raw
    else:
        producto = "Producto no especificado"  # Placeholder para productos filtrados
        productos_filtrados.append(producto_raw)
    
    costo_match = re.search(r"_\*Cobrar\*_\s*\n*\s*\$(\d+)", pedido)
    costo = int(costo_match.group(1)) if costo_match else 0
    fecha_match = re.search(r"\[(\d{2}/\d{2}/\d{2}),", pedido)
    fecha = fecha_match.group(1) if fecha_match else None
    data.append([fecha, establecimiento_normalizado, producto, costo])

# DataFrame
df = pd.DataFrame(data, columns=["fecha", "establecimiento", "producto", "costo_envio"])
df["fecha"] = pd.to_datetime(df["fecha"], format="%d/%m/%y", errors="coerce")

# Placeholder si no hay datos
if df["fecha"].isnull().all():
    st.warning("No se detectaron pedidos válidos. Selecciona un archivo desde S3 para ver resultados.")

# Selección de rango de fechas
fechas_validas = df["fecha"].dropna().sort_values().unique()

if len(fechas_validas) >= 1:
    min_date = fechas_validas[0].date()
    max_date = fechas_validas[-1].date()
    hoy = datetime.now().date()
    # Si solo hay una fecha válida, ambos selectores usan esa fecha
    if min_date == max_date:
        default_inicio = default_fin = min_date
    else:
        default_inicio = max(min_date, hoy - pd.Timedelta(days=7))
        default_fin = min(max_date, hoy)
else:
    # Si no hay fechas válidas, usar hoy como rango
    min_date = max_date = hoy
    default_inicio = default_fin = hoy

col_fecha1, col_fecha2 = st.columns(2)
fecha_inicio = col_fecha1.date_input(
    "Fecha de inicio",
    value=default_inicio,
    min_value=min_date,
    max_value=max_date,
    format="DD/MM/YYYY"
)
fecha_fin = col_fecha2.date_input(
    "Fecha de fin",
    value=default_fin,
    min_value=min_date,
    max_value=max_date,
    format="DD/MM/YYYY"
)

# Botón para ejecutar el análisis
analizar = st.button("Analizar")

# Buscar ingresos extra de mensajes de Yupii
def extra_ingresos(text, fecha_inicio_dt, fecha_fin_dt):
    # Regex: busca líneas con $ y cantidad, enviadas por Yupii y que incluyan 'más de envío'
    pattern = r"\[(\d{2}/\d{2}/\d{2}),.*?\] Yupii:.*?([$🔴🟢🟡🟣🟠🟤⚫️]*\$\d+).*más de envío"
    matches = re.findall(pattern, text)
    total = 0
    fechas = []
    for fecha_str, monto_text in matches:
        # Extraer monto numérico
        monto_match = re.search(r"\$(\d+)", monto_text)
        monto = int(monto_match.group(1)) if monto_match else 0
        fecha = pd.to_datetime(fecha_str, format="%d/%m/%y", errors="coerce")
        if pd.notnull(fecha) and fecha_inicio_dt <= fecha <= fecha_fin_dt:
            total += monto
            fechas.append(fecha)
    return total, fechas

if analizar:
    if fecha_fin < fecha_inicio:
        st.error("La fecha de fin no puede ser menor a la fecha de inicio.")
        df_filtrado = pd.DataFrame(columns=df.columns)
        ingresos_extra = 0
        ingresos_extra_weekend = 0
    else:
        fecha_inicio_dt = datetime.combine(fecha_inicio, datetime.min.time())
        fecha_fin_dt = datetime.combine(fecha_fin, datetime.max.time())
        df_filtrado = df[(df["fecha"] >= fecha_inicio_dt) & (df["fecha"] <= fecha_fin_dt)]
        ingresos_extra, fechas_ingresos_extra = extra_ingresos(text, fecha_inicio_dt, fecha_fin_dt)
        
        # Calcular ingresos extra específicos del fin de semana
        ingresos_extra_weekend = 0
        if fechas_ingresos_extra:
            for fecha_extra in fechas_ingresos_extra:
                # Si la fecha del ingreso extra es fin de semana (sábado=5, domingo=6)
                if fecha_extra.weekday() in [5, 6]:
                    # Buscar el monto específico de esa fecha
                    pattern = rf"\[{fecha_extra.strftime('%d/%m/%y')},.*?\] Yupii:.*?([$🔴🟢🟡🟣🟠🟤⚫️]*\$\d+).*más de envío"
                    matches = re.findall(pattern, text)
                    for monto_text in matches:
                        monto_match = re.search(r"\$(\d+)", monto_text)
                        if monto_match:
                            ingresos_extra_weekend += int(monto_match.group(1))
else:
    df_filtrado = pd.DataFrame(columns=df.columns)
    ingresos_extra = 0
    ingresos_extra_weekend = 0

# KPIs globales y de fin de semana
if not df_filtrado.empty:
    # KPIs globales
    envios_totales = len(df_filtrado)
    ingreso_total = df_filtrado["costo_envio"].sum() + ingresos_extra
    pago_total = ingreso_total * 0.7
    dias_con_pedidos = df_filtrado["fecha"].dt.date.nunique()
    reparaciones = 250 if dias_con_pedidos >= 6 else 0
    entregar_yupii = (ingreso_total * 0.3) - reparaciones

    st.subheader(f"{EMOJI_PAQUETE} KPIs Globales del Rango Seleccionado {EMOJI_MOTO}")
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Envíos totales", f"{envios_totales}")
    col2.metric("Ingreso total", f"${ingreso_total:,.2f}")
    col3.metric("Pago al repartidor (70%)", f"${pago_total:,.2f}")
    col4.metric("Reparaciones", f"${reparaciones:,.2f}")
    col5.metric("Total a entregar a Yupii", f"${entregar_yupii:,.2f}")

    # Exportar KPIs y datos principales a PNG tipo tarjeta/reporte
    import matplotlib.patches as patches
    from PIL import Image

    def exportar_kpis_png(nombre, fecha_inicio, fecha_fin, envios, ingreso, pago, reparaciones, entregar, ingresos_extra):
        fig, ax = plt.subplots(figsize=(8, 7), dpi=200)
        ax.axis('off')
        # Fondo con color corporativo
        rect = patches.Rectangle((0,0),1,1, transform=ax.transAxes, color=YUPII_CYAN, alpha=0.12)
        ax.add_patch(rect)
        # Título
        ax.text(0.5, 0.95, "Dashboard Yupii para Repartidores", fontsize=20, fontweight='bold', color=YUPII_BLUE, ha='center', va='top')
        # Nombre
        ax.text(0.5, 0.88, f"Repartidor: {nombre}", fontsize=16, fontweight='bold', color=YUPII_BLACK, ha='center', va='top')
        # Fechas
        ax.text(0.5, 0.82, f"Rango: {fecha_inicio.strftime('%d/%m/%Y')} - {fecha_fin.strftime('%d/%m/%Y')}", fontsize=13, color=YUPII_BLACK, ha='center', va='top')
        # KPIs
        kpi_labels = [
            "Envíos totales:",
            "Ingreso total:",
            "Pago al repartidor (70%):",
            "Reparaciones:",
            "Total a entregar a Yupii:",
        ]
        kpi_values = [
            f"{envios}",
            f"${ingreso:,.2f}",
            f"${pago:,.2f}",
            f"${reparaciones:,.2f}",
            f"${entregar:,.2f}",
        ]
        for i, (label, value) in enumerate(zip(kpi_labels, kpi_values)):
            ax.text(0.05, 0.7 - i*0.09, label, fontsize=14, color=YUPII_BLUE, ha='left', va='center')
            ax.text(0.95, 0.7 - i*0.09, value, fontsize=14, color=YUPII_BLACK, ha='right', va='center')
        # Ingresos extra
        if ingresos_extra > 0:
            ax.text(0.5, 0.25, f"Ingresos extra por mensajes de Yupii: ${ingresos_extra:,.2f}", fontsize=13, color="#008000", ha='center', va='center')
        # Footer
        ax.text(0.5, 0.08, "Colores corporativos Yupii: #185E8D, #00AEEF, #000000", fontsize=10, color=YUPII_BLACK, ha='center', va='center')
        buf = io.BytesIO()
        fig.tight_layout()
        plt.savefig(buf, format="png", dpi=300, bbox_inches='tight')
        plt.close(fig)
        buf.seek(0)
        return buf.getvalue()

    # Botón para exportar KPIs a PNG
    kpi_png = exportar_kpis_png(
        nombre=nombre_repartidor_archivo,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        envios=envios_totales,
        ingreso=ingreso_total,
        pago=pago_total,
        reparaciones=reparaciones,
        entregar=entregar_yupii,
        ingresos_extra=ingresos_extra
    )
    st.download_button(
        label="Exportar KPIs y datos principales a PNG",
        data=kpi_png,
        file_name=f"reporte_{nombre_repartidor_archivo}.png",
        mime="image/png"
    )

    # KPIs de fin de semana
    weekend_mask = df_filtrado["fecha"].dt.dayofweek.isin([5, 6])
    df_weekend = df_filtrado[weekend_mask]
    if not df_weekend.empty:
        st.subheader(f"🍕 KPIs de Fin de Semana (Sábado y Domingo) {EMOJI_MOTO}")
        colw1, colw2, colw3 = st.columns(3)
        envios_weekend = len(df_weekend)
        ingreso_weekend_base = df_weekend["costo_envio"].sum()
        ingreso_weekend_total = ingreso_weekend_base + ingresos_extra_weekend
        
        colw1.metric("Envíos en fin de semana", f"{envios_weekend}")
        colw2.metric("Ingreso base fin de semana", f"${ingreso_weekend_base:,.2f}")
        colw3.metric("Ingreso total fin de semana", f"${ingreso_weekend_total:,.2f}")
        
        if ingresos_extra_weekend > 0:
            st.success(f"💰 Ingresos extra del fin de semana: ${ingresos_extra_weekend:,.2f}")

    # Visualización por días de la semana
    st.subheader(f"📊 Pedidos e Ingresos por Día de la Semana {EMOJI_ENTREGA}")
    
    # Agregar columna de día de la semana en español
    dias_semana = {
        0: 'Lunes',
        1: 'Martes', 
        2: 'Miércoles',
        3: 'Jueves',
        4: 'Viernes',
        5: 'Sábado',
        6: 'Domingo'
    }
    df_filtrado["dia_semana"] = df_filtrado["fecha"].dt.dayofweek.map(dias_semana)
    
    # Agrupar por día de la semana
    resumen_dias = df_filtrado.groupby("dia_semana").agg({
        "producto": "count",  # Número de pedidos
        "costo_envio": "sum"  # Ingreso total
    }).reset_index()
    
    # Reordenar según orden de días de la semana
    orden_dias = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
    resumen_dias["dia_semana"] = pd.Categorical(resumen_dias["dia_semana"], categories=orden_dias, ordered=True)
    resumen_dias = resumen_dias.sort_values("dia_semana")
    
    if not resumen_dias.empty:
        # Crear gráfica de barras doble
        fig, ax1 = plt.subplots(figsize=(12, 7), dpi=200)
        
        # Configurar estilo
        sns.set_style("whitegrid")
        
        # Eje primario (pedidos)
        x_pos = range(len(resumen_dias))
        bars1 = ax1.bar([x - 0.2 for x in x_pos], resumen_dias["producto"], 
                       width=0.4, label="Pedidos", color=YUPII_BLUE, alpha=0.8)
        
        # Eje secundario (ingresos)
        ax2 = ax1.twinx()
        bars2 = ax2.bar([x + 0.2 for x in x_pos], resumen_dias["costo_envio"], 
                       width=0.4, label="Ingresos ($)", color=YUPII_CYAN, alpha=0.8)
        
        # Configurar etiquetas y títulos
        ax1.set_xlabel("Día de la Semana", fontsize=14, color=YUPII_BLACK)
        ax1.set_ylabel("Número de Pedidos", fontsize=14, color=YUPII_BLUE)
        ax2.set_ylabel("Ingresos ($)", fontsize=14, color=YUPII_CYAN)
        ax1.set_title("Pedidos e Ingresos por Día de la Semana", fontsize=16, color=YUPII_BLACK, fontweight='bold')
        
        # Configurar ejes
        ax1.set_xticks(x_pos)
        ax1.set_xticklabels(resumen_dias["dia_semana"], rotation=45, ha='right')
        ax1.tick_params(axis='y', labelcolor=YUPII_BLUE)
        ax2.tick_params(axis='y', labelcolor=YUPII_CYAN)
        
        # Agregar valores en las barras
        for i, (bar1, bar2) in enumerate(zip(bars1, bars2)):
            # Valor de pedidos
            ax1.text(bar1.get_x() + bar1.get_width()/2, bar1.get_height() + 0.5,
                    f'{int(resumen_dias.iloc[i]["producto"])}',
                    ha='center', va='bottom', fontsize=10, color=YUPII_BLUE, fontweight='bold')
            # Valor de ingresos
            ax2.text(bar2.get_x() + bar2.get_width()/2, bar2.get_height() + max(resumen_dias["costo_envio"])*0.01,
                    f'${int(resumen_dias.iloc[i]["costo_envio"])}',
                    ha='center', va='bottom', fontsize=10, color=YUPII_CYAN, fontweight='bold')
        
        # Leyenda combinada
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
        
        # Ajustar layout
        plt.tight_layout()
        st.pyplot(fig)
        
        # Mostrar tabla resumen
        st.subheader("📋 Resumen por Día de la Semana")
        resumen_display = resumen_dias.copy()
        resumen_display.columns = ["Día", "Pedidos", "Ingresos ($)"]
        resumen_display["Ingresos ($)"] = resumen_display["Ingresos ($)"].apply(lambda x: f"${x:,.2f}")
        st.dataframe(resumen_display, use_container_width=True)
        
        # Exportar gráfica
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=300, bbox_inches='tight')
        st.download_button(
            label="Descargar gráfica como PNG",
            data=buf.getvalue(),
            file_name=f"grafica_dias_{nombre_repartidor_archivo}.png",
            mime="image/png"
        )
        plt.close(fig)
else:
    pass

# Exportar data limpia y agregar al dataset global (usando S3)
if not df_filtrado.empty:
    # Agregar columna de repartidor
    df_global_append = df_filtrado.copy()
    df_global_append["repartidor"] = nombre_repartidor_archivo

    # Cargar dataset global desde S3
    if s3_connected:
        df_global = s3_manager.load_dataset("dataset_global.csv")
        
        if df_global is not None and not df_global.empty:
            # Asegurar que las fechas del dataset existente estén en formato datetime
            df_global["fecha"] = pd.to_datetime(df_global["fecha"], 
                                              infer_datetime_format=True, 
                                              errors='coerce')
            df_global = pd.concat([df_global, df_global_append], ignore_index=True)
        else:
            df_global = df_global_append

        # Asegurar formato consistente de fechas antes de guardar
        df_global["fecha"] = pd.to_datetime(df_global["fecha"], 
                                          infer_datetime_format=True, 
                                          errors='coerce')
        
        # Guardar dataset global actualizado en S3
        s3_manager.save_dataset(df_global, "dataset_global.csv")
    
    # Exportar data limpia individual
    csv = df_filtrado.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Exportar data limpia a CSV",
        data=csv,
        file_name=f"{repartidor}_clean.csv",
        mime="text/csv"
    )


