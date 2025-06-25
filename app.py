import streamlit as st
import pandas as pd
import numpy as np
import json
import altair as alt
from data_loader import load_data_from_s3

# =============================================================================
# Main App Function
# =============================================================================
def create_champions_dashboard(df):
    """
    The main function to create the Streamlit dashboard.
    It takes the raw dataframe, processes it, and displays the analysis.
    """
    st.set_page_config(layout="wide", page_title="ChatGPT Champions Dashboard", initial_sidebar_state="expanded")

    # --- Sidebar for Controls ---
    with st.sidebar:
        st.header("🏆 Score Weighting")
        st.markdown("Adjust the weights for each category to recalculate the Champion Score. **Weights must sum to 100%.**")

        # Sliders for each weight component
        messages_weight = st.slider("Total Messages (%)", 0, 100, 30, 5)
        models_weight = st.slider("Model Diversity (%)", 0, 100, 20, 5)
        gpts_weight = st.slider("GPTs Messaged (%)", 0, 100, 20, 5)
        projects_weight = st.slider("Projects Created (%)", 0, 100, 20, 5)
        tools_weight = st.slider("Tool Usage (%)", 0, 100, 10, 5)

        total_weight = messages_weight + models_weight + gpts_weight + projects_weight + tools_weight
        if total_weight != 100:
            st.error(f"Weights must sum to 100%. Current sum: {total_weight}%")
        else:
            st.success("Weights sum to 100%.")

    # --- Main Dashboard Title ---
    st.title("🏆 ChatGPT Champions Dashboard")
    st.markdown("""
    Welcome to the Champions Dashboard! This application analyzes user activity over time
    to identify the most active, consistent, and powerful users of ChatGPT.
    The **Champion Score** is calculated based on a combination of activity metrics.
    This dashboard ranks users based on their average weekly score and consistency over time.
    Use the sidebar to adjust how the Champion Score is calculated.
    """)

    # --- Data Processing ---
    # Use a caching mechanism to avoid reprocessing data on every interaction.
    @st.cache_data
    def process_data(df_raw, weights):
        df_processed = df_raw.copy()

        # Convert relevant columns to numeric, coercing errors
        numeric_cols = ['messages', 'gpts_messaged', 'projects_created']
        for col in numeric_cols:
            df_processed[col] = pd.to_numeric(df_processed[col], errors='coerce')

        # Fill NaNs in key columns to avoid errors during calculations
        df_processed[numeric_cols] = df_processed[numeric_cols].fillna(0)
        df_processed['model_to_messages'] = df_processed['model_to_messages'].fillna('{}')
        
        # Gracefully handle the absence of the 'tool_to_messages' column
        if 'tool_to_messages' not in df_processed.columns:
            df_processed['tool_to_messages'] = '{}'
        else:
            df_processed['tool_to_messages'] = df_processed['tool_to_messages'].fillna('{}')

        df_processed['name'] = df_processed['name'].fillna('Unknown User')
        df_processed['email'] = df_processed['email'].fillna('Unknown Email')
        df_processed['company'] = df_processed['company'].fillna('N/A').astype(str)
        if 'pbu' in df_processed.columns:
            df_processed['pbu'] = df_processed['pbu'].fillna('N/A').astype(str)
        
        # Ensure period_end is a datetime object for proper sorting
        df_processed['period_end'] = pd.to_datetime(df_processed['period_end'])

        # --- Feature Engineering: Calculate components of the Champion Score ---
        def safe_json_loads(s):
            try:
                # The data uses single quotes, which is not valid JSON. Replace them.
                return json.loads(s.replace("'", "\""))
            except (json.JSONDecodeError, AttributeError):
                return {}

        # Calculate model and tool diversity for each row (each week)
        df_processed['num_models_used'] = df_processed['model_to_messages'].apply(lambda x: len(safe_json_loads(x)))
        df_processed['num_tools_used'] = df_processed['tool_to_messages'].apply(lambda x: len(safe_json_loads(x)))

        # Normalize metrics on a scale of 0 to 1 to make them comparable
        # Normalization is done on the entire column
        df_processed['msg_norm'] = (df_processed['messages'] - df_processed['messages'].min()) / (df_processed['messages'].max() - df_processed['messages'].min())
        df_processed['model_norm'] = (df_processed['num_models_used'] - df_processed['num_models_used'].min()) / (df_processed['num_models_used'].max() - df_processed['num_models_used'].min())
        df_processed['gpts_norm'] = (df_processed['gpts_messaged'] - df_processed['gpts_messaged'].min()) / (df_processed['gpts_messaged'].max() - df_processed['gpts_messaged'].min())
        df_processed['projects_norm'] = (df_processed['projects_created'] - df_processed['projects_created'].min()) / (df_processed['projects_created'].max() - df_processed['projects_created'].min())
        df_processed['tool_norm'] = (df_processed['num_tools_used'] - df_processed['num_tools_used'].min()) / (df_processed['num_tools_used'].max() - df_processed['num_tools_used'].min())
        
        # Handle cases where max and min are the same (results in NaN)
        norm_cols = ['msg_norm', 'model_norm', 'gpts_norm', 'projects_norm', 'tool_norm']
        df_processed[norm_cols] = df_processed[norm_cols].fillna(0)

        # --- Calculate the Weekly Champion Score ---
        df_processed['champion_score'] = (
            df_processed['msg_norm'] * (weights['messages'] / 100) +
            df_processed['model_norm'] * (weights['models'] / 100) +
            df_processed['gpts_norm'] * (weights['gpts'] / 100) +
            df_processed['projects_norm'] * (weights['projects'] / 100) +
            df_processed['tool_norm'] * (weights['tools'] / 100)
        ) * 100 # Scale to 100 for better readability

        return df_processed

    # --- Aggregate Data for All-Time Analysis ---
    @st.cache_data
    def get_all_time_champions(df_processed):
        # Filter out users with no activity to clean up the list
        active_users_df = df_processed[df_processed['messages'] > 0]

        # Group by user to calculate all-time stats
        agg_champions = active_users_df.groupby(['name', 'email', 'company']).agg(
            avg_champion_score=('champion_score', 'mean'),
            score_stability=('champion_score', 'std'),
            total_messages=('messages', 'sum'),
            active_weeks=('period_end', 'nunique'),
            last_active=('period_end', 'max')
        ).reset_index()

        # Fill NaN in stability for users with only one active week (std is NaN)
        agg_champions['score_stability'] = agg_champions['score_stability'].fillna(0)
        
        # Sort to find the top champions
        agg_champions = agg_champions.sort_values(by='avg_champion_score', ascending=False)
        agg_champions['rank'] = agg_champions['avg_champion_score'].rank(method='dense', ascending=False).astype(int)

        return agg_champions

    # --- UI Rendering ---
    # Only proceed if weights are valid
    if total_weight == 100:
        weights = {
            'messages': messages_weight,
            'models': models_weight,
            'gpts': gpts_weight,
            'projects': projects_weight,
            'tools': tools_weight
        }
        df_processed = process_data(df, weights)
        df_champions = get_all_time_champions(df_processed)

        # --- Main Dashboard View ---
        st.header("Leaderboard: All-Time Champions")
        st.markdown("Users are ranked by their average weekly `Champion Score`. `Score Stability` shows the standard deviation of their score; a lower number means more consistent activity.")

        col1, col2 = st.columns([1, 2])
        with col1:
            num_champions = st.slider(
                "Select number of top champions to display:",
                min_value=5,
                max_value=100,
                value=10,
                step=5
            )

        with col2:
            st.write("") # Spacer

        # Display the champions table
        st.dataframe(
            df_champions[['rank', 'name', 'company', 'avg_champion_score', 'score_stability', 'active_weeks', 'total_messages', 'last_active']].head(num_champions).style.format({
                'avg_champion_score': '{:.1f}',
                'score_stability': '{:.1f}',
                'total_messages': '{:,.0f}'
            }),
            use_container_width=True
        )

        st.divider()

        # --- Individual User Deep Dive ---
        st.header("🔍 User Deep Dive")
        st.markdown("Select a user to see a detailed breakdown of their activity and performance over time.")

        # Get a sorted list of user names for the selectbox
        user_list = df_champions['name'].unique()
        selected_user_name = st.selectbox("Select User:", user_list)

        if selected_user_name:
            # Filter data for the selected user
            user_data = df_processed[df_processed['name'] == selected_user_name].sort_values(by='period_end')
            user_champion_stats = df_champions[df_champions['name'] == selected_user_name].iloc[0]

            st.subheader(f"Activity for {selected_user_name}")

            # Display key stats in columns
            kpi1, kpi2, kpi3, kpi4 = st.columns(4)
            kpi1.metric("Overall Rank", f"#{user_champion_stats['rank']}")
            kpi2.metric("Avg. Weekly Score", f"{user_champion_stats['avg_champion_score']:.1f}")
            kpi3.metric("Score Stability (Std Dev)", f"{user_champion_stats['score_stability']:.1f}")
            kpi4.metric("Total Active Weeks", f"{user_champion_stats['active_weeks']}")
            
            # --- Chart: Champion Score Over Time ---
            st.markdown("#### Weekly Champion Score Trend")
            
            # Create a chart-friendly dataframe for Altair
            chart_data = user_data[['period_end', 'champion_score']].reset_index()

            # Check if there is data to plot
            if not chart_data.empty:
                # Use Altair for more control over the chart
                chart = alt.Chart(chart_data).mark_line(point=True).encode(
                    x=alt.X('period_end:T', title='Week', axis=alt.Axis(format="%Y-%m-%d")),
                    y=alt.Y('champion_score:Q', title='Weekly Champion Score'),
                    tooltip=['period_end', 'champion_score']
                ).interactive()
                st.altair_chart(chart, use_container_width=True)
            else:
                st.warning("No weekly score data available to display for this user.")

        # --- Data Explorer ---
        with st.expander("View Raw and Processed Data"):
            st.subheader("Processed Data with Champion Scores")
            st.dataframe(df_processed)
            st.subheader("Original Uploaded Data")
            st.dataframe(df)
    else:
        st.error("Please adjust the weights in the sidebar until they sum to 100% to view the dashboard.")


# =============================================================================
# Load Data and Run App
# =============================================================================
# This part of the script assumes the user has already loaded the dataframe `df`.
# In a real-world scenario, you would load it from a file like this:
#
# try:
#     # The user has specified the file in the prompt
#     df = pd.read_csv("2025-06-25T16-53_export.csv")
#     create_champions_dashboard(df)
# except FileNotFoundError:
#     st.error("Error: The specified CSV file was not found.")
#     st.info("Please make sure '2025-06-25T16-53_export.csv' is in the same directory.")
# except Exception as e:
#     st.error(f"An error occurred while loading the data: {e}")

# Since the prompt specifies to use a pre-existing dataframe named 'df',
# we will simulate this by loading the file and then calling the main function.
# The user will not see this part, but it makes the script runnable.
if __name__ == '__main__':
    try:
        # This is where you would have your dataframe `df`
        full_df = load_data_from_s3("Weekly")
        create_champions_dashboard(full_df)
    except FileNotFoundError:
        st.error("Fatal Error: The data file '2025-06-25T16-53_export.csv' could not be found.")
        st.write("Please ensure the data file is available before running the app.")

