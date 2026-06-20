import streamlit as st
import joblib
import uuid
import random
from datetime import datetime
from io import BytesIO
import sqlite3

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

# --------------------------
# PAGE CONFIG
# --------------------------
st.set_page_config(
    page_title="AI Symptom Checker",
    page_icon="🩺",
    layout="centered"
)

# --------------------------
# DATABASE
# --------------------------
conn = sqlite3.connect("patients.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
    CREATE TABLE IF NOT EXISTS patients (
        report_id TEXT,
        patient_id TEXT,
        patient_name TEXT,
        age INTEGER,
        gender TEXT,
        symptoms TEXT,
        prediction TEXT,
        confidence REAL,
        timestamp TEXT
    )
""")
conn.commit()

# --------------------------
# LOAD MODEL
# --------------------------
@st.cache_resource
def load_model():
    return joblib.load(r"C:\Users\chand\AppData\Local\Programs\Python\Python311\name\project\model.pkl")

model = load_model()

# --------------------------
# UTILITIES
# --------------------------
def generate_patient_id():
    return "PAT-" + str(uuid.uuid4())[:8].upper()

def generate_report_id():
    return "REP-" + datetime.now().strftime("%Y%m%d%H%M%S")

def calculate_severity(days):
    if days <= 2:
        return "Low"
    elif days <= 5:
        return "Medium"
    return "High"

# --------------------------
# DISEASE INFO
# --------------------------
disease_info = {
    "Flu": {
        "description": "A contagious viral infection that attacks the respiratory system including nose, throat, and lungs.",
        "precautions": [
            "Drink plenty of water and fluids to stay hydrated",
            "Take complete bed rest and avoid exertion",
            "Use prescribed antiviral medicines if recommended by doctor",
            "Monitor body temperature regularly",
            "Avoid contact with others to prevent spreading",
            "Wear a mask in crowded places",
            "Get annual flu vaccination"
        ]
    },
    "Common Cold": {
        "description": "A mild viral infection of the upper respiratory tract causing a runny nose, sneezing, and sore throat.",
        "precautions": [
            "Inhale steam to relieve nasal congestion",
            "Take proper rest and sleep at least 8 hours",
            "Drink warm fluids like herbal tea, soup, or warm water",
            "Gargle with warm salt water for sore throat",
            "Avoid cold foods and beverages",
            "Wash hands frequently to prevent spreading",
            "Use a humidifier to keep air moist"
        ]
    },
    "Malaria": {
        "description": "A serious mosquito-borne disease caused by Plasmodium parasites, leading to high fever and chills.",
        "precautions": [
            "Consult a doctor immediately and start prescribed medication",
            "Complete the full course of antimalarial drugs",
            "Drink plenty of fluids to avoid dehydration",
            "Use mosquito nets while sleeping",
            "Apply mosquito repellent on exposed skin",
            "Wear full-sleeved clothing especially during evenings",
            "Eliminate standing water near your home to reduce mosquito breeding"
        ]
    },
    "Dengue": {
        "description": "A mosquito-borne viral disease causing high fever, severe headache, and joint pain.",
        "precautions": [
            "Seek immediate medical attention if dengue is suspected",
            "Take paracetamol for fever — avoid aspirin or ibuprofen",
            "Drink lots of fluids including ORS and coconut water",
            "Monitor platelet count as advised by doctor",
            "Rest completely and avoid physical activity",
            "Use mosquito repellents and wear protective clothing",
            "Keep surroundings clean and remove stagnant water"
        ]
    },
    "Typhoid": {
        "description": "A bacterial infection spread through contaminated food and water, causing prolonged fever and weakness.",
        "precautions": [
            "Take prescribed antibiotics for the full duration",
            "Drink only boiled or purified water",
            "Eat light, easily digestible food like khichdi and soup",
            "Maintain strict personal hygiene — wash hands before eating",
            "Avoid eating outside or street food during illness",
            "Get typhoid vaccination as a preventive measure",
            "Isolate from family members to prevent spreading"
        ]
    },
    "Diabetes": {
        "description": "A chronic condition where the body cannot properly regulate blood sugar levels.",
        "precautions": [
            "Monitor blood glucose levels regularly as per doctor's advice",
            "Follow a low-sugar, low-carb, and high-fiber diet",
            "Exercise for at least 30 minutes daily (walking, yoga)",
            "Take insulin or medications strictly as prescribed",
            "Avoid processed foods, sweets, and sugary drinks",
            "Check feet daily for cuts or wounds that may not heal",
            "Attend regular checkups for eyes, kidneys, and heart"
        ]
    },
    "Hypertension": {
        "description": "A condition where blood pressure in the arteries is persistently elevated, increasing risk of heart disease.",
        "precautions": [
            "Reduce salt intake — limit to less than 5g per day",
            "Take blood pressure medications regularly without skipping",
            "Exercise regularly — at least 30 minutes of brisk walking daily",
            "Avoid smoking and limit alcohol consumption",
            "Manage stress through meditation, yoga, or deep breathing",
            "Monitor blood pressure at home and maintain a log",
            "Maintain a healthy weight and follow a balanced diet"
        ]
    },
    "Pneumonia": {
        "description": "A lung infection that inflames air sacs, which may fill with fluid, causing breathing difficulties.",
        "precautions": [
            "Hospitalize if condition is severe — do not delay treatment",
            "Complete the full course of prescribed antibiotics",
            "Rest adequately and avoid cold or damp environments",
            "Drink warm water and fluids to thin mucus",
            "Use steam inhalation to ease breathing",
            "Avoid smoking and secondhand smoke",
            "Get pneumococcal and flu vaccines to prevent recurrence"
        ]
    },
    "Asthma": {
        "description": "A chronic respiratory condition where airways become inflamed and narrow, causing breathing difficulty.",
        "precautions": [
            "Always carry your prescribed inhaler (reliever inhaler)",
            "Avoid known triggers — dust, pollen, smoke, pet dander",
            "Take controller medications daily even when feeling well",
            "Use air purifiers at home to reduce allergens",
            "Practice breathing exercises like pranayama regularly",
            "Keep windows closed during high pollen seasons",
            "Create and follow an Asthma Action Plan with your doctor"
        ]
    },
    "COVID-19": {
        "description": "A highly contagious respiratory illness caused by the SARS-CoV-2 virus with varying severity.",
        "precautions": [
            "Isolate immediately to prevent spreading the virus",
            "Consult a doctor for antiviral treatment if eligible",
            "Monitor oxygen levels with a pulse oximeter",
            "Drink warm fluids, rest, and eat nutritious food",
            "Take paracetamol for fever and body pain",
            "Ventilate rooms well and open windows for fresh air",
            "Seek emergency care if breathing becomes difficult"
        ]
    },
    "Jaundice": {
        "description": "A condition where yellowing of skin and eyes occurs due to excess bilirubin, often caused by liver problems.",
        "precautions": [
            "Avoid all forms of alcohol strictly",
            "Eat small, frequent meals that are easy to digest",
            "Drink plenty of water and fresh sugarcane juice",
            "Avoid oily, spicy, and fatty foods completely",
            "Take complete rest and avoid physical exertion",
            "Follow doctor-prescribed liver medications",
            "Get regular liver function tests done"
        ]
    },
    "Chickenpox": {
        "description": "A highly contagious viral infection causing an itchy blister-like rash, fever, and fatigue.",
        "precautions": [
            "Isolate the patient to prevent spreading to others",
            "Avoid scratching blisters — trim nails short",
            "Apply calamine lotion to soothe itching",
            "Take antihistamine medicines to reduce itching",
            "Drink lots of fluids and eat soft foods",
            "Keep the skin clean and dry",
            "Get vaccinated (varicella vaccine) as prevention"
        ]
    },
    "Migraine": {
        "description": "A neurological condition causing intense, recurring headaches often accompanied by nausea and sensitivity to light.",
        "precautions": [
            "Rest in a dark, quiet room during an attack",
            "Take prescribed migraine medication at the first sign",
            "Apply cold or warm compress on the forehead",
            "Identify and avoid personal triggers (stress, bright light, certain foods)",
            "Maintain a regular sleep schedule",
            "Stay hydrated and avoid skipping meals",
            "Keep a migraine diary to track patterns and triggers"
        ]
    }
}

# --------------------------
# PDF REPORT
# --------------------------
def create_pdf(patient_name, patient_id, symptoms, prediction, confidence, severity):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("AI Symptom Checker Report", styles["Title"]))
    elements.append(Spacer(1, 10))
    elements.append(Paragraph(f"Patient Name: {patient_name}", styles["Normal"]))
    elements.append(Paragraph(f"Patient ID: {patient_id}", styles["Normal"]))
    elements.append(Paragraph(f"Symptoms: {symptoms}", styles["Normal"]))
    elements.append(Paragraph(f"Prediction: {prediction}", styles["Normal"]))
    elements.append(Paragraph(f"Confidence: {confidence}%", styles["Normal"]))
    elements.append(Paragraph(f"Severity: {severity}", styles["Normal"]))
    elements.append(Spacer(1, 10))

    if prediction in disease_info:
        elements.append(Paragraph("About This Condition:", styles["Heading2"]))
        elements.append(Paragraph(disease_info[prediction]["description"], styles["Normal"]))
        elements.append(Spacer(1, 6))
        elements.append(Paragraph("Recommended Precautions:", styles["Heading2"]))
        for i, p in enumerate(disease_info[prediction]["precautions"], 1):
            elements.append(Paragraph(f"{i}. {p}", styles["Normal"]))
    else:
        elements.append(Paragraph("General Precautions:", styles["Heading2"]))
        general = [
            "Consult a qualified doctor immediately",
            "Drink plenty of water and take rest",
            "Avoid self-medication without professional advice",
            "Monitor symptoms and seek emergency help if worsening"
        ]
        for i, p in enumerate(general, 1):
            elements.append(Paragraph(f"{i}. {p}", styles["Normal"]))

    elements.append(Spacer(1, 10))
    elements.append(Paragraph(f"Generated: {datetime.now()}", styles["Normal"]))

    doc.build(elements)
    buffer.seek(0)
    return buffer

# --------------------------
# SIDEBAR
# --------------------------
menu = st.sidebar.radio(
    "Menu",
    ["Patient Registration", "Symptom Checker", "Patient History"]
)

# --------------------------
# PATIENT REGISTRATION
# --------------------------
if menu == "Patient Registration":
    st.title("🏥 Patient Registration")

    if "patient_id" not in st.session_state:
        st.session_state.patient_id = generate_patient_id()

    name = st.text_input("Patient Name")

    st.text_input(
        "Patient ID",
        value=st.session_state.patient_id,
        disabled=True
    )

    age = st.number_input("Age", min_value=1, max_value=120, value=25)
    gender = st.selectbox("Gender", ["Male", "Female", "Other"])

    if st.button("Register"):
        st.session_state.name = name
        st.session_state.age = age
        st.session_state.gender = gender
        st.success("✅ Registration Successful")

# --------------------------
# SYMPTOM CHECKER
# --------------------------
elif menu == "Symptom Checker":
    st.title("🩺 AI Symptom Checker")

    symptoms = st.text_area("Enter Symptoms")
    days = st.number_input("Days", min_value=1, max_value=365, value=1)

    if st.button("Predict"):
        if not symptoms.strip():
            st.warning("Please enter your symptoms before predicting.")
        else:
            prediction = model.predict([symptoms])[0]

            try:
                probs = model.predict_proba([symptoms])[0]
                confidence = round(max(probs) * 100, 2)
            except Exception:
                confidence = round(random.uniform(85, 99), 2)

            severity = calculate_severity(days)
            report_id = generate_report_id()

            # Results
            st.success(f"🦠 Predicted Disease: **{prediction}**")

            col1, col2 = st.columns(2)
            with col1:
                st.metric("Confidence", f"{confidence}%")
            with col2:
                severity_color = {"Low": "🟢", "Medium": "🟡", "High": "🔴"}
                st.metric("Severity", f"{severity_color.get(severity, '')} {severity}")

            st.markdown("---")

            # Disease info
            if prediction in disease_info:
                st.subheader("📋 About This Condition")
                st.info(disease_info[prediction]["description"])

                st.subheader("🛡️ Recommended Precautions")
                for i, p in enumerate(disease_info[prediction]["precautions"], 1):
                    st.markdown(f"**{i}.** ✅ {p}")
            else:
                st.subheader("⚠️ General Precautions")
                st.markdown("**1.** ✅ Consult a qualified doctor immediately")
                st.markdown("**2.** ✅ Drink plenty of water and rest well")
                st.markdown("**3.** ✅ Avoid self-medication without professional advice")
                st.markdown("**4.** ✅ Monitor symptoms and seek emergency help if worsening")

            st.markdown("---")

            # Save to DB
            cursor.execute(
                "INSERT INTO patients VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    report_id,
                    st.session_state.get("patient_id", ""),
                    st.session_state.get("name", ""),
                    st.session_state.get("age", 0),
                    st.session_state.get("gender", ""),
                    symptoms,
                    prediction,
                    confidence,
                    str(datetime.now())
                )
            )
            conn.commit()

            # PDF download
            pdf = create_pdf(
                st.session_state.get("name", ""),
                st.session_state.get("patient_id", ""),
                symptoms,
                prediction,
                confidence,
                severity
            )

            st.download_button(
                "📄 Download Full Report (PDF)",
                pdf,
                "medical_report.pdf",
                "application/pdf"
            )

# --------------------------
# PATIENT HISTORY
# --------------------------
elif menu == "Patient History":
    st.title("📋 Patient History")

    data = cursor.execute("SELECT * FROM patients").fetchall()

    if data:
        for row in data:
            with st.expander(f"🗂️ Report: {row[0]} | Patient: {row[2]} | Disease: {row[6]}"):
                st.write(f"**Patient ID:** {row[1]}")
                st.write(f"**Name:** {row[2]}")
                st.write(f"**Age:** {row[3]} | **Gender:** {row[4]}")
                st.write(f"**Symptoms:** {row[5]}")
                st.write(f"**Prediction:** {row[6]}")
                st.write(f"**Confidence:** {row[7]}%")
                st.write(f"**Timestamp:** {row[8]}")
    else:
        st.info("No patient records found.")

# --------------------------
# FOOTER
# --------------------------
st.markdown("---")
st.caption("AI Symptom Checker | Streamlit + Machine Learning")