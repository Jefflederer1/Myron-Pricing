import streamlit as st
import pandas as pd

# Load and clean data
data = pd.read_excel("Product Price Calculator New.xlsx", sheet_name="Data", header=1)
data.columns = data.columns.str.strip()  # Remove leading/trailing spaces from column names

st.title("Myron Pricing Tool")

# Validate required columns
required_cols = ["Five_Digit", "Net_Cog", "Handling_Chgs", "Ship_Rev", "Merch_Rev", "Sum of totalRev", "Charge_Rev_SetUp", "Handling_Rev"]
missing = [col for col in required_cols if col not in data.columns]
if missing:
    st.error(f"Missing required columns: {', '.join(missing)}. Please check your Excel file.")
    st.stop()

# Extract and clean product ID options
product_options = pd.to_numeric(data["Five_Digit"], errors="coerce").dropna().astype(int).unique()
if not len(product_options):
    st.error("No valid product IDs found in the 'Five_Digit' column.")
    st.stop()

product_id = st.sidebar.selectbox("Select Product (Five_Digit ID)", sorted(product_options))
product_row = data[data["Five_Digit"] == product_id].iloc[0]

# Sidebar discount inputs
st.sidebar.markdown("### Discount Inputs")
discount_pct = st.sidebar.slider("% Discount on Merchandise", 0.0, 100.0, 0.0)
charge_discount = st.sidebar.number_input("Charge Discount ($)", value=0.0)
free_shipping = st.sidebar.checkbox("Free Shipping")

# Extract original values
net_cog = product_row["Net_Cog"]
handling_chgs = product_row["Handling_Chgs"]
ship_rev = product_row["Ship_Rev"]
merch_rev = product_row["Merch_Rev"]
total_rev = product_row["Sum of totalRev"]

# Discounted values
merch_rev_discounted = merch_rev * (1 - discount_pct / 100)
ship_rev_discounted = 0.0 if free_shipping else ship_rev
charge_rev_discounted = product_row["Charge_Rev_SetUp"] - charge_discount
total_rev_discounted = merch_rev_discounted + ship_rev_discounted + charge_rev_discounted + product_row["Handling_Rev"]

# Margin calculations
original_margin = (total_rev - net_cog - handling_chgs) / total_rev if total_rev else 0
discounted_margin = (total_rev_discounted - net_cog - handling_chgs) / total_rev_discounted if total_rev_discounted else 0

# Display results
st.header(f"Product ID: {product_id}")

col1, col2 = st.columns(2)
with col1:
    st.subheader("Original")
    st.metric("Revenue", f"${total_rev:.2f}")
    st.metric("Margin %", f"{original_margin:.2%}")
with col2:
    st.subheader("Discounted")
    st.metric("Revenue", f"${total_rev_discounted:.2f}")
    st.metric("Margin %", f"{discounted_margin:.2%}", delta=f"{discounted_margin - original_margin:.2%}")

# Recommendation
st.markdown("---")
if discounted_margin >= original_margin:
    st.success("✅ This discount maintains or improves profit margin.")
else:
    st.error("❌ This discount reduces the profit margin.")

# Margin chart
chart_data = pd.DataFrame({
    "Scenario": ["Original", "Discounted"],
    "Margin %": [original_margin * 100, discounted_margin * 100]
})
st.bar_chart(chart_data.set_index("Scenario"))
