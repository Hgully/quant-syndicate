import streamlit as st
import pandas as pd
import os

# --- PAGE SETTINGS ---
st.set_page_config(page_title="Quant Syndicate Sniper", page_icon="🎯", layout="wide")

st.title("🎯 Quant Syndicate Global Sniper")
st.markdown("Live Expected Value (+EV) Opportunities based on Sharp Market Implied Probabilities.")
st.markdown("---")

# --- LOAD DATA ---
@st.cache_data(ttl=60) # Refreshes the data every 60 seconds
def load_data():
    if os.path.exists("ev_log.csv"):
        try:
            df = pd.read_csv("ev_log.csv")
            # Sort by highest EV first if the column exists
            if 'EV' in df.columns:
                # Clean the EV column (remove '%' and convert to float for sorting)
                df['EV_Sort'] = df['EV'].str.rstrip('%').astype('float')
                df = df.sort_values(by='EV_Sort', ascending=False).drop(columns=['EV_Sort'])
            return df
        except pd.errors.EmptyDataError:
            return pd.DataFrame()
    return pd.DataFrame()

df = load_data()

# --- DASHBOARD UI ---
if df.empty:
    st.info("📡 The Sniper is currently scanning the markets. No edges found yet. Please wait for the next update.")
else:
    # 1. The Dropdown Filter
    st.subheader("Filter Markets")
    
    # Get a list of unique sports currently in the CSV
    available_sports = df['Sport'].unique().tolist()
    available_sports.insert(0, "All Sports") # Add 'All' to the top of the list
    
    selected_sport = st.selectbox("Select a League to view:", available_sports)
    
    # Filter the dataframe based on the dropdown
    if selected_sport != "All Sports":
        display_df = df[df['Sport'] == selected_sport]
    else:
        display_df = df
        
    # 2. Display Metrics
    st.metric(label=f"Active Edges in {selected_sport}", value=len(display_df))
    
    # 3. Display the Table
    st.dataframe(
        display_df, 
        use_container_width=True, 
        hide_index=True,
        height=500
    )
    
    st.caption("Data refreshes automatically. Sharp book used: LowVig.ag")