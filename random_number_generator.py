import streamlit as st
import random
import time

# --- Page config ---
st.set_page_config(page_title="🎲 Random Number Row", layout="centered")

# --- Initialize session state ---
if 'rolling' not in st.session_state:
    st.session_state.rolling = False
if 'final_numbers' not in st.session_state:
    st.session_state.final_numbers = ["❓"] * 8
if 'current_numbers' not in st.session_state:
    st.session_state.current_numbers = ["❓"] * 8

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
        transition: all 0.3s ease-in-out;
        margin: 5px;
    }
    
    .number-box.rolling {
        background: linear-gradient(to bottom right, #FF6B6B, #FFE66D);
        animation: pulse 0.1s infinite;
    }
    
    .number-box.final {
        background: linear-gradient(to bottom right, #4ECDC4, #44A08D);
        transform: scale(1.05);
    }
    
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.05); }
        100% { transform: scale(1); }
    }
    
    .roll-button {
        background: linear-gradient(45deg, #FF6B6B, #4ECDC4);
        border: none;
        color: white;
        padding: 15px 30px;
        font-size: 1.2em;
        border-radius: 25px;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    
    .roll-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0,0,0,0.2);
    }
    
    .controls {
        text-align: center;
        margin: 20px 0;
    }
    </style>
""", unsafe_allow_html=True)

# --- Title ---
st.markdown("<h1 style='text-align: center;'>🎰 8-Digit Random Generator with Rolling Animation</h1>", unsafe_allow_html=True)
st.write("")

# --- Controls ---
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.markdown("<div class='controls'>", unsafe_allow_html=True)
    
    # Rolling speed control
    speed = st.slider("Rolling Speed (seconds)", min_value=0.5, max_value=5.0, value=2.0, step=0.5)
    
    # Roll duration control  
    roll_duration = st.slider("Roll Duration (seconds)", min_value=1.0, max_value=10.0, value=3.0, step=0.5)
    
    st.markdown("</div>", unsafe_allow_html=True)

# --- Button to generate numbers ---
if st.button("🎲 Start Rolling Numbers", key="roll_btn"):
    st.session_state.rolling = True
    st.session_state.final_numbers = [random.randint(0, 9) for _ in range(8)]
    st.rerun()

# --- Rolling logic ---
if st.session_state.rolling:
    # Create placeholders for the numbers
    cols = st.columns(8)
    placeholders = []
    for i in range(8):
        with cols[i]:
            placeholders.append(st.empty())
    
    # Rolling animation
    start_time = time.time()
    roll_steps = int(roll_duration / 0.1)  # Number of animation steps
    
    for step in range(roll_steps):
        current_time = time.time()
        elapsed = current_time - start_time
        
        # Generate random numbers for rolling effect
        rolling_numbers = [random.randint(0, 9) for _ in range(8)]
        
        # Gradually slow down and reveal final numbers
        for i in range(8):
            # Calculate when this digit should stop rolling
            stop_time = (i + 1) * (roll_duration / 8)
            
            if elapsed >= stop_time:
                # This digit has stopped rolling
                display_number = st.session_state.final_numbers[i]
                box_class = "number-box final"
            else:
                # This digit is still rolling
                display_number = rolling_numbers[i]
                box_class = "number-box rolling"
            
            with placeholders[i]:
                st.markdown(f"<div class='{box_class}'>{display_number}</div>", unsafe_allow_html=True)
        
        time.sleep(0.1)  # Animation frame delay
        
        if elapsed >= roll_duration:
            break
    
    # Final display
    for i in range(8):
        with placeholders[i]:
            st.markdown(f"<div class='number-box final'>{st.session_state.final_numbers[i]}</div>", unsafe_allow_html=True)
    
    st.session_state.rolling = False
    st.session_state.current_numbers = st.session_state.final_numbers.copy()

else:
    # --- Display current numbers in a row ---
    cols = st.columns(8)
    for i in range(8):
        with cols[i]:
            st.markdown(f"<div class='number-box'>{st.session_state.current_numbers[i]}</div>", unsafe_allow_html=True)

# --- Statistics ---
if all(isinstance(num, int) for num in st.session_state.current_numbers):
    st.write("")
    st.markdown("### 📊 Current Numbers Statistics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Sum", sum(st.session_state.current_numbers))
    
    with col2:
        st.metric("Average", f"{sum(st.session_state.current_numbers)/8:.1f}")
    
    with col3:
        st.metric("Max", max(st.session_state.current_numbers))
    
    with col4:
        st.metric("Min", min(st.session_state.current_numbers))

# --- Additional features ---
st.write("")
st.markdown("### 🎯 Features")
st.write("• **Rolling Animation**: Numbers cycle through random values before stopping")
st.write("• **Progressive Stop**: Numbers stop rolling one by one from left to right")
st.write("• **Customizable Speed**: Adjust rolling speed and duration")
st.write("• **Visual Effects**: Different colors for rolling vs final states")
st.write("• **Statistics**: See sum, average, max, and min of generated numbers")
