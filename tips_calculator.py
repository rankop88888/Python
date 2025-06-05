import streamlit as st
import pandas as pd

st.set_page_config(page_title="Venue Tip Calculator", layout="wide")
st.title("Venue Tip Calculator")

if 'venues' not in st.session_state:
    st.session_state['venues'] = [{}]

shared_percent = st.selectbox(
    "Shared Tips %", options=list(range(10, 101, 5)), index=10
)

if st.button("Add Venue"):
    st.session_state['venues'].append({})

venue_rows = []
for i, venue in enumerate(st.session_state['venues']):
    st.subheader(f"Venue {i + 1}")
    name = st.text_input("Venue Name", value=venue.get('name', ''), key=f'name_{i}')
    tips = st.number_input("Tips", value=venue.get('tips', 0.0), key=f'tips_{i}')
    employees = st.number_input("Employees", value=venue.get('employees', 0), step=1, key=f'emp_{i}')
    hours = st.number_input("Hours", value=venue.get('hours', 0.0), key=f'hours_{i}')
    non_shared = st.number_input("Non-shared %", value=venue.get('non_shared', 0.0), min_value=0.0, max_value=100.0, key=f'nonshare_{i}')
    st.session_state['venues'][i] = {
        'name': name,
        'tips': tips,
        'employees': employees,
        'hours': hours,
        'non_shared': non_shared,
    }
    shared_amount = tips * (shared_percent / 100.0)
    non_shared_amount = tips * (non_shared / 100.0)
    tips_per_hour = tips / hours if hours else 0
    venue_rows.append({
        'Venue': name,
        'Tips': tips,
        'Employees': employees,
        'Hours': hours,
        'Tips/Hour': tips_per_hour,
        'Shared Amount': shared_amount,
        'Non-shared Amount': non_shared_amount,
    })

df = pd.DataFrame(venue_rows)

if not df.empty:
    totals = {
        'Venue': 'TOTAL',
        'Tips': df['Tips'].sum(),
        'Employees': df['Employees'].sum(),
        'Hours': df['Hours'].sum(),
        'Tips/Hour': df['Tips'].sum() / df['Hours'].sum() if df['Hours'].sum() else 0,
        'Shared Amount': df['Shared Amount'].sum(),
        'Non-shared Amount': df['Non-shared Amount'].sum(),
    }
    df = pd.concat([df, pd.DataFrame([totals])], ignore_index=True)
    st.dataframe(df)
