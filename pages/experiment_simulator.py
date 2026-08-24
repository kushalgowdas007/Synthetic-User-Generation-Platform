from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from frontend.shared import (
    get_experiment,
    get_survey_results,
    init_session_state,
    render_page_header,
    render_sidebar,
    require_personas,
)


def main() -> None:
    st.set_page_config(page_title="Experiment Simulator", page_icon="🧪", layout="wide")
    init_session_state()
    render_sidebar("Experiment Simulator")
    render_page_header("Scenario & Experiment Simulator", "Simulate how product changes (pricing, onboarding, feature additions) impact predicted product fit and adoption.")

    personas = require_personas()
    if personas is None:
        return

    survey_results = get_survey_results()
    base_fit = float((survey_results or {}).get("product_fit_score", 65.0) or 65.0)

    st.subheader("Simulation Controls")

    col1, col2, col3 = st.columns(3)
    with col1:
        pricing_model = st.selectbox("Pricing Strategy", ["Standard Paid", "Freemium / Free Trial", "Discounted / Subsidy", "Enterprise Custom"])
        trust_signals = st.checkbox("Add Trust Signals & Certifications", value=True)
    with col2:
        onboarding_friction = st.slider("Onboarding Complexity Reduction (%)", 0, 100, 50)
        automation_added = st.checkbox("Add Automated AI Assistant Feature", value=True)
    with col3:
        target_discount = st.slider("Price Discount / Trial Duration Bonus (%)", 0, 50, 15)
        guarantee_offered = st.checkbox("Money-Back Guarantee", value=False)

    # Calculate predicted fit impact
    delta = 0.0
    if pricing_model == "Freemium / Free Trial":
        delta += 12.0
    elif pricing_model == "Discounted / Subsidy":
        delta += 8.0
    elif pricing_model == "Enterprise Custom":
        delta -= 5.0

    if trust_signals:
        delta += 8.0
    if automation_added:
        delta += 7.0
    if guarantee_offered:
        delta += 5.0

    delta += (onboarding_friction / 100.0) * 10.0
    delta += (target_discount / 50.0) * 6.0

    simulated_fit = min(100.0, max(0.0, base_fit + delta))

    st.divider()
    st.subheader("Simulation Results")

    res_col1, res_col2, res_col3 = st.columns(3)
    res_col1.metric("Baseline Product Fit", f"{base_fit:.1f} / 100")
    res_col2.metric("Simulated Product Fit", f"{simulated_fit:.1f} / 100", delta=f"{delta:+.1f} pts")
    res_col3.metric("Predicted Adoption Rate", f"{min(98.0, simulated_fit * 0.9):.1f}%")

    # Simulation Chart
    df = pd.DataFrame([
        {"Scenario": "Baseline", "Product Fit": base_fit},
        {"Scenario": "Simulated Experiment", "Product Fit": simulated_fit}
    ])
    fig = px.bar(df, x="Scenario", y="Product Fit", color="Scenario", title="Baseline vs. Simulated Product Fit Comparison", text_auto=".1f")
    fig.update_layout(yaxis_range=[0, 100])
    st.plotly_chart(fig, use_container_width=True)

    st.success("✨ Simulation complete. Adjust controls above to test alternative product configurations.")


if __name__ == "__main__":
    main()
