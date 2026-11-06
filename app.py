import streamlit as st

st.title("PinkTax Detective")

try:
    has_key = "ANTHROPIC_API_KEY" in st.secrets
except Exception:
    has_key = False

st.write(f"ANTHROPIC_API_KEY in st.secrets: {has_key}")
