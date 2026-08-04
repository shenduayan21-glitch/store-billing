import streamlit as st
import pandas as pd
import datetime

# Page Configuration for Mobile View
st.set_page_config(page_title="Pro Scan Billing App", page_icon="⚡", layout="wide")

# Custom Styling
st.markdown("""
<style>
    .main-header { text-align: center; color: #1B365D; font-weight: bold; margin-bottom: 2px; }
    .sub-header { text-align: center; color: #555; font-size: 14px; margin-bottom: 15px; }
    .stButton>button { width: 100%; background-color: #1B365D; color: white; font-weight: bold; border-radius: 8px; }
    div[data-baseweb="tab-list"] { justify-content: center; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# SESSION STATE INITIALIZATION
# ---------------------------------------------------------
if 'store_info' not in st.session_state:
    st.session_state.store_info = {
        "store_name": "DECORATIVE LIGHTS & ELECTRICAL STORE",
        "address": "123, Main Market Road, Near City Center, Delhi",
        "phone": "+91 98765 43210",
        "gstin": "07AAAAA0000A1Z5",
        "upi_id": "storebilling@upi",
        "gst_rate": 18.0
    }

if 'inventory' not in st.session_state:
    st.session_state.inventory = pd.DataFrame([
        {"Item Code": "101", "Item Name": "LED Bulb 12W", "Category": "Electrical", "Price": 120.0, "Stock": 150},
        {"Item Code": "102", "Item Name": "Antique Brass Light", "Category": "Decorative", "Price": 2500.0, "Stock": 25},
        {"Item Code": "103", "Item Name": "Modern Wall Lamp", "Category": "Decorative", "Price": 1800.0, "Stock": 30},
        {"Item Code": "104", "Item Name": "Crystal Chandelier", "Category": "Decorative", "Price": 12500.0, "Stock": 8},
        {"Item Code": "105", "Item Name": "Smart RGB Strip 5M", "Category": "Smart Lights", "Price": 950.0, "Stock": 60},
    ])

if 'cart' not in st.session_state:
    st.session_state.cart = {}  # Format: {code: {"Code": ..., "Item Name": ..., "Qty": ..., "Rate": ...}}

if 'sales_history' not in st.session_state:
    st.session_state.sales_history = pd.DataFrame(columns=["Invoice No", "Date", "Customer", "Amount", "Payment Mode"])

# App Header
st.markdown(f"<h2 class='main-header'>⚡ {st.session_state.store_info['store_name']}</h2>", unsafe_allow_html=True)
st.markdown(f"<p class='sub-header'>{st.session_state.store_info['address']} | Ph: {st.session_state.store_info['phone']}</p>", unsafe_allow_html=True)

# Tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "⚡ Quick Scan", 
    "🧾 Final Bill", 
    "📦 Inventory", 
    "📊 Sales History", 
    "⚙️ Profile Settings"
])

# ---------------------------------------------------------
# TAB 1: QUICK BARCODE SCAN BILLING
# ---------------------------------------------------------
with tab1:
    st.subheader("🔍 Scan Product / Enter Code")
    
    # Callback function for Auto-Scan Processing
    def process_scan():
        scanned_code = st.session_state.scan_input.strip()
        if scanned_code:
            inv_match = st.session_state.inventory[st.session_state.inventory["Item Code"] == scanned_code]
            if not inv_match.empty:
                item = inv_match.iloc[0]
                if scanned_code in st.session_state.cart:
                    st.session_state.cart[scanned_code]["Qty"] += 1
                else:
                    st.session_state.cart[scanned_code] = {
                        "Code": scanned_code,
                        "Item Name": item["Item Name"],
                        "Qty": 1,
                        "Rate": float(item["Price"])
                    }
                st.session_state.scan_status = f"✅ Added: {item['Item Name']}"
            else:
                st.session_state.scan_status = f"❌ Code '{scanned_code}' not found in inventory!"
        st.session_state.scan_input = ""  # Reset input field for next scan

    if 'scan_status' not in st.session_state:
        st.session_state.scan_status = ""

    # Barcode/Code Scan Input Field
    st.text_input("Point Barcode Scanner here or Type Code & press Enter:", key="scan_input", on_change=process_scan, placeholder="e.g. 101, 102...")
    
    if st.session_state.scan_status:
        if "✅" in st.session_state.scan_status:
            st.success(st.session_state.scan_status)
        else:
            st.error(st.session_state.scan_status)

    st.divider()
    st.subheader("🛒 Current Cart Items")
    
    if st.session_state.cart:
        # Build Cart Display Table
        cart_data = []
        for code, details in list(st.session_state.cart.items()):
            cart_data.append({
                "Code": details["Code"],
                "Item Name": details["Item Name"],
                "Qty": details["Qty"],
                "Rate (₹)": details["Rate"],
                "Total (₹)": details["Qty"] * details["Rate"]
            })
            
        df_cart = pd.DataFrame(cart_data)
        
        # Display Table with Remove Option
        for idx, row in df_cart.iterrows():
            c1, c2, c3, c4, c5 = st.columns([1, 3, 1, 1.5, 1])
            c1.write(f"**{row['Code']}**")
            c2.write(row['Item Name'])
            c3.write(f"x{row['Qty']}")
            c4.write(f"₹{row['Total (₹)']:,.2f}")
            if c5.button("❌", key=f"remove_{row['Code']}"):
                del st.session_state.cart[row['Code']]
                st.rerun()

        st.divider()
        grand_cart_total = sum(d["Qty"] * d["Rate"] for d in st.session_state.cart.values())
        st.markdown(f"### **Cart Subtotal: ₹{grand_cart_total:,.2f}**")
        
        if st.button("🗑️ Clear Entire Cart"):
            st.session_state.cart = {}
            st.session_state.scan_status = ""
            st.rerun()
    else:
        st.info("No items scanned yet. Scan a code above to start billing!")

# ---------------------------------------------------------
# TAB 2: FINAL BILL & PAYMENT QR
# ---------------------------------------------------------
with tab2:
    st.subheader("🧾 Printable Invoice / Bill")
    if st.session_state.cart:
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            cust_name = st.text_input("Customer Name", "Walk-in Customer")
        with col_c2:
            pay_mode = st.selectbox("Payment Mode", ["UPI / PhonePe / GPay", "Cash", "Credit Card", "Udhar / Credit"])
            
        inv_no = f"INV-{datetime.datetime.now().strftime('%Y%m%d%H%M')}"
        today_date = datetime.date.today().strftime('%d-%b-%Y')
        
        st.markdown(f"**Invoice No:** `{inv_no}` | **Date:** `{today_date}`")
        st.markdown(f"**Customer:** {cust_name} | **GSTIN:** {st.session_state.store_info['gstin']}")
        st.divider()
        
        bill_data = []
        for details in st.session_state.cart.values():
            bill_data.append({
                "Item Name": details["Item Name"],
                "Qty": details["Qty"],
                "Rate": details["Rate"],
                "Total": details["Qty"] * details["Rate"]
            })
        
        df_bill = pd.DataFrame(bill_data)
        st.table(df_bill)
        
        subtotal = sum(d["Total"] for d in bill_data)
        gst_percent = st.session_state.store_info["gst_rate"]
        gst_amount = subtotal * (gst_percent / 100.0)
        grand_total = subtotal + gst_amount
        
        col_a, col_b = st.columns(2)
        with col_a:
            st.write(f"**Sub Total:** ₹{subtotal:,.2f}")
            st.write(f"**GST ({gst_percent}%):** ₹{gst_amount:,.2f}")
            st.markdown(f"## **Grand Total: ₹{grand_total:,.2f}**")
            
        with col_b:
            upi_id = st.session_state.store_info["upi_id"]
            store_n = st.session_state.store_info["store_name"]
            qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=160x160&data=upi://pay?pa={upi_id}&pn={store_n}&am={grand_total}&cu=INR"
            st.image(qr_url, caption=f"Scan to Pay ₹{grand_total:,.2f} via UPI", width=150)
            
        if st.button("✅ Complete Sale & Save History"):
            new_sale = pd.DataFrame([{
                "Invoice No": inv_no,
                "Date": today_date,
                "Customer": cust_name,
                "Amount": grand_total,
                "Payment Mode": pay_mode
            }])
            st.session_state.sales_history = pd.concat([st.session_state.sales_history, new_sale], ignore_index=True)
            st.session_state.cart = {}
            st.session_state.scan_status = ""
            st.balloons()
            st.success("Transaction Recorded & Cart Cleared!")
            st.rerun()
    else:
        st.warning("Cart is empty! Scan items in Tab 1 first.")

# ---------------------------------------------------------
# TAB 3: INVENTORY & STOCK MASTER
# ---------------------------------------------------------
with tab3:
    st.subheader("📦 Inventory Database & Add Products")
    
    with st.expander("➕ Add New Product"):
        col_p1, col_p2, col_p3 = st.columns(3)
        with col_p1:
            n_code = st.text_input("Item Code / Barcode")
            n_name = st.text_input("Item Name")
        with col_p2:
            n_cat = st.text_input("Category", "General")
            n_price = st.number_input("Selling Price (₹)", min_value=0.0, value=100.0)
        with col_p3:
            n_stock = st.number_input("Initial Stock", min_value=0, value=50)
            
        if st.button("Save Product"):
            if n_code and n_name:
                new_item = pd.DataFrame([{"Item Code": n_code, "Item Name": n_name, "Category": n_cat, "Price": n_price, "Stock": n_stock}])
                st.session_state.inventory = pd.concat([st.session_state.inventory, new_item], ignore_index=True)
                st.success(f"Product '{n_name}' added successfully!")
                st.rerun()
            else:
                st.error("Item Code and Name are required!")
                
    st.divider()
    st.subheader("Current Stock List")
    edited_df = st.data_editor(st.session_state.inventory, use_container_width=True, num_rows="dynamic")
    if st.button("💾 Update Stock / Price Changes"):
        st.session_state.inventory = edited_df
        st.success("Inventory updated successfully!")

# ---------------------------------------------------------
# TAB 4: SALES HISTORY
# ---------------------------------------------------------
with tab4:
    st.subheader("📊 Sales History & Reports")
    if not st.session_state.sales_history.empty:
        total_sales = st.session_state.sales_history["Amount"].sum()
        st.metric("Total Revenue", f"₹{total_sales:,.2f}")
        st.dataframe(st.session_state.sales_history, use_container_width=True)
        
        csv = st.session_state.sales_history.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Sales Report", csv, "sales_report.csv", "text/csv")
    else:
        st.info("No sales transactions recorded yet.")

# ---------------------------------------------------------
# TAB 5: PROFILE SETTINGS
# ---------------------------------------------------------
with tab5:
    st.subheader("⚙️ Store Profile Settings")
    
    s_name = st.text_input("Store Name", st.session_state.store_info["store_name"])
    s_addr = st.text_area("Store Address", st.session_state.store_info["address"])
    s_phone = st.text_input("Phone Number", st.session_state.store_info["phone"])
    s_gstin = st.text_input("GSTIN", st.session_state.store_info["gstin"])
    s_upi = st.text_input("UPI ID (For QR Code)", st.session_state.store_info["upi_id"])
    s_tax_rate = st.number_input("GST Rate (%)", min_value=0.0, max_value=28.0, value=float(st.session_state.store_info["gst_rate"]))
    
    if st.button("💾 Save Profile Settings"):
        st.session_state.store_info = {
            "store_name": s_name,
            "address": s_addr,
            "phone": s_phone,
            "gstin": s_gstin,
            "upi_id": s_upi,
            "gst_rate": s_tax_rate
        }
        st.success("Profile Updated!")
        st.rerun()
