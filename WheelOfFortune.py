import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import io

st.set_page_config(page_title="Wheel of Fortune Promo Simulator", layout="wide")
st.title("🎡 Wheel of Fortune Promo Simulator")

col1, col2, col3 = st.columns(3)

# --- 1.1 PROMO TICKET CONFIG ---
with col1:
    st.subheader("Promo Ticket Option")
    use_promo_ticket = st.checkbox("Use Promo Ticket Wheel (apply survival rate)", value=False)
    promo_survival = st.number_input(
        "Promo Ticket Survival Rate (%)", value=8.0, min_value=0.0, max_value=100.0,
        step=0.01, format="%.2f"
    )

# --- 1.2 WHEEL CONFIG ---
with col2:
    st.subheader("Configure Wheel")
    num_compartments = st.number_input("Number of Wheel Compartments", value=6, min_value=2, max_value=100, step=1)
    input_mode = st.radio("Input mode", ["Manual values", "Value × Count (multipliers)"])

    # Promo values for promo mode (default values)
    PROMO_VALUES = [2500, 5000, 7500, 10000, 15000]
    if use_promo_ticket:
        if num_compartments <= len(PROMO_VALUES):
            default_wheel = PROMO_VALUES[:num_compartments]
        else:
            default_wheel = PROMO_VALUES + [PROMO_VALUES[-1]] * (int(num_compartments) - len(PROMO_VALUES))
    else:
        default_wheel = [25, 50, 75, 100, 150, 200][:num_compartments]

    valid = False
    wheel_values = []

    if input_mode == "Manual values":
        default_text = ",".join(str(int(x)) for x in default_wheel)
        values_text = st.text_area(
            f"Enter all {int(num_compartments)} compartment values (comma-separated):",
            value=default_text
        )
        try:
            values_list = [float(x) for x in values_text.strip().split(",")]
            if len(values_list) != num_compartments:
                st.error(f"Enter exactly {num_compartments} values.")
            else:
                wheel_values = values_list
                valid = True
        except Exception:
            st.error("Invalid values. Please enter numbers, comma separated.")
    else:
        st.markdown("Enter value × count per line, e.g.: `25 2` (25 points appears 2 times)")
        if use_promo_ticket:
            default_lines = "\n".join(f"{v} 1" for v in default_wheel)
        else:
            default_lines = "\n".join(f"{v} 1" for v in default_wheel)
        pairs_text = st.text_area("Value × Count table", value=default_lines)
        pairs = []
        total = 0
        for line in pairs_text.strip().splitlines():
            try:
                if not line.strip():
                    continue
                val, cnt = line.strip().split()
                val = float(val)
                cnt = int(cnt)
                pairs.append((val, cnt))
                total += cnt
            except:
                st.error("Format each line as: value count (e.g. 25 24)")
                pairs = []
                break
        if pairs and total != num_compartments:
            st.error(f"Sum of counts is {total}, should be {num_compartments}.")
        elif pairs:
            wheel_values = []
            for v, c in pairs:
                wheel_values.extend([v]*c)
            valid = True

with col3:
    st.subheader("Spin Simulation Settings")
    point_eur = st.number_input("Points Value (ALL per point)", value=100.0, min_value=10.00, step=10.00, format="%.2f")
    num_spins = st.number_input("Spins per customer", value=1, min_value=1, max_value=100, step=1)
    num_customers = st.number_input("Customers per set", value=5, min_value=1, max_value=100_000, step=1)
    sets_per_day = st.number_input("Sets per day", value=1, min_value=1, max_value=100, step=1)
    st.caption(f"**Total spins per day:** {num_spins*num_customers*sets_per_day:,}")

# ---- CALCULATIONS AND RESULTS ----
if valid:
    avg_points = np.mean(wheel_values)
    if use_promo_ticket:
        avg_wheel_cost = avg_points * (promo_survival / 100.0)
    else:
        avg_wheel_cost = avg_points * point_eur

    expected_per_customer = num_spins * avg_wheel_cost
    total_daily_cost = sets_per_day * num_customers * num_spins * avg_wheel_cost

    # --- 2. SUMMARY TABLE ---
    st.header("Summary Table")
    summary_dict = {
        "Number of Compartments": [num_compartments],
        "Points per Compartment": [", ".join(str(int(p)) for p in wheel_values)],
        "Points Value (ALL)": [point_eur if not use_promo_ticket else "-"],
        "Avg Points per Spin": [avg_points],
        "Avg Cost per Spin (ALL)": [avg_wheel_cost],
        "Promo Survival Rate (%)": [promo_survival if use_promo_ticket else "-"],
        "Num Spins per Customer": [num_spins],
        "Customers per Set": [num_customers],
        "Sets per Day": [sets_per_day],
        "Total Spins per Day": [num_spins*num_customers*sets_per_day],
        "Expected Cost per Customer": [expected_per_customer],
        "Total Cost per Day": [total_daily_cost],
    }

    summary_df = pd.DataFrame(summary_dict)
    st.dataframe(summary_df)

    # --- 3. SIMULATE CUSTOMER SPINNING X TIMES IN A ROW ---
    st.header("Simulate Repeated Spins for a Single Customer")
    num_trials = st.number_input("How many simulated customers?", value=1000, min_value=1, max_value=100_000, step=1)
    run_customer_sim = st.button("Simulate for One Customer (X spins, Y times)")
    if run_customer_sim:
        rng = np.random.default_rng()
        total_points_list = []
        for _ in range(num_trials):
            spins = rng.choice(wheel_values, size=num_spins)
            total_points_list.append(np.sum(spins))
        avg_customer_points = np.mean(total_points_list)
        if use_promo_ticket:
            avg_customer_eur = avg_customer_points * (promo_survival / 100.0)
        else:
            avg_customer_eur = avg_customer_points * point_eur
        st.success(f"Average for {num_trials:,} customers spinning {num_spins}x: **{avg_customer_points:,.2f} points (ALL{avg_customer_eur:,.2f})**")
        st.write(f"- Min: {np.min(total_points_list):,.0f} points, Max: {np.max(total_points_list):,.0f} points")

    # --- 4. WINNING PROBABILITY CALCULATION ---
    st.header("Probability of Hitting a Prize")
    target_value = st.number_input("Prize value to check (e.g. 10000)", value=float(max(wheel_values)), step=1.0)
    hit_count = wheel_values.count(target_value)
    prob_single = hit_count / num_compartments if num_compartments > 0 else 0
    prob_at_least_one = 1 - (1 - prob_single)**num_spins if prob_single > 0 else 0
    exp_wins = num_spins * prob_single
    st.info(
        f"Chance of getting **at least one {int(target_value)}** in {num_spins} spins: "
        f"**{prob_at_least_one:.2%}**\n\n"
        f"Expected number of times: **{exp_wins:.2f}**"
    )

    # --- 5. PIE CHART & BAR CHART ---
    st.header("Wheel Distribution Visualization")
    chart_cols = st.columns(2)
    with chart_cols[0]:
        pie_labels = [f"{int(p)}" for p in sorted(set(wheel_values))]
        pie_counts = [wheel_values.count(float(lab)) for lab in pie_labels]
        fig_pie, ax_pie = plt.subplots(figsize=(4, 4))
        ax_pie.pie(pie_counts, labels=pie_labels, autopct=lambda pct: f"{pct:.1f}%")
        ax_pie.set_title("Wheel Compartment Probabilities", fontsize=10)
        st.pyplot(fig_pie, use_container_width=False)
    with chart_cols[1]:
        fig_bar, ax_bar = plt.subplots(figsize=(4, 4))
        ax_bar.bar(pie_labels, [float(x) for x in pie_labels])
        ax_bar.set_ylabel("Points/Promo Value", fontsize=10)
        ax_bar.set_xlabel("Wheel Compartment", fontsize=10)
        ax_bar.set_title("Values Distribution on Wheel", fontsize=10)
        st.pyplot(fig_bar, use_container_width=False)

    # --- 6. EXPORT SUMMARY ---
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
    st.warning("Please enter valid values/multipliers matching the number of compartments.")
