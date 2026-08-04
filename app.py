import streamlit as st
import pandas as pd
import datetime

# Page configuration for Mobile View
st.set_page_config(page_title="Store Billing App", page_icon="🛍️", layout="centered")

# Custom CSS for Mobile Optimization
st.markdown("""
<style>
    .main-header {
        text-align: center;
        color: #1B365D;
        font-weight: bold;
        margin-bottom: 5px;
    }
    .sub-header {
        text-align: center;
        color: #555;
        font-size: 14px;
        margin-bottom: 15px;
    }
    .stButton>button {
        width: 100%;
        background-color: #1B365D;
        color: white;
        font-weight: bold;
        border-radius: 8px;
        height: 45px;
    }
    .reset-btn>button {
        background-color: #C00000 !important;
    }
</style>
""", unsafe_allow_html=True)

# App Title
st.markdown("<h2 class='main-header'>🛍️ Store Billing Mobile App</h2>", unsafe_allow_html=True)
st.markdown("<p class='sub-header'>Decorative Lights & Electrical Store</p>", unsafe_allow_html=True)

# Initial Inventory Data
if 'inventory' not in st.session_state:
    st.session_state.inventory = pd.DataFrame([
        {"Item Code": "101", "Item Name": "LED Bulb 12W", "Price": 120.0, "Stock": 150},
        {"Item Code": "102", "Item Name": "Antique Brass Light", "Price": 2500.0, "Stock": 25},
        {"Item Code": "103", "Item Name": "Modern Wall Sconce Lamp", "Price": 1800.0, "Stock": 30},
        {"Item Code": "104", "Item Name": "Crystal Chandelier 6-Light", "Price": 12500.0, "Stock": 8},
        {"Item Code": "105", "Item Name": "Smart Wi-Fi RGB Strip 5M", "Price": 950.0, "Stock": 60},
        {"Item Code": "106", "Item Name": "Edison Filament Bulb 40W", "Price": 220.0, "Stock": 100},
    ])

# Cart Session State
if 'cart' not in st.session_state:
    st.session_state.cart = []

# Tabs
tab1, tab2, tab3 = st.tabs(["🛒 Quick Billing", "🧾 Final Bill & QR", "📦 Inventory Master"])

# --- TAB 1: QUICK BILLING ---
with tab1:
    st.subheader("1. Add Item to Cart")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        # Dropdown / Code selection
        item_options = [f"{row['Item Code']} - {row['Item Name']} (₹{row['Price']})" for _, row in st.session_state.inventory.iterrows()]
        selected_item = st.selectbox("Select Product or Scan Code", item_options)
    
    with col2:
        qty = st.number_input("Qty", min_value=1, value=1, step=1)
    
    if st.button("➕ Add to Cart"):
        code = selected_item.split(" - ")[0]
        item_row = st.session_state.inventory[st.session_state.inventory["Item Code"] == code].iloc[0]
        
        st.session_state.cart.append({
            "Code": code,
            "Item Name": item_row["Item Name"],
            "Qty": qty,
            "Rate": item_row["Price"],
            "Total": qty * item_row["Price"]
        })
        st.success(f"Added {item_row['Item Name']} x {qty}")

    st.divider()
    st.subheader("2. Cart Items")
    if st.session_state.cart:
        df_cart = pd.DataFrame(st.session_state.cart)
        st.dataframe(df_cart[["Item Name", "Qty", "Rate", "Total"]], use_container_width=True)
        
        subtotal = df_cart["Total"].sum()
        st.write(f"**Sub Total:** ₹{subtotal:,.2f}")
        
        if st.button("🗑️ Clear Cart"):
            st.session_state.cart = []
            st.rerun()
    else:
        st.info("Cart is empty. Add items above.")

# --- TAB 2: FINAL BILL & QR ---
with tab2:
    st.subheader("🧾 Tax Invoice / Bill")
    if st.session_state.cart:
        df_cart = pd.DataFrame(st.session_state.cart)
        
        st.markdown(f"**Invoice No:** INV-{datetime.datetime.now().strftime('%Y%m%d%H%M')}")
        st.markdown(f"**Date:** {datetime.date.today().strftime('%d-%b-%Y')}")
        st.markdown("---")
        
        st.table(df_cart[["Item Name", "Qty", "Rate", "Total"]])
        
        subtotal = df_cart["Total"].sum()
        gst = subtotal * 0.18
        grand_total = subtotal + gst
        
        col_a, col_b = st.columns(2)
        with col_a:
            st.write(f"**Sub Total:** ₹{subtotal:,.2f}")
            st.write(f"**GST (18%):** ₹{gst:,.2f}")
            st.markdown(f"### **Grand Total: ₹{grand_total:,.2f}**")
        
        with col_b:
            # Dynamic UPI QR Code URL
            upi_qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=upi://pay?pa=storebilling@upi&pn=DecorativeStore&am={grand_total}&cu=INR"
            st.image(upi_qr_url, caption="Scan to Pay via PhonePe / Paytm / GPay", width=140)
            
        st.divider()
        st.button("🖨️ Print / Save Invoice")
    else:
        st.warning("Please add items in Tab 1 first!")

# --- TAB 3: INVENTORY MASTER ---
with tab3:
    st.subheader("📦 Product Database & Stock")
    st.dataframe(st.session_state.inventory, use_container_width=True)
