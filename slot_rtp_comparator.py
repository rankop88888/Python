import math
from typing import List, Tuple

import numpy as np
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

st.set_page_config(page_title="Slot RTP Comparator", layout="wide")

# ---------- Constants ----------
CONF_TO_Z = {
    0.80: 1.2815515655446004,
    0.90: 1.6448536269514722,
    0.95: 1.959963984540054,
    0.975: 2.241402727604947,
    0.99: 2.5758293035489004,
}

PLOT_POINTS = 600
SE_RANGE_MULTIPLIER = 5

# ---------- Helper Functions ----------
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

def cis_overlap(ci1: Tuple[float, float], ci2: Tuple[float, float]) -> bool:
    """Check if two confidence intervals overlap."""
    if np.isnan(ci1[0]) or np.isnan(ci2[0]):
        return False
    return ci1[0] <= ci2[1] and ci2[0] <= ci1[1]

def sample_size_for_separation(rtp1: float, sd1: float, rtp2: float, sd2: float, z: float) -> int:
    """Estimate sample size needed for CIs to not overlap (conservative estimate)."""
    diff = abs(rtp1 - rtp2)
    if diff < 0.001:  # Effectively equal (within 0.001%)
        return np.inf
    # Conservative: need z * (se1 + se2) < diff
    # se = sd/sqrt(n), so z * (sd1 + sd2)/sqrt(n) < diff
    # sqrt(n) > z * (sd1 + sd2) / diff
    combined_sd = sd1 + sd2
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

def plot_comparison(ax, rtp1: float, sd1: float, rtp2: float, sd2: float, 
                   n: int, name1: str, name2: str, z: float):
    """Plot overlaid sampling distributions for both games."""
    if n <= 0 or sd1 <= 0 or sd2 <= 0:
        ax.text(0.5, 0.5, "Insufficient parameters", ha="center", va="center", 
                transform=ax.transAxes)
        return
    
    se1 = sd1 / math.sqrt(n)
    se2 = sd2 / math.sqrt(n)
    
    # Determine plot range
    min_val = min(rtp1 - SE_RANGE_MULTIPLIER * se1, rtp2 - SE_RANGE_MULTIPLIER * se2)
    max_val = max(rtp1 + SE_RANGE_MULTIPLIER * se1, rtp2 + SE_RANGE_MULTIPLIER * se2)
    xs = np.linspace(min_val, max_val, PLOT_POINTS)
    
    # Plot distributions
    ys1 = normal_pdf(xs, rtp1, se1)
    ys2 = normal_pdf(xs, rtp2, se2)
    
    ax.plot(xs, ys1, label=f"{name1}", color='#1f77b4', linewidth=2)
    ax.plot(xs, ys2, label=f"{name2}", color='#ff7f0e', linewidth=2)
    
    # Add confidence intervals
    lo1, hi1 = ci_for_mean(rtp1, sd1, n, z)
    lo2, hi2 = ci_for_mean(rtp2, sd2, n, z)
    
    ax.axvline(rtp1, color='#1f77b4', linestyle=':', alpha=0.7, label=f'{name1} mean')
    ax.axvspan(lo1, hi1, alpha=0.2, color='#1f77b4')
    
    ax.axvline(rtp2, color='#ff7f0e', linestyle=':', alpha=0.7, label=f'{name2} mean')
    ax.axvspan(lo2, hi2, alpha=0.2, color='#ff7f0e')
    
    ax.set_xlabel("Sample Mean RTP (%)", fontsize=10)
    ax.set_ylabel("Density", fontsize=10)
    ax.set_title(f"Sampling Distributions at n={n:,} spins", fontsize=11, fontweight='bold')
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)

# ---------- UI ----------
st.title("🎰 Slot Machine RTP Comparator")
st.markdown("Compare the statistical reliability of RTP measurements across different slot machines.")

with st.sidebar:
    st.header("⚙️ Configuration")
    
    conf = st.selectbox(
        "Confidence Level",
        [0.95, 0.99],
        index=0,
        format_func=lambda x: f"{x:.0%}",
        help="Higher confidence levels produce wider intervals. 95% and 99% are industry standards for slot testing."
    )
    z = CONF_TO_Z[conf]

    st.markdown("**Sample Sizes (Number of Spins)**")
    default_pulls = [10, 50, 100, 500, 1_000, 5_000, 10_000]
    pulls = st.multiselect(
        "Select sample sizes", 
        default_pulls, 
        default_pulls,
        help="Number of spins to analyze"
    )
    
    col1, col2 = st.columns([3, 1])
    with col1:
        new_pull = st.number_input("Custom sample size", min_value=1, step=1, value=200)
    with col2:
        st.write("")  # Spacing
        if st.button("Add", use_container_width=True):
            if new_pull not in pulls:
                pulls = sorted(pulls + [int(new_pull)])
                st.rerun()

    st.divider()
    st.caption("💡 **RTP** = Expected return per spin (%). **Volatility** = Standard deviation per spin (%).")

# Game input columns
colA, colB = st.columns(2, gap="large")

def game_input_block(col, game_id: str, default_name: str, default_rtp: float, default_sd: float):
    """Create input block for a single game."""
    with col:
        st.subheader(f"🎮 {default_name}")
        name = st.text_input(
            "Game Name", 
            value=default_name, 
            key=f"name_{game_id}",
            help="Identifier for this slot machine"
        )
        rtp_pct = st.number_input(
            "RTP (%)",
            min_value=0.0, 
            max_value=200.0, 
            value=default_rtp, 
            step=0.1,
            key=f"rtp_{game_id}",
            help="Expected return to player per spin"
        )
        sd_pct = st.number_input(
            "Volatility (SD per spin %)",
            min_value=0.0, 
            max_value=500.0, 
            value=default_sd, 
            step=1.0,
            key=f"sd_{game_id}",
            help="Higher volatility = more variable outcomes"
        )
        
        # Validation warnings
        if sd_pct > 300:
            st.warning("⚠️ Very high volatility - results may be unrealistic")
        if rtp_pct > 100:
            st.info("ℹ️ RTP > 100% means player advantage")
            
    return name, rtp_pct, sd_pct

nameA, rtpA, sdA = game_input_block(colA, "A", "Game A", 96.0, 120.0)
nameB, rtpB, sdB = game_input_block(colB, "B", "Game B", 94.0, 160.0)

# Validate inputs
if sdA <= 0 or sdB <= 0:
    st.error("❌ Volatility must be greater than 0")
    st.stop()

# ---------- Analysis ----------
st.markdown("---")
st.header("📊 Statistical Analysis")

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
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("RTP Difference", f"{abs(rtpA - rtpB):.2f}%")
with col2:
    better = nameA if rtpA > rtpB else nameB
    st.metric("Higher RTP", better)
with col3:
    if sep_n == np.inf:
        st.metric("Spins to Distinguish", "N/A (same RTP)")
    elif sep_n > 1_000_000:
        st.metric("Spins to Distinguish", f">{1_000_000:,}")
    else:
        st.metric("Spins to Distinguish", f"~{sep_n:,}")

st.markdown("### Confidence Interval Comparison")
st.dataframe(
    comparison.style.format({
        col: "{:.2f}" for col in comparison.columns if "%" in col or "RTP" in col
    }),
    use_container_width=True,
    height=400
)

# Download button
csv = comparison.to_csv(index=False)
st.download_button(
    label="📥 Download Table as CSV",
    data=csv,
    file_name=f"rtp_comparison_{nameA}_vs_{nameB}.csv",
    mime="text/csv"
)

# ---------- Visualization ----------
st.markdown("---")
st.header("📈 Distribution Visualization")

if len(pulls) > 0:
    viz_n = st.select_slider(
        "Select sample size to visualize",
        options=sorted(set(comparison["Pulls"])),
        value=int(sorted(set(comparison["Pulls"]))[min(2, len(set(comparison['Pulls']))-1)]),
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
        st.info(f"ℹ️ At **{viz_n:,} spins**, the {conf:.1%} confidence intervals **overlap**. "
                f"The observed difference could be due to random variation.")
    else:
        st.success(f"✅ At **{viz_n:,} spins**, the {conf:.1%} confidence intervals **do not overlap**. "
                   f"The RTP difference is likely statistically meaningful.")

# ---------- Documentation ----------
with st.expander("📖 Methodology & Assumptions"):
    st.markdown(f"""
    ### Statistical Method
    - **Confidence Intervals**: Calculated using normal approximation: `mean ± z × (SD / √n)`
    - **Current confidence level**: {conf:.1%} (z = {z:.3f})
    - **Assumptions**: 
        - Spins are independent
        - Large enough sample size for Central Limit Theorem to apply (typically n > 30)
        - Population standard deviation is known
    
    ### Interpretation
    - **RTP**: Return to Player percentage - the expected long-run return per spin
    - **Volatility (SD)**: Measures outcome variability - higher values mean more extreme swings
    - **CI Overlap**: When confidence intervals overlap, differences may be due to chance
    - **Spins to Distinguish**: Estimated sample size where CIs stop overlapping (conservative estimate)
    
    ### Limitations
    - Assumes known population parameters (real slot machines have unknown true RTP)
    - Normal approximation may be less accurate for very small samples
    - Does not account for bonus features, progressive jackpots, or other complex game mechanics
    """)

with st.expander("💭 Example Use Cases"):
    st.markdown("""
    - **Casino Operators**: Verify that measured RTP matches theoretical RTP
    - **Players**: Understand how many spins are needed to assess a machine's true performance
    - **Regulators**: Determine appropriate sample sizes for compliance testing
    - **Game Developers**: Design volatility profiles and understand measurement precision
    """)
