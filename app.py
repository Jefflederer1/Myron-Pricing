import streamlit as st
import pandas as pd

# Load and clean data
data = pd.read_excel("Product Price Calculator New.xlsx", sheet_name="Scenario-1", header=None)

# Clean up column headers for the Original pricing table
st.title("Myron Pricing Tool – Enhanced")

# Set base row index locations
pricing_start_row = 8
pricing_end_row = 13
discount_start_row = 8
discount_end_row = 13

# Quantity Breaks
qty_breaks = [24, 48, 96, 240, 432]

st.sidebar.header("Discount Settings")

# Input: Discount % by Quantity Break
discounts = {}
for i, qty in enumerate(qty_breaks):
    discounts[qty] = st.sidebar.slider(f"Discount % for Qty {qty}", 0.0, 100.0, float(data.loc[discount_start_row + i, 10] * 100), step=0.5) / 100

# Setup, Shipping, Handling Discounts
setup_discount = st.sidebar.slider("Setup Discount %", 0.0, 100.0, float(data.loc[14, 10] * 100), step=0.5) / 100
shipping_discount = st.sidebar.slider("Shipping Discount %", 0.0, 100.0, float(data.loc[16, 10] * 100), step=0.5) / 100
handling_discount = st.sidebar.slider("Handling Discount %", 0.0, 100.0, float(data.loc[17, 10] * 100), step=0.5) / 100

# Order Unit Growth
order_growth_pct = st.sidebar.slider("Increase in Avg Order Units %", 0.0, 100.0, 25.0, step=1.0) / 100

# Select a Qty Break to view detailed calculations
selected_qty = st.selectbox("Select Quantity Break", qty_breaks)

# Extract original and discounted data for selected quantity
row_offset = qty_breaks.index(selected_qty)
list_price = data.loc[pricing_start_row + row_offset, 5]
std_cost = data.loc[pricing_start_row + row_offset, 6]
orig_gm = data.loc[pricing_start_row + row_offset, 7]
orig_gm_pct = data.loc[pricing_start_row + row_offset, 8]

disc_pct = discounts[selected_qty]
disc_price = list_price * (1 - disc_pct)
gm_dollars = disc_price - std_cost
gm_pct = gm_dollars / disc_price if disc_price else 0

# Revenue components
setup_rev = float(data.loc[14, 5])
shipping_rev = float(data.loc[16, 5])
handling_rev = float(data.loc[17, 5])

setup_cost = float(data.loc[14, 6])
shipping_cost = float(data.loc[16, 6])
handling_cost = float(data.loc[17, 6])

# Apply discounts
setup_price = setup_rev * (1 - setup_discount)
shipping_price = shipping_rev * (1 - shipping_discount)
handling_price = handling_rev * (1 - handling_discount)

# Margin Summary for Selected Qty Break
st.subheader(f"Summary for Qty {selected_qty}")

col1, col2 = st.columns(2)
with col1:
    st.metric("List Price", f"${list_price:.2f}")
    st.metric("Std Cost", f"${std_cost:.2f}")
    st.metric("Gross Margin $", f"${gm_dollars:.2f}")
with col2:
    st.metric("Discounted Price", f"${disc_price:.2f}", delta=f"-{disc_pct*100:.1f}%")
    st.metric("GM %", f"{gm_pct:.2%}")

# Category Summary Table
st.subheader("Category-Based Summary")

summary_data = {
    "Category": ["Product Pricing", "Setup Revenue", "Shipping Revenue", "Handling Revenue"],
    "Revenue": [disc_price, setup_price, shipping_price, handling_price],
    "Cost": [std_cost, setup_cost, shipping_cost, handling_cost]
}
df_summary = pd.DataFrame(summary_data)
df_summary["GM $"] = df_summary["Revenue"] - df_summary["Cost"]
df_summary["GM %"] = df_summary["GM $"] / df_summary["Revenue"]

st.dataframe(df_summary.set_index("Category").style.format({
    "Revenue": "${:.2f}",
    "Cost": "${:.2f}",
    "GM $": "${:.2f}",
    "GM %": "{:.2%}"
}))
