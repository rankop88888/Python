# slot_rtp_comparator.py
import math
from typing import List, Tuple

import numpy as np
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
from scipy.stats import norm

st.set_page_config(page_title="Slot RTP Comparator", layout="wide")

# ---------- helpers ----------
CONF_TO_Z = {
    0.80: norm.ppf(0.9),
    0.90: norm.ppf(0.95),
    0.95: norm.ppf(0.975),
    0.975: norm.ppf(0.9875),
    0.99: norm.ppf(0.995),
}

def ci_for_mean(rtp_pct: float, sd_pct_per_spin: float, n: int, z: float) -> Tuple[float, float]:
    """Return (lo, hi) CI for RTP% over n pulls using normal approx."""
    if n <= 0 or sd_pct_per_spin < 0:
        return (np.nan, np.nan)
    se = sd_pct_per_spin / math.sqrt(n)
    lo = rtp_pct - z * se
    hi = rtp_pct + z * se
    return (max(0.0, lo), min(200.0, hi))  # clamp to 0–200% to be safe

def ci_table(name: str, rtp_pct: float, sd_pct_per_spin: float, pulls: List[int], z: float) -> pd.DataFrame:
    rows = []
    for n in sorted(set(int(x) for x in pulls if x and x > 0)):
        lo, hi = ci_for_mean(rtp_pct, sd_pct_per_spin, n, z)
        rows.append({"Game": name, "Pulls": n, "RTP % mean": rtp_pct, "CI low %": lo, "CI high %": hi})
    return pd.DataFrame(rows)

def plot_sampling_dist(ax, rtp_pct: float, sd_pct_per_spin: float, n: int, label: str):
    if n <= 0 or sd_pct_per_spin <= 0:
        ax.text(0.5, 0.5, "insufficient parameters", ha="center", va="center", transform=ax.transAxes)
        ax.set_xticks([]); ax.set_yticks([])
        return
    se = sd_pct_per_spin / math.sqrt(n)
    xs = np.linspace(rtp_pct - 5*se, rtp_pct + 5*se, 600)
    ys = norm.pdf(xs, loc=rtp_pct, scale=se)
    ax.plot(xs, ys, label=f"{label} (n={n})")
    ax.set_xlabel("Sample mean RTP (%)")
    ax.set_ylabel("Density")
    ax.set_title(f"{label} distribution")
    ax.legend()

# ---------- UI ----------
st.title("Two-Machine RTP Comparator")

with st.sidebar:
    st.header("Global settings")
    conf = st.selectbox("Confidence level", [0.80, 0.90, 0.95, 0.975, 0.99], index=2, format_func=lambda x: f"{x:.1%}" if x != 0.975 else "97.5%")
    z = CONF_TO_Z[conf]

    st.markdown("**Hand pulls**")
    default_pulls = [10, 50, 100, 500, 1_000, 5_000, 10_000]
    pulls = st.multiselect("Select pulls", default_pulls, default_pulls)
    new_pull = st.number_input("Add another pulls count", min_value=1, step=1, value=200)
    if st.button("Add"):
        pulls = sorted(set(pulls + [int(new_pull)]))

    st.divider()
    st.caption("RTP and volatility are entered as percentages per spin. Volatility = standard deviation per spin.")

colA, colB = st.columns(2, gap="large")

def game_block(col, default_name, default_rtp, default_sd):
    with col:
        st.subheader(default_name)
        name = st.text_input("Game name", value=default_name, key=f"name_{default_name}")
        rtp_pct = st.number_input("RTP % (expected return per spin)", min_value=0.0, max_value=200.0, value=default_rtp, step=0.1, key=f"rtp_{default_name}")
        st.markdown("**Volatility input**")
        sd_known = st.toggle("Provide volatility (SD per spin) directly", value=True, key=f"toggle_{default_name}")
        if sd_known:
            sd_pct = st.number_input("Volatility = SD per spin (%)", min_value=0.0, max_value=500.0, value=default_sd, step=0.1, key=f"sd_{default_name}")
        else:
            # If user prefers, allow entering SD as well. Same value, separate control to match request.
            sd_pct = st.number_input("Standard deviation per spin (%)", min_value=0.0, max_value=500.0, value=default_sd, step=0.1, key=f"sd_alt_{default_name}")
            st.caption("Volatility derived from SD. Confidence level affects the interval, not volatility.")
    return name, rtp_pct, sd_pct

nameA, rtpA, sdA = game_block(colA, "Game A", 96.0, 120.0)
nameB, rtpB, sdB = game_block(colB, "Game B", 94.0, 160.0)

# ---------- calculations ----------
tableA = ci_table(nameA, rtpA, sdA, pulls, z)
tableB = ci_table(nameB, rtpB, sdB, pulls, z)

# Combined comparison table
comparison = (
    tableA.merge(tableB, on="Pulls", suffixes=(f" [{nameA}]", f" [{nameB}]"))
    .rename(columns={
        f"RTP % mean [{nameA}]": f"{nameA} RTP %",
        f"CI low % [{nameA}]": f"{nameA} CI low %",
        f"CI high % [{nameA}]": f"{nameA} CI high %",
        f"RTP % mean [{nameB}]": f"{nameB} RTP %",
        f"CI low % [{nameB}]": f"{nameB} CI low %",
        f"CI high % [{nameB}]": f"{nameB} CI high %",
    })
)

st.markdown("### RTP confidence ranges by pulls")
st.dataframe(comparison, use_container_width=True)

# Let user choose which n to visualize
viz_n = st.select_slider("Select pulls to visualize distributions", options=sorted(set(comparison["Pulls"])), value=int(sorted(set(comparison["Pulls"]))[min(2, len(set(comparison['Pulls']))-1)]))

# ---------- plots ----------
left_plot, right_plot = st.columns(2, gap="large")

with left_plot:
    fig, ax = plt.subplots()
    plot_sampling_dist(ax, rtpA, sdA, viz_n, nameA)
    loA, hiA = ci_for_mean(rtpA, sdA, viz_n, z)
    ax.axvline(loA, linestyle="--")
    ax.axvline(hiA, linestyle="--")
    ax.axvline(rtpA, linestyle=":")
    st.pyplot(fig, clear_figure=True)
    st.caption(f"{nameA}: {conf:.1%} CI at n={viz_n}: [{loA:.2f}%, {hiA:.2f}%].")

with right_plot:
    fig, ax = plt.subplots()
    plot_sampling_dist(ax, rtpB, sdB, viz_n, nameB)
    loB, hiB = ci_for_mean(rtpB, sdB, viz_n, z)
    ax.axvline(loB, linestyle="--")
    ax.axvline(hiB, linestyle="--")
    ax.axvline(rtpB, linestyle=":")
    st.pyplot(fig, clear_figure=True)
    st.caption(f"{nameB}: {conf:.1%} CI at n={viz_n}: [{loB:.2f}%, {hiB:.2f}%].")

# ---------- notes ----------
with st.expander("Method notes"):
    st.markdown(
        """
- RTP is the expected percent return per spin. Volatility is the per-spin standard deviation in percent.
- Confidence intervals use a normal approximation: mean ± z * (SD / √n).
- Choose the confidence level in the sidebar. z is computed from the two-sided normal quantile.
- The table shows the interval tightening as pulls increase.
- If you do not know volatility, input the per-spin SD; it is used directly.
        """
    )
