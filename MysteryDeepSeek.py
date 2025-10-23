import streamlit as st
import pandas as pd

st.set_page_config(page_title="Mystery Jackpot Single Level Planner", layout="wide")
st.title("Mystery Jackpot Planner - Single Level")

# -------------------------------
# Section 1: Total Coin-In (Prominent)
# -------------------------------

st.markdown("### 💰 Total Coin-In per Day")
st.markdown("*Combined turnover from all EGMs included in the mystery jackpot*")
total_coin_in = st.number_input("", value=100000, min_value=0, key="coin_in", label_visibility="collapsed")
st.markdown(f"<h1 style='text-align: center; color: #1f77b4;'>€{total_coin_in:,.2f}</h1>", unsafe_allow_html=True)

st.divider()

# -------------------------------
# Section 2: Jackpot Configuration
# -------------------------------

st.subheader("🎰 Mystery Jackpot Configuration")

# Configuration mode selection
config_mode = st.radio(
    "Configuration Type:",
    ["Standard (Start Value → Must Hit By)", 
     "Advanced (Min Hit Value > Initial Value)",
     "Random Hit (No Start Value)"],
    help="Choose how the mystery jackpot behaves"
)

col1, col2 = st.columns(2)

with col1:
    st.markdown("**Range Settings**")
    min_jp_value = st.number_input("Minimum Jackpot Value (€)", value=100, min_value=0, 
                                    help="Absolute minimum the jackpot can be")
    max_jp_value = st.number_input("Maximum Jackpot Value (Must Hit By) (€)", value=1000, min_value=0,
                                    help="Jackpot MUST hit at or before this value")

with col2:
    st.markdown("**Increment Settings**")
    increment_percent = st.number_input("Increment % (Contribution Rate)", value=5.0, step=0.1, format="%.2f", min_value=0.0,
                                       help="Percentage of coin-in that goes to jackpot pool")
    increment_ratio = increment_percent / 100

# Configuration-specific inputs
if config_mode == "Standard (Start Value → Must Hit By)":
    st.markdown("**Standard Configuration**")
    col3, col4 = st.columns(2)
    with col3:
        start_value = st.number_input("Start Value (Initial Amount) (€)", value=100, min_value=0,
                                     help="Jackpot starts at this value (usually = Min)")
    with col4:
        must_hit_by = max_jp_value
        st.info(f"Must Hit By: €{must_hit_by:,.2f}")
    
    min_hit_value = None
    initial_value = start_value
    hit_range_start = start_value
    hit_range_end = must_hit_by

elif config_mode == "Advanced (Min Hit Value > Initial Value)":
    st.markdown("**Advanced Configuration**")
    st.info("⚡ Jackpot starts at Initial Value but cannot hit until it reaches Min Hit Value")
    col3, col4, col5 = st.columns(3)
    with col3:
        initial_value = st.number_input("Initial Value (€)", value=100, min_value=0,
                                       help="Jackpot starts here but cannot hit yet")
    with col4:
        min_hit_value = st.number_input("Min Hit Value (€)", value=500, min_value=0,
                                       help="Earliest point jackpot can hit")
    with col5:
        must_hit_by = max_jp_value
        st.info(f"Must Hit By: €{must_hit_by:,.2f}")
    
    start_value = initial_value
    hit_range_start = min_hit_value
    hit_range_end = must_hit_by

else:  # Random Hit
    st.markdown("**Random Hit Configuration**")
    st.info("🎲 Jackpot can hit randomly anywhere between Min and Max")
    initial_value = 0
    start_value = 0
    min_hit_value = min_jp_value
    hit_range_start = min_jp_value
    hit_range_end = max_jp_value
    st.warning("No initial seed - jackpot builds from zero via contributions")

# -------------------------------
# Section 3: Validations
# -------------------------------

error_flag = False

if min_jp_value >= max_jp_value:
    st.error("⚠️ Minimum must be less than Maximum (Must Hit By).")
    error_flag = True

if config_mode == "Standard (Start Value → Must Hit By)":
    if not (min_jp_value <= start_value <= max_jp_value):
        st.error("⚠️ Start value must be between Min and Max.")
        error_flag = True

elif config_mode == "Advanced (Min Hit Value > Initial Value)":
    if initial_value >= min_hit_value:
        st.error("⚠️ Initial Value must be less than Min Hit Value.")
        error_flag = True
    if not (initial_value < min_hit_value <= max_jp_value):
        st.error("⚠️ Min Hit Value must be between Initial Value and Must Hit By.")
        error_flag = True

# -------------------------------
# Section 4: Calculations
# -------------------------------

if not error_flag and total_coin_in > 0:
    st.success("✅ All validations passed")
    
    # Calculate metrics
    avg_hit_value = (hit_range_start + hit_range_end) / 2
    jp_increment_per_day = increment_ratio * total_coin_in
    
    # Time to reach milestones
    if jp_increment_per_day > 0:
        if config_mode == "Advanced (Min Hit Value > Initial Value)":
            days_to_min_hit = (min_hit_value - initial_value) / jp_increment_per_day
            days_to_must_hit = (must_hit_by - initial_value) / jp_increment_per_day
        elif config_mode == "Random Hit (No Start Value)":
            days_to_min_hit = min_jp_value / jp_increment_per_day
            days_to_must_hit = max_jp_value / jp_increment_per_day
        else:
            days_to_min_hit = 0
            days_to_must_hit = (must_hit_by - start_value) / jp_increment_per_day
    else:
        days_to_min_hit = float('inf')
        days_to_must_hit = float('inf')
    
    # Estimate hit frequency (average across possible hit range)
    hit_range_size = hit_range_end - hit_range_start
    if hit_range_size > 0 and jp_increment_per_day > 0:
        avg_cycles_per_month = (30 * jp_increment_per_day) / hit_range_size
        avg_hits_per_month = avg_cycles_per_month
        avg_hits_per_day = avg_hits_per_month / 30
        avg_days_per_hit = 30 / avg_hits_per_month if avg_hits_per_month > 0 else 0
    else:
        avg_hits_per_month = 0
        avg_hits_per_day = 0
        avg_days_per_hit = 0
    
    estimated_jp_paid_per_month = avg_hits_per_month * avg_hit_value
    estimated_jp_paid_per_day = avg_hits_per_day * avg_hit_value
    real_rtp_percent = (estimated_jp_paid_per_day / total_coin_in) * 100 if total_coin_in > 0 else 0
    
    # Display summary metrics
    st.subheader("📊 Summary Metrics")
    
    metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
    
    with metric_col1:
        st.metric("JP Increment/Day", f"€{jp_increment_per_day:,.2f}")
    
    with metric_col2:
        st.metric("Avg Hit Value", f"€{avg_hit_value:,.2f}")
    
    with metric_col3:
        st.metric("Est. Hits/Month", f"{avg_hits_per_month:.2f}")
    
    with metric_col4:
        st.metric("Real RTP %", f"{real_rtp_percent:.2f}%")
    
    # Display timing analysis
    st.subheader("⏱️ Timing Analysis")
    
    timing_col1, timing_col2 = st.columns(2)
    
    with timing_col1:
        if config_mode == "Advanced (Min Hit Value > Initial Value)":
            st.info(f"🕐 **Days to Min Hit Value**: {days_to_min_hit:.1f} days")
            st.info(f"🕐 **Days to Must Hit By**: {days_to_must_hit:.1f} days")
        elif config_mode == "Random Hit (No Start Value)":
            st.info(f"🕐 **Days to reach Min**: {days_to_min_hit:.1f} days")
            st.info(f"🕐 **Days to reach Max**: {days_to_must_hit:.1f} days")
        else:
            st.info(f"🕐 **Days to Must Hit By**: {days_to_must_hit:.1f} days")
    
    with timing_col2:
        if avg_days_per_hit > 0:
            st.info(f"🎯 **Average Hit Frequency**: Every {avg_days_per_hit:.1f} days")
        st.info(f"💸 **Est. Monthly Payout**: €{estimated_jp_paid_per_month:,.2f}")
    
    # Display detailed analysis
    st.subheader("📈 Detailed Analysis")
    
    analysis_data = {
        "Metric": [
            "Configuration Type",
            "Initial Jackpot Value (€)",
            "Min Hit Value (€)" if min_hit_value else "Start Value (€)",
            "Must Hit By Value (€)",
            "Hit Range Size (€)",
            "Average Hit Value (€)",
            "Increment % (Contribution)",
            "JP Increment per Day (€)",
            "Estimated Hits per Day",
            "Estimated Hits per Month",
            "Avg Days Between Hits",
            "Estimated JP Paid / Day (€)",
            "Estimated JP Paid / Month (€)",
            "Real RTP Contribution (%)"
        ],
        "Value": [
            config_mode,
            f"€{initial_value:,.2f}",
            f"€{min_hit_value:,.2f}" if min_hit_value else f"€{start_value:,.2f}",
            f"€{hit_range_end:,.2f}",
            f"€{hit_range_size:,.2f}",
            f"€{avg_hit_value:,.2f}",
            f"{increment_percent:.2f}%",
            f"€{jp_increment_per_day:,.2f}",
            f"{avg_hits_per_day:.3f}",
            f"{avg_hits_per_month:.2f}",
            f"{avg_days_per_hit:.1f}",
            f"€{estimated_jp_paid_per_day:,.2f}",
            f"€{estimated_jp_paid_per_month:,.2f}",
            f"{real_rtp_percent:.2f}%"
        ]
    }
    
    df = pd.DataFrame(analysis_data)
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    # Key insights
    st.subheader("💡 Key Insights")
    
    if config_mode == "Advanced (Min Hit Value > Initial Value)":
        st.info(f"🔒 **Build Phase**: Jackpot will build for {days_to_min_hit:.1f} days before it can hit (from €{initial_value:,.2f} to €{min_hit_value:,.2f})")
        st.info(f"🎲 **Hit Window**: Once at Min Hit Value, jackpot can hit anytime in the next {days_to_must_hit - days_to_min_hit:.1f} days")
    elif config_mode == "Random Hit (No Start Value)":
        st.info(f"🎲 **Random Hit Range**: Jackpot can hit anywhere between €{min_jp_value:,.2f} and €{max_jp_value:,.2f}")
        st.info(f"⏳ **Build Time**: Takes {days_to_must_hit:.1f} days to reach maximum if not hit earlier")
    else:
        st.info(f"📍 **Starting Point**: Jackpot begins at €{start_value:,.2f}")
        st.info(f"⏰ **Must Hit**: Will definitely hit within {days_to_must_hit:.1f} days at €{must_hit_by:,.2f}")
    
    st.info(f"📊 **RTP Impact**: This jackpot contributes {real_rtp_percent:.2f}% to the overall RTP")
    st.info(f"📈 **Daily Growth**: Jackpot pool grows by €{jp_increment_per_day:,.2f} per day from {increment_percent:.2f}% of total coin-in")
    st.info(f"💰 **Expected Frequency**: Approximately {avg_hits_per_month:.1f} jackpot hits per month, averaging €{avg_hit_value:,.2f} each")
