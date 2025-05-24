import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import io

st.set_page_config(page_title="Wheel of Fortune Promo Simulator", layout="wide")
st.title("🎡 Wheel of Fortune Promo Simulator")

col1, col2 = st.columns(2)

# -- 1. PROMO CONFIGURATION --
with col1:
    st.subheader("Reward Type")
    use_promo_ticket = st.checkbox("Use Promo Ticket (otherwise use Wheel/Points)", value=True)
    promo_survival = st.number_input("Promo Ticket Survival Rate (%)", value=8.0, min_value=0.0, max_value=100.0, step=0.01, format="%.2f")
    reward_value = st.number_input("Reward Value (Promo Ticket Face Value **or** Point Value (€))", value=100.0, min_value=0.01, step=0.01, format="%.2f")

# -- 2. WHEEL CONFIGURATION (Only relevant if not using promo ticket) --
with col2:
    st.subheader("Wheel Configuration (Points)")
    num_compartments = st.number_input("Number of Wheel Compartments", value=6, min_value=2, max_value=100, step=1)
    default_points = [25, 50, 75, 100, 150, 200]
    if num_compartments <= len(default_points):
        wheel_points = default_points[:num_compartments]
    else:
        wheel_points = default_points + [default_points[-1]] * (num_compartments - len(default_points))

    points_values = st.text_input(
        f"Enter {int(num_compartments)} point values (comma-separated)", 
        value=",".join(str(x) for x in wheel_points)
    )
    try:
        point_values = [float(x) for x in points_values.strip().split(",")]
        if len(point_values) != num_compartments:
            st.error(f"Enter exactly {num_compartments} values.")
            valid_input = False
        else:
            valid_input = True
    except Exception:
        st.error("Invalid point values. Please enter numbers, comma separated.")
        point_values = []
        valid_input = False

# -- 3. SPIN SETTINGS --
num_spins = st.number_input("Spins per customer", value=1, min_value=1, max_value=100, step=1)
num_customers = st.number_input("Customers per set", value=5, min_value=1, max_value=100_000, step=1)
sets_per_day = st.number_input("Sets per day", value=1, min_value=1, max_value=100, step=1)
st.caption(f"**Total spins per day:** {num_spins*num_customers*sets_per_day:,}")

# --- CALCULATIONS ---
if valid_input:
    if use_promo_ticket:
        cost_per_customer = reward_value * (promo_survival / 100.0)
        cost_type = f"Promo Ticket: €{reward_value:,.2f} × {promo_survival:.2f}% survival"
        avg_points = "-"
        avg_points_cost = "-"
    else:
        avg_points = np.mean(point_values)
        avg_points_cost = avg_points * reward_value
        cost_per_customer = num_spins * avg_points_cost
        cost_type = f"Wheel Avg: {avg_points:.2f} × €{reward_value:,.2f} × {num_spins} spins"
    total_cost_per_set = cost_per_customer * num_customers
    total_cost_per_day = total_cost_per_set * sets_per_day

    # --- SUMMARY TABLE ---
    st.header("Summary Table")
    summary_dict = {
        "Reward Type": [cost_type],
        "Avg Points per Spin": [avg_points if not use_promo_ticket else "-"],
        "Cost per Customer (€)": [cost_per_customer],
        "Customers per Set": [num_customers],
        "Sets per Day": [sets_per_day],
        "Total Cost per Set (€)": [total_cost_per_set],
        "Total Cost per Day (€)": [total_cost_per_day]
    }
    summary_df = pd.DataFrame(summary_dict)
    st.dataframe(summary_df)

    # --- SIMULATE REPEATED SPINS IF USING WHEEL ---
    if not use_promo_ticket:
        st.header("Simulate Repeated Spins for a Single Customer")
        num_trials = st.number_input("How many simulated customers?", value=1000, min_value=1, max_value=100_000, step=1)
        run_customer_sim = st.button("Simulate for One Customer (X spins, Y times)")
        if run_customer_sim:
            rng = np.random.default_rng()
            total_points_list = []
            for _ in range(num_trials):
                spins = rng.choice(point_values, size=num_spins)
                total_points_list.append(np.sum(spins))
            avg_customer_points = np.mean(total_points_list)
            avg_customer_eur = avg_customer_points * reward_value
            st.success(f"Average for {num_trials:,} customers spinning {num_spins}x: **{avg_customer_points:,.2f} points (€{avg_customer_eur:,.2f})**")
            st.write(f"- Min: {np.min(total_points_list):,.0f} points, Max: {np.max(total_points_list):,.0f} points")

        # --- CHARTS ---
        st.header("Wheel Distribution Visualization")
        chart_cols = st.columns(2)
        with chart_cols[0]:
            pie_labels = [f"{int(p)}" for p in point_values]
            pie_counts = [1]*len(point_values)
            fig_pie, ax_pie = plt.subplots(figsize=(4, 4))
            ax_pie.pie(pie_counts, labels=pie_labels, autopct=lambda pct: f"{pct:.1f}%")
            ax_pie.set_title("Wheel Compartment Probabilities", fontsize=10)
            st.pyplot(fig_pie, use_container_width=False)
        with chart_cols[1]:
            fig_bar, ax_bar = plt.subplots(figsize=(4, 4))
            ax_bar.bar(pie_labels, point_values)
            ax_bar.set_ylabel("Points per Compartment", fontsize=10)
            ax_bar.set_xlabel("Wheel Compartment", fontsize=10)
            ax_bar.set_title("Points Distribution on Wheel", fontsize=10)
            st.pyplot(fig_bar, use_container_width=False)

    # --- EXPORTS ---
    st.header("Download/Export Summary")
    csv_data = summary_df.to_csv(index=False).encode('utf-8')
    st.download_button("Download Summary as CSV", csv_data, "wheel_of_fortune_summary.csv", "text/csv")

    def to_excel(df):
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Summary')
        processed_data = output.getvalue()
        return processed_data

    excel_data = to_excel(summary_df)
    st.download_button(
        label="Download Summary as Excel (xlsx)",
        data=excel_data,
        file_name="wheel_of_fortune_summary.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    st.caption("Adjust values, get your cost. For multiple segments, rerun or build out per group.")

else:
    st.warning("Please enter a valid, comma-separated list of point values matching the number of compartments.")
