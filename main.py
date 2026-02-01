import json
import streamlit as st
import pandas as pd
import numpy as np
import math

setting_file_path = 'setting_data.json'

def load_config(setting_file_path):
    """Load configuration from a JSON file."""
    with open(setting_file_path, 'r') as file:
        config = json.load(file)
    return config

def display_machine_settings(config, selection):
    """Display the SettingData for the selected machine."""
    # Find the selected machine dict by name (selectbox returns the Name string)
    selected_machine = next((m for m in config.get('machines', []) if m.get('Name') == selection), None)

    if selected_machine is None:
        st.error(f"Selected machine '{selection}' not found in configuration.")
    else:
        setting_data = selected_machine.get('SettingData')
        if setting_data is None:
            st.warning("No 'SettingData' found for the selected machine.")
        else:
            df = pd.DataFrame(setting_data)
            st.write(df)

if __name__ == "__main__":
    config = load_config(setting_file_path)
    st.title("Machine Settings Viewer")
    selection = st.selectbox(
        'Select Machine',
        options=[machine.get('Name', '') for machine in config.get('machines', [])]
    )
    your_total_number = st.number_input('Enter your total number of games:', min_value=0, step=100)
    your_reg = st.number_input('Enter your REG count:', min_value=0, step=1)
    your_big = st.number_input('Enter your BIG count:', min_value=0, step=1)



    display_machine_settings(config, selection)
    