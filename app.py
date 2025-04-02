import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")

# Load and clean data
data = pd.read_excel("Product Price Calculator New.xlsx", sheet_name="Data", header=1)
data.columns = data.columns.str.strip()

st.title("Myron Pricing Tool – v3")

# Quantity breaks
qty_breaks = [24, 48, 96, 240, 432]

# Sidebar Inputs
st.sidebar.header("User Input – Manual Entry")
list_prices = {}
discounts = {}

st.sidebar.markdown("### List Price & Discount % (per Qty Break)")
for qty in qty_breaks:
    list_prices[qty] = st.sidebar.number_input(f"List Price @ Qty {qty}", value=round(50 - qty/20, 2), step=0.01)
    discounts[qty] = st.sidebar.slider(f"Discount % @ Qty {qty}", 0.0, 100.0, 0.0, step=0.5) / 100

setup_discount = st.sidebar.slider("Setup Discount %", 0.0, 100.0, 0.0, step=0.5) / 100
shipping_discount = st.sidebar.slider("Shipping Discount %", 0.0, 100.0, 0.0, step=0.5) / 100
handling_discount = st.sidebar.slider("Handling Discount %", 0.0, 100.0, 0.0, step=0.5) / 100
growth_pct = st.sidebar.slider("Increase in Avg Order Units %", 0.0, 100.0, 25.0, step=1.0) / 100

# Select Qty Break to focus on
selected_qty = st.selectbox("Select Qty Break to View Details", qty_breaks)

# Assume standard cost pulls from 'Data' tab by row index (for simplicity)
std_costs = data["Net_Cog"].iloc[0]
setup_rev = data["Handling_Rev"].iloc[0]
shipping_rev = data["Ship_Rev"].iloc[0]
handling_rev = data["Handling_Chgs"].iloc[0]

# Original vs Discounted Calculations
def calc_scenario(qty, list_price, discount, std_cost):
    disc_price = list_price * (1 - discount)
    gm_dollars = disc_price - std_cost
    gm_pct = gm_dollars / disc_price if disc_price else 0
    return disc_price, gm_dollars, gm_pct

# Build comparison table
comparison_rows = []
for qty in qty_breaks:
    disc_price, gm_dollars, gm_pct = calc_scenario(qty, list_prices[qty], discounts[qty], std_costs)
    row = {
        "Qty Break": qty,
        "List Price": list_prices[qty],
        "Discount %": f"{discounts[qty]*100:.1f}%",
        "Disc Price": disc_price,
        "Std Cost": std_costs,
        "GM $": gm_dollars,
        "GM %": f"{gm_pct*100:.1f}%"
    }
    comparison_rows.append(row)

st.subheader("Original vs Scenario – Pricing Summary")
st.dataframe(pd.DataFrame(comparison_rows).set_index("Qty Break").style.format({
    "List Price": "${:.2f}",
    "Disc Price": "${:.2f}",
    "Std Cost": "${:.2f}",
    "GM $": "${:.2f}"
}))

# Avg Order Value Simulation for selected Qty
selected_lp = list_prices[selected_qty]
selected_disc = discounts[selected_qty]
disc_price = selected_lp * (1 - selected_disc)
orig_value = selected_lp * selected_qty
disc_value = disc_price * selected_qty * (1 + growth_pct)

st.subheader("Average Order Value Comparison")
col1, col2 = st.columns(2)
with col1:
    st.metric("Original AOV", f"${orig_value:,.2f}")
with col2:
    st.metric("Scenario AOV", f"${disc_value:,.2f}", delta=f"{(disc_value - orig_value)/orig_value:.1%}")

# Revenue / Margin Projection
st.subheader("Total Revenue / Margin Projections")
base_sales = orig_value
base_cogs = std_costs * selected_qty
base_gm = base_sales - base_cogs
base_gm_pct = base_gm / base_sales

# Scenario 1
proj_sales = disc_price * selected_qty * (1 + growth_pct)
proj_cogs = std_costs * selected_qty * (1 + growth_pct)
proj_gm = proj_sales - proj_cogs
proj_gm_pct = proj_gm / proj_sales
gm_change = proj_gm - base_gm

st.table(pd.DataFrame({
    "Scenario": ["Original", "Discounted"],
    "Sales": [f"${base_sales:,.2f}", f"${proj_sales:,.2f}"],
    "Std COGS": [f"${base_cogs:,.2f}", f"${proj_cogs:,.2f}"],
    "GM $": [f"${base_gm:,.2f}", f"${proj_gm:,.2f}"],
    "GM %": [f"{base_gm_pct*100:.1f}%", f"{proj_gm_pct*100:.1f}%"],
    "Δ GM $": ["—", f"${gm_change:,.2f}"]
}).set_index("Scenario"))
