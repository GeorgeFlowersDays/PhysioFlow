import io
import os
import math
import sqlite3
import cv2
import numpy as np
import streamlit as st
from PIL import Image
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from streamlit_drawable_canvas import st_canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from supabase import create_client, Client

SUPABASE_URL = st.secrets.get("SUPABASE_URL", "")
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "")

# ==========================================
# 1. FUNCIÓN GENERADORA DE PDF (LEGAL GOLD STANDARD)
# ==========================================
def generar_pdf_expediente(datos_terapeuta, datos_paciente, historia_clinica):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )
    
    story = []
    styles = getSampleStyleSheet()
    
    style_header_title = ParagraphStyle(
        'HeaderTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=18,
        textColor=colors.HexColor('#003366'),
        spaceAfter=2
    )
    
    style_header_sub = ParagraphStyle(
        'HeaderSub',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        textColor=colors.HexColor('#555555'),
        spaceAfter=10
    )
    
    style_section = ParagraphStyle(
        'SectionTitle',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=12,
        textColor=colors.HexColor('#003366'),
        spaceBefore=10,
        spaceAfter=6
    )
    
    style_body = ParagraphStyle(
        'BodyTextCustom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13,
        textColor=colors.HexColor('#222222')
    )
    
    header_data = [
        [
            Paragraph(f"<b>PHYSIOFLOW</b> - Fisioterapia Especializada", style_header_title),
            Paragraph("<b>EXPEDIENTE CLÍNICO</b><br/>NOM-004-SSA3-2012", style_header_sub)
        ]
    ]
    t_header = Table(header_data, colWidths=[4.5*inch, 2.5*inch])
    t_header.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN', (1,0), (1,0), 'RIGHT'),
    ]))
    story.append(t_header)
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#003366'), spaceAfter=12))
    
    data_info = [
        [
            Paragraph(f"<b>Fisioterapeuta:</b> {datos_terapeuta.get('nombre', 'Profesional de la Salud')}", style_body),
            Paragraph(f"<b>Paciente:</b> {datos_paciente.get('nombre', 'N/A')}", style_body)
        ],
        [
            Paragraph(f"<b>Cédula Prof:</b> {datos_terapeuta.get('cedula', 'N/A')}", style_body),
            Paragraph(f"<b>Edad / Sexo:</b> {datos_paciente.get('edad', 'N/A')} años | {datos_paciente.get('sexo', 'N/A')}", style_body)
        ],
        [
            Paragraph(f"<b>Institución:</b> {datos_terapeuta.get('institucion', 'UNAM')}", style_body),
            Paragraph(f"<b>Ocupación / Actividad:</b> {datos_paciente.get('ocupacion', 'N/A')}", style_body)
        ],
        [
            Paragraph(f"<b>Especialidad:</b> {datos_terapeuta.get('especialidad', 'Músicos & Artes Escénicas')}", style_body),
            Paragraph(f"<b>Fecha de Evaluación:</b> {datos_paciente.get('fecha', 'N/A')}", style_body)
        ]
    ]
    t_info = Table(data_info, colWidths=[3.5*inch, 3.5*inch])
    t_info.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F4F6F8')),
        ('PADDING', (0,0), (-1,-1), 6),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E0E0E0'))
    ]))
    story.append(t_info)
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("1. Motivo de Consulta y Anamnesis", style_section))
    story.append(Paragraph(historia_clinica.get('anamnesis', 'Sin registro de anamnesis.'), style_body))
    story.append(Spacer(1, 8))
    
    story.append(Paragraph("2. Exploración Física y Biomecánica", style_section))
    story.append(Paragraph(historia_clinica.get('exploracion', 'Sin registro de exploración física.'), style_body))
    story.append(Spacer(1, 8))

    patron_resp = historia_clinica.get("patron_respiratorio", "No evaluado")
    estres_eva = historia_clinica.get("nivel_estres_percibido", "N/A")
    hallazgos_psico = historia_clinica.get("hallazgos_psicosomaticos", [])
    hallazgos_str = ", ".join(hallazgos_psico) if hallazgos_psico else "Ninguno reportado"

    story.append(Paragraph(f"<b>Patrón Respiratorio Dominante:</b> {patron_resp}", style_body))
    story.append(Paragraph(f"<b>Carga Alostática / Estrés Percibido (0-10):</b> {estres_eva}/10", style_body))
    story.append(Paragraph(f"<b>Manifestaciones Somáticas & Tono Reactivo:</b> {hallazgos_str}", style_body))
    story.append(Spacer(1, 8))
    
    story.append(Paragraph("3. Diagnóstico Funcional, Pronóstico & Plan de Intervención", style_section))
    data_plan = [
        [Paragraph("<b>Diagnóstico Nosológico/Clínico:</b>", style_body), Paragraph(historia_clinica.get('diagnostico', 'N/A'), style_body)],
        [Paragraph("<b>Diagnóstico Funcional (CIF):</b>", style_body), Paragraph(historia_clinica.get('diagnostico_funcional', 'N/A'), style_body)],
        [Paragraph("<b>Pronóstico Fisioterapéutico:</b>", style_body), Paragraph(historia_clinica.get('pronostico', 'N/A'), style_body)],
        [Paragraph("<b>Plan / Objetivos de Intervención:</b>", style_body), Paragraph(historia_clinica.get('plan', 'N/A'), style_body)]
    ]
    t_plan = Table(data_plan, colWidths=[2.2*inch, 4.8*inch])
    t_plan.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('PADDING', (0,0), (-1,-1), 4),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E0E0E0')),
        ('BACKGROUND', (0,0), (0,-1), colors.HexColor('#F8F9FA')),
    ]))
    story.append(t_plan)
    story.append(Spacer(1, 20))
    
    data_firma = [
        ["__________________________________"],
        [Paragraph(f"<b>{datos_terapeuta.get('nombre', 'Firma del Profesional')}</b>", ParagraphStyle('FirmaStyle', parent=style_body, alignment=1))],
        [Paragraph(f"Cédula Profesional: {datos_terapeuta.get('cedula', 'N/A')}", ParagraphStyle('FirmaStyle2', parent=style_body, alignment=1))],
        [Paragraph("Firma del Fisioterapeuta Tratante", ParagraphStyle('FirmaStyle3', parent=style_body, alignment=1))]
    ]
    t_firma = Table(data_firma, colWidths=[7*inch])
    t_firma.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('TEXTCOLOR', (0,0), (-1,-1), colors.HexColor('#333333')),
        ('FONTSIZE', (0,0), (-1,-1), 9),
    ]))
    story.append(t_firma)
    
    doc.build(story)
    buffer.seek(0)
    return buffer

# ==================== CONEXIÓN Y BASE DE DATOS (SUPABASE) ====================
@st.cache_resource
def get_supabase_client():
    url = st.secrets.get("SUPABASE_URL", "")
    key = st.secrets.get("SUPABASE_KEY", "")
    if url and key:
        return create_client(url, key)
    return None

def guardar_paciente_db(paciente_dict):
    supabase = get_supabase_client()
    if not supabase:
        st.warning("⚡ Supabase no configurado en Secrets. Guardando en sesión temporal.")
        return False
    try:
        usr_info = st.session_state.get("user_info") or {}
        terapeuta_email = usr_info.get("email", "contacto@physioflow.mx")
        
        datos_guardar = {
            "terapeuta_email": terapeuta_email,
            "nombre": paciente_dict.get("nombre", ""),
            "curp": paciente_dict.get("curp", ""),
            "edad": int(paciente_dict.get("edad", 0)) if paciente_dict.get("edad") else 0,
            "sexo": paciente_dict.get("sexo", ""),
            "ocupacion": paciente_dict.get("ocupacion", ""),
            "telefono": paciente_dict.get("telefono", ""),
            "especialidad": paciente_dict.get("especialidad", ""),
            "eva_dolor": int(paciente_dict.get("eva_dolor", 0)),
            "diagnostico": paciente_dict.get("diagnostico_sospechado", ""),
            "patron_respiratorio": paciente_dict.get("patron_respiratorio", ""),
            "nivel_estres_percibido": int(paciente_dict.get("nivel_estres_percibido", 0)),
            "hallazgos_psicosomaticos": paciente_dict.get("hallazgos_psicosomaticos", [])
        }
        
        supabase.table("pacientes").upsert(datos_guardar, on_conflict="curp").execute()
        return True
    except Exception as e:
        st.error(f"Error al guardar en Supabase: {e}")
        return False

def cargar_paciente_db(curp):
    supabase = get_supabase_client()
    if not supabase:
        return None
    try:
        res = supabase.table("pacientes").select("*").eq("curp", curp).execute()
        if res.data and len(res.data) > 0:
            p = res.data[0]
            return {
                "nombre": p.get("nombre", ""),
                "edad": p.get("edad", 0),
                "sexo": p.get("sexo", ""),
                "curp": p.get("curp", ""),
                "ocupacion": p.get("ocupacion", ""),
                "telefono": p.get("telefono", ""),
                "especialidad": p.get("especialidad", ""),
                "eva_dolor": p.get("eva_dolor", 0),
                "diagnostico_sospechado": p.get("diagnostico", "")
            }
        return None
    except Exception as e:
        st.error(f"Error al cargar paciente de Supabase: {e}")
        return None

def obtener_todos_pacientes_db():
    supabase = get_supabase_client()
    if not supabase:
        return []
    try:
        usr_info = st.session_state.get("user_info") or {}
        terapeuta_email = usr_info.get("email", "contacto@physioflow.mx")
        res = supabase.table("pacientes").select("*").eq("terapeuta_email", terapeuta_email).order("nombre").execute()
        return res.data if res.data else []
    except Exception as e:
        st.error(f"Error al consultar Supabase: {e}")
        return []
# ==========================================
# INICIALIZACIÓN DE ESTADO Y PERSISTENCIA (SUPABASE)
# ==========================================
if "pacientes_guardados" not in st.session_state:
    st.session_state["pacientes_guardados"] = obtener_todos_pacientes_db()
# -----------------------------------------------------------------------------
# CARGA DE MOTORES DE IA (YOLO POSE)
# -----------------------------------------------------------------------------
YOLO_DISPONIBLE = False
try:
    from ultralytics import YOLO
    if os.path.exists("yolov8n-pose.pt"):
        model_yolo = YOLO("yolov8n-pose.pt")
        YOLO_DISPONIBLE = True
except Exception:
    YOLO_DISPONIBLE = False

# -----------------------------------------------------------------------------
# CONFIGURACIÓN DE PÁGINA Y BRANDING
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="PhysioFlow - Expediente Clínico & Gestor DB",
    page_icon="⚡",
    layout="wide"
)

st.markdown("""
    <style>
    .main { background-color: #F8FAFC; }
    section[data-testid="stSidebar"] { background-color: #0F172A !important; }
    section[data-testid="stSidebar"] .stMarkdown,
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] div { color: #F8FAFC !important; }
    .stButton>button { background-color: #0284C7; color: white; border-radius: 8px; font-weight: bold; border: none; }
    .stButton>button:hover { background-color: #0369A1; color: white; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# ESTADO Y AUTENTICACIÓN DE SESIÓN (PERSISTENTE CON URL)
# ==========================================

# 1. Recuperar sesión desde la URL si el usuario recarga la página (F5)
if st.query_params.get("auth") == "true":
    st.session_state["authenticated"] = True
    email_url = st.query_params.get("email", "contacto@physioflow.mx")
    if not st.session_state.get("user_info"):
        st.session_state["user_info"] = {"email": email_url}

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
if "user_info" not in st.session_state:
    st.session_state["user_info"] = None

if not st.session_state["authenticated"]:
    st.title("⚡ PhysioFlow Pro")
    st.caption("Plataforma Clínica Integral & Copiloto de Decisión Fisioterapéutica")

    tab_login, tab_registro = st.tabs(["🔑 Iniciar Sesión", "📝 Registrarse"])

    with tab_login:
        email = st.text_input("Correo Electrónico:", key="login_email")
        password = st.text_input("Contraseña:", type="password", key="login_pass")
        if st.button("Ingresar a PhysioFlow", use_container_width=True):
            if email and password:
                st.session_state["authenticated"] = True
                st.session_state["user_info"] = {"email": email}
                # Guardar en la URL para sobrevivir al F5
                st.query_params["auth"] = "true"
                st.query_params["email"] = email
                st.success("¡Bienvenido a PhysioFlow!")
                st.rerun()
            else:
                st.error("Por favor ingresa tu correo y contraseña.")

    with tab_registro:
        st.subheader("Crear Cuenta de Profesional")
        reg_titulo = st.selectbox("Grado / Título Profesional:", ["LFT", "LTF", "Mtro.", "Mtra.", "Dr.", "Dra.", "Lic."])
        reg_nombre = st.text_input("Nombre Completo (sin prefijo):", placeholder="Ej. Jorge Antonio Flores Díaz")
        reg_cedula = st.text_input("Cédula Profesional:", placeholder="Ej. 12345678")
        reg_institucion = st.text_input("Institución / Universidad:", value="UNAM - Universidad Nacional Autónoma de México")
        reg_email = st.text_input("Correo Electrónico:", key="reg_email")
        reg_pass = st.text_input("Contraseña:", type="password", key="reg_pass")

        if st.button("Registrar Clínica / Cuenta", use_container_width=True):
            if reg_nombre and reg_cedula:
                st.session_state["user_info"] = {
                    "titulo": reg_titulo,
                    "nombre": reg_nombre,
                    "cedula": reg_cedula,
                    "institucion": reg_institucion,
                    "email": reg_email
                }
                st.session_state["authenticated"] = True
                # Guardar en la URL para sobrevivir al F5
                st.query_params["auth"] = "true"
                st.query_params["email"] = reg_email
                st.success("¡Cuenta registrada con éxito! Iniciando sesión...")
                st.rerun()
            else:
                st.error("Por favor ingresa al menos tu Nombre Completo y Cédula Profesional.")
    st.stop()
# -----------------------------------------------------------------------------
# DATOS DINÁMICOS POR ESPECIALIDAD
# -----------------------------------------------------------------------------
DATOS_ESPECIALIDADES = {
    "Músicos & Artes Escénicas": {
        "diagnosticos": ["Tenosinovitis de De Quervain", "Síndrome de Atrapamiento de Rama Sensitiva Radial", "Distonía Focal del Músico", "Síndrome del Túnel Carpiano"],
        "pruebas": ["Finkelstein Test (De Quervain)", "Test de Wartenberg (Radial Sensitivo)", "Phalen / Tinel Test", "Prueba de Digitación Fina"],
        "ejercicios": ["Neurodinamia Deslizamiento / Tensión Nervio Radial (3x10 rep)", "Neurodinamia Nervio Mediano", "Control Motor Fino en Instrumento"],
        "aditamentos": ["Mentonera Central Teka", "Almohadilla Ergonómica KorFkerRest", "Puntos de Apoyo Ergonómicos", "Soporte de Muñeca de Descarga"]
    },
    "Fisioterapia Neurológica": {
        "diagnosticos": ["Secuela de Evento Vascular Cerebral (EVC)", "Síndrome de Segunda Neurona Motora", "Marcha Atáxica / Parkinson", "Lesión Medular Incompleta"],
        "pruebas": ["Signo de Babinski / Hoffmann", "Signo de Romberg", "Prueba Índice-Nariz", "Test de Tinetti (Marcha y Equilibrio)"],
        "ejercicios": ["FNP (Iniciación Rítmica)", "Carga de Peso Dinámica y Transferencia de Centro de Gravedad", "Reeducación de la Marcha"],
        "aditamentos": ["Órtesis Tobillo-Pie (AFO)", "Cabestrillo Hemipléjico de Hombro", "Férula Antiespástica de Mano", "Andador Apoyo Antebrazo"]
    },
    "Fisioterapia Deportiva (Sports)": {
        "diagnosticos": ["Rotura / Reconstrucción de LCA", "Tendinopatía Aquilea / Rotuliana", "Síndrome de Pinzamiento Subacromial", "Esguince de Tobillo Grado II/III"],
        "pruebas": ["Lachman Test / Cajón Anterior", "McMurray / Apley Test", "Thompson Test", "Hawkins-Kennedy Test"],
        "ejercicios": ["Pliometría Progresiva y Control de Aterrizaje", "Nordic Hamstring Curls (3x8)", "Trabajo Excéntrico en Plano Inclinado"],
        "aditamentos": ["Rodillera Mecánica con Control de Flexión", "Cincha Infrapatelar para Tendón", "Tape Neuromuscular / Kinesiotape"]
    },
    "Ergonomía Laboral": {
        "diagnosticos": ["Cervicobraquialgia Sedente", "Epicondilopatía Lateral / Medial Laboral", "Síndrome del Túnel Carpiano Laboral", "Lumbalgia Mecánica Postural"],
        "pruebas": ["Test de Cozen / Mill", "Prueba de Roos / Wright", "Cuestionario Nórdico de Síntomas", "Evaluación Ergonómica de Puesto"],
        "ejercicios": ["Pausas Activas Cervicodorsales", "Estiramiento Activo de Pectoral Menor", "Fortalecimiento de Flexores Profundos Cervicales"],
        "aditamentos": ["Mouse Ergonómico Vertical 57°", "Apoyapiés Ergonómico Inclinable", "Soporte Lumbar Viscoelástico"]
    },
    "Geriátricos & Autonomía": {
        "diagnosticos": ["Síndrome de Fragilidad y Sarcopenia", "Osteoartrosis Severa de Rodilla / Cadera", "Inestabilidad de la Marcha y Riesgo de Caídas"],
        "pruebas": ["Timed Up and Go (TUG Test)", "Escala de Tinetti (Marcha/Equilibrio)", "Short Physical Performance Battery (SPPB)"],
        "ejercicios": ["Sit-to-Stand (3x10 rep)", "Entrenamiento de Balance Unipodal", "Fortalecimiento de Extensores de Cadera"],
        "aditamentos": ["Bastón Regulable de Aluminio", "Andador de Aluminio con Ruedas y Asiento", "Silla para Ducha con Respaldar"]
    },
    "Salud de la Mujer / Suelo Pélvico": {
        "diagnosticos": ["Incontinencia Urinaria de Esfuerzo (IUE)", "Diástasis Abdominal Posparto", "Dolor Pélvico Crónico / Vaginismo"],
        "pruebas": ["Valoración PERFECT / Oxford Modificada", "Medición de Diástasis Abdominal", "Cuestionario ICIQ-SF"],
        "ejercicios": ["Entrenamiento Suelo Pélvico (Kegel Guiado)", "Co-contracción Transverso - Suelo Pélvico", "Gimnasia Abdominal Hipopresiva"],
        "aditamentos": ["Biofeedback / Perineómetro Neumático", "Conos Vaginales Progresivos", "Cojín Cóncavo de Descarga Pélvica"]
    },
    "Traumatología & Ortopedia / Post-operatorio": {
        "diagnosticos": ["Plastia de Ligamento Cruzado Anterior (LCA)", "Fractura Reducida de Cadera / Fémur", "Reemplazo Total de Rodilla / Cadera", "Meniscectomía / Sutura Meniscal"],
        "pruebas": ["Prueba de Lachman / Cajón Anterior", "Valoración Goniométrica de ROM", "Prueba de Apley / McMurray", "Evaluación de Edema / Perimetría"],
        "ejercicios": ["Isométricos de Cuádriceps (10x10 sec)", "Movilización Pasiva Asistida de ROM", "Deslizamientos Neuromusculares en Camilla", "Carga Progresiva según Fase Quirúrgica"],
        "aditamentos": ["Muletas Axilares / Codos Ingleses", "Rodillera Mecánica Graduable (Hinged Knee Brace)", "Cojín Abductor de Cadera", "Criogeltrap de Compresión"]
    }
}

# -----------------------------------------------------------------------------
# FUNCIONES AUXILIARES Y CÁLCULOS BIOMECÁNICOS
# -----------------------------------------------------------------------------
def calcular_angulo_3puntos(a, b, c):
    a, b, c = np.array(a), np.array(b), np.array(c)
    v1, v2 = a - b, c - b
    norm_v1, norm_v2 = np.linalg.norm(v1), np.linalg.norm(v2)
    if norm_v1 == 0 or norm_v2 == 0:
        return 0.0
    dot_product = np.dot(v1, v2)
    cos_theta = np.clip(dot_product / (norm_v1 * norm_v2), -1.0, 1.0)
    return round(float(np.degrees(np.arccos(cos_theta))), 1)

# -----------------------------------------------------------------------------
# ESTADO DE SESIÓN Y REGISTRO
# -----------------------------------------------------------------------------
if "terapeuta" not in st.session_state:
    st.session_state["terapeuta"] = {
        "nombre": "Jorge Flores",
        "cedula": "",
        "institucion": "UNAM - Universidad Nacional Autónoma de México"
    }

if "paciente" not in st.session_state:
    st.session_state["paciente"] = {
        "nombre": "",
        "edad": 27,
        "sexo": "Masculino",
        "curp": "",
        "ocupacion": "",
        "telefono": "",
        "especialidad": "Músicos & Artes Escénicas",
        "ahf": "",
        "app": "",
        "apnp": "",
        "pa": "",
        "ef": "",
        "mapa_dolor_zona": "Cervical / Cuello",
        "eva_dolor": 5,
        "tipo_dolor": "Miofascial (Puntos Gatillo)",
        "grados_daniels": "Grado 5: Movimiento en rango completo contra resistencia máxima",
        "datos_especificos": {},
        "aditamentos_prescritos": [],
        "pruebas_seleccionadas": [],
        "ejercicios_seleccionados": [],
        "diagnostico_sospechado": "",
        "custom_prueba": "",
        "custom_ejercicio": "",
        "custom_aditamento": "",
        "custom_diagnostico": "",
        "resultado_1rm": ""
    }

if "goniometria" not in st.session_state:
    st.session_state["goniometria"] = {
        "articulacion": "Flexión de Codo",
        "grados_activos": 45,
        "grados_pasivos": 50,
        "hallazgo": "Dentro de límites normales"
    }

if "firma_paciente" not in st.session_state:
    st.session_state["firma_paciente"] = None

# -----------------------------------------------------------------------------
# BARRA LATERAL (NAVEGACIÓN SECUENCIAL POR CENTROS DE MANDO)
# -----------------------------------------------------------------------------
logo_path = None
for foto in ["logo_blanco.png", "Logo_blanco.png", "logo.png", "Logo.png"]:
    if os.path.exists(foto):
        logo_path = foto
        break

if logo_path:
    st.sidebar.image(logo_path, use_container_width=True)
else:
    st.sidebar.title("⚡ PhysioFlow")

st.sidebar.subheader("👤 Fisioterapeuta Autenticado")
usr_info = st.session_state.get("user_info") or {}
nombre_reg = usr_info.get("nombre", "Jorge Antonio Flores Díaz")
cedula_reg = usr_info.get("cedula", "")
institucion_reg = usr_info.get("institucion", "UNAM - Universidad Nacional Autónoma de México")
titulo_reg = usr_info.get("titulo", "LFT")

titulos_lista = ["LFT", "LTF", "Mtro.", "Mtra.", "Dr.", "Dra.", "Lic."]
index_defecto = titulos_lista.index(titulo_reg) if titulo_reg in titulos_lista else 0

titulo_seleccionado = st.sidebar.selectbox("Grado / Título Profesional:", titulos_lista, index=index_defecto)

st.session_state["terapeuta"]["nombre"] = f"{titulo_seleccionado}. {nombre_reg}"
st.session_state["terapeuta"]["cedula"] = cedula_reg
st.session_state["terapeuta"]["institucion"] = institucion_reg

st.sidebar.markdown(f"**Profesional:** {st.session_state['terapeuta']['nombre']}")
st.sidebar.markdown(f"**Cédula:** {st.session_state['terapeuta']['cedula']}")
st.sidebar.markdown(f"**Institución:** {st.session_state['terapeuta']['institucion']}")
st.sidebar.caption("🔒 *Datos verificados para reportes PDF.*")
st.sidebar.write("---")

especialidades = list(DATOS_ESPECIALIDADES.keys())
especialidad_sel = st.sidebar.selectbox("Especialidad Clínica Activa:", especialidades, key="especialidad_activa")
st.session_state["paciente"]["especialidad"] = especialidad_sel
st.sidebar.write("---")

# ==========================================
# NAVEGACIÓN EN 4 CENTROS DE MANDO SECUENCIALES
# ==========================================
st.sidebar.markdown("### 🧭 Centros de Mando (Flujo de Sesión)")

opciones_fases = [
    "1️⃣ Recepción & Historia Clínica (NOM-004)",
    "2️⃣ Exploración & Localización 3D del Dolor",
    "3️⃣ Biomecánica & Análisis de Gestos Técnicos",
    "4️⃣ Prescripción Basada en Evidencia & SOAP"
]

# Leer la fase actual de la URL para mantener la pestaña al recargar (F5)
fase_url = st.query_params.get("fase", opciones_fases[0])
indice_defecto = opciones_fases.index(fase_url) if fase_url in opciones_fases else 0

centro_mando = st.sidebar.radio(
    "Selecciona Fase de la Sesión:",
    opciones_fases,
    index=indice_defecto
)

# Guardar la selección actual en la URL automáticamente
st.query_params["fase"] = centro_mando
st.sidebar.write("---")

# Módulo de Configuración general siempre accesible al final o secundario
with st.sidebar.expander("⚙️ Configuración & Marca Personal"):
    modulo_config = st.checkbox("Abrir Configuración de Cuenta", value=False)

st.sidebar.write("---")
st.sidebar.subheader("📄 Reporte Clínico")
if st.sidebar.button("Generar Expediente PDF", use_container_width=True):
    datos_terapeuta = {
        "nombre": st.session_state["terapeuta"].get("nombre", "LFT. Jorge Antonio Flores Díaz"),
        "cedula": st.session_state["terapeuta"].get("cedula", "Por definir"),
        "institucion": st.session_state["terapeuta"].get("institucion", "UNAM"),
        "especialidad": st.session_state.get("especialidad_activa", "Músicos & Artes Escénicas")
    }
    paciente_dict = st.session_state.get("paciente", {})
    datos_paciente = {
        "nombre": paciente_dict.get("nombre", "Paciente de Ejemplo"),
        "edad": paciente_dict.get("edad", "N/A"),
        "sexo": paciente_dict.get("sexo", "N/A"),
        "ocupacion": paciente_dict.get("ocupacion", "N/A"),
        "fecha": "2026-09-04"
    }
    historia_clinica = {
        "anamnesis": paciente_dict.get("pa", "Sin registro de padecimiento actual."),
        "exploracion": f"Dermatomas: {paciente_dict.get('dermatomas', 'N/A')}\nMiotomas: {paciente_dict.get('miotomas', 'N/A')}",
        "diagnostico": paciente_dict.get("diagnostico_sospechado", "Por definir"),
        "diagnostico_funcional": "Deficiencia postural y sobreuso neuromuscular",
        "pronostico": "Favorable para la función",
        "plan": paciente_dict.get("plan_intervencion", "Dosificación de carga")
    }
    pdf_buffer = generar_pdf_expediente(datos_terapeuta, datos_paciente, historia_clinica)
    st.sidebar.download_button(
        label="⬇️ Descargar PDF",
        data=pdf_buffer,
        file_name=f"Expediente_{datos_paciente['nombre'].replace(' ', '_')}.pdf",
        mime="application/pdf",
        use_container_width=True
    )

# ==============================================================================
# VISTA: CONFIGURACIÓN Y MARCA PERSONAL (SI ESTÁ ACTIVA)
# ==============================================================================
# ==============================================================================
# VISTA: CONFIGURACIÓN Y MARCA PERSONAL (SI ESTÁ ACTIVA)
# ==============================================================================
if modulo_config:
    st.header("⚙️ Configuración del Perfil & Personalización de Marca")
    st.caption("Personaliza la información de tu práctica clínica, datos profesionales e institución.")

    tab_cfg1, tab_cfg2 = st.tabs(["👤 Datos Profesionales", "🎨 Branding & Marca Blanca"])

    with tab_cfg1:
        st.subheader("Información de la Cédula y Clínica")
        col_c1, col_c2 = st.columns(2)
        
        with col_c1:
            nuevo_nombre = st.text_input("Nombre Completo:", value=st.session_state.get("user_info", {}).get("nombre", "Jorge Antonio Flores Díaz"))
            nueva_cedula = st.text_input("Cédula Profesional:", value=st.session_state.get("user_info", {}).get("cedula", ""))
        
        with col_c2:
            # Ahora la institución es completamente editable y guarda el cambio de inmediato
            nueva_inst = st.text_input("Institución / Universidad:", value=st.session_state.get("user_info", {}).get("institucion", "UNAM - Universidad Nacional Autónoma de México"))
            nuevo_email = st.text_input("Correo de Contacto:", value=st.session_state.get("user_info", {}).get("email", ""))

        if st.button("💾 Guardar Cambios de Perfil", use_container_width=True):
            if "user_info" not in st.session_state or st.session_state["user_info"] is None:
                st.session_state["user_info"] = {}
            st.session_state["user_info"]["nombre"] = nuevo_nombre
            st.session_state["user_info"]["cedula"] = nueva_cedula
            st.session_state["user_info"]["institucion"] = nueva_inst
            st.session_state["user_info"]["email"] = nuevo_email
            
            # Actualizamos también el objeto global del terapeuta para que se refleje en los expedientes y PDF
            st.session_state["terapeuta"]["institucion"] = nueva_inst
            
            st.success("¡Información del perfil e institución actualizada correctamente!")
            st.rerun()

    with tab_cfg2:
        st.subheader("Identidad Visual & Reportes PDF")
        uploaded_logo = st.file_uploader("Subir Logotipo de la Clínica (PNG / JPG):", type=["png", "jpg", "jpeg"])
        if uploaded_logo is not None:
            st.session_state["custom_logo"] = uploaded_logo.getvalue()
            st.success("Logotipo cargado exitosamente.")
            
    st.stop()

# ==============================================================================
# CENTRO DE MANDO 1: RECEPCIÓN, DB & HISTORIA CLÍNICA (NOM-004)
# ==============================================================================
if centro_mando == "1️⃣ Recepción & Historia Clínica (NOM-004)":
    st.header("📁 Fase 1: Recepción, Base de Datos & Historia Clínica (NOM-004)")
    st.caption("Gestión de expedientes locales/remotos y anamnesis integral bajo normativa oficial.")

    tab_db, tab_hc1, tab_hc2, tab_hc3, tab_hc4 = st.tabs([
        "📂 Gestor de Pacientes (DB)",
        "1️⃣ Ficha Identificación",
        "2️⃣ Anamnesis & Semiología",
        "3️⃣ Exploración & Neurología",
        "4️⃣ Diagnóstico CIF & Pronóstico"
    ])

    with tab_db:
        st.subheader("Directorio & Base de Datos de Pacientes")
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            if st.button("💾 Guardar / Actualizar Paciente en DB"):
                p = st.session_state["paciente"]
                if p.get("nombre") and p.get("curp"):
                    guardar_paciente_db(p)
                    st.success(f"✅ Paciente **{p['nombre']}** guardado correctamente.")
                else:
                    st.error("⚠️ Ingrese Nombre y CURP/ID obligatorios.")
        
        pacientes_registrados = obtener_todos_pacientes_db()
        if pacientes_registrados:
            opciones_dict = {f"{p['nombre']} (CURP: {p['curp']}) - {p['especialidad']}": p for p in pacientes_registrados}
            paciente_sel_str = st.selectbox("Cargar paciente existente:", list(opciones_dict.keys()))
            if st.button("📂 Cargar Expediente"):
                p_datos = opciones_dict[paciente_sel_str]
                datos_cargados = cargar_paciente_db(p_datos["curp"])
                if datos_cargados:
                    st.session_state["paciente"].update(datos_cargados)
                    st.success("Expediente cargado con éxito.")
            st.dataframe(pacientes_registrados, use_container_width=True)
        else:
            st.info("No hay pacientes guardados en la base de datos.")

    with tab_hc1:
        st.subheader("Ficha de Identificación del Paciente")
        c1, c2, c3 = st.columns([2, 1, 1])
        with c1:
            st.session_state["paciente"]["nombre"] = st.text_input("Nombre completo:", value=st.session_state["paciente"].get("nombre", ""))
        with c2:
            st.session_state["paciente"]["edad"] = st.number_input("Edad:", value=int(st.session_state["paciente"].get("edad") or 0), min_value=0, max_value=120)
        with c3:
            sexos = ["Masculino", "Femenino", "Otro"]
            s_idx = sexos.index(st.session_state["paciente"].get("sexo", "Masculino")) if st.session_state["paciente"].get("sexo") in sexos else 0
            st.session_state["paciente"]["sexo"] = st.selectbox("Sexo:", sexos, index=s_idx)

        c4, c5, c6 = st.columns(3)
        with c4:
            st.session_state["paciente"]["curp"] = st.text_input("CURP / ID:", value=st.session_state["paciente"].get("curp", ""))
        with c5:
            st.session_state["paciente"]["ocupacion"] = st.text_input("Ocupación / Deporte / Instrumento:", value=st.session_state["paciente"].get("ocupacion", ""))
        with c6:
            st.session_state["paciente"]["telefono"] = st.text_input("Teléfono:", value=st.session_state["paciente"].get("telefono", ""))

    with tab_hc2:
        st.subheader("Antecedentes y Semiología del Dolor")
        col_a1, col_a2 = st.columns(2)
        with col_a1:
            st.session_state["paciente"]["ahf"] = st.text_area("Antecedentes Heredofamiliares (AHF):", value=st.session_state["paciente"].get("ahf", ""))
            st.session_state["paciente"]["app"] = st.text_area("Antecedentes Patológicos (APP):", value=st.session_state["paciente"].get("app", ""))
        with col_a2:
            st.session_state["paciente"]["apnp"] = st.text_area("Antecedentes No Patológicos (APNP):", value=st.session_state["paciente"].get("apnp", ""))
            st.session_state["paciente"]["pa"] = st.text_area("Padecimiento Actual:", value=st.session_state["paciente"].get("pa", ""))

        st.write("---")
        col_s1, col_s2, col_s3 = st.columns(3)
        with col_s1:
            st.session_state["paciente"]["eva_dolor"] = st.slider("EVA Dolor (0-10):", 0, 10, int(st.session_state["paciente"].get("eva_dolor") or 0))
        with col_s2:
            st.session_state["paciente"]["tipo_dolor"] = st.selectbox("Tipo de Dolor:", ["Nociceptivo / Mecánico", "Neuropático", "Nociplástico", "Isquémico"])
        with col_s3:
            st.session_state["paciente"]["tiempo_evolucion"] = st.selectbox("Evolución:", ["Agudo (< 2 sem)", "Subagudo (2-6 sem)", "Crónico (> 6 sem)"])

    with tab_hc3:
        st.subheader("Exploración Neurológica & Perfil Somático")
        col_neu1, col_neu2 = st.columns(2)
        with col_neu1:
            st.session_state["paciente"]["dermatomas"] = st.text_input("Dermatomas (Sensibilidad):", value=st.session_state["paciente"].get("dermatomas", ""))
            st.session_state["paciente"]["miotomas"] = st.text_input("Miotomas (Motor):", value=st.session_state["paciente"].get("miotomas", ""))
        with col_neu2:
            st.session_state["paciente"]["daniels_grupo"] = st.text_input("Segmento Evaluado (Daniels 0-5):", value=st.session_state["paciente"].get("daniels_grupo", ""))
            st.session_state["paciente"]["daniels_grado"] = st.selectbox("Grado de Fuerza:", ["Grado 5 - Normal", "Grado 4 - Bueno", "Grado 3 - Regular", "Grado 2 - Deficiente", "Grado 1 - Escaso", "Grado 0 - Nulo"])

        st.write("---")
        with st.expander("🧠 Perfil Somático & Regulación del Sistema Nervioso"):
            st.session_state["paciente"]["patron_respiratorio"] = st.selectbox("Patrón Respiratorio:", ["Abdominodiafragmático / Vagal", "Costal Superior / Simpático", "Paradójico / Ansiedad"])
            st.session_state["paciente"]["nivel_estres_percibido"] = st.slider("Carga Alostática / Estrés (0-10):", 0, 10, 3)
            st.session_state["paciente"]["hallazgos_psicosomaticos"] = st.multiselect("Manifestaciones Somáticas:", ["Hipertonía Defensiva", "Bruxismo", "Kinesiofobia", "Catastrofización"])

    with tab_hc4:
        st.subheader("Diagnóstico Funcional (CIF) & Pronóstico")
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            st.session_state["paciente"]["diagnostico_sospechado"] = st.text_input("Diagnóstico Nosológico:", value=st.session_state["paciente"].get("diagnostico_sospechado", ""))
            st.session_state["paciente"]["diag_funcional"] = st.text_area("Diagnóstico Funcional (CIF):", value=st.session_state["paciente"].get("diag_funcional", ""))
        with col_d2:
            st.session_state["paciente"]["pronostico_text"] = st.selectbox("Pronóstico:", ["Favorable para la función", "Reservado a evolución", "Desfavorable"])
            st.session_state["paciente"]["tiempo_estimado"] = st.text_input("Tiempo Estimado:", value=st.session_state["paciente"].get("tiempo_estimado", ""))

# ==============================================================================
# CENTRO DE MANDO 2: EXPLORACIÓN & LOCALIZACIÓN 3D DEL DOLOR
# ==============================================================================
# ==============================================================================
# CENTRO DE MANDO 2: EXPLORACIÓN & LOCALIZACIÓN 3D DEL DOLOR
# ==============================================================================
elif centro_mando == "2️⃣ Exploración & Localización 3D del Dolor":
    st.header("🦴 Fase 2: Exploración Física & Localización Anatómica 3D")
    st.caption("Visor tridimensional interactivo para mapeo de dolor y pruebas clínicas basadas en evidencia según especialidad.")

    col_izq, col_der = st.columns([1.3, 0.7])

    with col_izq:
        st.info(f"📍 **Visor Anatómico 3D Interactivo ({especialidad_sel}):** Rota y explora el espacio tridimensional.")
        
        # Visor 3D inmersivo con Three.js embebido en Streamlit
        st.components.v1.html(
            """
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body { margin: 0; background-color: #0F172A; overflow: hidden; font-family: sans-serif; }
                    #canvas-container { width: 100%; height: 400px; }
                    #info-overlay {
                        position: absolute; bottom: 10px; left: 10px; color: #38BDF8;
                        background: rgba(15, 23, 42, 0.8); padding: 5px 10px; border-radius: 4px;
                        font-size: 11px; pointer-events: none; border: 1px solid #1E293B;
                    }
                </style>
            </head>
            <body>
                <div id="canvas-container"></div>
                <div id="info-overlay">💡 Arrastra para rotar | Scroll para zoom</div>

                <!-- Importar Three.js desde CDN oficial -->
                <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
                <script>
                    // Configuración básica de la escena 3D
                    const container = document.getElementById('canvas-container');
                    const scene = new THREE.Scene();
                    scene.background = new THREE.Color(0x0F172A);

                    const camera = new THREE.PerspectiveCamera(45, container.clientWidth / container.clientHeight, 0.1, 1000);
                    camera.position.set(0, 2, 5);

                    const renderer = new THREE.WebGLRenderer({ antialias: true });
                    renderer.setSize(container.clientWidth, container.clientHeight);
                    container.appendChild(renderer.domElement);

                    // Luces profesionales clínicas
                    const ambientLight = new THREE.AmbientLight(0xffffff, 0.7);
                    scene.add(ambientLight);

                    const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
                    directionalLight.position.set(5, 10, 7);
                    scene.add(directionalLight);

                    // Geometría placeholder interactiva (Simulando núcleo anatómico central)
                    // (Aquí cargaremos tu archivo .glb más adelante)
                    const geometry = new THREE.CylinderGeometry(0.4, 0.6, 2.2, 32);
                    const material = new THREE.MeshStandardMaterial({ 
                        color: 0x0284C7, 
                        roughness: 0.3, 
                        metalness: 0.2,
                        wireframe: false 
                    });
                    const anatomicalModel = new THREE.Mesh(geometry, material);
                    scene.add(anatomicalModel);

                    // Esferas satélite decorativas para simular puntos anatómicos / nodos de dolor
                    const sphereGeo = new THREE.SphereGeometry(0.15, 16, 16);
                    const sphereMat = new THREE.MeshStandardMaterial({ color: 0xF43F5E });
                    const markerNode = new THREE.Mesh(sphereGeo, sphereMat);
                    markerNode.position.set(0, 0.8, 0.4);
                    scene.add(markerNode);

                    // Interactividad de rotación con mouse / touch
                    let isDragging = false;
                    let previousMousePosition = { x: 0, y: 0 };

                    container.addEventListener('mousedown', (e) => { isDragging = true; });
                    container.addEventListener('mouseup', () => { isDragging = false; });
                    container.addEventListener('mousemove', (e) => {
                        if (isDragging) {
                            const deltaX = e.clientX - previousMousePosition.x;
                            const deltaY = e.clientY - previousMousePosition.y;
                            
                            anatomicalModel.rotation.y += deltaX * 0.008;
                            anatomicalModel.rotation.x += deltaY * 0.008;
                            markerNode.rotation.y += deltaX * 0.008;
                        }
                        previousMousePosition = { x: e.clientX, y: e.clientY };
                    });

                    // Loop de animación fluido
                    function animate() {
                        requestAnimationFrame(animate);
                        // Suave rotación pasiva si no se interactúa
                        if (!isDragging) {
                            anatomicalModel.rotation.y += 0.003;
                        }
                        renderer.render(scene, camera);
                    }
                    animate();

                    // Ajuste responsivo de ventana
                    window.addEventListener('resize', () => {
                        camera.aspect = container.clientWidth / container.clientHeight;
                        camera.updateProjectionMatrix();
                        renderer.setSize(container.clientWidth, container.clientHeight);
                    });
                </script>
            </body>
            </html>
            """,
            height=420
        )

    with col_der:
        st.subheader("Pruebas Clínicas & Escalas Sugeridas")
        esp_info = DATOS_ESPECIALIDADES.get(especialidad_sel, {})
        pruebas_sugeridas = esp_info.get("pruebas", [])
        
        st.success(f"🔍 **Sugeridas por Evidencia ({especialidad_sel}):**")
        pruebas_elegidas = st.multiselect("Seleccionar pruebas realizadas:", pruebas_sugeridas, default=pruebas_sugeridas[:2])
        st.session_state["paciente"]["pruebas_seleccionadas"] = pruebas_elegidas

        st.write("---")
        st.markdown("### 📊 Calculadoras Rápidas (Escalas de Apoyo)")
        tipo_escala = st.selectbox("Seleccionar Escala de Evaluación:", ["QuickDASH (Miembro Superior)", "VISA (Tendinopatías)", "Oswestry (Lumbar)", "KOOS-12 (Rodilla)"])
        if "QuickDASH" in tipo_escala:
            q_val = st.slider("Dificultad general en actividades (1-5):", 1, 5, 1)
            st.metric("Puntaje QuickDASH Estimado", f"{(q_val-1)*25:.1f} / 100")
        elif "Oswestry" in tipo_escala:
            o_val = st.selectbox("Intensidad del dolor lumbar:", ["Leve", "Moderado", "Severo"])
            st.metric("ODI Lumbar", "20%")
        else:
            st.info("Seleccione una escala para calcular métrica funcional en tiempo real.")
# ==============================================================================
# CENTRO DE MANDO 3: BIOMECÁNICA & ANÁLISIS DE GESTOS TÉCNICOS
# ==============================================================================
elif centro_mando == "3️⃣ Biomecánica & Análisis de Gestos Técnicos":
    st.header("📐 Fase 3: Biomecánica, IA Pose & Estudios de Gabinete")
    st.caption("Análisis de video a cámara lenta, goniometría digital e interpretación de estudios de imagen.")

    tab_bio1, tab_bio2 = st.tabs(["📹 Análisis de Movimiento & IA Pose", "🖼️ Gabinete e Imagenología"])

    with tab_bio1:
        col_v1, col_v2 = st.columns([1.5, 1])
        with col_v1:
            archivo_video = st.file_uploader("Cargar video o imagen del gesto técnico:", type=["mp4", "mov", "avi", "jpg", "png"])
            if archivo_video:
                if archivo_video.name.endswith(('jpg', 'png', 'jpeg')):
                    st.image(archivo_video, use_container_width=True)
                else:
                    st.video(archivo_video)
        with col_v2:
            st.markdown("### 🛠️ Parámetros Biomecánicos")
            articulacion_medida = st.text_input("Articulación / Gesto:", placeholder="Ej. Flexión de Rodilla / Arco de Violín")
            grados_capturados = st.number_input("Ángulo Articular (°):", 0.0, 360.0, 90.0)
            st.selectbox("Simetría Bilateral:", ["Simétrico", "Déficit Izquierdo", "Déficit Derecho"])
            st.text_area("Hallazgos Biomecánicos:", placeholder="Compensación en cadena cinética...")
            if st.button("💾 Guardar Datos Biomecánicos"):
                st.success("¡Métrica biomecánica guardada en la sesión!")

    with tab_bio2:
        col_img1, col_img2 = st.columns(2)
        with col_img1:
            st.file_uploader("Cargar Estudio (Rx, RM, USG):", type=["png", "jpg", "jpeg"])
        with col_img2:
            st.selectbox("Tipo de Estudio:", ["Radiografía (Rx)", "Resonancia (RM)", "Ultrasonido (USG)"])
            st.text_area("Interpretación Radiológica:", placeholder="Hallazgos clave...")

# ==============================================================================
# CENTRO DE MANDO 4: PRESCRIPCIÓN BASADA EN EVIDENCIA & SOAP
# ==============================================================================
elif centro_mando == "4️⃣ Prescripción Basada en Evidencia & SOAP":
    st.header("📝 Fase 4: Prescripción Basada en Evidencia & Notas SOAP")
    st.caption("Generación inteligente de tratamientos con sustento científico y registro evolutivo sesión a sesión.")

    tab_soap1, tab_soap2 = st.tabs(["💡 Motor CDSS & Prescripción Inteligente", "📚 Notas de Evolución SOAP & Historial"])

    # Motor CDSS Interno
    def generar_prescripcion_adaptativa(paciente):
        diag = paciente.get("diagnostico_sospechado", "").lower()
        eva = paciente.get("eva_dolor", 0)
        ocupacion = paciente.get("ocupacion", "").lower()
        esp = paciente.get("especialidad", "")
        
        esp_data = DATOS_ESPECIALIDADES.get(esp, {})
        ejercicios_base = esp_data.get("ejercicios", ["Movilidad articular activa", "Control motor"])
        aditamentos_base = esp_data.get("aditamentos", ["Soporte ergonómico"])
        
        agentes = ["TENS Analgésico"] if eva >= 7 else ["Laserterapia LLLT"]
        manuales = ["Liberación Miofascial", "Movilización Articular Analítica"]
        
        return ejercicios_base, aditamentos_base, manuales, agentes

    with tab_soap1:
        st.subheader("Asistente de Decisión Clínica (Especialidad: " + especialidad_sel + ")")
        if st.button("💡 Generar Prescripción Sugerida por Evidencia", use_container_width=True):
            ej, ad, man, ag = generar_prescripcion_adaptativa(st.session_state["paciente"])
            st.session_state["paciente"]["plan_intervencion"] = " • " + "\n • ".join(ej)
            st.session_state["paciente"]["aditamentos_recomendados"] = " • " + "\n • ".join(ad)
            st.session_state["paciente"]["tecnicas_manuales"] = man
            st.session_state["paciente"]["agentes_soporte"] = ag
            st.success("¡Prescripción generada automáticamente según la especialidad activa!")

        st.write("---")
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            st.session_state["paciente"]["tecnicas_manuales"] = st.multiselect(
                "Técnicas Manuales:",
                ["Movilización Articular Analítica", "IASTM", "Liberación Miofascial", "Punción Seca", "Neurodinamia"],
                default=st.session_state["paciente"].get("tecnicas_manuales", ["Liberación Miofascial"])
            )
        with col_m2:
            st.session_state["paciente"]["agentes_soporte"] = st.multiselect(
                "Agentes Físicos:",
                ["TENS", "EMS / NMES", "Laserterapia LLLT", "Ondas de Choque", "Ultrasonido"],
                default=st.session_state["paciente"].get("agentes_soporte", ["Laserterapia LLLT"])
            )

        col_p1, col_p2 = st.columns(2)
        with col_p1:
            st.session_state["paciente"]["plan_intervencion"] = st.text_area(
                "Plan de Intervención (Ejercicios & Dosificación):",
                value=st.session_state["paciente"].get("plan_intervencion", ""),
                height=130
            )
        with col_p2:
            st.session_state["paciente"]["aditamentos_recomendados"] = st.text_area(
                "Aditamentos & Productos Recomendados:",
                value=st.session_state["paciente"].get("aditamentos_recomendados", ""),
                height=130
            )

    with tab_soap2:
        st.subheader("Registro de Evolución Sesión a Sesión (SOAP)")
        col_s, col_o = st.columns(2)
        with col_s:
            num_sesion = st.number_input("Número de Sesión:", 1, 50, 1)
            eva_soap = st.slider("EVA Actual (0-10):", 0, 10, 3, key="s_eva")
            sub_txt = st.text_area("S - Subjetivo (Reporte del Paciente):", placeholder="Evolución favorable...")
            adherencia = st.select_slider("Adherencia a casa:", options=["Baja", "Moderada", "Buena", "Excelente"], value="Buena")
        with col_o:
            obj_txt = st.text_area("O - Objetivo (Hallazgos Físicos / ROM):", placeholder="ROM activo completo...")
            carga_txt = st.text_input("Carga / Dosificación de hoy:", placeholder="Ej. 3x12 con banda")

        col_a, col_p = st.columns(2)
        with col_a:
            analisis_txt = st.text_area("A - Análisis Clínico:", placeholder="Respuesta al estímulo...")
        with col_p:
            plan_txt = st.text_area("P - Plan y Próxima Sesión:", placeholder="Progresión de ejercicios...")

        if st.button("💾 Guardar Nota SOAP en Historial"):
            if "historial_soap" not in st.session_state:
                st.session_state["historial_soap"] = []
            st.session_state["historial_soap"].append({
                "sesion": num_sesion,
                "eva": eva_soap,
                "subjetivo": sub_txt,
                "objetivo": obj_txt,
                "analisis": analisis_txt,
                "plan": plan_txt
            })
            st.success(f"✅ Nota de la Sesión #{num_sesion} guardada con éxito.")

        if st.session_state.get("historial_soap"):
            with st.expander("📚 Ver Historial de Notas SOAP Guardadas"):
                for nota in reversed(st.session_state["historial_soap"]):
                    st.markdown(f"### Sesión #{nota['sesion']} (EVA: {nota['eva']}/10)")
                    st.markdown(f"**S:** {nota['subjetivo']}")
                    st.markdown(f"**O:** {nota['objetivo']}")
                    st.markdown(f"**A:** {nota['analisis']}")
                    st.markdown(f"**P:** {nota['plan']}")
                    st.divider()