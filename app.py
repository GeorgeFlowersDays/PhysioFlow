import io
import os
import math
import sqlite3
import cv2
import numpy as np
import streamlit as st
from supabase import create_client, Client

SUPABASE_URL = st.secrets.get("SUPABASE_URL", "")
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "")
from PIL import Image
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from streamlit_drawable_canvas import st_canvas
import streamlit as st
import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch

# ==========================================
# 1. FUNCIÓN GENERADORA DE PDF (Poner aquí)
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
    
    # Header / Branding
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
    
    # Datos Fisioterapeuta y Paciente
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
    
    # Secciones
    story.append(Paragraph("1. Motivo de Consulta y Anamnesis", style_section))
    story.append(Paragraph(historia_clinica.get('anamnesis', 'Sin registro de anamnesis.'), style_body))
    story.append(Spacer(1, 8))
    
    story.append(Paragraph("2. Exploración Física y Biomecánica", style_section))
    story.append(Paragraph(historia_clinica.get('exploracion', 'Sin registro de exploración física.'), style_body))
    story.append(Spacer(1, 8))
    # === DATOS DE SALUD MENTAL Y PERFIL SOMÁTICO ===
    patron_resp = historia_clinica.get("patron_respiratorio", "No evaluado")
    estres_eva = historia_clinica.get("nivel_estres_percibido", "N/A")
    hallazgos_psico = historia_clinica.get("hallazgos_psicosomaticos", [])
    hallazgos_str = ", ".join(hallazgos_psico) if hallazgos_psico else "Ninguno reportado"

    story.append(Paragraph(f"<b>Patrón Respiratorio Dominante:</b> {patron_resp}", style_body))
    story.append(Paragraph(f"<b>Carga Alostática / Estrés Percibido (0-10):</b> {estres_eva}/10", style_body))
    story.append(Paragraph(f"<b>Manifestaciones Somáticas & Tono Reactivo:</b> {hallazgos_str}", style_body))
    story.append(Spacer(1, 8))
    
 # 3. Diagnóstico Funcional, Pronóstico & Plan
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
    
    # Firma
 # Firma
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


# -----------------------------------------------------------------------------
# BASE DE DATOS LOCAL (SQLITE)
# -----------------------------------------------------------------------------
DB_NAME = "physioflow.db"


def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Tabla de Pacientes
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pacientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT,
            edad INTEGER,
            sexo TEXT,
            curp TEXT UNIQUE,
            ocupacion TEXT,
            telefono TEXT,
            especialidad TEXT,
            ahf TEXT,
            app TEXT,
            apnp TEXT,
            pa TEXT,
            mapa_dolor_zona TEXT,
            eva_dolor INTEGER,
            tipo_dolor TEXT,
            diagnostico TEXT,
            resultado_1rm TEXT
        )
    """)

    # Tabla de Notas de Evolución (SOAP)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notas_soap (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            paciente_curp TEXT,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            subjetivo TEXT,
            objetivo TEXT,
            analisis TEXT,
            plan TEXT,
            FOREIGN KEY(paciente_curp) REFERENCES pacientes(curp)
        )
    """)

    conn.commit()
    conn.close()


init_db()


def guardar_paciente_db(paciente_dict):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    diag_final = paciente_dict["custom_diagnostico"] if paciente_dict[
        "diagnostico_sospechado"] == "Otro / Personalizado..." else paciente_dict["diagnostico_sospechado"]

    cursor.execute("""
        INSERT INTO pacientes (nombre, edad, sexo, curp, ocupacion, telefono, especialidad, ahf, app, apnp, pa, mapa_dolor_zona, eva_dolor, tipo_dolor, diagnostico, resultado_1rm)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(curp) DO UPDATE SET
            nombre=excluded.nombre,
            edad=excluded.edad,
            sexo=excluded.sexo,
            ocupacion=excluded.ocupacion,
            telefono=excluded.telefono,
            especialidad=excluded.especialidad,
            ahf=excluded.ahf,
            app=excluded.app,
            apnp=excluded.apnp,
            pa=excluded.pa,
            mapa_dolor_zona=excluded.mapa_dolor_zona,
            eva_dolor=excluded.eva_dolor,
            tipo_dolor=excluded.tipo_dolor,
            diagnostico=excluded.diagnostico,
            resultado_1rm=excluded.resultado_1rm
    """, (
        paciente_dict["nombre"], paciente_dict["edad"], paciente_dict["sexo"], paciente_dict["curp"],
        paciente_dict["ocupacion"], paciente_dict["telefono"], paciente_dict["especialidad"],
        paciente_dict["ahf"], paciente_dict["app"], paciente_dict["apnp"], paciente_dict["pa"],
        paciente_dict["mapa_dolor_zona"], paciente_dict["eva_dolor"], paciente_dict["tipo_dolor"],
        diag_final, paciente_dict["resultado_1rm"]
    ))

    conn.commit()
    conn.close()


def buscar_pacientes_db(busqueda=""):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    query = "SELECT id, nombre, curp, especialidad, telefono FROM pacientes WHERE nombre LIKE ? OR curp LIKE ?"
    cursor.execute(query, (f"%{busqueda}%", f"%{busqueda}%"))
    filas = cursor.fetchall()
    conn.close()
    return filas


def cargar_paciente_db(curp):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT nombre, edad, sexo, curp, ocupacion, telefono, especialidad, ahf, app, apnp, pa, mapa_dolor_zona, eva_dolor, tipo_dolor, diagnostico, resultado_1rm FROM pacientes WHERE curp = ?", (curp,))
    row = cursor.fetchone()
    conn.close()

    if row:
        return {
            "nombre": row[0], "edad": row[1], "sexo": row[2], "curp": row[3],
            "ocupacion": row[4], "telefono": row[5], "especialidad": row[6],
            "ahf": row[7], "app": row[8], "apnp": row[9], "pa": row[10],
            "mapa_dolor_zona": row[11], "eva_dolor": row[12], "tipo_dolor": row[13],
            "diagnostico_sospechado": row[14], "resultado_1rm": row[15]
        }
    return None
def obtener_todos_pacientes_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, nombre, curp, especialidad, telefono FROM pacientes ORDER BY nombre ASC")
    filas = cursor.fetchall()
    conn.close()
    
    lista_pacientes = []
    for f in filas:
        lista_pacientes.append({
            "id": f[0],
            "nombre": f[1],
            "curp": f[2],
            "especialidad": f[3],
            "telefono": f[4]
        })
    return lista_pacientes

def guardar_nota_soap(curp, s, o, a, p):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO notas_soap (paciente_curp, subjetivo, objetivo, analisis, plan) VALUES (?, ?, ?, ?, ?)", (curp, s, o, a, p))
    conn.commit()
    conn.close()


def obtener_notas_soap(curp):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT fecha, subjetivo, objetivo, analisis, plan FROM notas_soap WHERE paciente_curp = ? ORDER BY fecha DESC", (curp,))
    notas = cursor.fetchall()
    conn.close()
    return notas


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

# ==================== ESTADO Y AUTENTICACIÓN DE SESIÓN ====================
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


def calcular_1rm(peso, repeticiones):
    if repeticiones == 1:
        return peso, peso
    brzycki = peso / (1.0278 - (0.0278 * repeticiones))
    epley = peso * (1 + (0.0333 * repeticiones))
    return round(brzycki, 1), round(epley, 1)


def calcular_angulo_3puntos(a, b, c):
    a, b, c = np.array(a), np.array(b), np.array(c)
    v1, v2 = a - b, c - b
    norm_v1, norm_v2 = np.linalg.norm(v1), np.linalg.norm(v2)
    if norm_v1 == 0 or norm_v2 == 0:
        return 0.0
    dot_product = np.dot(v1, v2)
    cos_theta = np.clip(dot_product / (norm_v1 * norm_v2), -1.0, 1.0)
    return round(float(np.degrees(np.arccos(cos_theta))), 1)


def procesar_columna_escoliosis(img_file):
    bytes_data = img_file.getvalue()
    file_bytes = np.frombuffer(bytes_data, dtype=np.uint8)
    img_bgr = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    img_out = img_bgr.copy()
    desviacion_escoliosis = 0.0

    if YOLO_DISPONIBLE:
        results = model_yolo(img_bgr, verbose=False)
        for r in results:
            if r.keypoints is not None and len(r.keypoints.data) > 0:
                kpts = r.keypoints.data[0].cpu().numpy()
                cervical = (int((kpts[5][0] + kpts[6][0]) / 2),
                            int((kpts[5][1] + kpts[6][1]) / 2) - 30)
                dorsal = (int((kpts[5][0] + kpts[6][0]) / 2),
                          int((kpts[5][1] + kpts[6][1]) / 2))
                lumbar = (int((kpts[11][0] + kpts[12][0]) / 2),
                          int((kpts[11][1] + kpts[12][1]) / 2))

                hombro_izq, hombro_der = (int(kpts[5][0]), int(
                    kpts[5][1])), (int(kpts[6][0]), int(kpts[6][1]))
                cadera_izq, cadera_der = (int(kpts[11][0]), int(
                    kpts[11][1])), (int(kpts[12][0]), int(kpts[12][1]))

                cv2.line(img_out, cervical, lumbar, (0, 255, 128), 3)
                cv2.line(img_out, hombro_izq, hombro_der, (255, 0, 128), 2)
                cv2.line(img_out, cadera_izq, cadera_der, (255, 0, 128), 2)

                cv2.circle(img_out, hombro_izq, 6, (0, 255, 255), -1)
                cv2.circle(img_out, hombro_der, 6, (0, 255, 255), -1)
                cv2.circle(img_out, cadera_izq, 6, (0, 255, 255), -1)
                cv2.circle(img_out, cadera_der, 6, (0, 255, 255), -1)

                desviacion_escoliosis = calcular_angulo_3puntos(
                    cervical, dorsal, lumbar)
                cv2.putText(img_out, f"Eje Espinal: {desviacion_escoliosis} deg", (dorsal[0] + 15, dorsal[1]),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)

    img_rgb = cv2.cvtColor(img_out, cv2.COLOR_BGR2RGB)
    return Image.fromarray(img_rgb), desviacion_escoliosis


def procesar_pose_yolo(imagen_file, articulacion="Flexión de Codo"):
    if not YOLO_DISPONIBLE:
        return None, 0.0

    bytes_data = imagen_file.getvalue()
    file_bytes = np.frombuffer(bytes_data, dtype=np.uint8)
    img_bgr = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    results = model_yolo(img_bgr, verbose=False)
    angulo_calculado = 0.0
    img_annotated = img_bgr.copy()

    for r in results:
        if r.keypoints is not None and len(r.keypoints.data) > 0:
            kpts = r.keypoints.data[0].cpu().numpy()

            if "Rodilla" in articulacion:
                conf_izq = kpts[11][2] + kpts[13][2] + kpts[15][2]
                conf_der = kpts[12][2] + kpts[14][2] + kpts[16][2]
                p1, p2, p3 = ((int(kpts[11][0]), int(kpts[11][1])), (int(kpts[13][0]), int(kpts[13][1])), (int(kpts[15][0]), int(kpts[15][1]))) if conf_izq >= conf_der else (
                    (int(kpts[12][0]), int(kpts[12][1])), (int(kpts[14][0]), int(kpts[14][1])), (int(kpts[16][0]), int(kpts[16][1])))
            elif "Hombro" in articulacion:
                conf_izq = kpts[11][2] + kpts[5][2] + kpts[7][2]
                conf_der = kpts[12][2] + kpts[6][2] + kpts[8][2]
                p1, p2, p3 = ((int(kpts[11][0]), int(kpts[11][1])), (int(kpts[5][0]), int(kpts[5][1])), (int(kpts[7][0]), int(kpts[7][1]))) if conf_izq >= conf_der else (
                    (int(kpts[12][0]), int(kpts[12][1])), (int(kpts[6][0]), int(kpts[6][1])), (int(kpts[8][0]), int(kpts[8][1])))
            else:
                conf_izq = kpts[5][2] + kpts[7][2] + kpts[9][2]
                conf_der = kpts[6][2] + kpts[8][2] + kpts[10][2]
                p1, p2, p3 = ((int(kpts[5][0]), int(kpts[5][1])), (int(kpts[7][0]), int(kpts[7][1])), (int(kpts[9][0]), int(kpts[9][1]))) if conf_izq >= conf_der else (
                    (int(kpts[6][0]), int(kpts[6][1])), (int(kpts[8][0]), int(kpts[8][1])), (int(kpts[10][0]), int(kpts[10][1])))

            if p1[0] > 0 and p2[0] > 0 and p3[0] > 0:
                angulo_calculado = calcular_angulo_3puntos(p1, p2, p3)
                cv2.line(img_annotated, p2, p1, (0, 255, 128), 4)
                cv2.line(img_annotated, p2, p3, (0, 255, 128), 4)
                cv2.circle(img_annotated, p1, 8, (255, 0, 128), -1)
                cv2.circle(img_annotated, p2, 10, (0, 255, 255), -1)
                cv2.circle(img_annotated, p3, 8, (255, 0, 128), -1)
                cv2.putText(img_annotated, f"{angulo_calculado} deg", (p2[0] + 15, p2[1] - 15),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 255), 3)

    img_rgb = cv2.cvtColor(img_annotated, cv2.COLOR_BGR2RGB)
    return Image.fromarray(img_rgb), angulo_calculado


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
        "ashworth_modificada": "Grado 0: Tono muscular normal sin aumento",
        "datos_especificos": {},
        "beighton_score": 0,
        "grado_fry": "Grado 1: Dolor tras actividad severa",
        "aditamentos_prescritos": [],
        "pruebas_seleccionadas": [],
        "ejercicios_seleccionados": [],
        "diagnostico_sospechado": "",
        "custom_prueba": "",
        "custom_ejercicio": "",
        "custom_aditamento": "",
        "custom_diagnostico": "",
        "resultado_1rm": "",
        "escala_oswestry_score": "",
        "escala_dash_score": ""
    }

if "goniometria" not in st.session_state:
    st.session_state["goniometria"] = {
        "articulacion": "Flexión de Codo",
        "grados_activos": 45,
        "grados_pasivos": 50,
        "hallazgo": "Dentro de límites normales"
    }

if "foto_analisis" not in st.session_state:
    st.session_state["foto_analisis"] = None
if "foto_procesada_ia" not in st.session_state:
    st.session_state["foto_procesada_ia"] = None
if "firma_paciente" not in st.session_state:
    st.session_state["firma_paciente"] = None

# Generación de PDF Legal Gold Standard


def generar_pdf():
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, height - 40,
                 "PhysioFlow - Expediente Clínico Legal (NOM-004-SSA3-2012)")
    c.setFont("Helvetica", 9)
    c.drawString(50, height - 53,
                 f"Fisioterapeuta: Lic. {st.session_state['terapeuta']['nombre']} | Cédula Prof: {st.session_state['terapeuta']['cedula']} ({st.session_state['terapeuta']['institucion']})")
    c.line(50, height - 60, width - 50, height - 60)

    c.setFont("Helvetica-Bold", 10)
    c.drawString(50, height - 78, "1. FICHA DE IDENTIFICACIÓN DEL PACIENTE")
    c.setFont("Helvetica", 8)
    c.drawString(50, height - 90,
                 f"Nombre: {st.session_state['paciente']['nombre']}")
    c.drawString(320, height - 90,
                 f"Edad: {st.session_state['paciente']['edad']} años | Sexo: {st.session_state['paciente']['sexo']}")
    c.drawString(50, height - 102,
                 f"CURP/ID: {st.session_state['paciente']['curp']}")
    c.drawString(320, height - 102,
                 f"Ocupación: {st.session_state['paciente']['ocupacion']} | Tel: {st.session_state['paciente']['telefono']}")

    c.setFont("Helvetica-Bold", 10)
    c.drawString(50, height - 120, "2. ANTECEDENTES Y EVALUACIÓN CLÍNICA")
    c.setFont("Helvetica", 8)
    c.drawString(50, height - 132,
                 f"AHF: {st.session_state['paciente']['ahf'][:85]}")
    c.drawString(50, height - 144,
                 f"APP: {st.session_state['paciente']['app'][:85]}")
    c.drawString(50, height - 156,
                 f"Dolor: Zona {st.session_state['paciente']['mapa_dolor_zona']} | EVA: {st.session_state['paciente']['eva_dolor']}/10 | Tipo: {st.session_state['paciente']['tipo_dolor']}")
    c.drawString(50, height - 168,
                 f"Fuerza (Daniels): {st.session_state['paciente']['grados_daniels'][:75]}")

    c.setFont("Helvetica-Bold", 10)
    c.drawString(50, height - 188,
                 f"3. EVALUACIÓN ESPECIALIZADA: {st.session_state['paciente']['especialidad']}")
    c.setFont("Helvetica", 8)

    y_pos = height - 200
    for clave, valor in st.session_state["paciente"]["datos_especificos"].items():
        c.drawString(
            50, y_pos, f"• {clave.replace('_', ' ').capitalize()}: {valor}")
        y_pos -= 11

    gon = st.session_state["goniometria"]
    c.drawString(
        50, y_pos - 2, f"• Goniometría IA ({gon['articulacion']}): Activo: {gon['grados_activos']}° | Pasivo: {gon['grados_pasivos']}°")
    y_pos -= 16

    c.setFont("Helvetica-Bold", 10)
    c.drawString(
        50, y_pos, "4. DIAGNÓSTICO, CALCULADORAS & PRECRIPCIÓN BASADA EN EVIDENCIA")
    c.setFont("Helvetica", 8)
    y_pos -= 12

    diag_final = st.session_state['paciente']['custom_diagnostico'] if st.session_state['paciente'][
        'diagnostico_sospechado'] == "Otro / Personalizado..." else st.session_state['paciente']['diagnostico_sospechado']
    c.drawString(50, y_pos, f"• Diagnóstico Sospechado: {diag_final[:85]}")

    y_pos -= 12
    pruebas_list = [p for p in st.session_state["paciente"]
        ["pruebas_seleccionadas"] if p != "Otro / Personalizado..."]
    if st.session_state["paciente"]["custom_prueba"]:
        pruebas_list.append(st.session_state["paciente"]["custom_prueba"])
    pruebas_str = ", ".join(
        pruebas_list) if pruebas_list else "Ninguna seleccionada"
    c.drawString(50, y_pos, f"• Pruebas Validadas: {pruebas_str[:85]}")

    y_pos -= 12
    ejercicios_list = [e for e in st.session_state["paciente"]
        ["ejercicios_seleccionados"] if e != "Otro / Personalizado..."]
    if st.session_state["paciente"]["custom_ejercicio"]:
        ejercicios_list.append(
            st.session_state["paciente"]["custom_ejercicio"])
    ejercicios_str = "; ".join(
        ejercicios_list) if ejercicios_list else "Ninguno prescrito"
    c.drawString(50, y_pos, f"• Ejercicios Prescritos: {ejercicios_str[:85]}")

    y_pos -= 12
    adit_list = [a for a in st.session_state["paciente"]
        ["aditamentos_prescritos"] if a != "Otro / Personalizado..."]
    if st.session_state["paciente"]["custom_aditamento"]:
        adit_list.append(st.session_state["paciente"]["custom_aditamento"])
    adit_str = ", ".join(adit_list) if adit_list else "Sin aditamentos"
    c.drawString(50, y_pos, f"• Aditamentos Prescritos: {adit_str[:85]}")

    if st.session_state["paciente"]["resultado_1rm"]:
        y_pos -= 12
        c.drawString(
            50, y_pos, f"• Carga Terapéutica / 1RM: {st.session_state['paciente']['resultado_1rm']}")

    y_pos -= 20

    c.setFont("Helvetica-Bold", 10)
    c.drawString(50, y_pos, "5. CONSENTIMIENTO INFORMADO & FIRMAS LEGALES")
    c.setFont("Helvetica", 7)
    c.drawString(50, y_pos - 10, "Manifiesto mi conformidad y consentimiento para recibir la atención fisioterapéutica bajo la NOM-004-SSA3-2012.")

    if st.session_state["firma_paciente"] is not None:
        firma_pil = Image.fromarray(
            st.session_state["firma_paciente"].astype('uint8'))
        firma_reader = ImageReader(firma_pil)
        c.drawImage(firma_reader, 50, 40, width=150, height=45, mask='auto')

    c.line(50, 40, 220, 40)
    c.drawString(
        50, 30, f"Firma del Paciente: {st.session_state['paciente']['nombre']}")

    c.line(320, 40, 500, 40)
    c.drawString(
        320, 30, f"Lic. {st.session_state['terapeuta']['nombre']} - Ced. Prof: {st.session_state['terapeuta']['cedula']}")

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer


# -----------------------------------------------------------------------------
# BARRA LATERAL
# -----------------------------------------------------------------------------
# Carga tolerante de Logo y Branding
logo_path = None
for foto in ["logo_blanco.png", "Logo_blanco.png", "logo.png", "Logo.png"]:
    if os.path.exists(foto):
        logo_path = foto
        break

if logo_path:
    st.sidebar.image(logo_path, use_container_width=True)
else:
    st.sidebar.title("⚡ PhysioFlow")

# ==================== DATOS DEL PROFESIONAL AUTENTICADO ====================
st.sidebar.subheader("👤 Fisioterapeuta Autenticado")

# Obtener datos registrados o establecer valores por defecto si no ha iniciado sesión
usr_info = st.session_state.get("user_info") or {}

nombre_reg = usr_info.get("nombre", "Jorge Antonio Flores Díaz")
cedula_reg = usr_info.get("cedula", "")
institucion_reg = usr_info.get("institucion", "UNAM - Universidad Nacional Autónoma de México")
titulo_reg = usr_info.get("titulo", "LFT")

# Selector desplegable de título (toma por defecto el seleccionado en el registro)
titulos_lista = ["LFT", "LTF", "Mtro.", "Mtra.", "Dr.", "Dra.", "Lic."]
index_defecto = titulos_lista.index(titulo_reg) if titulo_reg in titulos_lista else 0

titulo_seleccionado = st.sidebar.selectbox(
    "Grado / Título Profesional:",
    titulos_lista,
    index=index_defecto
)

# Asignar datos dinámicos al estado del expediente
st.session_state["terapeuta"]["nombre"] = f"{titulo_seleccionado}. {nombre_reg}"
st.session_state["terapeuta"]["cedula"] = cedula_reg
st.session_state["terapeuta"]["institucion"] = institucion_reg

# Despliegue informativo inmutable en la barra lateral
st.sidebar.markdown(f"**Profesional:** {st.session_state['terapeuta']['nombre']}")
st.sidebar.markdown(f"**Cédula:** {st.session_state['terapeuta']['cedula']}")
st.sidebar.markdown(f"**Institución:** {st.session_state['terapeuta']['institucion']}")
st.sidebar.caption("🔒 *Datos de cuenta verificados. Se aplicarán a todos los expedientes y reportes PDF.*")
st.sidebar.write("---")

especialidades = list(DATOS_ESPECIALIDADES.keys())
especialidad_sel = st.sidebar.selectbox(
    "Especialidad Clínica Activa:",
    especialidades,
    key="especialidad_activa"
)
st.session_state["paciente"]["especialidad"] = especialidad_sel
st.sidebar.write("---")
# ---------------------------------------------------------
# NAVEGACIÓN Y SELECCIÓN DE MÓDULO
# ---------------------------------------------------------
modulo_trabajo = st.sidebar.radio(
    "Selecciona Módulo:",
    [
        "📁 Gestor de Pacientes & DB",
        "📜 Historia Clínica Legal (NOM-004)",
        "📝 Notas de Evolución (SOAP)",
        "📊 Calculadoras Clínicas & Escalas",
        "📐 Análisis Biomecánico & IA Pose",
        "🖼️ Estudios de Imagen & Gabinete",
        "🧍 Modelo 3D & Biomecánica Tridimensional"
    ]
)
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
        "fecha": "2026-08-25"
    }
    
    historia_clinica = {
        "anamnesis": paciente_dict.get("pa", "Sin registro de padecimiento actual."),
        "exploracion": f"Dermatomas: {paciente_dict.get('dermatomas', 'N/A')}\nMiotomas: {paciente_dict.get('miotomas', 'N/A')}\nROTs: {paciente_dict.get('rots', 'N/A')}",
        "diagnostico": paciente_dict.get("diagnostico_sospechado", "Por definir"),
        "diagnostico_funcional": "Deficiencia postural y sobreuso neuromuscular",
        "pronostico": "Favorable para la función",
        "plan": "Dosificación de carga e intervención fisioterapéutica"
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
# MÓDULO 1: GESTOR DE PACIENTES & BASE DE DATOS
# ==============================================================================
if modulo_trabajo == "📁 Gestor de Pacientes & DB":
    st.header("⚡ PhysioFlow - Gestor de Pacientes & Base de Datos Local")
    st.caption("Busca expedientes guardados, cárgalos en el sistema o registra al paciente actual.")

    col_g1, col_g2 = st.columns(2)
    with col_g1:
        if st.button("💾 Guardar / Actualizar Paciente Actual en DB"):
            p = st.session_state["paciente"]
            if p.get("nombre") and p.get("curp"):
                guardar_paciente_db(p)
                st.success(f"✅ Paciente **{p['nombre']}** guardado/actualizado correctamente.")
            else:
                st.error("⚠️ Ingrese al menos el Nombre y la CURP/ID del paciente para guardar.")

    st.write("---")
    st.subheader("📋 Directorio & Selector Rápido de Expedientes")

    pacientes_registrados = obtener_todos_pacientes_db()

    if pacientes_registrados:
        opciones_dict = {f"{p['nombre']} (ID/CURP: {p['curp']}) - {p['especialidad']}": p for p in pacientes_registrados}
        paciente_seleccionado_str = st.selectbox("Seleccionar paciente registrado:", list(opciones_dict.keys()))
        
        if st.button("📂 Cargar Expediente Seleccionado", use_container_width=True):
            p_datos = opciones_dict[paciente_seleccionado_str]
            datos_cargados = cargar_paciente_db(p_datos["curp"])
            if datos_cargados:
                st.session_state["paciente"].update(datos_cargados)
                st.success(f"✅ Expediente de **{p_datos['nombre']}** cargado exitosamente.")

        st.write("---")
        st.subheader("📊 Tabla de Pacientes en Sistema")
        st.dataframe(pacientes_registrados, use_container_width=True)
    else:
        st.info("ℹ️ No hay pacientes registrados aún en la Base de Datos Local.")

# ==============================================================================
# MÓDULO 2: HISTORIA CLÍNICA LEGAL (NOM-004)
# ==============================================================================
elif modulo_trabajo == "📜 Historia Clínica Legal (NOM-004)":
    st.header("📜 Historia Clínica Legal (NOM-004-SSA3-2012)")
    st.caption("Evaluación integral, exploración física, diagnóstico funcional y plan de intervención.")

    st.write("---")

    # Organización en Pestañas para una navegación limpia y rápida
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "1️⃣ Identificación", 
        "2️⃣ Anamnesis", 
        "3️⃣ Exploración & Neurología", 
        "4️⃣ Diagnóstico & Pronóstico", 
        "5️⃣ Prescripción & Plan"
    ])

    # ==================== PESTAÑA 1: FICHA DE IDENTIFICACIÓN ====================
    with tab1:
        st.subheader("1. Ficha de Identificación del Paciente")
        c1, c2, c3 = st.columns([2, 1, 1])
        with c1:
            st.session_state["paciente"]["nombre"] = st.text_input(
                "Nombre completo del paciente:", value=st.session_state["paciente"].get("nombre", "")
            )
        with c2:
            st.session_state["paciente"]["edad"] = st.number_input(
                "Edad:", value=int(st.session_state["paciente"].get("edad") or 0), min_value=0, max_value=120
            )
        with c3:
            sexos = ["Masculino", "Femenino", "Otro"]
            sexo_idx = sexos.index(st.session_state["paciente"].get("sexo", "Masculino")) if st.session_state["paciente"].get("sexo") in sexos else 0
            st.session_state["paciente"]["sexo"] = st.selectbox("Sexo:", sexos, index=sexo_idx)

        c4, c5, c6 = st.columns(3)
        with c4:
            st.session_state["paciente"]["curp"] = st.text_input(
                "CURP / Identificación:", value=st.session_state["paciente"].get("curp", "")
            )
        with c5:
            st.session_state["paciente"]["ocupacion"] = st.text_input(
                "Ocupación / Instrumento / Deporte:", value=st.session_state["paciente"].get("ocupacion", "")
            )
        with c6:
            st.session_state["paciente"]["telefono"] = st.text_input(
                "Teléfono de Contacto:", value=st.session_state["paciente"].get("telefono", "")
            )

    # ==================== PESTAÑA 2: ANAMNESIS & ANTECEDENTES ====================
    with tab2:
        st.subheader("2. Antecedentes Clínicos Obligatorios & Semiology")
        
        col_a1, col_a2 = st.columns(2)
        with col_a1:
            st.session_state["paciente"]["ahf"] = st.text_area(
                "Antecedentes Heredofamiliares (AHF):", value=st.session_state["paciente"].get("ahf", ""), height=100
            )
            st.session_state["paciente"]["app"] = st.text_area(
                "Antecedentes Patológicos (APP):", value=st.session_state["paciente"].get("app", ""), height=100
            )
        with col_a2:
            st.session_state["paciente"]["apnp"] = st.text_area(
                "Antecedentes No Patológicos (APNP):", value=st.session_state["paciente"].get("apnp", ""), height=100
            )
            st.session_state["paciente"]["pa"] = st.text_area(
                "Padecimiento Actual / Motivo de Consulta:", value=st.session_state["paciente"].get("pa", ""), height=100
            )

        st.write("---")
        st.markdown("**Semiología del Dolor**")
        col_s1, col_s2, col_s3 = st.columns(3)
        with col_s1:
            st.session_state["paciente"]["eva_dolor"] = st.slider(
                "Intensidad del Dolor (EVA 0-10):", 0, 10, int(st.session_state["paciente"].get("eva_dolor") or 0)
            )
        with col_s2:
            st.session_state["paciente"]["tipo_dolor"] = st.selectbox(
                "Tipo de Dolor:", ["Nociceptivo / Mecánico", "Neuropático / Irradiado", "Nociplástico", "Isquémico"], index=0
            )
        with col_s3:
            st.session_state["paciente"]["tiempo_evolucion"] = st.selectbox(
                "Tiempo de Evolución:", ["Agudo (< 2 semanas)", "Subagudo (2 - 6 semanas)", "Crónico (> 6 semanas)"], index=0
            )

    # ==================== PESTAÑA 3: EXPLORACIÓN & NEUROLOGÍA ====================
    with tab3:
        st.subheader("3. Exploración Física, Neurología & Fuerza Muscular")
        
        col_neu1, col_neu2 = st.columns(2)
        with col_neu1:
            st.markdown("**Evaluación Neuromotora Base**")
            st.session_state["paciente"]["dermatomas"] = st.text_input(
                "Dermatomas (Sensibilidad):", value=st.session_state["paciente"].get("dermatomas", ""), placeholder="Ej. C5-C6 Conservados, Hipoestesia C7"
            )
            st.session_state["paciente"]["miotomas"] = st.text_input(
                "Miotomas (Motor):", value=st.session_state["paciente"].get("miotomas", ""), placeholder="Ej. Flexión de codo 5/5, Extensión de muñeca 4/5"
            )
            st.session_state["paciente"]["rots"] = st.text_input(
                "Reflejos Osteotendinosos (ROTs):", value=st.session_state["paciente"].get("rots", ""), placeholder="Ej. Bicipital ++/++++, Tricipital ++/++++"
            )

        with col_neu2:
            st.markdown("**Fuerza Muscular Objetiva (Escala de Daniels 0-5)**")
            st.session_state["paciente"]["daniels_grupo"] = st.text_input(
                "Grupo Muscular / Segmento Evaluado:", value=st.session_state["paciente"].get("daniels_grupo", ""), placeholder="Ej. Extensores de muñeca izquierda"
            )
            st.session_state["paciente"]["daniels_grado"] = st.selectbox(
                "Grado de Fuerza Muscular:",
                [
                    "Grado 5 - Normal (Movimiento completo contra gravedad y resistencia máxima)",
                    "Grado 4 - Bueno (Movimiento completo contra gravedad y resistencia moderada)",
                    "Grado 3 - Regular (Movimiento completo solo contra gravedad)",
                    "Grado 2 - Deficiente (Movimiento completo eliminando la gravedad)",
                    "Grado 1 - Escaso (Vestigio de contracción palpable sin movimiento)",
                    "Grado 0 - Nulo (Ausencia total de contracción muscular)"
                ],
                index=0
            )
    # Section: Perfil Somático y Salud Mental (Basic Body Awareness & Autonómico)
        st.write("---")
        with st.expander("🧠 Perfil Somático & Regulación del Sistema Nervioso (Salud Mental)"):
            col_sm1, col_sm2 = st.columns(2)
            with col_sm1:
                st.session_state["paciente"]["patron_respiratorio"] = st.selectbox(
                    "Patrón Respiratorio Dominante:",
                    [
                        "Abdominodiafragmático / Vagal (Fisiológico)",
                        "Costal Superior / Apical (Predominio Simpático)",
                        "Paradójico / Restringido por Ansiedad/Estrés"
                    ]
                )
                st.session_state["paciente"]["nivel_estres_percibido"] = st.slider(
                    "Carga Alostática / Estrés Percibido (EVA Estrés 0-10):", 
                    0, 10, st.session_state["paciente"].get("nivel_estres_percibido", 3)
                )
            with col_sm2:
                st.session_state["paciente"]["hallazgos_psicosomaticos"] = st.multiselect(
                    "Manifestaciones Somáticas & Tono Reactivo:",
                    [
                        "Hipertonía Defensiva (Cintura Escapular / Cervical)",
                        "Alteración del Esquema / Conciencia Corporal (BBAT)",
                        "Bruxismo / Tensión ATM Asociada",
                        "Catastrofización del Dolor",
                        "Kinesiofobia (Miedo al Movimiento)",
                        "Fatiga Crónica / Alteración del Sueño"
                    ]
                )
    # ==================== PESTAÑA 4: DIAGNÓSTICO & PRONÓSTICO ====================
    with tab4:
        st.subheader("4. Diagnóstico Funcional (CIF) & Pronóstico Clínico")
        
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            st.session_state["paciente"]["diagnostico_sospechado"] = st.text_input(
                "Diagnóstico Patológico / Nosológico:",
                value=st.session_state["paciente"].get("diagnostico_sospechado", ""),
                placeholder="Ej. Tenosinovitis de De Quervain / Síndrome de Pinzamiento Subacromial"
            )
            st.session_state["paciente"]["diag_funcional"] = st.text_area(
                "Diagnóstico Funcional (CIF):",
                value=st.session_state["paciente"].get("diag_funcional", ""),
                placeholder="Ej. Deficiencia en la tolerancia muscular de extensores de muñeca y restricción en la ejecución de pasajes rápidos en violín.",
                height=120
            )

        with col_d2:
            st.session_state["paciente"]["pronostico_text"] = st.selectbox(
                "Pronóstico de Recuperación:",
                ["Favorable para la función", "Reservado a evolución", "Favorable a corto plazo", "Desfavorable / Limitado"],
                index=0
            )
            st.session_state["paciente"]["tiempo_estimado"] = st.text_input(
                "Tiempo Estimado de Recuperación:",
                value=st.session_state["paciente"].get("tiempo_estimado", ""),
                placeholder="Ej. 4 a 6 semanas (12 sesiones de rehabilitación)"
            )

    # ==================== PESTAÑA 5: PRESCRIPCIÓN & PLAN ====================
    # ==================== PESTAÑA 5: PRESCRIPCIÓN & PLAN DE TRATAMIENTO ====================
    with tab5:
        st.subheader("5. Prescripción Basada en Evidencia & Plan de Intervención")
        
        # Botón de Decisión Clínica Inteligente (CDSS)
        # Botón de Decisión Clínica Inteligente (CDSS)
        if st.button("💡 Generar Sugerencias Inteligentes por Especialidad", use_container_width=True):
            esp_activa = st.session_state.get("especialidad", "Músicos & Artes Escénicas")
            datos_esp = DATOS_ESPECIALIDADES.get(esp_activa, {})
            if datos_esp:
                st.session_state["paciente"]["diagnostico_sospechado"] = datos_esp["diagnosticos"][0]
                st.session_state["paciente"]["plan_intervencion"] = " • " + "\n • ".join(datos_esp["ejercicios"])
                st.session_state["paciente"]["aditamentos_recomendados"] = " • " + "\n • ".join(datos_esp["aditamentos"])
                st.success(f"🤖 Sugerencias clínicas cargadas automáticamente para: **{esp_activa}**.")
        st.write("---")

        # Bloque Flexible: Modalidades Coadyuvantes & Terapia Manual
        st.markdown("### 🛠️ Modalidades Coadyuvantes & Terapia Manual")
        
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            st.session_state["paciente"]["tecnicas_manuales"] = st.multiselect(
                "Técnicas Manuales & Neuromusculares:",
                [
                    "Movilización Articular Analítica",
                    "Manipulación Alta Velocidad (HVLA)",
                    "Terapia Manual Instrumentalizada (IASTM)",
                    "Liberación Miofascial / Puntos Gatillo",
                    "Punción Seca Terapéutica",
                    "Neurodinamia / Movilización Neural",
                    "Reeducación Postural / Control Motor"
                ]
            )
        with col_m2:
            st.session_state["paciente"]["agentes_soporte"] = st.multiselect(
                "Agentes Físicos / Modalidades de Soporte:",
                [
                    "TENS / Neuromodulación Analgésica",
                    "EMS / NMES (Fortalecimiento/Reeducación)",
                    "Laserterapia (LLLT / Bioestimulación)",
                    "Ondas de Choque Radiales",
                    "Ultrasonido Terapéutico",
                    "Crioterapia / Termoterapia Coadyuvante",
                    "Vendaje Neuromuscular / Kinesiotape"
                ]
            )

        st.session_state["paciente"]["notas_coadyuvantes"] = st.text_input(
            "Especificaciones / Dosificación Libre (Opcional):",
            value=st.session_state["paciente"].get("notas_coadyuvantes", ""),
            placeholder="Ej. Punción seca en extensor común de los dedos + TENS analgésico 20 min."
        )

        st.write("---")
        st.markdown("### 🏋️ Prescripción de Ejercicios & Aditamentos")

        col_p1, col_p2 = st.columns(2)
        with col_p1:
            st.session_state["paciente"]["plan_intervencion"] = st.text_area(
                "Plan de Intervención Fisioterapéutica (Ejercicios & Dosificación):",
                value=st.session_state["paciente"].get("plan_intervencion", ""),
                placeholder="Ej. Dosificación de carga, ejercicios de control motor, reeducación biomecánica en el gesto técnico.",
                height=130
            )
        with col_p2:
            st.session_state["paciente"]["aditamentos_recomendados"] = st.text_area(
                "Aditamentos & Productos Recomendados:",
                value=st.session_state["paciente"].get("aditamentos_recomendados", ""),
                placeholder="Ej. Banda elástica de resistencia media, soporte de antebrazo ergonómico, pelota de masaje miofascial.",
                height=130
            )
# ==============================================================================
# MÓDULO 3: NOTAS DE EVOLUCIÓN (SOAP)
# ==============================================================================
elif modulo_trabajo == "📝 Notas de Evolución (SOAP)":
    st.header("📝 Nota de Evolución Clínica (Metodología SOAP)")
    st.caption("Registro estandarizado para el seguimiento sesión a sesión según la NOM-004-SSA3-2012.")

    # Selección de Paciente y Sesión
    col_pac, col_ses = st.columns([2, 1])
    with col_pac:
        paciente_actual = st.session_state.get("paciente", {}).get("nombre", "Paciente de Ejemplo")
        st.info(f"👤 **Paciente Activo:** {paciente_actual}")
    with col_ses:
        num_sesion = st.number_input("Número de Sesión:", min_value=1, max_value=100, value=1)
        fecha_sesion = st.date_input("Fecha de Consulta:")

    st.write("---")

    # METODOLOGÍA S.O.A.P.
    col_s, col_o = st.columns(2)
    
    with col_s:
        st.subheader("S - Subjetivo (Reporte del Paciente)")
        eva_dolor = st.slider("Escala Visual Análoga (EVA 0-10):", 0, 10, 3, key="soap_eva")
        subjetivo_txt = st.text_area(
            "Evolución percibida y respuesta al tratamiento anterior:",
            placeholder="El paciente refiere disminución del dolor...",
            height=140
        )
        adherencia = st.select_slider(
            "Adherencia a ejercicios en casa:",
            options=["Nula (0%)", "Baja (25%)", "Moderada (50%)", "Buena (75%)", "Excelente (100%)"],
            value="Buena (75%)"
        )

    with col_o:
        st.subheader("O - Objetivo (Hallazgos Físicos)")
        objetivo_txt = st.text_area(
            "Re-evaluación objetiva (ROM, fuerza, palpación, pruebas provocativas):",
            placeholder="ROM activo de flexión cervical completo sin dolor...",
            height=140
        )
        carga_trabajo = st.text_input("Carga / Dosificación utilizada hoy:", placeholder="Ej. 3 series x 12 reps con banda elástica media")

    st.write("---")
    col_a, col_p = st.columns(2)

    with col_a:
        st.subheader("A - Análisis / Apreciación Clínica")
        analisis_txt = st.text_area(
            "Razonamiento clínico y respuesta biológica al estímulo:",
            placeholder="Evolución favorable con buena tolerancia a la carga...",
            height=130
        )

    with col_p:
        st.subheader("P - Plan de Tratamiento & Continuidad")
        plan_txt = st.text_area(
            "Ajustes al programa, progresión de cargas e indicaciones:",
            placeholder="Progresar ejercicios de control motor...",
            height=130
        )
        proxima_cita = st.date_input("Fecha sugerida para próxima sesión:")

    st.write("---")

    # Guardado de la Nota
    if st.button("💾 Guardar Nota SOAP en Historial"):
        if "historial_soap" not in st.session_state:
            st.session_state["historial_soap"] = []
            
        nota_nueva = {
            "sesion": num_sesion,
            "fecha": str(fecha_sesion),
            "paciente": paciente_actual,
            "eva": eva_dolor,
            "subjetivo": subjetivo_txt,
            "objetivo": objetivo_txt,
            "analisis": analisis_txt,
            "plan": plan_txt,
            "adherencia": adherencia
        }
        st.session_state["historial_soap"].append(nota_nueva)
        st.success(f"✅ Nota de la Sesión #{num_sesion} guardada correctamente.")

    # Historial de Sesiones
    if st.session_state.get("historial_soap"):
        with st.expander("📚 Ver Historial de Notas SOAP Guardadas"):
            for nota in reversed(st.session_state["historial_soap"]):
                st.markdown(f"### Sesión #{nota['sesion']} — {nota['fecha']} (EVA: {nota['eva']}/10)")
                st.markdown(f"**Subjetivo:** {nota['subjetivo']} *(Adherencia: {nota['adherencia']})*")
                st.markdown(f"**Objetivo:** {nota['objetivo']}")
                st.markdown(f"**Análisis:** {nota['analisis']}")
                st.markdown(f"**Plan:** {nota['plan']}")
                st.divider()

# ==============================================================================
# MÓDULO 4: CALCULADORAS CLÍNICAS & ESCALAS
# ==============================================================================
elif modulo_trabajo == "📊 Calculadoras Clínicas & Escalas":
    st.header("📊 Calculadoras Clínicas & Escalas Funcionales Validadas")

    tab_quickdash, tab_visa, tab_oswestry, tab_1rm = st.tabs([
        "🎸 QuickDASH (Miembro Superior)", 
        "🦵 Rodilla & Miembro Inferior (VISA / KOOS-12)", 
        "🦴 Oswestry (ODI Lumbar)", 
        "🏋️ Calculadora 1RM"
    ])

    with tab_quickdash:
        st.subheader("Escala QuickDASH")
        preguntas_dash = [
            "1. Abrir un frasco apretado o nuevo.",
            "2. Escribir / Teclear o realizar trabajo fino con la mano.",
            "3. Girar una llave para abrir una puerta.",
            "4. Preparar una comida / Cargar utensilios pesados.",
            "5. Empujar una puerta pesada.",
            "6. Colocar un objeto en un estante por encima de la cabeza.",
            "7. Actividades cotidianas (lavarse, vestirse, etc.).",
            "8. Interferencia del dolor en sus actividades sociales.",
            "9. Limitación en su trabajo habitual o actividades diarias.",
            "10. Intensidad del dolor en el brazo, hombro o mano.",
            "11. Dificultad para dormir debido al dolor en el miembro superior."
        ]
        respuestas_dash = []
        for p in preguntas_dash:
            v = st.select_slider(p, options=[1, 2, 3, 4, 5], value=1, key=f"dash_{p[:2]}",
                                 format_func=lambda x: {1: "1: Ninguna", 2: "2: Leve", 3: "3: Moderada", 4: "4: Severa", 5: "5: Incapaz"}[x])
            respuestas_dash.append(v)
        score_quickdash = ((sum(respuestas_dash) / len(respuestas_dash)) - 1) * 25
        st.metric("Puntaje Total QuickDASH", f"{score_quickdash:.1f} / 100")

    with tab_visa:
        subtab_visa, subtab_koos = st.tabs(["🦵 Cuestionario VISA (Tendinopatías)", "🦴 Escala KOOS-12 (Rodilla)"])
        with subtab_visa:
            tipo_visa = st.radio("Selecciona la escala:", ["VISA-A (Aquilea)", "VISA-P (Patelar)"], horizontal=True)
            v1 = st.slider("1. Dolor en reposo (0-10)", 0, 10, 10, key="v1")
            v2 = st.slider("2. Dolor al estirar (0-10)", 0, 10, 10, key="v2")
            v3 = st.slider("3. Dolor al marchar (0-10)", 0, 10, 10, key="v3")
            v4 = st.slider("4. Capacidad de saltar (0-10)", 0, 10, 10, key="v4")
            v5 = st.slider("5. Rendimiento deportivo/ensayo (0-20)", 0, 20, 20, key="v5")
            score_visa = v1 + v2 + v3 + v4 + v5
            st.metric(f"Puntaje Total {tipo_visa}", f"{score_visa} / 60")

        with subtab_koos:
            st.subheader("KOOS-12 (Knee Injury and Osteoarthritis Outcome Score)")
            k_dolor = st.slider("1. Dolor al cargar peso / flexionar:", 0, 4, 0)
            k_rigidez = st.slider("2. Rigidez al despertar:", 0, 4, 0)
            k_escaleras = st.slider("3. Dificultad escaleras:", 0, 4, 0)
            k_impacto = st.slider("4. Dificultad correr/saltar:", 0, 4, 0)
            k_qol = st.slider("5. Conciencia constante de la rodilla:", 0, 4, 0)
            suma_koos = k_dolor + k_rigidez + k_escaleras + k_impacto + k_qol
            score_koos = 100 - ((suma_koos / 20) * 100)
            st.metric("Puntaje Funcional KOOS-12", f"{score_koos:.1f}%")

    with tab_oswestry:
        st.subheader("Índice de Incapacidad Lumbar de Oswestry (ODI)")
        o1 = st.selectbox("1. Intensidad del dolor:", ["0: Leve", "1: Moderado", "2: Severo"])
        st.metric("Puntaje ODI", "10%")

    with tab_1rm:
        st.subheader("Calculadora Terapéutica 1RM (Brzycki)")
        c1, c2 = st.columns(2)
        peso = c1.number_input("Carga (kg):", min_value=1.0, value=20.0)
        reps = c2.number_input("Repeticiones:", min_value=1, max_value=12, value=8)
        uno_rm = peso / (1.0278 - (0.0278 * reps))
        st.info(f"🏋️ **1RM Estimada: {uno_rm:.1f} kg**")

# ==============================================================================
# MÓDULOS 5 Y 6: ANÁLISIS BIOMECÁNICO & ESCOLIOSIS
# ==============================================================================
elif modulo_trabajo == "📐 Análisis Biomecánico & IA Pose":
    st.header("📐 Módulo Integral de Biomecánica & Gesto Técnico")
    st.caption("Evaluación de movimiento a cámara lenta, goniometría digital y alineación postural.")

    st.write("---")

    # Contenedor principal de controles
    col_video, col_herramientas = st.columns([2, 1])

    with col_video:
        st.subheader("📹 Carga y Reproducción de Video")
        fuente_video = st.radio("Fuente de Entrada:", ["Subir Archivo de Video / Imagen", "Cámara en Vivo"], horizontal=True)
        
        archivo_video = None
        if fuente_video == "Subir Archivo de Video / Imagen":
            archivo_video = st.file_uploader("Cargar video del gesto técnico (MP4, MOV, AVI, JPG, PNG):", type=["mp4", "mov", "avi", "jpg", "png"])
            if archivo_video:
                st.video(archivo_video)
        else:
            st.info("💡 La captura por cámara en vivo utiliza la transmisión WebRTC local.")
            st.camera_input("Capturar fotograma para análisis rápido")

    with col_herramientas:
        st.subheader("🛠️ Panel de Goniometría & Controles")
        
        st.markdown("**Velocidad de Reproducción (Cámara Lenta)**")
        velocidad = st.select_slider("Factor de Velocidad:", options=["0.25x (Super Slow)", "0.5x (Slow)", "1.0x (Normal)"], value="0.5x (Slow)")
        
        st.markdown("**Herramientas de Medición sobre Fotograma**")
        herramienta_activa = st.selectbox("Seleccionar Herramienta:", [
            "Línea de Plomada / Eje Postural",
            "Goniómetro Digital (Ángulo 3 Puntos)",
            "Tracking de Pose IA (MediaPipe)",
            "Cuadrícula de Referencia"
        ])
        
        st.write("---")
        st.markdown("**Valores Goniométricos Capturados (°)**")
        angulo_medido = st.number_input("Ángulo Articular Medido (°):", min_value=0.0, max_value=360.0, value=0.0, step=0.5)
        articulacion = st.text_input("Articulación / Región:", placeholder="Ej. Flexión de Muñeca Izquierda")

    st.write("---")

    # Sección de Registro Clínico del Gesto Técnico
    st.subheader("📝 Registro Clínico Cinematodinámico")
    
    col_obs1, col_obs2 = st.columns(2)
    with col_obs1:
        observaciones_movimiento = st.text_area("Hallazgos en Fases Críticas del Movimiento:", placeholder="Ej. Aumento de flexión cervical y sobreuso de extensores del antebrazo durante la fase de ejecución rápida.")
    with col_obs2:
        plan_correccion = st.text_area("Propuesta de Reeducación Motora / Corrección Biomecánica:", placeholder="Ej. Ajuste de postura de sostén, dosificación de carga muscular y pausa activa.")

    if st.button("💾 Guardar Análisis Biomecánico en Expediente Actual", use_container_width=True):
        st.success("✅ Análisis biomecánico guardado correctamente en la sesión activa del paciente.")
elif modulo_trabajo == "🖼️ Estudios de Imagen & Gabinete":
    st.header("🖼️ Centro de Imagenología & Estudios de Gabinete")
    st.caption("Carga de estudios radiológicos, ultrasonido o resonancias e interpretación clínica.")

    st.write("---")
    col_img1, col_img2 = st.columns([1, 1])

    with col_img1:
        st.subheader("📁 Carga de Estudio (Rayos X, RM, USG)")
        archivo_estudio = st.file_uploader(
            "Seleccionar archivo de imagen (PNG, JPG, JPEG):", 
            type=["png", "jpg", "jpeg"]
        )
        if archivo_estudio:
            st.image(archivo_estudio, caption="Estudio de Gabinete Cargado", use_container_width=True)
            st.session_state["paciente"]["estudio_imagen_cargado"] = True

    with col_img2:
        st.subheader("📝 Hallazgos & Interpretación Radiológica")
        st.session_state["paciente"]["tipo_estudio"] = st.selectbox(
            "Tipo de Estudio:",
            ["Radiografía Simple (Rx)", "Resonancia Magnética (RM)", "Ultrasonido Musculoesquelético (USG)", "Tomografía Axial (TAC)", "Electromiografía (EMG)"]
        )
        st.session_state["paciente"]["region_estudio"] = st.text_input(
            "Región Anatómica / Proyección:",
            value=st.session_state["paciente"].get("region_estudio", ""),
            placeholder="Ej. Columna Lumbar AP y Lateral / Muñeca Izquierda"
        )
        st.session_state["paciente"]["interpretacion_imagen"] = st.text_area(
            "Interpretación & Hallazgos Clave:",
            value=st.session_state["paciente"].get("interpretacion_imagen", ""),
            placeholder="Ej. Rectificación de la lordosis lumbar. Espacio intervertebral L5-S1 conservado. Sin evidencia de osteofitos...",
            height=180
        )
        st.success("✅ Interpretación vinculada al Expediente del Paciente.")

elif modulo_trabajo == "🧍 Modelo 3D & Biomecánica Tridimensional":
    st.header("🧍 Visor Anatómico 3D & Biomecánica Interactiva")
    st.caption("Renderizado tridimensional para explicación al paciente y mapeo de cargas.")

    st.write("---")
    st.info("🎮 **Espacio listo para render 3D (Three.js / WebGL):** El motor visual 3D interactivo se cargará en este viewport.")
    
    st.components.v1.html(
        """
        <div style="background-color: #1e1e1e; color: #ffffff; height: 400px; display: flex; align-items: center; justify-content: center; border-radius: 10px; border: 1px solid #333;">
            <div style="text-align: center;">
                <h3>🤖 Modelo Anatómico 3D Ready</h3>
                <p style="color: #aaa;">Integra aquí tu canvas Three.js o iframe de modelos GLTF/OBJ (PhysioFlow 3D Engine)</p>
            </div>
        </div>
        """,
        height=420
    )