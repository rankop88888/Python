import streamlit as st
import pandas as pd
import json

st.set_page_config(page_title="Unified Jackpot Planner", layout="wide")
st.title("🎰 Jackpot Planner - Mystery & Progressive")

# -------------------------------
# Section 1: Jackpot Type Selection
# -------------------------------

st.sidebar.header("Jackpot Type")
jackpot_type = st.sidebar.radio(
    "Select Jackpot Type:",
    ["Mystery Progressive", "Standard Multi-Level Progressive"],
    help="Mystery: hits randomly in range. Standard: hits on trigger value"
)

# -------------------------------
# Section 2: Total Coin-In
# -------------------------------

st.markdown("### 💰 Total Coin-In per Day")
st.markdown("*Combined turnover from all EGMs included in the jackpot*")
total_coin_in = st.number_input("Total Turnover per Day (€)", value=100000, min_value=0, key="coin_in")
st.markdown(f"<h1 style='text-align: center; color: #1f77b4;'>€{total_coin_in:,.2f}</h1>", unsafe_allow_html=True)

st.divider()

# -------------------------------
# Section 3: Number of Levels
# -------------------------------

st.sidebar.header("Configuration")
num_levels = st.sidebar.number_input("Number of Jackpot Levels", min_value=1, max_value=5, value=1)

if jackpot_type == "Standard Multi-Level Progressive":
    preset_type = st.sidebar.selectbox("Desired Jackpot Behavior", options=["Normal", "Aggressive", "Lower"])

# -------------------------------
# Section 4: Level Configuration
# -------------------------------

st.subheader(f"🎯 {jackpot_type} - Level Configuration")

if jackpot_type == "Mystery Progressive":
    st.info("💡 **Mystery Progressive**: Jackpot hits randomly when value reaches somewhere between Start Value and Must Hit By")
else:
    st.info("💡 **Standard Progressive**: Jackpot hits when specific trigger turnover is reached")

level_data = []
error_flag = False

for level in range(1, num_levels + 1):
    st.markdown(f"### Level {level}")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**Range Settings**")
        min_value = st.number_input(f"L{level} Minimum JP (€)", value=100 * level, key=f"min_{level}", min_value=0)
        max_value = st.number_input(f"L{level} Maximum JP (Must Hit By) (€)", value=1000 * level, key=f"max_{level}", min_value=0)
    
    with col2:
        st.markdown("**Start Settings**")
        start_value = st.number_input(f"L{level} Start Value (€)", value=100 * level, key=f"start_{level}", min_value=0,
                                     help="Initial jackpot amount (seed money)")
        
        if jackpot_type == "Standard Multi-Level Progressive":
            trigger_value = st.number_input(f"L{level} Trigger Value (€)", 
                                          value=(min_value + max_value) / 2, 
                                          key=f"trigger_{level}", 
                                          min_value=1,
                                          help="Turnover needed for 1 JP hit")
        else:
            trigger_value = None
    
    with col3:
        st.markdown("**Contribution**")
        increment_percent = st.number_input(f"L{level} Increment %", value=1.0 * level, step=0.1, format="%.2f", 
                                          key=f"inc_{level}", min_value=0.0,
                                          help="% of coin-in that accumulates")
        increment_ratio = increment_percent / 100
        
        if jackpot_type == "Mystery Progressive":
            st.metric("Daily Accumulation", f"€{increment_ratio * total_coin_in:,.2f}")

    # --- Validations ---
    if min_value >= max_value:
        st.warning(f"Level {level}: Minimum must be less than Maximum.")
        error_flag = True
    
    if not (min_value <= start_value <= max_value):
        st.warning(f"Level {level}: Start value must be between Min and Max.")
        error_flag = True
    
    if jackpot_type == "Standard Multi-Level Progressive":
        if trigger_value and not (min_value <= trigger_value <= max_value):
            st.warning(f"Level {level}: Trigger must be between Min and Max.")
            error_flag = True
    
    if increment_ratio < 0:
        st.warning(f"Level {level}: Increment % must be non-negative.")
        error_flag = True

    level_data.append({
        "Level": level,
        "Start Value": start_value,
        "Min Value": min_value,
        "Max Value": max_value,
        "Trigger Value": trigger_value,
        "Increment %": increment_percent,
        "Increment Ratio": increment_ratio
    })

    st.divider()

df = pd.DataFrame(level_data)

# -------------------------------
# Section 5: Calculations
# -------------------------------

if not error_flag and total_coin_in > 0:
    st.success("✅ All validations passed")
    
    # Calculate based on jackpot type
    if jackpot_type == "Mystery Progressive":
        # Mystery Progressive Calculations
        df["Hit Range Size (€)"] = df["Max Value"] - df["Start Value"]
        df["Avg Hit Value (€)"] = (df["Start Value"] + df["Max Value"]) / 2
        df["Accumulation per Day (€)"] = df["Increment Ratio"] * total_coin_in
        
        # Calculate time to reach max
        df["Days to Must Hit"] = df["Hit Range Size (€)"] / df["Accumulation per Day (€)"]
        df["Days to Must Hit"] = df["Days to Must Hit"].replace([float('inf'), float('-inf')], 0)
        
        # Estimate hit frequency (conservative: assume hits near max)
        df["Est. Cycle Days"] = df["Days to Must Hit"]
        df["Hits per Month"] = 30 / df["Est. Cycle Days"]
        df["Hits per Month"] = df["Hits per Month"].replace([float('inf'), float('-inf')], 0)
        df["Hits per Day"] = df["Hits per Month"] / 30
        
        # CORRECTED: Real increment excludes start value (seed money)
        df["Real Increment per Hit (€)"] = df["Avg Hit Value (€)"] - df["Start Value"]
        df["Real Increment per Day (€)"] = df["Hits per Day"] * df["Real Increment per Hit (€)"]
        df["Total Cost per Day (€)"] = df["Hits per Day"] * df["Avg Hit Value (€)"]
        df["Total Cost per Month (€)"] = df["Total Cost per Day (€)"] * 30
        
        # Real RTP based on actual increment from coin-in
        df["Real RTP (%)"] = (df["Real Increment per Day (€)"] / total_coin_in) * 100
        
    else:
        # Standard Progressive Calculations
        df["Avg Hit Value (€)"] = (df["Start Value"] + df["Max Value"]) / 2
        df["Hits per Day"] = total_coin_in / df["Trigger Value"]
        df["Hits per Day"] = df["Hits per Day"].replace([float('inf'), float('-inf')], 0)
        df["Hits per Month"] = df["Hits per Day"] * 30
        df["Avg Days per Hit"] = 1 / df["Hits per Day"]
        df["Avg Days per Hit"] = df["Avg Days per Hit"].replace([float('inf'), float('-inf')], 0)
        
        # CORRECTED: Real increment excludes start value (seed money)
        df["Real Increment per Hit (€)"] = df["Avg Hit Value (€)"] - df["Start Value"]
        df["Real Increment per Day (€)"] = df["Hits per Day"] * df["Real Increment per Hit (€)"]
        df["Accumulation per Day (€)"] = df["Increment Ratio"] * total_coin_in
        df["Total Cost per Day (€)"] = df["Hits per Day"] * df["Avg Hit Value (€)"]
        df["Total Cost per Month (€)"] = df["Total Cost per Day (€)"] * 30
        
        # Real RTP based on actual increment from coin-in
        df["Real RTP (%)"] = (df["Real Increment per Day (€)"] / total_coin_in) * 100

    # -------------------------------
    # Section 6: Display Results
    # -------------------------------
    
    st.subheader("📊 Summary Metrics")
    
    total_accumulation = df["Accumulation per Day (€)"].sum()
    total_real_increment = df["Real Increment per Day (€)"].sum()
    total_rtp = df["Real RTP (%)"].sum()
    total_cost_day = df["Total Cost per Day (€)"].sum()
    total_cost_month = df["Total Cost per Month (€)"].sum()
    
    metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
    
    with metric_col1:
        st.metric("Accumulation/Day", f"€{total_accumulation:,.2f}", 
                 help="Amount accumulated from coin-in per day")
    
    with metric_col2:
        st.metric("Real Increment/Day", f"€{total_real_increment:,.2f}",
                 help="Actual increment paid (excluding start values)")
    
    with metric_col3:
        st.metric("Real RTP %", f"{total_rtp:.2f}%",
                 help="RTP from jackpot increments only")
    
    with metric_col4:
        st.metric("Total Cost/Day", f"€{total_cost_day:,.2f}",
                 help="Total jackpot payouts including start values")
    
    # Cost breakdown
    st.info(f"""
    💡 **Cost Breakdown**:
    - **Total Cost/Day**: €{total_cost_day:,.2f} (includes seed money + increments)
    - **Real Increment/Day**: €{total_real_increment:,.2f} (from coin-in only)
    - **Seed Money/Day**: €{total_cost_day - total_real_increment:,.2f} (start value costs)
    - **Total Cost/Month**: €{total_cost_month:,.2f}
    """)
    
    # Display detailed table
    st.subheader("📈 Detailed Analysis by Level")
    
    if jackpot_type == "Mystery Progressive":
        display_cols = ["Level", "Start Value", "Max Value", "Avg Hit Value (€)", 
                       "Increment %", "Accumulation per Day (€)", "Days to Must Hit",
                       "Hits per Month", "Real Increment per Hit (€)", "Real Increment per Day (€)",
                       "Total Cost per Month (€)", "Real RTP (%)"]
    else:
        display_cols = ["Level", "Start Value", "Max Value", "Trigger Value", "Avg Hit Value (€)",
                       "Increment %", "Accumulation per Day (€)", "Hits per Day", "Avg Days per Hit",
                       "Real Increment per Hit (€)", "Real Increment per Day (€)",
                       "Total Cost per Month (€)", "Real RTP (%)"]
    
    display_df = df[display_cols].copy()
    
    # Format numeric columns
    for col in display_df.columns:
        if col not in ["Level"]:
            if "%" in col:
                display_df[col] = display_df[col].apply(lambda x: f"{x:.2f}%")
            elif "€" in col or "Value" in col:
                display_df[col] = display_df[col].apply(lambda x: f"€{x:,.2f}" if isinstance(x, (int, float)) else x)
            elif "Days" in col or "Hits" in col:
                display_df[col] = display_df[col].apply(lambda x: f"{x:.2f}" if isinstance(x, (int, float)) else x)
    
    st.dataframe(display_df, use_container_width=True, hide_index=True)
    
    # Key Insights
    st.subheader("💡 Key Insights")
    
    for idx, row in df.iterrows():
        level = int(row["Level"])
        seed_cost_per_hit = row['Start Value']
        real_inc_per_hit = row['Real Increment per Hit (€)']
        
        if jackpot_type == "Mystery Progressive":
            st.info(f"""
            **Level {level} ({jackpot_type})**:
            - 🎲 Hits randomly between €{row['Start Value']:,.2f} and €{row['Max Value']:,.2f}
            - ⏰ Takes {row['Days to Must Hit']:.1f} days to reach Must Hit By
            - 📊 Contributes {row['Real RTP (%)']:.2f}% to RTP (real increment only)
            - 💰 Expected {row['Hits per Month']:.1f} hits/month averaging €{row['Avg Hit Value (€)']:,.2f}
            - 📈 Accumulates €{row['Accumulation per Day (€)']:,.2f}/day ({row['Increment %']:.2f}% of coin-in)
            - 💵 Real increment per hit: €{real_inc_per_hit:,.2f} (excludes €{seed_cost_per_hit:,.2f} seed)
            - 🎯 Total cost per month: €{row['Total Cost per Month (€)']:,.2f}
            """)
        else:
            st.info(f"""
            **Level {level} ({jackpot_type})**:
            - 🎯 Hits at trigger value €{row['Trigger Value']:,.2f}
            - ⏰ Average {row['Avg Days per Hit']:.1f} days between hits
            - 📊 Contributes {row['Real RTP (%)']:.2f}% to RTP (real increment only)
            - 💰 Expected {row['Hits per Month']:.1f} hits/month averaging €{row['Avg Hit Value (€)']:,.2f}
            - 📈 Accumulates €{row['Accumulation per Day (€)']:,.2f}/day ({row['Increment %']:.2f}% of coin-in)
            - 💵 Real increment per hit: €{real_inc_per_hit:,.2f} (excludes €{seed_cost_per_hit:,.2f} seed)
            - 🎯 Total cost per month: €{row['Total Cost per Month (€)']:,.2f}
            """)

# -------------------------------
# Section 7: AI Optimization (for Standard Progressive only)
# -------------------------------

if jackpot_type == "Standard Multi-Level Progressive" and num_levels > 1:
    st.divider()
    st.subheader("🤖 AI Optimization")
    
    def generate_ai_prompt():
        level_table = df[["Level", "Start Value", "Max Value", "Trigger Value", "Min Value", "Increment %"]].to_dict(orient="records")
        return f'''
You are an AI assistant for optimizing jackpot systems for electronic gaming machines (EGMs).

Goal:
Propose optimized "increment ratios" for each jackpot level based on behavior type, number of levels, and turnover.

Input:
- Behavior Type: {preset_type}
- Levels: {num_levels}
- Total Coin-In: €{total_coin_in}
- Per-Level Config:
{json.dumps(level_table, indent=2)}

Guidelines:
- Return a JSON list with one dictionary per level.
- Each dictionary must include: "Level" and "Recommended Increment Ratio" (as decimal, e.g., 0.05 for 5%).
- Behavior should shape the payout curve:
    - "Aggressive" -> higher ratios early, fast RTP buildup.
    - "Normal" -> balanced distribution.
    - "Lower" -> slow accumulation, longer duration.

Output JSON Example:
[
  {{"Level": 1, "Recommended Increment Ratio": 0.07}},
  {{"Level": 2, "Recommended Increment Ratio": 0.05}}
]
'''

    if not error_flag and st.button("🚀 Request AI Suggestion (DeepSeek R1)"):
        prompt = generate_ai_prompt()
        
        with st.expander("View AI Prompt"):
            st.code(prompt, language="markdown")

        # Placeholder for DeepSeek integration
        ai_output = '''[
  {"Level": 1, "Recommended Increment Ratio": 0.08},
  {"Level": 2, "Recommended Increment Ratio": 0.06},
  {"Level": 3, "Recommended Increment Ratio": 0.05}
]'''

        st.markdown("**AI Suggested Increment Ratios:**")
        st.code(ai_output, language="json")

        try:
            suggestions = json.loads(ai_output)
            st.success(f"✅ AI suggested {len(suggestions)} optimized increment ratios")
            
            # Show comparison
            comparison_data = []
            for suggestion in suggestions:
                level = suggestion["Level"]
                recommended_ratio = suggestion["Recommended Increment Ratio"]
                current_ratio = df.loc[df["Level"] == level, "Increment Ratio"].values[0]
                
                comparison_data.append({
                    "Level": level,
                    "Current %": f"{current_ratio * 100:.2f}%",
                    "Recommended %": f"{recommended_ratio * 100:.2f}%",
                    "Change": f"{(recommended_ratio - current_ratio) * 100:+.2f}%"
                })
            
            comparison_df = pd.DataFrame(comparison_data)
            st.dataframe(comparison_df, use_container_width=True, hide_index=True)
            
            if st.button("✅ Apply AI Recommendations"):
                for suggestion in suggestions:
                    level = suggestion["Level"]
                    ratio = suggestion["Recommended Increment Ratio"]
                    df.loc[df["Level"] == level, "Increment Ratio"] = ratio
                    df.loc[df["Level"] == level, "Increment %"] = ratio * 100
                st.success("✅ Applied AI recommendations! Scroll up to see updated analysis.")
                st.rerun()
                
        except Exception as e:
            st.error(f"❌ Failed to parse AI output: {e}")
