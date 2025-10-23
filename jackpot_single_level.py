import streamlit as st
import pandas as pd

st.set_page_config(page_title="Mystery Jackpot Single Level Planner", layout="wide")
st.title("Mystery Jackpot Planner - Single Level")

# -------------------------------
# Section 1: User Inputs
# -------------------------------

st.sidebar.header("User Input")

turnover_per_day = st.sidebar.number_input("Total Turnover per Day (€)", value=100000, min_value=0)

# -------------------------------
# Section 2: Jackpot Configuration
# -------------------------------

st.subheader("Jackpot Configuration")
st.markdown("🔍 **Trigger Value** = Turnover required for 1 jackpot hit. It affects frequency of jackpot hits per day.")

col1, col2 = st.columns(2)

with col1:
    min_value = st.number_input("Minimum Jackpot (€)", value=100, min_value=0)
    max_value = st.number_input("Maximum Jackpot (€)", value=500, min_value=0)
    start_value = st.number_input("Start Value (€)", value=100, min_value=0)

with col2:
    end_value = st.number_input("End Value (€)", value=500, min_value=0)
    trigger_value = st.number_input("Trigger Value (€)", value=300, min_value=1)
    increment_percent = st.number_input("Increment %", value=5.0, step=0.1, format="%.2f", min_value=0.0)

increment_ratio = increment_percent / 100

# -------------------------------
# Section 3: Validations
# -------------------------------

error_flag = False

if min_value >= max_value:
    st.error("⚠️ Minimum must be less than Maximum.")
    error_flag = True

if not (min_value <= start_value <= max_value):
    st.error("⚠️ Start value must be between Minimum and Maximum.")
    error_flag = True

if not (start_value <= trigger_value <= end_value):
    st.error("⚠️ Trigger value must be between Start and End.")
    error_flag = True

if not (min_value <= end_value <= max_value):
    st.error("⚠️ End value must be between Minimum and Maximum.")
    error_flag = True

# -------------------------------
# Section 4: Calculations
# -------------------------------

if not error_flag and turnover_per_day > 0:
    st.success("✅ All validations passed")
    
    # Calculate metrics
    avg_hit_value = (start_value + end_value) / 2
    hits_per_day = turnover_per_day / trigger_value
    hits_per_week = hits_per_day * 7
    hits_per_month = hits_per_day * 30
    avg_days_per_hit = 1 / hits_per_day if hits_per_day > 0 else 0
    real_rtp_percent = ((avg_hit_value * hits_per_day) / turnover_per_day) * 100
    real_cost = hits_per_day * avg_hit_value
    jp_increment_per_day = increment_ratio * turnover_per_day
    estimated_jp_paid_per_day = hits_per_day * avg_hit_value
    estimated_jp_paid_per_week = estimated_jp_paid_per_day * 7
    estimated_jp_paid_per_month = estimated_jp_paid_per_day * 30
    
    # Display summary metrics
    st.subheader("Summary Metrics")
    
    metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
    
    with metric_col1:
        st.metric("Real RTP %", f"{real_rtp_percent:.2f}%")
    
    with metric_col2:
        st.metric("Hits per Day", f"{hits_per_day:.2f}")
    
    with metric_col3:
        st.metric("Avg Days per Hit", f"{avg_days_per_hit:.2f}")
    
    with metric_col4:
        st.metric("JP Increment/Day", f"€{jp_increment_per_day:,.2f}")
    
    # Display detailed analysis
    st.subheader("Detailed Analysis")
    
    analysis_data = {
        "Metric": [
            "Average Hit Value (€)",
            "Hits per Day",
            "Hits per Week",
            "Hits per Month",
            "Avg Days per Hit",
            "Real RTP (%)",
            "Real Cost per Day (€)",
            "JP Increment per Day (€)",
            "Estimated JP Paid / Day (€)",
            "Estimated JP Paid / Week (€)",
            "Estimated JP Paid / Month (€)"
        ],
        "Value": [
            f"€{avg_hit_value:,.2f}",
            f"{hits_per_day:.2f}",
            f"{hits_per_week:.2f}",
            f"{hits_per_month:.2f}",
            f"{avg_days_per_hit:.2f}",
            f"{real_rtp_percent:.2f}%",
            f"€{real_cost:,.2f}",
            f"€{jp_increment_per_day:,.2f}",
            f"€{estimated_jp_paid_per_day:,.2f}",
            f"€{estimated_jp_paid_per_week:,.2f}",
            f"€{estimated_jp_paid_per_month:,.2f}"
        ]
    }
    
    df = pd.DataFrame(analysis_data)
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    # Display configuration recap
    st.subheader("Configuration Recap")
    
    config_data = {
        "Parameter": [
            "Minimum Jackpot (€)",
            "Maximum Jackpot (€)",
            "Start Value (€)",
            "End Value (€)",
            "Trigger Value (€)",
            "Increment %",
            "Turnover per Day (€)"
        ],
        "Value": [
            f"€{min_value:,.2f}",
            f"€{max_value:,.2f}",
            f"€{start_value:,.2f}",
            f"€{end_value:,.2f}",
            f"€{trigger_value:,.2f}",
            f"{increment_percent:.2f}%",
            f"€{turnover_per_day:,.2f}"
        ]
    }
    
    config_df = pd.DataFrame(config_data)
    st.dataframe(config_df, use_container_width=True, hide_index=True)
    
    # Key insights
    st.subheader("Key Insights")
    
    st.info(f"💰 **Expected Frequency**: A jackpot will hit approximately every {avg_days_per_hit:.1f} days")
    st.info(f"📊 **RTP Contribution**: This jackpot contributes {real_rtp_percent:.2f}% to the overall RTP")
    st.info(f"📈 **Daily Increment**: The jackpot pool grows by €{jp_increment_per_day:,.2f} per day from player contributions")
    st.info(f"💸 **Monthly Payout**: Expected to pay out approximately €{estimated_jp_paid_per_month:,.2f} per month")
