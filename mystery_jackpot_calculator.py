# ─────────────────────────────────────────────────────────────
#  Mystery Jackpot Contribution Calculator  •  v2.1
#  Rule: If Min Hit blank/zero, use Initial JP as Min Hit
# ─────────────────────────────────────────────────────────────
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
import re

st.set_page_config("Mystery JP Calculator", layout="wide")
st.title("🎰 Mystery Jackpot Contribution Calculator")

# ─────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────
DOT_GROUPS = re.compile(r"[.\s,]")

def parse_dot_int(text: str) -> int:
    """'1.234.567' → 1234567 : strips dots, spaces, commas."""
    text = DOT_GROUPS.sub("", text)
    return int(text) if text.isdigit() else 0

def fmt_dot(n: float | int) -> str:
    """1234567 → '1.234.567' (no decimals)."""
    return f"{int(round(n)):,}".replace(",", ".")

def bar(xs, ys, title, ylab):
    fig, ax = plt.subplots()
    ax.bar(xs, ys)
    ax.set_title(title)
    ax.set_xlabel("Level")
    ax.set_ylabel(ylab)
    fig.tight_layout()
    return fig

# ─────────────────────────────────────────────────────────────
# Session state – dynamic list of levels (text fields)
# ─────────────────────────────────────────────────────────────
if "levels" not in st.session_state:
    st.session_state.levels = [dict(coin="", init="", min="", max="", pct="0.00")]

col_add, col_del = st.columns(2)
with col_add:
    if st.button("➕ Add Level"):
        st.session_state.levels.append(dict(coin="", init="", min="", max="", pct="0.00"))
with col_del:
    if st.button("➖ Remove Last", disabled=len(st.session_state.levels) == 1):
        st.session_state.levels.pop()

# ─────────────────────────────────────────────────────────────
# Input rows
# ─────────────────────────────────────────────────────────────
records, disp_rows = [], []

for idx, lvl in enumerate(st.session_state.levels, 1):
    c1, c2, c3, c4, c5 = st.columns([2.2, 2.2, 2.2, 2.2, 1.6], gap="small")

    with c1:
        lvl["coin"] = st.text_input(f"Coin-In L{idx}", lvl["coin"], key=f"coin{idx}")
    with c2:
        lvl["init"] = st.text_input(f"Initial JP L{idx}", lvl["init"], key=f"init{idx}")
    with c3:
        lvl["min"]  = st.text_input(f"Min Hit L{idx}", lvl["min"],  key=f"min{idx}")
    with c4:
        lvl["max"]  = st.text_input(f"Max Hit L{idx}", lvl["max"],  key=f"max{idx}")
    with c5:
        lvl["pct"]  = st.text_input(f"% L{idx}",       lvl["pct"],  key=f"pct{idx}")

    # ── numeric parse ────────────────────────────────────────
    coin = parse_dot_int(lvl["coin"])
    init = parse_dot_int(lvl["init"])
    min_ = parse_dot_int(lvl["min"])
    max_ = parse_dot_int(lvl["max"])

    try:
        pct = float(lvl["pct"].replace(",", "."))
    except ValueError:
        pct = 0.0

    # ── logic fix: adopt Initial as Min when Min = 0 ─────────
    if init > 0 and min_ == 0:
        min_ = init
    # ensure Max ≥ Min
    if max_ < min_:
        max_ = min_

    avg_hit   = (min_ + max_) / 2.0
    build_amt = max(avg_hit - init, 0)
    daily_val = coin * (pct / 100)
    hit_days  = build_amt / daily_val if daily_val else float("inf")
    eff_pct   = pct * (avg_hit / build_amt) if build_amt else 0.0

    records.append(dict(Level=idx, Coin=coin, Init=init, Min=min_, Max=max_,
                        Avg=avg_hit, Raw=pct, Eff=eff_pct, Days=hit_days))

    disp_rows.append({
        "Level": idx,
        "Avg Coin-In": fmt_dot(coin),
        "Initial JP":  fmt_dot(init),
        "Min Hit":     fmt_dot(min_),
        "Max Hit":     fmt_dot(max_),
        "Avg Hit":     fmt_dot(avg_hit),
        "Raw %": f"{pct:.2f}",
        "Eff %": f"{eff_pct:.2f}",
        "Hit Days": f"{hit_days:.2f}",
    })

# ─────────────────────────────────────────────────────────────
# Table & totals
# ─────────────────────────────────────────────────────────────
if disp_rows:
    st.markdown("### 📊 Level Summary")
    st.dataframe(pd.DataFrame(disp_rows), use_container_width=True)
    tot_raw = sum(r["Raw"] for r in records)
    tot_eff = sum(r["Eff"] for r in records)
    st.markdown(f"**Total Raw %:** {tot_raw:.2f} &nbsp;|&nbsp; "
                f"**Total Effective %:** {tot_eff:.2f}")

# ─────────────────────────────────────────────────────────────
# Charts
# ─────────────────────────────────────────────────────────────
if any(r["Coin"] for r in records):
    lvls = [r["Level"] for r in records]
    colA, colB = st.columns(2)
    with colA:
        fig_raw = bar(lvls, [r["Raw"] for r in records], "Raw Contribution %", "%")
        st.pyplot(fig_raw)
    with colB:
        fig_eff = bar(lvls, [r["Eff"] for r in records], "Effective % (Seed + Min)", "%")
        st.pyplot(fig_eff)
    fig_days = bar(lvls, [r["Days"] for r in records], "Hit Frequency (Days)", "Days")
    st.pyplot(fig_days)

    # downloads
    for name, fig in [("raw_pct.png", fig_raw),
                      ("effective_pct.png", fig_eff),
                      ("hit_days.png", fig_days)]:
        buf = BytesIO()
        fig.savefig(buf, format="png")
        st.download_button(f"⬇️ {name}", buf.getvalue(),
                           file_name=name, mime="image/png", key=name)
