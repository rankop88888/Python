#  ────────────────────────────────────────────────────────────
#  Mystery Jackpot Contribution Calculator  •  Streamlit
#  ────────────────────────────────────────────────────────────
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO

st.set_page_config("Mystery JP Calculator", layout="wide")
st.title("🎰 Mystery Jackpot Contribution Calculator")

# ────────────────────────────────────────────────────────────
# Helper – 1.000.000 style (dot for thousands, no decimals)
# ────────────────────────────────────────────────────────────
def fmt_dot(n: float | int) -> str:
    """Return e.g. 1234567 → '1.234.567'."""
    return f"{int(round(n)):,}".replace(",", ".")

# ────────────────────────────────────────────────────────────
# Sidebar – how many levels?
# ────────────────────────────────────────────────────────────
st.sidebar.header("🧮 Levels")
num_levels = st.sidebar.number_input("Number of Levels", 1, 15, 1, 1)

records: list[dict] = []      # numeric for maths / charts
display_rows: list[dict] = [] # pretty strings for the table

# ────────────────────────────────────────────────────────────
# One horizontal row of inputs per level
# ────────────────────────────────────────────────────────────
for lvl in range(1, num_levels + 1):
    col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 2, 1.6], gap="small")

    with col1:
        coin_in = st.number_input(f"Coin-In  L{lvl}", 0, step=1, format="%d")
    with col2:
        initial = st.number_input(f"Initial JP  L{lvl}", 0, step=1, format="%d")
    with col3:
        min_hit = st.number_input(f"Min Hit  L{lvl}", 0, step=1, format="%d")
    with col4:
        max_hit = st.number_input(f"Max Hit  L{lvl}", 0, step=1, format="%d")
    with col5:
        pct = st.number_input(f"%  L{lvl}", 0.0, 100.0, step=0.01, format="%.2f")

    # ─ calculations ─
    avg_hit      = (min_hit + max_hit) / 2.0
    build_amount = max(avg_hit - initial, 0)         # only what players must grow
    daily_cont   = coin_in * (pct / 100)
    hit_days     = build_amount / daily_cont if daily_cont else float("inf")

    eff_pct = pct * (avg_hit / build_amount) if build_amount else 0.0

    records.append({
        "Level": lvl,
        "CoinIn": coin_in,
        "Initial": initial,
        "MinHit": min_hit,
        "MaxHit": max_hit,
        "AvgHit": avg_hit,
        "RawPct": pct,
        "EffPct": eff_pct,
        "HitDays": hit_days,
    })

    display_rows.append({
        "Level": lvl,
        "Avg Coin-In": fmt_dot(coin_in),
        "Initial JP": fmt_dot(initial),
        "Min Hit": fmt_dot(min_hit),
        "Max Hit": fmt_dot(max_hit),
        "Avg Hit": fmt_dot(avg_hit),
        "Raw %": f"{pct:.2f}",
        "Eff %": f"{eff_pct:.2f}",
        "Hit Days": f"{hit_days:.2f}",
    })

# ────────────────────────────────────────────────────────────
# Result table
# ────────────────────────────────────────────────────────────
if display_rows:
    st.markdown("### 📊 Level Summary")
    st.dataframe(pd.DataFrame(display_rows), use_container_width=True)

    total_raw = sum(r["RawPct"] for r in records)
    total_eff = sum(r["EffPct"] for r in records)
    st.markdown(
        f"**Total Raw %:** {total_raw:.2f} &nbsp; | &nbsp; "
        f"**Total Effective %:** {total_eff:.2f}"
    )

# ────────────────────────────────────────────────────────────
# Charts (only if we have any coin-in > 0)
# ────────────────────────────────────────────────────────────
if any(r["CoinIn"] for r in records):
    def bar(x, y, title, ylab):
        fig, ax = plt.subplots()
        ax.bar(x, y)
        ax.set_title(title)
        ax.set_xlabel("Level")
        ax.set_ylabel(ylab)
        fig.tight_layout()
        return fig

    levels = [r["Level"] for r in records]

    colA, colB = st.columns(2)
    with colA:
        fig1 = bar(levels, [r["RawPct"] for r in records], "Raw Contribution %", "%")
        st.pyplot(fig1)
    with colB:
        fig2 = bar(levels, [r["EffPct"] for r in records], "Effective % (Seed + Min)", "%")
        st.pyplot(fig2)

    fig3 = bar(levels, [r["HitDays"] for r in records], "Hit Frequency (Days)", "Days")
    st.pyplot(fig3)

    # downloads
    for fname, fig in [
        ("raw_pct.png", fig1),
        ("effective_pct.png", fig2),
        ("hit_days.png", fig3),
    ]:
        buf = BytesIO()
        fig.savefig(buf, format="png")
        st.download_button(
            f"⬇️ {fname}",
            buf.getvalue(),
            file_name=fname,
            mime="image/png",
            key=fname,
        )
