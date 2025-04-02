import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")
st.title("Myron Pricing Tool – v4.1")

# Load Excel
data = pd.read_excel("Product Price Calculator New.xlsx", sheet_name="Data", header=1)
data.columns = data.columns.str.strip()

qty_breaks = [24, 48, 96, 240, 432]

# --- SIDEBAR INPUTS ---
st.sidebar.header("🟨 Input Only Yellow Fields")
list_prices, std_costs, discounts = {}, {}, {}

for qty in qty_breaks:
    list_prices[qty] = st.sidebar.number_input(f"List Price @ Qty {qty}", value=round(50 - qty/20, 2), step=0.01)
    std_costs[qty] = st.sidebar.number_input(f"Std Cost @ Qty {qty}", value=24.02, step=0.01)
    discounts[qty] = st.sidebar.slider(f"Discount % @ Qty {qty}", 0.0, 100.0, 20.0, step=0.5) / 100

setup_discount = st.sidebar.slider("Setup Discount %", 0.0, 100.0, 0.0, step=0.5) / 100
shipping_discount = st.sidebar.slider("Shipping Discount %", 0.0, 100.0, 0.0, step=0.5) / 100
handling_discount = st.sidebar.slider("Handling Discount %", 0.0, 100.0, 0.0, step=0.5) / 100
growth_pct = st.sidebar.slider("Increase in Avg Order Units %", 0.0, 100.0, 25.0, step=1.0) / 100

selected_qty = st.selectbox("Select Qty Break for Scenario Comparison", qty_breaks)

# --- LOGIC FUNCTIONS ---
def calc_metrics(qty, lp, cost, disc):
    dp = lp * (1 - disc)
    gm = dp - cost
    gmp = gm / dp if dp else 0
    return dp, gm, gmp

# --- DETAILED TABLE ---
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

st.subheader("Pricing Detail Table")
st.caption("💡 Adjust yellow inputs above. All other fields update automatically.")
st.dataframe(pd.DataFrame(rows).set_index("Qty").style.format({
    "List Price": "${:.2f}",
    "Std Cost": "${:.2f}",
    "Disc Price": "${:.2f}",
    "GM $": "${:.2f}"
}))

# --- SCENARIO COMPARISON LOGIC ---
lp = list_prices[selected_qty]
cost = std_costs[selected_qty]
disc = discounts[selected_qty]
disc_price = lp * (1 - disc)

setup_rev = data["Handling_Rev"].iloc[0]
shipping_rev = data["Ship_Rev"].iloc[0]
handling_rev = data["Handling_Chgs"].iloc[0]

setup_price = setup_rev * (1 - setup_discount)
shipping_price = shipping_rev * (1 - shipping_discount)
handling_price = handling_rev * (1 - handling_discount)

original_qty = selected_qty
new_qty = int(selected_qty * (1 + growth_pct))

orig_sales = lp * original_qty
orig_cogs = cost * original_qty
orig_gm = orig_sales - orig_cogs
orig_gm_pct = orig_gm / orig_sales

new_sales = disc_price * new_qty
new_cogs = cost * new_qty
new_gm = new_sales - new_cogs
new_gm_pct = new_gm / new_sales
gm_delta = new_gm - orig_gm

# --- AOV ---
st.subheader("Average Order Value Comparison")
aov1, aov2 = orig_sales, new_sales
st.columns([1, 1])[0].metric("Original AOV", f"${aov1:,.2f}")
st.columns([1, 1])[1].metric("Scenario AOV", f"${aov2:,.2f}", delta=f"{(aov2 - aov1)/aov1:.1%}")

# --- MARGIN TABLE ---
st.subheader("Revenue / Margin Projections")
st.table(pd.DataFrame({
    "Scenario": ["Original", "Scenario"],
    "Sales": [f"${orig_sales:,.2f}", f"${new_sales:,.2f}"],
    "Std COGS": [f"${orig_cogs:,.2f}", f"${new_cogs:,.2f}"],
    "GM $": [f"${orig_gm:,.2f}", f"${new_gm:,.2f}"],
    "GM %": [f"{orig_gm_pct*100:.1f}%", f"{new_gm_pct*100:.1f}%"],
    "Change in GM $": ["—", f"${gm_delta:,.2f}"]
}).set_index("Scenario"))

# --- LINEAR VISUAL SUMMARY ---
st.subheader("📊 Visual Summary: Side-by-Side")
st.caption("Original vs Scenario Comparison")
col_orig, col_new = st.columns(2)

with col_orig:
    st.markdown("#### 🟦 Original")
    st.metric("Total Merch Units", original_qty)
    st.metric("GM $", f"${orig_gm:,.2f}")
    st.metric("GM %", f"{orig_gm_pct*100:.1f}%")

with col_new:
    st.markdown("#### 🟩 Scenario")
    st.metric("Total Merch Units", new_qty, delta=f"{new_qty - original_qty}")
    st.metric("GM $", f"${new_gm:,.2f}", delta=f"${gm_delta:,.2f}")
    st.metric("GM %", f"{new_gm_pct*100:.1f}%", delta=f"{(new_gm_pct - orig_gm_pct)*100:.1f}%")
