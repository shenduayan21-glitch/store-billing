import streamlit as st
import pandas as pd
import datetime

# Page Configuration
st.set_page_config(page_title="Pro Scan Billing App", page_icon="⚡", layout="wide")

# Custom Styling & Print Optimized CSS
st.markdown("""
<style>
    .main-header { text-align: center; color: #1B365D; font-weight: bold; margin-bottom: 2px; }
    .sub-header { text-align: center; color: #555; font-size: 14px; margin-bottom: 15px; }
    .stButton>button { width: 100%; background-color: #1B365D; color: white; font-weight: bold; border-radius: 8px; }
    div[data-baseweb="tab-list"] { justify-content: center; }

    /* MEDIA PRINT CSS: Hides QR code & app controls on Print */
    @media print {
        header, footer, [data-testid="stHeader"], [data-testid="stSidebar"], [data-baseweb="tab-list"], .no-print, .qr-code-box {
            display: none !important;
        }
        .printable-area {
            position: absolute !important;
            left: 0 !important;
            top: 0 !important;
            width: 100% !important;
            padding: 10px !important;
        }
    }
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
    st.session_state.cart = {}

if 'sales_history' not in st.session_state:
    st.session_state.sales_history = pd.DataFrame(columns=["Invoice No", "Date", "Customer", "Amount", "Payment Mode"])

# App Header
st.markdown(f"<div class='no-print'><h2 class='main-header'>⚡ {st.session_state.store_info['store_name']}</h2>"
            f"<p class='sub-header'>{st.session_state.store_info['address']} | Ph: {st.session_state.store_info['phone']}</p></div>", 
            unsafe_allow_html=True)

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
    
    def process_scan():
        scanned_code = st.session_state.scan_input.strip()
        if scanned_code:
            inv_match = st.session_state.inventory[st.session_state.inventory["Item Code"] == scanned_code]
            if not inv_match.empty:
                item = inv_match.iloc[0]
                current_stock = item["Stock"]
                current_in_cart = st.session_state.cart[scanned_code]["Qty"] if scanned_code in st.session_state.cart else 0
                
                if current_in_cart + 1 > current_stock:
                    st.session_state.scan_status = f"⚠️ Low Stock Alert! Only {current_stock} left."
                else:
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
                st.session_state.scan_status = f"❌ Code '{scanned_code}' not found!"
        st.session_state.scan_input = ""

    if 'scan_status' not in st.session_state:
        st.session_state.scan_status = ""

    st.text_input("Point Barcode Scanner here or Type Code & press Enter:", key="scan_input", on_change=process_scan, placeholder="e.g. 101, 102...")
    
    if st.session_state.scan_status:
        if "✅" in st.session_state.scan_status:
            st.success(st.session_state.scan_status)
        elif "⚠️" in st.session_state.scan_status:
            st.warning(st.session_state.scan_status)
        else:
            st.error(st.session_state.scan_status)

    st.divider()
    st.subheader("🛒 Current Cart Items")
    
    if st.session_state.cart:
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
# TAB 2: FINAL BILL (WITH AUTOMATIC STOCK DEDUCTION)
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
        
        st.markdown("<div class='no-print'>", unsafe_allow_html=True)
        col_b1, col_b2 = st.columns(2)
        with col_b1:
            show_only_bill = st.checkbox("📄 Fullscreen Bill Mode (For Printing)", value=False)
        with col_b2:
            if st.button("✅ Complete Sale & Clear Cart"):
                # 1. AUTOMATIC STOCK DEDUCTION FROM INVENTORY
                for code, details in st.session_state.cart.items():
                    qty_sold = details["Qty"]
                    st.session_state.inventory.loc[st.session_state.inventory["Item Code"] == code, "Stock"] -= qty_sold

                # 2. SAVE TRANSACTION TO SALES HISTORY
                total_sale_amt = sum(d["Qty"] * d["Rate"] for d in st.session_state.cart.values()) * (1 + st.session_state.store_info["gst_rate"]/100.0)
                new_sale = pd.DataFrame([{
                    "Invoice No": inv_no,
                    "Date": today_date,
                    "Customer": cust_name,
                    "Amount": total_sale_amt,
                    "Payment Mode": pay_mode
                }])
                st.session_state.sales_history = pd.concat([st.session_state.sales_history, new_sale], ignore_index=True)
                
                # 3. CLEAR CART & REFRESH
                st.session_state.cart = {}
                st.session_state.scan_status = ""
                st.balloons()
                st.success("Transaction Recorded & Inventory Stock Deducted!")
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

        st.divider()

        # PRINT CONTAINER
        st.markdown("<div class='printable-area'>", unsafe_allow_html=True)
        st.markdown(f"## **{st.session_state.store_info['store_name']}**")
        st.write(f"{st.session_state.store_info['address']} | Ph: {st.session_state.store_info['phone']}")
        st.write(f"**GSTIN:** {st.session_state.store_info['gstin']}")
        st.markdown("---")
        
        st.write(f"**Invoice No:** `{inv_no}` | **Date:** `{today_date}`")
        st.write(f"**Customer Name:** {cust_name} | **Payment Mode:** {pay_mode}")
        
        bill_data = []
        for details in st.session_state.cart.values():
            bill_data.append({
                "Item Description": details["Item Name"],
                "Qty": details["Qty"],
                "Rate (₹)": details["Rate"],
                "Total (₹)": details["Qty"] * details["Rate"]
            })
        
        df_bill = pd.DataFrame(bill_data)
        st.table(df_bill)
        
        subtotal = sum(d["Total (₹)"] for d in bill_data)
        gst_percent = st.session_state.store_info["gst_rate"]
        gst_amount = subtotal * (gst_percent / 100.0)
        grand_total = subtotal + gst_amount
        
        col_a, col_b = st.columns(2)
        with col_a:
            st.write(f"**Sub Total:** ₹{subtotal:,.2f}")
            st.write(f"**GST ({gst_percent}%):** ₹{gst_amount:,.2f}")
            st.markdown(f"### **Grand Total: ₹{grand_total:,.2f}**")
            
        with col_b:
            st.markdown("<div class='qr-code-box'>", unsafe_allow_html=True)
            upi_id = st.session_state.store_info["upi_id"]
            store_n = st.session_state.store_info["store_name"]
            qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=140x140&data=upi://pay?pa={upi_id}&pn={store_n}&am={grand_total}&cu=INR"
            st.image(qr_url, caption=f"Scan & Pay ₹{grand_total:,.2f}", width=130)
            st.markdown("</div>", unsafe_allow_html=True)
            
        st.markdown("</div>", unsafe_allow_html=True)

        if show_only_bill:
            st.info("💡 Mobile Print Tip: Tap browser 3-Dots ➔ Share ➔ Print / Save PDF")
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
