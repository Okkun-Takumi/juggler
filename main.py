import json
import streamlit as st
import pandas as pd
import numpy as np
import math

setting_file_path = 'setting_data.json'

# Load configuration from JSON file
def load_config(setting_file_path):
    """Load configuration from a JSON file."""
    with open(setting_file_path, 'r') as file:
        config = json.load(file)
    return config

# Display machine settings in a DataFrame
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

# Calculate log likelihood
def log_likelihood(total_number, count_big, count_reg, p_big, p_reg):
    p_big = 1/p_big
    p_reg = 1/p_reg
    p_miss = 1.0 - p_big - p_reg
    if p_miss <= 0:
        return float("-inf")

    return (
        count_big * math.log(p_big) +
        count_reg * math.log(p_reg) +
        (total_number - count_big - count_reg) * math.log(p_miss)
    )

def estimate_settings(total_number, count_big, count_reg, settings):
    logL = {}

    for s, probs in settings.items():
        logL[s] = log_likelihood(
            total_number, count_big, count_reg,
            probs["big"],
            probs["reg"]
        )

    # Calculate posterior probabilities
    max_logL = max(logL.values())
    likelihoods = {
        s: math.exp(logL[s] - max_logL)
        for s in logL
    }

    total = sum(likelihoods.values())
    posteriors = {
        s: likelihoods[s] / total
        for s in likelihoods
    }

    # Find the setting with the highest posterior probability
    best_setting = max(posteriors, key=posteriors.get)

    return best_setting, posteriors

# Calculate hit probabilities
def hit_probabilities(k, p_big, p_reg):
    p_big = 1/p_big
    p_reg = 1/p_reg
    p_hit = p_big + p_reg

    prob_within_k = 1.0 - (1.0 - p_hit) ** k
    expected_spins = 1.0 / p_hit

    return prob_within_k, expected_spins


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

    # Get settings for the selected machine
    selected_machine = next((m for m in config.get('machines', []) if m.get('Name') == selection), None)
    
    if selected_machine:
        settings_dict = {
            setting['setting']: {
                "big": setting['BIG'],
                "reg": setting['REG']
            }
            for setting in selected_machine.get('SettingData', [])
        }
        
        # Display estimated settings
        best_setting, posteriors = estimate_settings(
            your_total_number,
            your_big,
            your_reg,
            settings_dict
        )
        st.write(f"Estimated Setting: {best_setting}")
        st.write("Posterior Probabilities:")
        
        # Convert posteriors to DataFrame and display as percentages
        posteriors_df = pd.DataFrame(
            list(posteriors.items()),
            columns=['Setting', 'Probability']
        )
        posteriors_df['Probability (%)'] = (posteriors_df['Probability'] * 100).round(2)
        posteriors_df = posteriors_df[['Setting', 'Probability (%)']]
        
        # Highlight the highest probability
        posteriors_df_styled = posteriors_df.style.highlight_max(subset=['Probability (%)'], color='yellow')
        st.dataframe(posteriors_df_styled, use_container_width=True)

    # Display the machine settings
    display_machine_settings(config, selection)
    