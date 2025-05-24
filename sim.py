import streamlit as st
import numpy as np
import pandas as pd

st.set_page_config(page_title="Casino Promo & Expense Simulator", layout="wide")
st.title("🎰 Casino Promo Ticket & Expense Simulator")

# --- EMPHASIZED DEFAULT NOTICE AT THE TOP ---
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
        bet_size = st.number_input("Bet Size", value=100, min_value=1, step=1)
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
    • Bet Size: **ALL{bet_size:,}**  
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

# --- Run simulation and store result in session state ---
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

# --- CALCULATION: SURVIVAL RATE FOR CALCULATOR ---
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
- **Promo Tickets/Points Given:** For each scenario, enter tickets (points will auto-match; you can set points to 0 if needed).
- **Promo Ticket Face Value:** You can vary per row.
- **Promo Points Given:** Can be zero for ticket-only scenarios.
""")

# Realistic, casino-friendly demo table:
example = pd.DataFrame({
    "Turnover": [100_000, 250_000, 500_000, 1_000_000, 2_000_000],
    "No.Promo Tickets/Points Given": [10, 25, 50, 100, 200],
    "Promo Ticket Face Value": [5_000, 100_000, 150_000, 200_000, 500_000],
    "Promo Points Given": [0, 25, 50, 100, 150],   # Example: some rows, points can be zero
})

df = st.data_editor(
    example,
    num_rows="dynamic",
    use_container_width=True,
    key="expense_table"
)

# Enforce: Promo Points Given = Promo Tickets/Points Given (unless 0)
# (But allow manual 0 for points.)
df["Promo Points Given"] = [
    pts if pts == 0 else tix
    for tix, pts in zip(df["No.Promo Tickets/Points Given"], df["Promo Points Given"])
]

promo_points_cost_rate = st.number_input(
    "Cost per point (e.g., 1 EUR per 1 point)", value=1.0, step=0.1, format="%.2f"
)
st.caption(f"Cost per point: **ALL{promo_points_cost_rate:,.2f}**")

# --- Theoretical gross win per row
df["Theoretical Gross Win"] = df["Turnover"] * (1 - rtp)

# --- Cost of promo tickets and points
df["Cost of Promo Tickets"] = (
    df["No.Promo Tickets/Points Given"].astype(float)
    * df["Promo Ticket Face Value"].astype(float)
    * current_survival_rate
)
df["Cost of Promo Points"] = df["Promo Points Given"].astype(float) * promo_points_cost_rate
df["Total Promo Cost"] = df["Cost of Promo Tickets"] + df["Cost of Promo Points"]
df["Promo Cost % of TGW"] = 100 * df["Total Promo Cost"] / df["Theoretical Gross Win"]

# --- Allowed promo budget & net revenue
promo_budget_percent = st.number_input(
    "Promo Budget (% of Theoretical Gross Win)", value=20.0, min_value=0.0, max_value=100.0, step=0.1, format="%.2f"
)
st.caption(f"Promo cost budget: **{promo_budget_percent:.2f}%** of Theoretical Gross Win (TGW)")

df["Allowed Promo Budget"] = df["Theoretical Gross Win"] * promo_budget_percent / 100
df["Over/Under Budget"] = df["Total Promo Cost"] - df["Allowed Promo Budget"]
df["Over Budget?"] = df["Over/Under Budget"].apply(lambda x: "Yes" if x > 0 else "No")
df["Net Revenue After Promo"] = df["Turnover"] - df["Total Promo Cost"]

# --- Format DataFrame with RED for negative/cost columns
def color_negative_red(val):
    try:
        if float(val) < 0:
            return 'color: red;'
        if 'ALL' in str(val) or '%' in str(val):  # highlight cost/percent columns as red
            return 'color: red;'
    except Exception:
        return ''
    return 'color: red;' if isinstance(val, (int, float)) and val < 0 else ''

cost_columns = [
    "Cost of Promo Tickets", "Cost of Promo Points",
    "Total Promo Cost", "Promo Cost % of TGW",
    "Allowed Promo Budget", "Over/Under Budget"
]

styled_df = df.style.format({
    "Turnover": "{:,.0f}",
    "Promo Tickets/Points Given": "{:,.0f}",
    "Promo Ticket Face Value": "ALL{:,.2f}",
    "Promo Points Given": "{:,.0f}",
    "Cost of Promo Tickets": "ALL{:,.2f}",
    "Cost of Promo Points": "ALL{:,.2f}",
    "Total Promo Cost": "ALL{:,.2f}",
    "Promo Cost % of TGW": "{:,.2f}%",
    "Theoretical Gross Win": "ALL{:,.2f}",
    "Allowed Promo Budget": "ALL{:,.2f}",
    "Over/Under Budget": "ALL{:,.2f}",
    "Net Revenue After Promo": "ALL{:,.2f}"
}).applymap(color_negative_red, subset=cost_columns)

st.dataframe(styled_df, use_container_width=True)

st.info(
    f"""**Definitions:**  
    - *Promo ticket cost*: Tickets × face value × survival rate  
    - *Promo points*: Count × entry price (or 0 if blank)  
    - *Promo cost %*: How much of theoretical gross win is spent on promotions  
    - *Allowed Promo Budget*: User-entered % × TGW  
    - *Net Revenue*: Turnover minus all promo costs  
    """
)

st.caption("💡 To optimize: track incremental revenue generated by promos, and set a target promo % of theoretical gross win (TGW), usually 15–30% in real casino operations.")
