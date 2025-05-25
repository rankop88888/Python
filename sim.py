import streamlit as st
import numpy as np
import pandas as pd
import io
import matplotlib.pyplot as plt

st.set_page_config(page_title="Casino Promo & Expense Simulator", layout="wide")
st.title("🎰 Casino Promo Ticket & Expense Simulator")

st.info(
    "**Default: Calculator uses an 8% promo ticket survival rate until you run the simulator.**\n\n"
    "_Run the simulator below for your real result!_"
)

# --- PROMO SURVIVAL SIMULATION ---
st.header("1. Promo Ticket Survival Simulation")

with st.form("sim_params"):
    col1, col2 = st.columns(2)
    with col1:
        promo_ticket_face_value = st.number_input("Promo Ticket Face Value (ALL)", value=5000.0, min_value=0.01, step=0.01, format="%.2f")
        bet_size = st.number_input("Bet Size (ALL)", value=100.0, min_value=1.0, step=1.0, format="%.2f")
        multiplier = st.number_input("Wagering Multiplier (x)", value=40, min_value=1, step=1)
    with col2:
        rtp = st.number_input("RTP (e.g., 0.96 = 96%)", value=0.96, min_value=0.5, max_value=1.0, step=0.01, format="%.2f")
        num_sims = st.number_input("Number of Simulations", value=10000, min_value=100, max_value=100_000, step=100)
        stdev = st.number_input("Volatility (Standard Deviation, payout multiplier)", value=8.0, min_value=0.5, max_value=25.0, step=0.1)
    run_btn = st.form_submit_button("Run Promo Simulation")

required_wager = promo_ticket_face_value * multiplier
max_spins = int(required_wager // bet_size)
st.caption(
    f"""
    • Promo Ticket Face Value: **ALL{promo_ticket_face_value:,.2f}**  
    • Bet Size: **ALL{bet_size:,.2f}**  
    • Wagering Multiplier: **{multiplier:,}**  
    • Number of Simulations: **{num_sims:,}**  
    • Required Wager: **ALL{required_wager:,.2f}**  
    • Maximum Number of Spins: **{max_spins:,}**
    """
)

def get_spin_outcome(rtp):
    payouts = np.array([0, 0.2, 1, 3, 10, 50])
    weights = np.array([0.75, 0.12, 0.08, 0.04, 0.009, 0.001])
    weights = weights / weights.sum()
    current_rtp = np.sum(payouts * weights)
    scale = rtp / current_rtp
    payouts = payouts * scale
    return np.random.choice(payouts, p=weights)

if run_btn:
    progress_bar = st.progress(0, text="Running simulations...")
    survival_count = 0
    total_redeemed = []
    update_every = max(1, int(num_sims // 100))
    for sim in range(int(num_sims)):
        balance = promo_ticket_face_value
        total_wagered = 0
        while balance >= bet_size and total_wagered < required_wager:
            outcome = get_spin_outcome(rtp) * bet_size
            balance = balance - bet_size + outcome
            total_wagered += bet_size
        if total_wagered >= required_wager and balance > 0:
            survival_count += 1
            total_redeemed.append(balance)
        else:
            total_redeemed.append(0)
        if sim % update_every == 0 or sim == num_sims - 1:
            percent = (sim + 1) / num_sims
            progress_bar.progress(min(percent, 1.0), text=f"Simulations: {percent:.0%}")
    survival_rate = survival_count / num_sims
    avg_redeemed = np.mean(total_redeemed)
    st.success(f"Survival Rate: **{survival_rate*100:,.2f}%**")
    st.write(f"Average payout for surviving promo tickets: **ALL{avg_redeemed:,.2f}**")
    st.caption("You can now use these results in the expense table below.")
    st.session_state['promo_survival_rate'] = float(survival_rate)
    st.session_state['avg_redeemed'] = float(avg_redeemed)

if 'promo_survival_rate' in st.session_state:
    current_survival_rate = st.session_state['promo_survival_rate']
    st.caption(f"Current survival rate from simulator: **{current_survival_rate:.2%}**")
else:
    current_survival_rate = 0.08
    st.info("**Current survival rate (default): 8%**\n\n_Run the simulator for a real result!_")

# --- EXPENSE SCENARIO TABLE ---
st.header("2. Promo & Points Expense Table")

st.markdown("""
Edit the table below:  
- **Segment:** Campaign, Tier or Segment label  
- **Customers Rewarded:** How many customers receive a promo (ticket and/or points)
- **Turnover per Customer:** Each customer's turnover (flow) for the promo period.
- **Promo Ticket Face Value:** Value per ticket for each customer (can vary by row)
- **Promo Points per Customer:** Points per customer (can be zero for ticket-only scenarios)
""")

example = pd.DataFrame({
    "Segment": ["Regular", "Promo A", "Promo B", "Promo B", "VIP"],
    "Customers Rewarded": [100, 75, 50, 25, 10],
    "Turnover per Customer": [100_000, 250_000, 500_000, 1_000_000, 2_000_000],
    "Promo Ticket Face Value": [5_000.0, 10_000.0, 15_000.0, 20_000.0, 50_000.0],
    "Promo Points per Customer": [0, 25, 50, 100, 150],   # Points can be 0 for some campaigns
})

df = st.data_editor(
    example,
    num_rows="dynamic",
    use_container_width=True,
    key="expense_table"
)

promo_points_cost_rate = st.number_input(
    "Cost per point (e.g., 100 ALL per point)", value=100.0, step=50.0, format="%.2f"
)
st.caption(f"Cost per point: **ALL{promo_points_cost_rate:,.2f}**")

# --- Calculations per all customers
df["Total Turnover"] = df["Customers Rewarded"].astype(float) * df["Turnover per Customer"].astype(float)
df["Theoretical Gross Win"] = df["Total Turnover"] * (1 - rtp)
df["Total Promo Tickets Value"] = df["Customers Rewarded"].astype(float) * df["Promo Ticket Face Value"].astype(float)
df["Total Promo Points"] = df["Customers Rewarded"].astype(float) * df["Promo Points per Customer"].astype(float)

df["Cost of Promo Tickets"] = df["Total Promo Tickets Value"] * current_survival_rate
df["Cost of Promo Points"] = df["Total Promo Points"] * promo_points_cost_rate
df["Total Promo Cost"] = df["Cost of Promo Tickets"] + df["Cost of Promo Points"]
df["Promo Cost % of TGW"] = 100 * df["Total Promo Cost"] / df["Theoretical Gross Win"]

promo_budget_percent = st.number_input(
    "Promo Budget (% of Theoretical Gross Win)", value=20.0, min_value=0.0, max_value=100.0, step=0.1, format="%.2f"
)
st.caption(f"Promo cost budget: **{promo_budget_percent:.2f}%** of Theoretical Gross Win (TGW)")

df["Allowed Promo Budget"] = df["Theoretical Gross Win"] * promo_budget_percent / 100
df["Over/Under Budget"] = df["Total Promo Cost"] - df["Allowed Promo Budget"]
df["Over Budget?"] = df["Over/Under Budget"].apply(lambda x: "Yes" if x > 0 else "No")
df["Net Revenue After Promo"] = df["Total Turnover"] - df["Total Promo Cost"]

def color_negative_red(val):
    try:
        return 'color: red;' if float(val) < 0 else ''
    except Exception:
        return ''

def over_under_color(val):
    try:
        val = float(val)
        if val > 0:
            return 'color: red; font-weight: bold;'
        else:
            return 'color: green; font-weight: bold;'
    except Exception:
        return ''

# --- Split and Show Tables ---
summary_columns = [
    "Segment", "Customers Rewarded", "Turnover per Customer", "Total Turnover",
    "Promo Ticket Face Value", "Promo Points per Customer",
    "Total Promo Tickets Value", "Total Promo Points"
]

cost_columns = [
    "Cost of Promo Tickets", "Cost of Promo Points",
    "Total Promo Cost", "Promo Cost % of TGW",
    "Theoretical Gross Win", "Allowed Promo Budget",
    "Over/Under Budget", "Over Budget?", "Net Revenue After Promo"
]

summary_df = df[summary_columns]
costs_df = df[cost_columns]

st.subheader("Scenario Summary Table")
st.dataframe(
    summary_df.style.format({
        "Customers Rewarded": "{:,.0f}",
        "Turnover per Customer": "{:,.0f}",
        "Total Turnover": "{:,.0f}",
        "Promo Ticket Face Value": "{:,.2f}",
        "Promo Points per Customer": "{:,.0f}",
        "Total Promo Tickets Value": "{:,.2f}",
        "Total Promo Points": "{:,.0f}",
    }),
    use_container_width=True
)

st.subheader("Cost Breakdown Table")
styled_costs = costs_df.style.format({
    "Cost of Promo Tickets": "{:,.2f}",
    "Cost of Promo Points": "{:,.2f}",
    "Total Promo Cost": "{:,.2f}",
    "Promo Cost % of TGW": "{:,.2f}%",
    "Theoretical Gross Win": "{:,.2f}",
    "Allowed Promo Budget": "{:,.2f}",
    "Over/Under Budget": "{:,.2f}",
    "Net Revenue After Promo": "{:,.2f}"
}).applymap(color_negative_red, subset=[
    "Cost of Promo Tickets", "Cost of Promo Points",
    "Total Promo Cost", "Promo Cost % of TGW",
    "Allowed Promo Budget"
]).applymap(over_under_color, subset=["Over/Under Budget"])
st.dataframe(styled_costs, use_container_width=True)

# --- CHARTS ---
st.header("3. Promo Analysis Charts")
st.markdown("Visualize promo efficiency and cost structure by scenario/segment.")

# Promo Cost % of TGW Chart
chart_cols = st.columns(2)

with chart_cols[0]:
    fig1, ax1 = plt.subplots(figsize=(4, 3))   # or (3,2) for extra small
    ax1.bar(df["Segment"], df["Promo Cost % of TGW"])
    ax1.set_ylabel("Promo Cost % of TGW")
    ax1.set_title("Promo Cost % of Theoretical Gross Win by Segment", fontsize=10)
    ax1.axhline(y=promo_budget_percent, color='r', linestyle='--', label='Allowed Budget (%)')
    ax1.legend(fontsize=8)
    st.pyplot(fig1, use_container_width=False)

with chart_cols[1]:
    fig2, ax2 = plt.subplots(figsize=(4, 3))
    ax2.bar(df["Segment"], df["Total Promo Cost"])
    ax2.set_ylabel("Total Promo Cost (ALL)")
    ax2.set_title("Total Promo Cost by Segment", fontsize=10)
    st.pyplot(fig2, use_container_width=False)


# --- CSV & EXCEL EXPORT ---
st.header("4. Download Your Results")

def to_excel(bytes_df_dict):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        for name, frame in bytes_df_dict.items():
            frame.to_excel(writer, sheet_name=name, index=False)
    processed_data = output.getvalue()
    return processed_data

csv_summary = summary_df.to_csv(index=False).encode('utf-8')
csv_costs = costs_df.to_csv(index=False).encode('utf-8')

st.download_button(
    "Download Scenario Summary as CSV",
    csv_summary,
    "promo_summary.csv",
    "text/csv"
)

st.download_button(
    "Download Cost Breakdown as CSV",
    csv_costs,
    "promo_cost_breakdown.csv",
    "text/csv"
)

excel_bytes = to_excel({'Summary': summary_df, 'Cost Breakdown': costs_df})

st.download_button(
    "Download Both Tables as Excel (xlsx)",
    excel_bytes,
    "casino_promo_expense_report.xlsx",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

# --- VALIDATION ---
st.header("5. Data Validation")
warnings = []
if (df["Customers Rewarded"] <= 0).any():
    warnings.append("Warning: One or more rows have zero or negative customers rewarded.")
if (df["Turnover per Customer"] < 0).any():
    warnings.append("Warning: One or more rows have negative turnover per customer.")
if (df["Total Promo Cost"] < 0).any():
    warnings.append("Warning: Total Promo Cost negative (check your inputs).")
if (df["Theoretical Gross Win"] <= 0).any():
    warnings.append("Warning: Theoretical Gross Win is zero or negative for some rows (check turnover/RTP).")
if (df["Promo Cost % of TGW"] > 100).any():
    warnings.append("Warning: Promo cost exceeds 100% of theoretical gross win for some rows!")

if warnings:
    for w in warnings:
        st.warning(w)
else:
    st.success("✅ All data looks good!")

st.info(
    f"""**Definitions:**  
    - *Segment*: Campaign or player group  
    - *Total Turnover*: Customers × turnover per customer  
    - *Promo ticket cost*: Total promo ticket value × survival rate  
    - *Promo points*: Customers × points per customer × entry price  
    - *Promo cost %*: How much of theoretical gross win is spent on promotions  
    - *Allowed Promo Budget*: User-entered % × TGW  
    - *Net Revenue*: Total Turnover minus all promo costs  
    - *@Pierre2025 
    """
)

st.caption("💡 To optimize: track incremental revenue generated by promos, and set a target promo % of theoretical gross win (TGW), usually 15–30% in real casino operations.")
