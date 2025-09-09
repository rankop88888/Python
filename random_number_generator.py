import streamlit as st
import random

# --- Page config ---
st.set_page_config(page_title="🎲 Random Number Row", layout="centered")

# --- Custom CSS for style ---
st.markdown("""
    <style>
    .number-box {
        display: flex;
        justify-content: center;
        align-items: center;
        font-size: 3em;
        font-weight: bold;
        color: white;
        background: linear-gradient(to bottom right, #4A90E2, #9013FE);
        border-radius: 10px;
        height: 100px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.2);
        transition: transform 0.3s ease-in-out;
    }
    .number-box:hover {
        transform: scale(1.1);
    }
    </style>
""", unsafe_allow_html=True)

# --- Title ---
st.markdown("<h1 style='text-align: center;'>🎰 8-Digit Random Generator</h1>", unsafe_allow_html=True)
st.write("")

# --- Button to generate numbers ---
if st.button("🎲 Generate 8 Random Numbers"):
    random_numbers = [random.randint(0, 9) for _ in range(8)]
else:
    random_numbers = ["❓"] * 8

# --- Display numbers in a row ---
cols = st.columns(8)
for i in range(8):
    with cols[i]:
        st.markdown(f"<div class='number-box'>{random_numbers[i]}</div>", unsafe_allow_html=True)
