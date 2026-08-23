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
            Paragraph(f"<b>Fisioterapeuta:</b> {datos_terapeuta.get('nombre', 'Lic. Jorge Flores')}", style_body),
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
        [Paragraph(f"<b>{datos_terapeuta.get('nombre', 'Lic. Jorge Flores')}</b>", ParagraphStyle('FirmaStyle', parent=style_body, alignment=1))],
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
    st.write("---")
    st.subheader("Exportación de Reporte Clínico")

    if st.button("📄 Generar Expediente PDF (NOM-004)"):
        datos_terapeuta = {
            "nombre": st.session_state.get("nombre_terapeuta", "Jorge Flores"),
            "cedula": st.session_state.get("cedula_terapeuta", ""),
            "institucion": st.session_state.get("institucion_terapeuta", "UNAM"),
            "especialidad": st.session_state.get("especialidad_activa", "Músicos & Artes Escénicas")
        }
        
        datos_paciente = {
            "nombre": st.session_state.get("paciente_nombre", "Paciente de Ejemplo"),
            "edad": st.session_state.get("paciente_edad", 25),
            "sexo": st.session_state.get("paciente_sexo", "Masculino"),
            "ocupacion": st.session_state.get("paciente_ocupacion", "Músico / Violinista"),
            "fecha": "2026-08-22"
        }
        
        historia_clinica = {
            "anamnesis": st.session_state.get("anamnesis_text", "Paciente refiere molestia asociada a la práctica musical."),
            "exploracion": st.session_state.get("exploracion_text", "Rango de movimiento conservado con molestia a la palpación."),
            "diagnostico": st.session_state.get("diagnostico_text", "Síndrome de sobreuso muscular."),
            "diagnostico_funcional": st.session_state.get("diag_funcional_text", "Limitación leve en rangos de movimiento fino."),
            "pronostico": st.session_state.get("pronostico_text", "Favorable"),
            "plan": st.session_state.get("plan_text", "Terapia manual y reeducación postural.")
        }
        
        pdf_buffer = generar_pdf_expediente(datos_terapeuta, datos_paciente, historia_clinica)
        
        st.download_button(
            label="⬇️ Descargar Expediente PDF",
            data=pdf_buffer,
            file_name=f"Expediente_{datos_paciente['nombre'].replace(' ', '_')}.pdf",
            mime="application/pdf"
        )

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

# -----------------------------------------------------------------------------
# DATOS DINÁMICOS POR ESPECIALIDAD
# -----------------------------------------------------------------------------
DATOS_ESPECIALIDADES = {
    "Músicos & Artes Escénicas": {
        "diagnosticos": ["Tenosinovitis de De Quervain", "Síndrome de Atrapamiento de Rama Sensitiva Radial (Wartenberg)", "Distonía Focal del Músico", "Síndrome del Túnel Carpiano", "Síndrome de Hipermovilidad Articular BENIGNA"],
        "pruebas": ["Finkelstein Test (De Quervain)", "Test de Wartenberg (Radial Sensitivo)", "Phalen / Phalen Invertido (Túnel Carpiano)", "Elson Test (Banda Central)", "Test de Watson (Escafolunar)", "Otro / Personalizado..."],
        "ejercicios": ["Neurodinamia Deslizamiento / Tensión Nervio Radial (3x10 rep)", "Neurodinamia Deslizamiento / Tensión Nervio Mediano (3x10 rep)", "Excéntricos de Extensores de Muñeca (3x12 rep)", "Fortalecimiento de Intrínsecos de Mano (Ligas)", "Control Motor Cervical Profundo (3x15s)", "Otro / Personalizado..."],
        "aditamentos": ["Mentonera Central Teka", "Almohadilla Ergonómica KorfkerRest", "Puntos de Gel Viscoelástico (Silopad)", "Soporte de Pulgar Ton Kooiman", "Silver Ring Splints", "Otro / Personalizado..."]
    },
    "Fisioterapia Neurológica": {
        "diagnosticos": ["Secuela de Evento Vascular Cerebral (EVC)", "Síndrome de Segunda Neurona Motora", "Marcha Atáxica Espinocerebelosa", "Parálisis Facial Periférica (Bell)", "Enfermedad de Parkinson"],
        "pruebas": ["Signo de Babinski / Hoffmann", "Signo de Romberg", "Prueba Índice-Nariz", "Test de Disdiadococinesia", "Prueba de Clonus Aquileo / Rotuliano", "Otro / Personalizado..."],
        "ejercicios": ["FNP (Iniciación Rítmica)", "Carga de Peso Dinámica y Transferencia de Centro de Gravedad", "Reeducación de Marcha con Biofeedback", "Ejercicios de Mimación Facial", "Cinesiterapia Pasiva Asistida", "Otro / Personalizado..."],
        "aditamentos": ["Órtesis Tobillo-Pie (AFO)", "Cabestrillo Hemipléjico de Hombro", "Férula Antiespástica de Mano", "Andador de Cuatro Puntos", "Otro / Personalizado..."]
    },
    "Fisioterapia Deportiva (Sports)": {
        "diagnosticos": ["Rotura / Reconstrucción de LCA", "Tendinopatía Aquilea / Rotuliana", "Síndrome de Pinzamiento Subacromial", "Esguince de LLI de Rodilla", "Lesión Miotendinosa de Isquiotibiales"],
        "pruebas": ["Lachman Test / Cajón Anterior", "McMurray / Apley Test", "Thompson Test", "Hawkins-Kennedy / Neer Test", "Single Leg Hop Test (LSI)", "Otro / Personalizado..."],
        "ejercicios": ["Pliometría Progresiva y Control de Aterrizaje", "Nordic Hamstring Curls (3x8)", "Isométricos de Tendón Rotuliano (4x45s)", "Y-Balance Test Training", "Fortalecimiento Rotadores Externos", "Otro / Personalizado..."],
        "aditamentos": ["Rodillera Mecánica con Control de Flexión", "Cincha Infrapatelar para Tendón Rotuliano", "Taping Neuromuscular", "Muslera / Tobillera Neopreno", "Otro / Personalizado..."]
    },
    "Ergonomía Laboral": {
        "diagnosticos": ["Cervicobraquialgia Sedente", "Epicondilopatía Lateral / Medial Laboral", "Síndrome de Túnel Carpiano Laboral", "Lumbalgia Mecánica Postural", "Síndrome de Salida Torácica (TOS)"],
        "pruebas": ["Test de Cozen / Mill", "Prueba de Roos / Wright", "Cuestionario Nórdico de Síntomas", "Evaluación RULA / REBA", "Otro / Personalizado..."],
        "ejercicios": ["Pausas Activas Cervicodorsales", "Estiramiento Activo de Pectoral Menor", "Fortalecimiento de Trapecio Inferior y Serrato", "Deslizamientos Neurodinámicos Cervicobraquiales", "Otro / Personalizado..."],
        "aditamentos": ["Mouse Ergonómico Vertical 57°", "Apoyapiés Ergonómico Inclinable", "Soporte Lumbar Viscoelástico", "Teclado Ergonométrico Dividido", "Otro / Personalizado..."]
    },
    "Geriátricos & Autonomía": {
        "diagnosticos": ["Síndrome de Fragilidad y Sarcopenia", "Osteoartrosis Severa de Rodilla / Cadera", "Inestabilidad de Marcha y Riesgo de Caídas", "Síndrome de Inmovilidad Prolongada", "Post-op Prótesis Total de Cadera"],
        "pruebas": ["Timed Up and Go (TUG Test)", "Escala de Tinetti (Marcha/Equilibrio)", "Short Physical Performance Battery (SPPB)", "Dinamometría Prensil", "Otro / Personalizado..."],
        "ejercicios": ["Sit-to-Stand (3x10 rep)", "Entrenamiento de Balance Unipodal", "Fortalecimiento Extensores de Cadera con Polainas", "Caminata con Obstáculos Bajos", "Otro / Personalizado..."],
        "aditamentos": ["Bastón Regulable de Aluminio", "Andador de Aluminio con Ruedas y Asiento", "Sillas de Baño y Barras Antideslizantes", "Calzador de Mango Largo", "Otro / Personalizado..."]
    },
    "Salud de la Mujer / Suelo Pélvico": {
        "diagnosticos": ["Incontinencia Urinaria de Esfuerzo (IUE)", "Diástasis Abdominal Posparto (>25mm)", "Dolor Pélvico Crónico / Vaginismo", "Prolapso de Órganos Pélvicos (POP I/II)", "Disfunción Lumbo-Pélvica Periparto"],
        "pruebas": ["Valoración PERFECT / Oxford Modificada", "Medición de Diástasis Abdominal", "Cuestionario ICIQ-SF", "Test de Provocación con Tos", "Otro / Personalizado..."],
        "ejercicios": ["Entrenamiento Suelo Pélvico (Kegel Guiado)", "Co-contracción Transverso - Suelo Pélvico", "Gimnasia Abdominal Hipopresiva (GAH)", "Movilización Pélvica sobre Fitball", "Otro / Personalizado..."],
        "aditamentos": ["Biofeedback / Perineómetro Neumático", "Conos Vaginales Progresivos", "Cojín Pélvico Cóncavo", "Faja de Soporte Pélvico Posparto", "Otro / Personalizado..."]
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

st.sidebar.caption("by Lic. Jorge Flores | Fisioterapia Especializada")
st.sidebar.write("---")

st.sidebar.subheader("👨‍⚕️ Datos del Fisioterapeuta")
st.session_state["terapeuta"]["nombre"] = st.sidebar.text_input(
    "Nombre Terapeuta:", value=st.session_state["terapeuta"]["nombre"])
st.session_state["terapeuta"]["cedula"] = st.sidebar.text_input(
    "Cédula Profesional:", value=st.session_state["terapeuta"]["cedula"], placeholder="Ej. 12345678")
st.session_state["terapeuta"]["institucion"] = st.sidebar.text_input(
    "Institución:", value=st.session_state["terapeuta"]["institucion"])

st.sidebar.write("---")

especialidades = list(DATOS_ESPECIALIDADES.keys())
especialidad_sel = st.sidebar.selectbox(
    "Especialidad Clínica Activa:",
    especialidades,
    index=especialidades.index(st.session_state["paciente"]["especialidad"]
                               ) if st.session_state["paciente"]["especialidad"] in especialidades else 0
)
st.session_state["paciente"]["especialidad"] = especialidad_sel

st.sidebar.write("---")
modulo_trabajo = st.sidebar.radio(
    "Selecciona Módulo:",
    [
        "📂 Gestor de Pacientes & DB",
        "Historia Clínica Legal (NOM-004)",
        "📝 Notas de Evolución (SOAP)",
        "Calculadoras Clínicas & Escalas",
        "Análisis Biomecánico & IA Pose",
        "Análisis de Columna & Escoliosis",
        "Firma & Exportación PDF"
    ]
)

# -----------------------------------------------------------------------------
# INTERFAZ PRINCIPAL
# -----------------------------------------------------------------------------
st.title(f"⚡ PhysioFlow Gold Standard - {especialidad_sel}")

# MÓDULO NUEVO: GESTOR DE PACIENTES Y BASE DE DATOS LOCAL
if modulo_trabajo == "📂 Gestor de Pacientes & DB":
    st.header("📂 Gestor de Pacientes & Base de Datos Local")
    st.caption(
        "Busca expedientes guardados, cárgalos en el sistema o registra al paciente actual.")

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("💾 Guardar / Actualizar Paciente Actual en DB"):
            if st.session_state["paciente"]["curp"] and st.session_state["paciente"]["nombre"]:
                guardar_paciente_db(st.session_state["paciente"])
                st.success(
                    f"✅ Paciente '{st.session_state['paciente']['nombre']}' guardado correctamente en la Base de Datos.")
            else:
                st.error(
                    "⚠️ Ingrese al menos el Nombre y la CURP/ID del paciente para guardar.")

    st.write("---")
    st.subheader("🔍 Buscador de Expedientes Guardados")
    texto_busqueda = st.text_input(
        "Buscar por Nombre o CURP:", placeholder="Ej. Juan Pérez o CURP1234")

    resultados = buscar_pacientes_db(texto_busqueda)

    if resultados:
        for r in resultados:
            p_id, p_nombre, p_curp, p_esp, p_tel = r
            c1, c2, c3, c4 = st.columns([3, 2, 2, 2])
            c1.write(f"**{p_nombre}**")
            c2.write(f"ID/CURP: {p_curp}")
            c3.write(f"Esp: {p_esp}")
            if c4.button(f"📂 Cargar", key=f"btn_load_{p_id}"):
                datos_cargados = cargar_paciente_db(p_curp)
                if datos_cargados:
                    st.session_state["paciente"].update(datos_cargados)
                    st.success(
                        f"✅ Expediente de {p_nombre} cargado exitosamente en la sesión activa.")
    else:
        st.info("No se encontraron registros en la Base de Datos.")

# MÓDULO 1: HISTORIA CLÍNICA LEGAL COMPLETA
elif modulo_trabajo == "Historia Clínica Legal (NOM-004)":
    st.header("1. Ficha de Identificación del Paciente")

    c1, c2, c3 = st.columns([2, 1, 1])
    with c1:
        st.session_state["paciente"]["nombre"] = st.text_input(
            "Nombre completo del paciente", value=st.session_state["paciente"]["nombre"])
    with c2:
        st.session_state["paciente"]["edad"] = st.number_input("Edad", value=int(
            st.session_state["paciente"]["edad"]), min_value=0, max_value=120)
    with c3:
        st.session_state["paciente"]["sexo"] = st.selectbox(
            "Sexo", ["Masculino", "Femenino", "Otro"], index=0 if st.session_state["paciente"]["sexo"] == "Masculino" else 1)

    c4, c5, c6 = st.columns(3)
    with c4:
        st.session_state["paciente"]["curp"] = st.text_input(
            "CURP / Identificación", value=st.session_state["paciente"]["curp"])
    with c5:
        st.session_state["paciente"]["ocupacion"] = st.text_input(
            "Ocupación / Profesión", value=st.session_state["paciente"]["ocupacion"])
    with c6:
        st.session_state["paciente"]["telefono"] = st.text_input(
            "Teléfono de Contacto", value=st.session_state["paciente"]["telefono"])
    # SEMIOLOGÍA DEL DOLOR & EVOLUCIÓN
        st.subheader("3. Semiología del Dolor & Evolución")
        col_sem1, col_sem2 = st.columns(2)
        with col_sem1:
            st.session_state["paciente"]["evolucion"] = st.selectbox(
                "Tiempo de Evolución:",
                ["Agudo (< 2 semanas)", "Subagudo (2 - 6 semanas)",
                        "Crónico (> 6 semanas)", "Recidivante"]
            )
            st.session_state["paciente"]["agravantes"] = st.text_area(
                "Factores Agravantes (Posturas, pasajes rápidos, cargas):")
        with col_sem2:
            st.session_state["paciente"]["atenciones_previas"] = st.radio(
                "¿Consultas médicas/fisioterapéuticas previas?", ["No", "Sí"])
            if st.session_state["paciente"]["atenciones_previas"] == "Sí":
                st.session_state["paciente"]["detalle_atenciones"] = st.text_area(
                    "Detalle de diagnósticos o tratamientos previos:")
            st.session_state["paciente"]["mitigantes"] = st.text_area(
                "Factores Mitigantes (Calor, reposo, estiramientos):")

        # IMPACTO EN ACTIVIDADES DE LA VIDA DIARIA
        st.subheader("4. Impacto Funcional en AVD & Actividad Específica")
        st.session_state["paciente"]["dificultades_avd"] = st.multiselect(
            "Selecciona las actividades con restricción o dificultad:",
            [
                "Comer / Alimentarse sin apoyo",
                "Aseo personal / Baño / Peinado",
                "Vestido (Abotonar, calzar)",
                "Manipulación fina / Teclado / Herramientas",
                "Sostener instrumento / Posición de ensayo",
                "Carga de peso / Supermercado",
                "Conducción / Transporte"
            ]
        )
        st.write("---")
        st.header("2. Antecedentes Clínicos Obligatorios (NOM-004-SSA3-2012)")

        col_a, col_b = st.columns(2)
        with col_a:
            st.session_state["paciente"]["ahf"] = st.text_area(
                "Antecedentes Heredofamiliares (AHF)", value=st.session_state["paciente"]["ahf"], height=70)
            st.session_state["paciente"]["app"] = st.text_area(
                "Antecedentes Patológicos (APP)", value=st.session_state["paciente"]["app"], height=70)
        with col_b:
            st.session_state["paciente"]["apnp"] = st.text_area(
                "Antecedentes No Patológicos (APNP)", value=st.session_state["paciente"]["apnp"], height=70)
            st.session_state["paciente"]["pa"] = st.text_area(
                "Padecimiento Actual / Motivo de Consulta", value=st.session_state["paciente"]["pa"], height=70)

        st.write("---")
    # 3. MAPA CORPORAL INTERACTIVO & EXAMEN NEUROLÓGICO
        st.header("3. Mapa Corporal Interactivo (Body Chart) & Neurología")

        col_mapa, col_herramientas = st.columns([3, 1])

        with col_herramientas:
            st.markdown("**Herramientas de Anotación**")
            tipo_sintoma = st.radio(
                "Tipo de Marcador:",
                ["🔴 Dolor Agudo / Localizado", "🔵 Parestesia / Hormigueo",
                    "🟡 Punto Gatillo / Referido", "🟢 Irradiación / Dermatoma"]
            )

            color_map = {
                "🔴 Dolor Agudo / Localizado": "#FF0000",
                "🔵 Parestesia / Hormigueo": "#0088FF",
                "🟡 Punto Gatillo / Referido": "#FFCC00",
                "🟢 Irradiación / Dermatoma": "#00CC44"
            }
            stroke_color = color_map[tipo_sintoma]
            stroke_width = st.slider("Grosor del Trazo:", 1, 15, 4)
            drawing_mode = st.selectbox(
                "Modo de Dibujo:", ["freedraw", "line", "rect", "circle", "transform"])
    try:
                with col_mapa:
                    st.markdown("**Rellena o Dibuja las zonas sobre el Esquema Corporal:**")

                    import streamlit.elements.image as st_image
                    import base64
                    from io import BytesIO
                    from PIL import Image

                    def _image_to_url_patch(image, width, clamp, channels, output_format, image_id):
                        buffered = BytesIO()
                        image.save(buffered, format="PNG")
                        img_str = base64.b64encode(buffered.getvalue()).decode()
                        return f"data:image/png;base64,{img_str}"

                    st_image.image_to_url = _image_to_url_patch

                    try:
                        bg_image = Image.open("human_body.png").convert("RGBA")
                        bg_image = bg_image.resize((600, 500))
                    except Exception:
                        bg_image = Image.new("RGBA", (600, 500), (255, 255, 255, 255))

                    canvas_result = st_canvas(
                        fill_color="rgba(255, 165, 0, 0.3)",
                        stroke_width=stroke_width,
                        stroke_color=stroke_color,
                        background_image=bg_image,
                        height=500,
                        width=600,
                        drawing_mode=drawing_mode,
                        key="body_chart_canvas",
                    )
    except NameError:
            pass
    st.write("---")
    col_neuro1, col_neuro2, col_neuro3 = st.columns(3)

    with col_neuro1:
        st.markdown("**Dermatomas (Sensibilidad)**")
        st.session_state["paciente"]["dermatomas"] = st.text_area("C5 - T1 / Lumbo-sacro:", placeholder="Ej. C6 Hiperalgesia en dermatoma radial...", key="dermatomas_input")

    with col_neuro2:
        st.markdown("**Miotomas (Fuerza)**")
        st.session_state["paciente"]["miotomas"] = st.text_area("Evaluación Motora:", placeholder="Ej. C5 (Deltoides) 5/5, C6 (Bíceps) 4/5...", key="miotomas_input")

    with col_neuro3:
        st.markdown("**Reflejos Osteotendinosos (ROTs)**")
        st.session_state["paciente"]["rots"] = st.text_area("Respuestas Reflejas:", placeholder="Ej. Bicipital (++), Tricipital (++)...", key="rots_input")

    st.write("---")
    st.header("4. Prescripción Basada en Evidencia y Especialidad")

    # Carga de datos dinámicos según la especialidad activa
    dict_esp = DATOS_ESPECIALIDADES.get(especialidad_sel, {
        "diagnosticos": [], "pruebas": [], "ejercicios": [], "aditamentos": []
    })

    opciones_diag = dict_esp["diagnosticos"] + ["Otro / Personalizado..."]
    diag_sel = st.selectbox("🩺 Diagnóstico Presuntivo / Sospechado Sugerido:", opciones_diag)
    st.session_state["paciente"]["diagnostico_sospechado"] = diag_sel

    if diag_sel == "Otro / Personalizado...":
        st.session_state["paciente"]["custom_diagnostico"] = st.text_input("Escribe el diagnóstico personalizado:")

    st.subheader(f"🧪 Pruebas Validadas ({especialidad_sel})")
    sel_pruebas = st.multiselect("Selecciona pruebas (+):", options=dict_esp["pruebas"])
    st.session_state["paciente"]["pruebas_seleccionadas"] = sel_pruebas

    st.subheader(f"🏋️ Ejercicios Prescritos ({especialidad_sel})")
    sel_ejercicios = st.multiselect("Selecciona ejercicios:", options=dict_esp["ejercicios"])
    st.session_state["paciente"]["ejercicios_seleccionados"] = sel_ejercicios

    st.subheader(f"🎒 Aditamentos Prescritos ({especialidad_sel})")
    sel_aditamentos = st.multiselect("Selecciona aditamentos:", options=dict_esp["aditamentos"])
    st.session_state["paciente"]["aditamentos_prescritos"] = sel_aditamentos
    st.write("---")
    st.subheader("5. Exportación de Reporte Clínico (NOM-004)")

    if st.button("📄 Generar Expediente PDF"):
            datos_terapeuta = {
                "nombre": st.session_state.get("nombre_terapeuta", "Lic. Jorge Flores"),
                "cedula": st.session_state.get("cedula_terapeuta", "Por definir"),
                "institucion": st.session_state.get("institucion_terapeuta", "UNAM"),
                "especialidad": st.session_state.get("especialidad_activa", "Fisioterapia en Músicos & Artes Escénicas")
            }
            
            paciente_dict = st.session_state.get("paciente", {})
            datos_paciente = {
                "nombre": paciente_dict.get("nombre", "Paciente de Ejemplo"),
                "edad": paciente_dict.get("edad", "N/A"),
                "sexo": paciente_dict.get("sexo", "N/A"),
                "ocupacion": paciente_dict.get("ocupacion", "Músico"),
                "fecha": "2026-08-22"
            }
            
            historia_clinica = {
                "anamnesis": paciente_dict.get("pa", "Sin registro de padecimiento actual."),
                "exploracion": f"Dermatomas: {paciente_dict.get('dermatomas', 'N/A')}\nMiotomas: {paciente_dict.get('miotomas', 'N/A')}\nROTs: {paciente_dict.get('rots', 'N/A')}",
                "diagnostico": st.session_state.get("diagnostico_text", "Síndrome de sobreuso neuromuscular"),
                "diagnostico_funcional": st.session_state.get("diag_funcional_text", "Deficiencia en control motor fino y tolerancia a la carga postural"),
                "pronostico": st.session_state.get("pronostico_text", "Favorable para la función"),
                "plan": st.session_state.get("plan_text", "Terapia manual, dosificación de carga de ensayo y reeducación postural")
            }
            
            pdf_buffer = generar_pdf_expediente(datos_terapeuta, datos_paciente, historia_clinica)
            
            st.download_button(
                label="⬇️ Descargar Expediente Clínico PDF",
                data=pdf_buffer,
                file_name=f"Expediente_{datos_paciente['nombre'].replace(' ', '_')}.pdf",
                mime="application/pdf"
            )
# MÓDULO: NOTAS DE EVOLUCIÓN (SOAP)
if modulo_trabajo == "📝 Notas de Evolución (SOAP)":
    st.caption("Registra el seguimiento técnico continuo por cada sesión de tratamiento.")

    if not st.session_state["paciente"]["curp"]:
        st.warning("⚠️ Selecciona o carga un paciente activo desde el Gestor de Pacientes para vincular esta nota.")
    else:
        st.info(f"👤 Paciente Activo: **{st.session_state['paciente']['nombre']}** (CURP: {st.session_state['paciente']['curp']})")
        
        s_input = st.text_area("S - Subjetivo:", placeholder="Síntomas referidos por el paciente, variación de EVA de dolor, sensaciones...")
        o_input = st.text_area("O - Objetivo:", placeholder="Hallazgos objetivos de goniometría, pruebas repetidas, carga soportada en kg...")
        a_input = st.text_area("A - Análisis / Evaluación:", placeholder="Análisis clínico del progreso, respuesta al tratamiento anterior...")
        p_input = st.text_area("P - Plan:", placeholder="Ajustes a la dosificación de carga, nuevos ejercicios prescritos, indicación para casa...")

        if st.button("💾 Guardar Nota SOAP en Historial"):
            guardar_nota_soap(st.session_state["paciente"]["curp"], s_input, o_input, a_input, p_input)
            st.success("✅ Nota de evolución SOAP guardada con éxito.")

        st.write("---")
        st.subheader("📜 Historial de Evolución del Paciente")
        notas_previas = obtener_notas_soap(st.session_state["paciente"]["curp"])
        
        if notas_previas:
            for fecha, s, o, a, p in notas_previas:
                with st.expander(f"📅 Sesión: {fecha}"):
                    st.write(f"**S:** {s}")
                    st.write(f"**O:** {o}")
                    st.write(f"**A:** {a}")
                    st.write(f"**P:** {p}")
        else:
            st.write("No hay notas previas para este paciente.")

# MÓDULO CALCULADORAS
elif modulo_trabajo == "📊 Calculadoras Clínicas & Escalas":
    st.header("📊 Calculadoras Clínicas & Escalas Funcionales Validadas")

    tab_quickdash, tab_visa, tab_oswestry, tab_1rm = st.tabs([
        "🎸 QuickDASH (Miembro Superior)", 
        "🦵 Rodilla & Miembro Inferior (VISA / KOOS-12)", 
        "🦴 Oswestry (ODI Lumbar)", 
        "🏋️ Calculadora 1RM"
    ])

    # 1. QuickDASH
    with tab_quickdash:
        st.subheader("Escala QuickDASH (Discapacidad de Hombro, Codo y Mano)")
        st.caption("Puntuación de 0 (sin discapacidad) a 100 (discapacidad severa). Evaluado en escala Likert 1-5.")
        
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
        
        if score_quickdash < 25:
            st.success("Discapacidad leve o nula. Función conservada.")
        elif score_quickdash < 50:
            st.warning("Discapacidad moderada. Requiere adaptación ergonómica y manejo analgésico/postural.")
        else:
            st.error("Discapacidad severa. Restricción funcional marcada de miembro superior.")
            
        st.session_state["paciente"]["quickdash_score"] = score_quickdash

    # 2. Rodilla & Miembro Inferior (VISA / KOOS-12)
    with tab_visa:
        subtab_visa, subtab_koos = st.tabs(["🦵 Cuestionario VISA (Tendinopatías)", "🦴 Escala KOOS-12 (Rodilla)"])
        
        with subtab_visa:
            tipo_visa = st.radio("Selecciona la escala:", ["VISA-A (Aquilea)", "VISA-P (Patelar)"], horizontal=True)
            st.caption("Puntuación de 0 a 100 puntos. A menor puntuación, mayor severidad de la tendinopatía.")
            
            v1 = st.slider("1. Dolor en reposo o rigidez matutina (0 = Severo, 10 = Sin dolor)", 0, 10, 10, key="v1")
            v2 = st.slider("2. Dolor al estirar o realizar carga estática (0 = Severo, 10 = Sin dolor)", 0, 10, 10, key="v2")
            v3 = st.slider("3. Dolor al realizar marcha continua o escaleras (0 = Severo, 10 = Sin dolor)", 0, 10, 10, key="v3")
            v4 = st.slider("4. Capacidad de realizar saltos o carga pliométrica (0 = Imposible, 10 = Sin problema)", 0, 10, 10, key="v4")
            v5 = st.slider("5. Rendimiento en su práctica deportiva / ensayo activo (0 = Suspendido, 20 = 100%)", 0, 20, 20, key="v5")
            
            score_visa = v1 + v2 + v3 + v4 + v5
            st.metric(f"Puntaje Total {tipo_visa}", f"{score_visa} / 60 pts parciales")
            st.session_state["paciente"]["visa_score"] = f"{tipo_visa}: {score_visa}/60"

        with subtab_koos:
            st.subheader("KOOS-12 (Knee Injury and Osteoarthritis Outcome Score)")
            st.caption("Puntuación estandarizada de 0 a 100%. A mayor puntaje, mejor función clínica de la rodilla.")
            
            k_dolor = st.slider("1. Frecuencia / Intensidad del dolor al cargar peso o flexionar la rodilla:", 0, 4, 0, 
                                format_func=lambda x: {0: "0: Ninguno", 1: "1: Leve", 2: "2: Moderado", 3: "3: Severo", 4: "4: Extremo"}[x])
            k_rigidez = st.slider("2. Rigidez articular al despertarse o tras estar sentado:", 0, 4, 0,
                                format_func=lambda x: {0: "0: Sin rigidez", 1: "1: Leve", 2: "2: Moderada", 3: "3: Severa", 4: "4: Extrema"}[x])
            k_escaleras = st.slider("3. Dificultad para subir o bajar escaleras:", 0, 4, 0,
                                format_func=lambda x: {0: "0: Ninguna", 1: "1: Leve", 2: "2: Moderada", 3: "3: Severa", 4: "4: Extrema"}[x])
            k_impacto = st.slider("4. Dificultad para correr, saltar o hacer giros/pivotes:", 0, 4, 0,
                                format_func=lambda x: {0: "0: Ninguna", 1: "1: Leve", 2: "2: Moderada", 3: "3: Severa", 4: "4: Extrema"}[x])
            k_qol = st.slider("5. ¿Falta de confianza o conciencia constante de la rodilla en el día a día?:", 0, 4, 0,
                                format_func=lambda x: {0: "0: En absoluto", 1: "1: Un poco", 2: "2: Moderado", 3: "3: Mucho", 4: "4: Totalmente"}[x])
            
            suma_koos = k_dolor + k_rigidez + k_escaleras + k_impacto + k_qol
            score_koos = 100 - ((suma_koos / 20) * 100)
            
            st.metric("Puntaje Funcional KOOS-12", f"{score_koos:.1f}%")
            
            if score_koos >= 80:
                st.success("Función articular de rodilla óptima o con afectación mínima.")
            elif score_koos >= 50:
                st.warning("Compromiso funcional moderado. Indicado trabajo de estabilidad dinámica y fuerza.")
            else:
                st.error("Limitación funcional severa en articulación de rodilla.")
                
            st.session_state["paciente"]["koos_score"] = f"{score_koos:.1f}%"

    # 3. Oswestry (ODI)
    with tab_oswestry:
        st.subheader("Índice de Incapacidad Lumbar de Oswestry (ODI)")
        st.caption("Evaluación de la limitación funcional por lumbalgia.")
        
        o1 = st.selectbox("1. Intensidad del dolor:", ["0: Puedo soportarlo sin analgésicos", "1: Es malo pero me arreglo", "2: Moderado", "3: Bastante severo", "4: Muy severo", "5: El peor dolor imaginable"])
        o2 = st.selectbox("2. Cuidados personales (lavarse, vestirse):", ["0: Sin dolor extra", "1: Normal pero produce dolor", "2: Lento y con cuidado", "3: Necesito alguna ayuda", "4: Necesito ayuda en la mayoría", "5: No puedo vestirme"])
        o3 = st.selectbox("3. Levantar peso:", ["0: Puedo levantar objetos pesados", "1: Solo si están bien posicionados", "2: Solo si son ligeros", "3: Solo peso muy ligero", "4: Casi nada", "5: Incapaz de levantar nada"])
        
        puntos_odi = int(o1[0]) + int(o2[0]) + int(o3[0])
        score_odi = (puntos_odi / 15) * 100
        
        st.metric("Puntaje de Incapacidad Lumbar", f"{score_odi:.1f}%")
        st.session_state["paciente"]["odi_score"] = f"{score_odi:.1f}%"

    # 4. Calculadora de 1RM
    with tab_1rm:
        st.subheader("Calculadora Terapéutica 1RM (Brzycki)")
        c1, c2 = st.columns(2)
        peso_movido = c1.number_input("Carga Levantada (kg):", min_value=1.0, value=20.0)
        reps_completadas = c2.number_input("Repeticiones (1-12):", min_value=1, max_value=12, value=8)
        
        uno_rm_b = peso_movido / (1.0278 - (0.0278 * reps_completadas))
        st.info(f"🏋️ **1RM Estimada (Brzycki): {uno_rm_b:.1f} kg**")
        st.session_state["paciente"]["resultado_1rm"] = f"1RM Estimada: {uno_rm_b:.1f} kg"
# MÓDULO ANÁLISIS POSE IA
elif modulo_trabajo == "Análisis Biomecánico & IA Pose":
    st.header("📐 Goniometría Digital por IA")
    archivo_imagen = st.camera_input("Capturar articulación")
    if archivo_imagen is not None and st.button("🤖 Autodetectar con YOLO Pose"):
        img_proc, angulo = procesar_pose_yolo(archivo_imagen, st.session_state["goniometria"]["articulacion"])
        if img_proc is not None:
            st.session_state["foto_procesada_ia"] = img_proc
            st.session_state["goniometria"]["grados_activos"] = int(angulo)

    if st.session_state["foto_procesada_ia"] is not None:
        st.image(st.session_state["foto_procesada_ia"], use_container_width=True)
        st.success(f"🎯 Ángulo Calculado: {st.session_state['goniometria']['grados_activos']}°")

# MÓDULO COLUMNA Y ESCOLIOSIS
elif modulo_trabajo == "Análisis de Columna & Escoliosis":
    st.header("🦴 Análisis de Columna & Escoliosis")
    archivo_imagen = st.camera_input("Capturar postura posterior")
    if archivo_imagen is not None and st.button("🤖 Analizar Eje Espinal"):
        img_proc, desv = procesar_columna_escoliosis(archivo_imagen)
        if img_proc is not None:
            st.session_state["foto_procesada_ia"] = img_proc
            st.session_state["goniometria"]["grados_activos"] = int(desv)

    if st.session_state["foto_procesada_ia"] is not None:
        st.image(st.session_state["foto_procesada_ia"], use_container_width=True)
        st.success(f"🎯 Desviación Espinal: {st.session_state['goniometria']['grados_activos']}°")

# MÓDULO FIRMA Y EXPORTACIÓN PDF
elif modulo_trabajo == "Firma & Exportación PDF":
    st.header("✍️ Consentimiento Informado & Firma Digital")
    canvas_firma_paciente = st_canvas(
        fill_color="rgba(255, 165, 0, 0.3)", stroke_width=2.0, stroke_color="#000000",
        background_color="#FFFFFF", height=170, width=450, drawing_mode="freedraw", key="canvas_firma"
    )
    if canvas_firma_paciente.image_data is not None:
        st.session_state["firma_paciente"] = canvas_firma_paciente.image_data

    st.write("---")
    pdf_bytes = generar_pdf()
    nombre_archivo = f"Expediente_{st.session_state['paciente']['nombre'].replace(' ', '_')}.pdf" if st.session_state['paciente']['nombre'] else "Expediente_Paciente.pdf"
    
    st.download_button(
        label="📄 Exportar Expediente Clínico Completo (PDF)",
        data=pdf_bytes, file_name=nombre_archivo, mime="application/pdf"
    )

st.stop()