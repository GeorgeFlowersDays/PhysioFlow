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
import pandas as pd

# ==========================================
# CONFIGURACIÓN INICIAL & BRANDING
# ==========================================
st.set_page_config(
    page_title="PhysioFlow - Expediente Clínico & Gestor DB",
    page_icon="⚡",
    layout="wide"
)

st.markdown("""
    <style>
    .main { background-color: #F8FAFC; }
    section[data-testid="stSidebar"] { background-color: #0F172A !important; }
    section[data-testid="stSidebar"] .stMarkdown, section[data-testid="stSidebar"] label, section[data-testid="stSidebar"] div { color: #F8FAFC !important; }
    .stButton>button { background-color: #0284C7; color: white; border-radius: 8px; font-weight: bold; border: none; }
    .stButton>button:hover { background-color: #0369A1; color: white; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# DICCIONARIO DE ESPECIALIDADES CLÍNICAS
# ==========================================
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
        "ejercicios": ["Isométricos de Cuádriceps (10x10 seg)", "Movilización Pasiva Asistida de ROM", "Deslizamientos Neuromusculares en Camilla", "Carga Progresiva según Fase Quirúrgica"],
        "aditamentos": ["Muletas Axilares / Codos Ingleses", "Rodillera Mecánica Graduable (Hinged Knee Brace)", "Cojín Abductor de Cadera", "Criogeltrap de Compresión"]
    }
}

# ==========================================
# SERVICIOS: SUPABASE & PDF
# ==========================================
@st.cache_resource
def get_supabase_client():
    url = st.secrets.get("SUPABASE_URL", "")
    key = st.secrets.get("SUPABASE_KEY", "")
    return create_client(url, key) if (url and key) else None

def guardar_paciente_db(paciente_dict):
    supabase = get_supabase_client()
    if not supabase:
        st.warning("⚠️ Supabase no configurado. Guardando temporalmente en sesión.")
        return False
    try:
        usr_info = st.session_state.get("user_info") or {}
        datos_guardar = {
            "terapeuta_email": usr_info.get("email", "contacto@physioflow.mx"),
            "nombre": paciente_dict.get("nombre", ""),
            "curp": paciente_dict.get("curp", ""),
            "edad": int(paciente_dict.get("edad", 0)) if paciente_dict.get("edad") else 0,
            "sexo": paciente_dict.get("sexo", ""),
            "ocupacion": paciente_dict.get("ocupacion", ""),
            "telefono": paciente_dict.get("telefono", ""),
            "especialidad": paciente_dict.get("especialidad", ""),
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
            "dermatomas": paciente_dict.get("dermatomas", ""),
            "miotomas": paciente_dict.get("miotomas", ""),
            "daniels_grupo": paciente_dict.get("daniels_grupo", ""),
            "daniels_grado": paciente_dict.get("daniels_grado", ""),
            "pruebas_funcionales": paciente_dict.get("pruebas_funcionales", ""),
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
    if not supabase: return None
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
                "dermatomas": p.get("dermatomas", ""),
                "miotomas": p.get("miotomas", ""),
                "daniels_grupo": p.get("daniels_grupo", ""),
                "daniels_grado": p.get("daniels_grado", ""),
                "pruebas_funcionales": p.get("pruebas_funcionales", ""),
                "diagnostico_sospechado": p.get("diagnostico", ""),
                "diag_funcional": p.get("diag_funcional", ""),
                "pronostico_text": p.get("pronostico_text", ""),
                "tiempo_estimado": p.get("tiempo_estimado", ""),
                "plan_intervencion": p.get("plan_intervencion", "")
            }
        return None
    except Exception as e:
        st.error(f"Error al cargar paciente: {e}")
        return None

def obtener_todos_pacientes_db():
    supabase = get_supabase_client()
    if not supabase: return []
    try:
        usr_info = st.session_state.get("user_info") or {}
        terapeuta_email = usr_info.get("email", "contacto@physioflow.mx")
        res = supabase.table("pacientes").select("*").eq("terapeuta_email", terapeuta_email).order("nombre").execute()
        return res.data if res.data else []
    except Exception as e:
        st.error(f"Error al consultar Supabase: {e}")
        return []

def generar_pdf_expediente(datos_terapeuta, datos_paciente, historia_clinica):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    story = []
    styles = getSampleStyleSheet()
    
    style_header_title = ParagraphStyle('HeaderTitle', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=18, textColor=colors.HexColor('#003366'), spaceAfter=2)
    style_header_sub = ParagraphStyle('HeaderSub', parent=styles['Normal'], fontName='Helvetica', fontSize=9, textColor=colors.HexColor('#555555'), spaceAfter=10)
    style_section = ParagraphStyle('SectionTitle', parent=styles['Heading2'], fontName='Helvetica-Bold', fontSize=12, textColor=colors.HexColor('#003366'), spaceBefore=10, spaceAfter=6)
    style_body = ParagraphStyle('BodyTextCustom', parent=styles['Normal'], fontName='Helvetica', fontSize=9.5, leading=13, textColor=colors.HexColor('#222222'))
    
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
        img_element = ""
    
    header_data = [[img_element, [Paragraph("<b>PHYSIOFLOW</b> - Fisioterapia Especializada", style_header_title), Paragraph("<b>EXPEDIENTE CLÍNICO</b><br/>NOM-004-SSA3-2012", style_header_sub)]]]
    t_header = Table(header_data, colWidths=[1.5 * inch, 5.5 * inch])
    t_header.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('LEFTPADDING', (0,0), (-1,-1), 0), ('RIGHTPADDING', (0,0), (-1,-1), 0)]))
    story.append(t_header)
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#003366'), spaceAfter=10, spaceBefore=5))
    
    data_info = [
        [Paragraph(f"<b>Fisioterapeuta:</b> {datos_terapeuta.get('nombre', 'Profesional')}", style_body), Paragraph(f"<b>Paciente:</b> {datos_paciente.get('nombre', 'N/A')}", style_body)],
        [Paragraph(f"<b>Cédula Prof:</b> {datos_terapeuta.get('cedula', 'N/A')}", style_body), Paragraph(f"<b>Edad / Sexo:</b> {datos_paciente.get('edad', 'N/A')} años | {datos_paciente.get('sexo', 'N/A')}", style_body)],
        [Paragraph(f"<b>Institución:</b> {datos_terapeuta.get('institucion', 'UNAM')}", style_body), Paragraph(f"<b>Ocupación:</b> {datos_paciente.get('ocupacion', 'N/A')}", style_body)],
        [Paragraph(f"<b>Especialidad:</b> {datos_terapeuta.get('especialidad', 'General')}", style_body), Paragraph(f"<b>Fecha:</b> {datos_paciente.get('fecha', 'N/A')}", style_body)]
    ]
    t_info = Table(data_info, colWidths=[3.5*inch, 3.5*inch])
    t_info.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F4F6F8')), ('PADDING', (0,0), (-1,-1), 6), ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E0E0E0'))]))
    story.append(t_info)
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("1. Motivo de Consulta y Anamnesis", style_section))
    story.append(Paragraph(historia_clinica.get('anamnesis', 'Sin registro.'), style_body))
    story.append(Spacer(1, 8))
    
    story.append(Paragraph("2. Exploración Física y Biomecánica", style_section))
    story.append(Paragraph(historia_clinica.get('exploracion', 'Sin registro.'), style_body))
    story.append(Spacer(1, 8))
    
    patron_resp = historia_clinica.get("patron_respiratorio", "No evaluado")
    estres_eva = historia_clinica.get("nivel_estres_percibido", "N/A")
    story.append(Paragraph(f"<b>Patrón Respiratorio:</b> {patron_resp}", style_body))
    story.append(Paragraph(f"<b>Carga Alostática / Estrés:</b> {estres_eva}/10", style_body))
    story.append(Spacer(1, 8))
    
    story.append(Paragraph("3. Diagnóstico Funcional, Pronóstico & Plan", style_section))
    data_plan = [
        [Paragraph("<b>Diagnóstico Médico:</b>", style_body), Paragraph(historia_clinica.get('diagnostico', 'N/A'), style_body)],
        [Paragraph("<b>Diagnóstico CIF:</b>", style_body), Paragraph(historia_clinica.get('diagnostico_funcional', 'N/A'), style_body)],
        [Paragraph("<b>Pronóstico:</b>", style_body), Paragraph(historia_clinica.get('pronostico', 'N/A'), style_body)],
        [Paragraph("<b>Plan de Intervención:</b>", style_body), Paragraph(historia_clinica.get('plan', 'N/A'), style_body)]
    ]
    t_plan = Table(data_plan, colWidths=[2.2*inch, 4.8*inch])
    t_plan.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP'), ('PADDING', (0,0), (-1,-1), 4), ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E0E0E0')), ('BACKGROUND', (0,0), (0,-1), colors.HexColor('#F8F9FA'))]))
    story.append(t_plan)
    story.append(Spacer(1, 20))
    
    data_firma = [
        ["__________________________________"],
        [Paragraph(f"<b>{datos_terapeuta.get('nombre', 'Firma')}</b>", ParagraphStyle('FirmaStyle', parent=style_body, alignment=1))],
        [Paragraph(f"Cédula: {datos_terapeuta.get('cedula', 'N/A')}", ParagraphStyle('FirmaStyle2', parent=style_body, alignment=1))]
    ]
    t_firma = Table(data_firma, colWidths=[7*inch])
    t_firma.setStyle(TableStyle([('ALIGN', (0,0), (-1,-1), 'CENTER')]))
    story.append(t_firma)
    
    doc.build(story)
    buffer.seek(0)
    return buffer

# ==========================================
# MÓDULO AUXILIAR: BIBLIOTECA CLÍNICA
# ==========================================
def mostrar_biblioteca_clinica():
    st.subheader("📚 Biblioteca Clínica & Guía de Pruebas")
    st.caption("Consulta rápida de pruebas ortopédicas y dosificación respaldada por evidencia.")

    with st.expander("🤖 Asistente de Consulta Rápida (IA)"):
        consulta_biblio = st.text_input("¿Qué prueba, test o concepto deseas consultar?", placeholder="Ej. Test de Slump...")
        if st.button("Consultar con IA (Gemini)", use_container_width=True) and consulta_biblio:
            try:
                api_key = st.secrets["GEMINI_API_KEY"]
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent?key={api_key}"
                prompt_biblio = f"Actúa como un experto en fisioterapia basada en evidencia. Explica de forma breve y estructurada (en viñetas) la consulta: '{consulta_biblio}'."
                response = requests.post(url, headers={"Content-Type": "application/json"}, data=json.dumps({"contents": [{"parts": [{"text": prompt_biblio}]}]}))
                if response.status_code == 200:
                    st.info(response.json()["candidates"][0]["content"]["parts"][0]["text"])
                else:
                    st.error("Error al consultar la IA.")
            except Exception as e:
                st.error(f"Error: {e}")

    st.write("---")
    categoria = st.selectbox("Filtrar por Región:", ["Columna Lumbar & Pelvis", "Extremidad Inferior", "Extremidad Superior"])
    if categoria == "Columna Lumbar & Pelvis":
        col1, col2 = st.columns(2)
        with col1:
            with st.container(border=True):
                st.markdown("### 🔍 Test de Slump")
                st.markdown("* **Posición:** Sentado al borde de la camilla.\n* **Positivo:** Reproducción de sintomatología radicular.")
        with col2:
            with st.container(border=True):
                st.markdown("### 🔍 Test de Lasègue (SLR)")
                st.markdown("* **Posición:** Decúbito supino.\n* **Positivo:** Dolor irradiado entre 30° y 70°.")

# ==========================================
# INICIALIZACIÓN DE ESTADOS DE SESIÓN
# ==========================================
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = (st.query_params.get("auth") == "true")
if "user_info" not in st.session_state:
    st.session_state["user_info"] = {
        "email": st.query_params.get("email", ""),
        "nombre": st.query_params.get("nombre", "Jorge Antonio Flores Díaz"),
        "cedula": st.query_params.get("cedula", ""),
        "institucion": st.query_params.get("institucion", "UNAM")
    }
if "terapeuta" not in st.session_state:
    st.session_state["terapeuta"] = {"nombre": "Jorge Flores", "cedula": "", "institucion": "UNAM"}
if "paciente" not in st.session_state:
    st.session_state["paciente"] = {
        "nombre": "", "edad": 27, "sexo": "Masculino", "curp": "", "ocupacion": "",
        "telefono": "", "especialidad": "Músicos & Artes Escénicas", "eva_dolor": 5,
        "tipo_dolor": "Miofascial", "diagnostico_sospechado": "", "plan_intervencion": ""
    }

# Autenticación por URL
if st.query_params.get("auth") == "true":
    st.session_state["authenticated"] = True

# ==========================================
# PANTALLA DE LOGIN / REGISTRO
# ==========================================
if not st.session_state["authenticated"]:
    st.title("⚡ PhysioFlow Pro")
    st.caption("Plataforma Clínica Integral & Copiloto Fisioterapéutico")
    tab_login, tab_registro = st.tabs(["🔑 Iniciar Sesión", "📝 Registrarse"])
    
    with tab_login:
        email = st.text_input("Correo Electrónico:", key="login_email")
        password = st.text_input("Contraseña:", type="password", key="login_pass")
        if st.button("Ingresar", use_container_width=True):
            if email and password:
                st.session_state["authenticated"] = True
                st.query_params["auth"] = "true"
                st.query_params["email"] = email
                st.success("¡Bienvenido!")
                st.rerun()
            else:
                st.error("Ingresa correo y contraseña.")
                
    with tab_registro:
        reg_nombre = st.text_input("Nombre Completo:")
        reg_cedula = st.text_input("Cédula Profesional:")
        if st.button("Registrar Cuenta", use_container_width=True) and reg_nombre and reg_cedula:
            st.session_state["authenticated"] = True
            st.query_params["auth"] = "true"
            st.query_params["nombre"] = reg_nombre
            st.query_params["cedula"] = reg_cedula
            st.rerun()
    st.stop()

# ==========================================
# BARRA LATERAL & NAVEGACIÓN
# ==========================================
logo_path = next((f for f in ["logo_blanco.png", "Logo_blanco.png", "logo.png", "Logo.png"] if os.path.exists(f)), None)
if logo_path: st.sidebar.image(logo_path, use_container_width=True)
else: st.sidebar.title("⚡ PhysioFlow")

st.sidebar.subheader("👤 Fisioterapeuta Autenticado")
titulo_sel = st.sidebar.selectbox("Grado:", ["LFT", "LTF", "Mtro.", "Mtra.", "Dr.", "Dra.", "Lic."])
st.session_state["terapeuta"]["nombre"] = f"{titulo_sel}. {st.session_state['user_info'].get('nombre', 'Jorge Flores')}"
st.sidebar.markdown(f"**Profesional:** {st.session_state['terapeuta']['nombre']}")
st.sidebar.write("---")

especialidad_sel = st.sidebar.selectbox("Especialidad Clínica Activa:", list(DATOS_ESPECIALIDADES.keys()), key="especialidad_activa")
st.session_state["paciente"]["especialidad"] = especialidad_sel
st.sidebar.write("---")

# Resumen de Paciente Activo
st.sidebar.subheader("📋 Paciente en Atención")
p_activo = st.session_state.get("paciente", {})
if p_activo.get("nombre"):
    st.sidebar.markdown(f"**Nombre:** {p_activo.get('nombre')}")
    eva_v = p_activo.get("eva_dolor", 0)
    if eva_v >= 8: st.sidebar.error(f"🚨 EVA: {eva_v}/10 (Severo)")
    elif eva_v >= 5: st.sidebar.warning(f"⚠️ EVA: {eva_v}/10 (Moderado)")
    else: st.sidebar.success(f"🟢 EVA: {eva_v}/10 (Estable)")
else:
    st.sidebar.info("ℹ️ Ningún paciente seleccionado.")

st.sidebar.markdown("### 🧭 Centros de Mando")
opciones_fases = [
    "🗂️ Recepción & Historia Clínica (NOM-004)",
    "🔍 Exploración & Localización 3D del Dolor",
    "📐 Biomecánica & Análisis de Gestos",
    "📋 Prescripción & SOAP",
    "📚 Biblioteca Clínica & Guía"
]
centro_mando = st.sidebar.radio("Selecciona Fase:", opciones_fases)
st.sidebar.write("---")

modulo_config = st.sidebar.checkbox("⚙️ Configuración de Cuenta", value=False)

# Botón PDF global en barra lateral
if p_activo.get("nombre"):
    if st.sidebar.button("📥 Generar Expediente PDF", use_container_width=True):
        buffer = generar_pdf_expediente(st.session_state["terapeuta"], p_activo, {
            "anamnesis": p_activo.get("pa", ""),
            "exploracion": f"Dermatomas: {p_activo.get('dermatomas', 'N/A')}",
            "diagnostico": p_activo.get("diagnostico_sospechado", ""),
            "diagnostico_funcional": p_activo.get("diag_funcional", ""),
            "pronostico": p_activo.get("pronostico_text", ""),
            "plan": p_activo.get("plan_intervencion", "")
        })
        st.sidebar.download_button("Descargar Archivo PDF", buffer, file_name=f"Expediente_{p_activo['nombre']}.pdf", mime="application/pdf")

# ==========================================
# CONTROLADOR PRINCIPAL DE VISTAS (FASES)
# ==========================================
if modulo_config:
    st.header("⚙️ Configuración del Perfil")
    nuevo_nombre = st.text_input("Nombre Completo:", value=st.session_state["user_info"].get("nombre", ""))
    if st.button("Guardar Cambios"):
        st.session_state["user_info"]["nombre"] = nuevo_nombre
        st.success("¡Actualizado con éxito!")
        st.rerun()
else:
    if centro_mando == "🗂️ Recepción & Historia Clínica (NOM-004)":
        st.header("📁 Fase 1: Recepción, Base de Datos & Historia Clínica")
        tab_db, tab_hc1, tab_hc2, tab_hc3, tab_hc4 = st.tabs(["📂 Gestor DB", "1️⃣ Ficha", "2️⃣ Anamnesis", "3️⃣ Neurología", "4️⃣ CIF"])
        
        with tab_db:
            if st.button("💾 Guardar Paciente en DB"):
                if guardar_paciente_db(st.session_state["paciente"]):
                    st.success("Paciente guardado con éxito.")
            registros = obtener_todos_pacientes_db()
            if registros:
                sel = st.selectbox("Cargar existente:", [f"{p['nombre']} ({p['curp']})" for p in registros])
                if st.button("Cargar Expediente"):
                    curp_sel = sel.split("(")[1].split(")")[0]
                    cargado = cargar_paciente_db(curp_sel)
                    if cargado:
                        st.session_state["paciente"].update(cargado)
                        st.success("Expediente cargado.")
                        st.rerun()

        with tab_hc1:
            st.session_state["paciente"]["nombre"] = st.text_input("Nombre:", value=p_activo.get("nombre", ""))
            st.session_state["paciente"]["edad"] = st.number_input("Edad:", value=int(p_activo.get("edad", 0)))
            st.session_state["paciente"]["curp"] = st.text_input("CURP / ID:", value=p_activo.get("curp", ""))
            st.session_state["paciente"]["ocupacion"] = st.text_input("Ocupación:", value=p_activo.get("ocupacion", ""))

        with tab_hc2:
            st.session_state["paciente"]["pa"] = st.text_area("Padecimiento Actual:", value=p_activo.get("pa", ""))
            st.session_state["paciente"]["eva_dolor"] = st.slider("EVA Dolor:", 0, 10, int(p_activo.get("eva_dolor", 0)))

        with tab_hc3:
            st.session_state["paciente"]["dermatomas"] = st.text_input("Dermatomas:", value=p_activo.get("dermatomas", ""))

        with tab_hc4:
            st.session_state["paciente"]["diagnostico_sospechado"] = st.text_input("Diagnóstico Médico:", value=p_activo.get("diagnostico_sospechado", ""))
            st.session_state["paciente"]["plan_intervencion"] = st.text_area("Plan de Intervención:", value=p_activo.get("plan_intervencion", ""))

    elif centro_mando == "🔍 Exploración & Localización 3D del Dolor":
        st.header("🦴 Fase 2: Exploración Física & 3D")
        col1, col2 = st.columns(2)
        with col1:
            st.info("Visor Anatómico Interactivo Activo.")
        with col2:
            esp_info = DATOS_ESPECIALIDADES.get(especialidad_sel, {})
            st.multiselect("Pruebas sugeridas por evidencia:", esp_info.get("pruebas", []))

    elif centro_mando == "📐 Biomecánica & Análisis de Gestos":
        st.header("📐 Fase 3: Biomecánica y Movimiento")
        st.file_uploader("Cargar video o imagen de análisis:", type=["mp4", "jpg", "png"])

    elif centro_mando == "📋 Prescripción & SOAP":
        st.header("📋 Fase 4: Prescripción y Notas de Evolución SOAP")
        st.text_area("Plan actual:", value=p_activo.get("plan_intervencion", ""))

    elif centro_mando == "📚 Biblioteca Clínica & Guía":
        mostrar_biblioteca_clinica()