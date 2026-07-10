import streamlit as st
import time

# --------------------------------------------------
# Page Configuration
# --------------------------------------------------
st.set_page_config(
    page_title="Experiment Workspace",
    page_icon="🧪",
    layout="wide"
)

# --------------------------------------------------
# Sidebar
# --------------------------------------------------
with st.sidebar:
    st.title("🧪 Experiment Workspace")

    st.markdown("---")

    st.subheader("📌 Workspace Guide")

    st.write("""
Complete the experiment configuration before generating synthetic user personas.

### Steps
1. Enter experiment details
2. Select the industry
3. Choose simulation type
4. Set persona count
5. Generate personas
6. Continue to Survey Module
""")

# --------------------------------------------------
# Main Heading
# --------------------------------------------------
st.title("🧪 Experiment Workspace")

st.write(
    "Configure your experiment before generating synthetic user personas."
)

# --------------------------------------------------
# Experiment Form
# --------------------------------------------------
with st.form("experiment_form"):

    st.subheader("📝 Experiment Information")

    experiment_name = st.text_input(
        "🧪 Experiment Name",
        placeholder="e.g., Mobile Banking User Research"
    )

    product_name = st.text_input(
        "📦 Product Name",
        placeholder="e.g., FinBank Mobile App"
    )

    description = st.text_area(
        "📝 Description",
        placeholder="Briefly describe the product or experiment..."
    )

    target_audience = st.text_area(
        "🎯 Target Audience",
        placeholder="e.g., College students aged 18–25"
    )

    research_objective = st.text_area(
        "🔍 Research Objective",
        placeholder="What do you want to learn from this experiment?"
    )

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        industry = st.selectbox(
            "🏭 Industry",
            [
                "Technology",
                "Healthcare",
                "Education",
                "Finance",
                "E-commerce",
                "Retail",
                "Travel",
                "Entertainment",
                "Manufacturing",
                "Other"
            ]
        )

    with col2:
        persona_count = st.number_input(
            "👥 Persona Count",
            min_value=1,
            max_value=50,
            value=5
        )

    simulation_type = st.selectbox(
        "⚙️ Simulation Type",
        [
            "Customer Persona",
            "Employee Persona",
            "Student Persona",
            "Healthcare Persona",
            "Shopper Behavior",
            "General User"
        ]
    )

    st.divider()

    generate_button = st.form_submit_button(
        "🚀 Generate Personas",
        use_container_width=True
    )

# --------------------------------------------------
# Progress Bar
# --------------------------------------------------

progress = 0

if experiment_name:
    progress += 15

if product_name:
    progress += 15

if description:
    progress += 15

if target_audience:
    progress += 15

if research_objective:
    progress += 15

if industry:
    progress += 10

if simulation_type:
    progress += 10

if persona_count:
    progress += 5

st.progress(progress)

# --------------------------------------------------
# Validation
# --------------------------------------------------

if generate_button:

    if not experiment_name.strip():
        st.error("Please enter Experiment Name.")

    elif not product_name.strip():
        st.error("Please enter Product Name.")

    elif not description.strip():
        st.error("Please enter Description.")

    elif not target_audience.strip():
        st.error("Please enter Target Audience.")

    elif not research_objective.strip():
        st.error("Please enter Research Objective.")

    else:

        experiment_data = {
            "experiment_name": experiment_name,
            "product_name": product_name,
            "description": description,
            "target_audience": target_audience,
            "research_objective": research_objective,
            "industry": industry,
            "persona_count": persona_count,
            "simulation_type": simulation_type
        }

        # Store experiment for future pages
        st.session_state["experiment"] = experiment_data

        # Loading Animation
        with st.spinner("Generating experiment configuration..."):
            time.sleep(2)

        st.success("✅ Experiment configured successfully!")

        st.write(
            "Your experiment is ready for persona generation."
        )

        st.divider()

        # --------------------------------------------------
        # Metrics
        # --------------------------------------------------

        st.subheader("📊 Experiment Overview")

        m1, m2, m3 = st.columns(3)

        m1.metric("Industry", industry)
        m2.metric("Personas", persona_count)
        m3.metric("Simulation", simulation_type)

        st.divider()

        # --------------------------------------------------
        # Experiment Details
        # --------------------------------------------------

        st.subheader("📋 Experiment Details")

        col1, col2 = st.columns(2)

        with col1:

            st.write("### General Information")

            st.write(f"**Experiment Name:** {experiment_name}")
            st.write(f"**Product Name:** {product_name}")
            st.write(f"**Industry:** {industry}")

        with col2:

            st.write("### Research Information")

            st.write(f"**Target Audience:** {target_audience}")
            st.write(f"**Research Objective:** {research_objective}")
            st.write(f"**Simulation Type:** {simulation_type}")

        st.divider()

        st.subheader("📝 Description")

        st.info(description)

        st.divider()

        # --------------------------------------------------
        # JSON Configuration
        # --------------------------------------------------

        st.subheader("📦 Experiment Configuration")

        st.json(experiment_data)

        st.divider()

        # --------------------------------------------------
        # Persona Generation Placeholder
        # --------------------------------------------------

        st.subheader("🤖 Persona Generation")

        st.info(
            "This section will connect with the Persona Generator backend."
        )

        if st.button("Start Persona Generation"):

            with st.spinner("Generating personas..."):
                time.sleep(2)

            st.success(
                "Persona generation completed successfully! (Backend integration pending)"
            )

        st.divider()

        # --------------------------------------------------
        # Survey Module Placeholder
        # --------------------------------------------------

        st.subheader("📋 Survey Module")

        st.info(
            "Survey Module will be integrated after personas are generated."
        )

        if st.button("Open Survey Module"):

            st.success(
                "Survey page will be connected here."
            )

# --------------------------------------------------
# Footer
# --------------------------------------------------

st.divider()

st.caption("© 2026 Synthetic User Generation Platform")