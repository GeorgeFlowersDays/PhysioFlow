import io
import os
import math
import sqlite3
import requests
import json
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
            st.subheader("Exploración Neurológica, Perfil Somático & Pruebas")
            
            # --- 1. GUÍA DE REFERENCIA RÁPIDA ---
            with st.expander("🗺️ Guía de Referencia Rápida: Dermatomas & Miotomas"):
                st.markdown("""
                * **Extremidad Superior:** 
                  * **C5:** Cara lateral del hombro / Bíceps (Flexión de codo).
                  * **C6:** Cara lateral del antebrazo y pulgar / Extensores de muñeca.
                  * **C7:** Dedo medio / Tríceps y flexores de dedos.
                  * **C8:** Dedo meñique / Flexores de dedos.
                  * **T1:** Cara medial del brazo / Interóseos.
                * **Extremidad Inferior:** 
                  * **L2:** Muslo anterior / Flexores de cadera.
                  * **L3:** Rodilla y cara medial de pierna / Extensores de rodilla.
                  * **L4:** Maléolo medial / Tibial anterior (Dorsiflexión).
                  * **L5:** Dorso del pie y dedo gordo / Extensor largo del hallux.
                  * **S1:** Planta y borde lateral del pie / Flexores plantares.
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
            
            # --- 2. PERFIL SOMÁTICO ---
            with st.expander("🧠 Perfil Somático, Patrón Respiratorio & Regulación del SNA"):
                patrones_resp = ["Diafragmático / Abdominal (Funcional)", "Costal Superior / Accesorio (Disfuncional)", "Paradójico / Mixto"]
                idx_pr = patrones_resp.index(st.session_state["paciente"].get("patron_respiratorio", patrones_resp[0])) if st.session_state["paciente"].get("patron_respiratorio") in patrones_resp else 0
                st.session_state["paciente"]["patron_respiratorio"] = st.selectbox("Patrón Respiratorio Dominante:", patrones_resp, index=idx_pr)
                st.caption("💡 *Nota Clínica:* Un patrón costal superior constante sobreactiva los músculos accesorios del cuello.")
                
                st.session_state["paciente"]["nivel_estres_percibido"] = st.slider("Carga Alostática / Estrés Percibido (0-10):", 0, 10, value=int(st.session_state["paciente"].get("nivel_estres_percibido", 3)))
                st.session_state["paciente"]["hallazgos_psicosomaticos"] = st.multiselect("Manifestaciones Somáticas & Cognitivas:", ["Hipertonía Defensiva", "Bruxismo", "Kinesiofobia", "Catastrofización", "Hipervigilancia", "Fatiga Crónica"], default=st.session_state["paciente"].get("hallazgos_psicosomaticos", []))

            st.write("---")
            
            # --- 3. BATERÍA DE PRUEBAS FUNCIONALES CON IA (AHORA SÍ EN SU LUGAR) ---
            st.subheader("🔍 Batería de Pruebas Funcionales & Diagnóstico Diferencial")
            st.caption("Selección de pruebas ortopédicas y funcionales guiadas por evidencia clínica.")

            col_pf1, col_pf2 = st.columns([0.6, 0.4])
            with col_pf1:
                st.write("Resultados y Pruebas Aplicadas")
            with col_pf2:
                if st.button("Sugerir Pruebas con Evidencia (Gemini)", use_container_width=True):
                    # Recopilamos los datos clave del paciente en tiempo real
                    pa = st.session_state["paciente"].get("pa", "No especificado")
                    eva = st.session_state["paciente"].get("eva_dolor", 0)
                    tipo_dolor = st.session_state["paciente"].get("tipo_dolor", "No especificado")
                    agravantes = st.session_state["paciente"].get("factores_agravantes", "Ninguno")
                    mitigantes = st.session_state["paciente"].get("factores_mitigantes", "Ninguno")
                    ocupacion = st.session_state["paciente"].get("ocupacion", "No especificada")
                    especialidad = st.session_state["paciente"].get("especialidad_activa", "Fisioterapia General")

                    # Construimos un prompt clínico rico en contexto
                    prompt_pf = (
                        f"Actúa como un fisioterapeuta experto, investigador y especialista en {especialidad}.\n"
                        f"Analiza el siguiente cuadro clínico del paciente (Ocupación/Instrumento/Deporte: {ocupacion}):\n"
                        f"- Padecimiento Actual (PA): {pa}\n"
                        f"- Escala EVA: {eva}/10 | Tipo de dolor: {tipo_dolor}\n"
                        f"- Factores agravantes: {agravantes}\n"
                        f"- Factores mitigantes: {mitigantes}\n\n"
                        f"Basándote estrictamente en estos datos de anamnesis y semiología, propón una batería de 3 o 4 pruebas ortopédicas o funcionales altamente específicas y basadas en evidencia para este caso. "
                        f"Formato requerido: Nombre de la prueba y qué busca confirmar o descartar, redactado de forma muy breve y directa en viñetas."
                    )
                    try:
                        api_key = st.secrets["GEMINI_API_KEY"]
                        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent?key={api_key}"
                        payload = {"contents": [{"parts": [{"text": prompt_pf}]}]}
                        response = requests.post(url, headers={"Content-Type": "application/json"}, data=json.dumps(payload))
                        if response.status_code == 200:
                            texto_generado = response.json()["candidates"][0]["content"]["parts"][0]["text"]
                            st.session_state["paciente"]["pruebas_funcionales"] = texto_generado
                            st.success("¡Pruebas sugeridas con éxito!")
                            st.rerun()
                        else:
                            st.error("Error al conectar con la API de IA.")
                    except Exception as e:
                        st.error(f"Error: {e}")

            st.session_state["paciente"]["pruebas_funcionales"] = st.text_area(
                "Detalle de Pruebas Aplicadas y Hallazgos:",
                value=st.session_state["paciente"].get("pruebas_funcionales", ""),
                placeholder="Haz clic en 'Sugerir Pruebas con Evidencia' o redacta los hallazgos..."
            )
        with tab_hc4:
            st.subheader("Diagnóstico Nosológico, CIF & Plan de Intervención")
            st.caption("Evaluación clínica oficial, clasificación funcional y dosificación terapéutica basada en evidencia.")

            # 1. Diagnóstico Nosológico / Médico con Asistencia de IA Inteligente
            col_dx1, col_dx2 = st.columns([0.7, 0.3])
            with col_dx1:
                st.markdown("**Diagnóstico Nosológico / Médico (Presuntivo):**")
            with col_dx2:
                if st.button("Sugerir Diagnóstico con IA (Gemini)", use_container_width=True):
                    # Recopilamos el contexto completo del paciente
                    pa = st.session_state["paciente"].get("pa", "No especificado")
                    eva = st.session_state["paciente"].get("eva_dolor", 0)
                    tipo_dolor = st.session_state["paciente"].get("tipo_dolor", "No especificado")
                    agravantes = st.session_state["paciente"].get("factores_agravantes", "Ninguno")
                    mitigantes = st.session_state["paciente"].get("factores_mitigantes", "Ninguno")
                    pruebas = st.session_state["paciente"].get("pruebas_funcionales", "No especificadas")
                    ocupacion = st.session_state["paciente"].get("ocupacion", "No especificada")
                    especialidad = st.session_state["paciente"].get("especialidad_activa", "Fisioterapia General")

                    prompt_nosologico = (
                        f"Actúa como un médico especialista en rehabilitación y fisioterapeuta experto en {especialidad}.\n"
                        f"Analiza el siguiente cuadro clínico de un paciente (Ocupación/Instrumento/Deporte: {ocupacion}):\n"
                        f"- Padecimiento Actual (PA): {pa} (EVA: {eva}/10 | Tipo de dolor: {tipo_dolor})\n"
                        f"- Factores Agravantes: {agravantes} | Mitigantes: {mitigantes}\n"
                        f"- Hallazgos en Pruebas Funcionales: {pruebas}\n\n"
                        f"Propón un diagnóstico nosológico o médico presuntivo altamente certero y profesional para este caso (sé muy directo, máximo 1 o 2 opciones clínicas claras en una sola línea)."
                    )
                    try:
                        api_key = st.secrets["GEMINI_API_KEY"]
                        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent?key={api_key}"
                        response = requests.post(url, headers={"Content-Type": "application/json"}, data=json.dumps({"contents": [{"parts": [{"text": prompt_nosologico}]}]}))
                        if response.status_code == 200:
                            texto_dx = response.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
                            st.session_state["paciente"]["diagnostico_sospechado"] = texto_dx
                            st.success("¡Diagnóstico nosológico sugerido con éxito!")
                            st.rerun()
                        else:
                            st.error("Error al conectar con la API de IA.")
                    except Exception as e:
                        st.error(f"Error: {e}")

            st.session_state["paciente"]["diagnostico_sospechado"] = st.text_input(
                "Detalle del Diagnóstico Nosológico:",
                value=st.session_state["paciente"].get("diagnostico_sospechado", ""),
                placeholder="Haz clic en 'Sugerir Diagnóstico con IA' o escribe el diagnóstico..."
            )

            st.write("---")

            # 2. Diagnóstico Funcional (CIF) con IA Inteligente
            with st.expander("📌 Códigos CIF Frecuentes de Referencia"):
                st.markdown("""
                * **b28015** - Dolor en región lumbar / columna.
                * **b7100** - Movilidad articular (Restricción de rango).
                * **d4103** - Inclinarse o agacharse.
                * **d4300** - Levantar objetos pesados.
                * **d4500** - Caminar distancias cortas.
                """)

            col_cif1, col_cif2 = st.columns([0.7, 0.3])
            with col_cif1:
                st.markdown("**Diagnóstico Funcional (CIF):**")
            with col_cif2:
                if st.button("Sugerir CIF con IA (Gemini)", use_container_width=True):
                    dx_medico = st.session_state["paciente"].get("diagnostico_sospechado", "No especificado")
                    pa = st.session_state["paciente"].get("pa", "No especificado")
                    eva = st.session_state["paciente"].get("eva_dolor", 0)
                    pruebas = st.session_state["paciente"].get("pruebas_funcionales", "No especificadas")
                    especialidad = st.session_state["paciente"].get("especialidad_activa", "Fisioterapia General")

                    prompt_cif = (
                        f"Actúa como un experto en fisioterapia y clasificación CIF, especializado en {especialidad}.\n"
                        f"Analiza el caso completo del paciente:\n"
                        f"- Diagnóstico Médico/Nosológico: {dx_medico}\n"
                        f"- Padecimiento Actual (PA): {pa} (EVA: {eva}/10)\n"
                        f"- Hallazgos en Pruebas Funcionales: {pruebas}\n\n"
                        f"Redacta un diagnóstico funcional CIF muy breve, estructurado y directo (máximo 4 líneas en viñetas cortas) "
                        f"que relacione las deficiencias corporales y las limitaciones en actividades específicas de este paciente."
                    )
                    try:
                        api_key = st.secrets["GEMINI_API_KEY"]
                        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent?key={api_key}"
                        response = requests.post(url, headers={"Content-Type": "application/json"}, data=json.dumps({"contents": [{"parts": [{"text": prompt_cif}]}]}))
                        if response.status_code == 200:
                            texto_cif = response.json()["candidates"][0]["content"]["parts"][0]["text"]
                            st.session_state["paciente"]["diag_funcional"] = texto_cif
                            st.success("¡Diagnóstico CIF generado con éxito!")
                            st.rerun()
                        else:
                            st.error("Error al conectar con la API de IA.")
                    except Exception as e:
                        st.error(f"Error: {e}")

            st.session_state["paciente"]["diag_funcional"] = st.text_area(
                "Descripción del Diagnóstico Funcional (CIF):",
                value=st.session_state["paciente"].get("diag_funcional", ""),
                placeholder="Haz clic en 'Sugerir CIF con IA' o redacta los componentes funcionales..."
            )

            st.write("---")

            # 3. Pronóstico y Tiempos
            col_d1, col_d2 = st.columns(2)
            with col_d1:
                pronosticos = ["Favorable para la función (Corto plazo)", "Favorable con reservas", "Pronóstico reservado a evolución"]
                idx_p = pronosticos.index(st.session_state["paciente"].get("pronostico_text", pronosticos[0])) if st.session_state["paciente"].get("pronostico_text") in pronosticos else 0
                st.session_state["paciente"]["pronostico_text"] = st.selectbox("Pronóstico Fisioterapéutico:", pronosticos, index=idx_p)
            with col_d2:
                tiempos_rec = ["1 a 3 semanas (Fase Aguda)", "4 a 8 semanas (Fase Subaguda)", "3 a 6 meses (Fase Crónica/Reacondicionamiento)"]
                idx_t = tiempos_rec.index(st.session_state["paciente"].get("tiempo_estimado", tiempos_rec[0])) if st.session_state["paciente"].get("tiempo_estimado") in tiempos_rec else 0
                st.session_state["paciente"]["tiempo_estimado"] = st.selectbox("Tiempo Estimado de Recuperación:", tiempos_rec, index=idx_t)

            st.write("---")

            # 4. Plan de Intervención con IA Contextualizada
            col_pl1, col_pl2 = st.columns([0.6, 0.4])
            with col_pl1:
                st.subheader("Plan de Intervención & Dosificación de Carga")
            with col_pl2:
                if st.button("Sugerir Plan de Intervención (Gemini)", use_container_width=True):
                    dx_medico = st.session_state["paciente"].get("diagnostico_sospechado", "No especificado")
                    dx_cif = st.session_state["paciente"].get("diag_funcional", "No especificado")
                    eva = st.session_state["paciente"].get("eva_dolor", 0)
                    ocupacion = st.session_state["paciente"].get("ocupacion", "No especificada")
                    esp = st.session_state["paciente"].get("especialidad_activa", "Fisioterapia General")

                    prompt_clinico = (
                        f"Actúa como un experto en fisioterapia basada en evidencia y especialista en {esp}.\n"
                        f"Diseña una propuesta de plan de intervención y dosificación de carga altamente personalizada para este paciente:\n"
                        f"- Ocupación/Instrumento/Deporte: {ocupacion} | EVA: {eva}/10\n"
                        f"- Diagnóstico Médico: {dx_medico}\n"
                        f"- Diagnóstico Funcional (CIF): {dx_cif}\n\n"
                        f"Limítate estrictamente a viñetas cortas con los objetivos terapéuticos clave, modalidad principal, terapia manual y pautas de ejercicio adaptadas a su contexto."
                    )
                    try:
                        api_key = st.secrets["GEMINI_API_KEY"]
                        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent?key={api_key}"
                        response = requests.post(url, headers={"Content-Type": "application/json"}, data=json.dumps({"contents": [{"parts": [{"text": prompt_clinico}]}]}))
                        if response.status_code == 200:
                            texto_plan = response.json()["candidates"][0]["content"]["parts"][0]["text"]
                            st.session_state["paciente"]["plan_intervencion"] = texto_plan
                            st.success("¡Plan de intervención generado con éxito!")
                            st.rerun()
                        else:
                            st.error("Error al conectar con la API de IA.")
                    except Exception as e:
                        st.error(f"Error: {e}")

            st.session_state["paciente"]["plan_intervencion"] = st.text_area(
                "Objetivos Terapéuticos y Estrategia (Ejercicios, Terapia Manual, Dosificación):",
                value=st.session_state["paciente"].get("plan_intervencion", ""),
                height=150
            )