import streamlit as st

# Read the README contents
with open("README.md", "r") as f:
    readme_content = f.read()

st.markdown(readme_content)