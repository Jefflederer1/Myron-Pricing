import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")
st.title("Myron Pricing Tool – v4.3")

# Load Excel
data = pd.read_excel("Product Price Calculator New.xlsx", sheet_name="Data", header=1)
data.columns = data.columns.str.strip()

qty_breaks = [24, 48, 96, 240, 432]

# --- ITEM SELECTION ---
st.sidebar.header("🟨 Item Selection")
item_options = data["Five_Digit"].dropna().unique()
selected_item = st.sidebar.selectbox("Item #", item_options)
item_row = data[data["Five_Digit"] == selected_item].iloc[0]
item_description = item_row["Item_Description"] if "Item_Description" in item_row else "No Description"

st.markdown(f"### Item: `{selected_item}` – {item_description}")

# --- SIDEBAR USER INPUTS ---
st.sidebar.header("🟨 Editable Yellow Inputs")
std_cost = st.sidebar.number_input("Std Cost (applies to all qty)", value=24.02, step=0.01)
discount_pct = st.sidebar.slider("Discount % (applies to all qty)", 0.0, 100.0, 20.0, step=0.5) / 100

list_prices = {}
for qty in qty_breaks:
    list_prices[qty] = st.sidebar.number_input(f"List Price @ Qty {qty}", value=round(50 - qty/20, 2), step=0.01)

# Setup Revenue editable fields
setup_list_price = st.sidebar.number_input("Setup List Price", value=105.00, step=0.01)
setup_std_cost = st.sidebar.number_input("Setup Std Cost", value=44.00, step=0.01)
setup_discount = st.sidebar.slider("Setup Discount %", 0.0, 100.0, 10.0, step=0.5) / 100

# Shipping and handling discounts only
shipping_discount = st.sidebar.slider("Shipping Discount %", 0.0, 100.0, 10.0, step=0.5) / 100
handling_discount = st.sidebar.slider("Handling Discount %", 0.0, 100.0, 0.0, step=0.5) / 100
growth_pct = st.sidebar.slider("Increase in Avg Order Units %", 0.0, 100.0, 25.0, step=1.0) / 100

# Pull base values from data
shipping_rev = item_row["Ship_Rev"]
shipping_cost = item_row["Net_Cog"]
handling_rev = item_row["Handling_Rev"]
handling_cost = item_row["Handling_Chgs"]

# Apply discounts
setup_price = setup_list_price * (1 - setup_discount)
shipping_price = shipping_rev * (1 - shipping_discount)
handling_price = handling_rev * (1 - handling_discount)

# --- METRIC TABLE ---
def calc_metrics(qty, lp, std_cost, discount):
    dp = lp * (1 - discount)
    gm = dp - std_cost
    gmp = gm / dp if dp else 0
    return dp, gm, gmp

rows = []
for qty in qty_breaks:
    dp, gm, gmp = calc_metrics(qty, list_prices[qty], std_cost, discount_pct)
    rows.append({
        "Qty": qty,
        "List Price": list_prices[qty],
        "Std Cost": std_cost,
        "Discount %": f"{discount_pct*100:.1f}%",
        "Disc Price": dp,
        "GM $": gm,
        "GM %": f"{gmp*100:.1f}%"
    })

st.subheader("Pricing Detail Table")
st.caption("💡 Only yellow-highlighted inputs are editable. All others are calculated.")
st.dataframe(pd.DataFrame(rows).set_index("Qty").style.format({
    "List Price": "${:.2f}",
    "Std Cost": "${:.2f}",
    "Disc Price": "${:.2f}",
    "GM $": "${:.2f}"
}))

# --- SCENARIO CALCULATION BASED ON LOWEST QTY (24) ---
base_qty = 24
new_qty = int(base_qty * (1 + growth_pct))

lp = list_prices[base_qty]
dp = lp * (1 - discount_pct)

orig_merch_sales = lp * base_qty
new_merch_sales = dp * new_qty

orig_merch_cogs = std_cost * base_qty
new_merch_cogs = std_cost * new_qty

# Add extras
def full_calc(merch_sales, merch_cogs):
    total_sales = merch_sales + setup_price + shipping_price + handling_price
    total_cogs = merch_cogs + setup_std_cost + shipping_cost + handling_cost
    gm = total_sales - total_cogs
    gm_pct = gm / total_sales if total_sales else 0
    return total_sales, total_cogs, gm, gm_pct

orig_sales, orig_cogs, orig_gm, orig_gmp = full_calc(orig_merch_sales, orig_merch_cogs)
new_sales, new_cogs, new_gm, new_gmp = full_calc(new_merch_sales, new_merch_cogs)

# --- SUMMARY TABLE ---
st.subheader("Revenue / Margin Projections")
summary = pd.DataFrame({
    "Scenario": ["Original", "Scenario"],
    "Sales": [f"${orig_sales:,.2f}", f"${new_sales:,.2f}"],
    "COGS": [f"${orig_cogs:,.2f}", f"${new_cogs:,.2f}"],
    "GM $": [f"${orig_gm:,.2f}", f"${new_gm:,.2f}"],
    "GM %": [f"{orig_gmp*100:.1f}%", f"{new_gmp*100:.1f}%"],
    "Change in GM $": ["—", f"${new_gm - orig_gm:,.2f}"]
}).set_index("Scenario")
st.table(summary)

# --- VISUAL SUMMARY ---
st.subheader("📊 Visual Summary")
col1, col2 = st.columns(2)
with col1:
    st.markdown("#### 🟦 Original")
    st.metric("Units", base_qty)
    st.metric("GM $", f"${orig_gm:,.2f}")
    st.metric("GM %", f"{orig_gmp*100:.1f}%")
with col2:
    st.markdown("#### 🟩 Scenario")
    st.metric("Units", new_qty, delta=f"{new_qty - base_qty}")
    st.metric("GM $", f"${new_gm:,.2f}", delta=f"${new_gm - orig_gm:,.2f}")
    st.metric("GM %", f"{new_gmp*100:.1f}%", delta=f"{(new_gmp - orig_gmp)*100:.1f}%")
