import streamlit as st
import numpy as np
import pandas as pd

st.set_page_config(page_title="Casino Promo & Expense Simulator", layout="wide")

st.title("🎰 Casino Promo Ticket & Expense Simulator")

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
    st.caption("Payout Table (per spin): Most spins pay zero. This is a synthetic slot payout model.")
    run_btn = st.form_submit_button("Run Promo Simulation")

def get_spin_outcome(rtp):
    # Use a realistic slot: most spins lose, some small wins, rare big win
    payouts = np.array([0, 0.2, 1, 3, 10, 50])
    weights = np.array([0.75, 0.12, 0.08, 0.04, 0.009, 0.001])
    # Scale payouts to exactly hit desired RTP
    current_rtp = np.sum(payouts * weights)
    scale = rtp / current_rtp
    payouts = payouts * scale
    return np.random.choice(payouts, p=weights)

# Run the simulation and "remember" results for expense table
if run_btn:
    required_wager = promo_amount * multiplier
    max_spins = int(required_wager // bet_size)
    survival_count = 0
    total_redeemed = []
    for sim in range(int(num_sims)):
        balance = promo_amount
        total_wagered = 0
        while balance >= bet_size and total_wagered < required_wager:
            outcome = get_spin_outcome(rtp) * bet_size
            balance = balance - bet_size + outcome
            total_wagered += bet_size
        # If survived, cost is the final balance left
        # If not, cost is zero
        if total_wagered >= required_wager and balance > 0:
            survival_count += 1
            total_redeemed.append(balance)
        else:
            total_redeemed.append(0)
    survival_rate = survival_count / num_sims
    avg_redeemed = np.mean(total_redeemed)
    st.success(f"Survival Rate: **{survival_rate*100:.2f}%**")
    st.write(f"Average payout for surviving promo tickets: **{avg_redeemed:.2f}**")
    st.caption("You can now use these results in the expense table below.")

    # Store for use in expense table
    st.session_state['promo_survival_rate'] = survival_rate
    st.session_state['avg_redeemed'] = avg_redeemed

else:
    if 'promo_survival_rate' not in st.session_state:
        st.session_state['promo_survival_rate'] = 0.05
        st.session_state['avg_redeemed'] = promo_amount * 0.2

# --- EXPENSE SCENARIO TABLE ---
st.header("2. Promo & Points Expense Table")

st.markdown("""
Edit the table below:  
- **Turnover:** Total cash play turnover  
- **Promo Tickets Given:** Number of tickets distributed  
- **Promo Points Given:** Points awarded (not wagered, cost is full value)
""")

# Example data
example = pd.DataFrame({
    "Turnover": [100_000, 250_000, 500_000, 750_000, 1_000_000],
    "Promo Tickets Given": [5000, 10000, 20000, 25000, 50000],
    "Promo Points Given": [25, 50, 75, 100, 150]
})
df = st.data_editor(
    example,
    num_rows="dynamic",
    use_container_width=True,
    key="expense_table"
)

# Calculate expenses
promo_ticket_cost = st.session_state['promo_survival_rate'] * st.session_state['avg_redeemed']
promo_points_cost_rate = st.number_input("Cost per point (e.g., 1 EUR per 1 point)", value=1, step=0.1, format="%.4f")

df["Cost of Promo Tickets"] = df["Promo Tickets Given"] * promo_ticket_cost
df["Cost of Promo Points"] = df["Promo Points Given"] * promo_points_cost_rate
df["Total Promo Cost"] = df["Cost of Promo Tickets"] + df["Cost of Promo Points"]
df["Promo Cost % of Turnover"] = 100 * df["Total Promo Cost"] / df["Turnover"]

# Optional: Net Revenue After Promo
df["Net Revenue After Promo"] = df["Turnover"] - df["Total Promo Cost"]

styled_df = df.style.format({
    "Turnover": "{:,.0f}",
    "Promo Tickets Given": "{:,.0f}",
    "Promo Points Given": "{:,.0f}",
    "Cost of Promo Tickets": "€{:,.2f}",
    "Cost of Promo Points": "€{:,.2f}",
    "Total Promo Cost": "€{:,.2f}",
    "Promo Cost % of Turnover": "{:.2f}%",
    "Net Revenue After Promo": "€{:,.2f}"
})

st.dataframe(styled_df, use_container_width=True)

st.info(
    f"""**Definitions:**  
    - *Promo ticket cost*: Based on simulated survival rate & average payout  
    - *Promo points*: Costed 1:1 (or at your custom rate above), as not wagered  
    - *Net Revenue*: Turnover minus all promo costs  
    - *Promo cost %*: How much of turnover is spent on promotions  
    """
)

st.caption("Smart suggestion: To optimize, track not only costs but also incremental revenue generated by promos, and set a target promo % of turnover (often 1-5% in real casinos).")

