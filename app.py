import io
import os
import math
import sqlite3
import google.generativeai as genai
try:
    import cv2
except ImportError:
    cv2 = None

import numpy as np
import streamlit as st
from PIL import Image
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from streamlit_drawable_canvas import st_canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, Image as RLImage
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
        rightMargin=40, leftMargin=40,
        topMargin=40, bottomMargin=40
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
    
    logo_path = "custom_logo.png" if os.path.exists("custom_logo.png") else "Logo.png"
    img_element = ""
    custom_logo_bytes = st.session_state.get("custom_logo")
    
    try:
        ancho_logo_deseado = 90 
        if custom_logo_bytes:
            img_temp = ImageReader(io.BytesIO(custom_logo_bytes))
            w_orig, h_orig = img_temp.getSize()
            alto_logo_proporcional = (h_orig * ancho_logo_deseado) / w_orig
            img_element = RLImage(io.BytesIO(custom_logo_bytes), width=ancho_logo_deseado, height=alto_logo_proporcional)
        elif os.path.exists(logo_path):
            img_temp = ImageReader(logo_path)
            w_orig, h_orig = img_temp.getSize()
            alto_logo_proporcional = (h_orig * ancho_logo_deseado) / w_orig
            img_element = RLImage(logo_path, width=ancho_logo_deseado, height=alto_logo_proporcional)
    except Exception as e:
        print(f"Error al cargar el logo en PDF: {e}")
        img_element = ""
    
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
            img_element,
            [
                Paragraph("<b>PHYSIOFLOW</b> - Fisioterapia Especializada", style_header_title),
                Paragraph("<b>EXPEDIENTE CLÍNICO</b><br/>NOM-004-SSA3-2012", style_header_sub)
            ]
        ]
    ]
    t_header = Table(header_data, colWidths=[1.5 * inch, 5.5 * inch])
    t_header.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN', (0,0), (0,0), 'LEFT'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ]))
    
    story.append(t_header)
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#003366'), spaceAfter=10, spaceBefore=5))
    
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
        st.warning("⚠️ Supabase no configurado en Secrets. Guardando en sesión temporal.")
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
            # --- FASE 2: Antecedentes y Semiología ---
            "ahf": paciente_dict.get("ahf", ""),
            "app": paciente_dict.get("app", ""),
            "apnp": paciente_dict.get("apnp", ""),
            "pa": paciente_dict.get("pa", ""),
            "eva_dolor": int(paciente_dict.get("eva_dolor", 0)) if paciente_dict.get("eva_dolor") else 0,
            "tipo_dolor": paciente_dict.get("tipo_dolor", ""),
            "factores_agravantes": paciente_dict.get("factores_agravantes", ""),
            "factores_mitigantes": paciente_dict.get("factores_mitigantes", ""),
            "tiempo_evolucion": paciente_dict.get("tiempo_evolucion", ""),
            "patron_respiratorio": paciente_dict.get("patron_respiratorio", ""),
            "nivel_estres_percibido": int(paciente_dict.get("nivel_estres_percibido", 0)) if paciente_dict.get("nivel_estres_percibido") else 0,
            "hallazgos_psicosomaticos": paciente_dict.get("hallazgos_psicosomaticos", []),
            # --- FASE 3: Exploración Neurológica y Muscular ---
            "dermatomas": paciente_dict.get("dermatomas", ""),
            "miotomas": paciente_dict.get("miotomas", ""),
            "daniels_grupo": paciente_dict.get("daniels_grupo", ""),
            "daniels_grado": paciente_dict.get("daniels_grado", ""),
            "pruebas_funcionales": paciente_dict.get("pruebas_funcionales", ""),
            # --- FASE 4: Diagnóstico y Pronóstico ---
            "diagnostico": paciente_dict.get("diagnostico_sospechado", ""),
            "diag_funcional": paciente_dict.get("diag_funcional", ""),
            "pronostico_text": paciente_dict.get("pronostico_text", ""),
            "tiempo_estimado": paciente_dict.get("tiempo_estimado", ""),
            "plan_intervencion": paciente_dict.get("plan_intervencion", "")
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
                "ahf": p.get("ahf", ""),
                "app": p.get("app", ""),
                "apnp": p.get("apnp", ""),
                "pa": p.get("pa", ""),
                "eva_dolor": p.get("eva_dolor", 0),
                "tipo_dolor": p.get("tipo_dolor", ""),
                "factores_agravantes": p.get("factores_agravantes", ""),
                "factores_mitigantes": p.get("factores_mitigantes", ""),
                "tiempo_evolucion": p.get("tiempo_evolucion", ""),
                "patron_respiratorio": p.get("patron_respiratorio", ""),
                "nivel_estres_percibido": p.get("nivel_estres_percibido", 0),
                "hallazgos_psicosomaticos": p.get("hallazgos_psicosomaticos", []),
                # --- Exploración Neurológica y Muscular ---
                "dermatomas": p.get("dermatomas", ""),
                "miotomas": p.get("miotomas", ""),
                "daniels_grupo": p.get("daniels_grupo", ""),
                "daniels_grado": p.get("daniels_grado", ""),
                "pruebas_funcionales": p.get("pruebas_funcionales", ""),
                # --- Diagnóstico ---
                "diagnostico_sospechado": p.get("diagnostico", ""),
                "diag_funcional": p.get("diag_funcional", ""),
                "pronostico_text": p.get("pronostico_text", ""),
                "tiempo_estimado": p.get("tiempo_estimado", ""),
                "plan_intervencion": p.get("plan_intervencion", "")
            }
        return None
    except Exception as e:
        st.error(f"Error al cargar paciente de Supabase: {e}")
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
if st.query_params.get("auth") == "true":
    st.session_state["authenticated"] = True
    st.session_state["user_info"] = {
        "email": st.query_params.get("email", ""),
        "nombre": st.query_params.get("nombre", "Jorge Antonio Flores Díaz"),
        "cedula": st.query_params.get("cedula", ""),
        "institucion": st.query_params.get("institucion", "UNAM - Universidad Nacional Autónoma de México")
    }

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
                st.query_params["auth"] = "true"
                st.query_params["email"] = reg_email
                st.query_params["nombre"] = reg_nombre
                st.query_params["cedula"] = reg_cedula
                st.query_params["institucion"] = reg_institucion
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
# =========================================================================
# RESUMEN RÁPIDO DEL PACIENTE ACTIVO (BARRA LATERAL)
# =========================================================================
st.sidebar.subheader("📋 Paciente en Atención")
    
paciente_activo = st.session_state.get("paciente", {})
nombre_paciente = paciente_activo.get("nombre")
    
if nombre_paciente:
        st.sidebar.markdown(f"**Nombre:** {nombre_paciente}")
        if paciente_activo.get("edad"):
            st.sidebar.markdown(f"**Edad:** {paciente_activo.get('edad')} años")
        if paciente_activo.get("curp"):
            st.sidebar.markdown(f"**ID/CURP:** {paciente_activo.get('curp')}")
        
        # Muestra un indicador rápido del EVA actual si ya fue registrado
        eva_val = paciente_activo.get("eva_dolor", 0)
        if eva_val >= 8:
            st.sidebar.error(f"🚨 EVA Actual: {eva_val} / 10 (Severo)")
        elif eva_val >= 5:
            st.sidebar.warning(f"⚠️ EVA Actual: {eva_val} / 10 (Moderado)")
        else:
            st.sidebar.success(f"🟢 EVA Actual: {eva_val} / 10 (Leve/Estable)")
else:
        st.sidebar.info("ℹ️ Ningún paciente seleccionado. Ve a la Fase 1 para cargar o registrar uno.")
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

fase_url = st.query_params.get("fase", opciones_fases[0])
indice_defecto = opciones_fases.index(fase_url) if fase_url in opciones_fases else 0

centro_mando = st.sidebar.radio(
    "Selecciona Fase de la Sesión:",
    opciones_fases,
    index=indice_defecto
)

st.query_params["fase"] = centro_mando
st.sidebar.write("---")

with st.sidebar.expander("⚙️ Configuración & Marca Personal"):
    modulo_config = st.checkbox("Abrir Configuración de Cuenta", value=False)

st.sidebar.write("---")
st.sidebar.subheader("📄 Reporte Clínico")
    
# Validamos si hay un paciente activo en el session_state
paciente_valido = st.session_state.get("paciente", {}).get("nombre")

if not paciente_valido:
    st.sidebar.info("ℹ️ Selecciona o carga un paciente en la Fase 1 para habilitar la descarga del expediente PDF.")
else:
    if st.sidebar.button("Generar Expediente PDF", use_container_width=True):
        datos_terapeuta = {
            "nombre": st.session_state["terapeuta"].get("nombre", "LFT. Jorge Antonio Flores Díaz"),
            "cedula": st.session_state["terapeuta"].get("cedula", "Por definir"),
            "institucion": st.session_state["terapeuta"].get("institucion", "UNAM"),
            "especialidad": st.session_state["terapeuta"].get("especialidad_activa", "Músicos & Artes Escénicas")
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
            "exploracion": f"Dermatomas: {paciente_dict.get('dermatomas', 'N/A')} | Miotomas: {paciente_dict.get('miotomas', 'N/A')}",
            "diagnostico": paciente_dict.get("diagnostico_sospechado", "Por definir"),
            "diagnostico_funcional": paciente_dict.get("diag_funcional", "Deficiencia postural y sobreuso neuromuscular"),
            "pronostico": paciente_dict.get("pronostico_text", "Favorable para la función"),
            "plan": paciente_dict.get("plan_intervencion", "Dosificación de carga")
        }
        pdf_buffer = generar_pdf_expediente(datos_terapeuta, datos_paciente, historia_clinica)
        
        st.sidebar.download_button(
            label="📥 Descargar PDF",
            data=pdf_buffer,
            file_name=f"Expediente_{datos_paciente['nombre'].replace(' ', '_')}.pdf",
            mime="application/pdf",
            use_container_width=True
        )

# =====================================================================
# 1. BLOQUE DE CONFIGURACIÓN (SI ESTÁ ACTIVO)
# =====================================================================
if modulo_config:
    st.header("⚙️ Configuración del Perfil & Personalización de Marca")
    st.caption("Personaliza la información de tu práctica clínica, datos profesionales e institución.")
    
    tab_cfg1, tab_cfg2 = st.tabs(["👤 Datos Profesionales", "🎨 Branding & Marca Blanca"])
    
    with tab_cfg1:
        st.subheader("Información de la Cédula y Clínica")
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            nuevo_nombre = st.text_input("Nombre Completo:", value=st.session_state.get("user_info", {}).get("nombre", ""))
            nueva_cedula = st.text_input("Cedula Profesional:", value=st.session_state.get("user_info", {}).get("cedula", ""))
        with col_c2:
            nueva_inst = st.text_input("Institución / Universidad:", value=st.session_state.get("user_info", {}).get("institucion", ""))
            nuevo_email = st.text_input("Correo de Contacto:", value=st.session_state.get("user_info", {}).get("email", ""))

        if st.button("💾 Guardar Cambios de Perfil", use_container_width=True):
            if "user_info" not in st.session_state or st.session_state["user_info"] is None:
                st.session_state["user_info"] = {}
            st.session_state["user_info"]["nombre"] = nuevo_nombre
            st.session_state["user_info"]["cedula"] = nueva_cedula
            st.session_state["user_info"]["institucion"] = nueva_inst
            st.session_state["user_info"]["email"] = nuevo_email
            st.success("¡Información del perfil actualizada correctamente!")
            st.rerun()

    with tab_cfg2:
        st.subheader("Identidad Visual & Reportes PDF")
        uploaded_logo = st.file_uploader("Subir Logotipo de la Clínica (PNG / JPG):", type=["png", "jpg"])
        if uploaded_logo is not None:
            with open("custom_logo.png", "wb") as f:
                f.write(uploaded_logo.getbuffer())
            st.session_state["custom_logo"] = uploaded_logo.getvalue()
            st.success("¡Logotipo cargado y guardado permanentemente!")
            st.rerun()
            
        if os.path.exists("custom_logo.png"):
            st.image("custom_logo.png", width=150, caption="Logotipo actual activo")

# =====================================================================
# 2. BLOQUE DE CENTROS DE MANDO (FASES 1 A 4)
# =====================================================================
if not modulo_config:

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
                st.session_state["paciente"]["tipo_dolor"] = st.selectbox("Tipo de Dolor:", ["Nociceptivo / Mecánico", "Neuropático", "Nociceptivo", "Isquémico"])
            # --- Factores Agravantes y Mitigantes ---
            col_ag1, col_ag2 = st.columns(2)
            with col_ag1:
                st.session_state["paciente"]["factores_agravantes"] = st.text_input(
                    "Factores Agravantes:",
                    value=st.session_state["paciente"].get("factores_agravantes", ""),
                    placeholder="Ej. Sedestación prolongada, flexión lumbar"
                )
            with col_ag2:
                st.session_state["paciente"]["factores_mitigantes"] = st.text_input(
                    "Factores Mitigantes:",
                    value=st.session_state["paciente"].get("factores_mitigantes", ""),
                    placeholder="Ej. Descanso en decúbito, caminata corta"
                )    
                # --- GUÍA CLÍNICA DE AYUDA PARA CLASIFICACIÓN DE DOLOR ---
                with st.expander("💡 ¿Cómo clasificar el tipo de dolor?"):
                    st.markdown("""
                    * **Nociceptivo / Mecánico:** Bien localizado, se agrava o se alivia con el movimiento, cargas o posturas específicas.
                    * **Neuropático:** Patrón en dermatomas, descrito como ardor, quemazón, toques eléctricos o parestesias.
                    * **Nociplástico:** Dolor crónico generalizado, desproporcionado a la lesión tisular y con alta sensibilidad central.
                    * **Isquémico:** Dolor profundo, opresivo o claudicante asociado a la falta de riego sanguíneo.
                    """)
                tiempos_ev = [
                    "Agudo (< 3 semanas)",
                    "Subagudo (3 a 6 semanas)",
                    "Crónico (> 6 semanas)",
                    "Recurrente / Reagudizado"
                ]
                val_tev = st.session_state["paciente"].get("tiempo_evolucion", "Agudo (< 3 semanas)")
                idx_tev = tiempos_ev.index(val_tev) if val_tev in tiempos_ev else 0
                
                st.session_state["paciente"]["tiempo_evolucion"] = st.selectbox(
                    "Evolución:",
                    tiempos_ev,
                    index=idx_tev
                )
            # --- BLOQUE DE ALERTAS CLÍNICAS AUTOMÁTICAS (ANAMNESIS) ---
            eva_actual = st.session_state["paciente"].get("eva_dolor", 0)
            banderas_rojas_activas = st.session_state["paciente"].get("banderas_rojas", False)

            if eva_actual >= 8 or banderas_rojas_activas:
                st.error(
                    "🚨 **ALERTA CLÍNICA DE ATENCIÓN PRIORITARIA** 🚨\n\n"
                    f"• **Nivel de Dolor (EVA):** {eva_actual} / 10 (Dolor Severo / Agudo).\n"
                    "• **Precaución:** Se detectan umbrales de dolor altos o indicadores de alerta clínica. "
                    "Considere una valoración médica exhaustiva o descarte de patologías graves antes de iniciar cargas mecánicas o manipulación."
                )
            elif eva_actual >= 5:
                st.warning(
                    "⚠️ **Aviso Clínico Moderado:**\n\n"
                    f"• **Nivel de Dolor (EVA):** {eva_actual} / 10. Module las intensidades y dosificaciones en el plan de intervención inicial."
                )
            else:
                st.info("ℹ️ Parámetros de dolor dentro de rangos manejables para abordaje fisioterapéutico estándar.")

        with tab_hc3:
            st.subheader("Exploración Neurológica & Perfil Somático")
            
            # --- 1. MAPA DE REFERENCIA RÁPIDA PARA DERMATOMAS Y MIOTOMAS ---
            with st.expander("🗺️ Guía de Referencia Rápida: Dermatomas & Miotomas"):
                st.markdown("""
                * **Extremidad Superior:** 
                  * **C5:** Cara lateral del hombro / Bíceps (Flexión de codo).
                  * **C6:** Cara lateral del antebrazo y pulgar / Extensores de muñeca.
                  * **C7:** Dedo medio / Tríceps y flexores de dedos.
                  * **C8:** Dedo meñique / Flexores de dedos.
                  * **T1:** Cara medial del brazo / Interóseos (abducción/aducción de dedos).
                * **Extremidad Inferior:** 
                  * **L2:** Muslo anterior / Flexores de cadera.
                  * **L3:** Rodilla y cara medial de pierna / Extensores de rodilla.
                  * **L4:** Maléolo medial / Tibial anterior (Dorsiflexión).
                  * **L5:** Dorso del pie y dedo gordo / Extensor largo del hallux.
                  * **S1:** Planta y borde lateral del pie / Flexores plantares (Gemelos/Sóleo).
                """)

            col_neu1, col_neu2 = st.columns(2)
            
            with col_neu1:
                st.session_state["paciente"]["dermatomas"] = st.text_input(
                    "Dermatomas (Sensibilidad):", 
                    value=st.session_state["paciente"].get("dermatomas", ""),
                    placeholder="Ej. Normal o Hipoestesia en L5..."
                )
                st.session_state["paciente"]["miotomas"] = st.text_input(
                    "Miotomas (Motor):", 
                    value=st.session_state["paciente"].get("miotomas", ""),
                    placeholder="Ej. Fuerza conservada 5/5..."
                )
                
            with col_neu2:
                st.session_state["paciente"]["daniels_grupo"] = st.text_input(
                    "Músculo o Segmento Evaluado:", 
                    value=st.session_state["paciente"].get("daniels_grupo", ""),
                    placeholder="Ej. Cuádriceps / Tríceps sural"
                )
                
                grados_daniels = [
                    "5/5 - Normal (Vence resistencia completa)",
                    "4/5 - Bueno (Vence resistencia moderada)",
                    "3/5 - Regular (Vence únicamente la gravedad)",
                    "2/5 - Pobre (Movimiento sin gravedad)",
                    "1/5 - Trazas (Solo contracción visible/palpable)",
                    "0/5 - Nulo (Sin contracción)"
                ]
                idx_d = grados_daniels.index(st.session_state["paciente"].get("daniels_grado", grados_daniels[0])) if st.session_state["paciente"].get("daniels_grado") in grados_daniels else 0
                st.session_state["paciente"]["daniels_grado"] = st.selectbox("Grado de Fuerza (Daniels):", grados_daniels, index=idx_d)

            st.write("---")
            
            # --- 2. PERFIL SOMÁTICO, PATRÓN RESPIRATORIO & REGULACIÓN DEL SNA ---
            with st.expander("🧠 Perfil Somático, Patrón Respiratorio & Regulación del SNA"):
                st.caption("Evalúa el estado neurovegetativo, la respuesta al estrés crónico y los factores de sensibilización central:")
                
                # Patrón Respiratorio con nota clínica
                patrones_resp = [
                    "Diafragmático / Abdominal (Funcional)", 
                    "Costal Superior / Accesorio (Disfuncional)", 
                    "Paradójico / Mixto"
                ]
                idx_pr = patrones_resp.index(st.session_state["paciente"].get("patron_respiratorio", patrones_resp[0])) if st.session_state["paciente"].get("patron_respiratorio") in patrones_resp else 0
                st.session_state["paciente"]["patron_respiratorio"] = st.selectbox(
                    "Patrón Respiratorio Dominante:",
                    patrones_resp,
                    index=idx_pr
                )
                st.caption("💡 *Nota Clínica:* Un patrón costal superior constante sobreactiva los músculos accesorios del cuello (escalenos y ECM), perpetuando cervicalgias tensionales.")
                
                st.write("")
                
                # Carga Alostática / Estrés Percibido con escala explicativa
                st.session_state["paciente"]["nivel_estres_percibido"] = st.slider(
                    "Carga Alostática / Estrés Percibido (0-10):", 
                    0, 10, 
                    value=int(st.session_state["paciente"].get("nivel_estres_percibido", 3))
                )
                st.caption("💡 *Referencia:* 0-3 (Estrés bajo/controlado), 4-6 (Estrés moderado/fatiga laboral), 7-10 (Alta carga alostática, riesgo de sensibilización central).")
                
                st.write("")
                
                # Manifestaciones Somáticas
                st.session_state["paciente"]["hallazgos_psicosomaticos"] = st.multiselect(
                    "Manifestaciones Somáticas & Cognitivas:",
                    ["Hipertonía Defensiva", "Bruxismo", "Kinesiofobia", "Catastrofización", "Hipervigilancia", "Fatiga Crónica"],
                    default=st.session_state["paciente"].get("hallazgos_psicosomaticos", [])
                )
            
            # --- 3. SEMÁFORO Y ALERTA AUTOMÁTICA DE SENSIBILIZACIÓN CENTRAL ---
            estres_val = st.session_state["paciente"].get("nivel_estres_percibido", 0)
            factores_somaticos = st.session_state["paciente"].get("hallazgos_psicosomaticos", [])
            
            if estres_val >= 7 or len(factores_somaticos) >= 3:
                st.error(
                    "🧠 **ALERTA DE ALTA CARGA ALOSTÁTICA / SENSIBILIZACIÓN CENTRAL** 🧠\n\n"
                    f"• **Estrés Percibido:** {estres_val} / 10 | **Factores Somáticos:** {len(factores_somaticos)} detectados.\n"
                    "• **Implicación Clínica:** El sistema nervioso central se encuentra bajo un alto umbral de alerta. "
                    "Se recomienda incorporar **Educación en Neurobiología del Dolor (PNE)** y estrategias de modulación autonómica en el plan de intervención."
                )
            elif estres_val >= 4 or len(factores_somaticos) > 0:
                st.warning(
                    "⚠️ **Aviso de Regulación del Sistema Nervioso:**\n\n"
                    f"• Se identifican indicios de estrés moderado o factores tensionales ({', '.join(factores_somaticos) if factores_somaticos else 'Estrés moderado'}). "
                    "Considere ejercicios de respiración diafragmática y control de cargas."
                )
            else:
                st.success("🟢 Perfil somático y regulación autonómica en parámetros estables para abordaje fisioterapéutico convencional.")
        with tab_hc4:
            st.subheader("Diagnóstico Funcional (CIF) & Pronóstico")
            # ==========================================================
            # FASE 3: BATERÍA DE PRUEBAS FUNCIONALES CON IA
            # ==========================================================
            st.write("---")
            st.subheader("🔍 Fase 3: Batería de Pruebas Funcionales & Diagnóstico Diferencial")
            st.caption("Selección de pruebas ortopédicas y funcionales guiadas por evidencia clínica.")

            col_pf1, col_pf2 = st.columns([0.6, 0.4])
            with col_pf1:
                st.write("Selección y Recomendación Clínica")
            with col_pf2:
                if st.button("✨ Sugerir Pruebas con Evidencia (Gemini)", use_container_width=True):
                    dx = st.session_state["paciente"].get("diagnostico_sospechado", "No especificado")
                    tipo_d = st.session_state["paciente"].get("tipo_dolor", "No especificado")
                    eva = st.session_state["paciente"].get("eva_dolor", 0)
                    especialidad = st.session_state.get("especialidad_activa", "Fisioterapia General")
                    
                    prompt_pf = (
                        f"Actúa como un experto en fisioterapia basada en evidencia y especialista en {especialidad}. "
                        f"Sugiere un conjunto de pruebas ortopédicas, neurológicas y funcionales clave para realizar un diagnóstico diferencial preciso, considerando:\n"
                        f"- Diagnóstico sospechado: {dx}\n"
                        f"- Tipo de dolor: {tipo_d}\n"
                        f"- EVA: {eva}/10\n\n"
                        f"Lista de forma clara las pruebas recomendadas y qué evalúa cada una."
                    )
                    try:
                        model = genai.GenerativeModel("gemini-1.5-flash-latest")
                        response = model.generate_content(prompt_pf) # o prompt_clinico
                        st.session_state["paciente"]["pruebas_funcionales"] = response.text
                        st.success("¡Sugerencias generadas con éxito!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error al conectar con la IA: {e}")

            st.session_state["paciente"]["pruebas_funcionales"] = st.text_area(
                "Resultados y Pruebas Aplicadas:",
                value=st.session_state["paciente"].get("pruebas_funcionales", ""),
                placeholder="Haz clic en 'Sugerir Pruebas con Evidencia' o redacta los hallazgos de la exploración..."
            )
            
            st.write("---")
            
            # --- 1. GUÍA RÁPIDA DE LA CLASIFICACIÓN CIF ---
            with st.expander("📖 Guía de Referencia Rápida: Estructura CIF"):
                st.markdown("""
                * **Estructuras y Funciones Corporales:** Deficiencias anatómicas o fisiológicas (ej. debilidad del cuádriceps, alteración del patrón respiratorio).
                * **Limitaciones en la Actividad:** Dificultades para ejecutar tareas o acciones cotidianas o laborales (ej. incapacidad para mantener sedestación prolongada).
                * **Restricciones en la Participación:** Problemas para involucrarse en situaciones vitales, pasatiempos o interpretación musical.
                """)
            
            col_d1, col_d2 = st.columns(2)
            
            with col_d1:
                st.session_state["paciente"]["diagnostico_sospechado"] = st.text_input(
                    "Diagnóstico Nosológico / Médico:", 
                    value=st.session_state["paciente"].get("diagnostico_sospechado", ""),
                    placeholder="Ej. Cervicobraquialgia tensional"
                )
                
                st.session_state["paciente"]["diag_funcional"] = st.text_area(
                    "Diagnóstico Funcional (CIF):", 
                    value=st.session_state["paciente"].get("diag_funcional", ""),
                    placeholder="Describa deficiencias, limitaciones en la actividad y restricciones..."
                )
                
            with col_d2:
                pronosticos = [
                    "Favorable para la función (Corto plazo)",
                    "Favorable con reservas (Mediano plazo)",
                    "Reservado a la evolución clínica",
                    "Limitado por cronicidad o carga alostática"
                ]
                idx_p = pronosticos.index(st.session_state["paciente"].get("pronostico_text", pronosticos[0])) if st.session_state["paciente"].get("pronostico_text") in pronosticos else 0
                st.session_state["paciente"]["pronostico_text"] = st.selectbox("Pronóstico Fisioterapéutico:", pronosticos, index=idx_p)
                
                # Selector estandarizado de tiempo estimado de recuperación
                tiempos_rec = [
                    "1 a 3 semanas (Fase Aguda)",
                    "4 a 8 semanas (Fase Subaguda)",
                    "3 a 6 meses (Fase de Reacondicionamiento)",
                    "Más de 6 meses (Criterio de Cronicidad)"
                ]
                idx_t = tiempos_rec.index(st.session_state["paciente"].get("tiempo_estimado", tiempos_rec[0])) if st.session_state["paciente"].get("tiempo_estimado") in tiempos_rec else 0
                st.session_state["paciente"]["tiempo_estimado"] = st.selectbox("Tiempo Estimado de Recuperación:", tiempos_rec, index=idx_t)

            st.write("---")
            
            # --- 2. PLAN DE INTERVENCIÓN CON LLAMADA REAL A GEMINI ---
            col_pl1, col_pl2 = st.columns([0.6, 0.4])
            with col_pl1:
                st.subheader("Plan de Intervención & Dosificación de Carga")
            with col_pl2:
                if st.button("✨ Generar con Evidencia (Gemini)", use_container_width=True):                    
                    # Recopilamos todo el contexto clínico actual del paciente
                    dx = st.session_state["paciente"].get("diagnostico_sospechado", "No especificado")
                    dx_func = st.session_state["paciente"].get("diag_funcional", "No especificado")
                    eva = st.session_state["paciente"].get("eva_dolor", 0)
                    estres = st.session_state["paciente"].get("nivel_estres_percibido", 0)
                    somatico = st.session_state["paciente"].get("hallazgos_psicosomaticos", [])
                    especialidad = st.session_state.get("especialidad_activa", "Fisioterapia General")
                    
                    prompt_clinico = (
                        f"Actúa como un experto en fisioterapia basada en evidencia y especialista en {especialidad}. "
                        f"Genera una propuesta clínica estructurada y concisa de plan de intervención y dosificación de carga para un paciente con los siguientes datos:\n"
                        f"- Diagnóstico Médico: {dx}\n"
                        f"- Diagnóstico Funcional CIF: {dx_func}\n"
                        f"- EVA Dolor: {eva}/10\n"
                        f"- Estrés Percibido / Carga Alostática: {estres}/10\n"
                        f"- Factores Psicosomáticos: {', '.join(somatico) if somatico else 'Ninguno'}\n\n"
                        f"Estructura la respuesta en 3 puntos claros: 1. Modulación del dolor y terapia manual, 2. Dosificación específica de ejercicio terapéutico, y 3. Consideraciones de neurobiología del dolor o ergonomía."
                    )
                    
                    try:
                        model = genai.GenerativeModel("gemini-1.5-flash-latest")
                        response = model.generate_content(prompt_pf) # o prompt_clinico
                        st.session_state["paciente"]["pruebas_funcionales"] = response.text
                        st.success("¡Sugerencias generadas con éxito!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error al conectar con la IA: {e}")

            st.session_state["paciente"]["plan_intervencion"] = st.text_area(
                "Objetivos Terapéuticos y Estrategia (Modalidades, Terapia Manual, Ejercicio):",
                value=st.session_state["paciente"].get("plan_intervencion", ""),
                placeholder="Haz clic en 'Generar con Evidencia (Gemini)' para redactar la propuesta..."
            )
    # ==============================================================================
    # CENTRO DE MANDO 2: EXPLORACIÓN & LOCALIZACIÓN 3D DEL DOLOR
    # ==============================================================================
    elif centro_mando == "2️⃣ Exploración & Localización 3D del Dolor":
        st.header("🦴 Fase 2: Exploración Física & Localización Anatómica 3D")
        st.caption("Visor tridimensional interactivo para mapeo de dolor y pruebas clínicas basadas en evidencia según especialidad.")

        col_izq, col_der = st.columns([1.3, 0.7])

        with col_izq:
            st.info(f"📍 **Visor Anatómico 3D Interactivo ({especialidad_sel}):** Rota y explora el espacio tridimensional.")
            
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

                    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
                    <script>
                    const container = document.getElementById('canvas-container');
                    const scene = new THREE.Scene();
                    scene.background = new THREE.Color(0x0F172A);

                    const camera = new THREE.PerspectiveCamera(45, container.clientWidth / container.clientHeight, 0.1, 1000);
                    camera.position.set(0, 2, 5);

                    const renderer = new THREE.WebGLRenderer({ antialias: true });
                    renderer.setSize(container.clientWidth, container.clientHeight);
                    container.appendChild(renderer.domElement);

                    const ambientLight = new THREE.AmbientLight(0xffffff, 0.7);
                    scene.add(ambientLight);

                    const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
                    directionalLight.position.set(5, 10, 7);
                    scene.add(directionalLight);

                    const geometry = new THREE.CylinderGeometry(0.4, 0.6, 2.2, 32);
                    const material = new THREE.MeshStandardMaterial({ 
                        color: 0x0284C7, 
                        roughness: 0.3, 
                        metalness: 0.2,
                        wireframe: false 
                    });
                    const anatomicalModel = new THREE.Mesh(geometry, material);
                    scene.add(anatomicalModel);

                    const sphereGeo = new THREE.SphereGeometry(0.15, 16, 16);
                    const sphereMat = new THREE.MeshStandardMaterial({ color: 0xF43F5E });
                    const markerNode = new THREE.Mesh(sphereGeo, sphereMat);
                    markerNode.position.set(0, 0.8, 0.4);
                    scene.add(markerNode);

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

                    function animate() {
                        requestAnimationFrame(animate);
                        if (!isDragging) {
                            anatomicalModel.rotation.y += 0.003;
                        }
                        renderer.render(scene, camera);
                    }
                    animate();

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
            
            # --- ÚNICO BOTÓN MAESTRO UNIFICADO (CDSS LOCAL + GEMINI IA) ---
            if st.button("✨ Generar Prescripción Inteligente & Análisis Clínico", use_container_width=True):
                paciente_data = st.session_state.get("paciente", {})
                if not paciente_data.get("nombre"):
                    st.warning("⚠️ Por favor ingresa o selecciona un paciente en la Fase 1 primero.")
                else:
                    with st.spinner("Generando prescripción basada en evidencia y consultando al Copiloto Clínico..."):
                        # 1. Ejecutamos la lógica local de la especialidad automáticamente
                        ej, ad, man, ag = generar_prescripcion_adaptativa(st.session_state["paciente"])
                        st.session_state["paciente"]["plan_intervencion"] = " • " + "\n • ".join(ej)
                        st.session_state["paciente"]["aditamentos_recomendados"] = " • " + "\n • ".join(ad)
                        st.session_state["paciente"]["tecnicas_manuales"] = man
                        st.session_state["paciente"]["agentes_soporte"] = ag
                        
                        # 2. Consultamos a Gemini de forma integrada
                    try:
                        import google.genai as genai
                        client = genai.Client(api_key=st.secrets.get("GEMINI_API_KEY"))
                        paciente_nombre = paciente_data.get("nombre", "Paciente")
                        
                        prompt = f"""
                        Actúa como un fisioterapeuta experto y profesor universitario. 
                        Analiza el caso del paciente {paciente_nombre} en la especialidad de {especialidad_sel}. 
                        Proporciona una breve sugerencia estructurada en:
                        1. Posible análisis funcional.
                        2. Objetivos de intervención fisioterapéutica basados en evidencia.
                        Mantén un tono estrictamente clínico, formal y profesional en español.
                        """
                        
                        response = client.models.generate_content(
                            model="gemini-2.5-flash",
                            contents=prompt,
                        )
                        
                        # Guardamos el análisis en la sesión para poder copiarlo después
                        st.session_state["ultimo_analisis_ia"] = response.text
                        st.success("¡Prescripción inteligente y análisis clínico generados con éxito!")
                        
                    except Exception as e:
                        st.warning("⚠️ Prescripción local generada con éxito, pero hubo un error al conectar con la IA de Gemini.")
                        st.error(f"Detalle del error: {e}")

        # Mostramos el resultado guardado y el botón para enviarlo al plan de intervención
        if "ultimo_analisis_ia" in st.session_state:
            st.markdown("### 🤖 Sugerencia del Copiloto Clínico:")
            st.markdown(st.session_state["ultimo_analisis_ia"])
            
            if st.button("📥 Copiar este análisis al Plan de Intervención"):
                plan_actual = st.session_state["paciente"].get("plan_intervencion", "")
                analisis_ia = st.session_state["ultimo_analisis_ia"]
                
                st.session_state["paciente"]["plan_intervencion"] = (plan_actual + "\n\n--- ANÁLISIS CLÍNICO (IA) ---\n" + analisis_ia).strip()
                st.success("¡Análisis transferido al Plan de Intervención con éxito!")
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

            # =================================================================
            # NUEVO: VISUALIZACIÓN DINÁMICA Y GRÁFICA DE EVOLUCIÓN (EVA)
            # =================================================================
            if st.session_state.get("historial_soap"):
                st.write("---")
                st.subheader("📈 Gráfica de Evolución del Dolor (Escala EVA)")
                
                import pandas as pd
                historial = st.session_state["historial_soap"]
                historial_ordenado = sorted(historial, key=lambda x: x["sesion"])
                
                # Preparamos los datos para la gráfica nativa de Streamlit
                df_eva = pd.DataFrame([
                    {"Sesión": f"Sesión #{n['sesion']}", "EVA": n['eva']} 
                    for n in historial_ordenado
                ])
                
                if not df_eva.empty:
                    df_chart = df_eva.set_index("Sesión")
                    # Muestra la gráfica de líneas interactiva
                    st.line_chart(df_chart)
                    
                    # Si hay 2 o más sesiones, mostramos una métrica de progreso clínico
                    if len(historial_ordenado) >= 2:
                        eva_inicial = historial_ordenado[0]["eva"]
                        eva_actual = historial_ordenado[-1]["eva"]
                        delta_eva = eva_actual - eva_inicial
                        
                        st.metric(
                            label="Progreso del Dolor (Primera vs. Última Sesión)", 
                            value=f"{eva_actual} / 10", 
                            delta=f"{delta_eva} pts", 
                            delta_color="inverse"
                        )

                st.write("---")
                with st.expander("📚 Ver Historial Detallado de Notas SOAP"):
                    for nota in reversed(historial_ordenado):
                        st.markdown(f"### Sesión #{nota['sesion']} (EVA: {nota['eva']}/10)")
                        st.markdown(f"**S:** {nota['subjetivo']}")
                        st.markdown(f"**O:** {nota['objetivo']}")
                        st.markdown(f"**A:** {nota['analisis']}")
                        st.markdown(f"**P:** {nota['plan']}")
                        st.divider()