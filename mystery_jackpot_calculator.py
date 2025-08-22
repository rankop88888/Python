import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO

st.set_page_config("Mystery JP Calculator", layout="wide")
st.title("🎰 Mystery Jackpot Contribution Calculator")

# ──────────────────────────────────────────────────────────────
# 1) Helper   «1.000» thousands-separator, no decimals
# ──────────────────────────────────────────────────────────────
def fmt_dot_sep(n: float | int) -> str:
    """Return e.g. 1234567 → '1.234.567' (dot every 3 digits)."""
    return f"{int(round(n, 0)):,}".replace(",", ".")

# ………………………………………………………………………………………………………………………
# inside the main loop – keep maths exactly as before … then:

display_rows.append(
    {
        "Level": lvl,
        "Avg Coin-In":   fmt_dot_sep(coin_in),
        "Initial JP":    fmt_dot_sep(initial),
        "Min Hit":       fmt_dot_sep(min_hit),
        "Max Hit":       fmt_dot_sep(max_hit),
        "Avg Hit":       fmt_dot_sep(avg_hit),
        "Raw %": f"{contrib_pct:.2f}",
        "Eff %": f"{eff_pct:.2f}",
        "Hit Days": f"{hit_days:.2f}",
    }
)

# ──────────────────────────────────────────────────────────────
# 2) Results table – just after the loop finishes
# ──────────────────────────────────────────────────────────────
if display_rows:
    st.markdown("### 📊 Level Summary")
    df_show = pd.DataFrame(display_rows)        # ALL columns are strings now
    st.dataframe(df_show, use_container_width=True)

    total_raw = sum(r["RawPct"] for r in records)
    total_eff = sum(r["EffPct"] for r in records)

    st.markdown(
        f"**Total Raw % :** {total_raw:.2f} &nbsp;|&nbsp; "
        f"**Total Effective % :** {total_eff:.2f}"
    )


# ─────────────────────────────────────────────────────
# Inputs
# ─────────────────────────────────────────────────────
st.sidebar.header("🧮 Levels")
num_levels = st.sidebar.number_input("Number of Levels", 1, 15, 1, 1)

records = []           # raw numeric data for maths
display_rows = []      # pretty-formatted strings for the table

for lvl in range(1, num_levels + 1):
    c1, c2, c3, c4, c5 = st.columns([2, 2, 2, 2, 1.5], gap="small")
    with c1:
        coin_in = st.number_input(f"Coin-In L{lvl}", 0, step=1, format="%d")
    with c2:
        initial = st.number_input(f"Initial JP L{lvl}", 0, step=1, format="%d")
    with c3:
        min_hit = st.number_input(f"Min Hit L{lvl}", 0, step=1, format="%d")
    with c4:
        max_hit = st.number_input(f"Max Hit L{lvl}", 0, step=1, format="%d")
    with c5:
        contrib_pct = st.number_input(
            f"% L{lvl}", 0.0, 100.0, step=0.01, format="%.2f"
        )

    # ── maths per level ──────────────────────────────
    avg_hit = (min_hit + max_hit) / 2.0
    daily_contrib = coin_in * (contrib_pct / 100)
    build_amount = max(avg_hit - initial, 0)        # funded by players
    hit_days = build_amount / daily_contrib if daily_contrib else float("inf")

    # Effective player % to fund **entire** jackpot (initial + build)
    eff_pct = (
        contrib_pct * (avg_hit / build_amount) if build_amount else 0.0
    )

    # ── inside the main level loop ──────────────────────────────
records.append(
    {                           # <─ use {} instead of dict()
        "Level": lvl,
        "CoinIn": coin_in,
        "Initial": initial,
        "MinHit": min_hit,
        "MaxHit": max_hit,
        "AvgHit": avg_hit,
        "RawPct": contrib_pct,
        "EffPct": eff_pct,
        "HitDays": hit_days,
    }
)

display_rows.append(
    {                           # <─ same change here
        "Level": lvl,
        "Avg Coin-In": fmt_int(coin_in),
        "Initial JP": fmt_int(initial),
        "Min Hit": fmt_int(min_hit),
        "Max Hit": fmt_int(max_hit),
        "Avg Hit": fmt_int(avg_hit),
        "Raw %": f"{contrib_pct:.2f}",
        "Eff %": f"{eff_pct:.2f}",
        "Hit Days": f"{hit_days:.2f}",
    }
)

# ─────────────────────────────────────────────────────
# Results table
# ─────────────────────────────────────────────────────
if display_rows:
    st.markdown("### 📊 Level Summary")
    df_show = pd.DataFrame(display_rows)
    st.dataframe(df_show, use_container_width=True)

    total_raw = sum(r["RawPct"] for r in records)
    total_eff = sum(r["EffPct"] for r in records)

    st.markdown(
        f"**Total Raw %:** {total_raw:.2f} &nbsp;&nbsp;|&nbsp;&nbsp; "
        f"**Total Effective % (incl. seed & min):** {total_eff:.2f}"
    )

# ─────────────────────────────────────────────────────
# Charts
# ─────────────────────────────────────────────────────
if any(r["CoinIn"] for r in records):

    def bar_chart(x, y, title, ylab):
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
        fig1 = bar_chart(levels, [r["RawPct"] for r in records],
                         "Raw Contribution %", "%")
        st.pyplot(fig1)
    with colB:
        fig2 = bar_chart(levels, [r["EffPct"] for r in records],
                         "Effective % (Seed + Min)", "%")
        st.pyplot(fig2)

    fig3 = bar_chart(levels, [r["HitDays"] for r in records],
                     "Hit Frequency (Days)", "Days")
    st.pyplot(fig3)

    # ── download PNGs ──
    for name, fig in [
        ("raw_pct.png", fig1),
        ("effective_pct.png", fig2),
        ("hit_days.png", fig3),
    ]:
        buf = BytesIO()
        fig.savefig(buf, format="png")
        st.download_button(
            f"⬇️ {name}",
            buf.getvalue(),
            file_name=name,
            mime="image/png",
            key=name,
        )
