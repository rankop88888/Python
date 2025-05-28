import streamlit as st
import pandas as pd
import json

st.set_page_config(page_title="Mystery Jackpot AI Planner", layout="wide")
st.title("🎰 Mystery Jackpot Planner with DeepSeek AI Optimization")

# -------------------------------
# Section 1: User Inputs
# -------------------------------

st.sidebar.header("🎛 User Input")

input_mode = st.sidebar.radio("Define by:", ["Total Turnover", "Target RTP %"])
if input_mode == "Total Turnover":
    turnover_per_day = st.sidebar.number_input("Total Turnover per Day (ALL)", value=100000)
    target_rtp_percent = None
else:
    target_rtp_percent = st.sidebar.number_input("Target Overall RTP (%)", value=3.5)
    turnover_per_day = None

num_levels = st.sidebar.number_input("Number of Jackpot Levels", min_value=1, max_value=5, value=3)
preset_type = st.sidebar.selectbox("Desired Jackpot Behavior", options=["Normal", "Aggressive", "Lower"])

# -------------------------------
# Section 2: Level Configuration
# -------------------------------

st.subheader("💡 Jackpot Level Configuration")
level_data = []

for level in range(1, num_levels + 1):
    st.markdown(f"### Level {level}")
    start_value = st.number_input(f"Level {level} Start Value (ALL)", value=100 * level, key=f"start_{level}")
    end_value = st.number_input(f"Level {level} End Value (ALL)", value=500 * level, key=f"end_{level}")
    trigger_value = st.number_input(f"Level {level} Trigger Value (ALL)", value=300 * level, key=f"trigger_{level}")
    # Placeholder for now – AI will fill increment ratios
    increment_ratio = st.number_input(f"Level {level} Increment Ratio", value=0.05, step=0.01, format="%.3f", key=f"inc_{level}")

    level_data.append({
        "Level": level,
        "Start Value": start_value,
        "End Value": end_value,
        "Trigger Value": trigger_value,
        "Increment Ratio": increment_ratio
    })

df = pd.DataFrame(level_data)

# -------------------------------
# Section 3: Jackpot Calculations
# -------------------------------

if turnover_per_day:
    df["Avg Hit Value"] = (df["Start Value"] + df["End Value"]) / 2
    df["Hits per Day"] = turnover_per_day / df["Trigger Value"]
    df["Hits per Week"] = df["Hits per Day"] * 7
    df["Hits per Month"] = df["Hits per Day"] * 30
    df["Real RTP (%)"] = ((df["Avg Hit Value"] * df["Hits per Day"]) / turnover_per_day) * 100
    df["Real Cost (ALL)"] = df["Hits per Day"] * df["Avg Hit Value"]
    df["JP Increment per Day (ALL)"] = df["Increment Ratio"] * turnover_per_day

    st.subheader("📊 Jackpot Level Analysis")
    import ace_tools as tools
    tools.display_dataframe_to_user(name="Jackpot Levels", dataframe=df)

    st.success(f"Total Jackpot Increment per Day: ALL{df['JP Increment per Day (ALL)'].sum():,.2f}")
    st.info(f"Total Real RTP from Jackpot: {df['Real RTP (%)'].sum():.2f}%")

# -------------------------------
# Section 4: AI Prompt Builder
# -------------------------------

def generate_ai_prompt():
    level_table = df[["Level", "Start Value", "End Value", "Trigger Value"]].to_dict(orient="records")
    mode_text = f"Turnover = ALL{turnover_per_day}" if input_mode == "Total Turnover" else f"Target RTP = {target_rtp_percent}%"
    return f"""
You are an AI assistant for optimizing jackpot systems for electronic gaming machines (EGMs).

🎯 Goal:
Propose optimized "increment ratios" for each jackpot level based on behavior type, number of levels, and turnover or RTP target.

📥 Input:
- Behavior Type: {preset_type}
- Levels: {num_levels}
- Mode: {mode_text}
- Per-Level Config:
{json.dumps(level_table, indent=2)}

🧠 Guidelines:
- Return a JSON list with one dictionary per level.
- Each dictionary must include: "Level" and "Recommended Increment Ratio".
- Behavior should shape the payout curve:
    - "Aggressive" → higher ratios early, fast RTP buildup.
    - "Normal" → balanced.
    - "Lower" → slow accumulation, long duration.

📤 Output JSON Example:
[
  {{ "Level": 1, "Recommended Increment Ratio": 0.07 }},
  {{ "Level": 2, "Recommended Increment Ratio": 0.05 }},
  ...
]
"""

# -------------------------------
# Section 5: AI Integration Placeholder
# -------------------------------

st.subheader("🔮 AI Recommendation")

if st.button("💡 Request AI Suggestion (DeepSeek R1)"):
    prompt = generate_ai_prompt()
    st.code(prompt, language="markdown")

    # INSERT YOUR DEEPSEEK API CALL HERE:
    # ---------------------------------------
    # Example:
    # response = deepseek.chat(
    #     model="deepseek-chat",
    #     messages=[{"role": "user", "content": prompt}]
    # )
    # ai_output = response['choices'][0]['message']['content']
    # ---------------------------------------

    # For now, simulate mock AI response:
    ai_output = """
    [
      { "Level": 1, "Recommended Increment Ratio": 0.08 },
      { "Level": 2, "Recommended Increment Ratio": 0.06 },
      { "Level": 3, "Recommended Increment Ratio": 0.05 }
    ]
    """

    st.text("✅ AI Suggested Increment Ratios:")
    st.code(ai_output, language="json")

    # Parse and apply to UI
    try:
        suggestions = json.loads(ai_output)
        for suggestion in suggestions:
            level = suggestion["Level"]
            ratio = suggestion["Recommended Increment Ratio"]
            df.loc[df["Level"] == level, "Increment Ratio"] = ratio
        st.success("✔️ Updated increment ratios with AI suggestions.")
        import ace_tools as tools
        tools.display_dataframe_to_user(name="AI-Optimized Jackpot Levels", dataframe=df)
    except Exception as e:
        st.error(f"Failed to parse AI output: {e}")
