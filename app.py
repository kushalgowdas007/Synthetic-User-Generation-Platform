import streamlit as st
import google.generativeai as genai

# Paste your Gemini API Key below
genai.configure(api_key="AQ.Ab8RN6IL9Hiz-y-xjt6p2pkPsb5MIYp4WVAY4WMVmQwM5jAARA")

model = genai.GenerativeModel("gemini-2.5-flash")

st.set_page_config(page_title="Synthetic User Generation Platform")
st.sidebar.title("📌 Navigation")
st.sidebar.info(
    "Fill in the details and click 'Generate Synthetic User' to create a realistic profile using Gemini AI."
)
st.sidebar.markdown("---")
st.sidebar.write("Developed using Streamlit + Gemini AI")

st.sidebar.header("About")

st.sidebar.write("""
This platform generates realistic synthetic users for:
- UI/UX Testing
- Research
- Machine Learning
- Data Analysis
- Product Design
""")

st.title("👤 Synthetic User Generation Platform")
st.markdown(
    "Generate realistic synthetic user profiles using **Google Gemini AI**."
)

age = st.number_input("Age", 18, 100, 25)

gender = st.selectbox(
    "Gender",
    ["Male", "Female", "Other"]
)

profession = st.text_input("Profession")

location = st.text_input("Location")

interests = st.text_area("Interests")

if st.button("🚀 Generate Synthetic User", use_container_width=True):

    prompt = f"""
Generate one realistic synthetic user.

Age: {age}
Gender: {gender}
Profession: {profession}
Location: {location}
Interests: {interests}

Include:
Name
Bio
Personality
Hobbies
Lifestyle
"""

    with st.spinner("Generating synthetic user... Please wait..."):
        response = model.generate_content(prompt)

    st.success("✅ Synthetic User Generated Successfully!")
st.balloons()


st.subheader("📋 Generated Synthetic User")
st.markdown("---")

st.markdown(response.text)

if st.button("🔄 Reset"):
    st.rerun()

    st.markdown("---")
st.caption("© 2026 Synthetic User Generation Platform | Streamlit + Gemini AI")