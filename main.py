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
    p_miss = max(1e-12, 1.0 - p_big - p_reg)
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

# Calculate hit probabilities using Bayesian approach
def hit_probabilities_bayes(k, p_big, p_reg, posteriors):
    prob_no_hit = 0.0
    p_big = 1/p_big
    p_reg = 1/p_reg
    for s, ps in posteriors.items():
        p_hit = p_big + p_reg
        prob_no_hit += ps * ((1 - p_hit) ** k)

    prob_within_k = 1 - prob_no_hit

    expected_spins = sum(
        posteriors[s] / (p_big + p_reg)
        for s in posteriors
    )

    return prob_within_k, expected_spins


# Calculate expected value per spin
def expected_value_per_spin(settings, posteriors,
                            bet=100, big_pay=252, reg_pay=96):
    ev = 0.0

    for s, prob in posteriors.items():
        setting = settings.get(s)
        if not setting:
            continue

        # Read denominators (stored as integers like 200 meaning 1/200)
        big_den = setting.get("big")
        reg_den = setting.get("reg")

        # Safely convert to probabilities, handling zero/None/invalid values
        try:
            p_big = 1.0 / float(big_den) if big_den and float(big_den) != 0 else 0.0
        except (TypeError, ValueError):
            p_big = 0.0

        try:
            p_reg = 1.0 / float(reg_den) if reg_den and float(reg_den) != 0 else 0.0
        except (TypeError, ValueError):
            p_reg = 0.0

        ev_s = -bet + p_big * big_pay + p_reg * reg_pay
        ev += prob * ev_s

    return float(ev)

# Determine whether to quit based on expected value
def should_quit_safe(settings, posteriors, risk_margin=-0.1):
    ev = expected_value_per_spin(settings, posteriors)
    return ev < risk_margin, ev

# Determine whether to quit based on expected value over a horizon
def should_quit_with_horizon(settings, posteriors, horizon=100):
    ev_per_spin = expected_value_per_spin(settings, posteriors)
    total_ev = ev_per_spin * horizon
    return total_ev < 0, total_ev



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
        
        # Hit probabilities within 100 spins
        hit_prob, expected_spins = hit_probabilities_bayes(
            100,
            settings_dict[best_setting]["big"],
            settings_dict[best_setting]["reg"],
            posteriors
        )

        st.write(f"Hit Probability within 100 spins: {hit_prob:.2%}")
        st.write(f"Expected Spins by next hit: {expected_spins:.2f}")  

        #expected value per spin
        quit_flag, ev = should_quit_with_horizon(settings_dict, posteriors)
        st.write(f"Expected Value per Spin: {ev:.2f}")
        # Dynamic recommendation display: colored and shows EV
        rec_placeholder = st.empty()
        # Show EV alongside the recommendation and use color to emphasize
        if quit_flag:
            rec_placeholder.error(f"Recommendation: It is advisable to quit playing this machine. (EV: {ev:.2f})")
        else:
            rec_placeholder.success(f"Recommendation: You can continue playing this machine. (EV: {ev:.2f})")

    # Display the machine settings
    display_machine_settings(config, selection)
    