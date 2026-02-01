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
    selection = st.selectbox(
        'Select Machine',
        options=[machine.get('Name', '') for machine in config.get('machines', [])]
    )

    # Find the selected machine dict by name (selectbox returns the Name string)
    selected_machine = next((m for m in config.get('machines', []) if m.get('Name') == selection), None)

    if selected_machine is None:
        st.error(f"Selected machine '{selection}' not found in configuration.")
    else:
        setting_data = selected_machine.get('SettingData')
        if setting_data is None:
            st.warning("No 'SettingData' found for the selected machine.")
        else:
            st.write(setting_data)