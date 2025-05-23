import streamlit as st
import numpy as np
import pandas as pd

st.set_page_config(page_title="Slot Promo Ticket Survival Simulator", layout="centered")

st.title("🎰 Slot Promo Ticket Survival Simulator")

# --- User Input Form ---
with st.form("sim_params"):
    col1, col2 = st.columns(2)
    with col1:
        promo_amount = st.number_input("Promo Ticket Amount", value=5000, min_value=100, step=100)
        bet_size = st.number_input("Bet Size", value=500, min_value=1, step=1)
        multiplier = st.number_input("Wagering Multiplier (x)", value=40, min_value=1, step=1)
    with col2:
        rtp = st.number_input("RTP (e.g., 0.96 = 96%)", value=0.96, min_value=0.5, max_value=1.0, step=0.01, format="%.2f")
        num_sims = st.number_input("Number of Simulations", value=1000, min_value=100, max_value=100_000, step=100)
        stdev = st.number_input("Volatility (Standard Deviation, payout multiplier)", value=3.0, min_value=0.5, max_value=10.0, step=0.1)

    st.caption("Payout Table (per spin): Most spins pay zero. This is a synthetic slot payout model.")
    run_btn = st.form_submit_button("Run Simulation")

def get_spin_outcome(rtp, stdev):
    # Use a realistic slot: most spins lose, some small wins, rare big win
    payouts = np.array([0, 0.2, 1, 3, 10, 50])
    weights = np.array([0.75, 0.12, 0.08, 0.04, 0.009, 0.001])
    # Scale weights to exactly hit desired RTP
    current_rtp = np.sum(payouts * weights)
    scale = rtp / current_rtp
    payouts = payouts * scale
    return np.random.choice(payouts, p=weights)

if run_btn:
    st.subheader("Running Simulation...")

    required_wager = promo_amount * multiplier
    max_spins = int(required_wager // bet_size)

    survival_count = 0
    sample_balances = []
    for sim in range(int(num_sims)):
        balance = promo_amount
        total_wagered = 0
        spin_log = []
        for spin in range(max_spins):
            if balance < bet_size:
                break
            outcome = get_spin_outcome(rtp, stdev) * bet_size
            balance = balance - bet_size + outcome
            total_wagered += bet_size
            if sim == 0:
                spin_log.append(balance)
        if total_wagered >= required_wager and balance > 0:
            survival_count += 1
        if sim == 0:
            sample_balances = spin_log

    survival_rate = survival_count / num_sims * 100

    st.success(f"Survival Rate: **{survival_rate:.2f}%**  (out of {num_sims} tickets)")

    if sample_balances:
        st.line_chart(pd.Series(sample_balances, name="First Ticket Balance"))
    else:
        st.info("First ticket busted before any spins completed.")

    st.write(f"Completed {num_sims} simulations with: "
             f"Promo={promo_amount}, Bet={bet_size}, Wagering Mult={multiplier}, RTP={rtp:.2f}, Volatility={stdev}")

    st.caption("Tip: Try lowering the promo or increasing the multiplier to see bust rates rise.")

