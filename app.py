import streamlit as st
import google.generativeai as genai

from config.settings import GEMINI_API_KEY

# -------------------------------
# Configure Gemini
# -------------------------------
genai.configure(api_key=GEMINI_API_KEY)

model = genai.GenerativeModel("gemini-2.5-flash")

# -------------------------------
# Streamlit Page Configuration
# -------------------------------
st.set_page_config(
    page_title="Synthetic User Generation Platform",
    page_icon="👤",
    layout="wide"
)

# -------------------------------
# Sidebar
# -------------------------------
st.sidebar.title("📌 Navigation")

st.sidebar.info(
    "Fill in the details below and click **Generate Synthetic User**."
)

st.sidebar.markdown("---")

st.sidebar.header("About")

st.sidebar.write("""
This platform generates realistic synthetic users using **Google Gemini AI**.

### Use Cases
- UI/UX Testing
- User Research
- Product Design
- Machine Learning
- Data Analytics
""")

# -------------------------------
# Main Title
# -------------------------------
st.title("👤 Synthetic User Generation Platform")

st.markdown(
    "Generate realistic synthetic user personas using **Google Gemini AI**."
)

# -------------------------------
# User Inputs
# -------------------------------
age = st.number_input(
    "Age",
    min_value=18,
    max_value=100,
    value=25
)

gender = st.selectbox(
    "Gender",
    ["Male", "Female", "Other"]
)

profession = st.text_input(
    "Profession"
)

location = st.text_input(
    "Location"
)

interests = st.text_area(
    "Interests"
)

# -------------------------------
# Generate Button
# -------------------------------
if st.button("🚀 Generate Synthetic User", use_container_width=True):

    prompt = f"""
You are an expert UX researcher.

Generate ONE realistic synthetic user persona.

Return the result in a clean markdown format.

Age: {age}

Gender: {gender}

Profession: {profession}

Location: {location}

Interests: {interests}

Include the following sections:

# Name

# Bio

# Personality Traits

# Lifestyle

# Hobbies

# Goals

# Pain Points

# Buying Behaviour

# Technology Usage
"""

    try:

        with st.spinner("Generating synthetic user..."):

            response = model.generate_content(prompt)

        st.session_state["persona"] = response.text

        st.success("✅ Synthetic User Generated Successfully!")

        st.balloons()

    except Exception as e:

        st.error(f"Error: {e}")

# -------------------------------
# Display Persona
# -------------------------------
if "persona" in st.session_state:

    st.subheader("📋 Generated Synthetic User")

    st.markdown("---")

    st.markdown(st.session_state["persona"])

# -------------------------------
# Reset Button
# -------------------------------
if st.button("🔄 Reset"):

    st.session_state.clear()

    st.rerun()

# -------------------------------
# Footer
# -------------------------------
st.markdown("---")

st.caption("© 2026 Synthetic User Generation Platform | Streamlit + Gemini AI")