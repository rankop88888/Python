import streamlit as st
import numpy as np
import pandas as pd

st.set_page_config(page_title="Casino Promo & Expense Simulator", layout="wide")
st.title("🎰 Casino Promo Ticket & Expense Simulator")
st.info("**Default: Until you run the simulator, the calculator assumes an 8% promo ticket survival rate.**\n\n_Run the simulator for your real value!_")

# --- PROMO SURVIVAL SIMULATION ---
st.header("1. Promo Ticket Survival Simulation")

with st.form("sim_params"):
    col1, col2 = st.columns(2)
    with col1:
        promo_amount = st.number_input("Promo Ticket Amount", value=5000, min_value=100, step=100)
        bet_size = st.number_input("Bet Size", value=500, min_value=1, step=1)
        multiplier = st.number_input("Wagering Multiplier (x)", value=40, min_value=1, step=1)
    with col2:
        rtp = st.number_input("RTP (e.g., 0.96 = 96%)", value=0.96, min_value=0.5, max_value=1.0, step=0.01, format="%.2f")
        num_sims = st.number_input("Number of Simulations", value=10000, min_value=100, max_value=100_000, step=100)
        stdev = st.number_input("Volatility (Standard Deviation, payout multiplier)", value=3.0, min_value=0.5, max_value=10.0, step=0.1)
    run_btn = st.form_submit_button("Run Promo Simulation")

required_wager = promo_amount * multiplier
max_spins = int(required_wager // bet_size)
st.caption(
    f"""
    • Promo Ticket Amount: **{promo_amount:,}**  
    • Bet Size: **{bet_size:,}**  
    • Wagering Multiplier: **{multiplier:,}**  
    • Number of Simulations: **{num_sims:,}**  
    • Required Wager: **{required_wager:,}**  
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
        balance = promo_amount
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
    st.write(f"Average payout for surviving promo tickets: **€{avg_redeemed:,.2f}**")
    st.caption("You can now use these results in the expense table below.")
    st.session_state['promo_survival_rate'] = float(survival_rate)
    st.session_state['avg_redeemed'] = float(avg_redeemed)
# --- EXPENSE SCENARIO TABLE ---
st.header("2. Promo & Points Expense Table")

st.markdown("""
Edit the table below:  
- **Turnover:** Total cash play turnover  
- **Promo Tickets Given:** Number of tickets distributed  
- **Promo Points Given:** Points awarded (not wagered, cost is full value)
""")

example = pd.DataFrame({
    "Turnover": [100_000, 250_000, 500_000, 750_000, 1_000_000],
    "Promo Tickets Given": [5_000, 10_000, 20_000, 25_000, 50_000],
    "Promo Points Given": [25, 50, 75, 100, 150]
})

df = st.data_editor(
    example,
    num_rows="dynamic",
    use_container_width=True,
    key="expense_table"
)

# --- Use last simulation result if available, else use 8% default survival rate ---
if 'promo_survival_rate' in st.session_state:
    current_survival_rate = st.session_state['promo_survival_rate']
    st.caption(f"Current survival rate from simulator: **{current_survival_rate:.2%}**")
else:
    current_survival_rate = 0.08  # 8% default
    st.caption("Current survival rate (default): **8%** (run the simulator for a real result)")

promo_ticket_cost = promo_amount * current_survival_rate

promo_points_cost_rate = st.number_input(
    "Cost per point (e.g., 1 EUR per 1 point)", value=1.0, step=0.1, format="%.2f"
)
st.caption(f"Cost per point: **€{promo_points_cost_rate:,.2f}**")

# --- Calculator columns ---
df["Cost of Promo Tickets"] = df["Promo Tickets Given"].astype(float) * promo_ticket_cost
df["Cost of Promo Points"] = df["Promo Points Given"].astype(float) * promo_points_cost_rate
df["Total Promo Cost"] = df["Cost of Promo Tickets"] + df["Cost of Promo Points"]
df["Promo Cost % of Turnover"] = 100 * df["Total Promo Cost"] / df["Turnover"]

# --- THEORETICAL GROSS WIN & ALLOWED BUDGET ---
promo_budget_percent = st.number_input(
    "Promo Budget (% of Theoretical Gross Win)", value=20.0, min_value=0.0, max_value=100.0, step=0.1, format="%.2f"
)
st.caption(f"Promo cost budget: **{promo_budget_percent:.2f}%** of Theoretical Gross Win (TGW)")


df["Theoretical Gross Win"] = df["Turnover"] * (1 - rtp)
df["Allowed Promo Budget"] = df["Theoretical Gross Win"] * promo_budget_percent / 100
df["Over/Under Budget"] = df["Total Promo Cost"] - df["Allowed Promo Budget"]
df["Over Budget?"] = df["Over/Under Budget"].apply(lambda x: "Yes" if x > 0 else "No")
df["Net Revenue After Promo"] = df["Turnover"] - df["Total Promo Cost"]

# --- Format DataFrame ---
styled_df = df.style.format({
    "Turnover": "{:,.0f}",
    "Promo Tickets Given": "{:,.0f}",
    "Promo Points Given": "{:,.0f}",
    "Cost of Promo Tickets": "€{:,.2f}",
    "Cost of Promo Points": "€{:,.2f}",
    "Total Promo Cost": "€{:,.2f}",
    "Promo Cost % of Turnover": "{:,.2f}%",
    "Theoretical Gross Win": "€{:,.2f}",
    "Allowed Promo Budget": "€{:,.2f}",
    "Over/Under Budget": "€{:,.2f}",
    "Net Revenue After Promo": "€{:,.2f}"
})

st.dataframe(styled_df, use_container_width=True)

st.info(
    f"""**Definitions:**  
    - *Promo ticket cost*: Face value × simulated (or default) survival rate  
    - *Promo points*: Costed at entry price  
    - *Theoretical Gross Win*: Turnover × (1 - RTP)  
    - *Allowed Promo Budget*: User-entered % × TGW  
    - *Net Revenue*: Turnover minus all promo costs  
    - *Promo cost %*: Portion of turnover spent on promotions  
    """
)

st.caption("💡 To optimize: track incremental revenue generated by promos, and set a target promo % of theoretical gross win (TGW), usually 20–40% in real casino operations.")
