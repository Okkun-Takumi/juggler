import json
import streamlit as st

setting_file_path = 'setting_data.json'

def load_config(setting_file_path):
    """Load configuration from a JSON file."""
    with open(setting_file_path, 'r') as file:
        config = json.load(file)
    return config

if __name__ == "__main__":
    config = load_config(setting_file_path)
    st.title("Machine Settings Viewer")
    st.selectbox(
        'Select Machine',
        options=[machine['Name'] for machine in config['machines']]
    )