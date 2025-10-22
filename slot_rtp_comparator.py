import math
from typing import List, Tuple

import numpy as np
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

st.set_page_config(page_title="Slot RTP Comparator", layout="wide")

# ---------- Constants ----------
CONF_TO_Z = {
    0.95: 1.959963984540054,
    0.99: 2.5758293035489004,
}

PLOT_POINTS = 600
SE_RANGE_MULTIPLIER = 5

# ---------- Helper Functions ----------
def volatility_index_to_sd(vi: float, rtp: float, conf_level: float) -> float:
    """Convert Volatility Index to Standard Deviation per spin."""
    z = CONF_TO_Z[conf_level]
    return vi / z

def sd_to_volatility_index(sd: float, conf_level: float) -> float:
    """Convert Standard Deviation per spin to Volatility Index."""
    z = CONF_TO_Z[conf_level]
    return sd * z

def normal_pdf(x: np.ndarray, mu: float, sigma: float) -> np.ndarray:
    """Calculate normal probability density function."""
    if sigma <= 0:
        return np.zeros_like(x)
    c = 1.0 / (sigma * math.sqrt(2.0 * math.pi))
    return c * np.exp(-0.5 * ((x - mu) / sigma) ** 2)

def ci_for_mean(rtp_pct: float, sd_pct_per_spin: float, n: int, z: float) -> Tuple[float, float]:
    """Calculate confidence interval for mean RTP."""
    if n <= 0 or sd_pct_per_spin < 0:
        return (np.nan, np.nan)
    se = sd_pct_per_spin / math.sqrt(n)
    lo = rtp_pct - z * se
    hi = rtp_pct + z * se
    return (max(0.0, lo), min(200.0, hi))

def ci_for_proportion(p: float, n: int, z: float) -> Tuple[float, float]:
    """Calculate confidence interval for hit rate (proportion) using normal approximation."""
    if n <= 0 or p < 0 or p > 1:
        return (np.nan, np.nan)
    # Standard error for proportion
    se = math.sqrt(p * (1 - p) / n)
    lo = p - z * se
    hi = p + z * se
    return (max(0.0, lo), min(1.0, hi))

def cis_overlap(ci1: Tuple[float, float], ci2: Tuple[float, float]) -> bool:
    """Check if two confidence intervals overlap."""
    if np.isnan(ci1[0]) or np.isnan(ci2[0]):
        return False
    return ci1[0] <= ci2[1] and ci2[0] <= ci1[1]

def sample_size_for_separation(rtp1: float, sd1: float, rtp2: float, sd2: float, z: float) -> int:
    """Estimate sample size needed for CIs to not overlap (conservative estimate)."""
    diff = abs(rtp1 - rtp2)
    if diff < 0.001:
        return np.inf
    combined_sd = sd1 + sd2
    n = ((z * combined_sd) / diff) ** 2
    return int(np.ceil(n)) if not np.isinf(n) else np.inf

def sample_size_for_hitrate_separation(hr1: float, hr2: float, z: float) -> int:
    """Estimate sample size needed for hit rate CIs to not overlap."""
    diff = abs(hr1 - hr2)
    if diff < 0.0001:
        return np.inf
    # Conservative estimate: need z * (se1 + se2) < diff
    # se = sqrt(p*(1-p)/n), so we need to solve for n
    combined_sd = math.sqrt(hr1 * (1 - hr1)) + math.sqrt(hr2 * (1 - hr2))
    n = ((z * combined_sd) / diff) ** 2
    return int(np.ceil(n)) if not np.isinf(n) else np.inf

def ci_table(name: str, rtp_pct: float, sd_pct_per_spin: float, pulls: List[int], z: float) -> pd.DataFrame:
    """Generate confidence interval table for given parameters."""
    rows = []
    for n in sorted(set(int(x) for x in pulls if x and x > 0)):
        lo, hi = ci_for_mean(rtp_pct, sd_pct_per_spin, n, z)
        rows.append({
            "Game": name,
            "Pulls": n,
            "RTP %": rtp_pct,
            "CI Low %": lo,
            "CI High %": hi,
            "CI Width %": hi - lo
        })
    return pd.DataFrame(rows)

def hitrate_table(name: str, hit_rate: float, pulls: List[int], z: float) -> pd.DataFrame:
    """Generate hit rate confidence interval table."""
    rows = []
    for n in sorted(set(int(x) for x in pulls if x and x > 0)):
        lo, hi = ci_for_proportion(hit_rate, n, z)
        rows.append({
            "Game": name,
            "Pulls": n,
            "Hit Rate": hit_rate,
            "CI Low": lo,
            "CI High": hi,
            "CI Width": hi - lo
        })
    return pd.DataFrame(rows)

def plot_comparison(ax, rtp1: float, sd1: float, rtp2: float, sd2: float, 
                   n: int, name1: str, name2: str, z: float):
    """Plot overlaid sampling distributions for both games."""
    if n <= 0 or sd1 <= 0 or sd2 <= 0:
        ax.text(0.5, 0.5, "Insufficient parameters", ha="center", va="center", 
                transform=ax.transAxes)
        return
    
    se1 = sd1 / math.sqrt(n)
    se2 = sd2 / math.sqrt(n)
    
    min_val = min(rtp1 - SE_RANGE_MULTIPLIER * se1, rtp2 - SE_RANGE_MULTIPLIER * se2)
    max_val = max(rtp1 + SE_RANGE_MULTIPLIER * se1, rtp2 + SE_RANGE_MULTIPLIER * se2)
    xs = np.linspace(min_val, max_val, PLOT_POINTS)
    
    ys1 = normal_pdf(xs, rtp1, se1)
    ys2 = normal_pdf(xs, rtp2, se2)
    
    ax.plot(xs, ys1, label=f"{name1}", color='#1f77b4', linewidth=2)
    ax.plot(xs, ys2, label=f"{name2}", color='#ff7f0e', linewidth=2)
    
    lo1, hi1 = ci_for_mean(rtp1, sd1, n, z)
    lo2, hi2 = ci_for_mean(rtp2, sd2, n, z)
    
    ax.axvline(rtp1, color='#1f77b4', linestyle=':', alpha=0.7, label=f'{name1} mean')
    ax.axvspan(lo1, hi1, alpha=0.2, color='#1f77b4')
    
    ax.axvline(rtp2, color='#ff7f0e', linestyle=':', alpha=0.7, label=f'{name2} mean')
    ax.axvspan(lo2, hi2, alpha=0.2, color='#ff7f0e')
    
    ax.set_xlabel("Sample Mean RTP (%)", fontsize=10)
    ax.set_ylabel("Density", fontsize=10)
    ax.set_title(f"RTP Sampling Distributions at n={n:,} spins", fontsize=11, fontweight='bold')
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)

def plot_hitrate_comparison(ax, hr1: float, hr2: float, n: int, name1: str, name2: str, z: float):
    """Plot overlaid hit rate sampling distributions."""
    if n <= 0 or hr1 < 0 or hr1 > 1 or hr2 < 0 or hr2 > 1:
        ax.text(0.5, 0.5, "Insufficient parameters", ha="center", va="center", 
                transform=ax.transAxes)
        return
    
    se1 = math.sqrt(hr1 * (1 - hr1) / n)
    se2 = math.sqrt(hr2 * (1 - hr2) / n)
    
    min_val = max(0, min(hr1 - SE_RANGE_MULTIPLIER * se1, hr2 - SE_RANGE_MULTIPLIER * se2))
    max_val = min(1, max(hr1 + SE_RANGE_MULTIPLIER * se1, hr2 + SE_RANGE_MULTIPLIER * se2))
    xs = np.linspace(min_val, max_val, PLOT_POINTS)
    
    ys1 = normal_pdf(xs, hr1, se1)
    ys2 = normal_pdf(xs, hr2, se2)
    
    ax.plot(xs, ys1, label=f"{name1}", color='#2ca02c', linewidth=2)
    ax.plot(xs, ys2, label=f"{name2}", color='#d62728', linewidth=2)
    
    lo1, hi1 = ci_for_proportion(hr1, n, z)
    lo2, hi2 = ci_for_proportion(hr2, n, z)
    
    ax.axvline(hr1, color='#2ca02c', linestyle=':', alpha=0.7, label=f'{name1} mean')
    ax.axvspan(lo1, hi1, alpha=0.2, color='#2ca02c')
    
    ax.axvline(hr2, color='#d62728', linestyle=':', alpha=0.7, label=f'{name2} mean')
    ax.axvspan(lo2, hi2, alpha=0.2, color='#d62728')
    
    ax.set_xlabel("Sample Hit Rate (proportion)", fontsize=10)
    ax.set_ylabel("Density", fontsize=10)
    ax.set_title(f"Hit Rate Sampling Distributions at n={n:,} spins", fontsize=11, fontweight='bold')
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)
    
    # Format x-axis as percentages
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x*100:.1f}%'))

# ---------- UI ----------
st.title("🎰 Slot Machine RTP Comparator")
st.markdown("Compare the statistical reliability of RTP and hit rate measurements across different slot machines.")

# Initialize session state for pulls
if 'pulls' not in st.session_state:
    st.session_state.pulls = [10000, 100000, 1000000, 10000000]

with st.sidebar:
    st.header("⚙️ Configuration")
    
    conf = st.selectbox(
        "Confidence Level",
        [0.95, 0.99],
        index=0,
        format_func=lambda x: f"{int(x*100)}%",
        help="95% and 99% are industry standards for slot testing"
    )
    z = CONF_TO_Z[conf]

    st.markdown("**Number of Hand Pulls**")
    
    # Display current pulls
    pulls_display = st.multiselect(
        "Selected sample sizes", 
        sorted(st.session_state.pulls),
        sorted(st.session_state.pulls),
        help="Number of spins to analyze",
        key="pulls_multiselect"
    )
    st.session_state.pulls = pulls_display
    
    # Add new pull count
    col1, col2 = st.columns([3, 1])
    with col1:
        new_pull = st.number_input("Add custom size", min_value=1, step=1, value=50000, key="new_pull_input")
    with col2:
        st.write("")
        if st.button("Add", use_container_width=True):
            if new_pull not in st.session_state.pulls:
                st.session_state.pulls = sorted(st.session_state.pulls + [int(new_pull)])
                st.rerun()

    st.divider()
    st.caption("💡 **RTP** = Return to Player (%). **Hit Rate** = Probability of winning spin. **VI** = Volatility Index.")

pulls = st.session_state.pulls

# Game input columns
colA, colB = st.columns(2, gap="large")

def game_input_block(col, game_id: str, default_name: str, default_rtp: float, default_vi: float, default_hr: float):
    """Create input block for a single game."""
    with col:
        st.subheader(f"🎮 {default_name}")
        name = st.text_input(
            "Game Name", 
            value=default_name, 
            key=f"name_{game_id}",
            help="Identifier for this slot machine"
        )
        
        # Option to enter RTP or Hold Percentage
        input_method = st.radio(
            "Input Method",
            ["RTP (%)", "Hold Percentage (%)"],
            key=f"input_method_{game_id}",
            horizontal=True,
            help="RTP = 100% - Hold%. Hold% is house edge."
        )
        
        if input_method == "RTP (%)":
            rtp_pct = st.number_input(
                "RTP (%)",
                min_value=0.0, 
                max_value=200.0, 
                value=default_rtp, 
                step=0.1,
                key=f"rtp_{game_id}",
                help="Expected return to player per spin"
            )
            hold_pct = 100.0 - rtp_pct
            st.caption(f"📊 Hold Percentage: {hold_pct:.2f}%")
        else:
            hold_pct = st.number_input(
                "Hold Percentage (%)",
                min_value=0.0,
                max_value=100.0,
                value=100.0 - default_rtp,
                step=0.01,
                key=f"hold_{game_id}",
                help="House edge (100% - RTP)"
            )
            rtp_pct = 100.0 - hold_pct
            st.caption(f"📊 RTP: {rtp_pct:.2f}%")
        
        hit_rate = st.number_input(
            "Hit Rate (%)",
            min_value=0.0,
            max_value=100.0,
            value=default_hr,
            step=0.1,
            key=f"hr_{game_id}",
            help="Percentage of spins that result in a win"
        ) / 100.0  # Convert to proportion
        
        st.markdown("**Volatility Input Method**")
        use_vi = st.radio(
            "Choose input type",
            ["Volatility Index", "Standard Deviation"],
            key=f"vol_type_{game_id}",
            help="Volatility Index is industry standard (typically 1-15). SD is raw statistical measure."
        )
        
        if use_vi == "Volatility Index":
            vi = st.number_input(
                "Volatility Index",
                min_value=0.1, 
                max_value=50.0, 
                value=default_vi, 
                step=0.1,
                key=f"vi_{game_id}",
                help="Typical range: Low (1-5), Medium (5-10), High (10-15)"
            )
            sd_pct = volatility_index_to_sd(vi, rtp_pct, conf)
            st.caption(f"📊 Calculated SD per spin: {sd_pct:.2f}%")
        else:
            sd_pct = st.number_input(
                "Standard Deviation per spin (%)",
                min_value=0.1, 
                max_value=500.0, 
                value=volatility_index_to_sd(default_vi, default_rtp, conf), 
                step=1.0,
                key=f"sd_{game_id}",
                help="Raw statistical standard deviation per spin"
            )
            vi = sd_to_volatility_index(sd_pct, conf)
            st.caption(f"📊 Calculated Volatility Index: {vi:.2f}")
        
        if vi > 15:
            st.warning("⚠️ Very high volatility - unusual for most slot machines")
        if rtp_pct > 100:
            st.info("ℹ️ RTP > 100% means player advantage")
        if hit_rate > 0.5:
            st.info("ℹ️ High hit rate (>50%) - frequent small wins expected")
            
    return name, rtp_pct, sd_pct, hit_rate

nameA, rtpA, sdA, hrA = game_input_block(colA, "A", "Game A", 95.08, 5.795, 25.0)
nameB, rtpB, sdB, hrB = game_input_block(colB, "B", "Game B", 95.08, 5.795, 25.0)

# Validate inputs
if sdA <= 0 or sdB <= 0:
    st.error("❌ Volatility/SD must be greater than 0")
    st.stop()

if len(pulls) == 0:
    st.error("❌ Please select at least one sample size")
    st.stop()

# ---------- Analysis ----------
st.markdown("---")

# Create tabs for RTP and Hit Rate analysis
tab1, tab2 = st.tabs(["📊 RTP Analysis", "🎯 Hit Rate Analysis"])

with tab1:
    st.header("RTP Statistical Analysis")
    
    # Calculate tables
    tableA = ci_table(nameA, rtpA, sdA, pulls, z)
    tableB = ci_table(nameB, rtpB, sdB, pulls, z)
    
    # Merge and add overlap analysis
    comparison = tableA.merge(tableB, on="Pulls", suffixes=(f" ({nameA})", f" ({nameB})"))
    
    # Add overlap column
    overlap_data = []
    for _, row in comparison.iterrows():
        n = row["Pulls"]
        ci1 = ci_for_mean(rtpA, sdA, n, z)
        ci2 = ci_for_mean(rtpB, sdB, n, z)
        overlap_data.append(cis_overlap(ci1, ci2))
    
    comparison["CIs Overlap?"] = ["Yes" if x else "No" for x in overlap_data]
    
    # Calculate separation threshold
    sep_n = sample_size_for_separation(rtpA, sdA, rtpB, sdB, z)
    
    # Display key insights
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("RTP Difference", f"{abs(rtpA - rtpB):.3f}%")
    with col2:
        hold_diff = abs((100 - rtpA) - (100 - rtpB))
        st.metric("Hold % Difference", f"{hold_diff:.3f}%")
    with col3:
        if abs(rtpA - rtpB) < 0.001:
            st.metric("Higher RTP", "Equal")
        else:
            better = nameA if rtpA > rtpB else nameB
            st.metric("Higher RTP", better)
    with col4:
        if sep_n == np.inf:
            st.metric("Pulls to Distinguish", "N/A (same RTP)")
        elif sep_n > 1_000_000:
            st.metric("Pulls to Distinguish", f">{1_000_000:,}")
        else:
            st.metric("Pulls to Distinguish", f"~{sep_n:,}")
    
    st.markdown("### RTP Confidence Interval Comparison")
    
    # Add Hold Percentage columns
    comparison_display = comparison.copy()
    comparison_display[f"Hold % ({nameA})"] = 100 - comparison_display[f"RTP % ({nameA})"]
    comparison_display[f"Hold % ({nameB})"] = 100 - comparison_display[f"RTP % ({nameB})"]
    
    # Reorder columns for better display
    display_cols = ["Pulls"]
    # Game A columns
    display_cols.extend([f"RTP % ({nameA})", f"Hold % ({nameA})", 
                        f"CI Low % ({nameA})", f"CI High % ({nameA})", f"CI Width % ({nameA})"])
    # Game B columns  
    display_cols.extend([f"RTP % ({nameB})", f"Hold % ({nameB})",
                        f"CI Low % ({nameB})", f"CI High % ({nameB})", f"CI Width % ({nameB})"])
    display_cols.append("CIs Overlap?")
    
    st.dataframe(
        comparison_display[display_cols].style.format({
            col: "{:.3f}" for col in comparison_display.columns if "%" in col and col != "CIs Overlap?"
        }),
        use_container_width=True,
        height=400
    )
    
    # Download button
    csv = comparison.to_csv(index=False)
    st.download_button(
        label="📥 Download RTP Table as CSV",
        data=csv,
        file_name=f"rtp_comparison_{nameA}_vs_{nameB}.csv",
        mime="text/csv"
    )
    
    # Visualization
    st.markdown("---")
    st.subheader("📈 RTP Distribution Visualization")
    
    if len(pulls) > 0:
        viz_n = st.select_slider(
            "Select sample size to visualize RTP distributions",
            options=sorted(set(comparison["Pulls"])),
            value=int(sorted(set(comparison["Pulls"]))[min(2, len(set(comparison['Pulls']))-1)]),
            key="rtp_viz"
        )
        
        # Overlay plot
        fig, ax = plt.subplots(figsize=(12, 6))
        plot_comparison(ax, rtpA, sdA, rtpB, sdB, viz_n, nameA, nameB, z)
        st.pyplot(fig, clear_figure=True)
        
        # Interpretation
        ci1 = ci_for_mean(rtpA, sdA, viz_n, z)
        ci2 = ci_for_mean(rtpB, sdB, viz_n, z)
        overlap = cis_overlap(ci1, ci2)
        
        if overlap:
            st.info(f"ℹ️ At **{viz_n:,} spins**, the {int(conf*100)}% confidence intervals **overlap**. "
                    f"The observed RTP difference could be due to random variation.")
        else:
            st.success(f"✅ At **{viz_n:,} spins**, the {int(conf*100)}% confidence intervals **do not overlap**. "
                       f"The RTP difference is likely statistically meaningful.")

with tab2:
    st.header("Hit Rate Statistical Analysis")
    
    # Calculate hit rate tables
    hrTableA = hitrate_table(nameA, hrA, pulls, z)
    hrTableB = hitrate_table(nameB, hrB, pulls, z)
    
    # Merge and add overlap analysis
    hr_comparison = hrTableA.merge(hrTableB, on="Pulls", suffixes=(f" ({nameA})", f" ({nameB})"))
    
    # Add overlap column
    hr_overlap_data = []
    for _, row in hr_comparison.iterrows():
        n = row["Pulls"]
        ci1 = ci_for_proportion(hrA, n, z)
        ci2 = ci_for_proportion(hrB, n, z)
        hr_overlap_data.append(cis_overlap(ci1, ci2))
    
    hr_comparison["CIs Overlap?"] = ["Yes" if x else "No" for x in hr_overlap_data]
    
    # Calculate separation threshold for hit rate
    hr_sep_n = sample_size_for_hitrate_separation(hrA, hrB, z)
    
    # Display key insights
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Hit Rate Difference", f"{abs(hrA - hrB)*100:.2f}%")
    with col2:
        if abs(hrA - hrB) < 0.0001:
            st.metric("Higher Hit Rate", "Equal")
        else:
            better_hr = nameA if hrA > hrB else nameB
            st.metric("Higher Hit Rate", better_hr)
    with col3:
        if hr_sep_n == np.inf:
            st.metric("Pulls to Distinguish", "N/A (same rate)")
        elif hr_sep_n > 1_000_000:
            st.metric("Pulls to Distinguish", f">{1_000_000:,}")
        else:
            st.metric("Pulls to Distinguish", f"~{hr_sep_n:,}")
    
    st.markdown("### Hit Rate Confidence Interval Comparison")
    
    # Format hit rates as percentages for display
    hr_display = hr_comparison.copy()
    for col in hr_display.columns:
        if "Hit Rate" in col or "CI Low" in col or "CI High" in col or "CI Width" in col:
            if col != "Pulls" and col != "CIs Overlap?":
                hr_display[col] = hr_display[col] * 100
    
    st.dataframe(
        hr_display.style.format({
            col: "{:.2f}%" for col in hr_display.columns 
            if ("Hit Rate" in col or "CI" in col) and col != "CIs Overlap?"
        }),
        use_container_width=True,
        height=400
    )
    
    # Download button
    csv_hr = hr_comparison.to_csv(index=False)
    st.download_button(
        label="📥 Download Hit Rate Table as CSV",
        data=csv_hr,
        file_name=f"hitrate_comparison_{nameA}_vs_{nameB}.csv",
        mime="text/csv"
    )
    
    # Visualization
    st.markdown("---")
    st.subheader("📈 Hit Rate Distribution Visualization")
    
    if len(pulls) > 0:
        viz_n_hr = st.select_slider(
            "Select sample size to visualize hit rate distributions",
            options=sorted(set(hr_comparison["Pulls"])),
            value=int(sorted(set(hr_comparison["Pulls"]))[min(2, len(set(hr_comparison['Pulls']))-1)]),
            key="hr_viz"
        )
        
        # Overlay plot
        fig, ax = plt.subplots(figsize=(12, 6))
        plot_hitrate_comparison(ax, hrA, hrB, viz_n_hr, nameA, nameB, z)
        st.pyplot(fig, clear_figure=True)
        
        # Interpretation
        ci1_hr = ci_for_proportion(hrA, viz_n_hr, z)
        ci2_hr = ci_for_proportion(hrB, viz_n_hr, z)
        overlap_hr = cis_overlap(ci1_hr, ci2_hr)
        
        if overlap_hr:
            st.info(f"ℹ️ At **{viz_n_hr:,} spins**, the {int(conf*100)}% confidence intervals **overlap**. "
                    f"The observed hit rate difference could be due to random variation.")
        else:
            st.success(f"✅ At **{viz_n_hr:,} spins**, the {int(conf*100)}% confidence intervals **do not overlap**. "
                       f"The hit rate difference is likely statistically meaningful.")

# ---------- Documentation ----------
with st.expander("📖 Methodology & Concepts"):
    st.markdown(f"""
    ### Hit Rate
    - **Definition**: The proportion of spins that result in any win (regardless of amount)
    - **Typical ranges**: 
        - Low hit rate (10-20%): High volatility games with rare big wins
        - Medium hit rate (20-35%): Balanced gameplay
        - High hit rate (35-50%+): Frequent small wins, lower volatility
    - **Confidence Interval**: Uses normal approximation for proportions: p ± z × √(p(1-p)/n)
    
    ### Volatility Index vs Standard Deviation
    - **Volatility Index (VI)**: Industry-standard measure representing typical outcome range at a given confidence level
        - Low volatility: VI = 1-5 (classic slots, frequent small wins)
        - Medium volatility: VI = 5-10 (balanced gameplay)
        - High volatility: VI = 10-15+ (progressive jackpots, rare big wins)
    - **Standard Deviation (SD)**: Raw statistical measure of variability per spin
    - **Conversion**: VI = SD × z-score (at current confidence level: z = {z:.3f})
    
    ### Statistical Method
    - **RTP Confidence Intervals**: mean ± z × (SD / √n)
    - **Hit Rate Confidence Intervals**: p ± z × √(p(1-p)/n)
    - **Current confidence level**: {int(conf*100)}%
    - **Assumptions**: 
        - Spins are independent
        - Large enough sample for Central Limit Theorem (typically n > 30)
        - For hit rate: np and n(1-p) both ≥ 5
    
    ### Interpretation
    - **CI Overlap**: Overlapping intervals suggest differences may be due to chance
    - **Pulls to Distinguish**: Sample size where confidence intervals stop overlapping
    - **Hit Rate vs RTP**: Hit rate measures frequency of wins; RTP measures average return amount
    
    ### Limitations
    - Assumes known population parameters
    - Normal approximation less accurate for very small samples or extreme proportions
    - Doesn't account for bonus features, progressive jackpots, or complex game mechanics
    """)

with st.expander("💭 Example Use Cases"):
    st.markdown("""
    - **Casino Operators**: Verify measured RTP and hit rate match theoretical values
    - **Players**: Understand sample sizes needed to assess machine performance and volatility
    - **Regulators**: Determine appropriate testing sample sizes for compliance
    - **Game Developers**: Design volatility profiles and hit rate targets; understand measurement precision
    - **Game Comparison**: Evaluate whether differences in hit rate or RTP between machines are statistically meaningful
    """)
