import streamlit as st
import pandas as pd

st.title("🎰 Mystery Jackpot Contribution Calculator")

st.markdown("""
This tool calculates contribution percentage, hit frequency (in days), and average hit value for each mystery jackpot level.

---  
""")

st.sidebar.header("🧮 Add Jackpot Levels")

# Container to hold jackpot level inputs
jp_levels = []

# Default number of JP levels
num_levels = st.sidebar.number_input("Number of Jackpot Levels", min_value=1, max_value=10, value=1, step=1)

for i in range(num_levels):
    st.subheader(f"Jackpot Level {i+1}")
    with st.container():
        col1, col2 = st.columns(2)
        with col1:
            coin_in = st.number_input(f"Average Daily Coin-In (Level {i+1})", min_value=0.01, step=0.01, format="%.2f")
            initial_value = st.number_input(f"Initial Jackpot Value (Level {i+1})", min_value=0.0, step=0.01, format="%.2f")
            min_hit = st.number_input(f"Min Hit Value (Level {i+1})", min_value=0.0, step=0.01, format="%.2f")
        with col2:
            max_hit = st.number_input(f"Max Hit Value (Level {i+1})", min_value=0.0, step=0.01, format="%.2f")
            contribution_pct = st.number_input(f"Contribution % (Level {i+1})", min_value=0.0, max_value=100.0, step=0.01, format="%.2f")

    jp_levels.append({
        'level': i + 1,
        'coin_in': coin_in,
        'initial_value': initial_value,
        'min_hit': min_hit,
        'max_hit': max_hit,
        'contribution_pct': contribution_pct
    })

# Calculate results
results = []
total_contribution_pct = 0.0

for level_data in jp_levels:
    coin_in = level_data['coin_in']
    min_hit = level_data['min_hit']
    max_hit = level_data['max_hit']
    contribution_pct = level_data['contribution_pct']

    avg_hit = (min_hit + max_hit) / 2
    daily_contribution = coin_in * (contribution_pct / 100)
    hit_in_days = avg_hit / daily_contribution if daily_contribution > 0 else float('inf')

    total_contribution_pct += contribution_pct

    results.append({
        'Level': level_data['level'],
        'Average Daily Coin-In': coin_in,
        'Initial JP Value': level_data['initial_value'],
        'Min Hit Value': min_hit,
        'Max Hit Value': max_hit,
        'Avg Hit Value': round(avg_hit, 2),
        'Contribution %': contribution_pct,
        'Hit Frequency (Days)': round(hit_in_days, 2)
    })

# Display Results
st.markdown("## 📊 Jackpot Levels Summary")

df = pd.DataFrame(results)
st.dataframe(df, use_container_width=True)

st.markdown(f"### 💡 Total Contribution Percentage: **{round(total_contribution_pct, 2)}%**")

if total_contribution_pct > 5.0:
    st.warning("⚠️ Total contribution exceeds 5%. Review each level's contribution %.")
elif total_contribution_pct == 0.0:
    st.error("❌ Contribution % is zero. Check your inputs.")
