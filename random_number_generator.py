import streamlit as st
import random
import time
import asyncio

# --- Page config ---
st.set_page_config(page_title="Random Number Row", layout="centered")

# --- Initialize session state ---
if 'rolling' not in st.session_state:
    st.session_state.rolling = False
if 'numbers' not in st.session_state:
    st.session_state.numbers = ["?"] * 8
if 'final_numbers' not in st.session_state:
    st.session_state.final_numbers = []

# --- Custom CSS ---
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
        margin: 5px;
        transition: all 0.3s ease;
    }
    .number-box.rolling {
        background: linear-gradient(to bottom right, #FF6B6B, #FFE66D);
        box-shadow: 0 6px 15px rgba(255,107,107,0.4);
    }
    .number-box.final {
        background: linear-gradient(to bottom right, #4ECDC4, #44A08D);
        transform: scale(1.05);
    }
    .stButton > button {
        background: linear-gradient(45deg, #FF6B6B, #4ECDC4);
        border: none;
        color: white;
        padding: 15px 30px;
        font-size: 1.2em;
        border-radius: 25px;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# --- Title ---
st.markdown("<h1 style='text-align: center;'>🎰 Slow Rolling Number Generator</h1>", unsafe_allow_html=True)

# --- Controls ---
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    roll_speed = st.slider("Rolling Speed (seconds between changes)", 0.1, 1.0, 0.2, 0.1)
    total_duration = st.slider("Total Duration (seconds)", 2.0, 10.0, 5.0, 0.5)

# --- Rolling function ---
def roll_numbers_slowly():
    """Generate numbers with visible slow rolling effect"""
    
    # Generate final target numbers
    st.session_state.final_numbers = [random.randint(0, 9) for _ in range(8)]
    
    # Calculate number of steps
    steps = int(total_duration / roll_speed)
    
    # Create containers for each number
    cols = st.columns(8)
    containers = []
    for i in range(8):
        with cols[i]:
            containers.append(st.empty())
    
    # Rolling animation
    for step in range(steps):
        # Calculate progress
        progress = step / steps
        
        # Generate current display numbers
        current_display = []
        for i in range(8):
            # Gradually slow down each position
            position_stop_point = (i + 1) / 8  # Each position stops at different times
            
            if progress >= position_stop_point:
                # This position has stopped, show final number
                current_display.append(st.session_state.final_numbers[i])
                box_class = "number-box final"
            else:
                # Still rolling, show random number
                current_display.append(random.randint(0, 9))
                box_class = "number-box rolling"
            
            # Update display
            containers[i].markdown(f"<div class='{box_class}'>{current_display[i]}</div>", 
                                 unsafe_allow_html=True)
        
        # Wait before next update
        time.sleep(roll_speed)
        
        # Force refresh
        if step % 5 == 0:  # Refresh every 5 steps to show updates
            st.rerun()
    
    # Final update with all numbers stopped
    for i in range(8):
        containers[i].markdown(f"<div class='number-box final'>{st.session_state.final_numbers[i]}</div>", 
                             unsafe_allow_html=True)
    
    st.session_state.numbers = st.session_state.final_numbers.copy()
    st.session_state.rolling = False

# --- Button and display ---
if st.button("🎲 Start Slow Rolling", disabled=st.session_state.rolling):
    st.session_state.rolling = True
    with st.spinner("Rolling numbers..."):
        roll_numbers_slowly()
    st.success("Rolling complete!")

# --- Display current numbers if not rolling ---
if not st.session_state.rolling:
    cols = st.columns(8)
    for i in range(8):
        with cols[i]:
            st.markdown(f"<div class='number-box'>{st.session_state.numbers[i]}</div>", 
                       unsafe_allow_html=True)

# --- Statistics ---
if st.session_state.numbers and all(isinstance(x, int) for x in st.session_state.numbers):
    st.markdown("---")
    st.markdown("### 📊 Statistics")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Sum", sum(st.session_state.numbers))
    with col2:
        st.metric("Average", f"{sum(st.session_state.numbers)/8:.1f}")
    with col3:
        st.metric("Max", max(st.session_state.numbers))
    with col4:
        st.metric("Min", min(st.session_state.numbers))

# --- Instructions ---
st.markdown("---")
st.markdown("""
### 🎯 How it works:
- **Rolling Speed**: How fast numbers change (0.1-1.0 seconds)
- **Total Duration**: How long the entire rolling lasts (2-10 seconds)
- Numbers stop progressively from left to right
- Visual feedback shows rolling vs final states
""")
