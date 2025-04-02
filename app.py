
import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")
st.title("Myron Pricing Tool v4.5 – Complete")

# Load Excel
data = pd.read_excel("Product Price Calculator New.xlsx", sheet_name="Data", header=1)
data.columns = data.columns.str.strip()

# Optional: load external item number-to-product name mapping
try:
    mapping = pd.read_excel("ItemNumber_ProductName_Mapping.xlsx")
    mapping = mapping.set_index("Item Number")["Product Name"].to_dict()
except:
    mapping = {}

# --- ITEM SELECTION ---
st.sidebar.header("🟨 Item Selection")
item_options = data["Five_Digit"].dropna().unique()
selected_item = st.sidebar.selectbox("Item #", item_options)
item_row = data[data["Five_Digit"] == selected_item].iloc[0]
item_description = mapping.get(selected_item, "No description")

st.markdown(f"### Item: `{selected_item}` – {item_description}")

# --- QTY BREAK INPUTS ---
st.sidebar.header("🟨 Quantity Breaks")
qty_breaks = []
for i in range(5):
    qty = st.sidebar.number_input(f"Qty Break {i+1}", value=[24, 48, 96, 240, 432][i], step=1)
    qty_breaks.append(int(qty))

# --- PRICING INPUTS ---
st.sidebar.header("🟨 Pricing")
std_cost = st.sidebar.number_input("Std Cost (all qty)", value=24.02, step=0.01)

# Discount % input + slider
disc_col1, disc_col2 = st.sidebar.columns([2, 1])
discount_slider = disc_col1.slider("Discount % (all qty)", 0.0, 100.0, 20.0, step=0.5)
discount_input = disc_col2.number_input(" ", value=discount_slider, step=0.5, format="%.2f")
discount_pct = discount_input / 100

list_prices = {}
st.sidebar.markdown("#### List Prices")
for qty in qty_breaks:
    list_prices[qty] = st.sidebar.number_input(f"List Price @ Qty {qty}", value=round(50 - qty/20, 2), step=0.01)

# --- SETUP ---
st.sidebar.header("🟨 Setup Revenue")
setup_list = st.sidebar.number_input("Setup List Price", value=105.00, step=0.01)
setup_cost = st.sidebar.number_input("Setup Std Cost", value=44.00, step=0.01)
sc1, sc2 = st.sidebar.columns([2, 1])
setup_disc_slider = sc1.slider("Setup Discount %", 0.0, 100.0, 10.0, step=0.5)
setup_disc_input = sc2.number_input("Setup % Input", value=setup_disc_slider, step=0.5, format="%.2f")
setup_discount = setup_disc_input / 100

# --- SHIPPING ---
st.sidebar.header("🟨 Shipping")
sh1, sh2 = st.sidebar.columns([2, 1])
ship_disc_slider = sh1.slider("Shipping Discount %", 0.0, 100.0, 10.0, step=0.5)
ship_disc_input = sh2.number_input("Shipping % Input", value=ship_disc_slider, step=0.5, format="%.2f")
shipping_discount = ship_disc_input / 100

# --- HANDLING ---
st.sidebar.header("🟨 Handling")
hd1, hd2 = st.sidebar.columns([2, 1])
hand_disc_slider = hd1.slider("Handling Discount %", 0.0, 100.0, 0.0, step=0.5)
hand_disc_input = hd2.number_input("Handling % Input", value=hand_disc_slider, step=0.5, format="%.2f")
handling_discount = hand_disc_input / 100

# --- GROWTH %
st.sidebar.header("🟨 Growth Projection")
g1, g2 = st.sidebar.columns([2, 1])
growth_slider = g1.slider("Increase in Avg Order Units %", 0.0, 100.0, 25.0, step=1.0)
growth_input = g2.number_input("Growth % Input", value=growth_slider, step=1.0)
growth_pct = growth_input / 100

# --- Pull original data
shipping_rev = item_row["Ship_Rev"]
shipping_cogs = item_row["Net_Cog"]
handling_rev = item_row["Handling_Rev"]
handling_cogs = item_row["Handling_Chgs"]

# Discounted revenues
setup_rev = setup_list * (1 - setup_discount)
shipping_net = shipping_rev * (1 - shipping_discount)
handling_net = handling_rev * (1 - handling_discount)

# --- CALCULATIONS ---
def calc_metrics(qty, lp, cost, discount):
    dp = lp * (1 - discount)
    gm = dp - cost
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

st.subheader("Pricing Table")
st.dataframe(pd.DataFrame(rows).set_index("Qty").style.format({
    "List Price": "${:.2f}",
    "Std Cost": "${:.2f}",
    "Disc Price": "${:.2f}",
    "GM $": "${:.2f}"
}))

# --- BASE CALCS ---
base_qty = qty_breaks[0]
new_qty = int(base_qty * (1 + growth_pct))
base_lp = list_prices[base_qty]
base_dp = base_lp * (1 - discount_pct)

orig_sales = base_lp * base_qty
new_sales = base_dp * new_qty
orig_cogs = std_cost * base_qty
new_cogs = std_cost * new_qty

def totalize(merch_sales, merch_cogs):
    total_rev = merch_sales + setup_rev + shipping_net + handling_net
    total_cogs = merch_cogs + setup_cost + shipping_cogs + handling_cogs
    gm = total_rev - total_cogs
    gmp = gm / total_rev if total_rev else 0
    return total_rev, total_cogs, gm, gmp

o_rev, o_cogs, o_gm, o_gmp = totalize(orig_sales, orig_cogs)
n_rev, n_cogs, n_gm, n_gmp = totalize(new_sales, new_cogs)
gm_delta = n_gm - o_gm
gm_pct_delta = n_gmp - o_gmp

# --- OUTPUT ---
st.subheader("Revenue / Margin Comparison")
summary = pd.DataFrame({
    "Scenario": ["Original", "Scenario"],
    "Sales": [f"${o_rev:,.2f}", f"${n_rev:,.2f}"],
    "COGS": [f"${o_cogs:,.2f}", f"${n_cogs:,.2f}"],
    "GM $": [f"${o_gm:,.2f}", f"${n_gm:,.2f}"],
    "GM %": [f"{o_gmp*100:.1f}%", f"{n_gmp*100:.1f}%"],
    "Change in GM $": ["—", f"${gm_delta:,.2f}"]
}).set_index("Scenario")
st.table(summary)

# --- VISUAL SUMMARY ---
st.subheader("📊 Summary")
col1, col2 = st.columns(2)
with col1:
    st.markdown("### Original")
    st.metric("Units", base_qty)
    st.metric("GM $", f"${o_gm:,.2f}")
    st.metric("GM %", f"{o_gmp*100:.1f}%")
with col2:
    st.markdown("### Scenario")
    st.metric("Units", new_qty, delta=f"{new_qty - base_qty}")
    st.metric("GM $", f"${n_gm:,.2f}", delta=f"{'🔼 +' if gm_delta >= 0 else '🔻 -'}${abs(gm_delta):,.2f}", delta_color="inverse" if gm_delta < 0 else "normal")
    st.metric("GM %", f"{n_gmp*100:.1f}%", delta=f"{'🔼 +' if gm_pct_delta >= 0 else '🔻 -'}{abs(gm_pct_delta*100):.1f}%", delta_color="inverse" if gm_pct_delta < 0 else "normal")
