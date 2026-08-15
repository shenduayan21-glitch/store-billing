import streamlit as st
import pandas as pd
import datetime
import uuid
from supabase import create_client, Client
import razorpay

# Page Configuration
st.set_page_config(page_title="Pro Scan Billing App", page_icon="⚡", layout="wide")

# =========================================================
# 🔒 SECRETS & CLIENT INITIALIZATION
# =========================================================
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception:
    st.error("⚠️ Supabase Credentials missing in Streamlit Secrets!")
    st.stop()

try:
    RAZORPAY_KEY_ID = st.secrets["RAZORPAY_KEY_ID"]
    RAZORPAY_KEY_SECRET = st.secrets["RAZORPAY_KEY_SECRET"]
    razorpay_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))
except Exception:
    st.error("⚠️ Razorpay Credentials missing in Streamlit Secrets!")
    st.stop()

# =========================================================
# 🛠️ HELPER FUNCTIONS
# =========================================================
DEVELOPER_UPI_ID = "shenduayan21-2@okhdfcbank"

def create_or_extend_license(client_name, client_phone, plan_days):
    today = datetime.date.today()
    try:
        clean_p = str(client_phone).strip()
        res = supabase.table("licenses").select("*").eq("client_phone", clean_p).execute()
        if res.data:
            record = res.data[0]
            current_exp = datetime.datetime.strptime(record["expiry_date"], "%Y-%m-%d").date()
            base_date = current_exp if current_exp > today else today
            new_expiry = (base_date + datetime.timedelta(days=plan_days)).isoformat()
            
            supabase.table("licenses").update({
                "expiry_date": new_expiry,
                "status": "active"
            }).eq("client_phone", clean_p).execute()
            
            return record["license_key"], new_expiry, "renewed"
        else:
            new_key = f"BILL-{uuid.uuid4().hex[:8].upper()}"
            new_expiry = (today + datetime.timedelta(days=plan_days)).isoformat()
            
            supabase.table("licenses").insert({
                "license_key": new_key,
                "client_name": str(client_name).strip(),
                "client_phone": clean_p,
                "expiry_date": new_expiry,
                "status": "active"
            }).execute()
            
            return new_key, new_expiry, "created"
    except Exception as e:
        st.error(f"Database Error: {e}")
        return None, None, "error"

def verify_license(key):
    if key == "Ayan@786786":
        return True, {"client_name": "Admin Account", "expiry_date": None}
    try:
        res = supabase.table("licenses").select("*").eq("license_key", key).execute()
        if res.data:
            record = res.data[0]
            exp_str = record.get("expiry_date")
            if not exp_str:
                return True, record
            exp_date = datetime.datetime.strptime(exp_str, "%Y-%m-%d").date()
            if exp_date >= datetime.date.today() and record.get("status") == "active":
                return True, record
            else:
                return False, f"Expired on {exp_date.strftime('%d-%b-%Y')}"
    except Exception:
        pass
    return False, "Invalid License Key!"

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
    except Exception:
        return False

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
    except Exception:
        pass

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
    except Exception:
        pass

# =========================================================
# 🎨 STYLING
# =========================================================
st.markdown("""
<style>
    .main-header { text-align: center; color: #1B365D; font-weight: bold; margin-bottom: 2px; }
    .sub-header { text-align: center; color: #555; font-size: 14px; margin-bottom: 15px; }
    .stButton>button { width: 100%; background-color: #1B365D; color: white; font-weight: bold; border-radius: 8px; }
    div[data-baseweb="tab-list"] { justify-content: center; }

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
if 'client_name' not in st.session_state:
    st.session_state.client_name = ""
if 'expiry_display' not in st.session_state:
    st.session_state.expiry_display = ""
if 'store_info' not in st.session_state:
    st.session_state.store_info = {"store_name": "", "address": "", "phone": "", "gstin": "", "upi_id": "", "gst_rate": 0.0}
if 'inventory' not in st.session_state:
    st.session_state.inventory = pd.DataFrame(columns=["Item Code", "Item Name", "Category", "Price", "Stock"])
if 'cart' not in st.session_state:
    st.session_state.cart = {}
if 'sales_history' not in st.session_state:
    st.session_state.sales_history = pd.DataFrame(columns=["Invoice No", "Date", "Customer", "Amount", "Payment Mode"])

# =========================================================
# 🚪 AUTHENTICATION & PAYMENT SCREEN
# =========================================================
if not st.session_state.active_client_key:
    st.markdown("<h2 class='main-header'>🔑 Store Billing System</h2>", unsafe_allow_html=True)
    st.markdown("<p class='sub-header'>Login karein ya Instant Online Subscription lein</p>", unsafe_allow_html=True)

    tab_login, tab_buy = st.tabs(["🔐 License Login", "💳 Buy / Renew Subscription"])

    with tab_login:
        c_in = st.text_input("Enter License Key:", type="password", placeholder="BILL-XXXXXXXX ya Admin Key")
        if st.button("🔓 Login to Billing App", key="login_btn"):
            clean_key = c_in.strip()
            valid, info = verify_license(clean_key)
            if valid:
                st.session_state.active_client_key = clean_key
                st.session_state.client_name = info.get("client_name", "Store User")
                exp = info.get("expiry_date")
                st.session_state.expiry_display = "Lifetime" if not exp else exp
                st.session_state.store_info = load_client_profile(clean_key)
                st.session_state.inventory = load_client_inventory(clean_key)
                st.session_state.sales_history = load_client_sales(clean_key)
                st.success(f"Welcome {st.session_state.client_name}!")
                st.rerun()
            else:
                st.error(f"Access Denied: {info}")

    with tab_buy:
        st.subheader("⚡ Instant Subscription (Automatic License)")
        name_input = st.text_input("Store Name / Owner Name", key="b_name")
        phone_input = st.text_input("Mobile Number (Permanent ID)", key="b_phone")
        plan_choice = st.radio("Plan Select Karein:", ["Monthly Plan - 299 (30 Days)", "Yearly Plan - 3000 (365 Days)"])
        
        amount = 1 if "Monthly" in plan_choice else 3000
        days = 30 if "Monthly" in plan_choice else 365

        if st.button(f"Generate Payment Link (Rs.{amount})", type="primary"):
            if not phone_input or not name_input:
                st.error("Kripya Store Name aur Mobile Number fill karein!")
            else:
                try:
                    clean_name = str(name_input).strip()
                    clean_phone = str(phone_input).strip()
                    receipt_id = f"rcpt_{uuid.uuid4().hex[:6]}"
                    
                    order_data = {
                        "amount": int(amount * 100),
                        "currency": "INR",
                        "receipt": receipt_id
                    }
                    order = razorpay_client.order.create(data=order_data)
                    order_id = order.get("id")

                    st.session_state["pending_order_id"] = order_id
                    st.session_state["pending_client_name"] = clean_name
                    st.session_state["pending_client_phone"] = clean_phone
                    st.session_state["pending_days"] = days
                    st.session_state["pending_amount"] = amount
                except Exception as err:
                    st.error(f"Payment Gateway Error: {err}")

        if "pending_order_id" in st.session_state:
            st.divider()
            st.success("✅ Order Ready! Click below to pay:")
            
            rzp_key = st.secrets["RAZORPAY_KEY_ID"]
            rzp_amount_paise = int(st.session_state["pending_amount"] * 100)
            rzp_order_id = st.session_state["pending_order_id"]
            c_name = st.session_state["pending_client_name"]
            c_phone = st.session_state["pending_client_phone"]
            
            checkout_html = f"""
            <button id="rzp-button" style="width:100%; height:48px; background-color:#28a745; color:white; font-size:16px; font-weight:bold; border:none; border-radius:8px; cursor:pointer;">
                💳 Pay Rs.{st.session_state['pending_amount']} via UPI / Card / QR
            </button>
            <script src="https://checkout.razorpay.com/v1/checkout.js"></script>
            <script>
            var options = {{
                "key": "{rzp_key}",
                "amount": "{rzp_amount_paise}",
                "currency": "INR",
                "name": "Store Billing App",
                "description": "Software Subscription",
                "order_id": "{rzp_order_id}",
                "prefill": {{
                    "name": "{c_name}",
                    "contact": "{c_phone}"
                }},
                "theme": {{
                    "color": "#1B365D"
                }}
            }};
            var rzp = new Razorpay(options);
            document.getElementById('rzp-button').onclick = function(e){{
                rzp.open();
                e.preventDefault();
            }}
            </script>
            """
            st.components.v1.html(checkout_html, height=60)
            st.caption("Upar diye gaye Green Button par click karke payment complete karein, phir neeche 'Activate' button dabayein.")

            if st.button("🔄 Activate License After Payment"):
                try:
                    payments = razorpay_client.order.payments(st.session_state["pending_order_id"])
                    is_paid = False
                    if payments and "items" in payments:
                        for p in payments["items"]:
                            if p.get("status") == "captured":
                                is_paid = True
                                break
                    
                    if is_paid:
                        key, exp_date, action = create_or_extend_license(
                            st.session_state["pending_client_name"],
                            st.session_state["pending_client_phone"],
                            st.session_state["pending_days"]
                        )
                        st.balloons()
                        st.success("🎉 Payment Received & Verified!")
                        st.info(f"**Aapki License Key:** `{key}`\n\n**Expiry Date:** `{exp_date}`")
                        st.caption("License Login tab me jakar is key se login karein.")
                        del st.session_state["pending_order_id"]
                    else:
                        st.warning("⚠️ Payment abhi complete nahi hui hai. Green button daba kar pehle payment finish karein.")
                except Exception as ex:
                    st.error(f"Verification Error: {ex}")

    st.stop()

# =========================================================
# ⚡ MAIN BILLING APP DASHBOARD
# =========================================================
current_key = st.session_state.active_client_key
header_title = st.session_state.store_info.get('store_name') or "My Store"
header_addr = st.session_state.store_info.get('address') or "Store Address"
header_phone = st.session_state.store_info.get('phone') or "Phone"

st.markdown(f"<div class='no-print'><h2 class='main-header'>⚡ {header_title}</h2>"
            f"<p class='sub-header'>{header_addr} | Ph: {header_phone} | "
            f"<b>Valid: {st.session_state.expiry_display}</b></p></div>", 
            unsafe_allow_html=True)

with st.sidebar:
    st.write(f"👤 **{st.session_state.client_name}**")
    st.caption(f"Key: `{current_key}`")
    if st.button("🚪 Logout"):
        st.session_state.active_client_key = ""
        st.rerun()

if current_key == "Ayan@786786":
    tabs = st.tabs(["⚡ Quick Scan", "🧾 Final Bill", "📦 Inventory", "📊 Sales History", "⚙️ Profile Settings", "👑 Admin License Manager"])
else:
    tabs = st.tabs(["⚡ Quick Scan", "🧾 Final Bill", "📦 Inventory", "📊 Sales History", "⚙️ Profile Settings"])

tab1, tab2, tab3, tab4, tab5 = tabs[0], tabs[1], tabs[2], tabs[3], tabs[4]

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
                "Rate (Rs.)": details["Rate"],
                "Total (Rs.)": details["Qty"] * details["Rate"]
            })
            
        df_cart = pd.DataFrame(cart_data)
        
        for idx, row in df_cart.iterrows():
            c1, c2, c3, c4, c5 = st.columns([1, 3, 1, 1.5, 1])
            c1.write(f"**{row['Code']}**")
            c2.write(row['Item Name'])
            c3.write(f"x{row['Qty']}")
            c4.write(f"Rs.{row['Total (Rs.)']:,.2f}")
            if c5.button("❌", key=f"remove_{row['Code']}"):
                del st.session_state.cart[row['Code']]
                st.rerun()

        st.divider()
        grand_cart_total = sum(d["Qty"] * d["Rate"] for d in st.session_state.cart.values())
        st.markdown(f"### **Cart Subtotal: Rs.{grand_cart_total:,.2f}**")
        
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
                "Rate (Rs.)": details["Rate"],
                "Total (Rs.)": details["Qty"] * details["Rate"]
            })
        
        df_bill = pd.DataFrame(bill_data)
        st.table(df_bill)
        
        subtotal = sum(d["Total (Rs.)"] for d in bill_data)
        gst_percent = float(st.session_state.store_info.get("gst_rate", 0))
        gst_amount = subtotal * (gst_percent / 100.0)
        grand_total = subtotal + gst_amount
        
        col_a, col_b = st.columns(2)
        with col_a:
            st.write(f"**Sub Total:** Rs.{subtotal:,.2f}")
            if gst_percent > 0:
                st.write(f"**GST ({gst_percent}%):** Rs.{gst_amount:,.2f}")
            st.markdown(f"### **Grand Total: Rs.{grand_total:,.2f}**")
            
        with col_b:
            if st.session_state.store_info.get("upi_id"):
                st.markdown("<div class='qr-code-box'>", unsafe_allow_html=True)
                upi_id = st.session_state.store_info["upi_id"]
                store_n = st.session_state.store_info["store_name"]
                qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=140x140&data=upi://pay?pa={upi_id}&pn={store_n}&am={grand_total}&cu=INR"
                st.image(qr_url, caption=f"Scan & Pay Rs.{grand_total:,.2f}", width=130)
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
            n_price = st.number_input("Selling Price (Rs.)", min_value=0.0, value=0.0)
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
        st.metric("Total Revenue", f"Rs.{total_sales:,.2f}")
        st.dataframe(st.session_state.sales_history, use_container_width=True)
    else:
        st.info("Abhi tak koi sale record nahi hui hai.")

# --- TAB 5: PROFILE SETTINGS ---
with tab5:
    st.subheader("⚙️ Store Profile & GST Settings")
    prof = st.session_state.store_info
    
    col_pr1, col_pr2 = st.columns(2)
    with col_pr1:
        s_name = st.text_input("Store Name", value=prof.get("store_name", ""))
        s_addr = st.text_area("Store Address", value=prof.get("address", ""))
        s_ph = st.text_input("Phone Number", value=prof.get("phone", ""))
    with col_pr2:
        s_gst = st.text_input("GSTIN Number", value=prof.get("gstin", ""))
        s_upi = st.text_input("Store UPI ID for Payment QR", value=prof.get("upi_id", ""))
        s_rate = st.number_input("GST Rate (%)", min_value=0.0, max_value=28.0, value=float(prof.get("gst_rate", 0.0)))
        
    if st.button("💾 Save Profile Details"):
        updated_prof = {
            "store_name": s_name,
            "address": s_addr,
            "phone": s_ph,
            "gstin": s_gst,
            "upi_id": s_upi,
            "gst_rate": s_rate
        }
        if save_client_profile(current_key, updated_prof):
            st.session_state.store_info = updated_prof
            st.success("Profile saved successfully!")
            st.rerun()

# --- TAB 6: ADMIN MANAGER ---
if current_key == "Ayan@786786":
    with tabs[5]:
        st.subheader("👑 Client License Manager (Admin Control)")
        
        with st.expander("➕ Manually Add / Extend License"):
            a_name = st.text_input("Client Name")
            a_phone = st.text_input("Client Phone")
            a_days = st.number_input("Days Validity", min_value=1, value=30)
            if st.button("Generate / Extend Key"):
                k, e, act = create_or_extend_license(a_name, a_phone, a_days)
                st.success(f"Done! Key: `{k}` | Exp: {e}")
                st.rerun()

        st.divider()
        st.subheader("All Registered Licenses")
        try:
            res = supabase.table("licenses").select("*").order("id", desc=True).execute()
            if res.data:
                st.dataframe(pd.DataFrame(res.data), use_container_width=True)
            else:
                st.info("No licenses in database.")
        except Exception as e:
            st.error(f"Error fetching licenses: {e}")
