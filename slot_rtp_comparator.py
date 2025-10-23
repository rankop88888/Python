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
    """
    Convert Volatility Index to Standard Deviation per spin.
    Volatility Index already includes z-score for the confidence level.
    VI = z × SD, so SD = VI / z
    """
    z = CONF_TO_Z[conf_level]
    return vi / z

def sd_to_volatility_index(sd: float, conf_level: float) -> float:
    """
    Convert Standard Deviation per spin to Volatility Index.
    VI = z × SD
    """
    z = CONF_TO_Z[conf_level]
    return z * sd

def normal_pdf(x: np.ndarray, mu: float, sigma: float) -> np.ndarray:
    """Calculate normal probability density function."""
    if sigma <= 0:
        return np.zeros_like(x)
    c = 1.0 / (sigma * math.sqrt(2.0 * math.pi))
    return c * np.exp(-0.5 * ((x - mu) / sigma) ** 2)

def ci_for_mean(rtp_pct: float, sd: float, n: int, z: float) -> Tuple[float, float]:
    """
    Calculate confidence interval for mean RTP.
    sd parameter is the raw standard deviation (not VI).
    Margin of error = z × (sd / sqrt(n))
    """
    if n <= 0 or sd < 0:
        return (np.nan, np.nan)
    margin_of_error = z * sd / math.sqrt(n)
    lo = rtp_pct - margin_of_error
    hi = rtp_pct + margin_of_error
    return (max(0.0, lo), min(200.0, hi))

def ci_for_proportion(p: float, n: int, z: float) -> Tuple[float, float]:
    """Calculate confidence interval for hit rate (proportion) using normal approximation."""
    if n <= 0 or p < 0 or p > 1:
        return (np.nan, np.nan)
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
    combined_sd = math.sqrt(sd1**2 + sd2**2)
    n = ((z * combined_sd) / diff) ** 2
    return int(np.ceil(n)) if not np.isinf(n) else np.inf

def sample_size_for_hitrate_separation(hr1: float, hr2: float, z: float) -> int:
    """Estimate sample size needed for hit rate CIs to not overlap."""
    diff = abs(hr1 - hr2)
    if diff < 0.0001:
        return np.inf
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
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x*100:.1f}%'))

# ---------- UI ----------
st.title("🎰 Slot Machine RTP Comparator")
st.markdown("Compare the statistical reliability of RTP and hit rate measurements across different slot machines.")

if 'pulls' not in st.session_state:
    st.session_state.pulls = [10000, 100000, 1000000, 10000000]
if 'run_analysis' not in st.session_state:
    st.session_state.run_analysis = False

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
    
    preset_options = {
        "Small Scale (10K - 100K)": [10000, 50000, 100000],
        "Medium Scale (100K - 1M)": [100000, 500000, 1000000],
        "Large Scale (1M - 10M)": [1000000, 5000000, 10000000],
        "Full Range": [10000, 100000, 1000000, 10000000, 100000000],
        "Custom": []
    }
    
    preset = st.selectbox(
        "Choose preset",
        list(preset_options.keys()),
        index=3,
        help="Select a preset range or choose Custom"
    )
    
    if preset == "Custom":
        available_sizes = [10, 50, 100, 500, 1000, 5000, 10000, 50000, 100000, 
                          500000, 1000000, 5000000, 10000000, 50000000, 100000000]
        pulls = st.multiselect(
            "Select sample sizes",
            available_sizes,
            default=[10000, 100000, 1000000, 10000000],
            help="Choose multiple sample sizes",
            format_func=lambda x: f"{x:,}"
        )
    else:
        pulls = preset_options[preset]
        st.info(f"📊 Selected sizes: {', '.join([f'{p:,}' for p in pulls])}")
    
    with st.expander("➕ Add Individual Size"):
        custom_pull = st.number_input(
            "Custom pull count", 
            min_value=10, 
            step=1000, 
            value=50000,
            format="%d"
        )
        if st.button("Add to Analysis", use_container_width=True):
            if custom_pull not in pulls:
                pulls = sorted(pulls + [int(custom_pull)])
                st.success(f"Added {custom_pull:,} pulls")
                st.rerun()

    st.divider()
    st.caption("💡 **RTP** = Return to Player (%). **Hold %** = House edge. **VI** = Volatility Index.")

if not pulls or len(pulls) == 0:
    st.error("❌ Please select at least one sample size")
    st.stop()

colA, colB = st.columns(2, gap="large")

def game_input_block(col, game_id: str, default_name: str, default_rtp: float, default_vi: float, default_hr: float):
    with col:
        st.subheader(f"🎮 {default_name}")
        name = st.text_input(
            "Game Name", 
            value=default_name, 
            key=f"name_{game_id}",
            help="Identifier for this slot machine"
        )
        
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
                step=0.01,
                key=f"rtp_{game_id}",
                help="Expected return to player per spin",
                format="%.2f"
            )
            hold_pct = 100.0 - rtp_pct
            st.caption(f"📊 Hold Percentage: {hold_pct:.3f}%")
        else:
            hold_pct = st.number_input(
                "Hold Percentage (%)",
                min_value=0.0,
                max_value=100.0,
                value=100.0 - default_rtp,
                step=0.01,
                key=f"hold_{game_id}",
                help="House edge (100% - RTP)",
                format="%.3f"
            )
            rtp_pct = 100.0 - hold_pct
            st.caption(f"📊 RTP: {rtp_pct:.3f}%")
        
        hit_rate = st.number_input(
            "Hit Rate (%)",
            min_value=0.0,
            max_value=100.0,
            value=default_hr,
            step=0.1,
            key=f"hr_{game_id}",
            help="Percentage of spins that result in a win"
        ) / 100.0
        
        st.markdown("**Volatility Input Method**")
        use_vi = st.radio(
            "Choose input type",
            ["Volatility Index", "Standard Deviation"],
            key=f"vol_type_{game_id}",
            help="Volatility Index already includes z-score; SD is raw statistical measure"
        )
        
        if use_vi == "Volatility Index":
            vi = st.number_input(
                "Volatility Index",
                min_value=0.1, 
                max_value=50.0, 
                value=default_vi, 
                step=0.001,
                key=f"vi_{game_id}",
                help="Industry standard: VI already includes z-score. Typical range: Low (1-5), Medium (5-10), High (10-15)",
                format="%.3f"
            )
            sd_pct = volatility_index_to_sd(vi, rtp_pct, conf)
            st.caption(f"📊 Calculated SD per spin: {sd_pct:.3f}% (VI = {z:.3f} × SD)")
        else:
            sd_pct = st.number_input(
                "Standard Deviation per spin (%)",
                min_value=0.1, 
                max_value=500.0, 
                value=volatility_index_to_sd(default_vi, default_rtp, conf), 
                step=0.1,
                key=f"sd_{game_id}",
                help="Raw statistical standard deviation per spin (without z-score)"
            )
            vi = sd_to_volatility_index(sd_pct, conf)
            st.caption(f"📊 Calculated Volatility Index: {vi:.3f} (VI = {z:.3f} × SD)")
        
        if vi > 15:
            st.warning("⚠️ Very high volatility")
        if rtp_pct > 100:
            st.info("ℹ️ RTP > 100% means player advantage")
        if hit_rate > 0.5:
            st.info("ℹ️ High hit rate (>50%)")
            
    return name, rtp_pct, sd_pct, hit_rate

nameA, rtpA, sdA, hrA = game_input_block(colA, "A", "Game A", 95.08, 5.73, 25.0)
nameB, rtpB, sdB, hrB = game_input_block(colB, "B", "Game B", 95.08, 5.73, 25.0)

if sdA <= 0 or sdB <= 0:
    st.error("❌ Volatility/SD must be greater than 0")
    st.stop()

st.markdown("---")
run_col1, run_col2, run_col3 = st.columns([1, 1, 1])
with run_col2:
    if st.button("🚀 Run Analysis", type="primary", use_container_width=True):
        st.session_state.run_analysis = True

if not st.session_state.run_analysis:
    st.info("👆 Configure your games above and click **Run Analysis** to see results")
    st.stop()

st.markdown("---")

tab1, tab2 = st.tabs(["📊 RTP Analysis", "🎯 Hit Rate Analysis"])

with tab1:
    st.header("RTP Statistical Analysis")
    
    tableA = ci_table(nameA, rtpA, sdA, pulls, z)
    tableB = ci_table(nameB, rtpB, sdB, pulls, z)
    
    comparison = tableA.merge(tableB, on="Pulls", suffixes=(f" ({nameA})", f" ({nameB})"))
    
    overlap_data = []
    for _, row in comparison.iterrows():
        n = row["Pulls"]
        ci1 = ci_for_mean(rtpA, sdA, n, z)
        ci2 = ci_for_mean(rtpB, sdB, n, z)
        overlap_data.append(cis_overlap(ci1, ci2))
    
    comparison["CIs Overlap?"] = ["Yes" if x else "No" for x in overlap_data]
    
    sep_n = sample_size_for_separation(rtpA, sdA, rtpB, sdB, z)
    
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
            st.metric("Pulls to Distinguish", "N/A")
        elif sep_n > 1000000:
            st.metric("Pulls to Distinguish", f">{1000000:,}")
        else:
            st.metric("Pulls to Distinguish", f"~{sep_n:,}")
    
    st.markdown("### RTP Confidence Interval Comparison")
    
    comparison_display = comparison.copy()
    comparison_display[f"Hold % ({nameA})"] = 100 - comparison_display[f"RTP % ({nameA})"]
    comparison_display[f"Hold % ({nameB})"] = 100 - comparison_display[f"RTP % ({nameB})"]
    
    display_cols = ["Pulls"]
    display_cols.extend([f"RTP % ({nameA})", f"Hold % ({nameA})", 
                        f"CI Low % ({nameA})", f"CI High % ({nameA})", f"CI Width % ({nameA})"])
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
    
    csv = comparison_display[display_cols].to_csv(index=False)
    st.download_button(
        label="📥 Download RTP Table as CSV",
        data=csv,
        file_name=f"rtp_comparison_{nameA}_vs_{nameB}.csv",
        mime="text/csv"
    )
    
    st.markdown("---")
    st.subheader("📈 RTP Distribution Visualization")
    
    if len(pulls) > 0:
        viz_n = st.select_slider(
            "Select sample size to visualize RTP distributions",
            options=sorted(set(comparison["Pulls"])),
            value=int(sorted(set(comparison["Pulls"]))[min(2, len(set(comparison['Pulls']))-1)]),
            key="rtp_viz",
            format_func=lambda x: f"{x:,}"
        )
        
        fig, ax = plt.subplots(figsize=(12, 6))
        plot_comparison(ax, rtpA, sdA, rtpB, sdB, viz_n, nameA, nameB, z)
        st.pyplot(fig, clear_figure=True)
        
        ci1 = ci_for_mean(rtpA, sdA, viz_n, z)
        ci2 = ci_for_mean(rtpB, sdB, viz_n, z)
        overlap = cis_overlap(ci1, ci2)
        
        if overlap:
            st.info(f"ℹ️ At **{viz_n:,} spins**, the {int(conf*100)}% confidence intervals **overlap**.")
        else:
            st.success(f"✅ At **{viz_n:,} spins**, the {int(conf*100)}% confidence intervals **do not overlap**.")

with tab2:
    st.header("Hit Rate Statistical Analysis")
    
    hrTableA = hitrate_table(nameA, hrA, pulls, z)
    hrTableB = hitrate_table(nameB, hrB, pulls, z)
    
    hr_comparison = hrTableA.merge(hrTableB, on="Pulls", suffixes=(f" ({nameA})", f" ({nameB})"))
    
    hr_overlap_data = []
    for _, row in hr_comparison.iterrows():
        n = row["Pulls"]
        ci1 = ci_for_proportion(hrA, n, z)
        ci2 = ci_for_proportion(hrB, n, z)
        hr_overlap_data.append(cis_overlap(ci1, ci2))
    
    hr_comparison["CIs Overlap?"] = ["Yes" if x else "No" for x in hr_overlap_data]
    
    hr_sep_n = sample_size_for_hitrate_separation(hrA, hrB, z)
    
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
            st.metric("Pulls to Distinguish", "N/A")
        elif hr_sep_n > 1000000:
            st.metric("Pulls to Distinguish", f">{1000000:,}")
        else:
            st.metric("Pulls to Distinguish", f"~{hr_sep_n:,}")
    
    st.markdown("### Hit Rate Confidence Interval Comparison")
    
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
    
    csv_hr = hr_display.to_csv(index=False)
    st.download_button(
        label="📥 Download Hit Rate Table as CSV",
        data=csv_hr,
        file_name=f"hitrate_comparison_{nameA}_vs_{nameB}.csv",
        mime="text/csv"
    )
    
    st.markdown("---")
    st.subheader("📈 Hit Rate Distribution Visualization")
    
    if len(pulls) > 0:
        viz_n_hr = st.select_slider(
            "Select sample size to visualize hit rate distributions",
            options=sorted(set(hr_comparison["Pulls"])),
            value=int(sorted(set(hr_comparison["Pulls"]))[min(2, len(set(hr_comparison['Pulls']))-1)]),
            key="hr_viz",
            format_func=lambda x: f"{x:,}"
        )
        
        fig, ax = plt.subplots(figsize=(12, 6))
        plot_hitrate_comparison(ax, hrA, hrB, viz_n_hr, nameA, nameB, z)
        st.pyplot(fig, clear_figure=True)
        
        ci1_hr = ci_for_proportion(hrA, viz_n_hr, z)
        ci2_hr = ci_for_proportion(hrB, viz_n_hr, z)
        overlap_hr = cis_overlap(ci1_hr, ci2_hr)
        
        if overlap_hr:
            st.info(f"ℹ️ At **{viz_n_hr:,} spins**, the {int(conf*100)}% confidence intervals **overlap**.")
        else:
            st.success(f"✅ At **{viz_n_hr:,} spins**, the {int(conf*100)}% confidence intervals **do not overlap**.")

with st.expander("📖 Methodology & Concepts"):
    st.markdown(f"""
    ### Hit Rate
    - **Definition**: The proportion of spins that result in any win
    - **Typical ranges**: Low (10-20%), Medium (20-35%), High (35-50%+)
    - **Confidence Interval**: p ± z × √(p(1-p)/n)
    
    ### Hold Percentage vs RTP
    - **RTP**: Expected percentage returned to players
    - **Hold %**: House edge = 100% - RTP
    - Example: RTP 95.08% = Hold 4.92%
    
    ### Volatility Index vs Standard Deviation
    - **Volatility Index (VI)**: Industry standard that includes the z-score
      - VI = z × SD (e.g., for 95% confidence: VI = 1.96 × SD)
      - **Margin of Error Formula**: MoE = VI / √n
      - **Example**: VI = 5.73 at 10,000 pulls → MoE = 5.73 / √10,000 = 5.73 / 100 = 5.73%
      - **Ranges**: Low (1-5), Medium (5-10), High (10-15+)
    - **Standard Deviation (SD)**: Raw statistical measure per spin
      - **Margin of Error Formula**: MoE = z × SD / √n
      - **Example**: SD = 2.92 at 10,000 pulls with 95% confidence (z=1.96) → MoE = 1.96 × 2.92 / 100 = 5.73%
      - Both methods give the same confidence intervals, just different input conventions
    
    ### Statistical Method
    - **RTP CI**: mean ± z × (SD / √n)
    - **Hit Rate CI**: p ± z × √(p(1-p)/n)
    - **z-values**: 95% confidence = 1.96, 99% confidence = 2.576
    - **Assumptions**: Independent spins, n > 30
    
    ### Example Calculation
    Given: RTP = 95.09%, VI = 5.795, n = 10,000 spins, 95% confidence
    - SD = VI / z = 5.795 / 1.96 = 2.957%
    - Standard Error = SD / √n = 2.957 / 100 = 0.02957%
    - Margin of Error = z × SE = 1.96 × 2.957 / 100 = 5.795%
    - Or directly: MoE = VI / √n = 5.795 / 100 = 5.795%
    - Lower CI = 95.09 - 5.795 = 89.295%
    - Upper CI = 95.09 + 5.795 = 100.885%
    """)

with st.expander("💭 Example Use Cases"):
    st.markdown("""
    - **Casino Operators**: Verify measured RTP matches theoretical values
    - **Regulators**: Determine appropriate testing sample sizes
    - **Game Developers**: Design volatility profiles and understand precision
    - **Comparison**: Evaluate statistical significance of differences between games
    - **Quality Assurance**: Ensure games operate within acceptable variance ranges
    """)
