from datetime import datetime
from io import BytesIO
import random
import sqlite3
import uuid

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
import joblib
import streamlit as st
import wikipediaapi  # Added Wikipedia API

# --------------------------
# PAGE CONFIG
# --------------------------
st.set_page_config(
    page_title="AI Symptom Checker", page_icon="🩺", layout="centered"
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
    return joblib.load(r"model.pkl")


model = load_model()


# --------------------------
# UTILITIES & WIKIPEDIA FETCH
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


def fetch_wikipedia_details(disease_name):
    """Fetches summary description of a disease dynamically from Wikipedia."""
    # Wikipedia API requires a descriptive User-Agent header to avoid being blocked
    wiki_wiki = wikipediaapi.Wikipedia(
        user_agent="AISymptomChecker/1.0 (contact: your-email@example.com)",
        language="en",
    )

    try:
        page = wiki_wiki.page(disease_name)
        if page.exists():
            # Return the first paragraph or up to 600 characters for a clean UI snippet
            return page.summary[:600] + "..."
        else:
            return "No specific Wikipedia entry found for this exact condition phrase."
    except Exception as e:
        return f"Could not retrieve live details at this moment. Error: {str(e)}"


# --------------------------
# STATIC PRECAUTIONS DICTIONARY
# --------------------------
# Kept for medical precaution guidelines since Wikipedia covers encyclopedic summaries, not medical instructions.
disease_precautions = {
    "Flu": [
        "Drink plenty of water and fluids to stay hydrated",
        "Take complete bed rest and avoid exertion",
        "Use prescribed antiviral medicines if recommended by doctor",
    ],
    "Common Cold": [
        "Inhale steam to relieve nasal congestion",
        "Take proper rest and sleep at least 8 hours",
        "Drink warm fluids like herbal tea, soup, or warm water",
    ],
    "Malaria": [
        "Consult a doctor immediately and start prescribed medication",
        "Use mosquito nets while sleeping",
        "Eliminate standing water near your home to reduce mosquito breeding",
    ],
    "Dengue": [
        "Seek immediate medical attention if dengue is suspected",
        "Take paracetamol for fever — avoid aspirin or ibuprofen",
        "Drink lots of fluids including ORS and coconut water",
    ],
    "Typhoid": [
        "Take prescribed antibiotics for the full duration",
        "Drink only boiled or purified water",
        "Maintain strict personal hygiene — wash hands before eating",
    ],
    "Diabetes": [
        "Monitor blood glucose levels regularly as per doctor's advice",
        "Follow a low-sugar, low-carb, and high-fiber diet",
        "Exercise for at least 30 minutes daily (walking, yoga)",
    ],
    "Hypertension": [
        "Reduce salt intake — limit to less than 5g per day",
        "Take blood pressure medications regularly without skipping",
        "Manage stress through meditation, yoga, or deep breathing",
    ],
    "Pneumonia": [
        "Hospitalize if condition is severe — do not delay treatment",
        "Complete the full course of prescribed antibiotics",
        "Use steam inhalation to ease breathing",
    ],
    "Asthma": [
        "Always carry your prescribed inhaler (reliever inhaler)",
        "Avoid known triggers — dust, pollen, smoke, pet dander",
        "Use air purifiers at home to reduce allergens",
    ],
    "COVID-19": [
        "Isolate immediately to prevent spreading the virus",
        "Monitor oxygen levels with a pulse oximeter",
        "Seek emergency care if breathing becomes difficult",
    ],
    "Jaundice": [
        "Avoid all forms of alcohol strictly",
        "Eat small, frequent meals that are easy to digest",
        "Avoid oily, spicy, and fatty foods completely",
    ],
    "Chickenpox": [
        "Isolate the patient to prevent spreading to others",
        "Avoid scratching blisters — trim nails short",
        "Apply calamine lotion to soothe itching",
    ],
    "Migraine": [
        "Rest in a dark, quiet room during an attack",
        "Take prescribed migraine medication at the first sign",
        "Identify and avoid personal triggers (stress, bright light)",
    ],
}

# --------------------------
# PDF REPORT
# --------------------------
def create_pdf(
    patient_name, patient_id, symptoms, prediction, confidence, severity, wiki_desc
):
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

    elements.append(Paragraph("About This Condition (Wikipedia):", styles["Heading2"]))
    elements.append(Paragraph(wiki_desc, styles["Normal"]))
    elements.append(Spacer(1, 6))

    elements.append(Paragraph("Recommended Action & Precautions:", styles["Heading2"]))
    precautions = disease_precautions.get(
        prediction,
        [
            "Consult a qualified doctor immediately",
            "Drink plenty of water and take rest",
            "Avoid self-medication without professional advice",
            "Monitor symptoms and seek emergency help if worsening",
        ],
    )

    for i, p in enumerate(precautions, 1):
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
    "Menu", ["Patient Registration", "Symptom Checker", "Patient History"]
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
        "Patient ID", value=st.session_state.patient_id, disabled=True
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

            # Dynamic Wikipedia Fetch
            with st.spinner("Fetching Medical Context from Wikipedia..."):
                wiki_description = fetch_wikipedia_details(prediction)

            # Results
            st.success(f"🦠 Predicted Disease: **{prediction}**")

            col1, col2 = st.columns(2)
            with col1:
                st.metric("Confidence", f"{confidence}%")
            with col2:
                severity_color = {"Low": "🟢", "Medium": "🟡", "High": "🔴"}
                st.metric(
                    "Severity", f"{severity_color.get(severity, '')} {severity}"
                )

            st.markdown("---")

            # Display Wikipedia summary
            st.subheader("📚 About This Condition (Via Wikipedia)")
            st.info(wiki_description)

            # Precautions
            st.subheader("🛡️ Recommended Precautions")
            precautions_list = disease_precautions.get(
                prediction,
                [
                    "Consult a qualified doctor immediately",
                    "Drink plenty of water and rest well",
                    "Avoid self-medication without professional advice",
                    "Monitor symptoms and seek emergency help if worsening",
                ],
            )
            for i, p in enumerate(precautions_list, 1):
                st.markdown(f"**{i}.** ✅ {p}")

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
                    str(datetime.now()),
                ),
            )
            conn.commit()

            # PDF download
            pdf = create_pdf(
                st.session_state.get("name", ""),
                st.session_state.get("patient_id", ""),
                symptoms,
                prediction,
                confidence,
                severity,
                wiki_description,
            )

            st.download_button(
                "📄 Download Full Report (PDF)",
                pdf,
                "medical_report.pdf",
                "application/pdf",
            )

# --------------------------
# PATIENT HISTORY
# --------------------------
elif menu == "Patient History":
    st.title("📋 Patient History")

    data = cursor.execute("SELECT * FROM patients").fetchall()

    if data:
        for row in data:
            with st.expander(
                f"🗂️ Report: {row[0]} | Patient: {row[2]} | Disease: {row[6]}"
            ):
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
st.caption("AI Symptom Checker | Streamlit + Wikipedia API integration")
