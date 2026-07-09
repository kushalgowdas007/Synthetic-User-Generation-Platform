import streamlit as st

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

**Steps**
1. Enter experiment details.
2. Select the industry.
3. Choose simulation type.
4. Set persona count.
5. Click **Generate Personas**.
""")

# --------------------------------------------------
# Main Heading
# --------------------------------------------------
st.title("🧪 Experiment Workspace")

st.write(
    "Configure your experiment before generating synthetic user personas."
)

st.progress(25)

st.divider()

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
            value=5,
            step=1
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

        st.success("✅ Experiment configured successfully!")

        st.write(
            "Your experiment has been created successfully and is ready for persona generation."
        )

        st.divider()

        st.subheader("📊 Experiment Overview")

        metric1, metric2, metric3 = st.columns(3)

        metric1.metric("Industry", industry)
        metric2.metric("Personas", persona_count)
        metric3.metric("Simulation", simulation_type)

        st.divider()

        st.subheader("📋 Experiment Summary")

        left, right = st.columns(2)

        with left:
            st.info(f"**Experiment Name:** {experiment_name}")
            st.info(f"**Product Name:** {product_name}")

        with right:
            st.info(f"**Target Audience:** {target_audience}")
            st.info(f"**Research Objective:** {research_objective}")

        with st.expander("📝 Experiment Description"):
            st.write(description)

        st.divider()

        st.subheader("📦 Generated Experiment Configuration")

        st.json(experiment_data)

# --------------------------------------------------
# Footer
# --------------------------------------------------
st.divider()

st.caption("© 2026 Synthetic User Generation Platform")