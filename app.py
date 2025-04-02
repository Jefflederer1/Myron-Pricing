import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")
st.title("Myron Pricing Tool – v4")

# Load the Excel file
data = pd.read_excel("Product Price Calculator New.xlsx", sheet_name="Data", header=1)
data.columns = data.columns.str.strip()

# Define qty breaks
qty_breaks = [24, 48, 96, 240, 432]

# Sidebar: Inputs for pricing
st.sidebar.header("Manual Inputs (Yellow Cells)")
list_prices = {}
std_costs = {}
discounts = {}

for qty in qty_breaks:
    list_prices[qty] = st.sidebar.number_input(f"List Price @ Qty {qty}", value=round(50 - qty/20, 2), step=0.01)
    std_costs[qty] = st.sidebar.number_input(f"Std Cost @ Qty {qty}", value=24.02, step=0.01)
    discounts[qty] = st.sidebar.slider(f"Discount % @ Qty {qty}", 0.0, 100.0, 20.0, step=0.5) / 100

setup_discount = st.sidebar.slider("Setup Discount %", 0.0, 100.0, 0.0, step=0.5) / 100
shipping_discount = st.sidebar.slider("Shipping Discount %", 0.0, 100.0, 0.0, step=0.5) / 100
handling_discount = st.sidebar.slider("Handling Discount %", 0.0, 100.0, 0.0, step=0.5) / 100
growth_pct = st.sidebar.slider("Increase in Avg Order Units %", 0.0, 100.0, 25.0, step=1.0) / 100

# Select a quantity break to focus on
selected_qty = st.selectbox("Select Qty Break to View Scenario Comparison", qty_breaks)

# Set values from 'Data' tab
setup_rev = data["Handling_Rev"].iloc[0]
shipping_rev = data["Ship_Rev"].iloc[0]
handling_rev = data["Handling_Chgs"].iloc[0]

# Build detailed table
def calc_metrics(qty, lp, cost, disc):
    dp = lp * (1 - disc)
    gm = dp - cost
    gmp = gm / dp if dp else 0
    return dp, gm, gmp

rows = []
for qty in qty_breaks:
    dp, gm, gmp = calc_metrics(qty, list_prices[qty], std_costs[qty], discounts[qty])
    rows.append({
        "Qty": qty,
        "List Price": list_prices[qty],
        "Std Cost": std_costs[qty],
        "Discount %": f"{discounts[qty]*100:.1f}%",
        "Disc Price": dp,
        "GM $": gm,
        "GM %": f"{gmp*100:.1f}%"
    })

st.subheader("Original vs Scenario – Pricing Detail")
st.dataframe(pd.DataFrame(rows).set_index("Qty").style.format({
    "List Price": "${:.2f}",
    "Std Cost": "${:.2f}",
    "Disc Price": "${:.2f}",
    "GM $": "${:.2f}"
}))

# Scenario projections
lp = list_prices[selected_qty]
cost = std_costs[selected_qty]
disc = discounts[selected_qty]
disc_price = lp * (1 - disc)

# Setup/Shipping/Handling
setup_price = setup_rev * (1 - setup_discount)
shipping_price = shipping_rev * (1 - shipping_discount)
handling_price = handling_rev * (1 - handling_discount)

# Total revenue / costs
original_sales = lp * selected_qty
original_cogs = cost * selected_qty
original_gm = original_sales - original_cogs
original_gm_pct = original_gm / original_sales

# Scenario (w/ growth)
new_qty = int(selected_qty * (1 + growth_pct))
scenario_sales = disc_price * new_qty
scenario_cogs = cost * new_qty
scenario_gm = scenario_sales - scenario_cogs
scenario_gm_pct = scenario_gm / scenario_sales
gm_delta = scenario_gm - original_gm

# Output: AOV comparison
st.subheader("Average Order Value Comparison")
col1, col2 = st.columns(2)
with col1:
    st.metric("Original AOV", f"${original_sales:.2f}")
with col2:
    st.metric("Scenario AOV", f"${scenario_sales:.2f}", delta=f"{(scenario_sales - original_sales)/original_sales:.1%}")

# Output: Margin Comparison Table
st.subheader("Total Revenue / Margin Projections")
comparison = pd.DataFrame({
    "Scenario": ["Original", "Discounted"],
    "Sales": [f"${original_sales:,.2f}", f"${scenario_sales:,.2f}"],
    "Std COGS": [f"${original_cogs:,.2f}", f"${scenario_cogs:,.2f}"],
    "GM $": [f"${original_gm:,.2f}", f"${scenario_gm:,.2f}"],
    "GM %": [f"{original_gm_pct*100:.1f}%", f"{scenario_gm_pct*100:.1f}%"],
    "Change in GM $": ["—", f"${gm_delta:,.2f}"]
}).set_index("Scenario")

st.table(comparison)

# Output: Summary View Block
st.subheader("Visual Summary")
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total Merch Units (Orig)", selected_qty)
    st.metric("GM $", f"${original_gm:,.2f}")
with col2:
    st.metric("Total Merch Units (New)", new_qty)
    st.metric("GM $", f"${scenario_gm:,.2f}", delta=f"${gm_delta:,.2f}")
with col3:
    st.metric("GM % (Orig)", f"{original_gm_pct*100:.1f}%")
    st.metric("GM % (New)", f"{scenario_gm_pct*100:.1f}%", delta=f"{(scenario_gm_pct - original_gm_pct)*100:.1f}%")
