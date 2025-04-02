
import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")
st.title("Myron Pricing Tool v4.5")

try:
    # Load Excel file
    df = pd.read_excel("Product Price Calculator New.xlsx", sheet_name=None)
    sheet_names = list(df.keys())
    st.sidebar.selectbox("Select Sheet", sheet_names)
    
    st.markdown("### Sheet Previews")
    for sheet in sheet_names:
        st.markdown(f"#### {sheet}")
        st.dataframe(df[sheet].head())

    st.success("✅ File loaded successfully. Full functionality is being rebuilt.")
except Exception as e:
    st.error(f"❌ Could not load file: {e}")
