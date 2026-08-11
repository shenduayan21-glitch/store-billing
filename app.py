import streamlit as st
import pandas as pd
import datetime
from supabase import create_client, Client

# Page Configuration
st.set_page_config(page_title="Pro Scan Billing App", page_icon="⚡", layout="wide")

# =========================================================
# 🔒 SUPABASE CLOUD DATABASE CONNECTION
# =========================================================
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    st.error("⚠️ Supabase Credentials missing in Streamlit Secrets!")

# --- HELPER FUNCTIONS FOR SUPABASE ---

# 1. Profile Load & Save
def load_client_profile(client_key):
    try:
        res = supabase.table("store_profile").select("*").eq("client_key", client_key).execute()
        if res.data:
            data = res.data[0]
            return {
                "store_name": data.get("store_name", ""),
                "address": data.get("address", ""),
                "phone": data.get("phone", ""),
                "gstin": data.get("gstin", ""),
                "upi_id": data.get("upi_id", ""),
                "gst_rate": float(data.get("gst_rate", 0.0))
            }
    except Exception:
        pass
    return {"store_name": "", "address": "", "phone": "", "gstin": "", "upi_id": "", "gst_rate": 0.0}

def save_client_profile(client_key, profile_data):
    try:
        profile_data["client_key"] = client_key
        supabase.table("store_profile").upsert(profile_data, on_conflict="client_key").execute()
        return True
    except Exception as e:
        st.error(f"Profile save error: {e}")
        return False

# 2. Inventory Load & Save
def load_client_inventory(client_key):
    try:
        response = supabase.table("inventory").select("*").eq("client_key", client_key).execute()
        if response.data:
            df = pd.DataFrame(response.data)
            return df[["Item Code", "Item Name", "Category", "Price", "Stock"]]
    except Exception:
        pass
    return pd.DataFrame(columns=["Item Code", "Item Name", "Category", "Price", "Stock"])

def save_client_inventory(client_key, df_inventory):
    try:
        supabase.table("inventory").delete().eq("client_key", client_key).execute()
        records = df_inventory.to_dict(orient="records")
        for r in records:
            r["client_key"] = client_key
        if records:
            supabase.table("inventory").insert(records).execute()
    except Exception as e:
        st.error(f"Inventory save error: {e}")

# 3. Sales History Load & Save
def load_client_sales(client_key):
    try:
        response = supabase.table("sales_history").select("*").eq("client_key", client_key).order("id", desc=True).execute()
        if response.data:
            df = pd.DataFrame(response.data)
            df = df.rename(columns={
                "invoice_no": "Invoice No",
                "date": "Date",
                "customer": "Customer",
                "amount": "Amount",
                "payment_mode": "Payment Mode"
            })
            return df[["Invoice No", "Date", "Customer", "Amount", "Payment Mode"]]
    except Exception:
        pass
    return pd.DataFrame(columns=["Invoice No", "Date", "Customer", "Amount", "Payment Mode"])

def save_single_sale(client_key, invoice_no, date, customer, amount, pay_mode):
    try:
        sale_data = {
            "client_key": client_key,
            "invoice_no": invoice_no,
            "date": date,
            "customer": customer,
            "amount": float(amount),
            "payment_mode": pay_mode
        }
        supabase.table("sales_history").insert(sale_data).execute()
    except Exception as e:
        st.error(f"Sales record save error: {e}")

# =========================================================
# 🔒 MASTER KEYS & SUBSCRIPTION DATABASE
# =========================================================
CLIENT_LICENSES = {
    # 👑 AAPKI ADMIN KEY (Lifetime Access)
    "Ayan@786786": {
        "client_name": "Admin Account",
        "expiry_date": None
    },
    
    # 📱 CLIENT KEYS (Monthly System)
    "Ayan786123": {
        "client_name": "Sharma Electricals",
        "expiry_date": datetime.date(2026, 8, 15)
    },
    "DEMO-CLIENT-999": {
        "client_name": "Trial Demo Account",
        "expiry_date": datetime.date(2026, 8, 5)
    }
}

DEVELOPER_UPI_ID = "shenduayan21-2@okhdfcbank"

# Custom Styling & Print Logic
st.markdown("""
<style>
    .main-header { text-align: center; color: #1B365D; font-weight: bold; margin-bottom: 2px; }
    .sub-header { text-align: center; color: #555; font-size: 14px; margin-bottom: 15px; }
    .stButton>button { width: 100%; background-color: #1B365D; color: white; font-weight: bold; border-radius: 8px; }
    div[data-baseweb="tab-list"] { justify-content: center; }

    .lock-box {
        background-color: #FFEBEE;
        border: 2px solid #D32F2F;
        padding: 25px;
        border-radius: 12px;
        text-align: center;
        margin-top: 20px;
    }

    @media print {
        header, footer, [data-testid="stHeader"], [data-testid="stSidebar"], [data-baseweb="tab-list"], .no-print, button, .stButton {
            display: none !important;
        }
        .printable-area {
            position: absolute !important; left: 0 !important; top: 0 !important; width: 100% !important; padding: 10px !important;
        }
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# SESSION STATE INITIALIZATION
# ---------------------------------------------------------
if 'active_client_key' not in st.session_state:
    st.session_state.active_client_key = ""

if 'store_info' not in st.session_state:
    st.session_state.store_info = {"store_name": "", "address": "", "phone": "", "gstin": "", "upi_id": "", "gst_rate": 0.0}

if 'inventory' not in st.session_state:
    st.session_state.inventory = pd.DataFrame(columns=["Item Code", "Item Name", "Category", "Price", "Stock"])

if 'cart' not in st.session_state:
    st.session_state.cart = {}

if 'sales_history' not in st.session_state:
    st.session_state.sales_history = pd.DataFrame(columns=["Invoice No", "Date", "Customer", "Amount", "Payment Mode"])

# ---------------------------------------------------------
# LOGIN SCREEN & EXPIRY CHECK
# ---------------------------------------------------------
today_date = datetime.date.today()

# Login Screen
if not st.session_state.active_client_key:
    st.markdown("<h2 class='main-header'>🔑 Store Billing System Login</h2>", unsafe_allow_html=True)
    st.markdown("<p class='sub-header'>Kripya Apni Unique License Key Enter Karein</p>", unsafe_allow_html=True)
    
    col_q1, col_q2, col_q3 = st.columns([1, 1, 1])
    with col_q2:
        dev_qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=180x180&data=upi://pay?pa={DEVELOPER_UPI_ID}&pn=AppSubscription&cu=INR"
        st.image(dev_qr_url, caption=f"Payment / Renewal QR ({DEVELOPER_UPI_ID})", width=180)
    
    client_key_input = st.text_input("Enter License Key:", type="password", placeholder="Enter Key...")
    if st.button("🔓 Login to Billing App"):
        clean_key = client_key_input.strip()
        if clean_key in CLIENT_LICENSES:
            st.session_state.active_client_key = clean_key
            st.session_state.store_info = load_client_profile(clean_key)
            st.session_state.inventory = load_client_inventory(clean_key)
            st.session_state.sales_history = load_client_sales(clean_key)
            st.success(f"Welcome {CLIENT_LICENSES[clean_key]['client_name']}!")
            st.rerun()
        else:
            st.error("Invalid License Key! Kripya Apni Key Check Karein.")
    st.stop()

# License Expiry Check
current_key = st.session_state.active_client_key
client_data = CLIENT_LICENSES[current_key]
expiry_date = client_data["expiry_date"]

if expiry_date is not None and today_date > expiry_date:
    st.markdown(f"<h2 class='main-header'>🔒 {client_data['client_name']}</h2>", unsafe_allow_html=True)
    st.markdown(f"""
    <div class='lock-box'>
        <h1 style='color: #D32F2F;'>⚠️ SUBSCRIPTION EXPIRED!</h1>
        <p>Aapka Software Validity Date <b>({expiry_date.strftime('%d-%b-%Y')})</b> Khatam Ho Gayi Hai.</p>
        <p>Monthly renewal fee pay karke app continue karein.</p>
        <hr>
        <p><b>Pay via UPI ID:</b> <code>{DEVELOPER_UPI_ID}</code></p>
    </div>
    """, unsafe_allow_html=True)
    
    qr_pay_url = f"https://api.qrserver.com/v1/create-qr-code/?size=180x180&data=upi://pay?pa={DEVELOPER_UPI_ID}&pn=AppSubscription&cu=INR"
    st.image(qr_pay_url, caption="Scan to Pay Renewal Fee", width=180)
    
    if st.button("🚪 Logout / Switch Key"):
        st.session_state.active_client_key = ""
        st.rerun()
        
    st.stop()

# Auto-Sync Profile, Inventory, and Sales if empty
if not st.session_state.store_info.get("store_name"):
    st.session_state.store_info = load_client_profile(current_key)

if st.session_state.inventory.empty:
    st.session_state.inventory = load_client_inventory(current_key)

if st.session_state.sales_history.empty:
    st.session_state.sales_history = load_client_sales(current_key)

# ---------------------------------------------------------
# MAIN APP INTERFACE
# ---------------------------------------------------------
validity_display = "Lifetime (Unlimited)" if expiry_date is None else f"Valid Till: {expiry_date.strftime('%d-%b-%Y')}"

header_title = st.session_state.store_info['store_name'] if st.session_state.store_info['store_name'] else "My Store"
header_addr = st.session_state.store_info['address'] if st.session_state.store_info['address'] else "Store Address"
header_phone = st.session_state.store_info['phone'] if st.session_state.store_info['phone'] else "Phone"

st.markdown(f"<div class='no-print'><h2 class='main-header'>⚡ {header_title}</h2>"
            f"<p class='sub-header'>{header_addr} | Ph: {header_phone} | "
            f"<b>{validity_display}</b></p></div>", 
            unsafe_allow_html=True)

# Tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "⚡ Quick Scan", 
    "🧾 Final Bill", 
    "📦 Inventory", 
    "📊 Sales History", 
    "⚙️ Profile Settings"
])

# --- TAB 1: QUICK BARCODE SCAN BILLING ---
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
                st.session_state.scan_status = f"❌ Code '{scanned_code}' not found in Inventory!"
        st.session_state.scan_input = ""

    if 'scan_status' not in st.session_state:
        st.session_state.scan_status = ""

    st.text_input("Point Barcode Scanner here or Type Code & press Enter:", key="scan_input", on_change=process_scan, placeholder="Enter Item Code...", autocomplete="off")
    
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
        st.info("No items scanned yet. Add products in Inventory tab and scan code above to start!")

# --- TAB 2: FINAL BILL ---
with tab2:
    st.subheader("🧾 Printable Invoice / Bill")
    if st.session_state.cart:
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            cust_name = st.text_input("Customer Name", "Walk-in Customer")
        with col_c2:
            pay_mode = st.selectbox("Payment Mode", ["UPI / PhonePe / GPay", "Cash", "Credit Card", "Udhar / Credit"])
            
        inv_no = f"INV-{datetime.datetime.now().strftime('%Y%m%d%H%M')}"
        today_formatted = datetime.date.today().strftime('%d-%b-%Y')
        
        st.markdown("<div class='no-print'>", unsafe_allow_html=True)
        col_b1, col_b2 = st.columns(2)
        with col_b1:
            st.components.v1.html("""
                <button onclick="window.parent.print()" style="width:100%; height:45px; background-color:#28a745; color:white; font-weight:bold; font-size:16px; border:none; border-radius:8px; cursor:pointer;">
                    🖨️ Print / Save PDF Bill
                </button>
            """, height=50)
        with col_b2:
            if st.button("✅ Complete Sale & Save Record"):
                for code, details in st.session_state.cart.items():
                    qty_sold = details["Qty"]
                    st.session_state.inventory.loc[st.session_state.inventory["Item Code"] == code, "Stock"] -= qty_sold

                save_client_inventory(current_key, st.session_state.inventory)

                total_sale_amt = sum(d["Qty"] * d["Rate"] for d in st.session_state.cart.values()) * (1 + float(st.session_state.store_info.get("gst_rate", 0))/100.0)
                
                # Save to Supabase Cloud
                save_single_sale(current_key, inv_no, today_formatted, cust_name, total_sale_amt, pay_mode)
                st.session_state.sales_history = load_client_sales(current_key)

                st.session_state.cart = {}
                st.session_state.scan_status = ""
                st.balloons()
                st.success("Transaction Recorded & Saved to Cloud Database!")
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

        st.divider()

        st.markdown("<div class='printable-area'>", unsafe_allow_html=True)
        st.markdown(f"## **{header_title}**")
        st.write(f"{header_addr} | Ph: {header_phone}")
        if st.session_state.store_info.get('gstin'):
            st.write(f"**GSTIN:** {st.session_state.store_info['gstin']}")
        st.markdown("---")
        
        st.write(f"**Invoice No:** `{inv_no}` | **Date:** `{today_formatted}`")
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
        gst_percent = float(st.session_state.store_info.get("gst_rate", 0))
        gst_amount = subtotal * (gst_percent / 100.0)
        grand_total = subtotal + gst_amount
        
        col_a, col_b = st.columns(2)
        with col_a:
            st.write(f"**Sub Total:** ₹{subtotal:,.2f}")
            if gst_percent > 0:
                st.write(f"**GST ({gst_percent}%):** ₹{gst_amount:,.2f}")
            st.markdown(f"### **Grand Total: ₹{grand_total:,.2f}**")
            
        with col_b:
            if st.session_state.store_info.get("upi_id"):
                st.markdown("<div class='qr-code-box'>", unsafe_allow_html=True)
                upi_id = st.session_state.store_info["upi_id"]
                store_n = st.session_state.store_info["store_name"]
                qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=140x140&data=upi://pay?pa={upi_id}&pn={store_n}&am={grand_total}&cu=INR"
                st.image(qr_url, caption=f"Scan & Pay ₹{grand_total:,.2f}", width=130)
                st.markdown("</div>", unsafe_allow_html=True)
            
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.warning("Cart is empty! Add items in Tab 1 first.")

# --- TAB 3: INVENTORY MASTER ---
with tab3:
    st.subheader("📦 Inventory Database & Add Products")
    
    with st.expander("➕ Add New Product", expanded=True):
        col_p1, col_p2, col_p3 = st.columns(3)
        with col_p1:
            n_code = st.text_input("Item Code / Barcode (e.g. 101)")
            n_name = st.text_input("Item Name")
        with col_p2:
            n_cat = st.text_input("Category", "General")
            n_price = st.number_input("Selling Price (₹)", min_value=0.0, value=0.0)
        with col_p3:
            n_stock = st.number_input("Initial Stock", min_value=0, value=10)
            
        if st.button("Save Product"):
            if n_code and n_name:
                new_item = pd.DataFrame([{"Item Code": n_code, "Item Name": n_name, "Category": n_cat, "Price": n_price, "Stock": n_stock}])
                st.session_state.inventory = pd.concat([st.session_state.inventory, new_item], ignore_index=True)
                save_client_inventory(current_key, st.session_state.inventory)
                st.success(f"Product '{n_name}' added & saved to Cloud Database!")
                st.rerun()
            else:
                st.error("Item Code and Name are required!")
                
    st.divider()
    st.subheader("Current Stock List")
    edited_df = st.data_editor(st.session_state.inventory, use_container_width=True, num_rows="dynamic")
    if st.button("💾 Save Changes"):
        st.session_state.inventory = edited_df
        save_client_inventory(current_key, st.session_state.inventory)
        st.success("Inventory updated and saved to Cloud Database!")

# --- TAB 4: SALES HISTORY ---
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

# --- TAB 5: PROFILE SETTINGS ---
with tab5:
    st.subheader("⚙️ Store Profile Settings")
    st.info("Enter your Store details below and click Save.")
    
    curr = st.session_state.store_info
    
    s_name = st.text_input("Store Name", value=curr.get("store_name", ""), placeholder="e.g. Ayan Lights Store")
    s_addr = st.text_area("Store Address", value=curr.get("address", ""), placeholder="e.g. At Post Waholi Tal Kalyan")
    s_phone = st.text_input("Phone Number", value=curr.get("phone", ""), placeholder="e.g. 9689450833")
    s_gstin = st.text_input("GSTIN (Optional)", value=curr.get("gstin", ""), placeholder="e.g. 07AAAA444DDEEE")
    s_upi = st.text_input("UPI ID (For Billing QR Code)", value=curr.get("upi_id", ""), placeholder="e.g. shenduayan21-2@okhdfcbank")
    
    try:
        default_gst = float(curr.get("gst_rate", 0.0))
    except (ValueError, TypeError):
        default_gst = 0.0

    s_tax_rate = st.number_input("GST Rate (%)", min_value=0.0, max_value=28.0, value=default_gst, step=1.0)
    
    if st.button("💾 Save Store Profile"):
        new_profile = {
            "store_name": s_name,
            "address": s_addr,
            "phone": s_phone,
            "gstin": s_gstin,
            "upi_id": s_upi,
            "gst_rate": s_tax_rate
        }
        if save_client_profile(current_key, new_profile):
            st.session_state.store_info = new_profile
            st.success("✅ Profile Saved Permanently to Cloud Database!")
            st.rerun()

    st.divider()
    if st.button("🚪 Logout Active License Key"):
        st.session_state.active_client_key = ""
        st.session_state.store_info = {"store_name": "", "address": "", "phone": "", "gstin": "", "upi_id": "", "gst_rate": 0.0}
        st.session_state.inventory = pd.DataFrame(columns=["Item Code", "Item Name", "Category", "Price", "Stock"])
        st.session_state.sales_history = pd.DataFrame(columns=["Invoice No", "Date", "Customer", "Amount", "Payment Mode"])
        st.rerun()
